/* 银行详情页图表脚本 · 公共底座
 *
 * 原来的单文件 charts.js 有 3100+ 行，按主题拆成了下面这些平铺脚本（都是普通全局脚本，
 * 不是 ES module，页面按顺序 <script src> 引入，charts.js 必须排在最后）：
 *
 *   charts/core.js        本文件：银行代码、initChart、跨行容错 helper、KEY_DOM、分区注册表
 *   charts/compare.js     ROE / 不良总额的可复用渲染函数（供快速切换银行按钮重绘同一张图）
 *   charts/perf.js        业绩走势、规模与资产质量、OCI、每股指标、NIM 分解
 *   charts/asset.js       资产端：金融投资、公允价值、贷款结构与投向
 *   charts/debt.js        负债端：存款成本、已发行债务证券、重定价缺口
 *   charts/risk.js        风控：盈利质量与减值、核销、五级分类、迁徙率、到期结构、权益资产比
 *   charts/shareholder.js 分红、总股本、股东户数
 *   charts/holders.js     前十大股东（含穿透）、持股集中度、可排序表格
 *   charts/intro.js       公司概览：投诉、员工人数/岗位/学历/年龄、董监高薪酬
 *   charts/statement.js   分部信息、资产负债表趋势与结构、现金流
 *   charts/switcher.js    ROE 图 / 不良总额图上方的「快速切换银行」按钮面板
 *   charts.js             入口：renderAll（前置门控 + 依次跑各分区）+ 向后端拉数据
 *
 * 各图表块的渲染代码原样保留在分区文件里，通过 __section(fn) 注册，由 charts.js 的 renderAll
 * 按注册顺序调用，参数为 (D, SELF, notes)：D 是后端 payload，SELF 是本行简称（同业对比线用），
 * notes 是按 DOM id 下发的分行说明文案。
 *
 * 图容器不在当前页时 initChart 返回 null，配合 ?. 跳过该图，不影响后面的图。
 * 本文件不绑定具体银行：银行代码取自地址栏 ?code=（缺省 601077 渝农商行），
 * 图表数据向 /api/company_charts?code=<code> 拉，页面标题/H1 由返回的 _bank 元信息拼出。 */

/* 当前页的银行代码。由后端动态渲染时（/dashboard/company/bank/*.html）已在 <head> 里注入，
 * 直接沿用；静态打开（file://）时退回解析地址栏 ?code=。只认 5~6 位数字（A 股 6 位 / H 股 5 位），
 * 非法值退回默认值，免得把地址栏里的任意字符串直接拼进请求 URL。 */
window.COMPANY_CODE = (function () {
    if (/^[0-9]{5,6}$/.test(window.COMPANY_CODE || '')) return window.COMPANY_CODE;
    var raw = new URLSearchParams(location.search).get('code') || '';
    return /^[0-9]{5,6}$/.test(raw) ? raw : '601077';
})();

/* 用后端返回的 _bank 元信息覆盖页面标题与 H1：
 * 每页 <h1 data-page="业绩"> 只声明本页栏目名，银行名/代码/年报年份来自数据，
 * 同一份 HTML 换个 ?code= 就是另一家银行的页面。HTML 里的静态文案是后端没起时的兜底。
 * 股东页切回渝农商行时会再调一次，故写成幂等的，不做缓存。 */
window.__applyBankIdentity = function (D) {
    var b = D && D._bank;
    if (!b) return;
    var h1 = document.querySelector('.page-head h1[data-page]');
    var tail = b.reportYear + ' 年报 · ' + (h1 ? h1.getAttribute('data-page') : '');
    // 纯 H 股行没有 A 股代码，只列 H 股代码，别留下「（ / 01578）」；
    // fullName 与 shortName 相同时不要写成「哈尔滨银行（哈尔滨银行）」
    var codes = [b.aCode, b.hCode].filter(function (c) { return c; }).join(' / ');
    if (h1) {
        var paren = (b.shortName && b.shortName !== b.fullName) ? b.shortName : codes;
        h1.textContent = paren ? (b.fullName + '（' + paren + '）' + tail) : (b.fullName + tail);
    }
    document.title = b.shortName + (codes ? '（' + codes + '）' : '') + tail;
};

