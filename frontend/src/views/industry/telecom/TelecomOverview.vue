<template>
  <div class="page">
    <h1>三大运营商与通信产业链概览</h1>
    <div class="lede">按基础电信运营商 / 共享基础设施 / 上下游相关上市主体分组，附电信业重组与监管变革时间线</div>
    <div class="legend">
      <span><span class="code a">6xxxxx</span> A 股代码</span>
      <span><span class="code h">xxxxx.HK</span> 港股代码</span>
      <span style="color:#d97706;">橙色边框 = 已有同业对比数据</span>
    </div>

    <h2>基础电信运营商 <span class="count">3 家 · 均 A+H · 已抓取 A 股年报口径历年数据</span></h2>
    <div class="grid" ref="gridCarrierEl"></div>

    <h2>主体结构：中国联通的 A 股与红筹不是同一家公司 <span class="count">本行业最容易踩的口径坑</span></h2>
    <div class="entity">
      中国移动 <b>600941 与 00941</b>、中国电信 <b>601728 与 00728</b> 都是<b>同一法人</b>两地上市，
      A/H 年报是同一套合并报表，按项目规则取 A 股年报口径即可。<br>
      中国联通<b>不是</b>：A 股 600050 是「中国联合网络通信股份有限公司」，00762.HK 是
      「中国联通（香港）有限公司」<b>红筹主体</b>，两者是不同法人，红筹在上、A 股在下的多层持股结构，
      红筹的合并报表包含 600050 及大额少数股东权益。因此
      <b>600050 的归母净利润小于 00762 的股东应占利润，两条线不可当作同一公司的 A/H 口径混比，更不可相加</b>。
      本项目的联通数据一律取 600050。
    </div>

    <h2>共享基础设施与相关上市主体 <span class="count">4 家 · 暂未取数</span></h2>
    <div class="grid" ref="gridInfraEl"></div>

    <h2>电信业重组与监管变革时间线 <span class="count">1994–2025 · 重组、发牌、税制、资费与资本开支</span></h2>
    <div class="timeline" ref="timelineEl"></div>
    <div class="note">
      时间线中的<b>重组、发牌、税制与资费条目</b>为监管与交易所公开事实（营改增文号财税〔2014〕43 号、
      铁塔资产注入评估值与持股比例、联通混改募资上限、3G/5G 发牌日期均已核对公开来源）；
      <b>对财务序列的影响</b>已用本项目抓取的历年数据交叉验证（如联通 2008 年归母 202.4 亿元的一次性处置收益、
      2015→2017 年资本开支由 1,338.8 亿元降到 421.3 亿元）。历年数值见
      <a href="peers.html">三大运营商同业对比</a>。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 逐字搬自 dashboard/industry/telecom/overview.html：内联数据（COMPANIES / DETAIL_PAGES /
// EVENTS）与 render / renderTimeline 渲染逻辑原样保留，仅把 document.getElementById 改为组件 ref。
// 无 ECharts、无 /api，纯静态名录 + 时间线；字段、数值、文案、样式一律不变。
const gridCarrierEl = ref(null)
const gridInfraEl = ref(null)
const timelineEl = ref(null)

/* 每家：name 简称，a A股代码（可空），h 港股代码（可空），role 在产业链中的角色 */
const COMPANIES = {
    carrier: [
        {name: '中国移动', a: '600941', h: '00941.HK', role: '移动 10.05 亿户 · 收入体量约为电信 2 倍'},
        {name: '中国电信', a: '601728', h: '00728.HK', role: '移动 4.39 亿户 · 天翼云 1,207 亿元'},
        {name: '中国联通', a: '600050', h: '00762.HK', role: 'A 股与红筹为不同法人 · 与电信共建共享 5G'}
    ],
    infra: [
        {name: '中国铁塔', a: null, h: '00788.HK', role: '三家共同持股的站址公司 · 2015 年承接 152 万座存量铁塔'},
        {name: '中国通信服务', a: null, h: '00552.HK', role: '网络工程与维护外包 · 收入随三家资本开支波动'},
        {name: '中国卫通', a: '601698', h: null, role: '卫星通信（航天科技系）· 与运营商卫星业务互补'},
        {name: '中国广电', a: null, h: null, role: '2019 年第四张 5G 牌照 · 700MHz 与移动共建，未上市'}
    ]
};

/* 已抓取数据的公司：代码 → 该公司详情页（业绩与财务，页内可切换到收入构成／运营页） */
const DETAIL_PAGES = {
    '600941': '../../company/telecom/index.html?code=600941',
    '601728': '../../company/telecom/index.html?code=601728',
    '600050': '../../company/telecom/index.html?code=600050'
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

        const role = document.createElement('span');
        role.className = 'role';
        role.textContent = it.role;

        card.appendChild(name);
        card.appendChild(codes);
        card.appendChild(role);
        grid.appendChild(card);
    }
}

