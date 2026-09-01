/* 三大运营商公司详情页公共层 —— dashboard/company/telecom/*.html 共用
 *
 * 三家公司共用同一套页面，靠 ?code=600941|601728|600050 切换，数据全部来自
 * /api/telecom_annual?code=<code>（财务层 + ops_ 经营层 + segments 收入构成层）。
 *
 * 导航自己画（不挂 common/site-header.js）：站点导航的链接不带 query，
 * 点一下「收入构成」就会把 ?code= 丢掉退回中国移动，所以这里自建一条
 * 会保留当前 code 的导航 + 公司切换按钮，样式沿用 base.css 的 .site-nav。
 */
const TELECOM_CODES = [
    {code: '600941', name: '中国移动', color: '#1f6feb', pre: '#93c5fd'},
    {code: '601728', name: '中国电信', color: '#c0392b', pre: '#f0a9a0'},
    {code: '600050', name: '中国联通', color: '#0f766e', pre: '#7fc3bb'}
];
/* 股权结构不在这套页面里：五个板块共用 dashboard/company/bank/shareholder.html 一页，
 * 所以这里只留一个带 industry 参数的外链（q 字段），不再各行业复制一份 */
const TELECOM_PAGES = [
    {href: 'index.html', title: '业绩与财务'},
    {href: 'segment.html', title: '收入构成'},
    {href: 'operation.html', title: '运营与资本开支'},
    {href: '../bank/shareholder.html', q: 'industry=telecom', title: '股权结构'}
];
const CODE = (function () {
    const c = new URLSearchParams(location.search).get('code');
    return TELECOM_CODES.some(x => x.code === c) ? c : '600941';
})();
const META = TELECOM_CODES.find(x => x.code === CODE);

function buildTelecomNav() {
    if (document.querySelector('.site-nav')) return;
    const path = location.pathname.replace(/\/$/, '/index.html');
    const nav = document.createElement('nav');
    nav.className = 'site-nav';
    const brand = document.createElement('a');
    brand.className = 'brand';
    brand.href = '../../index.html';
    brand.textContent = '📊 行业看板';
    nav.appendChild(brand);
    for (const p of TELECOM_PAGES) {
        const a = document.createElement('a');
        a.href = p.href + '?' + (p.q ? p.q + '&' : '') + 'code=' + CODE;
        a.textContent = p.title;
        if (path.endsWith('/' + p.href.replace('../', ''))) a.className = 'active';
        nav.appendChild(a);
    }
    const gap = document.createElement('span');
    gap.style.cssText = 'flex:0 0 18px';
    nav.appendChild(gap);
    for (const c of TELECOM_CODES) {
        const a = document.createElement('a');
        a.href = location.pathname.split('/').pop() + '?code=' + c.code;
        a.textContent = c.name;
        a.style.cssText = 'border-bottom:3px solid ' + c.color;
        if (c.code === CODE) a.className = 'active';
        nav.appendChild(a);
    }
    const peers = document.createElement('a');
    peers.href = '../../industry/telecom/peers.html?focus=' + CODE;
    peers.textContent = '↗ 三家对比';
    nav.appendChild(peers);
    document.body.insertBefore(nav, document.body.firstChild);
}

function fmt(v, d) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    return v.toLocaleString('zh-CN', {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0});
}

/* 数据表里的口径说明是给人读的纯文本，里头用 **…** 标重点（JSON 里没法写 HTML）。
 * 直接塞进 innerHTML 会露出星号，这里统一转成 <b>。 */
function mdBold(s) {
    return (s || '').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
}

/* annual 里取一条序列：years 为外部给定的年份轴，scale 为除数（1e8 = 亿元）
 * src='A' 只取 A 股年报口径的年份、'PRE' 只取上市前回填的年份、null 全取 */
function seriesOf(annual, years, key, scale, src) {
    return years.map(y => {
        const rec = annual[y];
        if (!rec) return null;
        if (src && (rec.src || 'A') !== src) return null;
        const v = rec[key];
        if (v === null || v === undefined) return null;
        return +(v / (scale || 1)).toFixed(4);
    });
}

/* 年份轴：取 annual（可选再并入 extra 对象的键）里所有年份，
 * 再按 keys 里至少有一个非空值裁掉首尾空档 —— 经营层只覆盖近几年，
 * 沿用财务层 1999 年起的全区间会白留十几年空轴 */
