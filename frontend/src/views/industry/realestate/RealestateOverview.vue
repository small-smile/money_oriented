<template>
  <div class="page">
      <h1>央企地产开发商名录与政策线</h1>
      <div class="lede">按 A 股上市 / 仅港股上市 / 其他央企系平台 分组，附 2019–2025 房地产融资与需求端政策线</div>
      <div class="legend">
          <span><span class="code a">6000xx</span> A 股代码</span>
          <span><span class="code h">xxxxx.HK</span> 港股代码</span>
          <span>记账本位币 = 年报列示币种</span>
          <span style="color:#d97706;">橙色边框 = 已抓取历年数据</span>
      </div>
      <div class="lede" style="margin-top:-14px;">上游建材看 <a href="../cement/overview.html">水泥企业名录与供给侧政策线</a>
          （水泥发货当期确认收入，营收拐点领先开发商约 2 年）</div>

      <h2>A 股上市央企开发商 <span class="count">3 家 · 已按 A 股年报口径抓取历年数据</span></h2>
      <div class="grid" id="grid-a" ref="gridA"></div>

      <h2>仅港股上市的央企开发商 <span class="count">3 家 · 走港股 F10，无资产负债表明细</span></h2>
      <div class="grid" id="grid-hk" ref="gridHk"></div>

      <h2>其他央企系开发平台 <span class="count">4 家 · 暂未取数</span></h2>
      <div class="grid" id="grid-other" ref="gridOther"></div>

      <h2>房地产政策线 <span class="count">2019–2025 · 融资监管、供地与需求端</span></h2>
      <div class="timeline" id="timeline" ref="timelineEl"></div>
      <div class="note">
          <b>口径提示：</b>时间线中的三道红线阈值（剔预收资产负债率 70%、净负债率 100%、现金短债比 1）在
          <a href="peers.html">六家央企开发商对比</a> 页以红色横线标出，但该页三项指标是<b>按公开定义自算</b>、不是年报披露值
          （永续债留在权益分母、货币资金未剔预售监管资金，与披露值有方向可解释的偏差，详见该页口径说明）。
          政策条目为监管公开规则，未逐条回溯年报原文；财务序列由 <code>data/extract/fetch_developer_financials.py</code> 抓取东方财富 F10 生成。
      </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

// 1:1 搬自 dashboard/industry/realestate/overview.html —— 纯内容页（无 /api、无 ECharts）。
// DEVELOPERS / DETAIL_PAGES / EVENTS 内联数据逐字照搬；名录卡片与政策时间线的 DOM 构建逻辑
// 原样保留，仅把原 document.getElementById 换成模板 ref、执行时机移进 onMounted。样式按静态/
// 动态拆两块（动态节点拿不到 scoped 的 data-v）；* 重置与 body padding 复用 base.css、不重复。

const gridA = ref(null)
const gridHk = ref(null)
const gridOther = ref(null)
const timelineEl = ref(null)

/* 每家开发商：name 简称，group 控股集团，a A股代码（可空），h 港股代码（可空），cur 记账本位币 */
const DEVELOPERS = {
    a: [
        {name: '保利发展', group: '保利集团', a: '600048', h: null, cur: '人民币'},
        {name: '招商蛇口', group: '招商局集团', a: '001979', h: null, cur: '人民币'},
        {name: '华侨城A', group: '华侨城集团', a: '000069', h: null, cur: '人民币'}
    ],
    hk: [
        {name: '中国海外发展', group: '中国建筑集团', a: null, h: '00688.HK', cur: '人民币'},
        {name: '华润置地', group: '华润集团', a: null, h: '01109.HK', cur: '人民币'},
        {name: '中国金茂', group: '中国中化', a: null, h: '00817.HK', cur: '人民币'}
    ],
    other: [
        {name: '大悦城', group: '中粮集团', a: '000031', h: null, cur: '人民币'},
        {name: '中交地产', group: '中交集团', a: '000736', h: null, cur: '人民币'},
        {name: '保利置业集团', group: '保利集团', a: null, h: '00119.HK', cur: '人民币'},
        {name: '招商局置地', group: '招商局集团', a: null, h: '00978.HK', cur: '人民币'}
    ]
};

/* 已抓取数据：代码 → 同业对比页（按代码高亮该家） */
const DETAIL_PAGES = {
    '600048': 'peers.html?focus=600048',
    '001979': 'peers.html?focus=001979',
    '000069': 'peers.html?focus=000069',
    '00688': 'peers.html?focus=00688',
    '01109': 'peers.html?focus=01109',
    '00817': 'peers.html?focus=00817'
};