function initChart(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    // 复用已存在的实例（股东页银行切换器会重复调用同一 render 函数），避免重复 init 告警
    return echarts.getInstanceByDom(el) || echarts.init(el);
}

/* ────── 跨行通用：本文件原本是渝农商行专用，换行后要容忍数据缺口 ────── */

// 全空的系列不进 legend 也不画：同业对比图里只有部分行有数据时，图例不该列出空线
function live(series) {
    return series.filter(s => Array.isArray(s.data) && s.data.some(v => v != null));
}

// 同业对比虚线：农业/招商/邮储四行颜色相近，交叉处只靠图例辨不清是哪条，
// 用 endLabel 在每条线右端直接贴行名，扫一眼即可对上。self 线自带逐点数值标签，不用它。
function peerLine(name, data, color) {
    return { name: name, type: 'line', data: data, smooth: true, connectNulls: true, symbolSize: 6,
             lineStyle: { width: 3, color: color, type: 'dashed' }, itemStyle: { color: color },
             endLabel: { show: true, formatter: '{a}', fontSize: 15, color: color, distance: 4 } };
}

// 固定 y 轴上限是照渝农商行量级定的，别的行超出时按最大值放宽一成，避免线被截掉
function axMax(fixed) {
    let m = 0;
    for (let i = 1; i < arguments.length; i++) {
        (arguments[i] || []).forEach(v => { if (v != null && v > m) m = v; });
    }
    return m > fixed ? Math.ceil(m * 1.1 * 10) / 10 : fixed;
}

// 该行没有这项数据时：图位保留，贴占位说明。先销毁可能已存在的 echarts 实例，
// 再摘掉 id —— 让 initChart 和各 render 函数的 DOM 守卫自动跳过这张图，避免占位被空图覆盖。
// 占位文案用内联样式兜底，base.css 里即使没有 .chart-nodata 也能居中显示。
function __stub(id) {
    var el = document.getElementById(id);
    if (!el) return;
    try { var inst = echarts.getInstanceByDom(el); if (inst) inst.dispose(); } catch (e) {}
    el.removeAttribute('id');
    el.className = 'chart-empty';
    el.innerHTML = '<div class="chart-nodata" style="display:flex;align-items:center;' +
        'justify-content:center;height:100%;min-height:120px;color:#999;font-size:18px;">' +
        '该行暂无此项数据</div>';
}

// 整页兜底：后端 404 / 拉取失败时，把当前页所有图容器都换成占位说明，页面结构不崩。
function stubAll() {
    document.querySelectorAll('[id^="chart-"]').forEach(function (el) { __stub(el.id); });
}

// 缺失的 key 用它顶上：renderAll 里 D['x'].years 这类解构不会抛异常打断后面所有图
const EMPTY_D = new Proxy({}, { get: function () { return []; } });

/* 按数据取「整」的坐标轴区间：各行量级差几个数量级（H 股股东数渝农商 ~1.4 千户、招行 ~7 万户；
 * 总股本渝农商 113 亿股、工行 3564 亿股），写死 min/max 只能合一家。
 * 区间/5 向上取到 1/2/5×10ⁿ 作步长，再把上下界对齐到步长（渝农商 H 股股东仍得 1000–1500 步长 100）。
 * pad 为额外留白的步长数：折线贴着上下边框时给一格喘息（默认 0，轴上下正好贴住数据）。 */
function niceAxis(vals, pad) {
    const v = (vals || []).filter(x => x != null);
    if (!v.length) return {};
    const lo = Math.min.apply(null, v), hi = Math.max.apply(null, v);
    const span = (hi - lo) || hi || 1;
    const mag = Math.pow(10, Math.floor(Math.log10(span / 5)));
    const step = [1, 2, 5, 10].find(m => m * mag >= span / 5) * mag;
    const p = (pad || 0) * step;
    // 步长为 0.02/0.2 这类小数时，min/max 直接算会带出浮点尾巴（15.860000000000001、
    // 60.00000000000001），ECharts 会把它原样印成刻度标签、还会多出一根重复刻度，按步长精度收一下
    const dec = Math.min(10, Math.max(0, -Math.floor(Math.log10(step))) + 2);
    const rnd = x => Number(x.toFixed(dec));
    return { min: rnd(Math.floor(lo / step) * step - p), max: rnd(Math.ceil(hi / step) * step + p),
             interval: rnd(step) };
}

