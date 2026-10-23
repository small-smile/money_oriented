/* 中国移动详情页公共工具 —— 供 company/cmcc 的四个 SFC import 使用。
 *
 * 逐字搬自 dashboard/company/cmcc/charts/common.js：配色、数字格式、取数小工具与
 * 图表 option 骨架（axisBase / valueAxis / gapMark / eventMark）原样保留，只改成
 * ES module 具名导出；各页 onMounted 里 import 后调用，输出与原页一致。
 *
 * 与原 common.js 的唯一差异：图表实例的 init / 收集 / resize / dispose 交给各页组件
 * 生命周期管理（见各页的 mount / charts / onBeforeUnmount），本文件不再持有全局 CHARTS 单例；
 * 取数由各页 fetch('/api/tables/telecom_00941_*.json')（成品表原文，JSON 已进 MySQL）合成 C 对象后在页内使用，
 * 字段与合并方式与原 boot.js 完全一致。DOM 工具（$ / setHTML / renderKpis 等）沿用按 id 注入。
 */

/* ==== 配色：沿用 company/page.css 的深蓝 + 金；产品世代各占一色 ==== */
export const NAVY = '#10243e', GOLD = '#c9a24a', MUTED = '#6b7280';
/* 产品世代配色：越靠后的世代越亮，堆叠图上「新业务从底部长出来」看得清 */
export const ERA_COLORS = {
    voice:     '#10243e',   /* 语音 */
    sms:       '#4a6fa5',   /* 短信及彩信 */
    data:      '#2980b9',   /* 无线上网（手机流量） */
    broadband: '#16a085',   /* 有线宽带 */
    appInfo:   '#c9a24a',   /* 应用及信息服务（含算力、智能） */
    vas:       '#8e44ad',   /* 早年「增值业务」总口径 */
    other:     '#b0bac5'    /* 其他业务（终端销售等） */
};
export const PIE_COLORS = ['#10243e', '#c9a24a', '#2980b9', '#16a085', '#c0392b', '#8e44ad',
                  '#e67e22', '#27ae60', '#2c3e50', '#c2185b', '#00838f', '#d35400'];

