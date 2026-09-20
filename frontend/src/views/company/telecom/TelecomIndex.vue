<template>
  <div class="wrap">
    <div class="page-head">
      <h1 ref="pageTitle">业绩与财务</h1>
      <div class="meta" ref="pageMeta"></div>
      <div class="tags"><span>营收与利润</span><span>ROE 与毛利率</span><span>净现金</span><span>资本开支</span><span>人效</span><span>派息</span></div>
    </div>

    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">{{ error }}</div>

    <section id="sec-kpi" ref="secKpi" hidden>
      <h2 ref="kpiTitle">最新年度关键指标</h2>
      <p class="sub" ref="kpiSub"></p>
      <div class="kpis" ref="kpis"></div>
      <div class="entity" ref="entityNote"></div>
    </section>

    <div ref="chartsHost" id="charts"></div>

    <section id="sec-caliber" ref="secCaliber" hidden>
      <h2>数据来源与口径</h2>
      <p class="sub">财务层来自东方财富公司数据接口的 A 股年报合并数；经营层与收入构成层来自上交所年报原文</p>
      <div ref="caliber"></div>
    </section>
  </div>
</template>

<script setup>
import LoadingNote from '../../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { apiGet } from '../../../api'
import {
  getCode, getMeta, fmt, mdBold, seriesOf, yearsFor,
  lineSeries, barSeries, chartCard, AXIS_Y, axisX, marksOn,
} from './charts'

// 逐字搬自 dashboard/company/telecom/charts/perf.js（公共层 common.js 已抽到 ./charts）：
// 每个 ECharts option 与 renderHead/buildCharts/renderCaliber 逻辑原样保留（含分号），仅把
// document.getElementById 换成组件模板 ref、axios 换成统一 apiGet、echarts 实例收集进 charts。
const loading = ref(true)
const error = ref('')
const pageTitle = ref(null)
const pageMeta = ref(null)
const kpiTitle = ref(null)
const kpiSub = ref(null)
const kpis = ref(null)
const entityNote = ref(null)
const chartsHost = ref(null)
const caliber = ref(null)
const secKpi = ref(null)
const secCaliber = ref(null)

const CODE = getCode()
const META = getMeta(CODE)
let charts = []
let prevBodyBg = ''
const YUAN = 1e8;   // 元 → 亿元

function kpi(label, value, sub) {
    return '<div class="kpi"><div class="label">' + label + '</div>' +
        '<div class="value">' + value + '</div>' +
        (sub ? '<div class="delta" style="color:#7f8c8d">' + sub + '</div>' : '') + '</div>';
}