/* payload key → 用到它的图容器 id。缺 key 时把这些图位换成占位说明。
 * 一个 key 供多张图（如 scale-dep 同时喂规模与资产质量五张图），故为数组。 */
const KEY_DOM = {
    'perf': ['chart-perf'],
    'roe': ['chart-roe'],
    'scale-dep': ['chart-scale-dep', 'chart-scale-loan', 'chart-npl', 'chart-overdue',
                  'chart-npl-amt', 'chart-overdue-amt', 'chart-writeoff-rate', 'chart-npl-formation', 'chart-quality'],
    'nim-trend': ['chart-nim-trend', 'chart-costincome', 'chart-creditcost',
                  'chart-provision'],
    'writeoff': ['chart-writeoff'],
    'creditamount': ['chart-creditamount'],
    'oci': ['chart-oci'],
    'pershare': ['chart-pershare'],
    'dividend-per10': ['chart-dividend-per10'],
    'holder-count': ['chart-holder-count'],
    'share-capital': ['chart-share-capital'],
    'complaint': ['chart-complaint'],
    'invest': ['chart-invest'],
    'fvtpl-mix': ['chart-fvtpl-mix'],
    'fvlevel': ['chart-fvlevel'],
    'staff': ['chart-staff'],
    'loanmix-bal': ['chart-loanmix-bal', 'chart-loanmix-yld'],
    'depterm': ['chart-depterm'],
    'depcost': ['chart-depcost', 'chart-demandratio'],
    'bondpay': ['chart-bond-bal', 'chart-bond-cost', 'chart-bond-list'],
    'repricing': ['chart-repricing'],
    'loantrend': ['chart-loantrend'],
    'perloan-bal': ['chart-perloan-bal', 'chart-perloan-npl'],
    'holders': ['chart-holders', 'chart-holders-faction', 'chart-holders-through', 'chart-holders-through-faction'],
    'holders-h': ['chart-holders-h'],
    'holders-h-only': ['chart-holders-h-only'],
    // 三张柱图共用 holder-concentration（A 股定期报告口径）；港交所 H 股年报口径走
    // holder-concentration-hist，在同一张图里作为单独的 series 披露，不另占图位，
    // 所以不进 KEY_DOM——上面的空载荷占位循环对这个 key 有特例（纯 H 股行只有 hist）
    'holder-concentration': ['chart-conc-top1', 'chart-conc-top3', 'chart-conc-top10'],
    'seg-rev': ['chart-seg-rev'],
    'geo': ['chart-geo'],
    'loan-industry': ['chart-loan-industry'],
    '5tier': ['chart-5tier'],
    'migrate': ['chart-migrate', 'chart-migrate-normal'],
    'nim': ['chart-nim'],
    'bs-trend': ['chart-bs-trend'],
    'bs': ['chart-bs'],
    'cf': ['chart-cf'],
    'staff-role': ['chart-staff-role'],
    'staff-edu': ['chart-staff-edu'],
    'staff-age': ['chart-staff-age'],
    'chairman-pay': ['chart-chairman-pay'],
    'maturity': ['chart-maturity'],
    'equity-asset': ['chart-equity-asset']
};

