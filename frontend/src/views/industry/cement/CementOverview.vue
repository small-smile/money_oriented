<template>
  <div class="page">
    <h1>水泥企业名录与供给侧政策线</h1>
    <div class="lede">地产的上游建材：按 A 股上市 / 仅港股上市 / 暂未取数 分组，附 2009–2025 产能与环保政策线</div>
    <div class="legend">
      <span><span class="code a">6005xx</span> A 股代码</span>
      <span><span class="code h">xxxxx.HK</span> 港股代码</span>
      <span>记账本位币 = 年报列示币种</span>
      <span style="color:#d97706;">橙色边框 = 已抓取历年数据</span>
    </div>

    <h2>为什么把水泥放在地产上游 <span class="count">传导链条与观察指标</span></h2>
    <div class="chain">
      <div class="flow">新开工面积 → 水泥需求（吨） → 出厂价与吨毛利 → 水泥企业营收/毛利率 → 资本开支与分红</div>
      水泥是<b>不可库存、运输半径短</b>（陆运通常 200 公里内经济）的产品，需求几乎全部来自当期施工，
      因此对地产<b>新开工</b>而非销售面积敏感，传导比开发商自身的利润表<b>更快</b>——
      开发商营收要等项目竣工结转（滞后 2–3 年），水泥营收在施工当季就体现。
      2021 年之后可以直观看到：
      <a href="../realestate/peers.html">六家央企开发商</a>的营收在 2021–2022 年仍在扩张（结算的是早年项目），
      而<a href="peers.html">八家水泥企业</a>的营收与毛利率自 2021 年起就同步下行。
      另一半需求来自基建（公路、水利、电力），所以水泥的下行幅度通常小于地产本身——
      这也是判断「基建对冲有没有效」的一个高频代理变量。
      <br><br>
      <b>本站可看的观察角度：</b>价格与吨毛利不在财务接口里，但<b>毛利率</b>能替代看景气度；
      <b>净现金 / 净负债率</b>看谁能在下行期活得住并继续分红（海螺、塔牌为净现金，天山、华新、冀东为净负债）；
      <b>重资产度与资本开支强度</b>看产能扩张有没有真的停下来；
      <b>赊销强度</b>看行业议价能力的分化（直销基建占比高的企业应收账款显著更重）。
    </div>

    <h2>A 股上市水泥企业 <span class="count">5 家 · 已按 A 股年报口径抓取历年数据</span></h2>
    <div class="grid" ref="gridA"></div>

    <h2>仅港股上市的水泥企业 <span class="count">3 家 · 走港股 F10，无资产负债表明细</span></h2>
    <div class="grid" ref="gridHk"></div>

    <h2>其他水泥/建材上市平台 <span class="count">5 家 · 暂未取数</span></h2>
    <div class="grid" ref="gridOther"></div>

    <h2>水泥行业政策线 <span class="count">2009–2025 · 产能调控、错峰生产、能耗与碳约束</span></h2>
    <div class="timeline" ref="timeline"></div>
    <div class="note">
      <b>口径提示：</b><b>天山股份（000877）是中国建材（03323.HK）的并表子公司</b>，
      两条线不是独立样本，任何情况下都<b>不能相加</b>作为行业合计。
      吨毛利、吨成本、水泥熟料销量只在年报管理层讨论与分析中披露，不在东方财富 F10 接口内，本站未抓取。
      政策条目为监管公开规则，未逐条回溯原文；财务序列由 <code>data/extract/fetch_cement_financials.py</code> 抓取东方财富 F10 生成。
    </div>
  </div>
</template>
<script setup>
// 逐字搬自 dashboard/industry/cement/overview.html：纯 HTML 内容页，无 ECharts、无 /api 取数。
// 原页 <script src=".../common/site-header.js"> 是全站导航条，已由 App.vue 的 <SiteHeader> 统一注入，
// 组件内不重复。名录卡片与政策时间线原页由页内脚本动态渲染，这里在 onMounted 里用模板 ref 原样复现，
// 内联数据（CEMENTS / DETAIL_PAGES / EVENTS）逐字照搬，文案、代码、口径、内联样式一律不改。
import { ref, onMounted } from 'vue'

