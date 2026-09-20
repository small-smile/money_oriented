<template>
  <div class="wrap">
    <div class="page-head">
      <h1 ref="pageTitle">运营与资本开支</h1>
      <div class="meta" ref="pageMeta"></div>
      <div class="tags"><span>用户数</span><span>ARPU</span><span>5G</span><span>宽带</span><span>云与第二曲线</span><span>资本开支</span></div>
    </div>

    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">{{ error }}</div>

    <section id="sec-kpi" ref="secKpi" hidden>
      <h2 ref="kpiTitle">最新披露年度运营指标</h2>
      <p class="sub" ref="kpiSub"></p>
      <div class="kpis" ref="kpis"></div>
      <div class="entity" ref="caliberWarn"></div>
    </section>

    <div ref="chartsHost" id="charts"></div>

    <section id="sec-gaps" ref="secGaps" hidden>
      <h2>披露口径变更与缺口</h2>
      <p class="sub">以下均为发行人年报披露口径收窄／变更，本页对近似表述不录入、也不按渗透率或净增数推算</p>
      <ul class="gap-list" ref="gaps"></ul>
      <div class="note" ref="gapSrc" style="max-width:none"></div>
    </section>
  </div>
</template>

<script setup>
import LoadingNote from '../../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { apiGet } from '../../../api'
import {
  getCode, getMeta, fmt, mdBold, seriesOf,
  lineSeries, barSeries, chartCard, AXIS_Y, axisX, marksOn,
} from './charts'

// 逐字搬自 dashboard/company/telecom/charts/operation.js（公共层 common.js 已抽到 ./charts）：
// 每个 ECharts option 与 renderHead/buildCharts/renderGaps 逻辑原样保留（含分号），仅把
// document.getElementById 换成组件模板 ref、axios 换成统一 apiGet、echarts 实例收集进 charts。
const loading = ref(true)
const error = ref('')
const pageTitle = ref(null)
const pageMeta = ref(null)
const kpiTitle = ref(null)
const kpiSub = ref(null)
const kpis = ref(null)
const caliberWarn = ref(null)
const chartsHost = ref(null)
const secKpi = ref(null)
const gaps = ref(null)
const gapSrc = ref(null)
const secGaps = ref(null)

const CODE = getCode()
const META = getMeta(CODE)
let charts = []
let prevBodyBg = ''

function opsYears(A, keys) {
    return Object.keys(A).filter(y => keys.some(k => A[y][k] !== null && A[y][k] !== undefined)).sort();
}

function renderHead(d) {
    const A = d.annual;
    const years = opsYears(A, ['ops_capex_yr', 'ops_mobile_users_mn', 'ops_cloud_rev', 'ops_dx_rev']);
    const last = years[years.length - 1], rec = A[last];
    document.title = d.name + '（' + d.secucode + '）· 运营与资本开支';
    pageTitle.value.textContent = d.name + '（' + d.secucode + '）· 运营与资本开支';
    pageMeta.value.innerHTML =
        '上交所 A 股年报原文录入 · 用户为百万户、ARPU 为元/户/月、金额为亿元<br>' +
        '覆盖 ' + years[0] + '—' + last + ' 年度（' + (d.ops_meta && d.ops_meta.report_source ? d.ops_meta.report_source : '') + '）';

    kpiTitle.value.textContent = last + ' 年度运营指标';
    kpiSub.value.textContent = '空缺项为该年年报未披露精确值（见页尾缺口清单），未按渗透率或净增数推算';
    const card = (label, value, sub) => '<div class="kpi"><div class="label">' + label + '</div>' +
        '<div class="value">' + value + '</div>' +
        (sub ? '<div class="delta" style="color:#7f8c8d">' + sub + '</div>' : '') + '</div>';
    const num = (k, dec, unit) => rec[k] === null || rec[k] === undefined ? '未披露' : fmt(rec[k], dec) + ' ' + unit;
    kpis.value.innerHTML = [
        card('移动用户', num('ops_mobile_users_mn', 1, '百万户'), '移动 ARPU ' + num('ops_mobile_arpu', 1, '元/户/月')),
        card('5G 用户', num('ops_users_5g_net_mn', 0, '百万户（网络口径）') !== '未披露'
            ? num('ops_users_5g_net_mn', 0, '百万户') : num('ops_users_5g_pkg_mn', 0, '百万户'),
            rec.ops_penetration_5g ? '5G 渗透率 ' + fmt(rec.ops_penetration_5g, 1) + '%' : '套餐口径与网络口径见下图'),
        card('宽带用户', num('ops_broadband_users_mn', 1, '百万户'),
            rec.ops_gigabit_users_mn ? '千兆用户 ' + fmt(rec.ops_gigabit_users_mn, 0) + ' 百万户'
                : '宽带 ARPU ' + num('ops_bb_arpu', 1, '元/户/月')),
        card((rec.ops_cloud_name || '云业务') + '收入', num('ops_cloud_rev', 0, '亿元'),
            (rec.ops_dx_name || '第二曲线') + ' ' + num('ops_dx_rev', 0, '亿元')),
        card('资本开支（年报口径）', num('ops_capex_yr', 0, '亿元'),
            rec.ops_capex_guide_next ? '下一年度指引 ' + fmt(rec.ops_capex_guide_next, 0) + ' 亿元' : '下一年度指引未披露'),
        card('服务收入', num('ops_service_rev', 0, '亿元'),
            rec.ops_depreciation ? '折旧及摊销 ' + fmt(rec.ops_depreciation, 0) + ' 亿元' : '折旧摊销未单列')
    ].join('');
    caliberWarn.value.innerHTML = '<b>口径：</b>' + mdBold(d.ops_meta && d.ops_meta.caliber_note);
    secKpi.value.hidden = false;
}

