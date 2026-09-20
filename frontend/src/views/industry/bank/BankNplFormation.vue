<template>
  <div class="page bank-npl-formation">
    <h1>上市银行息差与不良生成横向对比</h1>
    <div class="lede">
      44 家已建数据页的 A/H 股上市银行 · <b>净息差 NIM／净利差 NIS</b>（利息业务盈利厚度）与<b>不良生成率</b>（新增不良速度）两组风控核心指标横向对比<br>
      先选指标、再选机构类型；息差为年报披露值，不良生成率依赖 IFRS9 后的「信用减值损失」科目、各行统一自 2018 年起可比。按机构类型分色，点按按钮可只看某一类
    </div>

    <div class="toolbar metricbar" ref="metricbarEl"></div>
    <div class="toolbar" ref="toolbarEl"></div>

    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">数据加载失败：{{ error }}（请确认后端服务已启动）</div>
    <div class="chart-card" v-show="ready">
      <div class="chart-box" ref="chartEl"></div>
      <div class="note" ref="noteEl"></div>
    </div>
  </div>
</template>

<script setup>
import LoadingNote from '../../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../../api'
import { useChartPool } from '../../../composables/useCharts'

// 逐字搬自 dashboard/industry/bank/npl-formation.js：数据（TIERS / METRICS）、序列构建、
// tooltip / legend / grid / xAxis / yAxis 与 note 文案原样保留；仅把取数改走统一 apiGet、
// 容器改用组件模板 ref、resize / dispose 归拢到组件生命周期。图与数据一律不变。
const API = '/api/bank_npl_formation'

const loading = ref(true)
const error = ref('')
const ready = ref(false)
const metricbarEl = ref(null)
const toolbarEl = ref(null)
const chartEl = ref(null)
const noteEl = ref(null)
const { charts } = useChartPool()

// 机构类型展示顺序与基准色（全部视图按类型着色，看聚簇）
const TIERS = [
    { key: '国有大行', color: '#c0392b' },
    { key: '股份行',   color: '#1f6feb' },
    { key: '城商行',   color: '#0f766e' },
    { key: '农商行',   color: '#b45309' }
];
const TIER_COLOR = Object.fromEntries(TIERS.map(t => [t.key, t.color]));

// 三个指标：各自的取值序列 / 年份轴字段 / 纵轴名 / tooltip 排序方向 / 页脚口径说明
const METRICS = {
    formation: {
        label: '不良生成率', axisName: '不良生成率%', yearsKey: 'years', valKey: 'formation',
        desc: true,   // 悬停时降序排名（越高越差）
        note: () =>
            `<b>口径：</b>不良生成率 = 不良生成额 ÷ 期初贷款总额，不良生成额 = 期末不良余额 − 期初不良余额 + 当期核销净额。` +
            `依赖利润表「信用减值损失」科目，2018 年 IFRS9 切换后才普遍出现，各行统一自 2018 年起可比。悬停任一年份即按当年不良生成率<b>降序排名</b>（越高越差）。` +
            `<details class="note-more"><summary>展开：口径偏差与已知陷阱</summary><div>` +
            `本指标为脚本自「信用减值损失」全口径倒推的<b>趋势近似量</b>，非年报附注原值，存在两处系统性偏差：` +
            `一是脚本用全口径信用减值损失（含金融投资、表外等）而非「发放贷款和垫款」单项计提，实测偏差约 −0.18pp ~ +0.58pp（个别行更大）；` +
            `二是 2018/2019 首个执行年的期初准备倒推未计 IFRS9 首日重述，恰好可能污染 2018 这个基准年。` +
            `因此跨行横比只看<b>量级与方向</b>，不宜比小数点后的高下；需精确值请回各行年报附注手工取。` +
            `个别行某些年份为负值（如核销力度大于新生成、或收回核销贷款），属正常现象。` +
            `明细见 <code>data/tables/data_sources.txt</code> 口径注意 (6)(7)。各行详情见其「风控」页。` +
            `</div></details>`
    },
    nim: {
        label: '净息差 NIM', axisName: '净息差%', yearsKey: 'nimYears', valKey: 'nim',
        desc: false,  // 悬停时升序排名（越低越承压）
        note: () =>
            `<b>口径：</b>净息差 NIM = 净利息收入 ÷ 生息资产平均余额，本集团合并数、年报披露值，单位 %。` +
            `是利息业务的最终盈利厚度。2012 前后见顶后单边下行，利率市场化 + 让利实体 + 资产端收益率下行共同压缩。悬停任一年份即按当年净息差<b>升序排名</b>（越低越承压）。` +
            `<details class="note-more"><summary>展开：口径说明</summary><div>` +
            `个别行早年（如招行 2016）年报口径调整年份缺披露，图中断点为真实缺口，非补零。` +
            `净息差含免税国债等的税收因素，跨行绝对值可比性略弱于净利差；看趋势与量级即可。` +
            `与净利差 NIS 的差异来自生息资产与计息负债的规模错配（活期存款、免息资金越多，NIM 相对 NIS 越高）。各行详情见其「风控」页利率风险。` +
            `</div></details>`
    },
    nis: {
        label: '净利差 NIS', axisName: '净利差%', yearsKey: 'nimYears', valKey: 'nis',
        desc: false,
        note: () =>
            `<b>口径：</b>净利差 NIS = 生息资产平均收益率 − 计息负债平均成本率，本集团合并数、年报披露值，单位 %。` +
            `剔除了资产负债规模错配，是两端定价能力的纯差值，跨行可比性优于净息差。悬停任一年份即按当年净利差<b>升序排名</b>（越低越承压）。` +
            `<details class="note-more"><summary>展开：口径说明</summary><div>` +
            `净利差通常略低于净息差；二者之差反映活期/免息资金对息差的加成。` +
            `资产端收益率下行快于负债端成本率下行时净利差收窄，是近年息差承压的核心。各行详情见其「风控」页利率风险。` +
            `</div></details>`
    }
};