/* 残余项灰斜线纹理（「不可穿透」「未单列」的口径统一用它） */
export const RESIDUAL_PATTERN = (function () {
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
export const RESIDUAL_SWATCH_CSS = 'repeating-linear-gradient(45deg,#999 0 1.5px,#f0f0f0 1.5px 7.1px)';

/* ==== 数据引导：逐字对应原 boot.js —— 三份表并行 fetch，合成与 window.CMCC 同构的 C 对象 ====
 * 原 boot.js 相对 charts/ 目录取 ../../../data/tables/telecom_00941_*.json；JSON 进 MySQL 后磁盘上
 * 不再有这些文件，改由后端 /api/tables/<表名> 按原文下发（不套 {code, data}），键序与合并方式与原页一致：
 * C = { annual: <annual.json>, operating: <operating.json>, profile: <profile.json> }。不改数据。 */
export const CMCC_TABLES = {
    annual: '/api/tables/telecom_00941_annual.json',
    operating: '/api/tables/telecom_00941_operating.json',
    profile: '/api/tables/telecom_00941_profile.json'
};
export function loadCmcc() {
    var keys = Object.keys(CMCC_TABLES);
    return Promise.all(keys.map(function (k) {
        return fetch(CMCC_TABLES[k]).then(function (r) {
            if (!r.ok) throw new Error(CMCC_TABLES[k].split('/').pop() + ' HTTP ' + r.status);
            return r.json();
        });
    })).then(function (arr) {
        var C = {};
        keys.forEach(function (k, i) { C[k] = arr[i]; });
        return C;
    });
}

/* 同色系深浅：与白色按 t 混合，t=0 即原色 */
export function shade(hex, t) {
    var n = parseInt(hex.slice(1), 16);
    var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    r = Math.round(r + (255 - r) * t);
    g = Math.round(g + (255 - g) * t);
    b = Math.round(b + (255 - b) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}

/* ==== 数字格式 ==== */
export function thou(n) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    var s = Math.round(Math.abs(n)).toString(), out = '';
    while (s.length > 3) { out = ',' + s.slice(-3) + out; s = s.slice(0, -3); }
    return (n < 0 ? '-' : '') + s + out;
}
export function fx(n, d) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    return (+n).toFixed(d === undefined ? 2 : d);
}
export function pct(n, d) { return n === null || n === undefined || isNaN(n) ? '—' : fx(n, d === undefined ? 1 : d) + '%'; }
/* 源表一律人民币百万元；图上按亿元读 */
export function toYi(rmbMn) { return rmbMn === null || rmbMn === undefined ? null : +(rmbMn / 100).toFixed(1); }
export function yiTxt(rmbMn) { return rmbMn === null || rmbMn === undefined ? '—' : thou(rmbMn / 100) + ' 亿'; }
/* 同比：两端都有数才算，缺一端返回空串而不是 0% */
export function yoy(cur, prv) {
    if (cur === null || cur === undefined || prv === null || prv === undefined || prv === 0) return null;
    return +((cur / prv - 1) * 100).toFixed(1);
}
export function yoyTxt(cur, prv) {
    var v = yoy(cur, prv);
    return v === null ? '' : '同比 ' + (v > 0 ? '+' : '') + fx(v, 1) + '%';
}

/* ==== DOM 小工具 ==== */
export function $(id) { return document.getElementById(id); }
export function setHTML(id, html) { var el = $(id); if (el) el.innerHTML = html; }
export function setText(id, txt) { var el = $(id); if (el) el.textContent = txt; }
export function renderKpis(id, items) {
    setHTML(id, items.map(function (k) {
        return '<div class="kpi"><div class="label">' + k.label + '</div>'
            + '<div class="value">' + k.value + '</div>'
            + (k.delta ? '<div class="delta" style="color:' + MUTED + '">' + k.delta + '</div>' : '')
            + '</div>';
    }).join(''));
}
export function renderCards(id, items) {
    setHTML(id, items.map(function (c) {
        return '<div class="card2"><h3>' + c.title + '</h3><p>' + c.body + '</p></div>';
    }).join(''));
}
export function renderList(id, items) {
    setHTML(id, items.map(function (t) { return '<li>' + t + '</li>'; }).join(''));
}
export function renderRows(id, rows) {
    setHTML(id, rows.map(function (r) {
        var cls = r._cls ? ' class="' + r._cls + '"' : '';
        return '<tr' + cls + '>' + r.cells.map(function (c, i) {
            return '<t' + (i === 0 && r._th ? 'h' : 'd') + '>' + c + '</t' + (i === 0 && r._th ? 'h' : 'd') + '>';
        }).join('') + '</tr>';
    }).join(''));
}
/* ==== 取数小工具：从年度字典里抽一条序列 ==== */
/* 有披露的年份（该字段非 null）；序列本身按 years 顺序保留 null，图上就是断开的点 */
export function years(dict, field) {
    return Object.keys(dict).filter(function (y) {
        return dict[y] && dict[y][field] !== null && dict[y][field] !== undefined;
    }).sort();
}
export function pick(dict, ys, field, conv) {
    return ys.map(function (y) {
        var v = dict[y] ? dict[y][field] : null;
        if (v === null || v === undefined) return null;
        return conv ? conv(v) : v;
    });
}
/* 某字段最后一个有披露的年份 —— 用来在图上标「自次年起不再单列」 */
export function lastYear(dict, field) {
    var ys = years(dict, field);
    return ys.length ? ys[ys.length - 1] : null;
}
export function firstYear(dict, field) {
    var ys = years(dict, field);
    return ys.length ? ys[0] : null;
}

/* 柱 + 线双轴的通用骨架 */
export function axisBase(opt) {
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
export function valueAxis(name, opt) {
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
export function gapMark(xs, from, to, label) {
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
export function eventMark(items) {
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

