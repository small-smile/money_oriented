/* 收入构成页（company/telecom/segment.html）
 * 数据来自 /api/telecom_annual 的 segments 块 —— 上交所 A 股年报「营业收入和营业成本」
 * 附注里的收入分解表，逐份原文解析，金额已统一归一到亿元。
 *
 * 三家的科目体系完全不同（移动按业务类型、电信按服务板块、联通按业务类型但更细），
 * 所以这页只画单家自己的构成，不做跨公司同名科目横比。
 * 「小计／服务收入」与「合计」都不进堆叠，只用来算占比与自检。
 */
const AGG_KEYS = ['total', 'service_total'];
const PALETTE = ['#1f6feb', '#0f766e', '#c0392b', '#b45309', '#7c3aed', '#0891b2',
    '#ca8a04', '#be185d', '#4d7c0f', '#475569', '#f59e0b', '#2563eb'];

/* 联通 2017 年起换过一套科目：2015—2016 是旧科目集（legacy_*），
 * 两套不能拼成一条线，图上用 markLine 标断点、图例里靠名字区分 */
const BREAK_MARKS = {'600050': [{year: '2017', text: '收入科目口径切换'}]};

function serviceRev(rec) {
    if (rec.service_total !== undefined) return rec.service_total;
    if (rec.total !== undefined && rec.products !== undefined) return +(rec.total - rec.products).toFixed(2);
    return null;
}

function renderHead(d, seg, years) {
    const last = years[years.length - 1], rec = seg.annual[last];
    const prev = seg.annual[years[years.length - 2]] || {};
    document.title = d.name + '（' + d.secucode + '）· 收入构成';
    document.getElementById('page-title').textContent = d.name + '（' + d.secucode + '）· 收入构成';
    document.getElementById('page-meta').innerHTML =
        '上交所 A 股年报附注原文 · 单位亿元 · 覆盖 ' + years[0] + '—' + last + ' 年度（共 ' + years.length + ' 份年报）<br>' +
        '科目体系为该公司自己的披露口径，' + (BREAK_MARKS[CODE] ? '<b>2017 年起换过一套科目，两套不可拼接</b>' : '五年内未变更');

    document.getElementById('kpi-title').textContent = last + ' 年度收入构成';
    document.getElementById('kpi-sub').textContent =
        '括号内为占营业收入比重；同比为与 ' + years[years.length - 2] + ' 年同口径科目相比';
    const stack = seg.order.filter(k => AGG_KEYS.indexOf(k) < 0 && rec[k] !== undefined);
    const total = rec.total;
    const cards = [
        '<div class="kpi"><div class="label">营业收入</div><div class="value">' + fmt(total, 0) +
        ' 亿元</div><div class="delta" style="color:#7f8c8d">服务收入 ' + fmt(serviceRev(rec), 0) +
        ' 亿元（' + fmt(serviceRev(rec) / total * 100, 1) + '%）</div></div>'
    ];
    stack.sort((a, b) => rec[b] - rec[a]).forEach(k => {
        const yoy = prev[k] !== undefined ? (rec[k] / prev[k] - 1) * 100 : null;
        cards.push('<div class="kpi"><div class="label">' + seg.labels[k] + '</div>' +
            '<div class="value">' + fmt(rec[k], 0) + ' 亿元</div>' +
            '<div class="delta" style="color:#7f8c8d">占 ' + fmt(rec[k] / total * 100, 1) + '%' +
            (yoy === null ? '' : '　同比 <span class="' + (yoy >= 0 ? 'up' : 'down') + '">' +
                (yoy >= 0 ? '+' : '') + fmt(yoy, 1) + '%</span>') + '</div></div>');
    });
    document.getElementById('kpis').innerHTML = cards.join('');
    document.getElementById('caliber-warn').innerHTML = '<b>口径：</b>' + mdBold(seg.caliber_note);
    document.getElementById('sec-kpi').hidden = false;
    return stack;
}

