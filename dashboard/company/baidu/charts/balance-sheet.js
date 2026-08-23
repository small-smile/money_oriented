/* 百度详情页 · 资产与现金（balance-sheet.html）
 *
 * 数据只来自 data.js 注入的 window.BAIDU：
 *   B.annual.annual  —— 资产负债表科目 FY2008–FY2025（SEC XBRL，与历年 20-F 同源）
 *   B.profile.vie    —— FY2025 20-F 的 VIE 余额表与收入占比披露
 * 页面里不手抄任何比率：资产负债率、净现金、商誉占资产比重都在这里现算。
 *
 * 两处必须现算而不能直接取字段的地方：
 *   ① 有息负债：XBRL 的 LongTermDebt（含当期部分）自 FY2015 才连续披露，
 *      FY2013–FY2014 缺该合计数，只有高级票据分项，故按分项回退并在页面上标明；
 *   ② 净现金：AN[y].netCash 是「现金 + 短期投资 − longTermDebt」的机械算法，
 *      在上述缺失年份等于没有扣负债，这里改用回退后的负债重算。
 */
var AN = (B.annual && B.annual.annual) || {};
var VIE = (B.profile && B.profile.vie) || {};

/* 有资产负债表的年份：FY2008 起 */
var BY = Object.keys(AN).filter(function (y) { return AN[y].assets != null; }).sort();
var LAST = BY[BY.length - 1], PREV = BY[BY.length - 2];
var L = AN[LAST], P = AN[PREV];

function yi(mn) { return mn === null || mn === undefined ? null : +(mn / 100).toFixed(2); }
function yiTxt(mn) { return mn === null || mn === undefined ? '—' : fx(yi(mn), 2) + ' 亿'; }
function yoyTxt(cur, prv) {
    if (cur === null || prv === null || cur === undefined || prv === undefined) return '';
    if (cur > 0 && prv > 0) return '同比 ' + fx((cur / prv - 1) * 100, 1) + '%';
    return '上年 ' + fx(yi(prv), 2) + ' 亿';
}
/* 有息负债：优先用含当期部分的合计数，缺失年份回退到票据分项之和 */
function debtOf(y) {
    var r = AN[y];
    if (r.longTermDebt !== null && r.longTermDebt !== undefined) return r.longTermDebt;
    var s = (r.seniorNotes || 0) + (r.convertibleDebt || 0);
    return s || null;
}
function cashPile(y) { return (AN[y].cash || 0) + (AN[y].shortTermInv || 0); }
function netCashOf(y) { return cashPile(y) - (debtOf(y) || 0); }
function levOf(y) { return AN[y].liabilities / AN[y].assets * 100; }
/* 总资产减负债、归母权益、少数股东权益之后的残余：主要是可赎回非控股权益等中间层科目 */
function residOf(y) {
    var r = AN[y];
    return r.assets - r.liabilities - (r.equity || 0) - (r.minorityInterest || 0);
}
function noncurrentOf(y) {
    var r = AN[y];
    return r.liabilitiesCurrent == null ? null : r.liabilities - r.liabilitiesCurrent;
}
/* ==== FY2025 年末概览 ==== */
setText('kpi-sub', '口径：' + LAST + '-12-31 资产负债表 · 与 ' + PREV
    + '-12-31 比较 · 金额换算为人民币亿元 · 权益为归属母公司口径');
