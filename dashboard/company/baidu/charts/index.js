/* 百度详情页 · 业绩（index.html）
 *
 * 数据只来自 data.js 注入的 window.BAIDU：
 *   B.annual.annual   —— 利润表 / 现金流 / 比率，FY2007–FY2025（SEC XBRL，与历年 20-F 同源）
 *   B.segments.annual —— 营收 21 年序列（含 FY2005–2006）、每股收益、口径标记
 * 页面不手抄任何比率：同比增速、占营收比重、自由现金流都在这里现算。
 */
var AN = (B.annual && B.annual.annual) || {};
var SG = (B.segments && B.segments.annual) || {};

/* 有完整利润表的年份：FY2007 起 */
var AY = Object.keys(AN).filter(function (y) { return AN[y].revenue != null; }).sort();
/* 营收序列可回溯到 FY2005 */
var SY = Object.keys(SG).filter(function (y) { return SG[y].totalRevenue != null; }).sort();
var LAST = AY[AY.length - 1], PREV = AY[AY.length - 2];
var L = AN[LAST], P = AN[PREV];

function yi(mn) { return mn === null || mn === undefined ? null : +(mn / 100).toFixed(2); }
function yiTxt(mn) { return mn === null || mn === undefined ? '—' : fx(yi(mn), 2) + ' 亿'; }
/* 同比：金额用 %，负数或跨零改为「上年 xx」以免出现无意义的百分比 */
function yoyTxt(cur, prv) {
    if (cur === null || prv === null || cur === undefined || prv === undefined) return '';
    if (cur > 0 && prv > 0) return '同比 ' + fx((cur / prv - 1) * 100, 1) + '%';
    return '上年 ' + fx(yi(prv), 2) + ' 亿';
}
function pctTxt(cur, prv) {
    if (cur === null || prv === null) return '';
    return '同比 ' + (cur - prv >= 0 ? '+' : '') + fx(cur - prv, 2) + 'pct';
}

/* ==== FY2025 概览 ==== */
setText('kpi-sub', '口径：' + LAST + ' 财年（截至 ' + LAST + '-12-31）· 与 ' + PREV
    + ' 财年比较 · 金额换算为人民币亿元 · 归母口径（不含少数股东权益）');
renderKpis('main-kpis', [
    { label: LAST + ' 营业收入', value: yiTxt(L.revenue), delta: yoyTxt(L.revenue, P.revenue) },
    { label: LAST + ' 经营利润', value: yiTxt(L.operatingIncome), delta: yoyTxt(L.operatingIncome, P.operatingIncome) },
    { label: LAST + ' 归母净利润', value: yiTxt(L.netIncome), delta: yoyTxt(L.netIncome, P.netIncome) },
    { label: LAST + ' 毛利率', value: pct(L.grossMargin), delta: pctTxt(L.grossMargin, P.grossMargin) },
    { label: LAST + ' 研发费用率', value: pct(L.rdRatio), delta: pctTxt(L.rdRatio, P.rdRatio) },
    { label: LAST + ' 经营现金流', value: yiTxt(L.opCashFlow), delta: yoyTxt(L.opCashFlow, P.opCashFlow) }
]);
setHTML('kpi-note',
    '<b>' + LAST + ' 是一个「营收小幅下滑、利润表转亏、但净利润仍为正」的组合，三件事需要分开看：</b>'
    + '① 营业收入 ' + yiTxt(L.revenue) + '（' + yoyTxt(L.revenue, P.revenue) + '），连续第二年负增长；'
    + '② 经营利润 ' + yiTxt(L.operatingIncome) + '，为可比区间（FY2007 起）<b>首次经营亏损</b>，'
    + '其中长期资产减值 ' + yiTxt(L.assetImpairment) + '（占营收 ' + pct(L.assetImpairment / L.revenue * 100) + '）是单一最大项，'
    + '剔除该项后经营利润仍为正；③ 归母净利润 ' + yiTxt(L.netIncome)
    + ' 靠经营以外的科目撑住（利息收入 ' + yiTxt(L.interestIncome) + '、权益法投资收益 ' + yiTxt(L.equityMethodPnl) + '），'
    + '因此本年净利率 ' + pct(L.netMargin) + ' <b>高于</b>经营利润率 ' + pct(L.opMargin) + '——这种倒挂在 FY2015、FY2018、FY2020 也出现过，成因各不相同。'
    + '另需注意：同年<b>经营活动现金流也转负</b>（' + yiTxt(L.opCashFlow) + '，上年 ' + yiTxt(P.opCashFlow)
    + '），是 FY2007 以来首次，说明这一年的压力不只体现在减值这类非现金项上。'
    );