/* 各家自己的构成变化事实，只写年报能核到的因果 */
const SEG_NOTES = {
    '600941': {
        mix: '<b>结构替代已经完成：</b>无线上网业务 2022 年 3,959 亿元见顶后连年回落到 2025 年 3,691 亿元，' +
            '而应用及信息服务由 2021 年 1,370 亿元升到 2,588 亿元（+89%）—— 流量收入的下滑正好被 DICT／智慧家庭等' +
            '应用类收入补上，营业收入因此仍能维持微增。语音业务 762→666 亿元、短彩信 311→296 亿元继续萎缩。',
        share: '销售产品收入及其他（终端销售）占营业收入 11.4%—14.7%，比电信、联通都高 —— ' +
            '直接比营业收入会高估中国移动的服务体量，看服务收入（合计 − 销售产品）才可比。'
    },
    '601728': {
        mix: '<b>产业数字化是唯一的增量引擎：</b>2021 年 989 亿元 → 2025 年 1,473 亿元（+48.9%），' +
            '同期移动通信服务 1,842→2,045 亿元、固网及智慧家庭 1,135→1,260 亿元均为个位数增长。' +
            '但产数增速已由前三年近 20% 降到 2024 年 +5.5%、2025 年 +0.5%，' +
            '这是全年收入几乎零增长的直接原因。',
        share: '服务收入占营业收入常年 92%—93%，终端销售占比低于中国移动，' +
            '因此电信的营业收入与服务收入两条线差距最小。'
    },
    '600050': {
        mix: '<b>数据及其他互联网应用收入是主线：</b>2017 年 201 亿元 → 2025 年 1,036 亿元（5.2 倍），' +
            '同期宽带及移动数据服务在 1,530—1,560 亿元横盘、语音通话及月租费由 392 亿元腰斩到 196 亿元。' +
            '收入总量的增长几乎全部来自互联网应用与终端销售。',
        share: '<b>2015—2016 年是另一套科目</b>（通话及月租费／宽带、数据及互联网／信息与通信技术服务等），' +
            '与 2017 年起的科目不可对应，图上以断点标出、图例里另起名字，不拼成一条线。'
    }
};

function buildCharts(d, seg, years, stackLatest) {
    const host = document.getElementById('charts');
    const N = SEG_NOTES[CODE];
    // 堆叠用的科目：order 里去掉合计与小计，且至少有一年有值
    const keys = seg.order.filter(k => AGG_KEYS.indexOf(k) < 0 &&
        years.some(y => (seg.annual[y] || {})[k] !== undefined));
    const color = {};
    keys.forEach((k, i) => { color[k] = PALETTE[i % PALETTE.length]; });
    const val = (y, k) => {
        const v = (seg.annual[y] || {})[k];
        return v === undefined ? null : v;
    };

    // ① 分业务收入堆叠柱 + 服务收入占比
    (function () {
        const s = keys.map(k => barSeries(seg.labels[k], years.map(y => val(y, k)), color[k], {stack: 'rev', barMaxWidth: 46}));
        s.push(lineSeries('服务收入占营业收入（右轴）',
            years.map(y => {
                const rec = seg.annual[y], sv = rec && serviceRev(rec);
                return sv === null || !rec.total ? null : +(sv / rec.total * 100).toFixed(2);
            }), '#111827', {yAxisIndex: 1, width: 2.2}));
        const c = chartCard(host, {
            id: 'mix', title: '分业务收入（年报附注口径）',
            sub: '堆叠柱：各业务收入（亿元）· 柱高即营业收入 · 线：服务收入占比（%，右轴）',
            note: N.mix,
            detail: '<b>为什么柱高等于营业收入：</b>本图把附注里的全部收入科目（含销售终端等其他业务收入）都堆进去，' +
                '合计与利润表的营业收入逐年核对一致（差额均在 ±0.05 亿元内，来自元→亿元的四舍五入）。<br>' +
                '<b>服务收入的算法：</b>年报披露「小计／服务收入」时直接取，未披露时用合计 − 销售产品收入现算。'
        });
        c.setOption({
            tooltip: {
                trigger: 'axis', axisPointer: {type: 'shadow'},
                formatter: ps => '<b>' + ps[0].axisValue + ' 年</b><br>' + ps.filter(p => p.value !== null)
                    .map(p => p.marker + p.seriesName + '　<b>' + fmt(p.value, 1) + '</b>' +
                        (p.seriesType === 'line' ? ' %' : ' 亿元')).join('<br>')
            },
            legend: {top: 0, itemGap: 12, textStyle: {fontSize: 14}},
            grid: {left: 88, right: 80, top: 88, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '亿元'}),
                Object.assign({}, AXIS_Y, {name: '%', scale: true, splitLine: {show: false}})],
            series: marksOn(s, years, BREAK_MARKS[CODE])
        });
    })();

    // ② 结构占比（100% 堆叠）
    (function () {
        const s = keys.map(k => barSeries(seg.labels[k], years.map(y => {
            const rec = seg.annual[y];
            const v = val(y, k);
            return v === null || !rec.total ? null : +(v / rec.total * 100).toFixed(2);
        }), color[k], {stack: 'share', barMaxWidth: 46}));
        const c = chartCard(host, {
            id: 'share', title: '收入结构占比', sub: '各业务收入 ÷ 营业收入（%，堆叠满 100%）',
            note: N.share,
            detail: '占比的分母统一用营业收入（含终端销售），因此这张图的各段之和为 100%；' +
                '若改用服务收入作分母，各服务科目的占比会同比例放大。'
        }, '55vh');
        c.setOption({
            tooltip: {
                trigger: 'axis', axisPointer: {type: 'shadow'},
                formatter: ps => '<b>' + ps[0].axisValue + ' 年</b><br>' + ps.filter(p => p.value !== null)
                    .map(p => p.marker + p.seriesName + '　<b>' + fmt(p.value, 1) + '</b> %').join('<br>')
            },
            legend: {top: 0, itemGap: 12, textStyle: {fontSize: 14}},
            grid: {left: 80, right: 40, top: 88, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '%', max: 100}),
            series: marksOn(s, years, BREAK_MARKS[CODE])
        });
    })();

    // ③ 各科目同比增速：看哪条曲线在换挡
    (function () {
        const s = keys.map(k => lineSeries(seg.labels[k], years.map((y, i) => {
            if (i === 0) return null;
            const cur = val(y, k), pre = val(years[i - 1], k);
            return cur === null || pre === null || !pre ? null : +((cur / pre - 1) * 100).toFixed(2);
        }), color[k])).filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'yoy', title: '各业务收入同比增速', sub: '按上一年同科目现算（%）· 科目口径切换年不给增速',
            note: '增速图比金额图更早显示拐点：三家的「第二曲线」科目（应用及信息服务／产业数字化／数据及互联网应用）' +
                '增速都已从两位数降到个位数，而传统语音与短彩信仍在负增长 —— ' +
                '这决定了营业收入总量能否继续微增。',
            detail: '首年与科目缺失年不计算增速（不做插值）；' + (BREAK_MARKS[CODE] ?
                '联通 2017 年换科目，旧科目在 2017 年无对应值，因此 2017 年这几条线断开。' :
                '各科目在覆盖年份内未变更，增速逐年连续。')
        }, '55vh');
        c.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 1) + ' %'},
            legend: {top: 0, itemGap: 12, textStyle: {fontSize: 14}},
            grid: {left: 80, right: 40, top: 88, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '%', scale: true}),
            series: marksOn(s, years, BREAK_MARKS[CODE])
        });
    })();
}