// 单一类型视图里每行一个可区分的颜色：在色轮上均匀取 N 个色相
function spread(n) {
    const out = [];
    for (let i = 0; i < n; i++) {
        const h = Math.round((360 * i) / Math.max(1, n));
        out.push(`hsl(${h}, 62%, 46%)`);
    }
    return out;
}

function fmt(v) {
    return (v === null || v === undefined) ? '—' : v.toFixed(2) + '%';
}

let BANKS = [];       // [{code,name,tier,years,formation,nimYears,nim,nis}]
let YEARS = [];       // 当前指标下的年份并集（升序，仅保留有任一行披露的年份）
let METRIC = 'formation';
let TIER = 'all';

function buildYears(metric) {
    const m = METRICS[metric];
    const set = new Set();
    for (const b of BANKS) {
        const yrs = b[m.yearsKey] || [], vals = b[m.valKey] || [];
        yrs.forEach((y, i) => {
            if (vals[i] !== null && vals[i] !== undefined) set.add(y);
        });
    }
    YEARS = Array.from(set).sort();
}

// 把某行某指标的序列重排到 YEARS 轴上（按年份对齐，缺年补 null）
function alignTo(bank, metric) {
    const m = METRICS[metric];
    const yrs = bank[m.yearsKey] || [], vals = bank[m.valKey] || [];
    const map = {};
    yrs.forEach((y, i) => { map[y] = vals[i]; });
    return YEARS.map(y => {
        const v = map[y];
        return (v === null || v === undefined) ? null : v;
    });
}

// 某指标下确有数据的行（整条为 null 的不进图，避免全部视图里挂一堆空 series）
function banksWithData(metric) {
    const m = METRICS[metric];
    return BANKS.filter(b => (b[m.valKey] || []).some(v => v !== null && v !== undefined));
}

