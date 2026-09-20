<template>
  <div class="page">
    <h1>A/H 股上市保险公司概览</h1>
    <div class="lede">按 A+H 综合保险集团 / 仅港股中资险企 / 港股外资险企 分组，附保险业重要变革时间线</div>
    <div class="legend">
      <span><span class="code a">601xxx</span> A 股代码</span>
      <span><span class="code h">xxxx.HK</span> 港股代码</span>
      <span style="color:#d97706;">橙色边框 = 已有同业对比数据</span>
    </div>

    <h2>A+H 上市保险集团 <span class="count">5 家 · 均已抓取 A 股年报口径历年数据</span></h2>
    <div class="grid" ref="gridAh"></div>

    <h2>仅港股上市的中资险企 <span class="count">5 家 · 无 A 股主体，暂未取数</span></h2>
    <div class="grid" ref="gridHk"></div>

    <h2>港股上市的外资／泛亚险企 <span class="count">2 家 · 报表为 IFRS／美元或港元口径</span></h2>
    <div class="grid" ref="gridForeign"></div>

    <h2>保险业重要变革时间线 <span class="count">2016–2025 · 会计准则、偿付能力与产品监管</span></h2>
    <div class="timeline" ref="timelineEl"></div>
    <div class="note">
      时间线中的<b>会计准则与偿付能力口径切换</b>已由本项目抓取的历年数据交叉验证（如金融资产三分类字段：中国平安自 2018 年起有值，
      国寿／太保／新华／人保自 2023–2024 年起才有值；退保金、赔付支出、提取保险责任准备金三项在 2022/2023 年后整体断供）；
      产品与渠道监管条目为监管公开规则，未逐条回溯年报原文。历年数值见
      <a href="peers.html">五大险企同业对比</a>。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { renderTimeline } from '../../../utils/format'

// 逐字搬自 dashboard/industry/insurance/overview.html 的内联脚本：数据（INSURERS/
// DETAIL_PAGES/EVENTS）与渲染逻辑原样保留，仅把 document.getElementById 换成组件模板 ref。
// 纯名录 + 时间线页，无 ECharts、无 /api 请求，全部内联数据；无异步故无 loading/error。
// site-header.js 由 App.vue 的 SiteHeader 组件全局提供，不并入本页。
const gridAh = ref(null)
const gridHk = ref(null)
const gridForeign = ref(null)
const timelineEl = ref(null)

/* 每家险企：name 简称，a A股代码（可空），h 港股代码（可空），note 备注（可空） */
const INSURERS = {
    ah: [
        {name: '中国平安', a: '601318', h: '2318.HK'},
        {name: '中国人寿', a: '601628', h: '2628.HK'},
        {name: '中国太保', a: '601601', h: '2601.HK'},
        {name: '新华保险', a: '601336', h: '1336.HK'},
        {name: '中国人保', a: '601319', h: '1339.HK'}
    ],
    hk: [
        {name: '中国太平', a: null, h: '0966.HK'},
        {name: '中国财险', a: null, h: '2328.HK'},
        {name: '中国再保险', a: null, h: '1508.HK'},
        {name: '众安在线', a: null, h: '6060.HK'},
        {name: '阳光保险', a: null, h: '6963.HK'}
    ],
    foreign: [
        {name: '友邦保险', a: null, h: '1299.HK'},
        {name: '保诚', a: null, h: '2378.HK'}
    ]
};

/* 已抓取数据的险企：代码 → 同业对比页（按代码高亮该家） */
const DETAIL_PAGES = {
    '601318': 'peers.html?focus=601318',
    '601628': 'peers.html?focus=601628',
    '601601': 'peers.html?focus=601601',
    '601336': 'peers.html?focus=601336',
    '601319': 'peers.html?focus=601319'
};

