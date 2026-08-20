/* 业绩 index.html / 资产端 asset.html / 负债端 debt.html 三页共用本文件：
 * 图容器不在当前页时 initChart 返回 null，配合 ?. 跳过该图，不影响后面的图。
 *
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
    if (h1) h1.textContent = b.fullName + '（' + b.shortName + '）' + tail;
    // 纯 H 股行（如天津银行 01578）没有 A 股代码，只列 H 股代码，别留下「（ / 01578）」
    var codes = [b.aCode, b.hCode].filter(function (c) { return c; }).join(' / ');
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
                  'chart-writeoff-rate', 'chart-npl-formation', 'chart-quality'],
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
    'holders': ['chart-holders', 'chart-holders-bar'],
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

/* ────── 1.1b 加权平均 ROE（2009 年起，2018 年新准则切换断口） ──────
 * 定义在 renderAll 外面：业绩页 ROE 图上方有一排「快速切换银行」按钮，点击时拿别家银行的
 * payload 只重画这一张图（不整页重载），所以渲染逻辑必须能被独立调用。入参只用到 D['roe']。 */
window.__renderRoe = function (D) {
    const R = (D && D['roe']) || {};
    const years = R.years || [];
    // 2009–2013 简单 ROE = 归母净利润 / 平均归母权益（年报未披露加权平均值）
    // 2009 年净利润 18.88 亿、期末权益 94.77 亿：取自 2010 年 H 股招股章程 Appendix IB 会计师报告（hkexnews.hk），2008 年期末权益 78.92 亿同源
    // 2010 年 12 月 H 股上市募资致权益年内跳升，简单平均偏低；2011–2013 无重大增发，近似加权
    const roeCalc = R.roeCalc || [];
    // 旧准则「加权平均股东权益回报率」(年报披露)，2014–2018
    const roeOld = R.roeOld || [];
    // 新准则「加权平均净资产收益率」(年报披露)，自 2018 年首次执行新金融工具准则起
    const roeNew = R.roeNew || [];
    // 只有渝农商行手工补了 2009–2013 的简单 ROE，其余行该段全空——用 live() 把空系列连图例一起摘掉，
    // 免得快速切换到别家行时图例里挂着一条画不出来的线
    const roeSeries = live([
        { name: '简单ROE（净利/平均权益）', type: 'line', data: roeCalc, symbolSize: 6,
          lineStyle: { width: 2.5, color: '#af7ac5', type: 'dotted' }, itemStyle: { color: '#af7ac5' },
          label: { show: true, position: 'top', fontSize: 16, color: '#af7ac5', formatter: '{c}%' } },
        { name: 'ROE（旧准则·年报）', type: 'line', data: roeOld, symbolSize: 6,
          lineStyle: { width: 3, color: '#6c3483', type: 'dashed' }, itemStyle: { color: '#6c3483' },
          label: { show: true, position: 'top', fontSize: 16, color: '#6c3483', formatter: '{c}%' } },
        { name: 'ROE（新准则·年报）', type: 'line', data: roeNew, symbolSize: 6,
          lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
          areaStyle: { color: 'rgba(108,52,131,0.08)' },
          label: { show: true, position: 'top', fontSize: 16, color: '#6c3483', formatter: '{c}%' } }
    ]);
    initChart('chart-roe')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue} 年</b>`;
                p.forEach(x => { if (x.value != null) s += `<br>${x.marker}${x.seriesName}：${x.value}%`; });
                return s;
            } },
        legend: { data: roeSeries.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 68 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: roeSeries
    }, true);   // notMerge —— 切行时年份跨度/系列长度不同，避免残留上一行的点
};

/* ────── 1.1c ROE 一键对比：所有可切换银行画在同一张图上 ──────
 * 入参 items = [{ code, name, roe }]，roe 即各行 payload 里的 D['roe']。
 * 每行只画一条线：同一年若新旧准则都披露（2018 年）取新准则，早年缺披露值时退到简单 ROE，
 * 因为十家行叠在一起时再分三段口径会有三十条线，图上根本读不出来；口径拼接在图下说明里写清。 */
/* 银行数量已到 13 家且还会加，凑不出这么多一眼可分的颜色：用 7 色 × 实线/虚线两轮 = 14 条可辨曲线，
 * 图例本身带线型，所以第二轮的虚线在图例里也认得出是哪家 */
window.__ROE_CMP_COLORS = ['#6c3483', '#c0392b', '#1f77b4', '#e67e22', '#16a085', '#2c3e50', '#d81b60'];
window.__renderRoeCompare = function (items) {
    // 各行年份跨度不同（渝农商行自 2009，多数行自 2014/2018），取并集做横轴，缺的年份留 null 断开
    const years = Array.from(new Set(items.reduce(
        (acc, it) => acc.concat((it.roe && it.roe.years) || []), []))).sort();
    const series = items.map(function (it, i) {
        const R = it.roe || {};
        const yy = R.years || [];
        const at = function (arr, y) {
            const k = yy.indexOf(y);
            return (k < 0 || !arr) ? null : (arr[k] == null ? null : arr[k]);
        };
        const data = years.map(function (y) {
            const v = at(R.roeNew, y);
            if (v != null) return v;
            const o = at(R.roeOld, y);
            return o != null ? o : at(R.roeCalc, y);
        });
        const self = it.code === window.COMPANY_CODE;
        const P = window.__ROE_CMP_COLORS;
        const color = P[i % P.length];
        const dashed = i >= P.length;   // 第二轮改虚线，避免与第一轮同色的行混淆
        return {
            name: it.name, type: 'line', data: data, connectNulls: false,
            symbolSize: self ? 7 : 5, z: self ? 9 : 2,
            lineStyle: { width: self ? 4.5 : 2, color: color, type: dashed ? 'dashed' : 'solid' },
            itemStyle: { color: color },
            // 十条线叠在一起时点上数字会糊成一片，数值看 tooltip；只给本页银行留末端标注
            endLabel: self ? { show: true, fontSize: 16, color: color, formatter: '{c}%' } : { show: false },
            emphasis: { focus: 'series', lineStyle: { width: self ? 5.5 : 3.5 } }
        };
    });
    initChart('chart-roe')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 17 },
            // 十几家行叠一起时这块内容又高又宽，不 confine 会被鼠标带出屏幕外
            confine: true,
            formatter: p => {
                // 同一年十家行的值按高低排，一眼看出座次
                const rows = p.filter(x => x.value != null)
                    .sort((a, b) => b.value - a.value)
                    .map(x => `${x.marker}${x.seriesName}：${x.value}%`);
                return `<b>${p[0].axisValue} 年</b><br>` + (rows.join('<br>') || '无披露');
            } },
        legend: { data: series.map(s => s.name), bottom: 2, textStyle: { fontSize: 17 }, itemGap: 14 },
        grid: { left: 56, right: 72, top: 36, bottom: 108 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        // 各行 ROE 落在 5%–32%（2011 年邮储 31.8% 是上沿），从 0 起画不至于把差异压扁，
        // 也和单行模式的纵轴口径一致，切换前后读数不会产生错觉
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: series
    }, true);   // notMerge —— 与单行模式的系列结构完全不同
};

/* ────── 1. 业绩走势（2009 年起，2008 年 6 月信用社改制为股份公司致口径断口） ────── */
function renderAll(D) {
// 同业对比图里代表"本行"的那条线：换行后跟着换名字，其余同业名保持不变
const SELF = (D._bank && D._bank.shortName) || '渝农商行';

// 生成脚本按 DOM id 给出的分行说明文字（页面里的静态文案是渝农商行版本，换行后要覆盖）
const notes = D._notes || {};

/* .yns-only 里写死的是渝农商行的具体数字（标题、说明段、分红卡片）。换行后：
 *   · _notes 里有同 id 文案的 → 整段被覆盖成本行版本，留着显示；
 *   · 没有对应文案的 → 仍然是渝农商行的数字，隐藏掉。
 * .yns-h-only 是"H 股年报口径"专属块：渝农商 H 股年报只到 2018、A 股年报从 2019 起，两边没有
 * 重叠年份，所以能并排画 A/H 两套环形图；其余 A+H 行同一年两份年报都有，按 A 股优先只画 A 股，
 * 这块对它们恒定无意义，一律隐藏。 */
if (window.COMPANY_CODE !== '601077') {
    document.querySelectorAll('.yns-only').forEach(el => {
        if (!(el.id && notes[el.id])) el.style.display = 'none';
    });
    document.querySelectorAll('.yns-h-only').forEach(el => { el.style.display = 'none'; });
}

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
Object.keys(KEY_DOM).forEach(function (k) {
    if (!__emptyPayload(D[k])) return;
    // 集中度三张图还能靠港交所口径（holder-concentration-hist）单独画出来（纯 H 股行只有这一份），
    // A 股口径为空不等于整块没数据，别提前占位
    if (k === 'holder-concentration' && !__emptyPayload(D['holder-concentration-hist'])) {
        D[k] = EMPTY_D;
        return;
    }
    KEY_DOM[k].forEach(__stub);
    D[k] = EMPTY_D;
});

// 「历年股东持股集中度」是独立板块、三张图共用同一份数据：数据整份缺失时（如只有 H 股年报、
// F10 没有前十大历史的天津银行/江西银行）别留三块 400px 的"暂无数据"占位撑掉一屏，整块收起。
(function () {
    const sec = document.getElementById('sec-concentration');
    if (!sec) return;
    if (__emptyPayload(D['holder-concentration']) && __emptyPayload(D['holder-concentration-hist'])) {
        sec.style.display = 'none';
    }
})();

// 覆盖页面上的渝农商行静态文案（上面的 .yns-only 门控已经按 notes 决定了哪些块留着）
Object.keys(notes).forEach(function (id) {
    const el = document.getElementById(id);
    if (el) { el.innerHTML = notes[id]; el.style.display = ''; }
});

(function () {
    const years   = D['perf'].years;
    // 2009 年营业收入 56.77 亿、净利润 18.88 亿：取自本行 2010 年 12 月 H 股招股章程 Appendix IB 会计师报告（重组后口径）
    // 2010/2011 归母净利润按 H 股年报「歸屬於本行股東的淨利潤」原文修正为 30.64/42.47 亿（此前误取衍生值 31.13/42.71）
    const revenue = D['perf'].revenue;
    const profit  = D['perf'].profit;
    initChart('chart-perf')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                p.map(x => `${x.marker}${x.seriesName}：${x.value} 亿元`).join('<br>') },
        legend: { data: ['营业收入','归母净利润'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
            axisLabel: { fontSize: 18, color: '#555', rotate: 40 }, axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
            axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '营业收入', type: 'line', data: revenue, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '归母净利润', type: 'line', data: profit, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } }
        ]
    });
})();

/* 1.1b ROE：渲染逻辑已提到文件顶部 window.__renderRoe（供快速切换银行按钮复用） */
window.__renderRoe(D);
(function () {
    const years = D['scale-dep'].years;
    const deposit = D['scale-dep'].deposit;
    const loan    = D['scale-dep'].loan;
    const npl     = D['scale-dep'].npl;
    const nplAbc  = D['scale-dep'].nplAbc;
    const nplCmb  = D['scale-dep'].nplCmb;
    const nplPsb  = D['scale-dep'].nplPsb;          // 邮储银行 不良率%
    const overdue    = D['scale-dep'].overdue;      // 逾期率%（渝农商行）2014 起披露
    const overdueAbc = D['scale-dep'].overdueAbc;   // 农业银行
    const overdueCmb = D['scale-dep'].overdueCmb;   // 招商银行
    const overduePsb = D['scale-dep'].overduePsb;   // 邮储银行
    const woRate     = D['scale-dep'].writeoffRate;     // 核销率% = 本期核销 ÷ 贷款总额（渝农商行）2018 起披露
    const woRateAbc  = D['scale-dep'].writeoffRateAbc;  // 农业银行
    const woRateCmb  = D['scale-dep'].writeoffRateCmb;  // 招商银行
    const woRatePsb  = D['scale-dep'].writeoffRatePsb;  // 邮储银行
    const formation    = D['scale-dep'].formation;     // 不良生成率%（渝农商行）2018 起披露
    const formationAbc = D['scale-dep'].formationAbc;  // 农业银行
    const formationCmb = D['scale-dep'].formationCmb;  // 招商银行
    const formationPsb = D['scale-dep'].formationPsb;  // 邮储银行
    const car     = D['scale-dep'].car;
    const cet1    = D['scale-dep'].cet1;

    // 对数线性回归 ln(y) = a + b·t，回归增速 = exp(b) − 1；返回拟合值供画趋势线
    function logFit(vals) {
        const t = [], ly = [];
        vals.forEach((v, i) => { if (v != null && v > 0) { t.push(i); ly.push(Math.log(v)); } });
        const n = t.length, mt = t.reduce((s, x) => s + x, 0) / n, ml = ly.reduce((s, x) => s + x, 0) / n;
        let sxy = 0, sxx = 0, sst = 0;
        for (let i = 0; i < n; i++) { sxy += (t[i] - mt) * (ly[i] - ml); sxx += (t[i] - mt) ** 2; sst += (ly[i] - ml) ** 2; }
        const b = sxy / sxx, a = ml - b * mt;
        let sse = 0;
        for (let i = 0; i < n; i++) sse += (ly[i] - (a + b * t[i])) ** 2;
        return { cagr: Math.exp(b) - 1, r2: 1 - sse / sst,
                 fit: vals.map((_, i) => +Math.exp(a + b * i).toFixed(2)) };
    }
    // 线性回归 y = a + b·t，增速为固定斜率（亿元/年）
    function linFit(vals) {
        const t = [], ys = [];
        vals.forEach((v, i) => { if (v != null) { t.push(i); ys.push(v); } });
        const n = t.length, mt = t.reduce((s, x) => s + x, 0) / n, my = ys.reduce((s, x) => s + x, 0) / n;
        let sxy = 0, sxx = 0, sst = 0;
        for (let i = 0; i < n; i++) { sxy += (t[i] - mt) * (ys[i] - my); sxx += (t[i] - mt) ** 2; sst += (ys[i] - my) ** 2; }
        const b = sxy / sxx, a = my - b * mt;
        let sse = 0;
        for (let i = 0; i < n; i++) sse += (ys[i] - (a + b * t[i])) ** 2;
        return { slope: b, r2: 1 - sse / sst, fit: vals.map((_, i) => +(a + b * i).toFixed(2)),
                 rate: `+${Math.round(b).toLocaleString()} 亿/年` };
    }
    const fits = {
        log: { dep: logFit(deposit),  loan: logFit(loan)  },
        lin: { dep: linFit(deposit),  loan: linFit(loan)  }
    };
    fits.log.dep.rate = `+${(fits.log.dep.cagr * 100).toFixed(2)}%/年`;
    fits.log.loan.rate = `+${(fits.log.loan.cagr * 100).toFixed(2)}%/年`;

    // 存款、贷款各占一张图、各自回归；每张图同时画指数回归与线性回归两条趋势线
    function makeScaleChart(domId, label, vals, key, color, areaColor) {
        const chart = initChart(domId);
        if (!chart) return;                       // 存款图在负债端页、贷款图在资产端页
        const exp = fits.log[key], lin = fits.lin[key];
        chart.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                formatter: p => {
                    const i = p[0].dataIndex, act = vals[i];
                    if (act == null) return `<b>${p[0].axisValue} 年</b><br>${label}：缺口`;
                    const prev = i > 0 ? vals[i - 1] : null;
                    const yoy = prev ? ((act / prev - 1) * 100).toFixed(2) + '%' : '—';
                    const dev = f => { const d = ((act / f.fit[i] - 1) * 100).toFixed(1); return `${d > 0 ? '+' : ''}${d}%`; };
                    return `<b>${p[0].axisValue} 年</b><br>` +
                           `<span style="color:${color}">●</span> ${label}：<b>${act.toLocaleString()}</b> 亿 · 同比 ${yoy}` +
                           `<br>　指数趋势 ${exp.fit[i].toLocaleString()} 亿 · 偏离 ${dev(exp)}` +
                           `<br>　线性趋势 ${lin.fit[i].toLocaleString()} 亿 · 偏离 ${dev(lin)}`;
                } },
            legend: { data: [label, '指数回归', '线性回归'], bottom: 2, textStyle: { fontSize: 18 } },
            grid: { left: 64, right: 170, top: 30, bottom: 52 },
            xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series: [
                { name: label, type: 'line', data: vals, smooth: true, connectNulls: true, symbolSize: 6,
                  lineStyle: { width: 3, color }, itemStyle: { color },
                  areaStyle: { color: areaColor } },
                { name: '指数回归', type: 'line', data: exp.fit, symbol: 'none', z: 3, silent: true,
                  lineStyle: { width: 2, type: 'dashed', color, opacity: 0.8 }, itemStyle: { color },
                  endLabel: { show: true, fontSize: 18, color, distance: 6,
                      formatter: `指数 ${exp.rate}` } },
                { name: '线性回归', type: 'line', data: lin.fit, symbol: 'none', z: 3, silent: true,
                  lineStyle: { width: 2, type: 'dotted', color: '#7f8c8d' }, itemStyle: { color: '#7f8c8d' },
                  endLabel: { show: true, fontSize: 18, color: '#7f8c8d', distance: 6,
                      formatter: `线性 ${lin.rate}` } }
            ]
        });
        document.getElementById('fit-note-' + key).innerHTML =
            `指数回归 ln(y)=a+b·t：<b>${exp.rate}</b>（R²=${exp.r2.toFixed(3)}）` +
            ` · 线性回归 y=a+b·t：<b>${lin.rate}</b>（R²=${lin.r2.toFixed(3)}）`;
    }
    makeScaleChart('chart-scale-dep',  '客户存款',      deposit, 'dep',  '#6c3483', 'rgba(108,52,131,0.08)');
    makeScaleChart('chart-scale-loan', '客户贷款及垫款', loan,    'loan', '#e67e22', 'rgba(230,126,34,0.08)');

    // 同业四行里本行那条实线名字随 ?code= 变；同业线若本行自己就是该行会重复，live() 只滤空线，重名无害
    const serNpl = live([
        { name: SELF, type: 'line', data: npl, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
          areaStyle: { color: 'rgba(192,57,43,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
        peerLine('农业银行', nplAbc, '#2874a6'),
        peerLine('招商银行', nplCmb, '#229954'),
        peerLine('邮储银行', nplPsb, '#d68910')
    ]);
    initChart('chart-npl')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: serNpl.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '不良率%', min: 0, max: axMax(3, npl, nplAbc, nplCmb, nplPsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serNpl
    });

    // 逾期率 = 逾期贷款 / 贷款总额（各行年报「贷款质量—逾期贷款」披露，渝农商 2014 起有此项）
    const serOd = live([
        { name: SELF, type: 'line', data: overdue, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
          areaStyle: { color: 'rgba(230,126,34,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#e67e22', formatter: '{c}%' } },
        peerLine('农业银行', overdueAbc, '#2874a6'),
        peerLine('招商银行', overdueCmb, '#229954'),
        peerLine('邮储银行', overduePsb, '#d68910')
    ]);
    initChart('chart-overdue')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serOd.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '逾期率%', min: 0, max: axMax(3.5, overdue, overdueAbc, overdueCmb, overduePsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#e67e22', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serOd
    });

    // 核销率 = 本期核销（含其他转出） ÷ 发放贷款和垫款总额（各行年报「贷款减值准备变动」披露本期核销额）
    const serWo = live([
        { name: SELF, type: 'line', data: woRate, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#8e44ad' }, itemStyle: { color: '#8e44ad' },
          areaStyle: { color: 'rgba(142,68,173,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#8e44ad', formatter: '{c}%' } },
        peerLine('农业银行', woRateAbc, '#2874a6'),
        peerLine('招商银行', woRateCmb, '#229954'),
        peerLine('邮储银行', woRatePsb, '#d68910')
    ]);
    initChart('chart-writeoff-rate')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serWo.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '核销率%', min: 0, max: axMax(2.2, woRate, woRateAbc, woRateCmb, woRatePsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#8e44ad', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serWo
    });

    // 不良生成率 = 不良生成额 ÷ 期初贷款总额（不良生成额 = 期末不良 − 期初不良 + 核销净额），衡量新增不良的速度
    const serFm = live([
        { name: SELF, type: 'line', data: formation, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
          areaStyle: { color: 'rgba(192,57,43,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
        peerLine('农业银行', formationAbc, '#2874a6'),
        peerLine('招商银行', formationCmb, '#229954'),
        peerLine('邮储银行', formationPsb, '#d68910')
    ]);
    initChart('chart-npl-formation')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serFm.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '不良生成率%', min: 0,
                 max: axMax(3, formation, formationAbc, formationCmb, formationPsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serFm
    });

    initChart('chart-quality')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['资本充足率', '核心一级资本充足率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 20, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, max: axMax(18, car, cet1), nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '资本充足率', type: 'line', data: car, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '核心一级资本充足率', type: 'line', data: cet1, smooth: true, connectNulls: true, symbolSize: 5,
              lineStyle: { width: 2, color: '#27ae60', type: 'dashed' }, itemStyle: { color: '#27ae60' } }
        ]
    });
})();

/* ────── 1e. 盈利质量与效率（2010–2025） ────── */
(function () {
    const years10  = D['nim-trend'].years10;
    // NIM/NIS：H 股 03618 历年年报「財務摘要—盈利能力指標」及本行 2010–2025 年年度报告披露值
    // 2018 年改用新准则（IFRS9）值 2.45/2.40（此前误取"經調整"IAS39 口径 2.65/2.44，与后续年份口径不一致）
    const nim  = D['nim-trend'].nim;
    const nis  = D['nim-trend'].nis;

    initChart('chart-nim-trend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['净息差 NIM', '净利差 NIS'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years10, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '净息差 NIM', type: 'line', data: nim, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '净利差 NIS', type: 'line', data: nis, smooth: true, connectNulls: true, symbolSize: 5,
              lineStyle: { width: 2, color: '#9b59b6', type: 'dashed' }, itemStyle: { color: '#9b59b6' } }
        ]
    });

    // 非息收入占比：2010–2018 由 H 股年报「淨利息收入佔營業收入總額」反算（100% − 该比率）；2019–2025 为本行年报「非利息净收入/营业收入」披露值
    // 2018 年为 H 股口径 23.29%，A 股 2019 年报比较列重述为 23.37%（此处衔接 2019 起的 A 股序列口径取 23.37%）
    const nonInt     = D['nim-trend'].nonInt;
    // 成本收入比：2010–2017 为 H 股年报「成本佔收入比率」披露值（总营业支出扣除税金及附加/其他业务成本 ÷ 营业收入）；2018–2025 为本行年报「成本收入比」披露值（业务及管理费/营业收入），两段定义不同、不完全可比
    const costIncome = D['nim-trend'].costIncome;

    initChart('chart-costincome')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['非息收入占比', '成本收入比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years10, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '非息收入占比', type: 'line', data: nonInt, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#16a085' }, itemStyle: { color: '#16a085' } },
            { name: '成本收入比', type: 'line', data: costIncome, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } }
        ]
    });

    const yearsCC  = D['nim-trend'].yearsCC;
    // 旧准则「资产减值损失 / 营业收入」(2010–2017)——港股 03618 年报英文合并利润表 Impairment losses on assets / Operating income
    // 2010 为减值净转回(+45.2 百万), 故比率为负
    const impOld   = D['nim-trend'].impOld;
    // 新准则「信用减值损失 / 营业收入」(2018–2025)——A股年报, 2018 年起执行 IFRS9/新金融工具准则
    const impNew   = D['nim-trend'].impNew;

    function baseSeries() {
        return [
            { name: '资产减值/营收（旧准则）', type: 'line', data: impOld, smooth: true, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
              label: { show: true, fontSize: 18, color: '#e67e22', formatter: '{c}%' } },
            { name: '信用减值/营收（新准则）', type: 'line', data: impNew, smooth: true, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' },
              label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } }
        ];
    }
    function creditcostOption(series) {
        return {
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '—' : v + '%' },
            legend: { data: series.map(s => s.name), top: 4, textStyle: { fontSize: 18 } },
            grid: { left: 48, right: 24, top: 46, bottom: 52 },
            xAxis: { type: 'category', data: yearsCC, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
            yAxis: { type: 'value', name: '%', nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series
        };
    }
    // 只展示渝农商行单行数据（新旧准则两段），不再与天津银行/农业银行横向对比
    initChart('chart-creditcost')?.setOption(creditcostOption(baseSeries()));

    const years13   = D['nim-trend'].years13;
    const provCov13 = D['nim-trend'].provCov13;
    const provRatio = D['nim-trend'].provRatio;

    initChart('chart-provision')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['拨备覆盖率', '拨贷比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 64, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years13, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '拨备覆盖率%', min: 0, nameTextStyle: { color: '#1e8449', fontSize: 18 },
              axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '拨贷比%', min: 0, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '拨备覆盖率', type: 'line', data: provCov13, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' },
              areaStyle: { color: 'rgba(30,132,73,0.08)' } },
            { name: '拨贷比', type: 'line', yAxisIndex: 1, data: provRatio, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' } }
        ]
    });
})();

/* ────── 10b. 贷款核销与收回（2018–2025，人民币百万元） ────── */
(function () {
    // 取自本行 2018-2025 年年度报告「贷款减值准备变动」附注（HKEXnews 03618.HK / cqrcb.com 官网 PDF），2026-08-14 核对
    // 2022 年起「本期核销」「收回已核销」分项披露；2018-2021 仅披露合并净额（本期核销及其他转出），以净核销虚线呈现
    const yearsWO   = D['writeoff'].yearsWO;
    const writeOff  = D['writeoff'].writeOff;
    const recovery  = D['writeoff'].recovery;
    const netWO     = D['writeoff'].netWO;
    initChart('chart-writeoff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 百万' },
        legend: { data: ['本期核销', '收回已核销', '净核销（2018–2021）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: yearsWO, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '人民币百万元', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
                 axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '本期核销', type: 'line', data: writeOff, connectNulls: true, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' } },
            { name: '收回已核销', type: 'line', data: recovery, connectNulls: false, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '净核销（2018–2021）', type: 'line', data: netWO, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 2, color: '#8e8e8e', type: 'dashed' }, itemStyle: { color: '#8e8e8e' } }
        ]
    });
})();

/* ────── 10c. 信用减值损失绝对值与总资产占比（2010–2025，人民币百万元） ────── */
(function () {
    const years16 = D['creditamount'].years16;
    // 资产减值损失(2010-2017,旧准则)/信用减值损失(2018-2025,新准则)绝对值——本行/H股03618历年年报「财务摘要」，与已披露的减值/营收比率反算核对一致
    // 2010 年为净转回(-45.2百万)
    const impAmt = D['creditamount'].impAmt;
    // 资产总额（年末数）——同上来源「财务摘要」；2018 年取 A 股 2019 年报比较列口径（950,177.9），与 2019 年起序列衔接
    const totalAssetsY = D['creditamount'].totalAssetsY;
    const impOverAsset = impAmt.map((v, i) => +(v / totalAssetsY[i] * 100).toFixed(2));

    initChart('chart-creditamount')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                p.map(x => x.seriesName === '信用减值/总资产'
                    ? `${x.marker}${x.seriesName}：${x.value}%`
                    : `${x.marker}${x.seriesName}：${x.value} 百万元`).join('<br>') },
        legend: { data: ['信用减值损失（绝对值）', '信用减值/总资产'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 72, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years16, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '百万元', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '%', nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '信用减值损失（绝对值）', type: 'line', data: impAmt, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' } },
            { name: '信用减值/总资产', type: 'line', yAxisIndex: 1, data: impOverAsset, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' } }
        ]
    });
})();

/* ────── 1i. 其他综合收益（OCI）与净利润 ────── */
(function () {
    const years16  = D['oci'].years16;
    const oci      = D['oci'].oci;
    initChart('chart-oci')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 亿' },
        legend: { data: ['其他综合收益'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 64, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years16, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '其他综合收益(亿元)', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '其他综合收益', type: 'line', data: oci, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' },
              markLine: {
                  symbol: 'none', silent: true,
                  lineStyle: { color: '#8e8e8e', type: 'dashed', width: 1.5 },
                  label: { formatter: '2018 IFRS9 新准则', position: 'end', distance: 6,
                           fontSize: 16, color: '#8e8e8e' },
                  data: [
                      { xAxis: '2018' },
                      { yAxis: 0, lineStyle: { color: '#bbb', type: 'solid', width: 1 },
                        label: { show: false } }
                  ]
              },
              markPoint: {
                  symbol: 'circle', symbolSize: 11, silent: true,
                  label: { fontSize: 16, fontWeight: 'bold', position: 'left', distance: 8,
                           formatter: '{c} 亿' },
                  data: [
                      { type: 'max', name: '最大', itemStyle: { color: '#c0392b' },
                        label: { color: '#c0392b' } },
                      { type: 'min', name: '最小', itemStyle: { color: '#2c6fb3' },
                        label: { color: '#2c6fb3' } }
                  ]
              } }
        ]
    });
})();

/* ────── 1j. 每股指标 EPS / BVPS ────── */
(function () {
    const years16 = D['pershare'].years16;
    const eps  = D['pershare'].eps;
    // BVPS：港交所 03618 历年年报「歸屬於本行股東的每股淨資產」披露值（2010 年为加权口径，2011 起为期末口径）
    const bvps = D['pershare'].bvps;

    initChart('chart-pershare')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 元' },
        legend: { data: ['基本每股收益(EPS)', '每股净资产(BVPS)'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 60, right: 60, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years16, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: 'EPS(元)', min: 0, nameTextStyle: { color: '#6c3483', fontSize: 18 },
              axisLabel: { color: '#6c3483', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: 'BVPS(元)', min: 0, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '基本每股收益(EPS)', type: 'line', data: eps, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              endLabel: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}' } },
            { name: '每股净资产(BVPS)', type: 'line', yAxisIndex: 1, data: bvps, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1j2. 历年每 10 股分红（元，含税，按年度累计） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsDividend）重绘。 */
window.__renderYnsDividend = function (D) {
    if (!document.getElementById('chart-dividend-per10')) return;   // 仅股东页
    // 2011–2018：03618 港股年报「盈利与股息」披露的内资股/H股每股派息（元）× 10；2010 年董事会未提常规股息（仅 IPO 前特别股息，口径不可比，未纳入）
    // 2019–2025：本行 A 股年度报告「利润分配方案」披露的每 10 股股利
    const years9 = D['dividend-per10'].years9;
    const per10  = D['dividend-per10'].per10;

    initChart('chart-dividend-per10')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 元' },
        grid: { left: 60, right: 40, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years9, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '每10股分红(元)', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
                 axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '每10股分红(含税)', type: 'bar', data: per10, itemStyle: { color: '#c0392b' },
              barMaxWidth: 44,
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}' } }
        ]
    });
};
window.__renderYnsDividend(D);

/* ────── 1j2b. 历年总股本变动（IPO / 定增 / 增发等资本运作导致的股份数量变化） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsShareCapital）重绘。
 * 载荷 D['share-capital'] = { years, shares(亿股), gaps?, base?, events? }：
 *   · years/shares 为逐年年末总股本，来自资产负债表「股本」科目（面值 1 元，元金额即股数）；
 *   · gaps 为该行披露缺失、整年剔除的年份（如农行 2002–2006），只写进脚注不插值；
 *   · base 为首年之前的期初股本（渝农商 2008 改制时 60 亿股），有它首年才画得出增量；
 *   · events 为 {年: {type, items[]}} 的手工明细（只有渝农商精编了 5 次资本运作的成因）。
 * 生成脚本给不出成因分类（F10 只有股本余额），故 events 缺失时全部点用中性色，
 * 增量标签也只在变动幅度 ≥ 上年 0.1% 时才显示——否则四舍五入的尾差会糊满全图。 */
window.__renderYnsShareCapital = function (D) {
    if (!document.getElementById('chart-share-capital')) return;   // 仅股东页
    const SC = (D && D['share-capital']) || {};
    const years = SC.years || [];
    if (!years.length) { __stub('chart-share-capital'); return; }
    const shares = SC.shares || [];
    const C = { base:'#95a5a6', ipo:'#c0392b', pp:'#e67e22', seo:'#16a085' };
    const EV = SC.events || {};
    let prev = SC.base != null ? SC.base : null;
    const rows = years.map((y, i) => {           // [年, 年末总股本, 当年增量(null=无从计算), 明细[], 色]
        const cur = shares[i];
        const ev = EV[y] || EV[String(y)];
        const d = prev == null ? null : +(cur - prev).toFixed(2);
        prev = cur;
        return [y, cur, d, ev ? (ev.items || []) : [], ev ? (C[ev.type] || C.base) : C.base];
    });
    // 「显著变动」阈值：上年股本的 0.1%（工行 3564 亿股约 3.5 亿股），滤掉四舍五入尾差
    const moved = rows.map((r, i) => r[2] != null && Math.abs(r[2]) >= (i ? shares[i - 1] : r[1]) * 0.001);
    const ax = niceAxis(shares, 1);
    const cum = rows.map(r => ({ value: r[1], itemStyle: { color: r[4] }, label: { color: r[4] } }));
    initChart('chart-share-capital')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: {
            trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex, r = rows[i];
                const detail = r[3].length
                    ? '<br><span style="color:#888">' + r[3].join('<br>') + '</span>'
                    : (moved[i] ? '' : '<br><span style="color:#888">当年无股本变动</span>');
                const dLine = r[2] == null ? ''
                    : '<br>当年增量：' + (moved[i] ? (r[2] > 0 ? '+' : '') + r[2].toFixed(2) + ' 亿股' : '无');
                return `<b>${r[0]} 年末</b><br>总股本：${r[1].toFixed(2)} 亿股` + dLine + detail;
            }
        },
        grid: { left: 88, right: 60, top: 40, bottom: 46 },
        xAxis: {
            type: 'category', data: years, boundaryGap: false,
            axisLabel: { fontSize: 15, color: '#555',
                         interval: Math.max(0, Math.ceil(years.length / 24) - 1) },
            axisLine: { lineStyle: { color: '#bbb' } },
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value', name: '总股本（亿股）',
            min: ax.min, max: ax.max, interval: ax.interval,
            nameTextStyle: { color: '#555', fontSize: 18 },
            axisLabel: { color: '#555', fontSize: 18 },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: [{
            name: '总股本', type: 'line', step: 'end', data: cum,
            symbolSize: 11, lineStyle: { width: 3, color: '#6c3483' },
            areaStyle: { color: 'rgba(108,52,131,0.08)' },
            label: {
                show: true, position: 'top', fontSize: 15, fontWeight: 600,
                formatter: p => {
                    const d = rows[p.dataIndex][2];
                    return moved[p.dataIndex] ? (d > 0 ? '+' : '') + d.toFixed(2) : '';
                }
            },
            endLabel: { show: true, fontSize: 16, color: '#6c3483',
                        formatter: p => `${p.value} 亿股` }
        }]
    }, true);   // notMerge —— 切行时年份跨度不同，避免残留上一行的点
};
window.__renderYnsShareCapital(D);

/* ────── 1j3. 历年股东户数（2017-12 至今：H 股年报 + 历年定期报告披露值） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolderCount）重绘。 */
window.__renderYnsHolderCount = function (D) {
    if (!document.getElementById('chart-holder-count')) return;   // 仅股东页
    // [披露日, 股东总数, A 股股东, H 股股东] —— A/H 部分披露点未拆分, 保留 null
    // 数据源:
    //   · A 股 IPO 后 (2019-10 至今, 43 期): 本行历年定期报告（年报/中报/季报）「股东情况」章节披露值
    //   · A 股 IPO 前 H 股登记股东数 (2017/2018 年末, 2 期): 03618 港股年报「股本变动及股东情况」章节脚注
    //     -> data/tables/holder_count_hshare_2010_2018.json  (2010-2016 年报未披露该项)
    const raw = D['holder-count'].raw;
    const dates  = raw.map(r => r[0]);
    const total  = raw.map(r => r[1]);
    const aNum   = raw.map(r => r[2]);
    const hNum   = raw.map(r => r[3]);
    const fmt    = v => v == null ? '—' : v.toLocaleString('en-US');
    const wan    = v => v == null ? '—' : (v / 10000).toFixed(2) + ' 万';

    // 左轴单位随各行量级：大行 A 股几十万户按万户标，户数少的行直接按户标
    const inWan  = (D['holder-count'].unit || 'wan') === 'wan';
    const aName  = 'A 股股东数（左轴 · ' + (inWan ? '万户' : '户') + '）';

    /* H 股登记股东数各行差两三个数量级（渝农商 ~1.4 千户、招行 ~7 万户），
     * 原来写死的 1000/1500/100 只合渝农商；改用顶层 niceAxis 按数据取「整」区间。 */
    const hAx = niceAxis(hNum);

    /* 主线按各行实际披露的列挑：
     *   · 多数期次只有股东总数、没有 A/H 拆分（工行/中行/交行的早年季报）→ 主线用股东总数；
     *   · 纯 H 股上市行（天津银行 01578）年报只有 H 股登记股东数，总数与 A 股列整列为空
     *     → 把 H 股序列提为左轴主线并收起右轴，否则左轴一条线都画不出来。 */
    const uHu = inWan ? '万户' : '户';
    const aAll = aNum.every(v => v == null);
    const hOnly = aAll && total.every(v => v == null);
    const main = hOnly ? hNum : (aAll ? total : aNum);
    const mainName = hOnly ? ('H 股登记股东数（左轴 · ' + uHu + '）')
                   : aAll ? ('股东总数（A+H · 左轴 · ' + uHu + '）') : aName;

    const serHC = live([{
        name: mainName,
        type: 'line', data: main, smooth: true, symbolSize: 6,
        connectNulls: false,      // A 股仅定期报告披露, 未拆分的季报点留空断线
        lineStyle: { width: 3, color: '#2c6fb3' },
        itemStyle: { color: '#2c6fb3' },
        areaStyle: { color: 'rgba(44,111,179,0.10)' },
        endLabel: { show: true, fontSize: 18, color: '#2c6fb3',
                    formatter: p => p.value == null ? '' :
                        (inWan ? (p.value / 10000).toFixed(2) + ' 万' : p.value.toLocaleString('en-US') + ' 户') }
    }, {
        name: 'H 股登记股东数（右轴 · 户）',
        type: 'line', yAxisIndex: 1, data: hOnly ? [] : hNum,   // 已提为左轴主线时不再重复画
        smooth: true, symbolSize: 8,
        connectNulls: true,       // H 股只在年末/半年末披露, 跨越缺口连线
        lineStyle: { width: 2.5, color: '#16a085', type: 'solid' },
        itemStyle: { color: '#16a085' },
        endLabel: { show: true, fontSize: 16, color: '#16a085',
                    formatter: p => p.value == null ? '' : `${p.value.toLocaleString('en-US')} 户` }
    }]);

    initChart('chart-holder-count')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        legend: {
            data: serHC.map(s => s.name),
            top: 4, left: 'center', textStyle: { fontSize: 16 },
            icon: 'roundRect'
        },
        tooltip: {
            trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex;
                // 找出前一个有 total 值的披露点用于环比
                let prev = null;
                for (let k = i - 1; k >= 0; k--) { if (total[k] != null) { prev = total[k]; break; } }
                const chg  = (prev == null || total[i] == null) ? '' :
                             (total[i] - prev >= 0 ? '+' : '') + (total[i] - prev).toLocaleString('en-US');
                const pct  = (prev == null || total[i] == null) ? '' :
                             ((total[i] - prev) / prev * 100).toFixed(2) + '%';
                const totalLine = total[i] == null
                    ? `股东总数：— <span style="color:#888">（A 股尚未上市）</span>`
                    : `股东总数：${fmt(total[i])} 户（${wan(total[i])}）` +
                      (prev == null ? '' : `<br>环比：${chg} 户（${pct}）`);
                return `<b>${dates[i]}</b><br>` + totalLine +
                       (aNum[i] != null ? `<br>其中 A 股：${fmt(aNum[i])} 户` : '') +
                       (hNum[i] != null ? `<br>H 股登记股东：${fmt(hNum[i])} 户` : '');
            }
        },
        grid: { left: 88, right: 160, top: 56, bottom: 70 },
        xAxis: {
            type: 'category', data: dates, boundaryGap: false,
            // 披露期数各行差得远（渝农商 43 期、工行 93 期），固定 interval:2 在大行上会糊成一片
            axisLabel: { fontSize: 16, color: '#555', rotate: 40,
                         interval: Math.max(2, Math.ceil(dates.length / 18) - 1) },
            axisLine: { lineStyle: { color: '#bbb' } }
        },
        yAxis: [
            {
                type: 'value',
                name: (hOnly ? 'H 股登记股东（' : aAll ? '股东总数（' : 'A 股股东数（') + uHu + '）',
                min: 0, position: 'left',
                nameTextStyle: { color: '#2c6fb3', fontSize: 18 },
                axisLabel: { color: '#2c6fb3', fontSize: 18,
                             formatter: v => inWan ? (v / 10000).toFixed(0) : v.toLocaleString('en-US') },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            {
                type: 'value', name: 'H 股股东（户）', show: !hOnly && hAx.min != null,
                min: hAx.min, max: hAx.max, interval: hAx.interval,
                position: 'right',
                nameTextStyle: { color: '#16a085', fontSize: 18 },
                axisLabel: { color: '#16a085', fontSize: 18, formatter: v => v.toLocaleString('en-US') },
                splitLine: { show: false }
            }
        ],
        series: serHC
    });
};
window.__renderYnsHolderCount(D);

/* ────── 1j4. 历年处理消费投诉数（件）与客户满意度（%） ────── */
(function () {
    if (!document.getElementById('chart-complaint')) return;   // 仅简介页
    const years3 = D['complaint'].years3;
    const complaints   = D['complaint'].complaints;
    const satisfaction = D['complaint'].satisfaction;

    initChart('chart-complaint')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 } },
        legend: { data: ['处理消费投诉数', '消费投诉处理客户满意度'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 60, right: 60, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years3, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '投诉数(件)', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '满意度(%)', min: 0, max: 100, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '处理消费投诉数', type: 'bar', data: complaints, itemStyle: { color: '#c0392b' },
              barMaxWidth: 60,
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '消费投诉处理客户满意度', type: 'line', yAxisIndex: 1, data: satisfaction, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#2980b9' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}%' } }
        ]
    });
})();


/* ────── 1k. 金融投资分类结构 AC / FVOCI / FVTPL ────── */
(function () {
    const years8 = D['invest'].years8;
    const ac        = D['invest'].ac;
    const fvociDebt = D['invest'].fvociDebt;
    const fvociEq   = D['invest'].fvociEq;
    const fvtpl     = D['invest'].fvtpl;

    initChart('chart-invest')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   valueFormatter: v => v + ' 亿' },
        legend: { data: ['债权投资(AC/摊余成本)', '其他债权投资(FVOCI债)', '其他权益工具(FVOCI股)', '交易性金融资产(FVTPL)'],
                  bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years8, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '债权投资(AC/摊余成本)', type: 'bar', stack: 'inv', data: ac, itemStyle: { color: '#2980b9' } },
            { name: '其他债权投资(FVOCI债)', type: 'bar', stack: 'inv', data: fvociDebt, itemStyle: { color: '#16a085' } },
            { name: '其他权益工具(FVOCI股)', type: 'bar', stack: 'inv', data: fvociEq, itemStyle: { color: '#f39c12' } },
            { name: '交易性金融资产(FVTPL)', type: 'bar', stack: 'inv', data: fvtpl, itemStyle: { color: '#c0392b' } }
        ]
    });
})();

/* ────── 1k-2. FVTPL 内部构成（本集团, 亿元, 2025 vs 2024） ────── */
(function () {
    // 2025年报附注「金融投资(1) 交易性金融资产」(第55页), 千元 → 亿元
    const cats  = D['fvtpl-mix'].cats;
    const y2025 = D['fvtpl-mix'].y2025;
    const y2024 = D['fvtpl-mix'].y2024;

    initChart('chart-fvtpl-mix')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   valueFormatter: v => v + ' 亿' },
        legend: { data: ['2025 年末', '2024 年末'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 116, right: 84, top: 20, bottom: 48 },
        xAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: cats, axisLabel: { fontSize: 18, color: '#555' } },
        series: [
            { name: '2025 年末', type: 'bar', data: y2025, itemStyle: { color: '#c0392b' },
              label: { show: true, position: 'right', fontSize: 18, color: '#c0392b' } },
            { name: '2024 年末', type: 'bar', data: y2024, itemStyle: { color: '#e8a49c' } }
        ]
    });
})();

/* ────── 1k-3. 公允价值计量层级 L1/L2/L3（本集团, 亿元） ────── */
(function () {
    // 2025年报附注「公允价值层次」(第139页), 千元 → 亿元
    const years = D['fvlevel'].years;
    const l1  = D['fvlevel'].l1;
    const l2  = D['fvlevel'].l2;
    const l3  = D['fvlevel'].l3;
    const tot = D['fvlevel'].tot;

    initChart('chart-fvlevel')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: {
            trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex;
                return p[0].name + '　合计 ' + tot[i].toFixed(2) + ' 亿<br>' + p.map(s =>
                    s.marker + s.seriesName + '：<b>' + s.value.toFixed(2) + ' 亿</b>（' +
                    (s.value / tot[i] * 100).toFixed(1) + '%）').join('<br>');
            }
        },
        legend: { data: ['第一层次 L1', '第二层次 L2', '第三层次 L3'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 84, right: 30, top: 30, bottom: 48 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '第一层次 L1', type: 'bar', stack: 'fv', barWidth: '46%', data: l1,
              itemStyle: { color: '#2980b9' } },
            { name: '第二层次 L2', type: 'bar', stack: 'fv', data: l2, itemStyle: { color: '#16a085' } },
            { name: '第三层次 L3', type: 'bar', stack: 'fv', data: l3, itemStyle: { color: '#f39c12' },
              label: { show: true, position: 'top', fontSize: 18, color: '#555',
                       formatter: p => '合计 ' + tot[p.dataIndex].toFixed(0) + ' 亿' } }
        ]
    });
})();

/* ────── 1l. 员工人数与人均效能 ────── */
(function () {
    const years15 = D['staff'].years15;
    // 员工数：2011–2018 为本行口径「在岗员工」（H 股年报「員工及人力資源管理」）；2019–2025 为本集团口径「在岗员工」（A 股年报「员工和机构情况」，含子公司），2018→2019 口径切换处不连续
    const staff = D['staff'].staff;
    // 人均营业收入/人均归母净利润 = 营业收入/归母净利润(本行历年年度报告「合并利润表」披露值) ÷ 对应口径员工数
    const perOI = D['staff'].perOI;
    const perNP = D['staff'].perNP;

    initChart('chart-staff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   formatter: p => {
                       const rows = p.map(s => s.seriesName + '：' + s.value +
                           (s.seriesName === '年末员工数' ? ' 人' : ' 万元/人'));
                       return p[0].axisValue + '<br>' + rows.join('<br>');
                   } },
        legend: { data: ['年末员工数', '人均营业收入', '人均归母净利润'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 66, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years15, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '员工数(人)', min: 0, nameTextStyle: { color: '#95a5a6', fontSize: 18 },
              axisLabel: { color: '#95a5a6', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '万元/人', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#555', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '年末员工数', type: 'bar', data: staff, itemStyle: { color: '#d5dbdb' },
              barWidth: '55%', z: 1 },
            { name: '人均营业收入', type: 'line', yAxisIndex: 1, data: perOI, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '人均归母净利润', type: 'line', yAxisIndex: 1, data: perNP, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
              endLabel: { show: true, fontSize: 18, color: '#e67e22', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1c. 公司/个人 存贷款结构与利率 ────── */
(function () {
    const loanYears = D['loanmix-bal'].loanYears;
    // 公司贷款 / 零售贷款 / 票据贴现 / 合计 平均余额（亿元），取自各年年报「利息收入分析」表
    const balCorp = D['loanmix-bal'].balCorp;
    const balRetail = D['loanmix-bal'].balRetail;
    const balBill = D['loanmix-bal'].balBill;
    const balTotal = D['loanmix-bal'].balTotal;
    // 同表平均收益率（%）
    const yldCorp = D['loanmix-bal'].yldCorp;
    const yldRetail = D['loanmix-bal'].yldRetail;
    const yldBill = D['loanmix-bal'].yldBill;
    const yldTotal = D['loanmix-bal'].yldTotal;
    const loanMixNames = ['公司贷款', '个人(零售)贷款', '票据贴现', '客户贷款合计'];
    const loanMixColors = ['#6c3483', '#2980b9', '#16a085', '#c0392b'];
    const loanMixLine = (name, data, color, unit, dy) => ({
        name, type: 'line', data, symbolSize: name === '客户贷款合计' ? 7 : 6,
        lineStyle: { width: name === '客户贷款合计' ? 3 : 2, color }, itemStyle: { color },
        endLabel: { show: true, fontSize: 18, color, offset: [0, dy || 0],
                    formatter: p => p.value + unit }
    });

    initChart('chart-loanmix-bal')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 亿' },
        legend: { data: loanMixNames, bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 128, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: loanYears, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [balCorp, balRetail, balBill, balTotal].map(
            (d, i) => loanMixLine(loanMixNames[i], d, loanMixColors[i], ' 亿'))
    });

    initChart('chart-loanmix-yld')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: loanMixNames, bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 128, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: loanYears, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '平均收益率%', min: 0, max: 6, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [yldCorp, yldRetail, yldBill, yldTotal].map(
            // 2025 年三条线收于 3.64%–3.87%，端点标签手动错开纵向位置避免相互压盖
            (d, i) => loanMixLine(loanMixNames[i], d, loanMixColors[i], '%', [-14, 8, 0, 28][i]))
    });

    // 存款期限结构：活期 vs 定期 占比（2025 年末）
    (function () {
        const dv = D['depterm'].vals, dt = dv.reduce((s, x) => s + (x || 0), 0) || 1;
        const pct = i => (dv[i] || 0) / dt * 100;
        initChart('chart-depterm')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        title: [
            { text: '定期 ' + pct(0).toFixed(2) + '%\n活期 ' + pct(1).toFixed(2) + '%',
              left: 'center', top: 'center', textAlign: 'center',
              textStyle: { fontSize: 18, color: '#6c3483', fontWeight: 700, lineHeight: 22 } }
        ],
        tooltip: { trigger: 'item', formatter: '{b}: {c} 亿元 ({d}%)', textStyle: { fontSize: 18 } },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        series: [{
            name: '存款期限结构', type: 'pie', radius: ['46%', '68%'], center: ['50%', '52%'],
            avoidLabelOverlap: true, label: { show: true, fontSize: 18, formatter: '{b}\n{d}%' },
            data: [
                { value: D['depterm'].vals[0], name: '定期存款', itemStyle: { color: '#6c3483' } },
                { value: D['depterm'].vals[1], name: '活期存款', itemStyle: { color: '#e67e22' } },
                { value: D['depterm'].vals[2],   name: '保证金及其他', itemStyle: { color: '#b0a0bd' } }
            ]
        }]
    });
    })();
})();

/* ────── 1c-2. 客户存款平均付息率 与 活期存款占比（历年 2019–2025） ────── */
(function () {
    const years = D['depcost'].years;
    // 全行客户存款合计平均付息率（%），取自历年年报「客户存款合计」表
    const cost  = D['depcost'].cost;
    // 活期存款占客户存款总额比重（%）= 公司活期 + 个人活期（期末）
    const demand = D['depcost'].demand;
    // 付息率轴范围随各行数据自适应（原写死 min1.3/max2.1 会裁掉招行1.17、民生2.36 等点）
    const cVals = cost.filter(v => v != null);
    const cMin = Math.floor((Math.min(...cVals) - 0.1) * 10) / 10;
    const cMax = Math.ceil((Math.max(...cVals) + 0.1) * 10) / 10;

    initChart('chart-depcost')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   valueFormatter: v => v + '%' },
        grid: { left: 60, right: 66, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '付息率%', min: cMin, max: cMax,
                 nameTextStyle: { fontSize: 18, color: '#c0392b' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [{
            name: '客户存款平均付息率', type: 'line', data: cost, smooth: true, symbolSize: 7, z: 3,
            lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
            label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%', position: 'top' }
        }]
    });

    initChart('chart-demandratio')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   valueFormatter: v => v + '%' },
        grid: { left: 60, right: 66, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '活期占比%', min: 0,
                 nameTextStyle: { fontSize: 18, color: '#6c3483' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [{
            name: '活期存款占比', type: 'line', data: demand, smooth: true, symbolSize: 7, z: 3,
            lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
            areaStyle: { color: 'rgba(108,52,131,0.10)' },
            label: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}%', position: 'top' }
        }]
    });
})();

/* ────── 1c-3. 已发行债务证券：期末余额、平均成本率、逐笔票面利率（2018–2025） ──────
 * 数据来自年报「应付债券」附注（按类别期末余额、逐笔发行条款）与「利息支出——已发行债务证券」
 * 表（平均余额 / 平均成本率）。同业存单发行流量比债券大两个数量级，故不画发行额，只画余额与成本率。 */
(function () {
    const B = D['bondpay'] || EMPTY_D;
    const years = B.years || [];

    /* 期末余额（亿元）：同业存单 + 应付债券堆叠，叠加平均余额合计（同量级，可同轴）。
     * 不少中小行只把「应付债券」当一个整体披露（内含同业存单），此时只有 balTotal，画一根合计柱。 */
    (function () {
        if (!document.getElementById('chart-bond-bal')) return;
        const balNcd = B.balNcd || [], balBond = B.balBond || [], avgTotal = B.avgTotal || [];
        const split = balNcd.some(v => v != null) || balBond.some(v => v != null);
        const balTotal = split ? [] : (B.balTotal || []);
        if (!split && !balTotal.some(v => v != null)) { __stub('chart-bond-bal'); return; }
        const tot = years.map((_, i) => split ? (balNcd[i] || 0) + (balBond[i] || 0) : (balTotal[i] || 0));
        // 存单压降到很小时柱内白字会压出柱外（无锡银行 2024/2025），矮于合计 9% 就不标，数值看 tooltip
        const thin = Math.max.apply(null, tot.concat([0])) * 0.09;
        const bigOnly = p => (p.value != null && p.value >= thin) ? p.value : '';
        const ser = live([
            { name: '已发行同业存单', type: 'bar', stack: 'bal', data: balNcd,
              itemStyle: { color: '#6c3483' },
              label: { show: true, fontSize: 16, color: '#fff', formatter: bigOnly } },
            { name: '应付债券（金融债/二级资本债）', type: 'bar', stack: 'bal', data: balBond,
              itemStyle: { color: '#e67e22' } },
            { name: '已发行债务证券合计', type: 'bar', stack: 'bal', data: balTotal,
              itemStyle: { color: '#6c3483' } },
            { name: '平均余额合计', type: 'line', data: avgTotal, smooth: true, symbolSize: 7, z: 3,
              lineStyle: { width: 2.5, color: '#95a5a6', type: 'dashed' }, itemStyle: { color: '#95a5a6' } }
        ]);
        const legendNames = ser.map(s => s.name);
        // 合计数值挂在一根零高透明柱上，z 抬到虚线之上，平均余额线才不会从数字中间穿过（招行 2024/2025）
        ser.push({ name: '期末合计', type: 'bar', stack: 'bal', data: years.map(() => 0),
                   itemStyle: { color: 'transparent' }, z: 10, silent: true,
                   label: { show: true, fontSize: 16, color: '#555', position: 'top', distance: 5,
                            formatter: p => tot[p.dataIndex] ? tot[p.dataIndex].toFixed(2) : '' } });
        initChart('chart-bond-bal')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                       formatter: ps => ps[0].axisValue + ' 年<br>' + ps
                           .filter(p => p.seriesName !== '期末合计').map(p =>
                           `${p.marker}${p.seriesName}：${p.value == null ? '—' : p.value + ' 亿元'}`).join('<br>') +
                           (split ? '<br>期末合计：' + tot[ps[0].dataIndex].toFixed(2) + ' 亿元' : '') },
            legend: { bottom: 2, data: legendNames, textStyle: { fontSize: 18 } },
            grid: { left: 76, right: 30, top: 36, bottom: 52 },
            xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                     axisLabel: { fontSize: 18, color: '#555' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            series: ser
        });
    })();

    /* 平均成本率（%）：同业存单 / 应付债券 / 合计 */
    (function () {
        if (!document.getElementById('chart-bond-cost')) return;
        const rNcd = B.rateNcd || [], rBond = B.rateBond || [], rTot = B.rateTotal || [];
        if (![rNcd, rBond, rTot].some(a => a.some(v => v != null))) { __stub('chart-bond-cost'); return; }
        const ax = niceAxis([].concat(rNcd, rBond, rTot), 1);
        // 首末两点的数值标签会压到纵轴刻度／右边界上，改成贴着点向内排
        const totData = rTot.map((v, i) => (i === 0 || i === rTot.length - 1)
            ? { value: v, label: { align: i === 0 ? 'left' : 'right',
                                   position: i === 0 ? 'top' : 'bottom' } } : v);
        initChart('chart-bond-cost')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '—' : v + '%' },
            legend: { bottom: 2, textStyle: { fontSize: 18 } },
            grid: { left: 70, right: 66, top: 32, bottom: 52 },
            xAxis: { type: 'category', data: years, boundaryGap: false,
                     axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '成本率%', min: ax.min, max: ax.max, interval: ax.interval,
                     nameTextStyle: { fontSize: 18, color: '#c0392b' },
                     axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            series: live([
                { name: '合计', type: 'line', data: totData, smooth: true, symbolSize: 8, z: 4,
                  lineStyle: { width: 3.5, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
                  // 统一两位小数，3.4% 与 3.99% 混排容易看成不同口径
                  label: { show: true, fontSize: 18, color: '#c0392b', position: 'top',
                           formatter: p => p.value == null ? '' : p.value.toFixed(2) + '%' } },
                { name: '已发行同业存单', type: 'line', data: rNcd, smooth: true, symbolSize: 6,
                  lineStyle: { width: 2.5, color: '#6c3483' }, itemStyle: { color: '#6c3483' } },
                { name: '应付债券', type: 'line', data: rBond, smooth: true, symbolSize: 6,
                  lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' } }
            ])
        });
    })();

    /* 逐笔债券票面利率（横向条形，按发行日自上而下）。存续/已到期/已赎回用颜色区分 */
    (function () {
        const el = document.getElementById('chart-bond-list');
        if (!el) return;
        const bonds = (B.bonds || []).slice().sort((a, b) => (a.issueDate || '') < (b.issueDate || '') ? 1 : -1);
        if (!bonds.length) { __stub('chart-bond-list'); return; }
        // 各行发行笔数从 0 到 20 不等，图高按条数给（HTML 里的固定高度只是渝农商行的默认值）
        el.style.height = Math.max(320, bonds.length * 40 + 70) + 'px';
        const COLOR = { '存续': '#6c3483', '已到期': '#95a5a6', '已赎回': '#b0a0bd' };
        // 债券简称长短不一（可转债带一串累进票面），超长的截断，全称在 tooltip 里
        const cut = s => (s || '').length > 15 ? (s || '').slice(0, 15) + '…' : (s || '');
        const labels = bonds.map(b => (b.issueDate || '') + '\n' + cut(b.name));
        initChart('chart-bond-list')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
                       formatter: p => {
                           const b = bonds[p.dataIndex];
                           return `<b>${b.name}</b><br>发行日：${b.issueDate}<br>期限：${b.tenor || '—'}` +
                                  `<br>票面利率：${b.coupon == null ? '未披露' : b.coupon + '%'}` +
                                  `<br>发行额：${b.amount} 亿元` +
                                  `<br>到期：${b.maturity || '—'}（${b.status || '—'}）`;
                       } },
            grid: { left: 250, right: 130, top: 20, bottom: 40 },
            xAxis: { type: 'value', name: '票面利率%', min: 0, nameTextStyle: { fontSize: 18 },
                     axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            yAxis: { type: 'category', data: labels,
                     axisLabel: { fontSize: 15, color: '#555', lineHeight: 18, interval: 0 } },
            series: [{
                name: '票面利率', type: 'bar', barWidth: '62%',
                // 票面未披露的（如无锡银行 14 二级资本债）画成零长条，用标签写明，不然那一行是空白
                data: bonds.map(b => ({ value: b.coupon == null ? 0 : b.coupon,
                                        itemStyle: { color: COLOR[b.status] || '#95a5a6' } })),
                label: { show: true, position: 'right', fontSize: 16, color: '#555',
                         // 票面统一两位小数，不然 4% 和 4.65% 混排看起来像两种口径
                         formatter: p => (bonds[p.dataIndex].coupon == null ? '票面未披露' : p.value.toFixed(2) + '%') +
                                         '　' + bonds[p.dataIndex].amount + ' 亿' }
            }]
        });
    })();
})();

/* ────── 10b. 利率重定价缺口（按重定价期限，2025 vs 2024） ────── */
(function () {
    const el = document.getElementById('chart-repricing');
    if (!el) return;
    const buckets = D['repricing'].buckets;
    // 单位：亿元（年报为人民币百万元，÷100 换算）；负值＝负债敏感（重定价负债多于资产）
    const g2025 = D['repricing'].g2025;
    const g2024 = D['repricing'].g2024;
    echarts.init(el).setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
                   textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 亿' },
        legend: { data: ['2025', '2024'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 24, top: 44, bottom: 40 },
        xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '缺口 亿元', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025', type: 'bar', data: g2025, barGap: '10%',
              itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 16, color: '#555',
                       position: p => p.value >= 0 ? 'top' : 'bottom', formatter: '{c}' } },
            { name: '2024', type: 'bar', data: g2024,
              itemStyle: { color: '#95a5a6' },
              label: { show: true, fontSize: 16, color: '#888',
                       position: p => p.value >= 0 ? 'top' : 'bottom', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1d2. 公司贷款 / 零售贷款期末余额（2012–2025） ────── */
(function () {
    const years = D['loantrend'].years;
    // 期末余额（亿元）——按产品类型划分的贷款及不良贷款分布情况 / 客户贷款和垫款的构成情况
    const corp   = D['loantrend'].corp;
    const retail = D['loantrend'].retail;
    // 公司贷款和垫款不良率（%）——「按产品类型划分的贷款及不良贷款分布情况」表「公司贷款和垫款」行
    const nplCorp = D['loantrend'].nplCorp;
    initChart('chart-loantrend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   formatter: ps => ps[0].axisValue + '<br>' + ps.map(p =>
                       `${p.marker}${p.seriesName}：${p.value == null ? '—'
                         : p.value + (p.seriesName === '公司贷款不良率' ? '%' : ' 亿元')}`).join('<br>') },
        legend: { data: ['公司贷款', '零售贷款', '公司贷款不良率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 60, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '不良率%', min: 0, position: 'right', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#c0392b' }, splitLine: { show: false } }
        ],
        series: [
            { name: '公司贷款', type: 'line', data: corp, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '零售贷款', type: 'line', data: retail, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } },
            { name: '公司贷款不良率', type: 'line', yAxisIndex: 1, data: nplCorp, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#c0392b', type: 'dashed' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } }
        ]
    });
})();

/* ────── 1d. 个人贷款按用途细分（2018–2025） ────── */
(function () {
    const years = D['perloan-bal'].years;
    // 期末余额（亿元）——按揭 / 经营 / 信用卡 全区间；消费贷 2018–2022 未单独披露
    const balMortgage = D['perloan-bal'].balMortgage;
    const balBusiness = D['perloan-bal'].balBusiness;
    const balCard     = D['perloan-bal'].balCard;
    const balConsume  = D['perloan-bal'].balConsume;

    initChart('chart-perloan-bal')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '未披露' : v + ' 亿', textStyle: { fontSize: 18 } },
        legend: { data: ['住房按揭', '个人经营', '信用卡', '个人消费'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 66, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '住房按揭', type: 'line', data: balMortgage, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' } },
            { name: '个人经营', type: 'line', data: balBusiness, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '信用卡', type: 'line', data: balCard, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' } },
            { name: '个人消费', type: 'line', data: balConsume, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#1e8449', type: 'dashed' }, itemStyle: { color: '#1e8449' } }
        ]
    });

    // 不良率（%）——按揭 / 经营 / 其他（其他口径 2018–2022 vs 2023–2025 不同，见说明）
    const nplMortgage = D['perloan-bal'].nplMortgage;
    const nplBusiness = D['perloan-bal'].nplBusiness;
    const nplOthers   = D['perloan-bal'].nplOthers;

    // 分产品余额有披露、但分产品不良率整份缺失（多数农商行不单列各产品不良率）：三条线全空时
    // 别留一张只有坐标轴、没有线的空图（同 ⑥ H3 口径），改贴「该行暂无此项数据」占位。
    const __nplHasData = [nplMortgage, nplBusiness, nplOthers].some(
        a => Array.isArray(a) && a.some(v => v != null));
    if (!__nplHasData) {
        __stub('chart-perloan-npl');
    } else {
    initChart('chart-perloan-npl')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '缺口' : v + '%', textStyle: { fontSize: 18 } },
        legend: { data: ['住房按揭', '个人经营', '其他（含消费/信用卡）'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '住房按揭', type: 'line', data: nplMortgage, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              label: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}%' } },
            { name: '个人经营', type: 'line', data: nplBusiness, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
            { name: '其他（含消费/信用卡）', type: 'line', data: nplOthers, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#7f8c8d', type: 'dashed' }, itemStyle: { color: '#7f8c8d' } }
        ]
    });
    }
})();

/* ────── 3. 前十大股东 ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolders）重绘。 */
window.__renderYnsHolders = function (D) {
    if (!document.getElementById('chart-holders')) return;   // 仅业绩页
    const holders = D['holders'].holders;
    // 表格
    const tb = document.getElementById('holder-tbody');
    const chgColor = c => c === '不变' ? '#888' : (c[0] === '+' ? '#c0392b' : '#1e8449');
    tb.innerHTML = holders.map(h =>
        `<tr><td>${h.name}</td><td>${h.pct.toFixed(2)}%</td>` +
        `<td style="color:${chgColor(h.chg)}">${h.chg}</td><td style="font-size:18px;color:#777">${h.type}</td></tr>`
    ).join('');
    // 股东结构单层环形图：全部股东在同一个环、按比例铺满整圈；「其他流通股东」也按普通股东参与、严格按持股比例从大到小排序
    // 派系配色：香港中央结算 #16a085 · 渝富系 #6c3483 · 发展系 #2980b9 · 城投 #e67e22 · 财信 #c0392b · 社保 #f1c40f · 其他 #95a5a6
    const holderData = D['holders'].holderData;
    const holderTip = { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占总股本）` };
    initChart('chart-holders')?.setOption({
        backgroundColor: '#fff',
        title: [
            { text: D['holders'].centerText || '前十大\n58.29%', left: 'center', top: 'center', textAlign: 'center',
              textStyle: { fontSize: 20, color: '#6c3483', fontWeight: 700, lineHeight: 24 } }
        ],
        tooltip: holderTip,
        series: [{
            type: 'pie', radius: ['40%', '74%'], center: ['50%', '54%'], startAngle: 90,
            sort: null, minShowLabelAngle: 12, avoidLabelOverlap: true,
            data: holderData,
            label: { show: true, position: 'outside', formatter: '{b}\n{c}%', fontSize: 18, color: '#333' },
            labelLine: { show: true, length: 12, length2: 10 },
            itemStyle: { borderColor: '#fff', borderWidth: 2 }
        }]
    });

    // 图外清单：确保每位股东信息清晰可读（不受扇区大小影响），按派系分组
    const factions = D['holders'].factions;
    const val = n => holderData.find(d => d.name === n).value;
    document.getElementById('holders-legend').innerHTML = factions.map(f => {
        const sum = f.names.reduce((a, n) => a + val(n), 0);
        const items = f.names.map(n => `${n} ${val(n)}%`).join('　');
        return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${f.color};vertical-align:-1px;margin-right:6px"></span>` +
               `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#6c3483;font-weight:600">${sum.toFixed(2)}%</span>` +
               (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
    }).join('');

    // H 股年报（2018）股东结构环形图：与 A 股环形图同款，数据取自 D['holders-h']（仅渝农商 payload 含此键）
    if (D['holders-h'] && document.getElementById('chart-holders-h')) {
        const hH = D['holders-h'];
        initChart('chart-holders-h')?.setOption({
            backgroundColor: '#fff',
            title: [
                { text: hH.centerText || '前十大\n67.00%', left: 'center', top: 'center', textAlign: 'center',
                  textStyle: { fontSize: 20, color: '#16a085', fontWeight: 700, lineHeight: 24 } }
            ],
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占总股本）` },
            series: [{
                type: 'pie', radius: ['40%', '74%'], center: ['50%', '54%'], startAngle: 90,
                sort: null, minShowLabelAngle: 12, avoidLabelOverlap: true,
                data: hH.holderData,
                label: { show: true, position: 'outside', formatter: '{b}\n{c}%', fontSize: 18, color: '#333' },
                labelLine: { show: true, length: 12, length2: 10 },
                itemStyle: { borderColor: '#fff', borderWidth: 2 }
            }]
        });
        const valH = n => hH.holderData.find(d => d.name === n).value;
        const legH = document.getElementById('holders-legend-h');
        if (legH) legH.innerHTML = hH.factions.map(f => {
            const sum = f.names.reduce((a, n) => a + valH(n), 0);
            const items = f.names.map(n => `${n} ${valH(n)}%`).join('　');
            return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${f.color};vertical-align:-1px;margin-right:6px"></span>` +
                   `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#16a085;font-weight:600">${sum.toFixed(2)}%</span>` +
                   (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
        }).join('');
    }

    // 只看 H 股内部：SFO 披露的持 H 股 ≥5% 主要股东，占 H 股总股本口径，数据取自 D['holders-h-only']
    if (D['holders-h-only'] && document.getElementById('chart-holders-h-only')) {
        const hO = D['holders-h-only'];
        initChart('chart-holders-h-only')?.setOption({
            backgroundColor: '#fff',
            title: [
                { text: hO.centerText || '披露≥5%\nH股股东\n合计 33.25%', left: 'center', top: 'center', textAlign: 'center',
                  textStyle: { fontSize: 20, color: '#16a085', fontWeight: 700, lineHeight: 24 } }
            ],
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占 H 股总股本）` },
            series: [{
                type: 'pie', radius: ['40%', '74%'], center: ['50%', '54%'], startAngle: 90,
                sort: null, minShowLabelAngle: 12, avoidLabelOverlap: true,
                data: hO.holderData,
                label: { show: true, position: 'outside', formatter: '{b}\n{c}%', fontSize: 18, color: '#333' },
                labelLine: { show: true, length: 12, length2: 10 },
                itemStyle: { borderColor: '#fff', borderWidth: 2 }
            }]
        });
        const valO = n => hO.holderData.find(d => d.name === n).value;
        const legO = document.getElementById('holders-legend-h-only');
        if (legO) legO.innerHTML = hO.factions.map(f => {
            const sum = f.names.reduce((a, n) => a + valO(n), 0);
            const items = f.names.map(n => `${n} ${valO(n)}%`).join('　');
            return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${f.color};vertical-align:-1px;margin-right:6px"></span>` +
                   `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#16a085;font-weight:600">${sum.toFixed(2)}%</span>` +
                   (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
        }).join('');
    }

    // 横向条形图：按比例排序，同派系同色；≥4% 条内显示股东名（白字），<4% 名称显示在条右侧；底部滑块可左右拉伸放大
    (function buildBar() {
        const names = holderData.map(h => h.name);
        const barData = holderData.map(h => ({
            value: h.value,
            itemStyle: { color: h.itemStyle.color },
            label: h.value >= 4
                ? { show: true, position: 'insideLeft', distance: 8, color: '#fff', fontSize: 18, fontWeight: 600, formatter: `${h.name}  ${h.value}%` }
                : { show: true, position: 'right', distance: 6, color: '#333', fontSize: 18, fontWeight: 600, formatter: `${h.name}  ${h.value}%` }
        }));
        // 44% 是照渝农商第一大股东量级定的；别的行第一大更高时按其值放宽，免得条被截断
        const barMax = Math.max(44, Math.ceil(Math.max.apply(null, holderData.map(h => h.value)) / 2) * 2);
        initChart('chart-holders-bar')?.setOption({
            backgroundColor: '#fff',
            grid: { left: 14, right: 170, top: 16, bottom: 16, containLabel: true },
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${names[p.dataIndex]}：${p.value}%（占总股本）` },
            xAxis: {
                type: 'value', min: 0, max: barMax, name: '占总股本 %', nameTextStyle: { fontSize: 18 },
                axisLabel: { fontSize: 18, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eee' } }
            },
            yAxis: {
                type: 'category', data: names, inverse: true,
                axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#ccc' } }
            },
            // 不加 dataZoom：股东数量有限，x 轴已按最大持股比例定死，一次看全
            series: [{
                type: 'bar', data: barData, barCategoryGap: '35%',
                itemStyle: { borderColor: '#fff', borderWidth: 1 }
            }]
    });
})();
};
window.__renderYnsHolders(D);

/* ────── 3b. 历年股东持股集中度（独立板块 · 第一大 / 前三大 / 前十大 三张柱状图） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolderConcentration）重绘。
 * 数据来源：东方财富 F10「前十名股东」接口按报告期（含季报）汇总，只取 IS_REPORT=1 的定期报告期。
 * 接口里还混着 IS_REPORT=0 的事件型快照（如 2022-12-22——隆鑫控股 4.33 亿股过户给重庆发展投资那天），
 * 这类快照只列受影响的前几名（2022-12-22 仅 4 行），算不出前十大合计，已在生成阶段整期剔除。
 * 三个口径各占一张全宽柱状图，而不是叠在一张图里：量级差得远（渝农商第一大 22% 上下、前三大 37.8%、
 * 前十大 55%~67%），共用一条 15~70 的轴时第一大 / 前三大那点年际差（<0.2pp）会被完全压平。
 * 横轴改成「每年一根柱」：原先按报告期画，一年四个点里三个是季报的重复值，柱子只会更密而不更有信息；
 * 每年取该年最后一个已披露报告期（最新年份即最近一期，柱标签里注明月日）。
 * 2010–2018 的港交所（03618 H 股年报）口径单独作为一个 series 披露（holder-concentration-hist，
 * 图例「港交所披露」、同色系浅色柱），与 2019 年起的 A 股定期报告口径分开；
 * 其中 2010–2017 是重构合并 A+H 口径，柱身再加红色虚线框，与 2018 年报披露原值区分。 */
window.__renderYnsHolderConcentration = function (D) {
    if (!document.getElementById('chart-conc-top10')) return;   // 仅股东页
    const IDS = ['chart-conc-top1', 'chart-conc-top3', 'chart-conc-top10'];
    const cur  = (D['holder-concentration'] || {}).raw || [];
    const hist = (D['holder-concentration-hist'] || {}).raw || [];
    if (!cur.length && !hist.length) { IDS.forEach(__stub); return; }
    // 第一大股东逐期可能换人/改名（工行的汇金 vs 财政部、招行的招商局系），并行数组按期给名字
    const t1Names = (D['holder-concentration'] || {}).top1Names || [];
    // 剔除「香港中央结算」名义持有人后的第一大 / 前三大（占总股本 %）与其第一大实益股东名：
    // A+H 银行的名义第一大恒为香港中央结算（代理人 / 沪深股通），剔除后才看得出真正的实益股东。
    // 只有 A 股定期报告口径（cur）算得出（有逐户明细），港交所 H 股年报口径（hist）无此数据。
    const t1Ex   = (D['holder-concentration'] || {}).top1Ex || [];
    const t3Ex   = (D['holder-concentration'] || {}).top3Ex || [];
    const t1ExNm = (D['holder-concentration'] || {}).top1ExNames || [];

    // hist(年度) + cur(报告期) 合成一条序列，再按年取该年最后一期；
    // 同一年两边都有时后 push 的 cur（A 股披露原值）覆盖 hist 重构值（用 >= 保证）
    // src 记住这一年的数据出自哪个交易所的披露：'H' = 港交所年报，'A' = 沪/深交易所定期报告。
    // 两者分成两个 series 单独画（见下），不再混进同一根序列里。
    const rows = hist.map(r => ({ date: r[0], t1: r[1], t3: r[2], t10: r[3],
                                  recon: r[4] === 'recon', t1name: '', src: 'H',
                                  t1ex: null, t3ex: null, t1exname: '' }))
        .concat(cur.map((r, i) => ({ date: r[0], t1: r[1], t3: r[2], t10: r[3],
                                     recon: false, t1name: t1Names[i] || '', src: 'A',
                                     t1ex: t1Ex[i], t3ex: t3Ex[i], t1exname: t1ExNm[i] || '' })));
    const byYear = new Map();
    rows.forEach(r => {
        const y = String(r.date).slice(0, 4);
        const prev = byYear.get(y);
        if (!prev || r.date >= prev.date) byYear.set(y, r);
    });
    const items = Array.from(byYear.keys()).sort().map(y => byYear.get(y));
    // 年末口径的柱只写年份；非年末（最新一期）补上月日，免得当成整年数
    const labels = items.map(it => it.date.slice(5) === '12-31'
        ? it.date.slice(0, 4) : it.date.slice(0, 4) + '\n(' + it.date.slice(5) + ')');

    // 港交所上市（H 股年报）口径的数据单独作为一个 series 披露，不与 A 股定期报告口径合成一根柱：
    // 两者披露主体、股东表范围都不同（H 股年报里 HKSCC 名义持有人代持全部 H 股，A 股定期报告的
    // 前十大是登记在册股东），混成一条序列会让人误以为是同一张表的连续读数。
    // 图例里各占一项、颜色深浅区分，legend 只列本行实际存在的来源。
    const SRC = {
        H: { name: '港交所披露（H 股年报口径）', tip: '港交所 H 股年报披露' },
        A: { name: 'A 股定期报告披露（沪 / 深交易所）', tip: 'A 股定期报告披露' }
    };
    const srcOrder = ['H', 'A'].filter(s => items.some(it => it.src === s));

    // 三张图共用这一个 formatter：四个口径（第一大 / 前三大 / 前十大 / 其他流通股东）一次列全，
    // 当前图画的那个加粗，其余灰显作参照——否则切到另一张图就查不到同年的别的口径。
    // 表头写明这一年的数据取自哪个交易所的披露（港交所年报 / A 股定期报告），口径不同不要看串。
    const pct = v => v == null ? '缺口' : v + '%';
    const concFormatter = own => p => {
        const it = items[p[0].dataIndex];
        const head = it.date
            + ' <span style="color:#888">· ' + SRC[it.src].tip + '</span>'
            + (it.recon ? ' <span style="color:#c0392b">（重构合并 A+H 口径）</span>' : '');
        const rs = [
            ['第一大股东' + (it.t1name ? '（' + it.t1name + '）' : ''), pct(it.t1), '第一大']
        ];
        // 剔除香港中央结算名义持有人后的第一大实益股东，仅 A 股口径且与含 HKSCC 值不同时才列
        if (it.t1ex != null && it.t1ex !== it.t1)
            rs.push(['　└ 剔除香港中央结算' + (it.t1exname ? '（' + it.t1exname + '）' : ''),
                     pct(it.t1ex), '第一大剔除']);
        rs.push(['前三大股东合计', pct(it.t3), '前三大']);
        if (it.t3ex != null && it.t3ex !== it.t3)
            rs.push(['　└ 剔除香港中央结算', pct(it.t3ex), '前三大剔除']);
        rs.push(['前十大股东合计', pct(it.t10), '前十大']);
        rs.push(['其他流通股东', it.t10 == null ? '缺口' : (100 - it.t10).toFixed(2) + '%', '其他']);
        return head + '<br/>' + rs.map(([k, v, tag]) => (tag === own || tag === own + '剔除')
            ? k + ' <b>' + v + '</b>'
            : '<span style="color:#999">' + k + ' ' + v + '</span>').join('<br/>');
    };

    /* 一张柱图：key 取 items 里的字段，own 决定 tooltip 里哪行加粗。
     * 轴按数据取整、不从 0 起（各行水平差得远：渝农商前十大 54~67%、招行 60%+、天津银行 80%+；
     * 从 0 起画时 5pp 的 U 形只占图高一成），绝对水平看柱顶数值。
     * 按披露来源拆成两个 series（港交所 H 股年报 / A 股定期报告）：同一年只会落在其中一个 series，
     * 故用 barGap:'-100%' 让两个 series 占同一个槽位，柱子仍居中、仍是满宽。 */
    const mkBar = (id, key, own, colors, exKey) => {
        if (!document.getElementById(id)) return;
        const vals = items.map(it => it[key]);
        if (!vals.some(v => v != null)) { __stub(id); return; }
        // 剔除香港中央结算后的实益股东占比：仅 A 股口径有、且与含 HKSCC 值不同的年份才画红线。
        // 纯 A 股行（HKSCC 不在前列）ex 恒等于含值，此时不画线、退化成普通单序列柱图。
        const exVals = exKey ? items.map(it => it[exKey]) : [];
        const showEx = exKey && items.some((it, i) => exVals[i] != null && exVals[i] !== vals[i]);
        // 红线 ex 值恒小于柱高（剔除了名义第一大），轴范围要把 ex 一并纳入，否则线落到轴下看不见；
        // 两者同轴（都是「占总股本 %」）直接可比，柱顶是名义值、红线是剔除 HKSCC 的真实实益值。
        const ax = niceAxis(showEx ? vals.concat(exVals).filter(v => v != null) : vals, 1);
        // 柱多了柱顶横排数值会连成一串（招行 2001 起 26 根柱时 "17.95%17.95%…" 直接叠住），
        // 超过 20 根就把数值竖排：柱宽 46px 容得下一列字，仍能逐柱读数；同时给顶部多留白。
        // （20 根以内横排还留得下——渝农商 17 根柱时 "58.91%" 各占 70px 互不相碰。）
        const dense = items.length > 20;
        const EX_NAME = '剔除香港中央结算';
        const hasLegend = srcOrder.length > 1 || showEx;   // 单一来源且无红线时不占图例行
        const legendData = srcOrder.map(s => SRC[s].name).concat(showEx ? [EX_NAME] : []);
        const series = srcOrder.map(s => ({
            name: SRC[s].name, type: 'bar', barMaxWidth: 46,
            barGap: '-100%',   // 两个来源共用同一个槽位（同一年只有一个来源有值）
            // 港交所口径里 2010–2017 是重构值，柱身再加红色虚线框，与年报披露原值区分
            data: items.map(it => it.src !== s ? null : ({
                value: it[key],
                itemStyle: it.recon
                    ? { color: colors[s], borderColor: '#c0392b',
                        borderType: 'dashed', borderWidth: 2 }
                    : { color: colors[s] }
            })),
            label: { show: true, position: 'top', fontSize: dense ? 14 : 15, fontWeight: 600,
                     color: colors[s], rotate: dense ? 90 : 0,
                     align: dense ? 'left' : 'center', verticalAlign: 'middle',
                     distance: dense ? 8 : 5,
                     formatter: p => p.value == null ? '' : p.value + '%' }
        }));
        // 红线：剔除香港中央结算名义持有人后的真实第一大 / 前三大实益占比（H 口径年份断线）
        if (showEx) series.push({
            name: EX_NAME, type: 'line', symbol: 'circle', symbolSize: 7, z: 5,
            lineStyle: { color: '#c0392b', width: 2 }, itemStyle: { color: '#c0392b' },
            data: exVals.map(v => v == null ? null : v),
            label: { show: !dense, position: 'bottom', fontSize: 14, fontWeight: 600,
                     color: '#c0392b', formatter: p => p.value == null ? '' : p.value + '%' }
        });
        initChart(id)?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                       axisPointer: { type: 'shadow' }, formatter: concFormatter(own) },
            legend: hasLegend
                ? { top: 0, itemGap: 24, textStyle: { fontSize: 16, color: '#555' },
                    data: legendData }
                : { show: false },
            grid: { left: 72, right: 32,
                    top: (dense ? 70 : 34) + (hasLegend ? 30 : 0), bottom: 78 },
            xAxis: {
                type: 'category', data: labels,
                axisLabel: { fontSize: 16, color: '#555', interval: 0, lineHeight: 18 },
                axisTick: { alignWithLabel: true },
                axisLine: { lineStyle: { color: '#bbb' } }
            },
            yAxis: {
                type: 'value', name: '占总股本 %',
                min: ax.min, max: ax.max, interval: ax.interval,
                nameTextStyle: { fontSize: 18 },
                axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            series
        }, true);   // notMerge —— 切行时年份跨度不同，避免残留上一行的柱
    };

    // 每张图一个色系：A 股定期报告口径用深色（本行主色），港交所年报口径用同色系浅色。
    // 第一大 / 前三大再叠一条红线：剔除香港中央结算名义持有人后的真实实益占比（前十大不叠）。
    mkBar('chart-conc-top1',  't1',  '第一大', { A: '#16a085', H: '#8ccfc4' }, 't1ex');
    mkBar('chart-conc-top3',  't3',  '前三大', { A: '#2c6fb3', H: '#9dc0e3' }, 't3ex');
    mkBar('chart-conc-top10', 't10', '前十大', { A: '#6c3483', H: '#b99ac8' });
};
window.__renderYnsHolderConcentration(D);



// 可排序表格：点击表头按该列排序，"合计"等 data-nosort 行固定在最后不参与排序。
// 数值列按 data-sort="num" 解析（去掉千分位逗号），文本列按 localeCompare。
(function initSortableTables() {
    document.querySelectorAll('table.sortable').forEach(table => {
        const headers = table.querySelectorAll('thead th');
        const tbody = table.querySelector('tbody');
        headers.forEach((th, colIndex) => {
            if (th.dataset.sort === 'none') return;   // 序号列：固定顺序，不参与排序
            th.addEventListener('click', () => {
                const type = th.dataset.sort || 'text';
                const curDir = th.dataset.sortDir;
                const dir = curDir === 'asc' ? 'desc' : 'asc';
                headers.forEach(h => delete h.dataset.sortDir);
                th.dataset.sortDir = dir;

                const rows = Array.from(tbody.querySelectorAll('tr'));
                const fixedRows = rows.filter(r => r.dataset.nosort !== undefined);
                const sortRows = rows.filter(r => r.dataset.nosort === undefined);

                sortRows.sort((ra, rb) => {
                    const a = ra.children[colIndex].textContent.trim();
                    const b = rb.children[colIndex].textContent.trim();
                    let cmp;
                    if (type === 'num') {
                        cmp = parseFloat(a.replace(/,/g, '')) - parseFloat(b.replace(/,/g, ''));
                    } else {
                        cmp = a.localeCompare(b, 'zh-Hans-CN');
                    }
                    return dir === 'asc' ? cmp : -cmp;
                });

                sortRows.concat(fixedRows).forEach(r => tbody.appendChild(r));
            });
        });
    });
})();

/* ────── 6. 分部信息 ────── */
(function () {
    const segs = D['seg-rev'].segs;
    const rev25 = D['seg-rev'].rev25;
    const rev24 = D['seg-rev'].rev24;
    initChart('chart-seg-rev')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 } },
        legend: { data: ['2025', '2024'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: segs, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '百万元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025', type: 'bar', data: rev25, itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 18, formatter: p => (p.value/1000).toFixed(1)+'亿' } },
            { name: '2024', type: 'bar', data: rev24, itemStyle: { color: '#b39ddb' } }
        ]
    });

    // 地域：存贷款占比
    initChart('chart-geo')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: ['县域', '主城'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: D['geo'].cats, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', max: 100, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '县域', type: 'bar', stack: 'geo', data: D['geo'].county, itemStyle: { color: '#1e8449' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } },
            { name: '主城', type: 'bar', stack: 'geo', data: D['geo'].urban, itemStyle: { color: '#e67e22' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } }
        ]
    });
})();

/* ────── 7. 贷款行业分布 ────── */
(function () {
    const inds = D['loan-industry'].inds;
    const bal25 = D['loan-industry'].bal25;
    const bal24 = D['loan-industry'].bal24;
    initChart('chart-loan-industry')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            valueFormatter: v => v == null ? '' : (v/10000).toFixed(1) + ' 万亿' },
        legend: { data: ['2025 余额', '2024 余额'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 90, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: inds, axisLabel: { fontSize: 18, color: '#555', rotate: 30 } },
        yAxis: { type: 'value', name: '百万元', nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025 余额', type: 'bar', data: bal25, itemStyle: { color: '#6c3483' } },
            { name: '2024 余额', type: 'bar', data: bal24, itemStyle: { color: '#b39ddb' } }
        ]
    });
})();

/* ────── 8. 五级分类 ────── */
(function () {
    initChart('chart-5tier')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: '{b}: {c} 百万 ({d}%)' },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['36%', '64%'], center: ['50%', '48%'],
            label: { show: true, fontSize: 18, formatter: '{b}\n{d}%' },
            data: [
                { value: D['5tier'].vals[0], name: '正常', itemStyle: { color: '#1e8449' } },
                { value: D['5tier'].vals[1],  name: '关注', itemStyle: { color: '#f39c12' } },
                { value: D['5tier'].vals[2],   name: '次级', itemStyle: { color: '#e67e22' } },
                { value: D['5tier'].vals[3],   name: '可疑', itemStyle: { color: '#c0392b' } },
                { value: D['5tier'].vals[4],   name: '损失', itemStyle: { color: '#7b241c' } }
            ]
        }]
    });
})();

/* ────── 8b. 贷款迁徙率（渝农商行 2019–2025，正常类对比农业银行 2010–2023） ────── */
(function () {
    // 渝农商行: 2019-2025 逐年迁徙率(%), 取自历年A股年报「贷款迁徙率」表 (dfcfw.com PDF, pdftotext -layout 抽取)
    // 2019/2020 已按银保监发[2022]2号文追溯调整口径; 相邻年报重叠年份数值已交叉核对一致, 2026-08-14 提取核对
    const yrsMigrate = D['migrate'].yrsMigrate;
    // 关注/次级/可疑三档年末迁徙率随行取值（渝农商 2019-2025 已入 migrate 键；其余行 migrate 为空时整图已被 __stub 占位）
    const mgGuanzhu = D['migrate'].guanzhu || [];
    const mgCiji    = D['migrate'].ciji || [];
    const mgKeyi    = D['migrate'].keyi || [];
    initChart('chart-migrate')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: yrsMigrate, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '关注类', type: 'line', data: mgGuanzhu, symbolSize: 7, lineStyle: { width: 3, color: '#f39c12' }, itemStyle: { color: '#f39c12' } },
            { name: '次级类', type: 'line', data: mgCiji, symbolSize: 7, lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '可疑类', type: 'line', data: mgKeyi, symbolSize: 7, lineStyle: { width: 2.5, color: '#7b241c', type: 'dashed' }, itemStyle: { color: '#7b241c' } }
        ]
    });

    // 正常类迁徙率对比: 渝农商行(2019-2025) vs 农业银行(2010-2023, 历年A股年报摘要/全文「其他财务指标」表)
    // 农行2017取自2019年报追溯值2.13%(非2017半年报摘要的年中数2.00%); 2018/2019两年在2019/2020两份年报重叠核对一致
    // 2021取2023年报口径1.10%(与2022/2023同表可比); 2024/2025年报未检索到该表，序列止于2023
    const yrsNormal = D['migrate'].yrsNormal;
    const ynshbNormal = D['migrate'].ynshbNormal;
    const abcNormal   = D['migrate'].abcNormal;
    const serMg = live([
        { name: SELF, type: 'line', data: ynshbNormal, connectNulls: false, symbolSize: 7, lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
        { name: '农业银行', type: 'line', data: abcNormal, connectNulls: false, symbolSize: 6, lineStyle: { width: 2.5, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' },
          endLabel: { show: true, formatter: '{a}', fontSize: 15, color: '#2980b9', distance: 4 } }
    ]);
    initChart('chart-migrate-normal')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: serMg.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 88, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: yrsNormal, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serMg
    });
})();


/* ────── 13. NIM 分解 ────── */
(function () {
    const items = D['nim'].items;
    const rate25 = D['nim'].rate25;
    const rate24 = D['nim'].rate24;
    initChart('chart-nim')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: ['2025 收益率/成本率', '2024 收益率/成本率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: items, axisLabel: { fontSize: 18, color: '#555', rotate: 35 } },
        yAxis: { type: 'value', name: '%', min: 0, max: 5, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025 收益率/成本率', type: 'bar', data: rate25, itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 18, formatter: '{c}%' } },
            { name: '2024 收益率/成本率', type: 'bar', data: rate24, itemStyle: { color: '#b39ddb' } }
        ]
    });
})();

/* ────── 5-① 资产负债表历年趋势（2010–2025，CAS 口径，balance-sheet.html） ────── */
(function () {
    const years = D['bs-trend'].years;
    // 资产总额 / 负债总额 / 股东权益合计（百万元），中国企业会计准则(CAS)合并口径期末数
    // 2010-2018 取自 H 股 03618 历年年报「合并财务状况表」；2019-2025 取自 A 股 601077 历年年报「合并资产负债表」
    // 均已与本行历年年报正式报表逐年交叉核对一致，2026-08-15 提取核对
    const assets = D['bs-trend'].assets;
    const liab   = D['bs-trend'].liab;
    const equity = D['bs-trend'].equity;
    initChart('chart-bs-trend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue} 年</b>`;
                p.forEach(x => { s += `<br>${x.marker}${x.seriesName}：${x.value.toLocaleString()} 百万元`; });
                return s;
            } },
        legend: { data: ['资产总额', '负债总额', '股东权益合计'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 88, right: 24, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        // 单一 Y 轴：权益与资产/负债共用同一刻度，如实呈现「银行权益仅占资产 6~10%」的结构
        // （原来把权益放右轴独立缩放，会让权益线看着与资产/负债一样高，误导量级——见 ⑥ 整改 H1）
        yAxis: { type: 'value', name: '百万元', min: 0, nameTextStyle: { fontSize: 16, color: '#555' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: v => (v/10000).toFixed(0) + '万' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '资产总额', type: 'line', data: assets, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '负债总额', type: 'line', data: liab, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '股东权益合计', type: 'line', data: equity, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } }
        ]
    });
})();

/* ────── 5-② 资产负债表结构 (2025) ────── */
(function () {
    const assets = D['bs'].assets;
    const claims = D['bs'].claims;
    const CAT = ['资产', '负债 + 权益'];
    const total = assets.reduce((s, it) => s + it.value, 0);
    const mk = (items, col) => items.map(it => ({
        name: it.name, type: 'bar', stack: 'bs', barMaxWidth: 160,
        emphasis: { focus: 'series' },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 18,
                 formatter: p => (p.value/total*100) < 4 ? '' : it.name },
        data: CAT.map((_, i) => i === col ? it.value : '-')
    }));
    initChart('chart-bs')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            valueFormatter: v => (v === '-' || v == null) ? '' : Number(v).toLocaleString() },
        legend: { type: 'scroll', bottom: 2, textStyle: { fontSize: 18 }, itemWidth: 14, itemHeight: 12 },
        grid: { left: 76, right: 30, top: 26, bottom: 54 },
        xAxis: { type: 'category', data: CAT, axisLabel: { fontSize: 18, fontWeight: 600, color: '#333' } },
        yAxis: { type: 'value', axisLabel: { fontSize: 18, formatter: v => (v/10000).toFixed(0) + '万', color: '#555' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        color: ['#8e44ad','#9b59b6','#af7ac5','#c39bd3','#d7bde2','#ebdef0','#e74c3c','#ec7063','#27ae60','#7dcea0'],
        series: [...mk(assets, 0), ...mk(claims, 1)]
    });
})();

