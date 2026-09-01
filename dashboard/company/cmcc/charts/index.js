/* 中国移动「业绩」页：营运收入与增速、EBITDA 与利润率、营运支出结构、
   资本开支与自由现金流、每股盈利与股息，以及近六年明细与口径缺口。
   数据全部来自 window.CMCC.annual（历年年报财务概览），页面不硬编码数字。 */

var AN = (C.annual && C.annual.annual) || {};
var META = (C.annual && C.annual._meta) || {};
/* 有营运收入的年份即为本页 x 轴；缺披露的字段在图上留 null，不插值 */
var Y = years(AN, 'totalRevenue');
var LAST = Y[Y.length - 1], PREV = Y[Y.length - 2];
var L = AN[LAST] || {}, P = AN[PREV] || {};

/* ==== 最新财年概览 ==== */
setText('kpi-sub',
    '口径：' + LAST + ' 财年 · 营运收入 = 主营业务收入 + 其他业务收入（其他业务主要为手机等终端销售）'
    + ' · 数据来源 ' + (L._reportBasis || META.sourcePrimary || '公司年报'));
renderKpis('main-kpis', [
    { label: LAST + ' 营运收入', value: yiTxt(L.totalRevenue), delta: yoyTxt(L.totalRevenue, P.totalRevenue) },
    { label: LAST + ' 主营业务收入', value: yiTxt(L.serviceRevenue), delta: yoyTxt(L.serviceRevenue, P.serviceRevenue) },
    { label: LAST + ' EBITDA', value: yiTxt(L.ebitda), delta: yoyTxt(L.ebitda, P.ebitda) },
    { label: LAST + ' 股东应占利润', value: yiTxt(L.netProfit), delta: yoyTxt(L.netProfit, P.netProfit) },
    { label: LAST + ' 资本开支', value: yiTxt(L.capex), delta: yoyTxt(L.capex, P.capex) },
    { label: LAST + ' 每股全年股息', value: L.dividendTotal === null || L.dividendTotal === undefined
        ? '—' : fx(L.dividendTotal, 2) + ' 港元', delta: yoyTxt(L.dividendTotal, P.dividendTotal) }
]);