/* ==== 营收走势（FY2005–FY2025） ==== */
mount('chart-revenue', function () {
    var rev = SY.map(function (y) { return yi(SG[y].totalRevenue); });
    var yoy = SY.map(function (y, i) {
        if (i === 0) return null;
        var p = SG[SY[i - 1]].totalRevenue;
        return +((SG[y].totalRevenue / p - 1) * 100).toFixed(1);
    });
    var o = axisBase({ x: SY, left: 84, right: 86 });
    o.yAxis = [valueAxis('亿元'), valueAxis('同比 %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '总营收（亿元）', type: 'bar', barWidth: '56%', itemStyle: { color: NAVY }, data: rev,
          /* FY2017 及以前为 ASC605 含增值税口径，用灰底标出；FY2018 起改 ASC606 净额法 */
          markArea: { silent: true, itemStyle: { color: 'rgba(0,0,0,0.05)' },
              label: { formatter: 'ASC605 含增值税口径\n（FY2018 起改净额法）', fontSize: 15,
                       color: MUTED, position: 'insideBottomLeft' },
              data: [[{ xAxis: SY[0] }, { xAxis: '2017' }]] } },
        { name: '同比增速（%）', type: 'line', yAxisIndex: 1, connectNulls: true, symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD }, data: yoy }
    ];
    return o;
});
setHTML('revenue-note',
    '营收从 FY2005 的 ' + yiTxt(SG[SY[0]].totalRevenue) + ' 增至 FY' + LAST + ' 的 ' + yiTxt(L.revenue)
    + '，但增长早已分成两段：<b>FY2005–FY2014 每年 35%–83% 的高增长</b>（十年 CAGR 约 '
    + fx((Math.pow(AN['2014'].revenue / SG['2005'].totalRevenue, 1 / 9) - 1) * 100, 1) + '%），'
    + '<b>FY2015 起增速台阶式下移</b>，FY2016 骤降至 6.3%，此后长期在 −3% 到 +20% 之间震荡，'
    + 'FY2020、FY2022、FY2024、FY2025 四年为负增长。'
    + '<b>口径提示：</b>灰底区间（FY2017 及以前）为 ASC605 含增值税口径，FY2018 起改用 ASC606 按净额法列示，'
    + '故 FY2017→FY2018 的 20.6% 增速里含一部分口径影响；FY2005–FY2006 早于 XBRL 期，取自早年 20-F。'
    );

/* ==== 经营利润 / 归母净利润 + 两条利润率 ==== */
mount('chart-profit', function () {
    var o = axisBase({ x: AY, left: 84, right: 86 });
    o.yAxis = [valueAxis('亿元'), valueAxis('利润率 %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '经营利润（亿元）', type: 'bar', barWidth: '32%', itemStyle: { color: NAVY },
          data: AY.map(function (y) { return yi(AN[y].operatingIncome); }) },
        { name: '归母净利润（亿元）', type: 'bar', barWidth: '32%', itemStyle: { color: '#2980b9' },
          data: AY.map(function (y) { return yi(AN[y].netIncome); }) },
        { name: '经营利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7, lineStyle: { width: 2.5 },
          itemStyle: { color: GOLD }, data: AY.map(function (y) { return AN[y].opMargin; }) },
        { name: '净利率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 2.5, type: 'dashed' }, itemStyle: { color: '#c0392b' },
          data: AY.map(function (y) { return AN[y].netMargin; }) }
    ];
    return o;
});