/* ────── 5-③ 现金流量（2025 分季度经营净额） ────── */
(function () {
    initChart('chart-cf')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => Number(v).toLocaleString(), textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 24, top: 26, bottom: 36 },
        xAxis: { type: 'category', data: ['Q1','Q2','Q3','Q4'],
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [{ type: 'bar', data: D['cf'].vals, barWidth: '48%',
            itemStyle: { color: p => p.value >= 0 ? '#8e44ad' : '#e74c3c', borderRadius: [4,4,0,0] },
            label: { show: true, position: 'top', fontSize: 18,
                     formatter: p => Number(p.value).toLocaleString() } }]
    });
})();

window.addEventListener('resize', () => {
    document.querySelectorAll('.chart').forEach(el => {
        const inst = echarts.getInstanceByDom(el);
        if (inst) inst.resize();
    });
});

/* ────── intro.html · 员工岗位结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-role')) return;
    // 数据来源：2025 年报「第四章 五、（一）员工情况」PDF 第 119 页；本行口径合计 13,853 人
    const roles = D['staff-role'].roles;
    initChart('chart-staff-role')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: roles,
            color: ['#6c3483', '#af7ac5', '#c0392b', '#e67e22']
        }]
    });
})();

/* ────── intro.html · 员工学历结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-edu')) return;
    const edu = D['staff-edu'].edu;
    initChart('chart-staff-edu')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: edu,
            color: ['#6c3483', '#95a5a6', '#af7ac5']
        }]
    });
})();

/* ────── intro.html · 历年董事长 / 行长薪酬披露（2010-2025，税前，万元） ──────
 * 2010-2018: H股03618年报「董事、监事及高级管理层人员」章节；2019-2025: A股601077年报「公司治理报告」章节。
 * 董事长换人：2022年4月刘建忠→谢文辉；2024年10月谢文辉离任后行长隋军代行董事长职务
 * （年报"董事长及行长"章节原文："谢文辉先生于2024年10月离任后，董事会推举隋军先生代行董事长职务"，
 * 2025年"隋军...并经董事会推举短暂代行董事长职务"），2024/2025两年董事长栏均取隋军的行长薪酬数
 * （年报薪酬表职务栏对代行期间未单列"代行董事长"报酬，隋军实际以行长身份领取同一份薪酬）；
 * 2026-01-08刘小军任职资格获监管核准，但2025年度隋军仍是全年代行董事长的实际人选，故2025年
 * 董事长栏仍用隋军59.75万元，刘小军42.07万元(候任身份取得)在图中不作为该年"董事长"代表数值。
 * 行长换人：2013年12月谭远胜退休→谢文辉（任职资格待核准，2013年谢文辉当年确实未在任何身份下
 * 领取报酬，年报本身未披露任何数字，非因职务代行而留空，故该点保留空缺并在note注明原因）；
 * 2014-2023年3月为谢文辉；2023年4月起为隋军。
 * 注意：2010-2021年董事长(刘建忠)与行长(谢文辉/谭远胜)始终是两个不同的人，2014年报"董事长及行长"
 * 一节原文强调"角色相互分立"；"一人兼两职"发生在2022年(谢文辉升任董事长兼行长)及2024-2025年
 * (隋军以行长身份代行董事长职务)——这几年两条线数值相同，图上用虚线叠画并标注"一人兼两职/代行"。
 * 各年数值均为年报"税前薪酬合计"列，历年年报均注明非最终考核数。 */