const OPS_NOTES = {
    '600941': {
        mobile: '移动客户 2025 年 10.05 亿户，年净增已降到千万级以内；ARPU 由 2024 年 48.5 元回落到 46.8 元 —— ' +
            '年报把营收同口径差异归因于套餐收入分拆纳税影响，ARPU 的下行与低价副卡、融合套餐分摊有关。',
        fiveg: '<b>套餐口径 ≠ 网络口径：</b>2023 年同时披露 5G 套餐客户 7.95 亿户与 5G 网络客户 4.65 亿户，' +
            '差额是买了 5G 套餐但未接入 5G 网络的用户。2024 年起只披露网络口径（2025 年 6.42 亿户），' +
            '因此本图两条线不能接续读。',
        bb: '有线宽带从 2015 年零起步做到 2024 年 3.15 亿户，是这十年唯一的份额逆转战。' +
            '2025 年报不再披露有线宽带客户数、改披露千兆宽带客户数（1.09 亿户），故这条线止于 2024 年。',
        cloud: '移动云 2021—2023 年 242→503→833 亿元，2024 年起不再披露绝对值；' +
            '数字化转型收入只有 2022 年（2,076 亿元）与 2024 年（2,788 亿元，占主营 45.6%）在正文给了绝对值。',
        capex: '资本开支 2022 年 1,852 亿元见顶后连降至 2025 年 1,509 亿元，2026 年指引 1,366 亿元；' +
            '折旧及摊销却仍在 1,700—1,800 亿元的高位，这是毛利率缓降的直接来源。'
    },
    '601728': {
        mobile: '移动用户由 2021 年 3.72 亿户升到 2025 年 4.39 亿户，是三家里唯一还有明显用户增量的；' +
            'ARPU 稳在 45 元附近（45.0/45.2/45.4/45.6/45.1），量增价稳。',
        fiveg: '2022 年后不再披露 5G 套餐用户绝对数，只给渗透率（2023 年 70.4%）；' +
            '2025 年口径又改为「5G 网络用户渗透率」68.8%。渗透率乘用户数属推算，本页不做，故绝对值序列止于 2022 年。',
        bb: '宽带用户 1.70→2.01 亿户稳步增长，宽带综合 ARPU（含天翼高清与智家应用）自 2021 年起小幅回升 —— ' +
            '与只含接入的联通口径不可比。',
        cloud: '<b>天翼云是三家里最大且披露最连续的：</b>2021 年 279 亿元 → 2025 年 1,207 亿元（四年 4.3 倍）；' +
            '产业数字化收入 989→1,473 亿元，但 2025 年增速只有 +0.5%，第二曲线进入平台期。',
        capex: '资本开支 2023 年 988 亿元见顶、2025 年 804 亿元。2019-09 起与联通共建共享 5G 接入网，' +
            '是其覆盖同等网络所需投资长期低于中国移动的制度性原因。'
    },
    '600050': {
        mobile: '移动出账用户 2019 年 3.18 亿户 → 2020 年 3.058 亿户的下降，是清理低效／不活跃用户与 2G 退网并行的结果，' +
            '同期 ARPU 由 40.4 元回升到 42.1 元。<b>2022 年起年报只给「超过 3.2 亿户」这类近似表述</b>，本图不录入，' +
            '所以两条线都止于 2021 年。',
        fiveg: '5G 套餐用户 2020—2022 年 70.83→155.29→213.03 百万户，2023 年起只披露渗透率（78%），' +
            '本页不按渗透率反推绝对值。',
        bb: '固网宽带 2015 年 7,233 万户 → 2021 年 9,505 万户；宽带用户接入 ARPU 由 63.6 元一路降到 41.3 元，' +
            '其中 2015→2016 年的落差同时含营改增后收入转不含税与光改后低价套餐放量两层因素。',
        cloud: '联通云 2022—2024 年 361→510→686 亿元，2025 年只披露同比 +5.2%；' +
            '2024 年起口径「优化为融合创新解决方案产生的云 IDC／云资源／云平台…」，与 2023 年及以前不完全可比。',
        capex: '资本开支 2015 年 1,338.8 亿元 → 2017 年 421.3 亿元（−68%），2025 年 541.5 亿元，' +
            '2026 年指引约 500 亿元且算力投资占比超 35%。共建共享使其 2023 年节省运营开支约 390 亿元、' +
            '<b>累计节省资本开支约 3,400 亿元</b>。'
    }
};