renderKpis('bs-kpis', [
    { label: LAST + ' 总资产', value: yiTxt(L.assets), delta: yoyTxt(L.assets, P.assets) },
    { label: LAST + ' 归母股东权益', value: yiTxt(L.equity), delta: yoyTxt(L.equity, P.equity) },
    { label: LAST + ' 资产负债率', value: pct(levOf(LAST)),
      delta: '上年 ' + pct(levOf(PREV)) },
    { label: LAST + ' 现金 + 短期投资', value: yiTxt(cashPile(LAST)),
      delta: yoyTxt(cashPile(LAST), cashPile(PREV)) },
    { label: LAST + ' 有息负债', value: yiTxt(debtOf(LAST)),
      delta: yoyTxt(debtOf(LAST), debtOf(PREV)) },
    { label: LAST + ' 净现金', value: yiTxt(netCashOf(LAST)),
      delta: yoyTxt(netCashOf(LAST), netCashOf(PREV)) }
]);
setHTML('kpi-note',
    '<b>资产表侧的故事和利润表侧相反：' + LAST + ' 总资产仍在增长，但「可动用的钱」在快速变薄。</b>'
    + '总资产 ' + yiTxt(L.assets) + '（' + yoyTxt(L.assets, P.assets)
    + '），资产负债率 ' + pct(levOf(LAST)) + '，仍处在 FY2017 以来的低位（FY2017 曾达 '
    + pct(levOf('2017')) + '）；但现金加短期投资已从 FY2023 的 ' + yiTxt(cashPile('2023'))
    + ' 连降两年到 ' + yiTxt(cashPile(LAST)) + '，同期有息负债回升到 ' + yiTxt(debtOf(LAST))
    + '，于是<b>净现金从 ' + yiTxt(netCashOf('2023')) + ' 降到 ' + yiTxt(netCashOf(LAST))
    + '，两年缩水超过一半</b>。同一年商誉从 ' + yiTxt(P.goodwill) + ' 增至 ' + yiTxt(L.goodwill)
    + '，而长期资产减值计提 ' + yiTxt(L.assetImpairment)
    + '——两者是不同科目，本页数据源（XBRL 余额）只给金额、不解释增减原因，故不在此推测。'
    );
/* ==== 资产负债结构 ==== */
mount('chart-assets', function () {
    var o = axisBase({ x: BY, left: 88, right: 96, top: 76 });
    o.legend.top = 4;
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('资产负债率 %', { position: 'right', splitLine: false, min: 0, max: 60 })];
    o.series = [
        { name: '总负债（亿元）', type: 'bar', stack: 'a', barWidth: '56%', itemStyle: { color: '#c0392b' },
          data: BY.map(function (y) { return yi(AN[y].liabilities); }) },
        { name: '少数股东权益（亿元）', type: 'bar', stack: 'a', itemStyle: { color: '#16a085' },
          data: BY.map(function (y) { return yi(AN[y].minorityInterest); }) },
        { name: '归母股东权益（亿元）', type: 'bar', stack: 'a', itemStyle: { color: NAVY },
          data: BY.map(function (y) { return yi(AN[y].equity); }) },
        /* 三项相加与总资产的差额单独画出来，不硬塞进权益，否则读者会以为权益更厚 */
        { name: '未归入上述三项的残余（亿元）', type: 'bar', stack: 'a',
          itemStyle: { color: RESIDUAL_PATTERN, borderColor: '#999', borderWidth: 1 },
          data: BY.map(function (y) { return yi(residOf(y)); }) },
        { name: '资产负债率（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: BY.map(function (y) { return +levOf(y).toFixed(2); }) }
    ];
    return o;
});