/* 色彩语义与银行/保险页一致：市场结构与重组 = 蓝 #0369a1 · 资费与监管新规 = 紫 #6c3483 ·
 * 长期趋势性变革（投资周期、业务结构） = 灰绿 #0f766e */
const EVENTS = [
    {
        time: '1994.7',
        name: '中国联通成立，电信垄断被打破',
        color: '#0369a1',
        desc: '国务院批准电子部、电力部、铁道部与中信集团各出资一亿元组建中国联合通信有限责任公司，开始在市话与移动业务上与中国电信竞争。此后二十年的行业格局，都是围绕「几家竞争、谁拿哪张牌照」反复重组。'
    },
    {
        time: '2000–2002',
        name: '移动资产剥离与电信南北分拆',
        color: '#0369a1',
        desc: '2000 年 4 月中国移动通信集团在原中国电信移动资产剥离基础上成立；2002 年 5 月中国电信南北分拆，北方十省与吉通、原中国网通组建中国网通，形成「四大两小」格局。中国联通 A 股（600050）于 2002 年 10 月上市，是三家里 A 股历史最长的一家，本项目的联通财务序列因此能回溯到 1999 年。'
    },
    {
        time: '2008.5–10',
        name: '六合三重组：电信 1,100 亿元收 CDMA、联通与网通合并',
        color: '#0369a1',
        desc: '三部委《关于深化电信体制改革的通告》确定：中国电信收购联通 CDMA 网络与用户（网络 438 亿元＋业务 662 亿元，合计 1,100 亿元，2008-10-01 起交割）、中国联通与中国网通合并（2008-10-15 新联通成立）、中国铁通并入中国移动、中国卫通基础电信业务并入中国电信。<b>本项目数据可直接看到这次重组：</b>联通 2008 年归母净利润 202.4 亿元（含处置 CDMA 的一次性收益），2009 年即回落至 31.4 亿元；联通员工数由 2007 年 4.8 万人跳到 2008 年 20.4 万人（并入网通）。'
    },
    {
        time: '2009.1.7',
        name: '3G 牌照发放：移动 TD-SCDMA、电信 CDMA2000、联通 WCDMA',
        color: '#0369a1',
        desc: '工信部同日向三家发放三种制式的 3G 牌照。制式差异直接决定了此后五年的竞争位势：联通拿到产业链最成熟的 WCDMA，移动被指定承担自主标准 TD-SCDMA 的建网任务，资本开支强度在 2009—2012 年集中抬升（联通该四年资本开支占收入比 35%—51%）。'
    },
    {
        time: '2013.12 / 2015.2',
        name: '4G 牌照：先 TD-LTE，后补 FDD-LTE',
        color: '#0369a1',
        desc: '2013 年 12 月三家同获 TD-LTE 牌照，2015 年 2 月电信与联通再获 FDD-LTE 牌照。晚一年多的 FDD 牌照使两家的 4G 建网整体滞后，联通移动出账用户与 ARPU 在 2015 年双双下滑（用户净减 1,426 万户至 25,232 万户），是其 2016 年归母仅 1.5 亿元的直接前因。'
    },
    {
        time: '2014.6.1',
        name: '电信业营改增（财税〔2014〕43 号）',
        color: '#6c3483',
        desc: '基础电信服务按 11%、增值电信服务按 6% 缴增值税，邮电通信业营业税税目停止执行。<b>这是本页收入类序列最重要的一处口径断点</b>：营收由含税转为不含税，三家 2014—2015 年的收入增速被系统性压低（联通 2014 年 2,885.7 亿元、2015 年 2,770.5 亿元连续两年下滑，其中含这层口径因素），跨 2014 年做同比要先扣掉税制影响。'
    },
    {
        time: '2015.10',
        name: '152 万座存量铁塔注入中国铁塔，评估值约 2,314 亿元',
        color: '#0f766e',
        desc: '中国铁塔以「发行股份＋现金」方式收购三家全部存量铁塔相关资产，交易后持股为中国移动 38%、中国联通 28.1%、中国电信 27.9%、中国国新 6%。此后新建站址改为向铁塔公司租用：资产端的自建铁塔折旧被替换为租费与（2019 年新租赁准则后的）使用权资产摊销，<b>资本开支口径与毛利率因此不完全跨期可比</b> —— 联通资本开支由 2015 年 1,338.8 亿元降至 2017 年 421.3 亿元，其中既有 4G 高峰过去、也有这层口径转移。'
    },
    {
        time: '2017.9 / 2018.7',
        name: '提速降费：取消手机国内长途漫游费、再取消流量漫游费',
        color: '#6c3483',
        desc: '2017-09-01 取消手机国内长途和漫游费，2018-07-01 取消流量「漫游」费。<b>ARPU 是承压最直接的指标</b>：联通移动出账用户 ARPU 由 2017 年 48.0 元降到 2019 年 40.4 元（−15.8%），宽带接入 ARPU 由 2015 年 63.6 元一路降到 2021 年 41.3 元。三家自此把增长寄托在用户数、融合套餐与政企业务上，而非单价。'
    },
    {
        time: '2017.8',
        name: '中国联通混改：非公开发行募资上限 617.25 亿元',
        color: '#0369a1',
        desc: '联通引入腾讯、阿里、百度、京东、苏宁等战略投资者，A 股非公开发行募集资金总额不超过约 617.25 亿元。混改后联通的资本开支纪律与自由现金流明显改善（2017 年资本开支同比降 41.6%），归母净利润从 2016 年 1.5 亿元回升到 2018 年 40.8 亿元，但 ROE 至今仍是三家最低。'
    },
    {
        time: '2019.6–11',
        name: '5G 发牌、电信联通共建共享、携号转网全国实施',
        color: '#0369a1',
        desc: '2019-06-06 工信部向移动、电信、联通与中国广电发放 5G 商用牌照；2019-09 电信与联通宣布共建共享 5G 接入网（2021-01 移动与中国广电签署 700MHz 共建共享协议）；2019-11-27 携号转网在全国实施。共建共享是电信与联通资本开支长期低于移动的制度性原因，也是三家 5G 期间资本开支强度没有回到 3G/4G 高位的关键。'
    },
    {
        time: '2021.8 / 2022.1',
        name: '中国电信、中国移动相继回归 A 股',
        color: '#0369a1',
        desc: '中国电信 2021-08-20、中国移动 2022-01-05 在上交所上市。<b>这是本页序列分段的依据：</b>两家的 A 股年报自 2021 年度起才有，更早年份的接口数据是按其上市前（H 股）披露回填的，口径不同源，本项目按「交易所口径分来源披露」规则分成两条 series，不拼成一条连续曲线。回 A 后三家同步提高派息比例（中国电信 2025 年度以现金分配的利润为股东应占利润的 75%），是「高股息」逻辑的起点。'
    },
    {
        time: '2023–2025',
        name: '资本开支从通信网络切向算力，第二曲线进入平台期',
        color: '#0f766e',
        desc: '三家资本开支同步见顶回落：移动 1,852（2022）→1,509 亿元（2025，2026 年指引 1,366 亿元），电信 988（2023）→804 亿元，联通 742（2022）→541.5 亿元（2026 年指引约 500 亿元、其中算力占比超 35%）。同期第二曲线增速换挡：电信产业数字化收入 2024 年 +5.5%、2025 年 +0.5%，云业务的绝对值披露也在收窄（移动 2024 年起不再单列移动云收入、联通 2025 年只给同比）。结果是 2025 年三家营收几乎零增长（移动 +0.9%、电信 +0.1%、联通 +0.7%），而自由现金流与派息率仍在改善 —— 这正是当前运营商股「低增长、高现金、高股息」定价的基本面。'
    }
];