function render() {
    const metric = METRIC, m = METRICS[metric];
    const pool = banksWithData(metric);
    const shown = TIER === 'all' ? pool : pool.filter(b => b.tier === TIER);
    const single = TIER !== 'all';
    const palette = single ? spread(shown.length) : null;

    const series = shown.map((b, i) => {
        const color = single ? palette[i] : (TIER_COLOR[b.tier] || '#6b7280');
        return {
            name: b.name,
            type: 'line',
            smooth: true,
            connectNulls: true,
            symbol: 'circle',
            symbolSize: single ? 6 : 4,
            data: alignTo(b, metric),
            lineStyle: { width: single ? 2.6 : 1.8, color: color, opacity: single ? 1 : 0.72 },
            itemStyle: { color: color },
            emphasis: { focus: 'series', lineStyle: { width: 4 } },
            // 行数少时右端贴行名；全部视图行太多，端点标签会糊成一团，改由排序 tooltip 辨识
            endLabel: single
                ? { show: true, formatter: '{a}', fontSize: 14, color: color, distance: 4 }
                : { show: false }
        };
    });

    // 单一 #chart 容器：复用同一 echarts 实例（收集入 charts 供 onBeforeUnmount dispose）
    const el = chartEl.value;
    const chart = echarts.getInstanceByDom(el) || echarts.init(el);
    if (!charts.includes(chart)) charts.push(chart);
    chart.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 15 },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'line' },
            // 悬停某一年即得当年全部在图行的排名，一眼看谁高谁低（不良降序、息差升序）
            formatter: function (ps) {
                const rows = ps.filter(p => p.value !== null && p.value !== undefined)
                    .sort((a, b) => m.desc ? b.value - a.value : a.value - b.value)
                    .map((p, i) => `${i + 1}. ${p.marker}${p.seriesName}　<b>${fmt(p.value)}</b>`);
                const dir = m.desc ? '降序' : '升序';
                return `<b>${ps[0].axisValue} 年 · ${m.label}</b>（${dir}）<br>` + (rows.length ? rows.join('<br>') : '无数据');
            }
        },
        legend: single
            ? { type: 'scroll', top: 0, itemGap: 16, textStyle: { fontSize: 14 }, data: series.map(s => s.name) }
            : { show: false },
        grid: { left: 56, right: single ? 120 : 60, top: single ? 42 : 16, bottom: 40 },
        xAxis: {
            type: 'category', data: YEARS, boundaryGap: false,
            axisLabel: { fontSize: 14, color: '#555' },
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value', name: m.axisName,
            nameTextStyle: { fontSize: 14 },
            axisLabel: { fontSize: 14, formatter: '{value}%' },
            splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
        },
        series: series
    }, { notMerge: true });

    const noteElm = noteEl.value;
    const legendTip = single
        ? '右端标签为行名，点击上方图例可临时隐藏个别行。'
        : '各行按机构类型着色（<b style="color:#c0392b">国有大行</b>／<b style="color:#1f6feb">股份行</b>／<b style="color:#0f766e">城商行</b>／<b style="color:#b45309">农商行</b>），点按上方类型按钮可只看某一类并显示行名。';
    noteElm.innerHTML = m.note() + `<br>${legendTip}`;
}

// 上排：指标切换
function buildMetricBar() {
    const bar = metricbarEl.value;
    bar.innerHTML = '';
    Object.keys(METRICS).forEach((key, i) => {
        const el = document.createElement('button');
        el.textContent = METRICS[key].label;
        if (key === METRIC) el.classList.add('active');
        el.addEventListener('click', () => {
            if (key === METRIC) return;
            METRIC = key;
            bar.querySelectorAll('button').forEach(x => x.classList.remove('active'));
            el.classList.add('active');
            buildYears(METRIC);
            buildTierBar();      // 各指标可用行数不同，类型按钮计数随之刷新
            render();
        });
        bar.appendChild(el);
    });
}

// 下排：机构类型筛选（计数按当前指标确有数据的行来算）
function buildTierBar() {
    const bar = toolbarEl.value;
    const pool = banksWithData(METRIC);
    const counts = {};
    for (const b of pool) counts[b.tier] = (counts[b.tier] || 0) + 1;
    // 切换指标后若原类型在新指标下已无行，回落到「全部」
    if (TIER !== 'all' && !counts[TIER]) TIER = 'all';
    const btns = [{ key: 'all', label: `全部 ${pool.length} 家` }]
        .concat(TIERS.filter(t => counts[t.key]).map(t => ({ key: t.key, label: `${t.key} ${counts[t.key]} 家` })));
    bar.innerHTML = '';
    btns.forEach(b => {
        const el = document.createElement('button');
        el.textContent = b.label;
        if (b.key === TIER) el.classList.add('active');
        el.addEventListener('click', () => {
            TIER = b.key;
            bar.querySelectorAll('button').forEach(x => x.classList.remove('active'));
            el.classList.add('active');
            render();
        });
        bar.appendChild(el);
    });
}

