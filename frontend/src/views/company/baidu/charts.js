/* 百度详情页公共工具 —— 供 baidu/*.vue 各页 import
 *
 * 逐字搬自 dashboard/company/baidu/charts/common.js：配色、纹理、数字格式、KPI/卡片/列表/表格
 * 渲染、axisBase/valueAxis、mount 全部原样保留。仅为适配 Vue/ESM 做三处最小改动，均已标注：
 *   ① 数据来源由 <script src="data.js"> 注入 window.BAIDU 改为 import 同目录 data.js（仍逐字搬入）；
 *   ② $ 增加可选作用域（setScope）：查找限定在各页组件根 ref 内，取代整页 document.getElementById，
 *      对应「容器用模板 ref」；不设作用域时行为与原 document.getElementById 一致；
 *   ③ 去掉 common.js 里挂在 window 上的全局 resize 监听——改由各页 onMounted 收集实例、
 *      在 onBeforeUnmount 里 dispose，并各自挂 resize（见各页 .vue），对应「echarts 实例收集 dispose+resize」。
 * echarts 由 import 提供（原页是 CDN 全局）。图与数据一律不变。
 */
import * as echarts from 'echarts'
import BAIDU_DATA from './data.js'   /* 运行 data.js（其中 window.BAIDU 已逐字设置），并取默认导出 */

var B = BAIDU_DATA || {};

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
/* 改动②：查找作用域可由各页 setScope(组件根 ref) 限定，取代整页 document.getElementById。 */
var _scope = null;
function setScope(el) { _scope = el || null; }
function $(id) { return _scope ? _scope.querySelector('#' + id) : document.getElementById(id); }
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
/* 改动③：CHARTS 仍收集 {ins, build}，但不在这里挂 window resize；各页 onMounted 后取
 * CHARTS.slice() 收集本页实例，自行挂 resize（原 common.js 的 resize 逻辑逐字复现于各页）、
 * 在 onBeforeUnmount 里 dispose 并清空 CHARTS。 */
var CHARTS = [];
function mount(id, buildOption) {
    var el = $(id);
    if (!el) return null;
    var ins = echarts.init(el);
    ins.setOption(buildOption(ins), true);
    CHARTS.push({ ins: ins, build: buildOption });
    return ins;
}

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

export {
    echarts, B,
    NAVY, GOLD, MUTED, PIE_COLORS, RESIDUAL_PATTERN, RESIDUAL_SWATCH_CSS,
    shade, thou, fx, pct, toYi,
    setScope, $, setHTML, setText,
    renderKpis, renderCards, renderList, renderRows,
    CHARTS, mount, axisBase, valueAxis
}