/* ==== 四条比率 ==== */
mount('chart-margin', function () {
    var o = axisBase({ x: AY, left: 78, right: 40 });
    o.yAxis = [valueAxis('%', { formatter: '{value}%' })];
    var defs = [
        ['毛利率', 'grossMargin', '#16a085'],
        ['经营利润率', 'opMargin', NAVY],
        ['净利率', 'netMargin', '#c0392b'],
        ['研发费用率', 'rdRatio', GOLD]
    ];
    o.series = defs.map(function (d) {
        return { name: d[0], type: 'line', symbolSize: 7, lineStyle: { width: 2.5 },
                 itemStyle: { color: d[2] },
                 data: AY.map(function (y) { return AN[y][d[1]]; }) };
    });
    return o;
});
setHTML('profit-note',
    '<b>利润率的长期方向是下行，而且四条线不是同步的。</b>'
    + '毛利率从 FY2011 的 73.13% 降至 FY' + LAST + ' 的 ' + pct(L.grossMargin)
    + '，主要是收入结构从纯广告转向带宽/服务器/内容成本更重的业务（云、爱奇艺内容）；'
    + '研发费用率反向抬升，从 FY2007 的 8.07% 升到 FY2021 的 20.03% 峰值，FY' + LAST + ' 为 ' + pct(L.rdRatio)
    + '——毛利率下行与研发上行两头挤压，经营利润率由 FY2010 的 50.02% 一路降到本年 ' + pct(L.opMargin) + '。'
    + '<b>净利率与经营利润率多次背离</b>，且方向可以相反：FY2015 净利率 50.71% 远高于经营利润率 17.58%（处置类收益推高），'
    + 'FY2019 净利率 1.92% 低于经营利润率 5.87%（减值与投资损失拖累），FY' + LAST
    + ' 又回到净利率高于经营利润率。读这两条线时必须记住：<b>经营利润率反映主业，净利率含大量投资与一次性损益</b>。'
    );

/* ==== 成本结构占营收比重 ==== */
mount('chart-cost', function () {
    function share(y, key) { return +(AN[y][key] / AN[y].revenue * 100).toFixed(2); }
    /* 三项费用 + 经营利润率 ≈ 100%，差额为减值等其他经营损益；FY2025 的 12.54pct 即长期资产减值 */
    var other = AY.map(function (y) {
        return +(100 - share(y, 'costOfRevenue') - share(y, 'rd') - share(y, 'selling') - AN[y].opMargin).toFixed(2);
    });
    var o = axisBase({ x: AY, left: 78, right: 40 });
    o.yAxis = [valueAxis('占营收 %', { formatter: '{value}%' })];
    o.series = [
        { name: '营业成本', type: 'bar', stack: 'c', itemStyle: { color: NAVY },
          data: AY.map(function (y) { return share(y, 'costOfRevenue'); }) },
        { name: '研发费用', type: 'bar', stack: 'c', itemStyle: { color: GOLD },
          data: AY.map(function (y) { return share(y, 'rd'); }) },
        { name: '销售、一般及行政费用', type: 'bar', stack: 'c', itemStyle: { color: '#2980b9' },
          data: AY.map(function (y) { return share(y, 'selling'); }) },
        { name: '减值及其他经营损益', type: 'bar', stack: 'c', itemStyle: { color: '#c0392b' }, data: other },
        { name: '经营利润率', type: 'line', symbolSize: 7, lineStyle: { width: 3 },
          itemStyle: { color: '#16a085' }, data: AY.map(function (y) { return AN[y].opMargin; }) }
    ];
    return o;
});
setHTML('cost-note',
    '<b>营业成本是压缩毛利率的主因：</b>占营收比重从 FY2011 的 26.9% 升到 FY' + LAST + ' 的'
    + pct(L.costOfRevenue / L.revenue * 100) + '，十四年间几乎翻倍；销售、一般及行政费用则在 11.2%（FY2012）到 25.7%（FY2015）之间大幅摆动，'
    + '与各年营销投放强度相关；研发费用率单向上行。'
    + '<b>「减值及其他经营损益」这一层在多数年份为 0</b>——因为三项费用加经营利润率恰好等于 100%；'
    + '只有 FY' + LAST + ' 凸出 ' + fx(100 - L.costOfRevenue / L.revenue * 100 - L.rd / L.revenue * 100 - L.selling / L.revenue * 100 - L.opMargin, 2)
    + 'pct，对应当年 ' + yiTxt(L.assetImpairment) + ' 长期资产减值，这也是经营利润率跌破零的直接原因。'
    );

/* ==== 经营现金流 / 资本开支 / 自由现金流 ==== */
mount('chart-cash', function () {
    var fcf = AY.map(function (y) { return yi(AN[y].opCashFlow - AN[y].capex); });
    var o = axisBase({ x: AY, left: 84, right: 40 });
    o.yAxis = [valueAxis('亿元')];
    o.series = [
        { name: '经营活动现金流净额', type: 'bar', barWidth: '32%', itemStyle: { color: NAVY },
          data: AY.map(function (y) { return yi(AN[y].opCashFlow); }) },
        { name: '资本开支（画为负）', type: 'bar', barWidth: '32%', itemStyle: { color: '#8e44ad' },
          data: AY.map(function (y) { return yi(-AN[y].capex); }) },
        { name: '自由现金流（经营现金流 − 资本开支）', type: 'line', symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD }, data: fcf }
    ];
    return o;
});
setHTML('cash-note',
    '经营活动现金流在 FY2007–FY2024 每年都为正，且长期高于同年净利润（折旧摊销与股权激励等非现金项较大）；'
    + 'FY2023 达到峰值 ' + yiTxt(AN['2023'].opCashFlow) + '。<b>FY' + LAST + ' 转为 ' + yiTxt(L.opCashFlow)
    + '，是可比区间内首次为负</b>，同年资本开支反而升到 ' + yiTxt(L.capex) + '（近三年最高），'
    + '两头相加使自由现金流降至 ' + yiTxt(L.opCashFlow - L.capex) + '。'
    + '资本开支自 FY2021 起长期在 80–120 亿量级，与 AI 算力投入的方向一致，但本页数据不含资本开支的用途拆分。'
    );