(function () {
    if (!document.getElementById('chart-chairman-pay')) return;
    const years = D['chairman-pay'].years;
    const chairmanNames = D['chairman-pay'].chairmanNames;
    const chairmanPay   = D['chairman-pay'].chairmanPay;
    // 2013 谢文辉当年刚获聘行长、任职资格未获监管核准，年报本身未披露其任何报酬数（非代行职务留空，是确无数据）
    const presidentNames = D['chairman-pay'].presidentNames;
    const presidentPay   = D['chairman-pay'].presidentPay;
    // 一人兼两职/代行区间：用虚线线型标注两条线数值相同的年份。索引由数据 dashedIdx 提供
    // （编辑口径，需语义读年报判定同一人兼任，不能靠数值相等推断，故随数据下发）；缺省则无虚线。
    const dashedIdx = new Set(D['chairman-pay'].dashedIdx || []);
    // 换任/代行标注线：由数据 marks 提供 [{xAxis, name}]，缺省则不画标注线（各行专属）
    const payMarks = D['chairman-pay'].marks || [];

    initChart('chart-chairman-pay')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` + p.map(x => {
                const idx = x.dataIndex;
                const who = x.seriesIndex === 0 ? chairmanNames[idx] : presidentNames[idx];
                const note = dashedIdx.has(idx) ? '（一人兼两职/代行）' : '';
                return x.value == null ? '' : `${x.marker}${x.seriesName}（${who}）${note}：${x.value} 万元`;
            }).filter(Boolean).join('<br>') },
        legend: { data: ['董事长', '行长'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 52, bottom: 40 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '万元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            {
                name: '董事长', type: 'line', data: chairmanPay, smooth: true, symbolSize: 8,
                lineStyle: {
                    width: 2.5, color: '#c9a24a',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#c9a24a' },
                markLine: {
                    symbol: 'none', silent: true,
                    lineStyle: { color: '#999', type: 'dashed', width: 1 },
                    label: { fontSize: 16, color: '#888', formatter: p => p.name },
                    data: payMarks
                },
                label: { show: true, position: 'top', fontSize: 15, color: '#8a6d1f', formatter: '{c}' }
            },
            {
                name: '行长', type: 'line', data: presidentPay, smooth: true, symbolSize: 8,
                connectNulls: true,   // 仅2013年谢文辉当年确无薪酬数据(非代行留空), 跨越该点连线并在note说明
                lineStyle: {
                    width: 2.5, color: '#2980b9',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#2980b9' },
                label: { show: true, position: 'bottom', fontSize: 15, color: '#1f618d',
                         formatter: p => p.value == null ? '' : p.value }
            }
        ]
    });
})();

/* ────── intro.html · 员工年龄结构（横向堆叠条） ────── */
(function () {
    if (!document.getElementById('chart-staff-age')) return;
    const buckets = D['staff-age'].buckets;
    const vals    = D['staff-age'].vals;
    const total   = vals.reduce((s, v) => s + v, 0);
    initChart('chart-staff-age')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            textStyle: { fontSize: 18 },
            formatter: p => {
                const x = p[0];
                const pct = (x.value / total * 100).toFixed(1);
                return `<b>${x.axisValue}</b><br>${x.marker}人数：${x.value.toLocaleString()} 人（${pct}%）`;
            } },
        grid: { left: 100, right: 60, top: 20, bottom: 40 },
        xAxis: { type: 'value', name: '人数', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: buckets, inverse: true,
                 axisLabel: { fontSize: 18, color: '#333' } },
        series: [{
            type: 'bar', data: vals,
            itemStyle: { color: '#6c3483' },
            barWidth: 26,
            label: { show: true, position: 'right', fontSize: 17, color: '#333',
                formatter: p => `${p.value.toLocaleString()}（${(p.value / total * 100).toFixed(1)}%）` }
        }]
    });
})();

/* ────── debt.html · 到期期限结构（金融资产 vs 金融负债，2025 年末，7 档） ──────
 * 数据来源：2025 年报财务报表附注「金融风险管理 · 流动性风险 · (1) 剩余到期日分析」
 * PDF 第 131–133 页；单位：亿元（原表为人民币千元，÷100,000 换算）。
 * 报告未披露 Macaulay / 修正久期数值——本行利率风险计量采用重定价缺口 + 敏感性 + 情景分析。
 */
(function () {
    if (!document.getElementById('chart-maturity')) return;
    const buckets = D['maturity'].buckets;
    // 2025-12-31 金融资产 / 金融负债（亿元）
    const asset2025 = D['maturity'].asset2025;
    const debt2025  = D['maturity'].debt2025;
    const net2025   = asset2025.map((a, i) => +(a - debt2025[i]).toFixed(2));

    initChart('chart-maturity')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue}</b>`;
                p.forEach(x => {
                    if (x.value == null) return;
                    s += `<br>${x.marker}${x.seriesName}：${Number(x.value).toLocaleString()} 亿`;
                });
                return s;
            } },
        legend: { data: ['金融资产', '金融负债', '净头寸（资产 − 负债）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 46, bottom: 60 },
        xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 17, color: '#555', interval: 0 },
                 axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: { type: 'value', name: '亿元', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555',
                     formatter: v => (Math.abs(v) >= 1000 ? (v / 1000).toFixed(1) + '千' : v) },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '金融资产', type: 'bar', data: asset2025, barGap: '10%',
              itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 14, color: '#555',
                       formatter: p => Number(p.value).toLocaleString() } },
            { name: '金融负债', type: 'bar', data: debt2025,
              itemStyle: { color: '#95a5a6' },
              label: { show: true, position: 'top', fontSize: 14, color: '#888',
                       formatter: p => Number(p.value).toLocaleString() } },
            { name: '净头寸（资产 − 负债）', type: 'line', data: net2025, smooth: false,
              symbolSize: 8, lineStyle: { width: 2.5, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 14, color: '#c0392b',
                       position: p => p.value >= 0 ? 'top' : 'bottom',
                       formatter: p => Number(p.value).toLocaleString() } }
        ]
    });
})();