const gridA = ref(null)
const gridHk = ref(null)
const gridOther = ref(null)
const timeline = ref(null)

/* 每家水泥企业：name 简称，group 控股集团，a A股代码（可空），h 港股代码（可空），cur 记账本位币 */
const CEMENTS = {
    a: [
        {name: '海螺水泥', group: '安徽海螺集团', a: '600585', h: '00914.HK', cur: '人民币'},
        {name: '天山股份', group: '中国建材集团', a: '000877', h: null, cur: '人民币'},
        {name: '华新水泥', group: '华新集团 / Holcim 参股', a: '600801', h: '06655.HK', cur: '人民币'},
        {name: '冀东水泥', group: '金隅集团', a: '000401', h: null, cur: '人民币'},
        {name: '塔牌集团', group: '民营（广东梅州）', a: '002233', h: null, cur: '人民币'}
    ],
    hk: [
        {name: '中国建材', group: '中国建材集团', a: null, h: '03323.HK', cur: '人民币'},
        {name: '华润建材科技', group: '华润集团', a: null, h: '01313.HK', cur: '人民币'},
        {name: '亚洲水泥（中国）', group: '台湾远东 / 亚泥系', a: null, h: '00743.HK', cur: '人民币'}
    ],
    other: [
        {name: '上峰水泥', group: '民营（浙江诸暨）', a: '000672', h: null, cur: '人民币'},
        {name: '万年青', group: '江西省国资', a: '000789', h: null, cur: '人民币'},
        {name: '青松建化', group: '新疆生产建设兵团', a: '600425', h: null, cur: '人民币'},
        {name: '西部水泥', group: '民营（陕西）· 海螺参股', a: null, h: '02233.HK', cur: '人民币'},
        {name: '中国山水水泥', group: '民营（山东）', a: null, h: '00691.HK', cur: '人民币'}
    ]
};