function renderHead(d) {
    const years = Object.keys(d.annual).filter(y => (d.annual[y].src || 'A') === 'A').sort();
    const last = years[years.length - 1];
    const rec = d.annual[last];
    document.title = d.name + '（' + d.secucode + '）· 业绩与财务';
    pageTitle.value.textContent = d.name + '（' + d.secucode + '）· 业绩与财务';
    pageMeta.value.innerHTML =
        'A 股年报合并数 · 金额为人民币亿元、比率为 % · A 股年报口径自 <b>' + d.a_report_from + '</b> 年度起<br>' +
        '同期 H 股代码 ' + d.h_code + (d.h_same_entity ? '（同一法人主体，A/H 同股同权）' :
            '（<b>不同法人主体</b>，红筹公司合并本公司，口径不可混比）');

    kpiTitle.value.textContent = last + ' 年度关键指标';
    kpiSub.value.textContent =
        '取 ' + last + ' 年年报合并数；净现金 = 货币资金 + 交易性金融资产 − 有息负债；派息按报告年度归集';
    const payout = (d.dividend_per10 || {})[last] && rec.total_share && rec.parent_netprofit
        ? (d.dividend_per10[last] / 10 * rec.total_share) / rec.parent_netprofit * 100 : null;
    kpis.value.innerHTML = [
        kpi('营业收入', fmt(rec.revenue / YUAN, 0) + ' 亿元', '服务收入 ' + (rec.ops_service_rev ? fmt(rec.ops_service_rev, 0) + ' 亿元' : '未单列')),
        kpi('归母净利润', fmt(rec.parent_netprofit / YUAN, 0) + ' 亿元', '扣非 ' + fmt(rec.deduct_parent_netprofit / YUAN, 0) + ' 亿元'),
        kpi('加权 ROE', fmt(rec.roe_weighted, 2) + ' %', '销售毛利率 ' + fmt(rec.gross_margin, 1) + ' %'),
        kpi('净现金', fmt(rec.net_cash / YUAN, 0) + ' 亿元', '有息负债 ' + fmt(rec.interest_debt / YUAN, 0) + ' 亿元'),
        kpi('资本开支强度', fmt(rec.capex_ratio, 1) + ' %', '年报口径资本开支 ' + (rec.ops_capex_yr ? fmt(rec.ops_capex_yr, 0) + ' 亿元' : '—')),
        kpi('每 10 股派现', fmt((d.dividend_per10 || {})[last], 3) + ' 元', payout ? '现算派息率 ' + fmt(payout, 1) + ' %' : '派息率待披露'),
        kpi('员工人数', fmt(rec.staff_num, 0) + ' 人', '人均营收 ' + fmt(rec.rev_per_staff, 0) + ' 万元'),
        kpi('重资产占比', fmt(rec.heavy_asset_ratio, 1) + ' %', '（固定资产＋在建工程）／总资产')
    ].join('');
    entityNote.value.innerHTML = '<b>主体口径：</b>' + mdBold(d.source);
    secKpi.value.hidden = false;
    return {years: Object.keys(d.annual).sort(), last: last};
}
/* 各家公司自己的历史事实注释：只写该主体年报／公告能核到的因果，不做跨公司比较 */
const NOTES = {
    '600941': {
        revprofit: '中国移动 2021-01 从纽交所退市、2022-01 回 A 上市，<b>本页 2021 年度起为 A 股年报口径</b>；' +
            '2021 年以前的行是接口按上市前披露回填的（且 2012—2017 年整段缺失、2011 年两个收入字段差一个量级），' +
            '只能看量级，不作精确同比。2025 年营业收入 10,501.87 亿元、归母净利润 1,370.95 亿元，已对上交所年报原文核验。',
        capex: '资本开支 2022 年 1,852 亿元见顶后连降三年至 2025 年 1,509 亿元，2026 年指引 1,366 亿元；' +
            '同期资本开支强度由 19.8% 降到 14.9%，是自由现金流改善的直接来源。',
        cash: '常年 2,500—4,400 亿元净现金，几乎不靠有息负债经营 —— 这是能连年提高派息率的底气，' +
            '也是低杠杆压低 ROE 的原因（权益乘数约 1.5 倍）。',
        dividend: '回 A 后派息率逐年抬升：每 10 股派现由 2021 年 20.939 元升到 2025 年 47.037 元。'
    },
    '601728': {
        revprofit: '中国电信 2021-08 回 A 上市，<b>2021 年度起为 A 股年报口径</b>，更早年份为接口回填（虚线／半透明柱）。' +
            '2025 年营业收入 5,239.2 亿元、归母净利润 331.8 亿元、加权 ROE 7.2%，已对上交所年报原文核验。' +
            '营收增速 2024 年起降到 1% 以内，增量几乎全部来自产业数字化。',
        capex: '资本开支 2023 年 988 亿元见顶、2025 年降至 804 亿元。2019-09 起与联通共建共享 5G 接入网，' +
            '是其单位覆盖投资长期低于中国移动的制度性原因。',
        cash: '有息负债与现金长期接近，净现金 2021 年前后由负转正、2025 年为 869 亿元 —— ' +
            '资产负债表修复与资本开支下行同步发生。',
        dividend: '2025 年度以现金分配的利润为股东应占利润的 <b>75%</b>（每股中期 0.1812 元＋末期 0.0908 元＝全年 0.2720 元）。'
    },
    '600050': {
        revprofit: '<b>2008 年归母 202.4 亿元不是经营性利润</b>：当年向中国电信出售 CDMA 网络及业务（总价 1,100 亿元）' +
            '产生处置收益，次年即回落到 31.4 亿元。2016 年 1.5 亿元、2017 年 4.3 亿元是全样本绝对低点，' +
            '对应 3G 制式劣势叠加 4G 建设滞后，也是 2017 年混改的直接背景。',
        capex: '资本开支 2015 年 1,338.8 亿元 → 2017 年 421.3 亿元（−68%），既有 4G 高峰过去，' +
            '也有 2015-10 铁塔资产注入后自建支出转为租费的口径因素；2025 年 541.5 亿元，' +
            '2026 年指引约 500 亿元且算力投资占比超 35%。',
        cash: '2012 年净现金 −1,236 亿元（4G 建设期靠借款），2019 年起转正 —— ' +
            '本页净现金口径比年报粗（一年内到期非流动负债含租赁负债等非有息项），只看方向与量级。',
        dividend: 'A 股上市最早，历年有 23 个年度的分红记录，但 2016—2017 年利润谷底期间派现几近归零。'
    }
};