function render(grid, list) {
    if (!grid) return;
    for (const it of list) {
        const hasData = it.a && DETAIL_PAGES[it.a];
        const card = document.createElement(hasData ? 'a' : 'div');
        card.className = 'b-card' + (hasData ? ' has-data' : ' static');
        if (hasData) card.href = DETAIL_PAGES[it.a];

        const name = document.createElement('span');
        name.className = 'name';
        name.textContent = it.name;

        const codes = document.createElement('span');
        codes.className = 'codes';
        if (it.a) {
            const c = document.createElement('span');
            c.className = 'code a';
            c.textContent = it.a;
            codes.appendChild(c);
        }
        if (it.h) {
            const c = document.createElement('span');
            c.className = 'code h';
            c.textContent = it.h;
            codes.appendChild(c);
        }
        if (!it.a && !it.h) {
            const c = document.createElement('span');
            c.className = 'code none';
            c.textContent = '未上市';
            codes.appendChild(c);
        }

        card.appendChild(name);
        card.appendChild(codes);
        grid.appendChild(card);
    }
}

/* 色彩语义与银行页一致：会计准则/口径变更 = 蓝 #0369a1 · 产品与渠道监管新规 = 紫 #6c3483 · 长期趋势性变革 = 灰绿 #0f766e */
const EVENTS = [
    {
        time: '2016.1.1',
        name: '偿二代（C-ROSS）正式实施',
        color: '#0369a1',
        desc: '偿付能力监管由规模导向的偿一代切换为风险导向的偿二代，分子（实际资本）与分母（最低资本）计算规则全部重写。本项目抓取的「偿付能力充足率」序列因此在 2016 年前后不可比：偿一代下各家常见数百个百分点，偿二代下综合偿付能力充足率回落至 200%–300% 区间。'
    },
    {
        time: '2017.10',
        name: '人身险产品设计负面清单（134 号文）',
        color: '#6c3483',
        desc: '中短存续期、快速返还型年金与附加万能账户被限制，销售端从「高现价理财型」向长期保障型切换。对应保费规模在 2017–2018 年出现明显增速换挡，是新业务价值（NBV）与保费增速脱钩的起点之一。'
    },
    {
        time: '2018.1.1',
        name: 'IFRS9 先行：中国平安单家切换金融资产三分类',
        color: '#0369a1',
        desc: '中国平安自 2018 年 1 月 1 日起执行新金融工具准则，金融资产由「可供出售 / 持有至到期」四分类改为债权投资 / 其他债权投资 / 其他权益工具投资三分类；本项目数据可直接看到该切换：平安的 available_sale_finasset、hold_maturity_invest 两字段只到 2017 年，creditor_invest 等新字段自 2018 年起有值，而国寿、太保、新华、人保的旧口径字段一直延续到 2022–2023 年。'
    },
    {
        time: '2020.9',
        name: '车险综合改革',
        color: '#6c3483',
        desc: '交强险责任限额提高、商车险附加费用率上限由 35% 降至 25%，财险保费单均下降、赔付率上升而费用率下降。主要影响以财险为主的中国人保，其保费与承保利润结构在 2020–2021 年出现台阶。'
    },
    {
        time: '2021.2.1',
        name: '重疾定义修订与新发生率表切换',
        color: '#6c3483',
        desc: '重疾险疾病定义与发生率表同步更新，旧定义产品在 2021 年 1 月底集中停售，形成 2020Q4–2021Q1 的销售脉冲与随后的透支效应；寿险公司 NBV 增速在 2021 年普遍转负。'
    },
    {
        time: '2022.1.1',
        name: '偿二代二期工程实施',
        color: '#0369a1',
        desc: '二期规则收紧实际资本认定（长期股权投资、保单未来盈余分级计入核心资本等），各家核心／综合偿付能力充足率在 2022 年整体下移。因此「偿付能力充足率」序列存在偿一代（≤2015）、偿二代一期（2016–2021）、二期（2022 起）三段口径，跨段比较无意义。'
    },
    {
        time: '2023.1.1',
        name: 'IFRS17 + IFRS9 全面实施（新保险合同准则）',
        color: '#0369a1',
        desc: '保费收入改按「保险服务收入」列示，投资成分不再计入收入；退保金、赔付支出、提取保险责任准备金、手续费及佣金支出等传统科目在利润表中取消，负债端改按保险合同负债（BBA/VFA/PAA）计量，2022 年作为可比期被重述。本项目数据表现为：compensate_expense、surrender_value、extract_insurance_reserve 等字段在 2022（或 2023）年之后整体为空，营业收入与净利润前后可比性下降、利润波动放大。'
    },
    {
        time: '2023.8',
        name: '预定利率下调启动 + 银保渠道「报行合一」',
        color: '#6c3483',
        desc: '普通型人身险预定利率上限由 3.5% 降至 3.0%（2023 年 7 月底旧产品停售），同期银保渠道推行「报行合一」压降手续费；2024 年 9 月普通型进一步降至 2.5%、10 月分红型降至 2.0%，2025 年 9 月起再降至 2.0%／1.75%。停售脉冲推高当期保费、压低次期基数，是近三年保费与 NBV 波动的主要外生因素。'
    },
    {
        time: '2019–2025',
        name: '个险代理人渠道长期收缩',
        color: '#0f766e',
        desc: '寿险个人代理人规模自 2019 年前后见顶后连续多年下降（行业口径由高峰约 900 万人降至 300 万人以下），各家转向「绩优＋银保」双轮驱动。该变革不体现为单一年份事件，但与保费增速换挡、NBV 率回升（人均产能提升）同期发生；本项目数据中的员工人数（staff_num，含内勤，不含代理人）不能直接度量该趋势。'
    },
    {
        time: '长期口径提示',
        name: '中国平安合并平安银行，总资产／ROA 不可直接横比',
        color: '#0f766e',
        desc: '中国平安资产负债表含吸收存款（accept_deposit）与发放贷款及垫款（loan_advance）等银行科目，2025 年末分别约 3.59 万亿元与 3.41 万亿元，占集团 13.9 万亿元总资产的一半以上。因此平安的总资产、ROA、权益乘数与四家纯保险主体不同质，同业对比页对总资产类图表已单独标注。'
    }
];

