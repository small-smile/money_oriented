<template>
  <div class="wrap" ref="wrapEl">

    <div class="page-head">
      <h1>百度集团（09888 / 89888 / BIDU）· 资产与现金</h1>
      <div class="meta">
        美国会计准则（US GAAP）· 人民币百万元／亿元（比率为 %）· 资产负债表科目覆盖 FY2008–FY2025<br>
        有息负债合计口径自 FY2015 起披露 · 使用权资产自 FY2019 起 · VIE 余额表为 FY2024–FY2025
      </div>
      <div class="tags"><span>资产负债结构</span><span>净现金</span><span>商誉与减值</span><span>固定资产</span><span>回购</span><span>VIE</span></div>
    </div>

    <!-- ══════════ FY2025 概览 ══════════ -->
    <section id="sec-kpi">
      <h2>FY2025 年末概览</h2>
      <p class="sub" id="kpi-sub"></p>
      <div class="kpis" id="bs-kpis"></div>
      <div class="note-generic" id="kpi-note"></div>
    </section>

    <!-- ══════════ 资产负债结构 ══════════ -->
    <section id="sec-structure">
      <h2>总资产的两侧：负债、少数股东权益与归母权益</h2>
      <p class="sub">堆叠柱：总负债 / 少数股东权益 / 归母股东权益（亿元，三者相加即总资产）· 线：资产负债率（%，现算）</p>
      <div id="chart-assets" class="chart" style="height:420px"></div>
      <h3 class="chart-title" style="margin-top:18px">负债的期限结构：流动负债与非流动负债（亿元，柱）与流动负债占总负债比重（%，线）</h3>
      <div id="chart-liab" class="chart" style="height:380px"></div>
      <div class="note-generic" id="structure-note"></div>
    </section>

    <!-- ══════════ 净现金 ══════════ -->
    <section id="sec-netcash">
      <h2>现金、短期投资与有息负债</h2>
      <p class="sub">堆叠柱：现金及等价物 / 短期投资（亿元）· 红柱：有息负债（画为负值）· 线：净现金 = 现金 + 短期投资 − 有息负债</p>
      <div id="chart-netcash" class="chart" style="height:440px"></div>
      <div class="note-generic" id="netcash-note"></div>
    </section>

    <!-- ══════════ 商誉与减值 ══════════ -->
    <section id="sec-impair">
      <h2>商誉余额与历年减值</h2>
      <p class="sub">柱：年末商誉余额（亿元）· 红柱：当年长期资产减值 · 橙柱：当年商誉减值（两者在年报中是不同科目）</p>
      <div id="chart-goodwill" class="chart" style="height:420px"></div>
      <div class="note-generic" id="impair-note"></div>
    </section>

    <!-- ══════════ 固定资产与租赁 ══════════ -->
    <section id="sec-ppe">
      <h2>固定资产、使用权资产与资本开支</h2>
      <p class="sub">堆叠柱：固定资产净额 / 经营租赁使用权资产（亿元）· 线：当年资本开支（亿元）</p>
      <div id="chart-ppe" class="chart" style="height:420px"></div>
      <div class="note-generic" id="ppe-note"></div>
    </section>
    <!-- ══════════ 回购与少数股东权益 ══════════ -->
    <section id="sec-return">
      <h2>股份回购与少数股东权益</h2>
      <p class="sub">左：历年回购金额（亿元，未披露或未回购的年份为 0）· 右：年末少数股东权益（亿元，主要来自爱奇艺等非全资子公司）</p>
      <div class="two-col">
        <div>
          <div id="chart-buyback" class="chart" style="height:400px"></div>
        </div>
        <div>
          <div id="chart-nci" class="chart" style="height:400px"></div>
        </div>
      </div>
      <div class="note-generic" id="return-note"></div>
    </section>

    <!-- ══════════ VIE 口径 ══════════ -->
    <section id="sec-vie">
      <h2>合并报表里的 VIE：占多大一块</h2>
      <p class="sub">数据取自 FY2025 20-F 的 VIE 余额表与引言段；资产占比为自算值，年报未以百分比披露</p>
      <div class="kpis" id="vie-kpis"></div>
      <div class="cards" id="vie-cards"></div>
      <div class="note-generic" id="vie-note"></div>
    </section>

    <!-- ══════════ 逐年明细 ══════════ -->
    <section id="sec-table">
      <h2>逐年资产负债表主要科目（FY2008–FY2025）</h2>
      <p class="sub">单位：人民币百万元（比率为 %）· 括号内为负值 · 「—」为该年未披露 · 数据取自历年 20-F · 表格可左右滑动</p>
      <div style="overflow-x:auto">
        <table>
          <thead><tr id="tbl-head"></tr></thead>
          <tbody id="tbl-body"></tbody>
        </table>
      </div>
    </section>

    <!-- ══════════ 口径与缺口 ══════════ -->
    <section id="sec-gaps">
      <h2>口径提示与披露缺口</h2>
      <p class="sub">本页只用 20-F／SEC XBRL 一手数据，以下为读图时必须知道的口径边界</p>
      <ul class="gap-list" id="gaps-list"></ul>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { B, setScope, CHARTS, mount, axisBase, valueAxis, setText, setHTML,
         renderKpis, renderCards, renderRows, renderList,
         NAVY, GOLD, MUTED, RESIDUAL_PATTERN, shade, fx, pct, thou } from './charts.js'