function buildCharts(d) {
    const host = chartsHost.value;
    const A = d.annual, N = NOTES[CODE];
    // ① 营业收入与归母净利润：柱=营收（左轴），线=归母净利润（右轴），上市前段半透明／虚线
    (function () {
        const years = yearsFor(A, ['revenue', 'parent_netprofit']);
        const s = [
            barSeries('营业收入', seriesOf(A, years, 'revenue', YUAN, 'A'), META.color),
            barSeries('营业收入（上市前·回填）', seriesOf(A, years, 'revenue', YUAN, 'PRE'), META.pre),
            lineSeries('归母净利润', seriesOf(A, years, 'parent_netprofit', YUAN, 'A'), '#b45309', {yAxisIndex: 1}),
            lineSeries('归母净利润（上市前·回填）', seriesOf(A, years, 'parent_netprofit', YUAN, 'PRE'), '#fcd34d',
                {yAxisIndex: 1, type: 'dashed', width: 1.8})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'revprofit', title: '营业收入与归母净利润', sub: '柱：营业总收入（亿元，左轴）· 线：归母净利润（亿元，右轴）',
            note: N.revprofit,
            detail: '<b>2014-06-01 电信业营改增</b>（基础电信 11%、增值电信 6%）后营收由含税转不含税，2014 年前后不严格可比；' +
                '<b>2015-10 铁塔资产注入</b>后自建铁塔改为向中国铁塔租用，成本结构与折旧口径同时变化。'
        }, undefined, charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 84, right: 84, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '亿元'}),
                Object.assign({}, AXIS_Y, {name: '归母净利润 亿元', splitLine: {show: false}})],
            series: marksOn(s, years, [{year: '2014', text: '营改增'}, {year: d.a_report_from, text: 'A 股年报口径起点'}])
        });
    })();

    // ② 利润率与回报：三条比率线，窄幅指标不从 0 起画
    (function () {
        const years = yearsFor(A, ['gross_margin', 'net_margin', 'roe_weighted']);
        const s = [
            lineSeries('销售毛利率', seriesOf(A, years, 'gross_margin', 1, null), '#1d4ed8'),
            lineSeries('销售净利率', seriesOf(A, years, 'net_margin', 1, null), '#0f766e'),
            lineSeries('加权平均 ROE', seriesOf(A, years, 'roe_weighted', 1, null), '#c0392b')
        ];
        const c = chartCard(host, {
            id: 'margin', title: '毛利率、净利率与加权 ROE', sub: '接口口径（%）· 含上市前回填年份，故不分段',
            note: '运营商的利润率上限由折旧率与 ARPU 决定：收入端受提速降费与套餐分摊压制，' +
                '成本端的网络折旧却按年限刚性摊完，因此毛利率长期缓降。' +
                '低杠杆（净现金、权益乘数 1.4—1.9 倍）意味着几乎没有财务杠杆放大 ROE。',
            detail: '<b>为什么这张图不分 A／上市前两段：</b>比率字段在上市前回填年份里同样有值且量级正常，' +
                '分段会把一条本来连续的比率线切成两截；但加权 ROE 在移动、电信 2018 年前基本为空，' +
                '是该指标未回填，不是当年没有盈利。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 2) + ' %'},
            legend: {top: 0, itemGap: 16, textStyle: {fontSize: 15}},
            grid: {left: 80, right: 40, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '%', scale: true}), series: s
        });
    })();
    // ③ 现金与有息负债：净现金行业的资产负债表特征
    (function () {
        const years = yearsFor(A, ['cash_like', 'interest_debt', 'net_cash']);
        const s = [
            barSeries('货币资金＋交易性金融资产', seriesOf(A, years, 'cash_like', YUAN, null), '#60a5fa'),
            barSeries('有息负债', seriesOf(A, years, 'interest_debt', YUAN, null), '#f59e0b'),
            lineSeries('净现金', seriesOf(A, years, 'net_cash', YUAN, null), '#111827', {width: 2.4})
        ];
        const c = chartCard(host, {
            id: 'cash', title: '现金、有息负债与净现金', sub: '柱：现金类资产与有息负债（亿元）· 线：净现金 = 前者 − 后者',
            note: N.cash,
            detail: '<b>有息负债口径：</b>短期借款＋一年内到期非流动负债＋应付短期债券＋长期借款＋应付债券，' +
                '比年报口径粗；<b>租赁负债不计入</b>，2019 年起新租赁准则把铁塔／站址租赁计入使用权资产与租赁负债，' +
                '若计入则净现金会明显下降。货币资金亦含受限资金。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 0) + ' 亿元'},
            legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 90, right: 40, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: Object.assign({}, AXIS_Y, {name: '亿元'}), series: s
        });
    })();

    // ④ 资本开支与自由现金流：财务口径（现金流量表）+ 年报披露口径叠在同一张图
    (function () {
        const years = yearsFor(A, ['construct_long_asset', 'fcf_proxy', 'capex_ratio', 'ops_capex_yr']);
        const s = [
            barSeries('购建长期资产支付的现金', seriesOf(A, years, 'construct_long_asset', YUAN, null), '#94a3b8'),
            barSeries('自由现金流（经营净现金 − 购建长期资产现金）', seriesOf(A, years, 'fcf_proxy', YUAN, null), '#34d399'),
            lineSeries('年报披露口径资本开支', seriesOf(A, years, 'ops_capex_yr', 1, null), META.color, {width: 2.4}),
            lineSeries('资本开支强度（右轴）', seriesOf(A, years, 'capex_ratio', 1, null), '#c0392b', {yAxisIndex: 1, type: 'dashed'})
        ].filter(x => x.data.some(v => v !== null));
        const c = chartCard(host, {
            id: 'capex', title: '资本开支、自由现金流与开支强度', sub: '柱：现金流量表口径（亿元）· 实线：年报披露口径资本开支（亿元）· 虚线：资本开支／营业收入（%，右轴）',
            note: N.capex,
            detail: '<b>两套资本开支口径为什么不重合：</b>实线是年报按发生额披露的「当年完成资本开支」，' +
                '柱是现金流量表「购建固定资产、无形资产和其他长期资产支付的现金」—— 预算制、应付工程款账期与租赁处理' +
                '都会造成差额，数据表里两套都保留（<code>ops_capex_yr</code> 与 <code>construct_long_asset</code>）。' +
                '年报口径只覆盖有原文录入的年份（移动／电信 2021 年起、联通 2015 年起）。'
        }, undefined, charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 90, right: 76, top: 84, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '亿元'}),
                Object.assign({}, AXIS_Y, {name: '%', splitLine: {show: false}})],
            series: marksOn(s, years, [{year: '2019', text: '5G 发牌'}])
        });
    })();
    // ⑤ 员工与人效
    (function () {
        const years = yearsFor(A, ['staff_num', 'rev_per_staff']);
        const s = [
            barSeries('年末员工人数', seriesOf(A, years, 'staff_num', 1, null), '#a5b4fc'),
            lineSeries('人均营收（右轴）', seriesOf(A, years, 'rev_per_staff', 1, null), '#1d4ed8', {yAxisIndex: 1}),
            lineSeries('人均归母净利润（右轴）', seriesOf(A, years, 'np_per_staff', 1, null), '#c0392b', {yAxisIndex: 1})
        ];
        const c = chartCard(host, {
            id: 'staff', title: '员工人数与人均产出', sub: '柱：员工人数（人）· 线：人均营收／人均归母净利润（万元/人，右轴）',
            note: '员工规模十年基本持平而收入翻倍 —— <b>人效提升几乎全部来自收入端，不是减员</b>。' +
                (CODE === '600050' ? '联通 2008 年员工由 4.8 万跳到 20.4 万，是与网通合并并表所致。' : ''),
            detail: '<b>口径提醒：</b>员工数为接口快照、含全部子公司（移动含咪咕、中移金科；电信含天翼云科技；' +
                '联通含智网创新等），与「通信主业员工」不是一回事；外包与代理渠道人员不计入，' +
                '因此人均指标只适合看自身趋势。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 92, right: 76, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '人'}),
                Object.assign({}, AXIS_Y, {name: '万元/人', splitLine: {show: false}})],
            series: s
        });
    })();

    // ⑥ 派息：每 10 股派现（柱）+ 用股本与归母净利润现算的派息率（线）
    (function () {
        const div = d.dividend_per10 || {};
        // 财务层与分红表的年份要去重后再排序：直接 concat 会让同一年在横轴上出现两格
        const all = Array.from(new Set(Object.keys(A).concat(Object.keys(div)))).sort();
        const has = all.map(y => div[y] !== undefined);
        const from = has.indexOf(true), to = has.lastIndexOf(true);
        const years = from < 0 ? all : all.slice(from, to + 1);
        const payout = years.map(y => {
            const rec = A[y];
            if (!rec || div[y] === undefined || !rec.total_share || !rec.parent_netprofit) return null;
            return +((div[y] / 10 * rec.total_share) / rec.parent_netprofit * 100).toFixed(2);
        });
        const s = [
            barSeries('每 10 股派现（含税）', years.map(y => div[y] === undefined ? null : div[y]), '#c9a24a'),
            lineSeries('现算派息率（右轴）', payout, '#0f766e', {yAxisIndex: 1})
        ];
        const c = chartCard(host, {
            id: 'dividend', title: '每 10 股派现与派息率',
            sub: '柱：按报告年度归集的每 10 股派现（元，含中期与末期）· 线：每股派现 × 总股本 ÷ 归母净利润（%，右轴）',
            note: N.dividend,
            detail: '<b>派息率是现算值：</b>用当年总股本 × 每股派现 ÷ 当年归母净利润，与年报按「股东应占利润的 x%」' +
                '披露的口径会有小差（股本变动、A/H 分派时点、中期分红归属年度）。<br>' +
                '<b>不要用每 10 股派现横比三家：</b>股本与股价不同，只有派息率或股息率可比。'
        }, '55vh', charts);
        c.setOption({
            tooltip: {trigger: 'axis'}, legend: {top: 0, itemGap: 14, textStyle: {fontSize: 15}},
            grid: {left: 84, right: 76, top: 62, bottom: 40}, xAxis: axisX(years),
            yAxis: [Object.assign({}, AXIS_Y, {name: '元/10股'}),
                Object.assign({}, AXIS_Y, {name: '%', splitLine: {show: false}})],
            series: s
        });
    })();
}