function yearsFor(annual, keys, extra) {
    const set = new Set(Object.keys(annual || {}));
    for (const y of Object.keys(extra || {})) set.add(y);
    const all = Array.from(set).sort();
    const has = all.map(y => {
        const rec = (annual || {})[y] || {};
        if ((extra || {})[y] !== undefined) return true;
        return keys.some(k => rec[k] !== null && rec[k] !== undefined);
    });
    const from = has.indexOf(true), to = has.lastIndexOf(true);
    return from < 0 ? all : all.slice(from, to + 1);
}

function lineSeries(name, data, color, opt) {
    const o = opt || {};
    return {
        name: name, type: 'line', symbol: 'circle', symbolSize: o.dim ? 5 : 6,
        connectNulls: false, yAxisIndex: o.yAxisIndex || 0, z: 3,
        lineStyle: {width: o.width || (o.dim ? 1.6 : 2.6), type: o.type || 'solid', opacity: o.dim ? 0.6 : 1},
        itemStyle: {color: color, opacity: o.dim ? 0.6 : 1},
        emphasis: {focus: 'series'}, data: data
    };
}

function barSeries(name, data, color, opt) {
    const o = opt || {};
    return {
        name: name, type: 'bar', stack: o.stack, barMaxWidth: o.barMaxWidth || 34,
        yAxisIndex: o.yAxisIndex || 0, itemStyle: {color: color, opacity: o.opacity || 1},
        emphasis: {focus: 'series'}, data: data
    };
}

/* 通用图表壳：标题 + 图 + 常显 note（可带一个折叠的 detail），
 * 返回 ECharts 实例，页面各自 setOption */
function chartCard(host, cfg, height) {
    const wrap = document.createElement('div');
    wrap.className = 'chart-card';
    wrap.style.cssText = 'padding:14px 18px 20px; margin-bottom:20px';
    wrap.innerHTML = '<div class="chart-title">' + cfg.title +
        (cfg.sub ? '<span class="sub">' + cfg.sub + '</span>' : '') + '</div>' +
        '<div id="chart-' + cfg.id + '" style="height:' + (height || '62vh') + '"></div>' +
        (cfg.note ? '<div class="note" style="max-width:1100px;color:#6b7280;font-size:16px">' + cfg.note +
            (cfg.detail ? '<details class="note-more" style="margin-top:6px"><summary style="cursor:pointer;color:#1d4ed8;font-size:15px">' +
                '展开详细口径</summary><div style="margin-top:6px;padding-left:10px;border-left:3px solid #e5e7eb">' +
                cfg.detail + '</div></details>' : '') + '</div>' : '');
    host.appendChild(wrap);
    const chart = echarts.init(document.getElementById('chart-' + cfg.id));
    window.addEventListener('resize', () => chart.resize());
    return chart;
}

const AXIS_Y = {
    type: 'value', nameTextStyle: {fontSize: 14},
    axisLabel: {fontSize: 14, formatter: v => v.toLocaleString('zh-CN')},
    splitLine: {lineStyle: {type: 'dashed', color: '#e5e7eb'}}
};

function axisX(years) {
    return {
        type: 'category', data: years, axisTick: {alignWithLabel: true},
        axisLabel: {fontSize: 14, rotate: years.length > 18 ? 45 : 0}
    };
}

/* 竖向 markLine：口径断点／制度事件，挂在第一条 series 上 */
function marksOn(series, years, marks) {
    const data = (marks || []).filter(m => years.includes(m.year))
        .map(m => ({xAxis: m.year, label: {formatter: m.text}}));
    if (!data.length || !series.length) return series;
    series[0].markLine = {
        silent: true, symbol: 'none',
        lineStyle: {type: 'dashed', color: '#9ca3af', width: 1.4},
        label: {position: 'insideEndTop', fontSize: 13, color: '#6b7280'},
        data: data
    };
    return series;
}

function loadCompany(render) {
    buildTelecomNav();
    axios.get('/api/telecom_annual?code=' + CODE).then(function (res) {
        if (!res.data || res.data.code !== 200) throw new Error((res.data && res.data.msg) || 'load failed');
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
        render(res.data.data);
    }).catch(function (e) {
        console.error('fetch error', e);
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
        const box = document.getElementById('error-msg');
        if (box) {
            box.style.display = 'block';
            box.textContent = '数据加载失败：' + e.message + '（请确认 backend_python.py 已启动）';
        }
    });
}