/* ==== 每股收益（每股 ADS）与 ROE ==== */
var EY = Object.keys(SG).filter(function (y) { return SG[y].epsBasicPerAds != null; }).sort();
var EL = SG[EY[EY.length - 1]], EP = SG[EY[EY.length - 2]];
renderKpis('pershare-kpis', [
    { label: LAST + ' 基本每股收益（每 ADS）', value: fx(EL.epsBasicPerAds, 2) + ' 元',
      delta: '上年 ' + fx(EP.epsBasicPerAds, 2) + ' 元' },
    { label: LAST + ' 摊薄每股收益（每 ADS）', value: fx(EL.epsDilutedPerAds, 2) + ' 元',
      delta: '上年 ' + fx(EP.epsDilutedPerAds, 2) + ' 元' },
    { label: LAST + ' 净资产收益率 ROE', value: pct(L.roe), delta: pctTxt(L.roe, P.roe) }
]);
mount('chart-eps', function () {
    /* FY2005–FY2007 的每股数据早于现行 ADS 比率，标为不可比区间 */
    var badTail = EY.filter(function (y) { return SG[y].epsPerAdsComparable === false; }).pop();
    var o = axisBase({ x: EY, left: 78, right: 40 });
    o.yAxis = [valueAxis('元 / ADS')];
    o.series = [
        { name: '基本每股收益（元/ADS）', type: 'bar', barWidth: '46%', itemStyle: { color: NAVY },
          data: EY.map(function (y) { return SG[y].epsBasicPerAds; }),
          markArea: badTail ? { silent: true, itemStyle: { color: 'rgba(0,0,0,0.05)' },
              label: { formatter: 'ADS 比率折算前\n与后续年份不可比', fontSize: 15, color: MUTED, position: 'insideTop' },
              data: [[{ xAxis: EY[0] }, { xAxis: badTail }]] } : undefined },
        { name: '摊薄每股收益（元/ADS）', type: 'line', symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: EY.map(function (y) { return SG[y].epsDilutedPerAds; }) }
    ];
    return o;
});
mount('chart-roe', function () {
    var o = axisBase({ x: AY, left: 92, right: 86 });
    o.yAxis = [valueAxis('股权激励（亿元）'), valueAxis('ROE %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '股权激励费用（亿元）', type: 'bar', barWidth: '48%', itemStyle: { color: '#2980b9' },
          data: AY.map(function (y) { return yi(AN[y].sbc); }) },
        { name: '净资产收益率 ROE（%）', type: 'line', yAxisIndex: 1, symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD },
          data: AY.map(function (y) { return AN[y].roe; }) }
    ];
    return o;
});
setHTML('pershare-note',
    '<b>ROE 的落差比利润率更大：</b>FY2011 峰值 56.03%，FY' + LAST + ' 仅 ' + pct(L.roe)
    + '。分子端是净利润下滑，分母端是权益长期累积（归母权益 FY' + LAST + ' 为 ' + yiTxt(L.equity)
    + '），两头共同压低 ROE——分母这一侧在「资产与现金」页可以对照看到。'
    + '<b>每股收益的年际跳动主要来自一次性损益</b>：FY2015 的 95.46 元/ADS、FY2019 的 5.68 元、'
    + 'FY' + LAST + ' 的 ' + fx(EL.epsBasicPerAds, 2) + ' 元，都不宜与相邻年份直接比较；'
    + '基本与摊薄的差距本年扩大到 ' + fx(EL.epsBasicPerAds - EL.epsDilutedPerAds, 2) + ' 元/ADS（上年仅 '
    + fx(EP.epsBasicPerAds - EP.epsDilutedPerAds, 2) + ' 元），与可转债等潜在摊薄工具有关。'
    + '股权激励费用自 FY2007 的 0.40 亿升至 FY2021 峰值 70.56 亿，FY' + LAST + ' 回落至 ' + yiTxt(L.sbc)
    + '，是净利润与经营现金流之间差额的主要非现金项之一。'
    );

