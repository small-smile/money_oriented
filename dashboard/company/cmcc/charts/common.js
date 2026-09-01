/* 中国移动详情页公共工具 —— 供 charts/*.js 使用
 *
 * 数据来源只有一个：同目录 data.js 注入的 window.CMCC（annual / operating / profile），
 * 由 data/extract/gen_cmcc_pages.py 从 data/tables/telecom_00941_*.json 打包。
 * 页面里不手抄任何百分比与占比：凡是比例都在这里由金额/户数现算。
 *
 * 与百度页的 charts/*.js 是两套独立文件（同一套写法），改一个不影响另一个。
 *
 * 本页与百度页最大的不同：运营商的披露口径二十多年里换过好几轮
 * （语音收入 → 不再单列、增值业务 → 应用及信息服务 → 通信/算力/智能三分类），
 * 序列天然有断点。断点不靠「让线自己断在那里」表达，一律用 gapMark() 画成
 * 带说明的灰色竖带，读图的人一眼知道这里是「停止披露」而不是「数据没补」。
 */
var C = window.CMCC || {};

/* ==== 配色：沿用 company/page.css 的深蓝 + 金；产品世代各占一色 ==== */
var NAVY = '#10243e', GOLD = '#c9a24a', MUTED = '#6b7280';
/* 产品世代配色：越靠后的世代越亮，堆叠图上「新业务从底部长出来」看得清 */
var ERA_COLORS = {
    voice:     '#10243e',   /* 语音 */
    sms:       '#4a6fa5',   /* 短信及彩信 */
    data:      '#2980b9',   /* 无线上网（手机流量） */
    broadband: '#16a085',   /* 有线宽带 */
    appInfo:   '#c9a24a',   /* 应用及信息服务（含算力、智能） */
    vas:       '#8e44ad',   /* 早年「增值业务」总口径 */
    other:     '#b0bac5'    /* 其他业务（终端销售等） */
};
var PIE_COLORS = ['#10243e', '#c9a24a', '#2980b9', '#16a085', '#c0392b', '#8e44ad',
                  '#e67e22', '#27ae60', '#2c3e50', '#c2185b', '#00838f', '#d35400'];

/* 残余项灰斜线纹理（「不可穿透」「未单列」的口径统一用它） */
var RESIDUAL_PATTERN = (function () {
    var c = document.createElement('canvas');
    c.width = 10; c.height = 10;
    var x = c.getContext('2d');
    x.fillStyle = '#f0f0f0'; x.fillRect(0, 0, 10, 10);
    x.strokeStyle = '#999'; x.lineWidth = 1.5;
    x.beginPath(); x.moveTo(0, 10); x.lineTo(10, 0); x.stroke();
    x.beginPath(); x.moveTo(-2, 2); x.lineTo(2, -2); x.stroke();
    x.beginPath(); x.moveTo(8, 12); x.lineTo(12, 8); x.stroke();
    return { image: c, repeat: 'repeat' };
})();
var RESIDUAL_SWATCH_CSS = 'repeating-linear-gradient(45deg,#999 0 1.5px,#f0f0f0 1.5px 7.1px)';

/* 同色系深浅：与白色按 t 混合，t=0 即原色 */
function shade(hex, t) {
    var n = parseInt(hex.slice(1), 16);
    var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    r = Math.round(r + (255 - r) * t);
    g = Math.round(g + (255 - g) * t);
    b = Math.round(b + (255 - b) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}

/* ==== 数字格式 ==== */
function thou(n) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    var s = Math.round(Math.abs(n)).toString(), out = '';
    while (s.length > 3) { out = ',' + s.slice(-3) + out; s = s.slice(0, -3); }
    return (n < 0 ? '-' : '') + s + out;
}
function fx(n, d) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    return (+n).toFixed(d === undefined ? 2 : d);
}
function pct(n, d) { return n === null || n === undefined || isNaN(n) ? '—' : fx(n, d === undefined ? 1 : d) + '%'; }
/* 源表一律人民币百万元；图上按亿元读 */
function toYi(rmbMn) { return rmbMn === null || rmbMn === undefined ? null : +(rmbMn / 100).toFixed(1); }
function yiTxt(rmbMn) { return rmbMn === null || rmbMn === undefined ? '—' : thou(rmbMn / 100) + ' 亿'; }
/* 同比：两端都有数才算，缺一端返回空串而不是 0% */
function yoy(cur, prv) {
    if (cur === null || cur === undefined || prv === null || prv === undefined || prv === 0) return null;
    return +((cur / prv - 1) * 100).toFixed(1);
}
function yoyTxt(cur, prv) {
    var v = yoy(cur, prv);
    return v === null ? '' : '同比 ' + (v > 0 ? '+' : '') + fx(v, 1) + '%';
}