/* ────── risk.html · 权益资产比（股东权益合计 ÷ 资产总额，2010–2025，四行对比） ──────
 * = 1 − 资产负债率 = 1/权益乘数，最直观的财务杠杆指标；全口径权益（含少数股东权益）÷ 账面总资产。
 * 数据来源：东方财富 F10 各行历年年报合并资产负债表（data/tables/bank_<code>_annual.json 的 equity_asset_ratio）。
 */
(function () {
    if (!document.getElementById('chart-equity-asset')) return;
    const years = D['equity-asset'].years;
    const yrcb  = D['equity-asset'].yrcb;   // 本行（键名沿用 yrcb，换行时只换系列名）
    const abc   = D['equity-asset'].abc;    // 农业银行
    const cmb   = D['equity-asset'].cmb;    // 招商银行
    const psb   = D['equity-asset'].psb;    // 邮储银行

    const serEA = live([
        { name: SELF, type: 'line', data: yrcb, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#16a085' }, itemStyle: { color: '#16a085' },
          areaStyle: { color: 'rgba(22,160,133,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#16a085', formatter: '{c}%' } },
        peerLine('农业银行', abc, '#2874a6'),
        peerLine('招商银行', cmb, '#229954'),
        peerLine('邮储银行', psb, '#d68910')
    ]);
    initChart('chart-equity-asset')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serEA.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '权益资产比%', min: 0, max: axMax(11, yrcb, abc, cmb, psb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#16a085', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serEA
    });
})();


}