mount('chart-liab', function () {
    var o = axisBase({ x: BY, left: 88, right: 96, top: 44 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('流动负债占比 %', { position: 'right', splitLine: false, min: 0, max: 100 })];
    o.series = [
        { name: '流动负债（亿元）', type: 'bar', stack: 'l', barWidth: '56%',
          itemStyle: { color: shade('#c0392b', 0.35) },
          data: BY.map(function (y) { return yi(AN[y].liabilitiesCurrent); }) },
        { name: '非流动负债（亿元）', type: 'bar', stack: 'l', itemStyle: { color: '#8e44ad' },
          data: BY.map(function (y) { return yi(noncurrentOf(y)); }) },
        { name: '流动负债占总负债（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD },
          data: BY.map(function (y) {
              var c = AN[y].liabilitiesCurrent;
              return c == null ? null : +(c / AN[y].liabilities * 100).toFixed(2);
          }) }
    ];
    return o;
});
setHTML('structure-note',
    '<b>杠杆的高点在 FY2017，之后一路回落。</b>资产负债率从 FY2008 的 ' + pct(levOf('2008'))
    + ' 升到 FY2017 的 ' + pct(levOf('2017')) + '（发债与并表爱奇艺的共同结果），此后逐年下行到 '
    + LAST + ' 的 ' + pct(levOf(LAST)) + '。灰斜线的「残余」是<b>总资产减去总负债、归母权益与少数股东权益后的差额</b>，'
    + LAST + ' 为 ' + yiTxt(residOf(LAST)) + '（占总资产 ' + pct(residOf(LAST) / L.assets * 100)
    + '）：这类中间层科目（如可赎回非控股权益）既不在负债标签里、也不在权益标签里，'
    + '本页数据源无法进一步拆分，因此按项目惯例用灰斜线单列，不并入任何一侧。'
    + '<br><br>负债内部结构（第二张图）：早年负债几乎全是流动负债（FY2008 流动负债占总负债 '
    + pct(AN['2008'].liabilitiesCurrent / AN['2008'].liabilities * 100)
    + '），FY2012 起开始发行长期票据，流动占比在 FY2013 降到 '
    + pct(AN['2013'].liabilitiesCurrent / AN['2013'].liabilities * 100) + ' 的低点；'
    + LAST + ' 为 ' + pct(L.liabilitiesCurrent / L.liabilities * 100)
    + '（流动 ' + yiTxt(L.liabilitiesCurrent) + ' + 非流动 ' + yiTxt(noncurrentOf(LAST)) + '）。'
    );
/* ==== 现金、短期投资与有息负债 ==== */
mount('chart-netcash', function () {
    var o = axisBase({ x: BY, left: 88, right: 96 });
    o.yAxis = [valueAxis('亿元')];
    o.series = [
        { name: '现金及等价物（亿元）', type: 'bar', stack: 'c', barWidth: '56%', itemStyle: { color: NAVY },
          data: BY.map(function (y) { return yi(AN[y].cash); }) },
        { name: '短期投资（亿元）', type: 'bar', stack: 'c', itemStyle: { color: '#2980b9' },
          data: BY.map(function (y) { return yi(AN[y].shortTermInv); }) },
        /* 负债画为负值，与上方现金对照；FY2013–FY2014 用票据分项回退，见下方说明 */
        { name: '有息负债（亿元，画为负值）', type: 'bar', barWidth: '56%', itemStyle: { color: '#c0392b' },
          data: BY.map(function (y) { var d = debtOf(y); return d ? -yi(d) : null; }) },
        { name: '净现金（亿元）', type: 'line', symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: BY.map(function (y) { return yi(netCashOf(y)); }) }
    ];
    return o;
});
setHTML('netcash-note',
    '<b>净现金在 FY2023 见顶（' + yiTxt(netCashOf('2023')) + '），随后两年连降至 '
    + yiTxt(netCashOf(LAST)) + '。</b>拆开看：现金及等价物从 FY2022 的 ' + yiTxt(AN['2022'].cash)
    + ' 降到 ' + yiTxt(L.cash) + '，短期投资从 FY2023 的 ' + yiTxt(AN['2023'].shortTermInv)
    + ' 降到 ' + yiTxt(L.shortTermInv) + '，同时有息负债在 ' + LAST + ' 回升 '
    + yoyTxt(debtOf(LAST), debtOf(PREV)) + '（' + yiTxt(debtOf(PREV)) + ' → ' + yiTxt(debtOf(LAST)) + '）。'
    + '钱去哪了在同一份年报里对得上：' + LAST + ' 经营活动现金流为<b>净流出 '
    + yiTxt(-L.opCashFlow) + '</b>（上年为净流入 ' + yiTxt(P.opCashFlow) + '），'
    + '同期资本开支 ' + yiTxt(L.capex) + '、回购 ' + yiTxt(L.buyback) + '——三者叠加，'
    + '现金池只能靠增加有息负债来补。'
    + '<br><br><b>口径提示：</b>「短期投资」只含年报归为短期投资的部分，长期投资、权益法投资与长期理财都不在内，'
    + '所以这条净现金是<b>狭义口径</b>，不等于「全部可动用金融资产减全部负债」；'
    + 'FY2013–FY2014 的披露里没有含当期部分的有息负债合计数，这两年用高级票据余额（'
    + yiTxt(AN['2013'].seniorNotes) + ' / ' + yiTxt(AN['2014'].seniorNotes) + '）替代，'
    + '因此这两年的净现金与其他年份不完全可比。'
    );
/* ==== 商誉与减值 ==== */
mount('chart-goodwill', function () {
    /* 商誉自 FY2008 起披露，减值自 FY2011 起；三条都放同一金额轴，便于比大小 */
    var o = axisBase({ x: BY, left: 88, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('商誉占总资产 %', { position: 'right', splitLine: false, min: 0, max: 25 })];
    o.series = [
        { name: '年末商誉余额（亿元）', type: 'bar', barWidth: '36%', itemStyle: { color: NAVY },
          data: BY.map(function (y) { return yi(AN[y].goodwill); }) },
        { name: '当年长期资产减值（亿元）', type: 'bar', barWidth: '36%', itemStyle: { color: '#c0392b' },
          data: BY.map(function (y) { return yi(AN[y].assetImpairment); }) },
        { name: '当年商誉减值（亿元）', type: 'bar', barWidth: '36%', itemStyle: { color: '#e67e22' },
          data: BY.map(function (y) { return yi(AN[y].goodwillImpairment); }) },
        { name: '商誉占总资产（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD },
          data: BY.map(function (y) {
              return AN[y].goodwill == null ? null : +(AN[y].goodwill / AN[y].assets * 100).toFixed(2);
          }) }
    ];
    return o;
});
setHTML('impair-note',
    '<b>商誉的相对重要性早已从 FY2013 的高点大幅回落，但减值是另一条线。</b>商誉余额在 FY2013 达 '
    + yiTxt(AN['2013'].goodwill) + '，占总资产 ' + pct(AN['2013'].goodwill / AN['2013'].assets * 100)
    + '（当年多笔收购的结果），此后余额长期停在 220–230 亿区间，占总资产比重一路降到 FY2024 的 '
    + pct(P.goodwill / P.assets * 100) + '；' + LAST + ' 余额升至 ' + yiTxt(L.goodwill) + '（占 '
    + pct(L.goodwill / L.assets * 100) + '）。减值方面，金额最大的两年是 FY2019 的 '
    + yiTxt(AN['2019'].assetImpairment) + ' 与 ' + LAST + ' 的 ' + yiTxt(L.assetImpairment)
    + '；<b>「长期资产减值」与「商誉减值」在年报里是两个科目</b>，本页分开画：'
    + '商誉减值只有 FY2011 有 ' + yiTxt(AN['2011'].goodwillImpairment)
    + ' 的记录，其余披露年份为 0，' + LAST + ' 未单列商誉减值——'
    + '也就是说 ' + LAST + ' 的巨额减值计提在长期资产（含无形与固定资产）一侧，不是冲减商誉。'
    + '<b>口径提示：</b>商誉减值只在 FY2010–FY2013 与 FY2021–FY2024 有明确列示，'
    + '其余年份图上留空，是披露缺口而非「金额为 0」。'
    );
/* ==== 固定资产、使用权资产与资本开支 ==== */
mount('chart-ppe', function () {
    var o = axisBase({ x: BY, left: 88, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('资本开支 亿元', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '固定资产净额（亿元）', type: 'bar', stack: 'p', barWidth: '56%', itemStyle: { color: NAVY },
          data: BY.map(function (y) { return yi(AN[y].ppe); }) },
        { name: '经营租赁使用权资产（亿元）', type: 'bar', stack: 'p', itemStyle: { color: '#2980b9' },
          data: BY.map(function (y) { return yi(AN[y].opLeaseRou); }) },
        { name: '当年资本开支（亿元）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: BY.map(function (y) { return yi(AN[y].capex); }) }
    ];
    return o;
});
setHTML('ppe-note',
    '<b>固定资产在 FY2024 见顶后于 ' + LAST + ' 回落，而资本开支反而创下区间新高。</b>'
    + '固定资产净额从 FY2023 的 ' + yiTxt(AN['2023'].ppe) + '、FY2024 的 ' + yiTxt(P.ppe)
    + ' 降到 ' + yiTxt(L.ppe) + '，同年资本开支 ' + yiTxt(L.capex) + '（'
    + yoyTxt(L.capex, P.capex) + '，为 FY2008 以来最高）——一边大额投入、一边账面净额下降，'
    + '与当年计提的长期资产减值 ' + yiTxt(L.assetImpairment) + ' 方向一致。'
    + '<b>口径提示：</b>经营租赁使用权资产是 FY2019 起采用新租赁准则后才出现的科目（FY2018 列示为 0），'
    + 'FY2018 及以前的柱子里没有这一块，不代表当年没有租赁。'
    );
/* ==== 回购与少数股东权益 ==== */
mount('chart-buyback', function () {
    /* 回购自 FY2009 起才有记录，从 FY2009 连续排到最新年，缺披露的年份（FY2012）留空不补 0 */
    var YY = BY.filter(function (y) { return y >= '2009'; });
    var o = axisBase({ x: YY, left: 76, right: 30, bottom: 40 });
    o.legend.top = 6;
    o.yAxis = [valueAxis('亿元', { min: 0 })];
    o.series = [
        { name: '当年回购金额（亿元）', type: 'bar', barWidth: '56%', itemStyle: { color: GOLD },
          data: YY.map(function (y) { return yi(AN[y].buyback); }) }
    ];
    return o;
});
mount('chart-nci', function () {
    /* 少数股东权益自 FY2010 起才有余额，同样单独取区间 */
    var YY = BY.filter(function (y) { return AN[y].minorityInterest != null; });
    var o = axisBase({ x: YY, left: 76, right: 30, bottom: 40 });
    o.legend.top = 6;
    o.yAxis = [valueAxis('亿元')];
    o.series = [
        { name: '年末少数股东权益（亿元）', type: 'bar', barWidth: '56%', itemStyle: { color: '#16a085' },
          data: YY.map(function (y) { return yi(AN[y].minorityInterest); }) }
    ];
    return o;
});
(function () {
    var cum = BY.reduce(function (s, y) { return s + (AN[y].buyback || 0); }, 0);
    var peak = BY.reduce(function (m, y) {
        return (AN[y].buyback || 0) > (AN[m] && AN[m].buyback || 0) ? y : m;
    }, BY[0]);
    setHTML('return-note',
        '<b>回购是百度目前唯一的股东回报方式——开曼母公司自上市以来从未宣派或支付股息（FY'
        + LAST + ' 年报原文）。</b>FY2009 起累计回购 '
        + yiTxt(cum) + '，单年最高是 FY' + peak + ' 的 ' + yiTxt(AN[peak].buyback)
        + '，' + LAST + ' 为 ' + yiTxt(L.buyback) + '（' + yoyTxt(L.buyback, P.buyback)
        + '）。放在上一节的语境里看：' + LAST + ' 在经营现金流为负的同时仍回购 '
        + yiTxt(L.buyback) + '，这部分钱直接来自现金池。'
        + '<br><br>右图的少数股东权益从 FY2010 的 0 起步，FY2017–FY2018 明显跳升（'
        + yiTxt(AN['2017'].minorityInterest) + ' → ' + yiTxt(AN['2018'].minorityInterest)
        + '），' + LAST + ' 为 ' + yiTxt(L.minorityInterest)
        + '（上年 ' + yiTxt(P.minorityInterest) + '），主要对应爱奇艺等非全资子公司中不属于百度的部分。'
        + 'FY2016 出现 ' + yiTxt(AN['2016'].minorityInterest) + ' 的小额负数，是个别子公司累计亏损'
        + '超过少数股东出资所致，金额极小（不足 0.3 亿）。'
        );
})();
/* ==== VIE 余额与收入占比 ==== */
(function () {
    var A = VIE.asset_share || {};
    var va = A.vie_total_assets_rmb_million || {}, ca = A.consolidated_total_assets_rmb_million || {};
    var vl = A.vie_total_liabilities_rmb_million || {}, ip = A.vie_intragroup_payables_rmb_million || {};
    var rs = VIE.revenue_share_disclosed || {};
    var sd = (VIE.single_vie_revenue_detail || {}).baidu_netcom_pct_of_external_revenues || {};
    var d2 = LAST + '-12-31', d1 = PREV + '-12-31';
    renderKpis('vie-kpis', [
        { label: LAST + ' VIE 总资产', value: yiTxt(va[d2]),
          delta: yoyTxt(va[d2], va[d1]) },
        { label: 'VIE 资产 / 合并总资产', value: pct(va[d2] / ca[d2] * 100, 1),
          delta: '上年 ' + pct(va[d1] / ca[d1] * 100, 1) },
        { label: LAST + ' VIE 总负债', value: yiTxt(vl[d2]),
          delta: yoyTxt(vl[d2], vl[d1]) },
        { label: '其中：应付集团内其他主体', value: yiTxt(ip[d2]),
          delta: yoyTxt(ip[d2], ip[d1]) },
        { label: 'VIE 贡献的外部收入占比', value: pct(rs[LAST], 0),
          delta: PREV + ' 年 ' + pct(rs[PREV], 0) },
        { label: '其中：百度网讯单一主体', value: pct(sd[LAST], 0),
          delta: PREV + ' 年 ' + pct(sd[PREV], 0) }
    ]);
    renderCards('vie-cards', [
        { title: '为什么需要 VIE', body: VIE.why_needed || '—' },
        { title: '控制链条（' + ((VIE.control_chain || []).length) + ' 层）',
          body: (VIE.control_chain || []).join(' → ') + '<br><span style="color:' + MUTED + '">'
                + (VIE.chain_note || '') + '</span>' },
        { title: '控制机制', body: VIE.control_mechanics || '—' },
        { title: '合约类型（' + ((VIE.contract_types || []).length) + ' 类）',
          body: (VIE.contract_types || []).join('；') }
    ]);
    setHTML('vie-note',
        '<b>把 VIE 单独看一眼，是因为它决定了「合并报表上的资产在多大程度上由股权支撑」。</b>'
        + LAST + ' 年末 VIE 总资产 ' + yiTxt(va[d2]) + '，占合并总资产 ' + yiTxt(ca[d2]) + ' 的 '
        + pct(va[d2] / ca[d2] * 100, 1) + '；VIE 总负债 ' + yiTxt(vl[d2]) + '，其中 ' + yiTxt(ip[d2])
        + ' 是应付集团内其他主体的款项。<b>口径提示：</b>年报本身没有以百分比披露 VIE 资产占比，'
        + pct(va[d2] / ca[d2] * 100, 1) + ' 是本页自算；且 VIE 余额表<b>未与集团内部往来抵销</b>，'
        + '所以这个比例不等于「归属集团的净资产中有多少在 VIE 里」。'
        + '收入侧是定量披露的：VIE 贡献的外部收入占集团外部收入 ' + pct(rs[PREV], 0) + '（' + PREV
        + '）→ ' + pct(rs[LAST], 0) + '（' + LAST + '），单一主体里只有百度网讯与 Beijing Perusal 有占比披露，'
        + '爱奇艺一线的 VIE 未单列。年报另有定性表述：逾 96% 收入来自中国内地、逾 73% 总资产位于中国内地。'
        );
})();
/* ==== 逐年明细表（FY2008–FY2025 全年份，不抽样） ==== */
(function () {
    /* 表内单位是百万元，负值按表头说明加括号 */
    function mn(v) {
        if (v === null || v === undefined || isNaN(v)) return '—';
        /* 残余等差额算出来可能是 −0.4 这类零头，四舍五入后不要显示成「(0)」 */
        if (Math.abs(v) < 0.5) return '0';
        return v < 0 ? '(' + thou(-v) + ')' : thou(v);
    }
    var cols = ['年份', '总资产', '总负债', '流动负债', '非流动负债', '归母权益', '少数股东权益',
                '残余', '资产负债率', '现金及等价物', '短期投资', '有息负债', '净现金',
                '商誉', '长期资产减值', '固定资产净额', '使用权资产', '资本开支', '回购'];
    setHTML('tbl-head', cols.map(function (c) { return '<th>' + c + '</th>'; }).join(''));
    renderRows('tbl-body', BY.slice().reverse().map(function (y) {
        var r = AN[y];
        return {
            _th: true,
            _cls: y === LAST ? 'row-total' : '',
            cells: ['FY' + y, mn(r.assets), mn(r.liabilities), mn(r.liabilitiesCurrent),
                    mn(noncurrentOf(y)), mn(r.equity), mn(r.minorityInterest), mn(residOf(y)),
                    pct(levOf(y), 1), mn(r.cash), mn(r.shortTermInv), mn(debtOf(y)),
                    mn(netCashOf(y)), mn(r.goodwill), mn(r.assetImpairment), mn(r.ppe),
                    mn(r.opLeaseRou), mn(r.capex), mn(r.buyback)]
        };
    }));
})();
/* ==== 披露缺口：把本页取不到或不可比的地方一次说清 ==== */
renderList('gaps-list', [
    '<b>FY2006–FY2007 无完整资产负债表</b>：本页从 FY2008 起画，更早年份只有现金与股东权益等零散科目，不足以拼出结构图。',
    '<b>有息负债合计自 FY2015 起才连续披露</b>：FY2013–FY2014 只有高级票据分项，本页用票据余额（'
        + yiTxt(AN['2013'].seniorNotes) + ' / ' + yiTxt(AN['2014'].seniorNotes)
        + '）替代合计数，这两年的「有息负债」与「净现金」与其余年份不完全可比；FY2008–FY2011 未见有息负债，图上留空。',
    '<b>「残余」无法进一步拆分</b>：总资产减总负债、归母权益与少数股东权益后仍有差额（'
        + LAST + ' 为 ' + yiTxt(residOf(LAST)) + '，占总资产 ' + pct(residOf(LAST) / L.assets * 100, 1)
        + '；历年在 0 到 4.4% 之间），主要是可赎回非控股权益一类的中间层科目，本页数据源只给合计标签，故用灰斜线单列。',
    '<b>经营租赁使用权资产自 FY2019 起才有</b>：FY2019 起采用新租赁准则，FY2018 及以前柱子里没有这一块，不代表当年没有租赁。',
    '<b>少数股东权益自 FY2010 起才有余额</b>：FY2008–FY2009 未列示，右下图因此从 FY2010 起画。',
    '<b>商誉减值披露稀疏</b>：只有 FY2010–FY2013 与 FY2021–FY2024 明确列示（其中仅 FY2011 为 '
        + yiTxt(AN['2011'].goodwillImpairment) + '，其余为 0），其他年份图上留空是缺披露而非金额为 0。',
    '<b>「短期投资」是狭义口径</b>：只含年报归类为短期投资的部分，长期投资、权益法投资与长期理财都不在内，'
        + '所以本页净现金不等于「全部可动用金融资产减全部负债」。',
    '<b>FY2013 权益两套口径对不平</b>：归母权益加少数股东权益与「含少数股东权益合计」相差 '
        + yiTxt(628) + '，属年报重述期的列示差异，本页各图统一用归母口径，不做人工调平。',
    '<b>VIE 余额表未作集团内抵销</b>：VIE 总负债里含应付集团内其他主体 '
        + yiTxt(((VIE.asset_share || {}).vie_intragroup_payables_rmb_million || {})[LAST + '-12-31'])
        + '，故「VIE 资产占合并总资产 ' + pct((((VIE.asset_share || {}).vie_total_assets_rmb_million || {})[LAST + '-12-31'])
            / L.assets * 100, 1) + '」是自算的毛口径比例，不能读作「集团净资产中有这么大比例在 VIE 里」。',
    '<b>本页只回答「余额是多少」</b>：XBRL 余额不解释增减原因，商誉增加、减值计提、回购节奏背后的动因需回到年报正文，本页不作推测。'
]);