/* ==== 营运收入：主营 + 其他堆叠，线为营运收入同比 ==== */
mount('chart-revenue', function () {
    var o = axisBase({ x: Y, left: 84, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('营运收入同比 %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '主营业务收入（亿元）', type: 'bar', stack: 'r', barWidth: '58%',
          itemStyle: { color: NAVY }, data: pick(AN, Y, 'serviceRevenue', toYi) },
        { name: '其他业务收入（亿元）', type: 'bar', stack: 'r',
          itemStyle: { color: ERA_COLORS.other }, data: pick(AN, Y, 'otherRevenue', toYi) },
        { name: '营运收入同比（%）', type: 'line', yAxisIndex: 1, symbolSize: 7, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, connectNulls: false,
          data: Y.map(function (y, i) { return i === 0 ? null : yoy(AN[y].totalRevenue, AN[Y[i - 1]].totalRevenue); }),
          markArea: (function () {
              /* 主营/其他两分法从哪年起才有披露：之前只有营运收入一个总数，
                 柱子会只剩一层，用灰带说明这是口径问题不是业务问题 */
              var f = firstYear(AN, 'serviceRevenue');
              if (!f || f === Y[0]) return undefined;
              return gapMark(Y, Y[0], String(+f - 1), '此前只披露营运收入总额，未分主营／其他');
          })() }
    ];
    return o;
});

/* ==== EBITDA / 净利润 / 两条率 ==== */
mount('chart-profit', function () {
    var o = axisBase({ x: Y, left: 84, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('率 %', { position: 'right', splitLine: false, min: 0 })];
    var ebitdaMargin = Y.map(function (y) {
        var r = AN[y];
        if (r.ebitda === null || r.ebitda === undefined || !r.totalRevenue) return null;
        return +(r.ebitda / r.totalRevenue * 100).toFixed(1);
    });
    var netMargin = Y.map(function (y) {
        var r = AN[y];
        if (r.netProfit === null || r.netProfit === undefined || !r.totalRevenue) return null;
        return +(r.netProfit / r.totalRevenue * 100).toFixed(1);
    });
    o.series = [
        { name: 'EBITDA（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: NAVY },
          data: pick(AN, Y, 'ebitda', toYi) },
        { name: '股东应占利润（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: '#2980b9' },
          data: pick(AN, Y, 'netProfit', toYi) },
        { name: 'EBITDA 率（%，本页按营运收入现算）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD }, data: ebitdaMargin },
        { name: '股东应占利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#c0392b' }, data: netMargin }
    ];
    return o;
});

/* ==== 营运支出结构：各项占营运收入 % ==== */
var OPEX_ITEMS = [
    { field: 'networkOpex',    name: '网络运营及支撑成本', color: NAVY },
    { field: 'depreciation',   name: '折旧及摊销',         color: '#2980b9' },
    { field: 'staffCost',      name: '雇员薪酬及相关成本', color: '#16a085' },
    { field: 'sellingExpense', name: '销售费用',           color: GOLD },
    { field: 'productCost',    name: '销售产品成本',       color: '#8e44ad' },
    { field: 'otherOpex',      name: '其他营运支出',       color: '#b0bac5' }
];
mount('chart-cost', function () {
    /* 支出明细只有近年才逐项披露，x 轴收窄到有网络成本的年份，避免左侧一大片空柱 */
    var OY = years(AN, 'networkOpex');
    var o = axisBase({ x: OY, left: 84, right: 96 });
    o.yAxis = [valueAxis('占营运收入 %', { min: 0 }),
               valueAxis('营运利润率 %', { position: 'right', splitLine: false, min: 0 })];
    o.series = OPEX_ITEMS.map(function (it, i) {
        return {
            name: it.name, type: 'bar', stack: 'c', barWidth: i === 0 ? '58%' : undefined,
            itemStyle: { color: it.color },
            data: OY.map(function (y) {
                var r = AN[y];
                if (r[it.field] === null || r[it.field] === undefined || !r.totalRevenue) return null;
                return +(r[it.field] / r.totalRevenue * 100).toFixed(1);
            })
        };
    });
    o.series.push({
        name: '营运利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7, lineStyle: { width: 3 },
        itemStyle: { color: '#c0392b' },
        data: OY.map(function (y) {
            var r = AN[y];
            if (r.opProfit === null || r.opProfit === undefined || !r.totalRevenue) return null;
            return +(r.opProfit / r.totalRevenue * 100).toFixed(1);
        })
    });
    return o;
});

/* ==== 资本开支 · 折旧 · 自由现金流 ==== */
mount('chart-capex', function () {
    var o = axisBase({ x: Y, left: 88, right: 104 });
    o.yAxis = [valueAxis('亿元'),
               valueAxis('资本开支占主营业务收入 %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '资本开支（亿元，画为负值）', type: 'bar', barWidth: '30%', itemStyle: { color: '#c0392b' },
          data: Y.map(function (y) {
              var v = AN[y].capex;
              return v === null || v === undefined ? null : -toYi(v);
          }) },
        { name: '折旧及摊销（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: '#2980b9' },
          data: pick(AN, Y, 'depreciation', toYi) },
        { name: '自由现金流（亿元）', type: 'line', symbolSize: 7, lineStyle: { width: 3 },
          itemStyle: { color: '#16a085' }, data: pick(AN, Y, 'fcf', toYi) },
        { name: '资本开支占主营业务收入（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: GOLD },
          data: Y.map(function (y) {
              var r = AN[y];
              if (r.capex === null || r.capex === undefined || !r.serviceRevenue) return null;
              return +(r.capex / r.serviceRevenue * 100).toFixed(1);
          }) }
    ];
    return o;
});

/* ==== 每股盈利与股息 ==== */
mount('chart-dividend', function () {
    var o = axisBase({ x: Y, left: 84, right: 104 });
    o.yAxis = [valueAxis('每股金额', { min: 0 }),
               valueAxis('派息率 %', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '每股全年股息（港元）', type: 'bar', barWidth: '52%', itemStyle: { color: GOLD },
          data: pick(AN, Y, 'dividendTotal') },
        { name: '每股基本盈利（人民币元）', type: 'line', symbolSize: 7, lineStyle: { width: 3 },
          itemStyle: { color: NAVY }, data: pick(AN, Y, 'eps') },
        { name: '派息率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#c0392b' },
          data: pick(AN, Y, 'payoutRatio') }
    ];
    return o;
});

/* ==== 股息 KPI ==== */
(function () {
    var DY = years(AN, 'dividendTotal');
    if (!DY.length) return;
    var first = AN[DY[0]], last = AN[DY[DY.length - 1]];
    renderKpis('div-kpis', [
        { label: '有股息披露的年份', value: DY[0] + '–' + DY[DY.length - 1] + '（' + DY.length + ' 年）' },
        { label: DY[DY.length - 1] + ' 每股全年股息', value: fx(last.dividendTotal, 2) + ' 港元',
          delta: DY[0] + ' 为 ' + fx(first.dividendTotal, 2) + ' 港元' },
        { label: DY[DY.length - 1] + ' 派息率',
          value: last.payoutRatio === null || last.payoutRatio === undefined ? '—' : pct(last.payoutRatio, 0) }
    ]);
})();

/* ==== 近六年明细表 ==== */
(function () {
    var TY = Y.slice(-6);
    setHTML('tbl-head', '<th>指标</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
    var ROWS = [
        { label: '营运收入', field: 'totalRevenue', total: true },
        { label: '　主营业务收入', field: 'serviceRevenue', sub: true },
        { label: '　其他业务收入', field: 'otherRevenue', sub: true },
        { label: '营运支出', field: 'opexTotal' },
        { label: '营运利润', field: 'opProfit' },
        { label: 'EBITDA', field: 'ebitda' },
        { label: '股东应占利润', field: 'netProfit', total: true },
        { label: '资本开支', field: 'capex' },
        { label: '经营活动现金流净额', field: 'ocf' },
        { label: '自由现金流', field: 'fcf' },
        { label: '每股基本盈利（人民币元）', field: 'eps', dec: 2 },
        { label: '每股全年股息（港元）', field: 'dividendTotal', dec: 2 },
        { label: '派息率（%）', field: 'payoutRatio', dec: 0 }
    ];
    renderRows('tbl-body', ROWS.map(function (r) {
        return {
            _th: true,
            _cls: r.total ? 'row-total' : (r.sub ? 'row-sub' : ''),
            cells: [r.label].concat(TY.map(function (y) {
                var v = AN[y] ? AN[y][r.field] : null;
                if (v === null || v === undefined) return '—';
                if (r.dec !== undefined) return fx(v, r.dec);
                return v < 0 ? '(' + thou(-v) + ')' : thou(v);
            }))
        };
    }));
})();

/* ==== 说明文字：全部由数据现算，改数不用改文案 ==== */
(function () {
    var f = AN[Y[0]];
    setHTML('kpi-note',
        '<b>这家公司的报表从 ' + Y[0] + ' 年的 ' + yiTxt(f.totalRevenue) + ' 营运收入长到 '
        + LAST + ' 年的 ' + yiTxt(L.totalRevenue) + '，'
        + (Y.length > 1 ? '合计 ' + (+LAST - +Y[0]) + ' 年、年化 '
            + fx((Math.pow(L.totalRevenue / f.totalRevenue, 1 / (+LAST - +Y[0])) - 1) * 100, 1) + '%。</b>' : '</b>')
        + '增长的形状值得注意：前十几年靠客户数扩张，近十年营运收入增速已降到个位数，'
        + '真正在变的是<b>收入里面的产品构成</b>——那部分放在「产品更迭」页。');

    setHTML('revenue-note',
        '柱子分两层：深蓝是主营业务收入（通信/算力/智能服务），灰色是其他业务收入（主要为手机等终端销售）。'
        + '终端销售毛利很薄，把它和主营混在一起看会低估主业的利润率——这也是公司自己在年报里'
        + '始终把两者分开呈报的原因。' + LAST + ' 年其他业务收入 ' + yiTxt(L.otherRevenue)
        + '，占营运收入 ' + (L.otherRevenue && L.totalRevenue ? pct(L.otherRevenue / L.totalRevenue * 100) : '—') + '。');

    setHTML('profit-note',
        '<b>EBITDA 率与净利率的差额几乎全部是折旧摊销</b>——运营商是重资产生意，'
        + '每一轮制式换代（3G/4G/5G）都先砸资本开支、再用十年折旧摊回来。'
        + LAST + ' 年 EBITDA ' + yiTxt(L.ebitda) + '、股东应占利润 ' + yiTxt(L.netProfit)
        + '，两者之差 ' + (L.ebitda != null && L.netProfit != null ? yiTxt(L.ebitda - L.netProfit) : '—')
        + '，主要由折旧及摊销 ' + yiTxt(L.depreciation) + ' 与税项构成。'
        + '<b>口径提示：</b>本页 EBITDA 率按营运收入现算，公司年报部分年份改用「EBITDA / 主营业务收入」口径列示，'
        + '两者分母不同、数值会差 3–5 个百分点，跨年引用时务必看清分母。');

    setHTML('cost-note',
        '这张图只画到有逐项披露的年份为止。<b>销售产品成本（终端）这一层是「非主业」的重量</b>，'
        + '它涨的时候营运收入也涨，但几乎不带利润；真正决定利润率的是网络运营及支撑成本与折旧摊销两层。');

    setHTML('capex-note',
        '资本开支画成负值是为了和折旧摊销上下对照：<b>当资本开支的绝对额低于折旧摊销时，'
        + '意味着这一轮网络投资已经过了峰值</b>，账面开始"收回"前几年的投入。'
        + (L.capex != null && L.depreciation != null
            ? LAST + ' 年资本开支 ' + yiTxt(L.capex) + '、折旧及摊销 ' + yiTxt(L.depreciation) + '。'
            : ''));

    setHTML('dividend-note',
        '<b>币种不同请注意：</b>每股盈利以人民币计、每股股息以港元派发，图上两者同轴只是为了看趋势，'
        + '直接相除得不到真实派息率——派息率一栏用的是公司年报自己披露的口径。');

    /* 口径缺口：由数据里各字段的实际覆盖区间现算，不手写年份 */
    var GAP_FIELDS = [
        ['serviceRevenue', '主营业务收入'],
        ['opexTotal', '营运支出总额'],
        ['networkOpex', '营运支出逐项明细'],
        ['fcf', '自由现金流'],
        ['payoutRatio', '派息率'],
        ['capex', '资本开支']
    ];
    var items = GAP_FIELDS.map(function (p) {
        var ys = years(AN, p[0]);
        if (!ys.length) return '<b>' + p[1] + '</b>：本页数据源中无任何年份披露。';
        var missing = Y.filter(function (y) {
            return +y >= +ys[0] && +y <= +ys[ys.length - 1] && (AN[y][p[0]] === null || AN[y][p[0]] === undefined);
        });
        return '<b>' + p[1] + '</b>：覆盖 ' + ys[0] + '–' + ys[ys.length - 1] + '（共 ' + ys.length + ' 年）'
            + (+ys[0] > +Y[0] ? '，' + Y[0] + '–' + (+ys[0] - 1) + ' 未披露' : '')
            + (missing.length ? '，区间内缺 ' + missing.join('、') : '') + '。';
    });
    if (META.gaps) {
        Object.keys(META.gaps).forEach(function (k) {
            items.push('<b>' + k + '</b>：' + META.gaps[k]);
        });
    }
    items.push('<b>来源与优先级</b>：' + (META.sourcePriority
        || '2022–2025 年以 A 股年报为准，1997–2021 年用港股年报；官网投资者关系页仅用于交叉核对。'));
    renderList('gaps-list', items);
})();
