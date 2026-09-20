<template>
  <div class="wrap" ref="wrapEl">

    <div class="page-head">
      <h1>百度集团（09888 / 89888 / BIDU）· 分部与运营</h1>
      <div class="meta">
        美国会计准则（US GAAP）· 人民币百万元／亿元（比率为 %）· 分部为公司披露的可报告分部<br>
        营收构成覆盖 FY2005–FY2025 · 分部（百度核心 / 爱奇艺）覆盖 FY2017–FY2025 · 分部内拆分覆盖 FY2018–FY2024
      </div>
      <div class="tags"><span>营销 / 非营销</span><span>百度核心</span><span>爱奇艺</span><span>智能云</span><span>员工</span><span>萝卜快跑</span></div>
    </div>

    <!-- ══════════ FY2025 分部概览 ══════════ -->
    <section id="sec-kpi">
      <h2>FY2025 分部概览</h2>
      <p class="sub" id="kpi-sub"></p>
      <div class="kpis" id="seg-kpis"></div>
      <div class="note-generic" id="kpi-note"></div>
    </section>

    <!-- ══════════ 营销 / 非营销 ══════════ -->
    <section id="sec-mix">
      <h2>营销收入与非营销收入（FY2005–FY2025）</h2>
      <p class="sub">柱：在线营销收入 / 非在线营销收入（亿元，堆叠）· 线：非营销收入占总营收比重（%）</p>
      <div id="chart-mix" class="chart" style="height:420px"></div>
      <div class="note-generic" id="mix-note"></div>
    </section>

    <!-- ══════════ 分部营收与利润 ══════════ -->
    <section id="sec-seg">
      <h2>百度核心与爱奇艺（FY2017–FY2025）</h2>
      <p class="sub">柱：分部营收（亿元，堆叠，含分部间抵销）· 线：百度核心占比（%）</p>
      <div id="chart-segrev" class="chart" style="height:420px"></div>
      <h3 class="chart-title" style="margin-top:18px">分部经营利润与百度核心经营利润率</h3>
      <div id="chart-segop" class="chart" style="height:400px"></div>
      <div class="note-generic" id="seg-note"></div>
    </section>

    <!-- ══════════ 分部内部拆分 ══════════ -->
    <section id="sec-inner">
      <h2>分部内部拆分（FY2018–FY2024）</h2>
      <p class="sub">左：百度核心内部构成（亿元）· 右：爱奇艺内部构成（亿元）· 两图口径均为公司披露的收入类别</p>
      <div class="two-col">
        <div>
          <h3 class="chart-title">百度核心：营销 vs 智能云 vs 其他</h3>
          <div id="chart-core" class="chart" style="height:400px"></div>
        </div>
        <div>
          <h3 class="chart-title">爱奇艺：会员 vs 广告 vs 内容分发 vs 其他</h3>
          <div id="chart-iqiyi" class="chart" style="height:400px"></div>
        </div>
      </div>
      <div class="note-generic" id="inner-note"></div>
    </section>

    <!-- ══════════ 员工与人均 ══════════ -->
    <section id="sec-staff">
      <h2>员工人数与人均营收（FY2005–FY2025）</h2>
      <p class="sub">柱：年末员工人数（人）· 线：人均营收（万元／人，由当年总营收 ÷ 年末人数现算）</p>
      <div id="chart-staff" class="chart" style="height:420px"></div>
      <div class="note-generic" id="staff-note"></div>
    </section>
    <!-- ══════════ 运营指标 ══════════ -->
    <section id="sec-ops">
      <h2>运营指标：百度 App 月活与萝卜快跑</h2>
      <p class="sub">柱：百度 App 12 月月活（百万）· 萝卜快跑为累计订单（百万单）与开放城市数，取自年报披露时点</p>
      <div id="chart-mau" class="chart" style="height:380px"></div>
      <div class="kpis" id="ops-kpis"></div>
      <div class="note-generic" id="ops-note"></div>
    </section>

    <!-- ══════════ 分部数据表 ══════════ -->
    <section id="sec-table">
      <h2>分部数据（FY2020–FY2025）</h2>
      <p class="sub">单位：人民币百万元（比率为 %）· 括号内为负值 · 数据取自历年 20-F 分部附注</p>
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
         renderKpis, renderRows, renderList, NAVY, GOLD, MUTED, fx, pct, thou } from './charts.js'