(function () {
    // 后端渲染时页面与接口同源，用相对路径（换端口/换机器都不用改代码）；
    // file:// 直接打开时没有同源可言，仍指向本机 5000 端口的开发服务。
    var BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
    var API = BASE + '/api/company_charts?code=' + window.COMPANY_CODE;
    if (typeof axios !== 'undefined') {
        axios.get(API).then(function (res) {
            // 后端 404 / 无数据：整页图位换占位说明，不调 renderAll（拿 undefined 解构会整页崩）
            if (!res.data || res.data.code !== 200 || !res.data.data) { stubAll(); return; }
            window.__companyD = res.data.data;   // 缓存原始数据供股东页银行切换器复用
            window.__applyBankIdentity(res.data.data);
            renderAll(res.data.data);
        }).catch(function (e) { console.error('company_charts fetch error', e); stubAll(); });
    }
})();

/* ────── ROE 图·快速切换银行 ──────
 * 只有业绩页（index.html）里有 #roe-banks 这排按钮，其余页面本块直接跳过。
 * 与导航条上的银行下拉框分工：下拉框换 ?code= 整页重载（整页都变成那家行），
 * 这排按钮不动页面主体，只把 ROE 一张图换成别家行的曲线 —— 用来快速对照 ROE 高低。
 * 数据按需向 /api/company_charts?code=<code> 拉（与主数据同一端点）并缓存，二次点击不再发请求。 */