function render(grid, list) {
    if (!grid) return;
    for (const it of list) {
        const key = it.a || (it.h || '').replace('.HK', '');
        const hasData = !!DETAIL_PAGES[key];
        const card = document.createElement(hasData ? 'a' : 'div');
        card.className = 'b-card' + (hasData ? ' has-data' : ' static');
        if (hasData) card.href = DETAIL_PAGES[key];

        const name = document.createElement('span');
        name.className = 'name';
        name.textContent = it.name;

        const group = document.createElement('span');
        group.className = 'group';
        group.textContent = it.group;

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
        const cur = document.createElement('span');
        cur.className = 'cur';
        cur.textContent = it.cur;
        codes.appendChild(cur);

        card.appendChild(name);
        card.appendChild(group);
        card.appendChild(codes);
        grid.appendChild(card);
    }
}

/* 色彩语义：融资与债务监管 = 蓝 #0369a1 · 需求端与土地供应 = 紫 #6c3483 · 长期趋势性变革 = 灰绿 #0f766e */
const EVENTS = [
    {
        time: '2019.7',
        name: '境外发债只能置换到期债务（发改委 778 号文）',
        color: '#0369a1',
        desc: '房企发行外债备案登记只允许用于置换未来一年内到期的中长期境外债务，境外融资由「增量」转为「借新还旧」。这是本轮融资收紧的起点，对高度依赖美元债的民营房企影响远大于央企——六家央企开发商的有息负债以境内银行贷款与公司债为主。'
    },
    {
        time: '2020.8',
        name: '三道红线（重点房企资金监测与融资管理规则）',
        color: '#0369a1',
        desc: '住建部、央行召开 12 家重点房企座谈会，按剔除预收款后的资产负债率 > 70%、净负债率 > 100%、现金短债比 < 1 三项分「红橙黄绿」四档，逐档限制有息负债年增速（绿档 15%、红档 0）。2021 年起试点扩围。同业对比页的三张红线图即对应这三项指标，红色横线为阈值。'
    },
    {
        time: '2020.12',
        name: '银行房地产贷款集中度管理（金融端两条红线）',
        color: '#0369a1',
        desc: '央行、银保监会按银行分档设定房地产贷款占比与个人住房贷款占比上限，2021 年 1 月 1 日起实施。约束从房企资产负债表转移到银行资产端，开发贷与按揭同时受限，行业整体加杠杆能力见顶。'
    },
    {
        time: '2021.2',
        name: '22 城集中供地（「两集中」）',
        color: '#6c3483',
        desc: '重点城市集中发布出让公告、集中组织出让活动，全年分批次供地。资金实力强的主体在批次窗口内更占优势，央企与地方国企拿地金额占比自 2021 年下半年起快速上升；对应到财报上是央企的存货与合同负债在 2021–2022 年仍能扩张，而民企同期收缩。'
    },
    {
        time: '2022.1',
        name: '商品房预售资金监管全国统一（重点监管额度）',
        color: '#0369a1',
        desc: '住建部、央行、银保监会出台预售资金监管指导意见，按项目工程造价确定重点监管额度，专户内资金按节点拨付。后果是「集团账面货币资金 ≠ 可自由调用资金」：本站自算的现金短债比用的是资产负债表货币资金，未剔除受监管的预售资金，因此系统性高于房企披露值。'
    },
    {
        time: '2022.11',
        name: '金融十六条 + 融资「三支箭」',
        color: '#0369a1',
        desc: '央行、银保监会《关于做好当前金融支持房地产市场平稳健康发展工作的通知》共 16 条，配合信贷、债券（中债增担保）、股权（11 月底恢复房企再融资与并购重组）三支箭。政策从「压杠杆」转向「保交楼、稳融资」，但落地明显向优质主体倾斜，央企是最直接的受益方。'
    },
    {
        time: '2023.7',
        name: '中央政治局会议：供求关系发生重大变化',
        color: '#6c3483',
        desc: '首次表述「我国房地产市场供求关系发生重大变化」，随后 8–9 月落地「认房不认贷」、首付比例与房贷利率下限下调、存量首套房贷利率批量调整。需求端政策全面转向宽松，但同业对比页可见六家的营收与毛利率在 2023 年之后仍继续下行——结算的是 2021–2022 年高地价项目。'
    },
    {
        time: '2024.1',
        name: '城市房地产融资协调机制（项目「白名单」）',
        color: '#0369a1',
        desc: '住建部、金融监管总局建立城市层面协调机制，按项目而非按主体推送可贷清单，融资对象从「企业信用」下沉到「项目现金流」。这一转向使集团层面的三道红线档位对新增融资的解释力下降。'
    },
    {
        time: '2024.5',
        name: '5·17 新政：取消房贷利率下限 + 首付 15% + 收储再贷款',
        color: '#6c3483',
        desc: '央行取消全国层面首套与二套房贷利率政策下限，首套最低首付降至 15%、二套 25%，并设立 3000 亿元保障性住房再贷款支持地方国企收购存量商品房。需求端政策工具箱基本用尽。'
    },
    {
        time: '2024.9',
        name: '政治局会议定调「止跌回稳」+ 一线城市松限购',
        color: '#6c3483',
        desc: '9 月 26 日政治局会议罕见就房地产提出「促进市场止跌回稳」，随后广深沪京相继放松限购、存量房贷利率再次批量下调。此后销售同比降幅收窄，但对开发商利润表的传导要滞后 1–2 年（先体现为合同负债，再结转为营收）。'
    },
    {
        time: '2025.5',
        name: '《住宅项目规范》实施（「好房子」新标准）',
        color: '#6c3483',
        desc: '强制性国家标准 GB 55038—2025 自 2025 年 5 月 1 日施行，层高不低于 3 米、四层及以上设电梯、隔声与防水要求提高。新项目建造成本上升、产品力成为竞争维度，对现金充裕且能做产品溢价的主体相对有利。'
    },
    {
        time: '2019–2025',
        name: '长期趋势：行业出清与央企份额抬升',
        color: '#0f766e',
        desc: '融资收紧叠加销售下行，民营房企大面积出险退出，销售与拿地份额向央企、头部地方国企集中。本站数据侧可交叉验证的是三家 A 股主体内部的分化：招商蛇口三项自算指标始终在阈值内侧（2025 年 61.74% / 59.05% / 1.39）、保利发展剔预收资产负债率贴着 70% 附近但现金短债比长年 1.5 以上，而华侨城 A 2025 年三项全部触线（78.82% / 177.10% / 0.61，文旅重资产叠加结算下滑）。「央企」不等于安全，需逐家看。'
    },
    {
        time: '长期口径提示',
        name: '三家港股主体无资产负债表明细，已售未结改用年报原文补齐',
        color: '#0f766e',
        desc: '中国海外发展、华润置地、中国金茂只走港股 F10 主要指标接口，没有分科目负债数据，因此净负债率、现金短债比、存货占比、销售回款等自算指标在这三家为空；已售未结蓄水池与剔预收资产负债率已逐年从 HKEXnews 年度业绩公告原文取数补齐（中海外「预售楼款」、华润「合约负债」、金茂在「其他应付款项和应计款项」附注里的合约负债 + 预收款项），起点为各家改以人民币编制之后的年份。币种上早前的结论已修正：港股 F10 返回的金额是年报本位币原值、不做折算（接口字段却一律标 HKD），但三家近年年报都以人民币编制 —— 中海外自 2019 年年报起（2018 年比较数经重列）、华润置地自 2018 年年报起、中国金茂自 2016 年年报起（FY2016 公告附注 2.2「呈列货币变更」，追溯重列 FY2015 比较数；早前写 2015 年，2026-08-19 已修正），故金额类图表六家可直接比大小。'
    }
];

onMounted(() => {
  render(gridA.value, DEVELOPERS.a)
  render(gridHk.value, DEVELOPERS.hk)
  render(gridOther.value, DEVELOPERS.other)

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
})
</script>

<style scoped>
/* 静态模板元素依赖的规则（逐字搬自源页 <style>）；* 重置 / body / 已在 base.css 全局引入，不重复。 */
.page { max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }
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
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
}
.legend {
    display: flex;
    gap: 16px;
    justify-content: center;
    font-size: 14px;
    color: #6b7280;
    margin: 4px 0 24px;
    flex-wrap: wrap;
}

.note { font-size: 17px; color: #6b7280; line-height: 1.7; margin-top: 14px; }
.note b { color: #4b5563; }
</style>

<style>
/* 以下针对动态生成的节点：名录卡片 .b-card（onMounted 里 document.createElement）与政策时间线
   .t-*（innerHTML 注入）。动态节点拿不到 scoped 的 data-v 属性，规则必须放非 scoped 块。逐字搬自源页 <style>。 */
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

.b-card .group { font-size: 15px; color: #6b7280; }
.b-card .codes { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }

.cur { font-size: 14px; color: #9ca3af; }

.t-desc { font-size: 18px; color: #374151; line-height: 1.7; }
</style>