// 逐字搬自 dashboard/company/baidu/charts/segment.js：option 与渲染逻辑原样保留，
// 仅把渲染放进 onMounted、容器查找经 setScope 限定在本组件 ref 内。图与数据一律不变。
const wrapEl = ref(null)
let charts = []
let onResize = null

onMounted(() => {
  setScope(wrapEl.value)
  CHARTS.length = 0

  /* ============ 逐字搬运开始（charts/segment.js） ============ */
var SG = (B.segments && B.segments.annual) || {};
var AN = (B.annual && B.annual.annual) || {};
var SY = Object.keys(SG).filter(function (y) { return SG[y].totalRevenue != null; }).sort();
/* 分部（百度核心 / 爱奇艺）自 FY2017 才披露 */
var GY = Object.keys(SG).filter(function (y) { return SG[y].coreRevenue != null; }).sort();
/* 分部内部拆分只有 FY2018–FY2024 */
var IY = Object.keys(SG).filter(function (y) { return SG[y].coreOnlineMarketing != null; }).sort();
var LAST = SY[SY.length - 1], PREV = SY[SY.length - 2];
var L = SG[LAST], P = SG[PREV];

function yi(mn) { return mn === null || mn === undefined ? null : +(mn / 100).toFixed(2); }
function yiTxt(mn) { return mn === null || mn === undefined ? '—' : fx(yi(mn), 2) + ' 亿'; }
function yoyTxt(cur, prv) {
    if (cur === null || prv === null || cur === undefined || prv === undefined) return '';
    if (cur > 0 && prv > 0) return '同比 ' + fx((cur / prv - 1) * 100, 1) + '%';
    return '上年 ' + fx(yi(prv), 2) + ' 亿';
}
function shareTxt(part, total) { return pct(part / total * 100); }

/* ==== FY2025 分部概览 ==== */
setText('kpi-sub', '口径：' + LAST + ' 财年 · 分部为公司披露的两个可报告分部（百度核心 / 爱奇艺）'
    + '，两者相加还需减去分部间抵销 ' + yiTxt(-L.interSegmentEliminations) + ' 才等于合并总营收');
renderKpis('seg-kpis', [
    { label: LAST + ' 百度核心营收', value: yiTxt(L.coreRevenue), delta: yoyTxt(L.coreRevenue, P.coreRevenue) },
    { label: LAST + ' 爱奇艺营收', value: yiTxt(L.iqiyiRevenue), delta: yoyTxt(L.iqiyiRevenue, P.iqiyiRevenue) },
    { label: LAST + ' 核心占总营收', value: shareTxt(L.coreRevenue, L.totalRevenue),
      delta: '上年 ' + shareTxt(P.coreRevenue, P.totalRevenue) },
    { label: LAST + ' 非营销收入', value: yiTxt(L.nonOnlineMarketing), delta: yoyTxt(L.nonOnlineMarketing, P.nonOnlineMarketing) },
    { label: LAST + ' 非营销占比', value: shareTxt(L.nonOnlineMarketing, L.totalRevenue),
      delta: '上年 ' + shareTxt(P.nonOnlineMarketing, P.totalRevenue) },
    { label: LAST + ' 年末员工', value: thou(L.employees) + ' 人',
      delta: '上年 ' + thou(P.employees) + ' 人' }
]);
setHTML('kpi-note',
    '<b>百度的收入结构在这十年里换了一次骨架：</b>在线营销收入从 FY2019 的 '
    + yiTxt(SG['2019'].onlineMarketing) + ' 一路降到 ' + LAST + ' 的 ' + yiTxt(L.onlineMarketing)
    + '，同期非营销收入（智能云、智能驾驶、爱奇艺会员等）从 ' + yiTxt(SG['2019'].nonOnlineMarketing)
    + ' 增至 ' + yiTxt(L.nonOnlineMarketing) + '，占总营收比重由 '
    + shareTxt(SG['2019'].nonOnlineMarketing, SG['2019'].totalRevenue) + ' 升到 '
    + shareTxt(L.nonOnlineMarketing, L.totalRevenue) + '——'
    + '<b>总营收几乎没动，里面的构成已经换掉近一半。</b>'
    + LAST + ' 百度核心经营利润 ' + yiTxt(L.coreOpIncome) + '（含长期资产减值），'
    + '爱奇艺 ' + yiTxt(L.iqiyiOpIncome) + '，全年经营亏损来自核心分部而非爱奇艺。'
    );
/* ==== 营销 / 非营销构成 ==== */
mount('chart-mix', function () {
    var nonShare = SY.map(function (y) {
        return +(SG[y].nonOnlineMarketing / SG[y].totalRevenue * 100).toFixed(2);
    });
    var o = axisBase({ x: SY, left: 84, right: 92 });
    o.yAxis = [valueAxis('亿元'), valueAxis('非营销占比 %', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '在线营销收入（亿元）', type: 'bar', stack: 'r', barWidth: '56%', itemStyle: { color: NAVY },
          data: SY.map(function (y) { return yi(SG[y].onlineMarketing); }) },
        { name: '非在线营销收入（亿元）', type: 'bar', stack: 'r', itemStyle: { color: '#2980b9' },
          data: SY.map(function (y) { return yi(SG[y].nonOnlineMarketing); }) },
        { name: '非营销占比（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: nonShare }
    ];
    return o;
});
setHTML('mix-note',
    '这张图是全页的主线：<b>FY2005–FY2013 非营销收入几乎可以忽略</b>（占比长期低于 1%），'
    + 'FY2014 起爱奇艺并表与云、智能设备等新业务陆续计入，占比 '
    + shareTxt(SG['2014'].nonOnlineMarketing, SG['2014'].totalRevenue) + ' → '
    + shareTxt(SG['2019'].nonOnlineMarketing, SG['2019'].totalRevenue) + '（FY2019）→ '
    + shareTxt(L.nonOnlineMarketing, L.totalRevenue) + '（' + LAST + '），'
    + LAST + ' 首次逼近一半。<b>口径提示：</b>这里的「非在线营销收入」是合并层面的口径，'
    + '既包含百度核心的智能云与智能驾驶，也包含爱奇艺的会员与内容分发，与下方按分部的拆分不是同一刀切法；'
    + 'FY2017 及以前为 ASC605 含增值税口径。'
    );

/* ==== 分部营收 ==== */
mount('chart-segrev', function () {
    var coreShare = GY.map(function (y) {
        return +(SG[y].coreRevenue / SG[y].totalRevenue * 100).toFixed(2);
    });
    var o = axisBase({ x: GY, left: 84, right: 92 });
    /* 分部间抵销只有 7–13 亿，与千亿级柱同轴会把纵轴拉进负区且柱子看不见，只在下方表格列示 */
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('核心占比 %', { position: 'right', splitLine: false, min: 0, max: 100 })];
    o.series = [
        { name: '百度核心（亿元）', type: 'bar', stack: 's', barWidth: '52%', itemStyle: { color: NAVY },
          data: GY.map(function (y) { return yi(SG[y].coreRevenue); }) },
        { name: '爱奇艺（亿元）', type: 'bar', stack: 's', itemStyle: { color: '#16a085' },
          data: GY.map(function (y) { return yi(SG[y].iqiyiRevenue); }) },
        { name: '百度核心占比（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: coreShare }
    ];
    return o;
});
/* ==== 分部经营利润 ==== */
mount('chart-segop', function () {
    var o = axisBase({ x: GY, left: 84, right: 96 });
    o.yAxis = [valueAxis('亿元'), valueAxis('核心经营利润率 %', { position: 'right', splitLine: false })];
    o.series = [
        { name: '百度核心经营利润（亿元）', type: 'bar', barWidth: '32%', itemStyle: { color: NAVY },
          data: GY.map(function (y) { return yi(SG[y].coreOpIncome); }) },
        { name: '爱奇艺经营利润（亿元）', type: 'bar', barWidth: '32%', itemStyle: { color: '#16a085' },
          data: GY.map(function (y) { return yi(SG[y].iqiyiOpIncome); }) },
        { name: '百度核心经营利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: GY.map(function (y) { return SG[y].coreOpMargin; }) }
    ];
    return o;
});
setHTML('seg-note',
    '<b>两个分部的角色在 FY2022 前后调了个头。</b>FY2017–FY2021 爱奇艺连续五年经营亏损（'
    + yiTxt(SG['2017'].iqiyiOpIncome) + ' 至 ' + yiTxt(SG['2021'].iqiyiOpIncome)
    + '，FY2019 亏损最深 ' + yiTxt(SG['2019'].iqiyiOpIncome) + '），全靠百度核心的利润顶住；'
    + 'FY2022 起爱奇艺转正（' + yiTxt(SG['2022'].iqiyiOpIncome) + '），FY2023 达 '
    + yiTxt(SG['2023'].iqiyiOpIncome) + '。而百度核心经营利润率从 FY2018 的 '
    + pct(SG['2018'].coreOpMargin) + ' 一路下行到 FY2022 的 ' + pct(SG['2022'].coreOpMargin)
    + '，' + LAST + ' 因长期资产减值转为 ' + pct(L.coreOpMargin) + '——'
    + '<b>' + LAST + ' 的经营亏损全部来自百度核心，爱奇艺该年仍为 ' + yiTxt(L.iqiyiOpIncome) + '。</b>'
    + '柱状图里没有画分部间抵销，因为金额很小（历年在 ' + yiTxt(-SG['2023'].interSegmentEliminations)
    + ' 到 ' + yiTxt(-SG['2019'].interSegmentEliminations) + ' 之间，与千亿级的柱子不同量级），'
    + '但两个分部相加不等于合并数就是它造成的，具体金额见下方表格。'
    );
/* ==== 分部内部拆分 ==== */
mount('chart-core', function () {
    var o = axisBase({ x: IY, left: 78, right: 30, bottom: 40 });
    o.legend.top = 6;
    o.yAxis = [valueAxis('亿元')];
    var defs = [['核心在线营销', 'coreOnlineMarketing', NAVY],
                ['智能云', 'aiCloudRevenue', '#2980b9'],
                ['其他非营销', 'coreOthers', GOLD]];
    o.series = defs.map(function (d) {
        return { name: d[0], type: 'bar', stack: 'c', barWidth: '54%', itemStyle: { color: d[2] },
                 data: IY.map(function (y) { return yi(SG[y][d[1]]); }) };
    });
    return o;
});
mount('chart-iqiyi', function () {
    var o = axisBase({ x: IY, left: 78, right: 30, bottom: 40 });
    o.legend.top = 6;
    o.yAxis = [valueAxis('亿元')];
    var defs = [['会员服务', 'iqiyiMembership', NAVY],
                ['在线广告', 'iqiyiOnlineAdvertising', '#16a085'],
                ['内容分发', 'iqiyiContentDistribution', GOLD],
                ['其他', 'iqiyiOthers', '#9aa5b1']];
    o.series = defs.map(function (d) {
        return { name: d[0], type: 'bar', stack: 'q', barWidth: '54%', itemStyle: { color: d[2] },
                 data: IY.map(function (y) { return yi(SG[y][d[1]]); }) };
    });
    return o;
});
setHTML('inner-note',
    '<b>百度核心内部：</b>智能云从 FY2018 的 ' + yiTxt(SG['2018'].aiCloudRevenue) + ' 增至 FY2024 的 '
    + yiTxt(SG['2024'].aiCloudRevenue) + '（七年约 ' + fx(SG['2024'].aiCloudRevenue / SG['2018'].aiCloudRevenue, 1)
    + ' 倍），核心非营销收入合计 ' + yiTxt(SG['2018'].coreNonOnlineMarketing) + ' → '
    + yiTxt(SG['2024'].coreNonOnlineMarketing) + '；同期核心在线营销收入 '
    + yiTxt(SG['2018'].coreOnlineMarketing) + ' → ' + yiTxt(SG['2024'].coreOnlineMarketing) + '，基本原地踏步。'
    + '<b>爱奇艺内部：</b>会员服务在 FY2019 超过在线广告成为第一大收入（'
    + yiTxt(SG['2019'].iqiyiMembership) + ' vs ' + yiTxt(SG['2019'].iqiyiOnlineAdvertising)
    + '），FY2023 达 ' + yiTxt(SG['2023'].iqiyiMembership) + '，而在线广告从 FY2018 的 '
    + yiTxt(SG['2018'].iqiyiOnlineAdvertising) + ' 缩到 FY2024 的 ' + yiTxt(SG['2024'].iqiyiOnlineAdvertising) + '。'
    + '<b>口径提示：</b>这两张图只到 FY2024——' + LAST + ' 年报未按同一套类别披露分部内部拆分，故不做外推。'
    );
/* ==== 员工与人均营收 ==== */
mount('chart-staff', function () {
    var perHead = SY.map(function (y) {
        return +(SG[y].totalRevenue / SG[y].employees * 100).toFixed(1);   /* 百万元 → 万元/人 */
    });
    var o = axisBase({ x: SY, left: 92, right: 96 });
    o.yAxis = [valueAxis('人'), valueAxis('万元 / 人', { position: 'right', splitLine: false })];
    o.series = [
        { name: '年末员工人数（人）', type: 'bar', barWidth: '56%', itemStyle: { color: '#2980b9' },
          data: SY.map(function (y) { return SG[y].employees; }) },
        { name: '人均营收（万元/人）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: perHead }
    ];
    return o;
});
setHTML('staff-note',
    '员工人数在 FY2014 见顶（' + thou(SG['2014'].employees) + ' 人）后长期回落，'
    + LAST + ' 为 ' + thou(L.employees) + ' 人，<b>比十一年前的高点少了约 '
    + thou(SG['2014'].employees - L.employees) + ' 人</b>；'
    + '人均营收同期从 ' + fx(SG['2014'].totalRevenue / SG['2014'].employees * 100, 0) + ' 万元升到 '
    + fx(L.totalRevenue / L.employees * 100, 0) + ' 万元。'
    + '<b>口径提示：</b>FY2019 起口径由「员工」改为「全职员工」，FY2015→FY2016→FY2017 的台阶'
    + '（' + thou(SG['2015'].employees) + ' → ' + thou(SG['2016'].employees) + ' → '
    + thou(SG['2017'].employees) + '）同时含业务剥离与口径重述（FY2017 由 39,343 重述为 '
    + thou(SG['2017'].employees) + '），FY2018 之后的数字为公司披露的约数，因此这条曲线不宜逐年细读。'
    );
/* ==== 运营指标 ==== */
var MY = Object.keys(SG).filter(function (y) { return SG[y].mau != null; }).sort();
mount('chart-mau', function () {
    var o = axisBase({ x: MY, left: 84, right: 40, bottom: 40 });
    o.yAxis = [valueAxis('百万月活', { min: 0 })];
    o.series = [
        { name: '百度 App 月活（百万，12 月）', type: 'bar', barWidth: '46%', itemStyle: { color: NAVY },
          label: { show: true, position: 'top', fontSize: 15, color: MUTED },
          data: MY.map(function (y) { return SG[y].mau; }) }
    ];
    return o;
});
var AGY = Object.keys(SG).filter(function (y) { return SG[y].apolloGoRidesCumulative != null; }).sort();
var AGL = AGY[AGY.length - 1];
var CY = Object.keys(SG).filter(function (y) { return SG[y].apolloGoCities != null; }).sort();
renderKpis('ops-kpis', [
    { label: '百度 App 月活（' + LAST + ' 年 12 月）', value: fx(L.mau, 0) + ' 百万',
      delta: '上年 ' + fx(P.mau, 0) + ' 百万' },
    { label: '萝卜快跑累计订单', value: fx(SG[AGL].apolloGoRidesCumulative, 0) + ' 百万单',
      delta: '截至 ' + SG[AGL].apolloGoRidesCumulativeAsOf },
    { label: '萝卜快跑开放城市', value: thou(SG[CY[CY.length - 1]].apolloGoCities) + ' 座',
      delta: SG[CY[CY.length - 1]].apolloGoNote ? '' + CY[CY.length - 1] + ' 年报口径' : '' },
    { label: '萝卜快跑累计订单（上一披露）',
      value: fx(SG[AGY[AGY.length - 2]].apolloGoRidesCumulative, 0) + ' 百万单',
      delta: '截至 ' + SG[AGY[AGY.length - 2]].apolloGoRidesCumulativeAsOf }
]);
setHTML('ops-note',
    '百度 App 月活从 FY' + MY[0] + ' 的 ' + fx(SG[MY[0]].mau, 0) + ' 百万增至 ' + fx(L.mau, 0)
    + ' 百万，<b>但最近两年停在同一个数字（' + fx(SG['2024'].mau, 0) + ' 与 ' + fx(L.mau, 0) + '）</b>，流量端已进入平台期。'
    + '萝卜快跑是另一条曲线：累计订单 ' + fx(SG['2022'].apolloGoRidesCumulative, 0) + ' 百万单（截至 '
    + SG['2022'].apolloGoRidesCumulativeAsOf + '）→ ' + fx(SG[AGL].apolloGoRidesCumulative, 0)
    + ' 百万单（截至 ' + SG[AGL].apolloGoRidesCumulativeAsOf + '），'
    + '开放城市 ' + thou(SG['2021'].apolloGoCities) + ' → ' + thou(SG[CY[CY.length - 1]].apolloGoCities) + ' 座。'
    + '<b>口径提示：</b>累计订单是「截至年报披露日」而非「截至财年末」，各年的截止日不同（见 KPI 卡上的日期），'
    + '不能当作财年数据直接算增速；年度订单数只有 FY2022（' + fx(SG['2022'].apolloGoRidesAnnual, 1)
    + ' 百万）与 FY2023（' + fx(SG['2023'].apolloGoRidesAnnual, 1) + ' 百万）两年披露过。'
    );
/* ==== 分部数据表 ==== */
var TY = GY.slice(-6);
setHTML('tbl-head', '<th>项目</th>' + TY.map(function (y) {
    return '<th style="text-align:right">' + y + '</th>';
}).join(''));
function num(v) { return v === null || v === undefined ? '—' : (v < 0 ? '(' + thou(-v) + ')' : thou(v)); }
function segRow(label, key, cls, fmt) {
    var cells = TY.map(function (y) {
        var v = SG[y][key];
        if (fmt === 'pct') return v === null || v === undefined ? '—' : pct(v);
        return '<span' + (v < 0 ? ' class="neg"' : '') + '>' + num(v) + '</span>';
    });
    return { cells: [label].concat(cells), _cls: cls };
}
renderRows('tbl-body', [
    segRow('百度核心营收', 'coreRevenue', 'row-total'),
    segRow('　核心在线营销收入', 'coreOnlineMarketing', 'row-sub'),
    segRow('　智能云', 'aiCloudRevenue', 'row-sub'),
    segRow('　其他非营销收入', 'coreOthers', 'row-sub'),
    segRow('爱奇艺营收', 'iqiyiRevenue', 'row-total'),
    segRow('　会员服务', 'iqiyiMembership', 'row-sub'),
    segRow('　在线广告', 'iqiyiOnlineAdvertising', 'row-sub'),
    segRow('　内容分发', 'iqiyiContentDistribution', 'row-sub'),
    segRow('　其他', 'iqiyiOthers', 'row-sub'),
    segRow('分部间抵销', 'interSegmentEliminations'),
    segRow('合并总营收', 'totalRevenue', 'row-total'),
    segRow('百度核心经营利润', 'coreOpIncome', 'row-total'),
    segRow('百度核心经营利润率', 'coreOpMargin', null, 'pct'),
    segRow('爱奇艺经营利润', 'iqiyiOpIncome', 'row-total'),
    segRow('抵销的经营利润', 'eliminationsOpIncome'),
    segRow('合并经营利润', 'totalOpIncome', 'row-total'),
    segRow('在线营销收入（合并）', 'onlineMarketing'),
    segRow('非在线营销收入（合并）', 'nonOnlineMarketing'),
    segRow('年末员工人数（人）', 'employees'),
    segRow('百度 App 月活（百万）', 'mau')
]);
/* ==== 口径与缺口 ==== */
renderList('gaps-list', [
    '<b>分部数据自 FY2017 才披露</b>：FY2016 及以前公司未按「百度核心 / 爱奇艺」分部列示，'
    + '故分部图从 FY2017 起，而营销／非营销构成图可回溯到 FY2005。',
    '<b>两个分部相加不等于合并数</b>：还要减去分部间抵销（' + LAST + ' 为 '
    + yiTxt(L.interSegmentEliminations) + '），表中单列一行。',
    '<b>分部内部拆分只有 FY2018–FY2024</b>：智能云、核心在线营销、爱奇艺会员／广告等类别在 ' + LAST
    + ' 年报中未按同一口径披露，因此内部拆分图与表中相应行在最新年度为空。',
    '<b>「百度核心」的名称与范围随年报变化</b>：公司在近年年报中把这一分部改称 Baidu General Business，'
    + '范围亦随业务调整而变，跨年比较时不能假定完全同口径。',
    '<b>员工口径自 FY2019 由「员工」改为「全职员工」</b>，FY2017 曾由 39,343 重述为 '
    + thou(SG['2017'].employees) + '，FY2018 起披露的是约数（40,000 一类的整数），'
    + '因此人均营收曲线只宜看趋势。',
    '<b>萝卜快跑口径不齐</b>：累计订单为「截至年报披露日」（' + AGY.map(function (y) {
        return y + ' 年报截至 ' + SG[y].apolloGoRidesCumulativeAsOf;
    }).join('、') + '），口径不是财年末；年度订单数只有 FY2022、FY2023 披露过；'
    + '开放城市数只有 FY' + CY.join('、FY') + ' 三个年度有数。',
    '<b>月活只有百度 App 一个口径</b>（每年 12 月），日活仅 FY2019 披露过一次（'
    + fx(SG['2019'].dau, 0) + ' 百万），无法构成序列；爱奇艺的会员数不在本页数据内。',
    '<b>本页不含分部资产与分部资本开支</b>：公司分部附注只给到营收与经营利润，'
    + '资产、现金与债务见「资产与现金」页，合并层面的资本开支见「业绩」页。'
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

<!-- 静态节点（容器 / 标题 / section / 图容器 / 两列 / 表格骨架）在模板里带 data-v，用 scoped 收敛，
     取自 dashboard/company/page.css。base.css 已全局引入，不重复其规则（.chart-title 等来自 base.css）。 -->
<style scoped>
section > h2 { font-size: 22px; color: #1f2937; margin-bottom: 4px; border-left: 4px solid #10243e; padding-left: 10px; }
section > h2 { font-size: 22px; color: #1f2937; margin-bottom: 4px; border-left: 4px solid #10243e; padding-left: 10px; }

section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 20px 22px; margin-top: 22px; scroll-margin-top: 116px; }

.chart { width: 100%; height: 428px; }

@media (max-width: 820px) { .two-col { grid-template-columns: 1fr; } }
table { width: 100%; border-collapse: collapse; font-size: 18px; }
</style>

<!-- 动态节点（KPI / 表格行 / 说明 / 缺口）由脚本 innerHTML 注入，不带 data-v，样式必须非 scoped；
     通用元素选择器统一以 .wrap 前缀限定在本公司页内，避免泄漏到其它页面（等价于原页各自独立文档的作用域）。 -->
<style>

.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }

</style>
