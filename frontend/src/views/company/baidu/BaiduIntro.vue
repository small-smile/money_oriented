<template>
  <div class="wrap" ref="wrapEl">

    <div class="page-head">
      <h1>百度集团（09888 / 89888 / BIDU）· 简介</h1>
      <div class="meta">
        数据取自 FY2025 Form 20-F（报送日 2026-03-17）与港交所年报中译本 · 业务与财务数据截至 2025-12-31<br>
        股权与投票权数据截至 2026-01-31 · 萝卜快跑运营数据截至 2026-02（年报原文口径）
      </div>
      <div class="tags"><span>公司沿革</span><span>两地上市</span><span>股本与投票权</span><span>员工</span><span>业务分部</span><span>公司治理</span><span>VIE 控制链</span><span>结构性风险</span></div>
    </div>

    <!-- ══════════ 公司基本情况 ══════════ -->
    <section id="sec-basics">
      <h2>公司基本情况</h2>
      <p class="sub" id="basics-sub"></p>
      <div class="kpis" id="basics-kpis"></div>
      <div style="overflow-x:auto;margin-top:14px">
        <table>
          <tbody id="basics-body"></tbody>
        </table>
      </div>
      <div class="note-generic" id="basics-note"></div>
    </section>

    <!-- ══════════ 上市与存托 ══════════ -->
    <section id="sec-listing">
      <h2>两地上市、ADS 与存托安排</h2>
      <p class="sub">纳斯达克为首次上市地（ADS），港交所为《香港上市规则》第 19C 章二次上市（A 类普通股）</p>
      <div class="cards" id="listing-cards"></div>
      <div class="note-generic" id="listing-note"></div>
    </section>

    <!-- ══════════ 股本与不同投票权 ══════════ -->
    <section id="sec-capital">
      <h2>股本结构与不同投票权（WVR）</h2>
      <p class="sub" id="cap-sub"></p>
      <div class="kpis" id="cap-kpis"></div>
      <div style="margin-top:14px">
        <h3 class="chart-title">A 类 / B 类：占已发行股数与占总投票权（%）</h3>
        <div id="chart-share-vote" class="chart" style="height:380px"></div>
      </div>
      <div style="margin-top:18px">
        <h3 class="chart-title">投票权集中度（%，截至 2026-01-31）</h3>
        <div id="chart-voting-power" class="chart" style="height:400px"></div>
      </div>
      <div class="note-generic" id="cap-note"></div>
    </section>
    <!-- ══════════ 员工 ══════════ -->
    <section id="sec-employees">
      <h2>员工规模与结构</h2>
      <p class="sub">全职员工，年报原文均为约数（approximately）· 职能与地域拆分仅披露 2025 年末</p>
      <div class="two-col">
        <div>
          <h3 class="chart-title">年末全职员工总数（人）</h3>
          <div id="chart-employees" class="chart" style="height:360px"></div>
        </div>
        <div>
          <h3 class="chart-title">2025 年末职能结构（人）</h3>
          <div id="chart-emp-func" class="chart" style="height:360px"></div>
        </div>
      </div>
      <div class="note-generic" id="emp-note"></div>
    </section>

    <!-- ══════════ 业务与分部 ══════════ -->
    <section id="sec-business">
      <h2>业务构成与报告分部</h2>
      <p class="sub" id="biz-sub"></p>
      <div id="chart-segrev" class="chart" style="height:380px"></div>
      <div class="cards" id="biz-cards"></div>
      <div class="note-generic" id="biz-note"></div>
    </section>

    <!-- ══════════ 公司治理 ══════════ -->
    <section id="sec-governance">
      <h2>公司治理：董事会与委员会</h2>
      <p class="sub">截至 FY2025 20-F 报送日 · 董事会 5 人（1 名执行董事 + 4 名独立董事）</p>
      <div style="overflow-x:auto">
        <table>
          <thead><tr id="board-head"></tr></thead>
          <tbody id="board-body"></tbody>
        </table>
      </div>
      <div class="cards" id="gov-cards"></div>
      <div class="note-generic" id="gov-note"></div>
    </section>
    <!-- ══════════ VIE 控制链 ══════════ -->
    <section id="sec-vie">
      <h2>股权与控制链：从开曼母公司到境内 VIE</h2>
      <p class="sub">Item 4.C 组织结构 + Introduction 的 VIE 说明；集团在 VIE 中不持有任何股权，仅以合约控制</p>
      <ol class="chain-list" id="chain-list"></ol>
      <div class="cards" id="vie-cards"></div>
      <div class="note-generic" id="vie-note"></div>
    </section>

    <!-- ══════════ 里程碑 ══════════ -->
    <section id="sec-milestones">
      <h2>发展沿革（2000–2026）</h2>
      <p class="sub">仅收录可在本地年报文件中确证的事件，逐条标注年报原文日期；无月份披露的年份留空</p>
      <div style="overflow-x:auto">
        <table>
          <thead><tr id="ms-head"></tr></thead>
          <tbody id="ms-body"></tbody>
        </table>
      </div>
    </section>

    <!-- ══════════ 结构性风险 ══════════ -->
    <section id="sec-risks">
      <h2>结构性风险（年报风险因素摘要）</h2>
      <p class="sub">按主题归并 Item 3.D 的风险因素，保留年报自身的表述与当期状态，不作预测</p>
      <div class="cards" id="risk-cards"></div>
    </section>

    <!-- ══════════ 披露缺口 ══════════ -->
    <section id="sec-gaps">
      <h2>口径提示与披露缺口</h2>
      <p class="sub">以下条目在本地年报文件中确实未披露或未对账，宁缺勿编</p>
      <ul class="gap-list" id="gaps-list"></ul>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { B, setScope, CHARTS, mount, axisBase, valueAxis, setText, setHTML,
         renderKpis, renderCards, renderRows, renderList,
         NAVY, GOLD, MUTED, PIE_COLORS, RESIDUAL_PATTERN, shade, toYi, fx, thou } from './charts.js'