function renderCaliber(d) {
    caliber.value.innerHTML =
        '<div class="note" style="max-width:none;color:#4b5563;font-size:17px">' +
        '<div><b>财务层：</b>' + mdBold(d.caliber_note) + '</div>' +
        '<div style="margin-top:6px">' + mdBold(d.unit_note) + '　来源：' + mdBold(d.source) + '</div>' +
        (d.ops_meta ? '<div style="margin-top:6px"><b>经营层：</b>' + mdBold(d.ops_meta.caliber_note) +
            '　来源：' + (d.ops_meta.source || '') + '</div>' : '') +
        (d.segments ? '<div style="margin-top:6px"><b>收入构成层：</b>' + mdBold(d.segments.caliber_note) +
            '　来源：' + (d.segments.source || '') + '</div>' : '') +
        '<div style="margin-top:6px"><b>抓取脚本：</b><code>data/extract/fetch_telecom_financials.py</code>（财务层）、' +
        '<code>data/extract/fetch_telecom_reports.py</code>（上交所年报 PDF）、' +
        '<code>data/extract/extract_telecom_segments.py</code>（收入构成），' +
        '接口 <code>/api/telecom_annual?code=' + CODE + '</code>。</div></div>';
    secCaliber.value.hidden = false;
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
        renderCaliber(d);
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
</style>

<style>
.wrap .note summary { cursor: pointer; color: #6b7280; font-weight: 500; list-style: none; }
.wrap .note summary::-webkit-details-marker { display: none; }
.wrap .note summary::before { content: '▸ '; color: #9ca3af; }
.wrap .note[open] summary::before { content: '▾ '; }
.wrap .note summary:hover { color: #374151; }

.wrap details.note-more > summary { list-style: revert; }
</style>