/* 已抓取数据：代码 → 同业对比页（按代码高亮该家） */
const DETAIL_PAGES = {
    '600585': 'peers.html?focus=600585',
    '000877': 'peers.html?focus=000877',
    '600801': 'peers.html?focus=600801',
    '000401': 'peers.html?focus=000401',
    '002233': 'peers.html?focus=002233',
    '03323': 'peers.html?focus=03323',
    '01313': 'peers.html?focus=01313',
    '00743': 'peers.html?focus=00743'
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

/* 色彩语义：产能与供给侧调控 = 蓝 #0369a1 · 需求端（地产与基建）= 紫 #6c3483 · 环保能耗与碳约束 = 灰绿 #0f766e */
const EVENTS = [
    {
        time: '2009.9',
        name: '国发 38 号文：水泥列入产能过剩重点行业',
        color: '#0369a1',
        desc: '《国务院关于抑制部分行业产能过剩和重复建设引导产业健康发展的若干意见》把水泥与钢铁、平板玻璃并列为产能过剩行业，要求严格控制新增熟料产能、加快淘汰立窑。但四万亿投资周期内需求仍在扩张，实际执行有限——2010–2013 年是新型干法熟料产能投放最集中的几年，也是本站序列里几家企业重资产度快速抬升的阶段。'
    },
    {
        time: '2013.10',
        name: '国发 41 号文：化解产能严重过剩矛盾',
        color: '#0369a1',
        desc: '明确「严禁备案和新建扩大产能的水泥项目」，新增产能须实行等量或减量置换。此后行业竞争从「铺产能」转向「争市场 + 兼并重组」，中国建材系（南方水泥、中联水泥、西南水泥，后整体注入天山股份）与海螺的区域整合都在这一阶段加速。'
    },
    {
        time: '2015',
        name: '需求首次负增长：全国水泥产量与全行业利润同步大跌',
        color: '#6c3483',
        desc: '2015 年是水泥行业罕见的「量价利」三杀年——产量出现改革开放以来首次年度下滑，全行业利润总额较 2014 年腰斩，部分区域出现全面亏损。本站序列中几家的毛利率与 ROE 在 2015 年触底，是后续供给侧改革的直接触发背景。（产量与全行业利润为行业公开统计口径，非本站抓取数据。）'
    },
    {
        time: '2016.5',
        name: '国办发 34 号文：停止新增产能 + 错峰生产常态化',
        color: '#0369a1',
        desc: '《关于促进建材工业稳增长调结构增效益的指导意见》要求 2020 年底前停止新增水泥熟料产能，严禁新增产能置换中的「以大代小」注水，并推动北方采暖季全面错峰生产。这是水泥供给侧改革的纲领性文件，效果在 2017–2019 年集中体现：产量基本零增长而价格与吨毛利创历史新高，本站可看到几家的毛利率与 ROE 在 2018–2019 年冲到区间顶部。'
    },
    {
        time: '2017',
        name: '错峰生产从北方推向全国 + 环保督察常态化',
        color: '#0f766e',
        desc: '错峰生产由「采暖季北方限产」扩展到长江流域等非采暖区的季节性停窑，叠加中央环保督察，落后产能与无组织排放企业实质出清。供给端的行政性约束成为价格的主要支撑，也让区域格局（谁在协同区内、谁在协同区外）比全国产能总量更能解释单家利润率的差异。'
    },
    {
        time: '2018.1',
        name: '《环境保护税法》施行，排污费改环保税',
        color: '#0f766e',
        desc: '2018 年 1 月 1 日起对大气、水、固废与噪声污染物征收环境保护税，取代此前的排污费。对水泥这类高排放行业，脱硝、除尘与在线监测的固定投入抬升单位成本，进一步压缩小产能的生存空间。注意会计上环保税计入税金及附加，不再作为排污费列在管理费用，跨 2018 年比较期间费用率时要意识到这一口径变化。'
    },
    {
        time: '2020.9',
        name: '碳达峰、碳中和目标提出（3060）',
        color: '#0f766e',
        desc: '水泥是国内碳排放第三大行业（约占全国 13%，主要来自石灰石分解的工艺过程排放，无法靠换能源解决）。3060 目标之后，产能置换比例收紧、超低排放改造与替代燃料成为长期资本开支方向；本站的资本开支强度指标在 2021 年之后仍不低，很大一部分不再是新建产能，而是环保与技改。'
    },
    {
        time: '2021.10',
        name: '能耗双控 + 拉闸限电：水泥价格创历史新高',
        color: '#0f766e',
        desc: '2021 年三季度能耗双控考核趋严叠加电力短缺，多省对水泥企业强制限产限电，四季度全国水泥均价创历史新高。但成本端煤炭同期暴涨，价格上涨并未完全转化为利润——本站序列可以看到 2021 年营收仍在高位而毛利率已经开始回落，这是「量价利」开始背离的第一年。'
    },
    {
        time: '2022',
        name: '地产下行传导到位：需求进入趋势性收缩',
        color: '#6c3483',
        desc: '新开工面积在 2022 年大幅下滑，水泥需求跟随收缩，全国产量回落到 2012 年前后的水平。与开发商不同，水泥企业没有「已售未结」蓄水池缓冲，利润表当年就反映——这一年几家的营收、毛利率、ROE 同时下台阶，净负债企业的现金压力也在这一年开始显性化。'
    },
    {
        time: '2024',
        name: '错峰生产大幅加码 + 反内卷式限产自律',
        color: '#0369a1',
        desc: '需求持续下滑、行业整体逼近盈亏平衡后，各省错峰生产天数显著增加，头部企业转向「以价换量」的反向操作（主动停窑保价）。这使得产能利用率降到历史低位，固定成本摊薄恶化——重资产度高的企业受损更明显，这也是本站把重资产度单列一张图的原因。'
    },
    {
        time: '2025.3',
        name: '全国碳市场扩容至水泥、钢铁、铝冶炼',
        color: '#0f766e',
        desc: '生态环境部印发工作方案，将水泥（熟料生产）纳入全国碳排放权交易市场，2024 年度为首个管控年度，初期以强度控制、免费配额为主。短期财务影响有限，但长期把碳效率变成成本项：能耗与替代燃料领先的企业将获得配额盈余，落后产能的边际成本抬升。（本条日期与覆盖范围未逐条回溯原文，见页末口径提示。）'
    },
    {
        time: '长期',
        name: '结构性看点：净现金的企业在下行期继续分红，净负债的企业在收缩',
        color: '#0f766e',
        desc: '水泥的周期底部不由企业自己决定，因此资产负债表决定谁能穿越。本站 FY2025 数据的分化非常清楚：海螺水泥净现金约 +367 亿（净负债率 −18%）、塔牌集团净现金约 +51 亿（−42%），两家在需求最差的年份仍保持分红；而天山股份净负债约 1035 亿（净负债率 +113%）、华新水泥 −159 亿、冀东水泥 −132 亿，资本开支与分红空间都被利息与偿债挤压。看水泥不能只看毛利率，必须把净现金、赊销强度和重资产度一起看。'
    }
];

function renderTimeline(wrap) {
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
    render(gridA.value, CEMENTS.a);
    render(gridHk.value, CEMENTS.hk);
    render(gridOther.value, CEMENTS.other);
    renderTimeline(timeline.value);
});
</script>