/* ==== DOM 小工具 ==== */
function $(id) { return document.getElementById(id); }
function setHTML(id, html) { var el = $(id); if (el) el.innerHTML = html; }
function setText(id, txt) { var el = $(id); if (el) el.textContent = txt; }
function renderKpis(id, items) {
    setHTML(id, items.map(function (k) {
        return '<div class="kpi"><div class="label">' + k.label + '</div>'
            + '<div class="value">' + k.value + '</div>'
            + (k.delta ? '<div class="delta" style="color:' + MUTED + '">' + k.delta + '</div>' : '')
            + '</div>';
    }).join(''));
}
function renderCards(id, items) {
    setHTML(id, items.map(function (c) {
        return '<div class="card2"><h3>' + c.title + '</h3><p>' + c.body + '</p></div>';
    }).join(''));
}
function renderList(id, items) {
    setHTML(id, items.map(function (t) { return '<li>' + t + '</li>'; }).join(''));
}
function renderRows(id, rows) {
    setHTML(id, rows.map(function (r) {
        var cls = r._cls ? ' class="' + r._cls + '"' : '';
        return '<tr' + cls + '>' + r.cells.map(function (c, i) {
            return '<t' + (i === 0 && r._th ? 'h' : 'd') + '>' + c + '</t' + (i === 0 && r._th ? 'h' : 'd') + '>';
        }).join('') + '</tr>';
    }).join(''));
}

/* ==== 取数小工具：从年度字典里抽一条序列 ==== */
/* 有披露的年份（该字段非 null）；序列本身按 years 顺序保留 null，图上就是断开的点 */
function years(dict, field) {
    return Object.keys(dict).filter(function (y) {
        return dict[y] && dict[y][field] !== null && dict[y][field] !== undefined;
    }).sort();
}
function pick(dict, ys, field, conv) {
    return ys.map(function (y) {
        var v = dict[y] ? dict[y][field] : null;
        if (v === null || v === undefined) return null;
        return conv ? conv(v) : v;
    });
}
/* 某字段最后一个有披露的年份 —— 用来在图上标「自次年起不再单列」 */
function lastYear(dict, field) {
    var ys = years(dict, field);
    return ys.length ? ys[ys.length - 1] : null;
}
function firstYear(dict, field) {
    var ys = years(dict, field);
    return ys.length ? ys[0] : null;
}

/* ==== 图表：统一 init + 自适应；按 rule 不使用 dataZoom ==== */
var CHARTS = [];
function mount(id, buildOption) {
    var el = $(id);
    if (!el) return null;
    var ins = echarts.init(el);
    ins.setOption(buildOption(ins), true);
    CHARTS.push({ ins: ins, build: buildOption });
    return ins;
}
window.addEventListener('resize', function () {
    CHARTS.forEach(function (c) {
        c.ins.resize();
        c.ins.setOption(c.build(c.ins), true);
    });
});

/* 柱 + 线双轴的通用骨架 */
function axisBase(opt) {
    opt = opt || {};
    return {
        tooltip: { trigger: 'axis', textStyle: { fontSize: 17 },
                   axisPointer: { type: 'shadow' } },
        legend: { top: 4, textStyle: { fontSize: 17, color: '#444' } },
        grid: { left: opt.left || 78, right: opt.right || 78, top: opt.top || 48, bottom: opt.bottom || 40 },
        xAxis: { type: 'category', data: opt.x || [],
                 axisLabel: { fontSize: 17, color: '#555' },
                 axisLine: { lineStyle: { color: '#ccc' } } }
    };
}
function valueAxis(name, opt) {
    opt = opt || {};
    return {
        type: 'value', name: name, nameTextStyle: { fontSize: 16, color: MUTED },
        position: opt.position, offset: opt.offset,
        axisLabel: { fontSize: 16, color: '#666', formatter: opt.formatter },
        splitLine: { show: opt.splitLine !== false, lineStyle: { color: '#f0f0f0' } },
        min: opt.min, max: opt.max
    };
}

/* ==== 口径断点：把「停止披露」画成带说明的灰带 ====
 * 用法：series 上挂 markArea —— gapMark(x, '2019', null, '语音收入自2020年起不再单列')
 * from/to 用 x 轴的类目值（年份字符串）；to 为 null 表示一直到序列末端。
 * 断点不留白：读图的人看到灰带与文字，就知道这里是口径变化而不是漏数。 */
function gapMark(xs, from, to, label) {
    var end = to || xs[xs.length - 1];
    return {
        silent: true,
        itemStyle: { color: 'rgba(180,188,198,0.16)' },
        label: {
            show: true, position: 'insideTop', distance: 6,
            fontSize: 15, color: '#7b8493', formatter: label, width: 150, overflow: 'break'
        },
        data: [[{ xAxis: from }, { xAxis: end }]]
    };
}
/* 竖线标注某一年发生的口径/产品事件（如 4G 发牌、5G 商用） */
function eventMark(items) {
    return {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#c9a24a', width: 1.5, type: 'dashed' },
        label: { show: true, position: 'end', fontSize: 15, color: '#9a7b2a' },
        data: items.map(function (it) {
            return { xAxis: it.year, label: { formatter: it.text } };
        })
    };
}