/* ==== 近六年主要指标表 ==== */
var TY = AY.slice(-6);
setHTML('tbl-head', '<th>项目</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
/* 负数用括号表示，与银行页的表格惯例一致 */
function num(v) { return v === null || v === undefined ? '—' : (v < 0 ? '(' + thou(-v) + ')' : thou(v)); }
function moneyRow(label, key, cls) {
    return { _cls: cls, cells: [label].concat(TY.map(function (y) {
        var v = AN[y][key];
        return v === null || v === undefined ? '—'
            : '<span' + (v < 0 ? ' class="neg"' : '') + '>' + num(v) + '</span>';
    })) };
}
function ratioRow(label, key, cls) {
    return { _cls: cls, cells: [label].concat(TY.map(function (y) { return pct(AN[y][key]); })) };
}
renderRows('tbl-body', [
    moneyRow('营业收入', 'revenue', 'row-total'),
    moneyRow('营业成本', 'costOfRevenue', 'row-sub'),
    moneyRow('研发费用', 'rd', 'row-sub'),
    moneyRow('销售、一般及行政费用', 'selling', 'row-sub'),
    moneyRow('长期资产减值', 'assetImpairment', 'row-sub'),
    moneyRow('经营利润', 'operatingIncome', 'row-total'),
    ratioRow('经营利润率', 'opMargin'),
    moneyRow('归母净利润', 'netIncome', 'row-total'),
    ratioRow('净利率', 'netMargin'),
    ratioRow('毛利率', 'grossMargin'),
    ratioRow('研发费用率', 'rdRatio'),
    ratioRow('净资产收益率 ROE', 'roe'),
    moneyRow('股权激励费用', 'sbc'),
    moneyRow('经营活动现金流净额', 'opCashFlow', 'row-total'),
    moneyRow('资本开支', 'capex'),
    { _cls: 'row-total', cells: ['自由现金流'].concat(TY.map(function (y) {
        var v = AN[y].opCashFlow - AN[y].capex;
        return '<span' + (v < 0 ? ' class="neg"' : '') + '>' + num(v) + '</span>';
    })) },
    { cells: ['基本每股收益（元/ADS）'].concat(TY.map(function (y) {
        return SG[y] ? fx(SG[y].epsBasicPerAds, 2) : '—';
    })) },
    { cells: ['摊薄每股收益（元/ADS）'].concat(TY.map(function (y) {
        return SG[y] ? fx(SG[y].epsDilutedPerAds, 2) : '—';
    })) }
]);

/* ==== 口径提示与披露缺口 ==== */
renderList('gaps-list', [
    '<b>FY2005–FY2006 不在利润表序列里。</b>这两年早于 SEC XBRL 覆盖期，只有营收、每股收益与员工数（取自早年 20-F），'
    + '故营收图从 FY2005 起、利润与现金流各图从 FY2007 起。',
    '<b>FY2018 起营收改按 ASC606 净额法列示</b>（此前 ASC605 含增值税），跨越这一年的增速含口径影响，公司未按新旧准则并行披露可比数。',
    '<b>净利润为归母口径</b>（不含少数股东权益）。爱奇艺等非全资子公司的少数股东部分只体现在「含少数股东权益的合并净利润」里，'
    + '本页图表统一用归母数，与 ROE、每股收益的分子一致。',
    '<b>FY2005–FY2007 的每股收益不可与后续年份直连</b>：ADS 与普通股的折算比率此后变更过，图中已用灰底标出该区间。',
    '<b>本页全部为 US GAAP 口径</b>，未收录公司同时披露的非 GAAP（调整后）利润与调整后 EBITDA，两套数字不可混用。',
    '<b>减值只有合计数。</b>FY' + LAST + ' 的 ' + yiTxt(L.assetImpairment)
    + ' 长期资产减值，本页数据未含按业务／资产类别的拆分，因此无法判断减值集中在哪一块业务。',
    '<b>现金流量表只收录了经营活动现金流净额与资本开支</b>，投资与筹资活动的分项（并购、处置、发债、回购的现金流）不在本页；'
    + '回购金额见「股权结构」页，债务与现金余额见「资产与现金」页。',
    '<b>分部数据（百度核心 vs 爱奇艺）自 FY2017 才披露</b>，故本页的营收与利润均为合并数；分部拆分见「分部与运营」页。'
]);