function buildCharts(d) {
    const host = chartsHost.value;
    const A = d.annual, N = OPS_NOTES[CODE];
    const marks = [{year: '2019', text: '5G 发牌'}];

    // ① 移动用户与 ARPU
    (function () {
        const years = opsYears(A, ['ops_mobile_users_mn', 'ops_mobile_arpu']);
        if (!years.length) return;
        const s = [
            barSeries('移动用户数', seriesOf(A, years, 'ops_mobile_users_mn', 1, null), META.color, {barMaxWidth: 42}),
            lineSeries('移动 ARPU（右轴）', seriesOf(A, years, 'ops_mobile_arpu', 1, null), '#b45309', {yAxisIndex: 1, width: 2.4})
        ];
        const c = chartCard(host, {
            id: 'mobile', title: '移动用户数与 ARPU', sub: '柱：期末移动用户／客户／出账用户（百万户）· 线：移动 ARPU（元/户/月，右轴，不从 0 起画）',
            note: N.mobile,
            detail: '<b>口径提醒：</b>三家的分母定义不同（移动客户／移动用户／移动出账用户），分子是否含增值业务也不完全一致，' +
                '只适合看自身趋势，不宜比小数点后的高下。提速降费的两个时点：2017-09 取消手机国内长途漫游费、' +
                '2018-07 取消流量漫游费。'
        }, undefined, charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 86, right: 86, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '百万户'}),
                Object.assign({}, AXIS_Y, {name: '元/户/月', scale: true, splitLine: {show: false}})],
            series: marksOn(s, years, marks)
        });
    })();

    // ② 5G 用户：套餐口径与网络口径分列，渗透率单挂右轴
    (function () {
        const years = opsYears(A, ['ops_users_5g_pkg_mn', 'ops_users_5g_net_mn', 'ops_penetration_5g']);
        if (!years.length) return;
        const s = [
            barSeries('5G 套餐用户', seriesOf(A, years, 'ops_users_5g_pkg_mn', 1, null), '#7c3aed', {barMaxWidth: 42}),
            barSeries('5G 网络用户', seriesOf(A, years, 'ops_users_5g_net_mn', 1, null), '#a78bfa', {barMaxWidth: 42}),
            lineSeries('5G 渗透率（右轴）', seriesOf(A, years, 'ops_penetration_5g', 1, null), '#0f766e',
                {yAxisIndex: 1, type: 'dashed', width: 2.2})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'fiveg', title: '5G 用户与渗透率', sub: '柱：5G 套餐口径／网络口径用户（百万户，两种口径不可接续）· 虚线：渗透率（%，右轴）',
            note: N.fiveg,
            detail: '<b>5G 时间线：</b>2019-06-06 工信部向移动、电信、联通、中国广电发放 5G 商用牌照；' +
                '2019-09 电信与联通共建共享 5G 接入网；2021-01 移动与中国广电签署 700MHz 共建共享协议。<br>' +
                '<b>渗透率与绝对值不能互推：</b>渗透率的分母（移动用户口径）在各家年报里也不完全一致，' +
                '用渗透率 × 用户数得到的绝对值属推算，本页一律不做。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 86, right: 76, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '百万户'}),
                Object.assign({}, AXIS_Y, {name: '%', splitLine: {show: false}})],
            series: marksOn(s, years, marks)
        });
    })();

    // ③ 宽带用户与宽带 ARPU（移动另有千兆与家庭综合 ARPU 两个口径）
    (function () {
        const years = opsYears(A, ['ops_broadband_users_mn', 'ops_bb_arpu', 'ops_gigabit_users_mn', 'ops_home_arpu']);
        if (!years.length) return;
        const s = [
            barSeries('有线宽带用户', seriesOf(A, years, 'ops_broadband_users_mn', 1, null), '#0891b2', {barMaxWidth: 42}),
            barSeries('千兆宽带用户', seriesOf(A, years, 'ops_gigabit_users_mn', 1, null), '#67e8f9', {barMaxWidth: 42}),
            lineSeries('宽带 ARPU（右轴）', seriesOf(A, years, 'ops_bb_arpu', 1, null), '#b45309', {yAxisIndex: 1, width: 2.4}),
            lineSeries('家庭客户综合 ARPU（右轴）', seriesOf(A, years, 'ops_home_arpu', 1, null), '#c0392b',
                {yAxisIndex: 1, type: 'dotted', width: 2.2})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'bb', title: '宽带用户与宽带 ARPU', sub: '柱：宽带用户（百万户）· 线：宽带 ARPU 与家庭综合 ARPU（元/户/月，右轴，不从 0 起画）',
            note: N.bb,
            detail: '<b>三家的宽带 ARPU 口径不同：</b>移动为纯有线宽带 ARPU（另有含增值的家庭客户综合 ARPU，2025 年 44.5 元）、' +
                '电信为宽带综合 ARPU（含天翼高清与智家应用）、联通为宽带用户接入 ARPU（仅接入）。' +
                '数据表里移动的两个口径分开存（<code>ops_bb_arpu</code> 与 <code>ops_home_arpu</code>），' +
                '前者 2024 年起停止披露。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 86, right: 86, top: 84, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '百万户'}),
                Object.assign({}, AXIS_Y, {name: '元/户/月', scale: true, splitLine: {show: false}})],
            series: s
        });
    })();

    // ④ 云与第二曲线收入（名字随公司变，取年报自己的叫法）
    (function () {
        const years = opsYears(A, ['ops_cloud_rev', 'ops_dx_rev']);
        if (!years.length) return;
        const nameOf = k => {
            for (let i = years.length - 1; i >= 0; i--) if (A[years[i]][k]) return A[years[i]][k];
            return null;
        };
        const cloudName = nameOf('ops_cloud_name') || '云业务', dxName = nameOf('ops_dx_name') || '第二曲线';
        const s = [
            barSeries(cloudName + '收入', seriesOf(A, years, 'ops_cloud_rev', 1, null), '#1d4ed8', {barMaxWidth: 42}),
            barSeries(dxName + '收入', seriesOf(A, years, 'ops_dx_rev', 1, null), '#f59e0b', {barMaxWidth: 42})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'cloud', title: '云与第二曲线收入', sub: '柱：' + cloudName + '／' + dxName + '（亿元，年报自身叫法）· 缺失年份为未披露绝对值',
            note: N.cloud,
            detail: '<b>三家的「第二曲线」不是同一个筐：</b>移动的数字化转型收入把个人新业务、智慧家庭、政企 DICT、' +
                '物联网、专线都算进去；电信的产业数字化收入以政企 IT 服务与天翼云为主；联通的算网数智收入 2023 年起才有。' +
                '范围差异大于经营差异，只看各自增速与占比。<br>' +
                '<b>缺失年份不补：</b>只披露同比或占比的年份留空，不用增速反推绝对值。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 0) + ' 亿元'},
            legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 86, right: 40, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '亿元'}), series: s
        });
    })();
    // ⑤ 年报口径资本开支 + 下一年度指引 + 折旧摊销
    (function () {
        const base = opsYears(A, ['ops_capex_yr', 'ops_depreciation']);
        if (!base.length) return;
        // 指引挂在被指引的那一年：末年披露「下一年度资本开支计划」时，横轴要多一格
        const guideYear = {};
        base.forEach(y => {
            const g = A[y].ops_capex_guide_next;
            if (g !== null && g !== undefined) guideYear[String(+y + 1)] = g;
        });
        const years = Array.from(new Set(base.concat(Object.keys(guideYear)))).sort();
        const s = [
            barSeries('资本开支（年报披露口径）', seriesOf(A, years, 'ops_capex_yr', 1, null), META.color, {barMaxWidth: 42}),
            barSeries('下一年度资本开支指引', years.map(y => guideYear[y] === undefined ? null : guideYear[y]),
                META.pre, {barMaxWidth: 42}),
            lineSeries('折旧及摊销', seriesOf(A, years, 'ops_depreciation', 1, null), '#111827', {width: 2.4})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'capex', title: '资本开支、下一年度指引与折旧摊销', sub: '柱：年报「当年完成资本开支」与年报给出的下一年度计划（亿元）· 线：折旧及摊销（亿元）',
            note: N.capex,
            detail: '<b>指引画在被指引的年份上：</b>浅色柱是上一年年报披露的下一年度资本开支计划，' +
                '与该年实际完成额不必相等（历年多为实际低于计划）。<br>' +
                '<b>与现金流量表口径的差别：</b>本图为年报按发生额披露的资本开支，' +
                '「业绩与财务」页的柱是现金流量表「购建固定资产、无形资产和其他长期资产支付的现金」，' +
                '两者因预算制、应付工程款账期与租赁处理不同而有出入，数据表里两套都保留。'
        }, undefined, charts);
        c.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 0) + ' 亿元'},
            legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 86, right: 40, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '亿元'}),
            series: marksOn(s, years, [{year: '2019', text: '5G 发牌'}, {year: '2015', text: '铁塔资产注入'}])
        });
    })();
}