/* 缺失 key 的判定：renderAll 的占位门控与「逾期分档」块共用，故放在公共底座里 */
// 缺失的 key：先把对应图位改成占位说明，再塞 EMPTY_D 让后面的解构不抛异常
// 「缺」不只是 key 不存在——gen 对没数据的行常给出空数组/全空对象（如 migrate.yrsMigrate=[]），
// 这类「有 key 但没内容」也要当缺处理，否则会画出一张只有坐标轴、没有线的空图（⑥ 整改 H3）。
function __emptyPayload(v) {
    if (v == null) return true;
    if (Array.isArray(v)) return v.length === 0;
    if (typeof v === 'object') {
        var ks = Object.keys(v);
        if (!ks.length) return true;
        // 全部子值都是空数组/空/null 才算空；只要有一个非空数组或标量就当有数据
        return ks.every(function (k) {
            var x = v[k];
            return x == null || (Array.isArray(x) && x.length === 0);
        });
    }
    return false;   // 标量（数字/字符串）视为有数据
}

/* ────── 饼图统一样式 ────── */
/* 全站饼图共用一套样式，基准是股东页的「A+H 合并」图（切 tab 时圆环不跳动、标注排法也一致）：
 * 外径 68% 而不是 74%——alignTo:'edge' 给每条标注的可用宽度是「画布宽 - edgeDistance -
 * 引线终点 x」，3 点钟方向那几条最窄，外径 74% 时只剩 ~314px，装不下「全称 + 比例」的 336px；
 * minShowLabelAngle: 0 让只占一两度的小扇区也出标注；名称 / 比例拆成两段定宽富文本，
 * 同侧标注靠画布边缘右对齐成一列（不跟着扇形斜排），名字起点和小数点各自对成一条竖线，
 * minMargin 留行距免得几条小扇区标注挤成一坨。n 段 272px 按最长的一条留
 *（「香港中央结算（代理人）有限公司」18px 下 270px），改窄名字会溢出压到比例段上；
 * n + v = 336px 也已经贴着 3 点钟方向的可用宽度（1258×760 画布下约 337px），不能再加宽——
 * 也因此用这套样式的图容器必须占满整行，几百 px 宽的分栏里名字会被推出画布。
 * 圆心不写字、也不另配 legend：名称已经在标注里，圆心/图例再写一遍是重复。 */
const PIE_BASE = {
    type: 'pie', radius: ['38%', '68%'], center: ['50%', '54%'], startAngle: 90,
    sort: null, minShowLabelAngle: 0, avoidLabelOverlap: true,
    labelLine: { show: true, length: 12, length2: 10 },
    itemStyle: { borderColor: '#fff', borderWidth: 2 }
};
/* 默认 formatter 按「data.value 本身就是百分数」写（股东系列各图如此）；
 * value 是绝对值（亿元 / 百万 / 人数）的图传 labelExtra 覆盖成 p.percent。 */
const PIE_LABEL = {
    show: true, position: 'outside', fontSize: 18, color: '#333',
    alignTo: 'edge', edgeDistance: 12, minMargin: 20,
    rich: {
        n: { fontSize: 18, color: '#333', width: 272, align: 'left' },
        v: { fontSize: 18, color: '#333', width: 64, align: 'right' }
    },
    formatter: p => `{n|${p.name}}{v|${(+p.value).toFixed(2)}%}`
};
/* 各张图的 series 只写 data 和个别覆盖项，样式一律从上面两个常量来 */
function pieSeries(extra, labelExtra) {
    return [Object.assign({}, PIE_BASE, { label: Object.assign({}, PIE_LABEL, labelExtra || {}) }, extra || {})];
}
/* 标注里的比例改用 echarts 自算的 percent（value 为绝对值的图用） */
const PIE_LABEL_PCT = { formatter: p => `{n|${p.name}}{v|${p.percent.toFixed(2)}%}` };

/* 窗口尺寸变化时所有图跟着重算（脚本加载即挂，与数据无关） */

window.addEventListener('resize', () => {
    document.querySelectorAll('.chart').forEach(el => {
        const inst = echarts.getInstanceByDom(el);
        if (inst) inst.resize();
    });
});

/* ────── 分区注册表 ────── */
/* 各 charts-*.js 在加载时把自己的图表块 push 进来，charts.js 的 renderAll 拿到数据后按注册
 * 顺序依次调用。顺序即原来单文件里的书写顺序（同一分区内保持原顺序），各块之间互不依赖。 */
window.__BANK_SECTIONS = [];
function __section(fn) { window.__BANK_SECTIONS.push(fn); }
