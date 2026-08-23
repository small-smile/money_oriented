/* 百度详情页公共工具 —— 供 charts/*.js 使用
 *
 * 数据来源只有一个：同目录 data.js 注入的 window.BAIDU（annual / segments / holders / profile），
 * 由 data/extract/gen_baidu_pages.py 从 data/tables/tech_09888_*.json 打包。
 * 页面里不手抄任何百分比：凡是比例都在这里由股数/金额现算。
 *
 * 与银行页的 charts/*.js 相互独立：银行那套要按 ?code= 请求 /api/company_charts 渲染上百家，
 * 百度只有一家、数据随页面一起加载，所以另起一套更简单的工具。
 */
var B = window.BAIDU || {};

/* ==== 配色：沿用 company/page.css 的深蓝 + 金 ==== */
var NAVY = '#10243e', GOLD = '#c9a24a', MUTED = '#6b7280';
var PIE_COLORS = ['#10243e', '#c9a24a', '#2980b9', '#16a085', '#c0392b', '#8e44ad',
                  '#e67e22', '#27ae60', '#2c3e50', '#c2185b', '#00838f', '#d35400'];

/* 残余项灰斜线纹理（「不可穿透」的口径统一用它），照搬 bank/charts.js 的 RESIDUAL_PATTERN */
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
function pct(n, d) { return n === null || n === undefined || isNaN(n) ? '—' : fx(n, d === undefined ? 2 : d) + '%'; }
/* 亿 / 百万：年报口径是人民币百万元，图上按需要换算 */
function toYi(rmbMn) { return rmbMn === null || rmbMn === undefined ? null : +(rmbMn / 100).toFixed(2); }

/* ==== DOM 小工具 ==== */
function $(id) { return document.getElementById(id); }
function setHTML(id, html) { var el = $(id); if (el) el.innerHTML = html; }
function setText(id, txt) { var el = $(id); if (el) el.textContent = txt; }
/* KPI 卡片：[{label, value, delta}] */
function renderKpis(id, items) {
    setHTML(id, items.map(function (k) {
        return '<div class="kpi"><div class="label">' + k.label + '</div>'
            + '<div class="value">' + k.value + '</div>'
            + (k.delta ? '<div class="delta" style="color:' + MUTED + '">' + k.delta + '</div>' : '')
            + '</div>';
    }).join(''));
}
/* 说明卡片：[{title, body}]，body 允许 HTML */
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
        /* 手画标注（graphic）的图必须重算坐标，重新 setOption 才不会错位 */
        c.ins.setOption(c.build(c.ins), true);
    });
});

/* 柱 + 线双轴的通用骨架：y 轴名称、legend、grid 一次配好 */
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