onMounted(() => {
    render(gridAh.value, INSURERS.ah);
    render(gridHk.value, INSURERS.hk);
    render(gridForeign.value, INSURERS.foreign);
    renderTimeline(timelineEl.value, EVENTS);
});
</script>

<!-- 静态节点（模板里存在，能带 data-v）：scoped 防止 h1/h2 等通用选择器泄漏到别的页面。
     base.css 已全局引入（* reset、body、.site-nav、.chart-card 等），此处不再重复。 -->
<style scoped>
.page { max-width: var(--content-w, 1200px); margin: 0 auto; padding: 32px 20px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin-bottom: 8px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 28px; }
h2 {
    color: #2c3e50;
    font-size: 23px;
    border-left: 5px solid #1f2937;
    padding-left: 12px;
    margin: 32px 0 12px;
    display: flex;
    align-items: baseline;
    gap: 10px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
}
.legend {
    display: flex;
    gap: 16px;
    justify-content: center;
    font-size: 14px;
    color: #6b7280;
    margin: 4px 0 24px;
}

.note { font-size: 17px; color: #6b7280; line-height: 1.7; margin-top: 14px; }
</style>
<!-- 动态节点（onMounted 里 document.createElement 生成，不带 data-v）：必须非 scoped 才能命中。
     这些类名（.b-card / .code / .t-*）在本前端其余页面未使用，逐字照搬自源页内联 <style>。 -->
<style>
.b-card {
    background: #fff;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 6px;
    border: 1px solid #e5e7eb;
    transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}

.b-card .codes { display: flex; gap: 6px; flex-wrap: wrap; }

.t-desc { font-size: 18px; color: #374151; line-height: 1.7; }
</style>