function renderGaps(d) {
    const breaks = (d.ops_meta && d.ops_meta.breaks) || [];
    gaps.value.innerHTML = breaks.map(b => '<li>' + mdBold(b) + '</li>').join('') ||
        '<li>该公司在已录入的年报区间内未发生经营指标口径变更。</li>';
    gapSrc.value.innerHTML =
        (d.ops_meta ? mdBold(d.ops_meta.unit_note) + '　来源：' + d.ops_meta.source : '') +
        '　抓取脚本 <code>data/extract/fetch_telecom_reports.py</code>（上交所年报 PDF → txt），' +
        '经营层为原文通读后手工录入 <code>data/tables/telecom_ops_manual.json</code>。';
    secGaps.value.hidden = false;
}

function onResize() { charts.forEach(c => { try { c.resize() } catch (_) {} }); }

onMounted(async () => {
    prevBodyBg = document.body.style.background;
    document.body.style.background = '#f5f6f8';
    try {
        const d = await apiGet('/api/telecom_annual', { code: CODE });
        loading.value = false;
        renderHead(d);
        buildCharts(d);
        renderGaps(d);
        window.addEventListener('resize', onResize);
    } catch (e) {
        console.error('fetch error', e);
        loading.value = false;
        error.value = '数据加载失败：' + (e.message || String(e)) + '（请确认 app.py 已启动）';
    }
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', onResize);
    charts.forEach(c => { try { c.dispose() } catch (_) {} });
    charts = [];
    document.body.style.background = prevBodyBg;
});
</script>

<style scoped>
section > h2 { font-size: 22px; color: #1f2937; margin-bottom: 4px; border-left: 4px solid #10243e; padding-left: 10px; }
.wrap .note summary { cursor: pointer; color: #6b7280; font-weight: 500; list-style: none; }

section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 20px 22px; margin-top: 22px; scroll-margin-top: 116px; }

.entity { margin: 10px 0 0; padding: 12px 16px; background: #fff7ed; border-left: 4px solid #f59e0b; border-radius: 6px; font-size: 17px; color: #78350f; line-height: 1.7; }
.gap-list { margin: 6px 0 0 18px; font-size: 17px; color: #555; line-height: 1.8; }
</style>

<style>
.wrap .note summary { cursor: pointer; color: #6b7280; font-weight: 500; list-style: none; }
.wrap .note summary::-webkit-details-marker { display: none; }
.wrap .note summary::before { content: '▸ '; color: #9ca3af; }
.wrap .note[open] summary::before { content: '▾ '; }
.wrap .note summary:hover { color: #374151; }

</style>