(function () {
    var box = document.getElementById('roe-banks');
    if (!box) return;

    var BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
    var CACHE = {};          // code → payload；本页自身那家行进来时用 window.__companyD 填
    var cur = document.getElementById('roe-current');
    var note = document.getElementById('note-roe');
    var OWN_NOTE = note ? note.innerHTML : '';   // 本页银行的三段口径说明，切回来时还原
    var btns = [];

    // 可切换清单与导航下拉框同源：后端注入 window.__BANKS，静态打开时由 bank-header.js 兜底赋值。
    // bank-header.js 是 defer、本文件是普通脚本，所以按钮要等 DOMContentLoaded 再建。
    function banks() {
        return (Array.isArray(window.__BANKS) && window.__BANKS.length) ? window.__BANKS : [];
    }

    function setActive(code) {
        btns.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-code') === code); });
    }

    // 对比模式要塞十条线加两行图例，400px 高度不够；切回单行时还原，避免图被拉得空旷
    function setHeight(px) {
        var el = document.getElementById('chart-roe');
        if (!el || el.style.height === px) return;
        el.style.height = px;
        var ins = window.echarts && echarts.getInstanceByDom(el);
        if (ins) ins.resize();   // 容器高度是 JS 改的，ECharts 不会自己知道
    }

    function draw(code, name, D) {
        if (!document.getElementById('chart-roe')) return;   // 本页该图已被 __stub 摘掉 id
        setHeight('400px');
        window.__renderRoe(D);
        if (cur) cur.textContent = name;
        if (note) {
            note.innerHTML = code === window.COMPANY_CODE ? OWN_NOTE :
                ('当前显示 <b>' + name + '</b> 的 ROE，三段口径同上（简单 ROE / 旧准则 / 新准则加权平均净资产收益率）。' +
                 '数据来源：该行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_' + code + '.json</code>。' +
                 '按钮切回本页银行可看完整口径说明。');
        }
    }

    function drawCompare(items) {
        if (!document.getElementById('chart-roe')) return;
        setHeight('600px');
        window.__renderRoeCompare(items);
        if (cur) cur.textContent = '全部对比（' + items.length + ' 家）';
        if (note) {
            note.innerHTML = '一键对比：' + items.length + ' 家银行的 ROE 画在同一张图，每行一条线。' +
                '口径拼接规则——同一年优先取年报披露的<b>新准则加权平均净资产收益率</b>，' +
                '该年未披露时退到<b>旧准则加权平均股东权益回报率</b>，仍无则用<b>简单 ROE</b>（净利/平均权益，' +
                '仅渝农商行 2009–2013 手工补算）。因此 2018 年前后同一条线存在准则切换断口，跨段比较请留意。' +
                '各行起始年份不同（多数行数据自 2014 或 2018 年起），缺披露的年份线段断开。' +
                '本页银行画粗线并在末端标数值；银行家数超过配色轮数时，第二轮改用虚线区分。' +
                '数据来源：各行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_&lt;code&gt;.json</code>。';
        }
    }

    function pick(code, name) {
        setActive(code);
        // 本页自身那家行：主数据已在 window.__companyD 里，不再发请求
        var D = code === window.COMPANY_CODE ? window.__companyD : CACHE[code];
        if (D) { draw(code, name, D); return; }
        if (typeof axios === 'undefined') return;
        if (cur) cur.textContent = name + '（加载中…）';
        axios.get(BASE + '/api/company_charts?code=' + code).then(function (res) {
            if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
            CACHE[code] = res.data.data;
            draw(code, name, res.data.data);
        }).catch(function (e) {
            console.error('ROE 快速切换：' + code + ' 数据拉取失败', e);
            if (cur) cur.textContent = name + '（数据拉取失败）';
        });
    }

    // 一键对比：把清单里所有行的数据凑齐（缓存里没有的并发拉），谁失败就跳过谁，不因一家挂掉整图空白
    function pickAll() {
        setActive('__all');
        if (typeof axios === 'undefined') return;
        var list = banks();
        if (cur) cur.textContent = '全部对比（加载中…）';
        var jobs = list.map(function (b) {
            var D = b.code === window.COMPANY_CODE ? window.__companyD : CACHE[b.code];
            if (D) return Promise.resolve({ code: b.code, name: b.name, roe: D['roe'] });
            return axios.get(BASE + '/api/company_charts?code=' + b.code).then(function (res) {
                if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
                CACHE[b.code] = res.data.data;
                return { code: b.code, name: b.name, roe: res.data.data['roe'] };
            }).catch(function (e) {
                console.error('ROE 一键对比：' + b.code + ' 数据拉取失败', e);
                return null;
            });
        });
        Promise.all(jobs).then(function (rows) {
            // 没有 roe 这一项的行（该行数据里缺这块）也一并剔掉，免得图例挂空名字
            var items = rows.filter(function (r) { return r && r.roe && (r.roe.years || []).length; });
            if (!items.length) { if (cur) cur.textContent = '全部对比（无可用数据）'; return; }
            drawCompare(items);
        });
    }

    function build() {
        var list = banks();
        if (!list.length || box.querySelector('button')) return;
        list.forEach(function (b) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.setAttribute('data-code', b.code);
            btn.textContent = b.name;
            btn.addEventListener('click', function () { pick(b.code, b.name); });
            box.appendChild(btn);
            btns.push(btn);
        });
        // 对比按钮排在最后，用 .cmp 与单行按钮区分（样式里给了实心边框）
        var all = document.createElement('button');
        all.type = 'button';
        all.className = 'cmp';
        all.setAttribute('data-code', '__all');
        all.textContent = '一键对比全部';
        all.addEventListener('click', pickAll);
        box.appendChild(all);
        btns.push(all);
        setActive(window.COMPANY_CODE);
        // 本页银行的名字由数据里的 _bank 元信息给（HTML 里的静态文案是渝农商行版本）
        var own = list.filter(function (b) { return b.code === window.COMPANY_CODE; })[0];
        if (own && cur) cur.textContent = own.name;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