// 逐字搬自 dashboard/company/baidu/charts/balance-sheet.js：option 与渲染逻辑原样保留，
// 仅把渲染放进 onMounted、容器查找经 setScope 限定在本组件 ref 内。图与数据一律不变。
const wrapEl = ref(null)
let charts = []
let onResize = null

onMounted(() => {
  setScope(wrapEl.value)
  CHARTS.length = 0

  /* ============ 逐字搬运开始（charts/balance-sheet.js） ============ */
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
  /* ============ 逐字搬运结束 ============ */

  charts = CHARTS.slice()
  onResize = function () { charts.forEach(function (c) { c.ins.resize(); c.ins.setOption(c.build(c.ins), true); }); }
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  if (onResize) window.removeEventListener('resize', onResize)
  charts.forEach(function (c) { try { c.ins.dispose() } catch (e) {} })
  charts = []
  setScope(null)
})
</script>

<!-- 静态节点（容器 / 标题 / section / 图容器 / 两列 / 卡片容器 / 表格骨架）在模板里带 data-v，用 scoped 收敛，
     取自 dashboard/company/page.css。base.css 已全局引入，不重复其规则（.chart-title 等来自 base.css）。 -->
<style scoped>
.wrap { max-width: var(--content-w, 1200px); margin: 0 auto; padding: 24px 24px 60px; }
.page-head { text-align: center; margin-bottom: 8px; }
.page-head h1 { font-size: 29px; color: #1f2937; margin-bottom: 6px; }
.page-head .meta { color: #6b7280; font-size: 18px; line-height: 1.7; }
.page-head .tags { margin-top: 8px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.page-head .tags span { background: #dde8f3; color: #10243e; border-radius: 12px; padding: 3px 12px; font-size: 18px; font-weight: 500; }
section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 20px 22px; margin-top: 22px; scroll-margin-top: 116px; }
section > h2 { font-size: 22px; color: #1f2937; margin-bottom: 4px; border-left: 4px solid #10243e; padding-left: 10px; }
section > .sub { color: #6b7280; font-size: 18px; margin: 0 0 14px 14px; }
.chart { width: 100%; height: 428px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; margin-bottom: 16px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px,420px)); gap: 14px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
@media (max-width: 820px) { .two-col { grid-template-columns: 1fr; } }
table { width: 100%; border-collapse: collapse; font-size: 18px; }
</style>

<!-- 动态节点（KPI / 卡片 / 表格行 / 说明 / 缺口）由脚本 innerHTML 注入，不带 data-v，样式必须非 scoped；
     通用元素选择器统一以 .wrap 前缀限定在本公司页内，避免泄漏到其它页面（等价于原页各自独立文档的作用域）。 -->
<style>
/* —— balance-sheet.html <head> 内联样式，逐字搬入 —— */
.note-generic { margin: 10px 0 0; padding: 12px 16px; background: #f6f7f9; border-left: 4px solid #b7b1c4; border-radius: 6px; font-size: 18px; color: #555; line-height: 1.75; }
.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }
.gap-list b { color: #10243e; }
/* —— company/page.css 中作用于动态节点的规则，加 .wrap 前缀限定 —— */
.wrap .kpi { background: #f3f6fa; border: 1px solid #dde8f3; border-radius: 8px; padding: 12px 14px; }
.wrap .kpi .label { font-size: 18px; color: #7f8c8d; }
.wrap .kpi .value { font-size: 25px; font-weight: 700; color: #10243e; margin-top: 4px; }
.wrap .kpi .delta { font-size: 18px; margin-top: 2px; }
.wrap th, .wrap td { padding: 8px 10px; text-align: right; border-bottom: 1px solid #eee; }
.wrap th:first-child, .wrap td:first-child { text-align: left; }
.wrap thead th { background: #eef2f7; color: #10243e; font-weight: 600; border-bottom: 2px solid #c9a24a; }
.wrap tbody tr:hover { background: #f3f6fa; }
.wrap .row-total td { font-weight: 700; background: #f6f8fb; border-top: 2px solid #c9a24a; }
.wrap .row-sub td:first-child { padding-left: 26px; color: #555; font-weight: 400; }
.wrap .neg { color: #c0392b; }
.wrap .card2 { background: #f3f6fa; border: 1px solid #dde8f3; border-radius: 8px; padding: 14px 16px; }
.wrap .card2 h3 { font-size: 18px; color: #10243e; margin-bottom: 6px; }
.wrap .card2 p { font-size: 18px; color: #444; line-height: 1.65; }
.wrap .card2 ul { margin: 4px 0 0 18px; font-size: 18px; color: #444; line-height: 1.7; }
</style>