onMounted(async () => {
    try {
        // 源页 axios.get(API) → 统一 apiGet：非 200 抛错，成功直接拿解包后的 data（银行数组）
        const data = await apiGet(API);
        BANKS = data || [];
        if (!BANKS.length) throw new Error('无银行数据');
        // 类型内按 BANK_ORDER 已定顺序（后端返回顺序）保留，类型间按 TIERS 顺序聚拢，聚簇更清晰
        const rank = Object.fromEntries(TIERS.map((t, i) => [t.key, i]));
        BANKS.sort((a, b) => (rank[a.tier] ?? 9) - (rank[b.tier] ?? 9));
        buildYears(METRIC);
        loading.value = false;
        ready.value = true;
        await nextTick();       // 等 v-show 展开图卡再 init，容器才有正确尺寸
        buildMetricBar();
        buildTierBar();
        render();
    } catch (e) {
        console.error('fetch error', e);
        loading.value = false;
        error.value = e.message || String(e);
    }
});

onBeforeUnmount(() => {
    charts.forEach(c => { try { c.dispose() } catch (_) {} });
    charts = [];
});
</script>

<style scoped>
/* 逐字搬自源页 <style> 中静态模板节点依赖的规则。* 重置、body、.chart-card 的白底、
   .chart-title 复用已全局引入的 common/base.css，不再重复；#loading / #error-msg 本页有
   自定义配色/间距，需覆盖 base.css（scoped 的 [data-v] 使特异性高于 base.css 的裸选择器）。
   本块只作用于模板里的静态节点；动态生成的按钮与 note 富文本见下方非 scoped 块。 */
.page { max-width: 1500px; margin: 0 auto; padding: 20px 16px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin: 12px 0 6px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 16px; }
.lede b { color: #b45309; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 14px; }
/* 指标切换排：更醒目一档，与下方类型筛选区分开 */
.metricbar { margin-bottom: 8px; }
/* .chart-card 白底/圆角/投影在 base.css，本页覆盖为更薄一档（8px 圆角 + 更淡投影）并补内边距/下边距 */
.chart-card { padding: 16px 18px 22px; margin-bottom: 22px; background: #fff;
              border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.chart-box { height: 78vh; min-height: 520px; }
.note { font-size: 16px; color: #6b7280; line-height: 1.7; margin-top: 10px; }
#loading, #error-msg { text-align: center; color: #6b7280; font-size: 17px; padding: 40px 0; }
#error-msg { display: none; color: #b91c1c; }
</style>

<style>
/* 以下针对 onMounted 里 document.createElement 动态注入的按钮，以及 note 用 innerHTML 写入的
   富文本（b / details / summary / code / a）。动态节点拿不到 scoped 的 data-v 属性，规则必须放
   非 scoped 块；为避免泄漏到其它页面，全部限定在组件根类 .bank-npl-formation 之下。逐字搬自源页 <style>。 */
.bank-npl-formation .toolbar button {
    border: 1px solid #cbd5e1; background: #fff; color: #374151;
    font-size: 15px; padding: 5px 14px; border-radius: 16px; cursor: pointer;
    transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.bank-npl-formation .toolbar button:hover { border-color: #94a3b8; }
.bank-npl-formation .toolbar button.active { background: #1f2937; color: #fff; border-color: #1f2937; }
.bank-npl-formation .metricbar button { font-size: 16px; padding: 6px 18px; border-color: #94a3b8; }
.bank-npl-formation .metricbar button.active { background: #b45309; border-color: #b45309; }
.bank-npl-formation .note b { color: #b45309; }
.bank-npl-formation details.note-more { margin-top: 6px; }
.bank-npl-formation details.note-more > summary { cursor: pointer; color: #1d4ed8; font-size: 15px; }
.bank-npl-formation details.note-more > div { margin-top: 6px; padding-left: 10px; border-left: 3px solid #e5e7eb; }
.bank-npl-formation a { color: #1d4ed8; }
</style>