<!-- 静态模板节点（h1/lede/legend/chain/h2/note/grid 容器）用 scoped：逐字搬自源页 <head><style>。
     仅省略 body { padding: 0 }——base.css 的 * 重置已把 body padding 置 0，属「勿重复 base.css」。 -->
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
h2 .count { color: #9ca3af; font-size: 16px; font-weight: 500; }
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
.legend .code { font-size: 14px; }

/* === 产业链传导说明块 === */
.chain {
    background: #fff;
    border-radius: 8px;
    border-left: 4px solid #64748b;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 18px;
    color: #374151;
    line-height: 1.75;
}
.chain b { color: #1f2937; }
.chain a { color: #1d4ed8; }
.chain .flow {
    font-size: 17px;
    color: #475569;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    margin-bottom: 8px;
}
.note { font-size: 17px; color: #6b7280; line-height: 1.7; margin-top: 14px; }
.note b { color: #4b5563; }
details.note > summary { cursor: pointer; color: #4b5563; font-weight: 600; }
details.note > div { margin-top: 8px; }
</style>

<!-- 动态渲染的名录卡片与政策时间线（onMounted 里 createElement / innerHTML 生成）不带 scoped 的 data-v
     属性，样式必须放非 scoped 块才能命中。逐字搬自源页 <head><style>；.code 基类同时服务上方图例
     里的静态 code 与卡片里的动态 code，因此也放这里以覆盖两处。 -->
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
.b-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.10);
    border-color: #cbd5e1;
}
.b-card.static { pointer-events: none; }
.b-card .name { font-size: 18px; font-weight: 600; color: #1f2937; }
.b-card .group { font-size: 15px; color: #6b7280; }
.b-card .codes { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.code {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 14px;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-weight: 500;
}
.code.a { background: #fee2e2; color: #b91c1c; }
.code.h { background: #dbeafe; color: #1d4ed8; }
.cur { font-size: 14px; color: #9ca3af; }
.b-card.has-data { border-color: #d97706; box-shadow: 0 1px 4px rgba(217,119,6,0.15); }
.b-card.has-data .name::after {
    content: "· 数据页";
    font-size: 14px;
    color: #d97706;
    font-weight: 500;
    margin-left: 4px;
}
/* === 政策时间线（与银行页/险企页/地产页同款设计） === */
.timeline { position: relative; margin-top: 12px; padding-left: 108px; }
.timeline::before {
    content: '';
    position: absolute;
    left: 92px;
    top: 6px;
    bottom: 6px;
    width: 2px;
    background: #e5e7eb;
}
.t-item { position: relative; margin-bottom: 28px; }
.t-item:last-child { margin-bottom: 0; }
.t-year {
    position: absolute;
    left: -108px;
    top: 2px;
    width: 80px;
    text-align: right;
    font-family: "SF Mono", Consolas, monospace;
    font-size: 18px;
    font-weight: 700;
    color: #4b5563;
}
.t-dot {
    position: absolute;
    left: -19.5px;
    top: 6px;
    width: 13px;
    height: 13px;
    border-radius: 50%;
    border: 3px solid #fff;
    box-shadow: 0 0 0 2px currentColor;
}
.t-card {
    background: #fff;
    border-radius: 8px;
    border-left: 4px solid transparent;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.t-name { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.t-desc { font-size: 18px; color: #374151; line-height: 1.7; }
</style>