function renderTimeline() {
    const wrap = timelineEl.value;
    if (!wrap) return;
    wrap.innerHTML = EVENTS.map(e => `
        <div class="t-item">
            <div class="t-year">${e.time}</div>
            <div class="t-dot" style="color:${e.color}"></div>
            <div class="t-card" style="border-left-color:${e.color}">
                <div class="t-name" style="color:${e.color}">${e.name}</div>
                <div class="t-desc">${e.desc}</div>
            </div>
        </div>
    `).join('');
}

onMounted(() => {
    render(gridCarrierEl.value, COMPANIES.carrier);
    render(gridInfraEl.value, COMPANIES.infra);
    renderTimeline();
});
</script>

<!-- 动态节点：名录卡片（.b-card*）、代码徽标（.code*）与时间线条目（.t-*）由脚本用
     createElement / innerHTML 注入，不带 scoped 的 data-v 属性，其样式必须放在非 scoped 块；
     .code 同时用于静态图例与动态卡片，也放这里。base.css 已全局引入，此处不重复其规则。 -->
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

.b-card .role { font-size: 15px; color: #6b7280; }
.b-card .codes { display: flex; gap: 6px; flex-wrap: wrap; }

.t-desc { font-size: 18px; color: #374151; line-height: 1.7; max-width: 900px; }
</style>

<!-- 静态节点（页面容器/标题/图例/主体结构说明/时间线容器/脚注）在模板里，带 data-v，可 scoped 收敛。
     原页 body { padding: 0 } 与 base.css 的 * { padding: 0 } 等效，属重复 base.css，此处不再写。 -->
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

.entity {
    background: #fff;
    border-radius: 8px;
    border-left: 4px solid #0369a1;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 17px;
    color: #374151;
    line-height: 1.8;
    max-width: 1000px;
}
.entity b { color: #0369a1; }

.note { font-size: 17px; color: #6b7280; line-height: 1.7; margin-top: 14px; max-width: 1000px; }
</style>