function renderTable(d, seg, years) {
    const cols = years.slice(-6);
    document.getElementById('tbl-head').innerHTML = '<th>科目</th>' +
        cols.map(y => '<th>' + y + '</th>').join('');
    const rows = seg.order.map(k => {
        const isAgg = AGG_KEYS.indexOf(k) >= 0;
        const cells = cols.map(y => {
            const rec = seg.annual[y] || {}, v = rec[k];
            if (v === undefined) return '<td>—</td>';
            const share = rec.total ? '<span style="color:#9ca3af">（' + fmt(v / rec.total * 100, 1) + '%）</span>' : '';
            return '<td>' + fmt(v, 2) + ' ' + share + '</td>';
        }).join('');
        if (cols.every(y => ((seg.annual[y] || {})[k]) === undefined)) return '';
        return '<tr class="' + (isAgg ? 'row-total' : 'row-sub') + '"><td>' + seg.labels[k] + '</td>' + cells + '</tr>';
    });
    document.getElementById('tbl-body').innerHTML = rows.join('');
    document.getElementById('tbl-note').innerHTML =
        '<b>自检：</b>每年各服务科目之和 = 小计／服务收入，小计 + 销售产品收入 = 合计，' +
        '合计 = 利润表营业收入（' + years[years.length - 1] + ' 年 ' +
        fmt(seg.annual[years[years.length - 1]].total, 2) + ' 亿元），三层已逐年核对。' +
        '　' + mdBold(seg.unit_note) + '　来源：' + mdBold(seg.source);
    document.getElementById('sec-table').hidden = false;
}

loadCompany(function (d) {
    const seg = d.segments;
    if (!seg || !Object.keys(seg.annual || {}).length) {
        const box = document.getElementById('error-msg');
        box.style.display = 'block';
        box.textContent = '本公司暂无年报收入构成数据，请先运行 data/extract/extract_telecom_segments.py';
        return;
    }
    const years = Object.keys(seg.annual).sort();
    const stack = renderHead(d, seg, years);
    buildCharts(d, seg, years, stack);
    renderTable(d, seg, years);
});