// 逐字搬自 dashboard/company/baidu/charts/intro.js：option 与渲染逻辑原样保留，
// 仅把渲染放进 onMounted、容器查找经 setScope 限定在本组件 ref 内。图与数据一律不变。
const wrapEl = ref(null)
let charts = []
let onResize = null

onMounted(() => {
  setScope(wrapEl.value)
  CHARTS.length = 0

  /* ============ 逐字搬运开始（charts/intro.js） ============ */
var P = B.profile || {};
var BA = P.basics || {};
var GV = P.governance || {};
var VI = P.vie || {};
var SG = P.segments || {};
var MT = P._meta || {};
var CC = GV.control_concentration || {};
var LI = CC.robin_li || {};

/* 从「约 100」这类原文约数里取数字；取不到返回 null */
function num(v) {
    if (typeof v === 'number') return v;
    if (typeof v !== 'string') return null;
    var m = v.replace(/,/g, '').match(/\d+(\.\d+)?/);
    return m ? +m[0] : null;
}

function esc(s) { return s === null || s === undefined ? '—' : String(s); }

/* ── 基本情况 ───────────────────────────────────────────── */
(function () {
    var emp = BA.employees || {};
    var head = (emp.full_time_headcount || {})['2025-12-31'];
    var sc = BA.share_capital || {};
    var out = sc.outstanding_2025_12_31 || {};
    var au = BA.auditor || {};

    setText('basics-sub', '注册地开曼群岛 · 总部北京 · 业务与员工数据截至 2025-12-31 · 审计报告日 ' + esc(au.report_date));

    renderKpis('basics-kpis', [
        { label: '注册成立', value: '2000-01-18', delta: '开曼群岛豁免有限公司' },
        { label: '纳斯达克上市', value: '2005-08-05', delta: 'BIDU（ADS）' },
        { label: '港交所上市', value: '2021-03-23', delta: '9888 · 第 19C 章二次上市' },
        { label: '年末全职员工', value: thou(head) + ' 人', delta: '较 2023 年末减少 6,300 人' },
        { label: '年末已发行股份', value: fx(out.total_computed / 1e8, 2) + ' 亿股', delta: 'A 类 + B 类，封面页口径' },
        { label: '创始人投票权', value: fx(LI.pct_of_voting_power, 1) + '%',
          delta: '李彦宏，截至 ' + esc(LI.as_of) }
    ]);
})();
/* ── 基本情况明细表 ─────────────────────────────────────── */
(function () {
    var au = BA.auditor || {};
    var fee = au.audit_fees_rmb_thousand || {};
    var sc = BA.share_capital || {};
    var bb = BA.buyback || {};
    var rows = [
        ['法定形式', esc(BA.legal_form)],
        ['注册成立', esc(BA.incorporation_date)],
        ['名称沿革', (BA.name_history || []).join('<br>')],
        ['注册办事处', esc(BA.registered_office)],
        ['总部', esc(BA.headquarters)],
        ['财政年度', esc(BA.fiscal_year)],
        ['审计师', esc(au.name) + '（' + esc(au.location) + '）· PCAOB ID ' + esc(au.pcaob_id)
            + '<br>' + esc(au.tenure)
            + '<br>审计费用：' + thou(fee['2024']) + ' → ' + thou(fee['2025']) + ' 千元人民币（FY2024 → FY2025）'],
        ['优先股', esc(sc.preferred_shares_issued)],
        ['库存股', thou(bb.treasury_shares_2025_12_31) + ' 股（2025-12-31）<br>' + esc(bb.programs)]
    ];
    renderRows('basics-body', rows.map(function (r) {
        return { cells: ['<b>' + r[0] + '</b>', r[1]] };
    }));
    setHTML('basics-note',
        '公司在 20-F 中明确表述<b>「Baidu, Inc. is not a Chinese operating company but a Cayman Islands holding company」</b>——'
        + '上市主体本身不在中国内地经营业务，境内业务由子公司与 VIE 承担，投资者持有的是开曼控股公司的股份而非境内经营主体的股权。'
        + '<br><br>本页所有条目均取自本地年报文件（' + esc((MT.as_of || {}).filing_date) + ' 报送的 FY2025 20-F 为主用来源），'
        + '未联网补数；年报中无法确证的字段一律留空，见页尾「披露缺口」。');
})();
/* ── 上市与存托 ─────────────────────────────────────────── */
(function () {
    var LS = BA.listings || {};
    var NQ = LS.nasdaq || {};
    var HK = LS.hkex || {};
    var AD = BA.ads || {};
    renderCards('listing-cards', [
        { title: '纳斯达克（BIDU，' + esc(NQ.date) + '）',
          body: esc(NQ.instrument) + '。' + esc(NQ.note) + '：一份 ADS 与其代表的 A 类普通股可自由互换，'
              + '因此美股与港股实为同一类股份的两个交易场所。' },
        { title: '港交所（9888 / 89888，' + esc(HK.date) + '）',
          body: esc(HK.type) + '，净募资' + esc(HK.net_proceeds) + '。' + esc(HK.board_lot)
              + '。<br>自 2023-06-19 起增设人民币柜台，股份代号 89888，配合联交所「港币—人民币双柜台模式」（20-F Item 9.A 原文）。' },
        { title: '第 19C 章豁免与 55% 转板触发线',
          body: esc(HK.chapter_19c_exemptions) + '<br><br>' + esc(HK.dual_primary_trigger) },
        { title: 'ADS 比例与存托、登记安排',
          body: '当前比例：<b>' + esc(AD.ratio_current) + '</b><br>沿革：' + (AD.ratio_history || []).join('；')
              + '<br><br>存托银行：' + esc(AD.depositary_bank)
              + '<br>香港股份登记及过户处：' + esc(AD.hk_share_registrar)
              + '<br>香港托管人：' + esc(AD.hk_custodian) }
    ]);
    setHTML('listing-note',
        '读跨市场数据时要注意<b>比例与拆细两次口径变化</b>：ADS 由 1:1 → 1:10（2010-05-12）→ 1 ADS = 8 股 A 类（2021-03-01，同时实施 1 拆 80 股份拆细）。'
        + '因此每股类指标（EPS、每股净资产）在这两个时点前后不可直接比较，年报披露的每 ADS 数据已按最新比例追溯调整。'
        + '<br><br>本地年报文件未提及港股简称的 WVR 后缀标记（-W / -SW / -WS），也未提及港股通资格，两项均留空——'
        + '不是「没有」，而是<b>本地一手文件无从确证</b>。');
})();
/* ── 股本与投票权 ───────────────────────────────────────── */
var SC = BA.share_capital || {};
var OUT = SC.outstanding_2026_01_31 || {};
var DC = GV.dual_class || {};
var VOTE_A = OUT.class_a * (DC.class_a_votes || 1);
var VOTE_B = OUT.class_b * (DC.class_b_votes || 10);
var VOTE_ALL = VOTE_A + VOTE_B;

(function () {
    var AU = SC.authorized || {};
    setText('cap-sub', '股数与投票权截至 2026-01-31（Item 6.E 实益持股表分母）· 法定股本取自股本附注 · 总投票权 '
        + thou(VOTE_ALL) + ' 票为按 A 类 1 票 / B 类 10 票自算');
    renderKpis('cap-kpis', [
        { label: '法定股本', value: fx(AU.total_shares / 1e8, 0) + ' 亿股',
          delta: 'A 类 660 亿 / B 类 28.32 亿 / 优先股 8 亿' },
        { label: 'A 类已发行', value: fx(OUT.class_a / 1e8, 2) + ' 亿股',
          delta: '占股数 ' + fx(OUT.class_a / OUT.total * 100, 2) + '% · 每股 1 票' },
        { label: 'B 类已发行', value: fx(OUT.class_b / 1e8, 2) + ' 亿股',
          delta: '占股数 ' + fx(OUT.class_b / OUT.total * 100, 2) + '% · 每股 10 票' },
        { label: 'B 类占总投票权', value: fx(VOTE_B / VOTE_ALL * 100, 2) + '%',
          delta: '19.25% 的股数对应七成投票权' },
        { label: '李彦宏投票权', value: fx(LI.pct_of_voting_power, 1) + '%',
          delta: '持股 ' + fx(LI.pct_of_total_shares, 1) + '%' },
        { label: 'WVR 受益人合计', value: fx(CC.wvr_beneficiaries_total_pct_of_voting_rights, 1) + '%',
          delta: '港交所口径，含马东敏 11.4%' }
    ]);
})();
mount('chart-share-vote', function () {
    var o = axisBase({ x: ['A 类普通股', 'B 类普通股'], left: 72, right: 30, top: 44 });
    o.yAxis = [valueAxis('%', { min: 0, max: 100 })];
    o.series = [
        { name: '占已发行股数（%）', type: 'bar', barWidth: '28%', itemStyle: { color: NAVY },
          label: { show: true, position: 'top', fontSize: 16, formatter: '{c}%' },
          data: [+fx(OUT.class_a / OUT.total * 100, 2), +fx(OUT.class_b / OUT.total * 100, 2)] },
        { name: '占总投票权（%）', type: 'bar', barWidth: '28%', itemStyle: { color: GOLD },
          label: { show: true, position: 'top', fontSize: 16, formatter: '{c}%' },
          data: [+fx(VOTE_A / VOTE_ALL * 100, 2), +fx(VOTE_B / VOTE_ALL * 100, 2)] }
    ];
    return o;
});
mount('chart-voting-power', function () {
    /* 具名投票权披露：李彦宏 / 马东敏 / BlackRock；其余不可穿透部分作残余垫最后 */
    var WB = CC.wvr_beneficiaries || [];
    var melissa = 0;
    WB.forEach(function (w) { if (/Melissa|马东敏/.test(w.name)) melissa = w.pct_of_voting_rights; });
    var named = [
        { name: '李彦宏（含员工不可撤销投票代理）', v: LI.pct_of_voting_power },
        { name: '马东敏（Melissa Ma）', v: melissa },
        { name: 'BlackRock, Inc.', v: (CC.blackrock || {}).pct_of_voting_power }
    ];
    var sum = named.reduce(function (s, d) { return s + d.v; }, 0);
    var data = named.map(function (d, i) {
        return { name: d.name, value: +d.v.toFixed(2), itemStyle: { color: PIE_COLORS[i] } };
    });
    data.push({ name: '其他股东（不可穿透）', value: +(100 - sum).toFixed(2),
                itemStyle: { color: RESIDUAL_PATTERN, borderColor: '#999', borderWidth: 1 } });
    return {
        tooltip: { trigger: 'item', fontSize: 17, valueFormatter: function (v) { return v + '%'; } },
        series: [{
            type: 'pie', radius: ['52%', '72%'], center: ['50%', '52%'], sort: null,
            data: data,
            label: {
                fontSize: 15, alignTo: 'edge', edgeDistance: 6, minMargin: 20, overflow: 'none',
                formatter: function (p) { return '{n|' + p.name + '}{v|' + fx(p.value, 2) + '%}'; },
                rich: {
                    n: { fontSize: 15, color: '#374151', width: 254, align: 'left' },
                    v: { fontSize: 15, color: NAVY, fontWeight: 'bold', width: 68, align: 'right' }
                }
            },
            labelLine: { length: 10, length2: 14 }
        }]
    };
});
(function () {
    var trig = DC.auto_conversion_triggers || [];
    var iss = SC.issued_shares_per_balance_sheet || {};
    setHTML('cap-note',
        '<b>B 类每股 10 票是这家公司治理结构的全部关键</b>：19.25% 的股数（' + thou(OUT.class_b) + ' 股 B 类）对应 '
        + fx(VOTE_B / VOTE_ALL * 100, 2) + '% 的投票权，创始人一人即掌握 ' + fx(LI.pct_of_voting_power, 1)
        + '% 投票权，足以决定董事选举、章程修订、合并与重大资产出售。'
        + '<br><br>转换安排：' + esc(DC.conversion) + '；' + trig.join('；') + '。'
        + '<br><br>上图「李彦宏」一栏含 ' + thou(51550880) + ' 股以 ADS 形式由员工持有、但已向其授予不可撤销投票代理的 A 类股，'
        + '因此这部分投票权并非其自有持股。'
        + '<br><br>两点必须提示的口径问题：（1）年报<b>全文未使用「controlled company」表述</b>，也未声明依赖纳斯达克受控公司豁免，'
        + '创始人控制只能由 59.9% 投票权与 WVR 受益人合计 71.4% 间接说明；'
        + '（2）封面页口径的已发行股份 ' + thou(SC.outstanding_2025_12_31.total_computed) + ' 股与股本附注口径 '
        + thou(iss['2025-12-31']) + ' 股相差约 3.98 亿股，库存股仅 ' + thou((BA.buyback || {}).treasury_shares_2025_12_31)
        + ' 股不足以解释全部差额，本地文件未提供逐项对账。');
})();
/* ── 员工 ───────────────────────────────────────────────── */
var EMP = BA.employees || {};
var HC = EMP.full_time_headcount || {};
var HC_YEARS = Object.keys(HC).sort();

mount('chart-employees', function () {
    var o = axisBase({ x: HC_YEARS.map(function (d) { return d.slice(0, 4) + ' 年末'; }), left: 84, right: 30, top: 44 });
    o.yAxis = [valueAxis('人', { min: 0 })];
    o.series = [{ name: '年末全职员工（人）', type: 'bar', barWidth: '46%', itemStyle: { color: NAVY },
                  label: { show: true, position: 'top', fontSize: 16,
                           formatter: function (p) { return thou(p.value); } },
                  data: HC_YEARS.map(function (y) { return HC[y]; }) }];
    return o;
});

mount('chart-emp-func', function () {
    var fs = EMP.function_split_2025 || {};
    var keys = Object.keys(fs);
    return {
        tooltip: { trigger: 'item', fontSize: 17,
                   valueFormatter: function (v) { return thou(v) + ' 人'; } },
        series: [{
            type: 'pie', radius: ['40%', '62%'], center: ['50%', '52%'], sort: null,
            data: keys.map(function (k, i) {
                return { name: k, value: fs[k], itemStyle: { color: PIE_COLORS[i] } };
            }),
            label: { fontSize: 16, alignTo: 'edge', edgeDistance: 12, minMargin: 20,
                     formatter: function (p) { return p.name + ' ' + fx(p.percent, 1) + '%'; } },
            labelLine: { length: 12, length2: 14 }
        }]
    };
});
(function () {
    var geo = EMP.geography_2025 || {};
    var parts = Object.keys(geo).map(function (k) {
        var n = num(geo[k]);
        return k + ' ' + (n === null ? esc(geo[k]) : thou(n) + ' 人');
    });
    setHTML('emp-note',
        '员工总数连续三年下降：' + thou(HC['2023-12-31']) + ' → ' + thou(HC['2024-12-31']) + ' → '
        + thou(HC['2025-12-31']) + ' 人，三年累计减少 ' + thou(HC['2023-12-31'] - HC['2025-12-31']) + ' 人。'
        + '同期研发仍占 ' + fx((EMP.function_split_2025 || {}).研发 / HC['2025-12-31'] * 100, 1) + '%，是四类职能中最大的一块。'
        + '<br><br>地域分布（2025 年末）：' + parts.join(' · ') + '——境外员工仅约百人，人力几乎全部在中国内地，其中北京一地占三分之二。'
        + '<br><br>' + esc(EMP.note) + '；年报未披露员工的学历、年龄、岗位序列细分，也未披露人均薪酬，故本页不作推算。');
})();
/* ── 业务与分部 ─────────────────────────────────────────── */
var REV = SG.revenue_rmb_million || {};
var R23 = REV['2023'] || {}, R25 = REV['2025'] || {};

setText('biz-sub', 'ASC 280 口径两个报告分部：Baidu General Business 与 iQIYI · 年报只给出 FY2023 与 FY2025 两个年度的分部收入对比 · 单位：亿元人民币');

mount('chart-segrev', function () {
    var o = axisBase({ x: ['Baidu General Business', 'iQIYI'], left: 84, right: 30, top: 44 });
    o.yAxis = [valueAxis('亿元', { min: 0 })];
    function bar(name, r, color) {
        return { name: name, type: 'bar', barWidth: '28%', itemStyle: { color: color },
                 label: { show: true, position: 'top', fontSize: 16,
                          formatter: function (p) { return fx(p.value, 0); } },
                 data: [toYi(r.baidu_general_business), toYi(r.iqiyi)] };
    }
    o.series = [bar('FY2023 收入（亿元）', R23, shade(NAVY, 0.45)), bar('FY2025 收入（亿元）', R25, NAVY)];
    return o;
});
(function () {
    var G = SG.baidu_general_business || {};
    var IQ = SG.iqiyi || {};
    renderCards('biz-cards', [
        { title: '搜索与信息流', body: esc(G.search_and_feed) },
        { title: 'AI 云', body: esc(G.ai_cloud) },
        { title: '文心（ERNIE）大模型', body: esc(G.ernie) },
        { title: '飞桨（PaddlePaddle）与自研芯片', body: esc(G.paddlepaddle) + '<br><br>' + esc(G.ai_chip) },
        { title: '萝卜快跑（Apollo Go）', body: esc(G.apollo_go) + '<br><br>' + esc(G.apollo_go_global)
              + '<br><br>车型：' + esc(G.apollo_vehicles) },
        { title: '小度（Smart Living Group）', body: esc(G.xiaodu) },
        { title: 'iQIYI（独立上市的合并分部）', body: esc(IQ.positioning) + '<br><br>' + esc(IQ.note) },
        { title: '管理层叙事与科技伦理', body: esc(SG.ai_narrative_zh) + '<br><br>' + esc(SG.tech_ethics) }
    ]);
    setHTML('biz-note',
        '<b>分部口径自 FY2025 第四季度起更名</b>：' + esc(SG.rename_note)
        + '。看图时把「Baidu General Business」与旧文中的「百度核心」视为同一分部，但需注意更名同时伴随口径重新界定。'
        + '<br><br>' + esc(SG.revenue_trend_note) + '。两个分部收入相加还需扣除分部间抵销（FY2023 −'
        + fx(-toYi(R23.eliminations), 2) + ' 亿元、FY2025 −' + fx(-toYi(R25.eliminations), 2)
        + ' 亿元）才等于合并收入（' + fx(toYi(R23.consolidated), 0) + ' 亿元 → ' + fx(toYi(R25.consolidated), 0) + ' 亿元）。'
        + '<br><br>' + esc(SG.core_share_of_revenue) + '；商誉分三个报告单元（Baidu General Business 剔除 SLG、SLG、iQIYI），'
        + '部分资产不分摊至分部，因此分部收入之外的分部资产／利润拆分在年报中并不完整。');
})();
/* ── 治理 ───────────────────────────────────────────────── */
(function () {
    var cols = ['姓名', '年龄', '职务', '独立董事', '任职起始', '委员会'];
    setHTML('board-head', cols.map(function (c) { return '<th>' + c + '</th>'; }).join(''));
    renderRows('board-body', (GV.board_members || []).map(function (d) {
        var cm = (d.committees || []).length ? d.committees.join('、') : '—';
        return {
            cells: [
                esc(d.name_zh) + '<br><span style="font-size:15px;color:#6b7280">' + esc(d.name_en) + '</span>',
                esc(d.age), esc(d.title_zh), d.independent ? '是' : '否', esc(d.since), cm
            ],
            _th: true,
            _cls: d.independent ? '' : 'row-total'
        };
    }));

    var CM = GV.committees || {};
    var AC = CM.audit_committee || {};
    var SM = GV.senior_management_partial || [];
    renderCards('gov-cards', [
        { title: '三个董事会委员会',
          body: (CM.list || []).join('<br>') + '<br><br>' + esc(GV.director_terms) },
        { title: '审计委员会仅 2 人（偏离纳斯达克规则）',
          body: '成员：' + (AC.members || []).join('、') + '<br>' + esc(AC.independence)
              + '<br>' + esc(AC.financial_expert) + '<br><br><b>' + esc(AC.deviation) + '</b>' },
        { title: '高管（可确证部分）',
          body: SM.map(function (m) {
              return esc(m.name_zh || m.name_en) + '：' + esc(m.title_zh);
          }).join('<br>') + '<br><br>' + esc(GV.senior_management_note) },
        { title: '网络安全治理（Item 16K）', body: esc(GV.cybersecurity_governance) }
    ]);
    setHTML('gov-note',
        '<b>' + esc(GV.board_size_quote_zh) + '</b>——五人董事会里只有创始人一人是执行董事，其余四位均为独立董事，'
        + '但在 B 类 10 票的架构下，董事选举本身由创始人的 ' + fx(LI.pct_of_voting_power, 1) + '% 投票权决定。'
        + '<br><br>' + esc(GV.board_diversity) + '。' + esc(GV.board_note) + '。'
        + '<br><br>另需注意：港交所年报中译本是依《香港上市规则》第 13.46(2) 条提供的 20-F 摘录，<b>没有港式「企业管治报告」章节</b>，'
        + '因此董事会会议出席率、企业管治守则偏离说明、审核委员会工作报告等港式披露在本地文件中完全缺失。');
})();
/* ── VIE 控制链 ─────────────────────────────────────────── */
(function () {
    var chain = VI.control_chain || [];
    setHTML('chain-list', chain.map(function (c, i) {
        var last = i === chain.length - 1;
        return '<li' + (last ? ' style="margin-top:4px"' : '') + '>'
            + (last ? '<b>' + c + '</b>（合约控制，非股权）' : c) + '</li>';
    }).join(''));

    var OL = VI.onshore_licenses || {};
    var AS = VI.asset_share || {};
    var RS = VI.revenue_share_disclosed || {};
    renderCards('vie-cards', [
        { title: '为什么需要 VIE', body: esc(VI.why_needed) },
        { title: '控制是怎么实现的', body: esc(VI.control_mechanics) },
        { title: '合约类型（8 类）', body: (VI.contract_types || []).join('<br>') },
        { title: '持牌主体与牌照范围',
          body: esc(OL.holder) + '<br><br>' + (OL.license_scope || []).join('、')
              + '<br><br><span style="color:#6b7280">' + esc(OL.note) + '</span>' },
        { title: '监管背景', body: esc(VI.regulatory_backdrop) }
    ]);
    setHTML('vie-note',
        'VIE 在合并报表里的分量：FY2025 外部收入占集团的 <b>' + esc(RS['2025']) + '%</b>（FY2023 '
        + esc(RS['2023']) + '% → FY2024 ' + esc(RS['2024']) + '%），总资产 '
        + fx(toYi(AS.vie_total_assets_rmb_million['2025-12-31']), 2) + ' 亿元、约占合并总资产 '
        + fx(AS.vie_asset_share_pct_2025_computed, 1) + '%（自算值，年报未以百分比披露）。'
        + '单一 VIE 层面只披露百度网讯（占外部收入 ' + esc((VI.single_vie_revenue_detail || {}).baidu_netcom_pct_of_external_revenues['2025'])
        + '%）与 Beijing Perusal（0%），iQIYI 一线的 VIE 未单列占比。'
        + '<br><br>' + esc(VI.chain_note) + '。'
        + '<br><br>结构含义：投资者买入的是开曼母公司股份，母公司对持牌主体<b>没有任何股权</b>，'
        + '只有一整套可被中国法律与司法解释否定的合约；名义股东违约、继承或婚姻纠纷、监管认定合约无效，'
        + '都可能导致失去控制并终止合并（详见下节风险）。');
})();
/* ── 里程碑 / 风险 / 缺口 ───────────────────────────────── */
(function () {
    setHTML('ms-head', ['年份', '日期', '事件'].map(function (c) { return '<th>' + c + '</th>'; }).join(''));
    renderRows('ms-body', (P.milestones || []).slice().reverse().map(function (m) {
        return { cells: [esc(m.year), m.date ? esc(m.date) : '—', esc(m.text_zh)], _th: true };
    }));

    renderCards('risk-cards', (P.risks || []).map(function (r) {
        var body = esc(r.statement_zh);
        if (r.current_status_zh) {
            body += '<br><br><b>当期状态：</b>' + esc(r.current_status_zh);
        }
        return { title: esc(r.title_zh), body: body };
    }));

    renderList('gaps-list', (P.disclosure_gaps || []).map(function (g) {
        return '<b>' + esc(g.gap) + '</b>——' + esc(g.detail);
    }));
})();
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

<!-- 动态节点（KPI / 卡片 / 表格行 / 控制链 / 说明 / 缺口）由脚本 innerHTML 注入，不带 data-v，样式必须非 scoped；
     通用元素选择器统一以 .wrap 前缀限定在本公司页内，避免泄漏到其它页面（等价于原页各自独立文档的作用域）。 -->
<style>
/* —— intro.html <head> 内联样式，逐字搬入 —— */
.note-generic { margin: 10px 0 0; padding: 12px 16px; background: #f6f7f9; border-left: 4px solid #b7b1c4; border-radius: 6px; font-size: 18px; color: #555; line-height: 1.75; }
.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }
.gap-list b { color: #10243e; }
.chain-list { margin: 6px 0 0 22px; font-size: 18px; color: #444; line-height: 1.9; }
.chain-list b { color: #10243e; }
/* 文字型表格：右对齐是给数字用的，这几张表要靠左，标签列与日期列不折行 */
#basics-body td { text-align: left; vertical-align: top; }
#basics-body td:first-child { white-space: nowrap; width: 96px; }
#board-head th, #board-body td { text-align: left; }
#board-head th:nth-child(2), #board-body td:nth-child(2) { text-align: right; }
#ms-head th, #ms-body td { text-align: left; }
#ms-body td:first-child, #ms-body td:nth-child(2),
#ms-body th:first-child, #ms-body th:nth-child(2) { white-space: nowrap; }
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
