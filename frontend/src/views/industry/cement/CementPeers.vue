<template>
  <div class="page">
    <h1>八家水泥企业同业对比</h1>
    <div class="lede">
      海螺水泥 600585 · 天山股份 000877 · 华新水泥 600801 · 冀东水泥 000401 · 塔牌集团 002233 —— A 股上市，取<b>各期 A 股年报</b>合并口径，三张表明细科目齐全<br>
      中国建材 03323 · 华润建材科技 01313 · 亚洲水泥（中国）00743（<span style="border-bottom: 2px dashed #0e7490">虚线</span>）——
      仅港交所上市，财务序列走港股 F10 主要指标，只有收入/利润/比率类科目；<b>八家均为人民币口径</b>，
      <a href="overview.html">名录与政策时间线</a> · 下游看 <a href="../realestate/peers.html">六家央企开发商</a><br>
      <b>销量 / 吨收入 / 吨成本 / 吨毛利</b>四类图另走<b>逐份年报手工提取层</b>（F10 三张表里没有这些字段），
      覆盖八家 2010—2025 年，见页尾口径说明
    </div>
    <div class="warn">
      <b>样本重叠提示：</b>天山股份（000877）是中国建材（03323.HK）的<b>并表水泥业务平台</b>，
      中国建材的水泥板块收入绝大部分即来自天山股份。这两条线<b>不是独立样本，任何情况下都不能相加</b>；
      看行业格局时请把它们当作「同一集团的子公司口径 / 集团口径」两条线来读。
    </div>

    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">数据加载失败：{{ error }}（请确认后端服务已启动）</div>
    <div ref="chartsEl" id="charts"></div>
  </div>
</template>

<script setup>
import LoadingNote from '../../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../../api'

// 逐字搬自 dashboard/industry/cement/peers.html：CHARTS/ORDER/COLORS/HK_CODES、fmt、buildChart 与
// onMounted 渲染逻辑（含三块口径说明 + 缺口说明）原样保留，仅取数改走统一 apiGet（解包后返回 peers），
// charts 容器改用组件 ref、每张图的 resize/dispose 归拢到组件生命周期。图、颜色、轴、tooltip、legend、
// series 与数据口径（含后端 /api/cement_peers 现算的 ops_* 字段）一律不变。
const loading = ref(true)
const error = ref('')
const chartsEl = ref(null)
let charts = []

function onResize() { charts.forEach(c => { try { c.resize() } catch (_) {} }) }

const API = '/api/cement_peers';
const ORDER = ['600585', '000877', '600801', '000401', '002233', '03323', '01313', '00743'];
const COLORS = {
    '600585': '#c0392b',   // 海螺水泥
    '000877': '#1f6feb',   // 天山股份
    '600801': '#b45309',   // 华新水泥
    '000401': '#0f766e',   // 冀东水泥
    '002233': '#6c3483',   // 塔牌集团
    '03323': '#0e7490',    // 中国建材
    '01313': '#16a34a',    // 华润建材科技
    '00743': '#db2777'     // 亚洲水泥（中国）
};
// 非 A 股年报口径的公司：线型改虚线，提醒数据来自港股 F10 主要指标
const HK_CODES = ['03323', '01313', '00743'];

/* 每张图：key 取 annual 记录里的字段，scale 除数（1e8 = 亿元），unit 轴单位，decimals 提示框小数位
 * marks 画竖向 markLine 标注政策/景气断点年；note 常显，detail 折叠展开
 * redline 画横向红线（如净负债率 0 = 净现金分界）
 * codes 只画指定几家（量级差太大时拆图用）；trim 裁掉首尾全空的年份列
 * extraSeries 把同一公司的另一币种/另一披露口径单列成一条序列，绝不与主序列拼接 */
const CHARTS = [
    {
        id: 'revenue', key: 'total_operate_income', scale: 1e8, unit: '亿元', decimals: 0,
        title: '营业收入',
        sub: '水泥收入在发货当期确认，跟随施工强度实时波动，没有开发商那样的结算时滞',
        marks: [{year: '2016', text: '供给侧改革'}, {year: '2021', text: '需求见顶'}],
        note: '<b>与下游的时滞差：</b>开发商营收要等竣工交付结转（滞后销售 2—3 年），水泥在发货当期就确认收入，' +
              '所以水泥的营收拐点<b>领先</b>开发商 2 年左右——2021 年起水泥就在下行，而' +
              '<a href="../realestate/peers.html">六家开发商</a>的营收要到 2023—2024 年才明显回落。' +
              '<b>天山股份 2021 年的跳升不是内生增长</b>：中国建材把中联、南方、西南水泥等资产重组注入天山股份，' +
              '营收从 80 亿级跳到 1,700 亿级，跨 2021 年不可比。',
        detail: '<b>需求的两条腿：</b>水泥需求约六成来自房地产（新开工与施工），约四成来自基建（公路、水利、电力、市政）。' +
                '因此营收下行幅度通常小于地产投资降幅——判断「基建对冲有没有效」可以看水泥营收相对新开工面积的偏离。<br>' +
                '<b>不可库存 + 短运距：</b>熟料与水泥的经济运输半径通常在陆运 200 公里、水运 500 公里内，' +
                '产品保质期只有一两个月，无法像钢材那样跨区套利或囤货。结果是水泥高度<b>区域化</b>，' +
                '同一年份各家的量价表现取决于所在区域的供需与协同程度，全国总量解释不了单家差异。<br>' +
                '<b>口径：</b>取东财 <code>TOTAL_OPERATE_REVE</code>（A 股）与港股 F10 <code>OPERATE_INCOME</code>，' +
                '均为营业总收入含其他业务；华新水泥近年海外（中亚、非洲、阿曼）与骨料/混凝土收入占比上升，' +
                '中国建材还含玻纤、风电叶片、石膏板等非水泥板块，横比营收规模时要意识到业务口径不同质。'
    },
    {
        id: 'profit', key: 'parent_netprofit', scale: 1e8, unit: '亿元', decimals: 0,
        title: '归母净利润',
        sub: '周期性极强：2018—2019 年集体创历史新高，2024—2025 年多家亏损',
        marks: [{year: '2015', text: '行业首次全面亏损'}, {year: '2019', text: '盈利峰值'}],
        note: '水泥的利润弹性远大于收入弹性：收入从 2021 年到 2025 年降三到五成，利润却从峰值跌九成以上甚至转负。' +
              '原因是<b>固定成本占比高</b>——折旧、人工与矿山摊销不随销量下降，销量一跌，单位成本立刻抬升。',
        detail: '<b>利润 ≈（吨价 − 吨成本）× 销量：</b>这个拆解本页已经画出来了——' +
                '销量看下面两张<b>水泥熟料销量</b>图，量价与成本看<b>吨收入 / 吨成本 / 吨毛利</b>三张图，' +
                '数据逐份年报手工提取（F10 财务接口里没有吨指标）。<br>' +
                '<b>2015 与 2024—2025 两次谷底的差别：</b>2015 年是产能过剩 + 需求短暂失速，靠供给侧改革（行政限产）' +
                '就把价格拉回来了；2024—2025 年是地产进入趋势性收缩，需求中枢下移，限产只能维持盈亏平衡而无法复制 2018 年的暴利。<br>' +
                '<b>非经常项：</b>下行期利润里包含资产减值（产能关停、商誉减值）与处置收益，' +
                '数据文件保留了 <code>deduct_parent_netprofit</code>（扣非归母）与 <code>asset_impairment</code> 字段，' +
                '判断经营质量应以扣非口径为准。'
    },
    {
        id: 'sales-big', key: 'ops_sales_total_wt', scale: 1, unit: '万吨', decimals: 0, trim: true,
        codes: ['600585', '03323', '000877'],
        title: '水泥熟料销量——亿吨级三家',
        sub: '海螺 / 中国建材 / 天山，逐份年报手工提取；与下面「区域五家」拆图是因为量级差近 40 倍',
        marks: [{year: '2016', text: '供给侧改革'}, {year: '2021', text: '需求见顶'}],
        note: '<b>这是全行业需求收缩最直接的证据。</b>海螺水泥 2020 年 4.53 亿吨见顶，2025 年 2.70 亿吨，' +
              '<b>五年掉四成</b>；中国建材 2019 年 3.91 亿吨见顶，2025 年 2.17 亿吨，掉四成五。' +
              '<b>天山股份 2021 年从 2,146 万吨跳到 3.17 亿吨是资产重组</b>（中国建材注入中联 / 南方 / 西南水泥），' +
              '不是内生增长，跨 2020/2021 完全不可比。' +
              '天山与中国建材是<b>子公司口径 / 集团口径</b>，两条线任何情况下都不能相加。',
        detail: '<b>口径：</b>海螺取年报「水泥和熟料合计净销量」（2017 年起同时披露自产品销量，本图仍取合计）；' +
                '中国建材取年报「水泥及熟料销量」；天山取水泥销量 + 熟料销量（2017 年起分列）。' +
                '<b>产量不等于销量</b>，本页一律只取销量披露，没披露就断线，不用产量代替也不用收入 ÷ 价格倒算。<br>' +
                '<b>并购台阶：</b>中国建材 2018 年合并中材股份，销量从 2.89 亿吨跳到 3.69 亿吨；' +
                '并购年份的跳升与内生量变化混在一条线里，读趋势要跳过这些台阶年。<br>' +
                '<b>与全国产量对照：</b>全国水泥产量 2020 年约 23.8 亿吨、2024 年约 18.3 亿吨（降幅约两成），' +
                '而这三家降幅四成以上——<b>龙头的降幅大于全国</b>，说明它们在主动收缩而非抢份额。' +
                '（全国数据未入库，见页尾「本页缺什么」。）'
    },
    {
        id: 'sales-region', key: 'ops_sales_total_wt', scale: 1, unit: '万吨', decimals: 0, trim: true,
        codes: ['000401', '01313', '600801', '00743', '002233'],
        title: '水泥熟料销量——区域五家',
        sub: '冀东 / 华润建材科技 / 华新 / 亚洲水泥（中国）/ 塔牌，1,000—11,000 万吨区间，同图可直读',
        marks: [{year: '2016', text: '供给侧改革'}, {year: '2021', text: '需求见顶'}],
        note: '区域企业的量比龙头抗跌：华新水泥 2019 年 7,693 万吨 → 2025 年 6,196 万吨只掉两成' +
              '（海外产能与骨料业务撑住了发货），塔牌集团 2021 年 2,000 万吨 → 2025 年 1,674 万吨掉一成六。' +
              '<b>华润建材科技是本组降幅最大的</b>：2020 年 9,083 万吨 → 2025 年 5,542 万吨，' +
              '因为主战场广西 / 广东西部在 2021 年后新增产能与需求下滑同时到来。' +
              '冀东水泥 2020 年 10,733 万吨 → 2025 年 8,345 万吨，华北量降但赊销上升（见赊销强度图）。',
        detail: '<b>口径逐家不同，同图只比趋势与量级：</b>冀东、塔牌取「水泥 + 熟料」合计销量' +
                '（塔牌 2010—2012、2018—2019 年报没披露熟料外销量，这几年的点实为水泥销量；' +
                '冀东 2010—2011 年只有叙述里的含熟料合计「统计口径」5,681 / 7,193 万吨，2012 年起才有产销存表）；' +
                '华新取年报「水泥和熟料销售总量」（2010—2011 年年报自注为「统计 / 内部统计口径」，' +
                '2012 年起为财务口径，量级连续 3,476 → 4,228 → 4,235 万吨；' +
                '2023 年报没有这句合并表述，故 2023 年断点，' +
                '不用 5,818 + 372 倒算）；华润取水泥 + 熟料销量（2024 年起口径改为「水泥产品」含熟料不再分列）；' +
                '亚洲水泥（中国）取表一总销量统计。<br>' +
                '<b>亚洲水泥（中国）2025 年断线不是漏抓：</b>2025 年年报整本没有任何销量表，' +
                '正文只说「水泥销量同比下滑」，按不推算原则置空。<br>' +
                '<b>华润建材科技 2020—2022 年销量含向关联方销售</b> 430 / 460 / 400 万吨，' +
                '这部分是集团内部调拨，读份额时应意识到其中含非市场化销量。'
    },
    {
        id: 'unit-rev', key: 'ops_unit_rev', scale: 1, unit: '元/吨', decimals: 1, trim: true,
        title: '吨收入（水泥熟料含税前售价的会计口径）',
        sub: '= 水泥（熟料）业务收入 ÷ 水泥熟料销量，逐份年报手工算；八家都有，01313 的港元年份单列一条',
        marks: [{year: '2016', text: '价格谷底'}, {year: '2019', text: '价格峰值'}],
        extraSeries: [{code: '01313', key: 'ops_unit_rev_hkd', name: '华润建材科技（港元/吨，≤2022）', unit: '港元/吨'}],
        note: '<b>这就是水泥的「价」。</b>2010 年起点在 222—287 元/吨（华新 222、海螺 248、塔牌 287），' +
              '2016 年谷底集体落到 177—226 元/吨（冀东 177、海螺 198；' +
              '<b>华新是唯一最低点不在 2016 年的</b>——它 2016 年 226 元/吨还略高于自己 2010 年的 222），' +
              '2019 年峰值冲到 320—377 元/吨，2025 年回落到 228—258 元/吨（华新 353 是例外，见下）——' +
              '<b>已经跌回 2018 年以前，但仍比 2016 年谷底高约三成</b>（海螺 258 对 198），' +
              '供给侧改革抬起来的价格中枢并没有全部还回去。' +
              '华新水泥 2025 年 353 元/吨明显高于同业，是因为 2019 年起它的「水泥」行不含熟料（熟料单价低），' +
              '加上海外（中亚、非洲、阿曼）售价高，<b>不能直接读成它卖得贵</b>。',
        detail: '<b>为什么不用年报披露的「吨售价」：</b>中国建材、亚洲水泥（中国）、华润建材科技在管理层报告里' +
                '直接给过综合售价（数据文件里保留为 <code>ops_unit_price_disclosed</code>），但口径不一致——' +
                '亚洲水泥 2010—2012 年是<b>含税</b>价、2013 年起未标明；本图统一改用「分部/分产品收入 ÷ 销量」' +
                '自算，八家同一算法，可横比。<br>' +
                '<b>分子分母必须同口径：</b>海螺 2018 年起用<b>自产品</b>收入 ÷ 自产品销量（其营业收入含大宗贸易，' +
                '2023 年营业收入 1,409.99 亿而主营仅 864.07 亿，用营业收入会把吨价算高一倍）；' +
                '天山 2010—2016 年因「收入含熟料而销量不含对外熟料」<b>整段置空</b>，' +
                '冀东 2010—2011 年只有「水泥及熟料」合计销量而收入是水泥单品，同样置空（2012 年起产销存表分列才有线），' +
                '两处都不做估算。<br>' +
                '<b>华润建材科技的两条线：</b>该公司 2022 年及以前年报以<b>港元</b>呈列，2023 年首年改人民币并追溯重列 2022 年。' +
                '按项目规则不同币种不拼接，故港元年份单列一条点线（2022 年港元 358.7/吨，' +
                '2023 年报重列的人民币数是另一口径）。东财 F10 则把历年营收按年均汇率折成了人民币，与本图不同量纲。'
    },
    {
        id: 'unit-cost', key: 'ops_unit_cost', scale: 1, unit: '元/吨', decimals: 1, trim: true,
        title: '吨成本',
        sub: '= 水泥（熟料）业务营业成本 ÷ 销量；中国建材与亚洲水泥（中国）年报不披露分部成本，故无线',
        marks: [{year: '2021', text: '煤价暴涨'}],
        gapNote: '这两家年报的分部资料只披露水泥分部对外销售额、<b>从不披露分部成本</b>（不是本站没抓），' +
                 '而集团毛利率含玻纤 / 叶片 / 石膏板等非水泥业务，反推会失真，故按不推算原则留空。',
        extraSeries: [{code: '01313', key: 'ops_unit_cost_hkd', name: '华润建材科技（港元/吨，≤2022）', unit: '港元/吨'}],
        note: '<b>吨成本是水泥唯一能长期比出管理能力的指标。</b>2010 年在 168—203 元/吨（海螺 168、华新 174、塔牌 203），' +
              '2016 年谷底 133—168 元/吨（有 2010 年数据的三家，最低点都在 2016 年而不在起点），' +
              '2022 年煤价高点集体冲到 239—281 元/吨（天山 281、华新 255），2025 年回落到 173—235 元/吨。' +
              '<b>塔牌集团近三年最低</b>（2023—2025 年 208 / 189 / 173 元/吨），而 2016 年最低的是海螺' +
              '（133 元/吨，塔牌当年 163）——<b>成本座次是会换的</b>，看的是当期煤价敞口与产能利用率；' +
              '<b>天山股份重组后成本最高</b>（2022 年 281 元/吨），区域分散、老线多、运距长。',
        detail: '<b>成本结构：</b>煤炭 + 电力约占五到六成（熟料煅烧需 1,450℃），石灰石矿山与折旧各占一成多，' +
                '所以吨成本曲线的形状基本就是煤价曲线 + 产能利用率。销量下滑时折旧被摊到更少的吨数上，' +
                '<b>2024—2025 年吨成本降不下去的一半原因是量在跌</b>。<br>' +
                '<b>与年报披露的「综合成本」有差：</b>海螺与华润建材科技在年报里直接给过每吨成本' +
                '（<code>ops_unit_cost_disclosed</code>），海螺 2023 年披露 204.97 元/吨而本图自算 219.07 元/吨，' +
                '差约 14 元——披露值是<b>制造成本口径</b>，自算值是分部营业成本（含运费、包装等销售相关成本，' +
                '2020 年运费重分类后差额扩大）。两者各自跨年可比，不要混用。华润建材科技没有分部成本明细，' +
                '本图直接采用其年报「每吨成本结构图」的合计值。<br>' +
                '<b>为什么缺两家：</b>中国建材的分部资料只披露水泥分部<b>对外销售额</b>不披露分部成本，' +
                '亚洲水泥（中国）同样只有分部收入。<b>不用集团毛利率反推吨成本</b>（集团含玻纤、叶片、石膏板等），' +
                '故这两家的吨成本与吨毛利一律为空。'
    },
    {
        id: 'unit-gross', key: 'ops_unit_gross', scale: 1, unit: '元/吨', decimals: 1, trim: true,
        title: '吨毛利 = 吨收入 − 吨成本',
        sub: '水泥行业最核心的经营变量；六家有（中国建材 / 亚洲水泥（中国）无分部成本）',
        marks: [{year: '2019', text: '盈利峰值'}, {year: '2021', text: '需求见顶'}],
        gapNote: '同吨成本图——这两家年报只有分部收入、没有分部成本，吨毛利无法在同口径下算出，留空不猜。',
        extraSeries: [{code: '01313', key: 'ops_unit_gross_hkd', name: '华润建材科技（港元/吨，≤2022）', unit: '港元/吨'}],
        note: '<b>这张图解释了归母净利润为什么跌九成而收入只跌三五成。</b>' +
              '2010 年起点只有 48—84 元/吨（华新 48 是它自己十六年里的最低值），' +
              '2018—2019 年峰值：海螺 157 元/吨、天山 158、华新 148、塔牌 144；' +
              '2024—2025 年集体落到 <b>35—75 元/吨</b>（冀东 2023 年最低 24.5 元/吨；' +
              '华新 2025 年 118.5 元/吨是口径与海外业务造成的例外）——' +
              '吨毛利从峰值掉五到七成，而吨收入只掉三成，因为吨成本几乎没跟着降。' +
              '按 2025 年海螺 71.6 元/吨 × 2.70 亿吨 ≈ 193 亿元毛利，覆盖费用后所剩极薄，' +
              '<b>这就是「量价齐跌 + 成本刚性」在报表上的最终形态</b>。',
        detail: '<b>吨毛利 × 销量 ≈ 毛利总额</b>，所以本图与销量两图配合，可以把利润变动拆成量、价、成本三项贡献。' +
                '例：海螺 2021 → 2025 年吨毛利 161 → 72 元/吨（−55%）、销量 4.53 → 2.70 亿吨（−40%），' +
                '两者相乘即毛利掉七成三，与归母净利润跌九成的差额是费用刚性与减值。<br>' +
                '<b>为什么与毛利率图不完全同形：</b>毛利率是比值（含其他业务与贸易），吨毛利是绝对额且只含水泥口径；' +
                '毛利率能跨八家比，吨毛利能算钱。两张一起看：<b>毛利率判断景气位置，吨毛利判断赚不赚钱</b>。<br>' +
                '<b>华新水泥 2025 年 118.5 元/吨为六家最高</b>，主要是口径（水泥行不含熟料）与海外业务，' +
                '不宜直接读成经营效率领先；<b>跨 2018/2019 有口径缝</b>（2019 年起水泥与熟料分列）。'
    },
    {
        id: 'gross-margin', key: 'gross_margin', scale: 1, unit: '%', decimals: 2,
        title: '销售毛利率',
        sub: '东财主要指标口径（XSMLL），港股为 GROSS_PROFIT ÷ 收入；八家可同图直读，本页最可比的一张图',
        marks: [{year: '2016', text: '停止新增产能'}, {year: '2021', text: '煤价暴涨'}],
        note: '<b>八家唯一同口径可比的景气指标：</b>比值不受口径与规模影响，' +
              '八家都有（吨毛利缺中国建材与亚洲水泥（中国），故两张要对着看）。' +
              '2018—2019 年集体冲到 35%—40%（限产 + 需求尚在），2024 年集体落到 10%—25%。' +
              '<b>2021 年的背离值得注意：</b>当年水泥价格创历史新高，但煤炭价格同步暴涨，毛利率已经先于价格见顶回落。',
        detail: '<b>成本结构：</b>吨成本里煤炭 + 电力约占五到六成（熟料煅烧需 1,450℃），石灰石矿山与折旧各占一成多。' +
                '所以水泥的毛利率同时受<b>水泥价格</b>与<b>煤价</b>两头挤压，看毛利率不能只看限产强度。' +
                '自有矿山比例高、有余热发电与替代燃料（垃圾、生物质）的企业成本更抗跌。<br>' +
                '<b>区域差异：</b>塔牌集团在粤东、亚洲水泥（中国）在长江中下游与四川，区域协同好、外来冲击少时毛利率显著高于全国均值；' +
                '而华北（冀东）长期是产能过剩最严重的区域，同期毛利率系统性偏低。<br>' +
                '<b>互校：</b>本页数据同时保留了按「（营业收入 − 营业成本）÷ 营业收入」自算的 <code>gross_margin_calc</code>，' +
                '八家逐年与接口值一致（已核 FY2025 全部吻合到小数后 4 位），说明接口口径就是营业成本项。'
    },
    {
        id: 'roe', key: 'roe_weighted', scale: 1, unit: '%', decimals: 2,
        title: '净资产收益率（ROE）',
        sub: 'A 股为加权平均 ROE（ROEJQ），港股为接口 ROE_AVG（期初期末均值），两者算法不完全一致',
        marks: [{year: '2019', text: 'ROE 峰值'}],
        note: '2018—2019 年海螺、华新、华润建材都做到 20%—36%，2024—2025 年普遍掉到 5% 以下，天山与中国建材转负。' +
              '<b>口径提醒：</b>A 股「加权平均」按净资产时间加权，港股 ROE_AVG 为期初期末均值，横比只看量级与方向。',
        detail: '<b>杜邦分解：</b>水泥的 ROE 主要由净利率驱动（周期性），总资产周转率长期在 0.3—0.9 之间波动、' +
                '本页单列一图；权益乘数则取决于扩张期的举债强度——净现金型企业（海螺、塔牌）权益乘数低，' +
                '所以景气顶部的 ROE 反而不如高杠杆同业，但底部不亏钱。<b>看水泥的 ROE 必须看整轮周期的平均值，' +
                '单年 ROE 没有可比性。</b><br>' +
                '<b>不要用 total_equity 反推：</b>接口 <code>total_equity</code> 是股东权益合计含少数股东权益，' +
                '天山股份与冀东水泥的少数股东权益占比很高（区域子公司普遍有地方国资或原股东参股），' +
                '拿合计做分母会显著低估归母 ROE；数据文件保留了 <code>parent_equity</code> 与 <code>minority_equity</code>。'
    },
    {
        id: 'net-cash', key: 'net_cash', scale: 1e8, unit: '亿元', decimals: 0,
        title: '净现金 =（货币资金 + 交易性金融资产）− 有息负债',
        sub: '正值为账上现金多于全部借款；仅 A 股五家（港股 F10 无负债明细科目）',
        marks: [{year: '2016', text: '供给侧改革'}, {year: '2021', text: '需求见顶'}],
        redline: {value: 0, text: '0 = 净现金 / 净负债分界'},
        note: '<b>这张图是水泥行业最大的分化：</b>海螺水泥 2011 年还是净负债 145 亿，2021 年峰值净现金 820 亿，' +
              '2025 年仍有 367 亿；塔牌集团 2016—2023 年账上<b>一分钱借款都没有</b>，2025 年净现金 51 亿。' +
              '反面是天山股份 2025 年净负债 1,035 亿、华新水泥 −159 亿、冀东水泥 −132 亿。' +
              '<b>周期底部能不能熬，看的是这条线而不是利润。</b>',
        detail: '<b>算法：</b>（货币资金 <code>monetaryfunds</code> + 交易性金融资产 <code>trade_finasset</code>）' +
                '−（短期借款 + 一年内到期非流动负债 + 应付短期债券 + 长期借款 + 应付债券）。' +
                '不剔除受限资金（保证金、承兑保证金），也不计入长期理财与结构性存款，' +
                '因此这是一个<b>偏保守但可跨年一致</b>的口径。<br>' +
                '<b>零负债年份不是缺口：</b>塔牌集团 2016—2023 年接口里所有借款科目都不返回，' +
                '抓取脚本在资产负债表存在时把缺失的有息负债科目认定为 0（否则这些年会画成断线），' +
                '所以塔牌那几年的净现金就等于账上现金。<br>' +
                '<b>为什么水泥能攒出净现金：</b>2016 年后停止新增产能，行政上不允许扩产能，' +
                '龙头的经营现金流没有资本开支去处，只能沉淀成现金或分红——这与地产「越赚越要拿地」的资金循环完全相反。' +
                '天山股份是例外，因为 2021 年资产重组注入的是<b>带债务的水泥平台</b>，负债随资产一起并进来。'
    },
    {
        id: 'net-gearing', key: 'net_gearing', scale: 1, unit: '%', decimals: 2,
        title: '净负债率 = 净负债 ÷ 股东权益',
        sub: '负值表示净现金；仅 A 股五家。与地产「三道红线」的净负债率同口径，可与开发商直接对比',
        marks: [{year: '2016', text: '供给侧改革'}],
        redline: {value: 0, text: '0 = 净现金'},
        note: '把上一张图除以权益后可跨规模比较：2011 年五家都是净负债（冀东 124%、天山 95%），' +
              '2018 年后海螺与塔牌转为净现金并越攒越多（2025 年 −18% / −42%），' +
              '天山从 2021 年的 72% 一路升到 2025 年的 113%。' +
              '<b>与下游对照：</b><a href="../realestate/peers.html">开发商</a>的净负债率红线是 100%，' +
              '水泥龙头长期在负值区间——这是上游相对下游的资产负债表优势。',
        detail: '<b>算法：</b>净负债（= 有息负债 − 现金类资产）÷ 股东权益合计 <code>total_equity</code>，' +
                '分母含少数股东权益与永续债，与地产页的自算口径一致（因此两页可以直接比）。<br>' +
                '<b>不要与资产负债率混读：</b>资产负债率 <code>debt_ratio</code> 把经营性负债（应付账款、' +
                '应付工程款）也算进去，水泥企业对上游煤炭、工程方的占款不小，' +
                '所以会出现「资产负债率 30% 但净负债率是负数」的组合——前者衡量总负债结构，后者只看带息的钱。<br>' +
                '<b>权益资产比是另一面：</b>本页单列一图；净现金型企业（海螺 79.6%、塔牌 89.8%）与' +
                '高杠杆型（天山 33.2%、中国建材 38.1%）差出两倍以上。'
    },
    {
        id: 'heavy-asset', key: 'heavy_asset_ratio', scale: 1, unit: '%', decimals: 2,
        title: '重资产度 =（固定资产 + 在建工程）÷ 总资产',
        sub: '衡量产能沉没在窑炉与矿山里的比例；仅 A 股五家',
        marks: [{year: '2016', text: '停止新增产能'}],
        note: '水泥是典型重资产：2011 年五家都在 55%—67%，此后随着停止新增产能、现金与金融资产堆积，' +
              '海螺从 56.6% 降到 2025 年 38.6%、塔牌降到 24.4%，而冀东仍有 53.5%、天山 47.5%。' +
              '<b>这个比例越低不代表越落后</b>，多半是分母（现金、投资）变大而不是分子缩水。',
        detail: '<b>为什么重资产决定了周期形态：</b>一条 5,000 吨/日熟料线投资十几亿、寿命二三十年，' +
                '建成后折旧与矿山摊销是刚性的。需求下滑时企业宁可降价保开工率也不愿停窑，' +
                '这就是水泥价格战一旦开打就极其惨烈、必须靠<b>行政限产 / 错峰生产</b>才能收敛的根本原因。<br>' +
                '<b>与地产的对照：</b>开发商的资产是存货（可售房源），可以靠降价去化换回现金；' +
                '水泥的资产是窑炉，退出成本极高、不可转换——所以水泥的供给侧出清必须靠政策，地产靠市场。<br>' +
                '<b>口径：</b>固定资产 <code>fixed_asset</code> + 在建工程 <code>cip</code>；' +
                '不含使用权资产 <code>useright_asset</code> 与矿山采矿权（后者在无形资产 <code>intangible_asset</code> 里）。'
    },
    {
        id: 'capex', key: 'capex_ratio', scale: 1, unit: '%', decimals: 2,
        title: '资本开支强度 = 购建固定资产等支付的现金 ÷ 营业收入',
        sub: '看扩张意愿；仅 A 股五家（港股 F10 无现金流量表明细）',
        marks: [{year: '2016', text: '停止新增产能'}],
        note: '2011 年扩产高峰：天山 38.6%、冀东 30.0%、海螺 17.0%。2016 年后新增产能被行政关闭，' +
              '强度降到个位数（2018 年天山仅 0.5%、冀东 2.6%）。' +
              '2021 年后又回到 6%—19%，但钱不再投熟料线，而是投<b>骨料、混凝土、海外产能与光伏/储能</b>。',
        detail: '<b>看这张图要配合营收下滑读：</b>2024—2025 年分母（营收）已经腰斩，' +
                '所以 10% 左右的强度对应的绝对金额比 2011 年的 17% 还小。判断真实扩张请看数据文件里的' +
                '<code>construct_long_asset</code>（购建固定资产、无形资产和其他长期资产支付的现金，绝对额）。<br>' +
                '<b>华新水泥是唯一的例外</b>：2021 年 19.2% 主要投向中亚（乌兹别克、塔吉克）、非洲（赞比亚、' +
                '马拉维、莫桑比克）与阿曼的海外产能，这也是它营收下滑幅度小于同业、但净负债走高的原因。<br>' +
                '<b>口径：</b>该现金流项含无形资产（矿权）与其他长期资产，不是纯产能投资；' +
                '并购支付的现金走「投资活动」其他项，不在此列，因此天山 2021 年的资产注入在这张图上看不到。'
    },
    {
        id: 'recv', key: 'recv_ratio', scale: 1, unit: '%', decimals: 2,
        title: '赊销强度 =（应收票据 + 应收账款）÷ 营业收入',
        sub: '水泥以现款现货为传统，这个比例上升意味着经营质量恶化；仅 A 股五家',
        marks: [{year: '2021', text: '需求见顶'}],
        note: '<b>本页最能区分「谁在硬撑销量」的一张图。</b>塔牌集团常年 0.4%—5%（几乎纯现款现货），' +
              '海螺 2025 年 10.6%；而天山股份从 2021 年 19.6% 升到 2025 年 <b>35.7%</b>——' +
              '意味着三分之一以上的年收入还挂在账上没收回，客户结构里基建与国企项目占比高、账期长。' +
              '冀东 2018 年曾达 41.6%，是当时华北市场恶性竞争的直接证据。',
        detail: '<b>为什么水泥的赊销特别危险：</b>产品单价低（几百元/吨）、客户是搅拌站与工程方，' +
                '一旦下游（尤其地产项目）出问题，应收账款几乎无法通过抵押物回收，只能计提信用减值。' +
                '数据文件保留了 <code>credit_impairment</code>（信用减值损失）与 <code>asset_impairment</code>，' +
                '把赊销强度和信用减值一起看，才知道这些应收有多少最终收不回来。<br>' +
                '<b>票据与账款要合看：</b>只看应收账款会低估，因为不少企业用商业承兑票据结算；' +
                '本图分子取接口的 <code>note_accounts_rece</code>（应收票据及应收账款合计）。' +
                '<b>还有一条暗线：</b>应收款项融资 / 已贴现票据不在表内，' +
                '数据文件的 <code>finance_rece</code>（应收款项融资）可作补充观察。'
    },
    {
        id: 'expense', key: 'expense_ratio', scale: 1, unit: '%', decimals: 2,
        title: '期间费用率 =（销售 + 管理 + 研发 + 财务费用）÷ 营业收入',
        sub: '仅 A 股五家。跨 2018 年读要注意环保税改变了税金及附加与成本的归属',
        marks: [{year: '2018', text: '环保税法实施'}, {year: '2021', text: '需求见顶'}],
        note: '景气顶部被摊薄（海螺 2018 年 5.5%、2021 年 5.1%），需求下滑后分母缩小、费用刚性，' +
              '2025 年集体回到 11%—18%。冀东水泥长期最高（2018 年 21.8%），' +
              '海螺长期最低——<b>费用率的排序几十年基本不变，反映的是管理效率而非周期。</b>',
        detail: '<b>口径与断点：</b>2018 年《环境保护税法》实施后，原排污费从「管理费用」' +
                '改为环保税计入<b>税金及附加</b>（不在本图分子内），因此 2018 年前后的费用率有一个' +
                '不大但真实的口径下移，跨该年比较时不要全读成降本。<br>' +
                '<b>财务费用会反向：</b>净现金型企业（海螺、塔牌）的利息收入使财务费用为负，' +
                '直接压低费用率——所以这张图对净现金企业是「双重优待」，横比时要意识到其中一部分来自资产负债表而非运营。<br>' +
                '<b>研发费用：</b>2018 年后单列（<code>research_expense</code>），水泥企业的研发主要是' +
                '替代燃料、余热发电与低碳熟料，占收入通常不到 1%，对费用率影响有限。'
    },
    {
        id: 'asset-turnover', key: 'asset_turnover', scale: 1, unit: '次', decimals: 2,
        title: '总资产周转率',
        sub: '八家都有。杜邦分解里唯一能直接看「产能利用率」的代理指标',
        marks: [{year: '2021', text: '需求见顶'}],
        note: '2018 年海螺做到 0.95 次、华新 0.86 次，2025 年八家全部掉到 0.26—0.47 次，' +
              '<b>几乎腰斩</b>——同样的窑炉资产只产出一半的收入，这就是当前水泥低盈利的直接来源。' +
              '华新水泥 2025 年 0.47 次为八家最高（海外与骨料业务支撑）。',
        detail: '<b>为什么可以当产能利用率读：</b>水泥的资产几乎全是产能（见重资产度图），' +
                '收入 ≈ 销量 × 价格，所以周转率同时被销量与价格拖累，' +
                '下滑幅度大于全国水泥产量的降幅（后者只含量、不含价）。<br>' +
                '<b>口径：</b>A 股取东财主要指标 <code>TOTALASSETS_TURNOVER</code>（营业总收入 ÷ 平均总资产），' +
                '港股取 <code>TOTAL_ASSETS_TURNOVER</code>；两者都是「次/年」。' +
                '海螺与塔牌的分母含大额现金与金融资产，会系统性压低它们的周转率——' +
                '<b>这张图对净现金企业不利，与净负债率图正好相反，两张要对着看。</b>'
    },
    {
        id: 'inventory-days', key: 'inventory_days', scale: 1, unit: '天', decimals: 1,
        title: '存货周转天数',
        sub: '仅 A 股五家。水泥不可长期库存，天数主要由煤炭与备品备件构成',
        note: '常年在 24—65 天，2018 年景气高点海螺压到 23.8 天，2024—2025 年普遍升到 45—65 天。' +
              '<b>不要按其他行业的直觉读：</b>水泥熟料保质期只有一两个月，存货里真正的成品占比很小，' +
              '主要是<b>原煤、石灰石堆场与备品备件</b>，天数上升更多反映燃料备货策略与减产后的库存滞留。',
        detail: '<b>与地产的对照最有意思：</b>开发商的存货周转天数以千天计（土地 + 在建 + 现房），' +
                '水泥以几十天计——同一条产业链上，上游是快周转的制造业，下游是慢周转的资产持有业务，' +
                '这解释了为什么下行期水泥企业的现金流恶化远慢于开发商。<br>' +
                '<b>口径：</b>东财 <code>INVENTORY_TDAYS</code>（360 ÷ 存货周转率，分母用平均存货），' +
                '与自算的 <code>inventory_turnover</code> 互为倒数关系；港股 F10 无存货科目，故三家港股不在此图。'
    },
    {
        id: 'equity-ratio', key: 'equity_asset_ratio', scale: 1, unit: '%', decimals: 2,
        title: '权益资产比 = 股东权益 ÷ 总资产',
        sub: '八家都有。与资产负债率互补（相加 = 100%），本页选权益视角以便与净现金图同向阅读',
        note: '分化极大且稳定：塔牌 2025 年 89.8%、亚洲水泥（中国）85.7%、海螺 79.6%，' +
              '而天山股份 33.2%、中国建材 38.1%。<b>方向与净负债率图完全一致</b>，' +
              '互为印证：账上净现金的公司权益占比高，靠并购做大的平台权益占比低。',
        detail: '<b>含少数股东权益：</b>分子取 <code>total_equity</code>（股东权益合计），' +
                '天山股份与冀东水泥的区域子公司普遍有地方国资参股，少数股东权益占比高，' +
                '若改用归母权益 <code>parent_equity</code> 这两家会更低；数据文件两个字段都保留了。<br>' +
                '<b>与资产负债率的关系：</b>本图 + <code>debt_ratio</code> = 100%（接口自算偶有 0.02% 的舍入差），' +
                '所以看哪一个都行；用权益视角是为了让「越高越稳健」与净现金图的方向一致，避免读图时反向。<br>' +
                '<b>不是监管指标：</b>水泥没有地产那样的三道红线，权益资产比高低本身是<b>权衡</b>——' +
                '2011 年前后的高杠杆换来了产能扩张，2018 年后的低杠杆换来了熬周期的能力。'
    },
    {
        id: 'ocf', key: 'netcash_operate', scale: 1e8, unit: '亿元', decimals: 0,
        title: '经营活动现金流净额',
        sub: '八家都有。水泥的现金流质量长期好于利润，是这个行业最被低估的特征',
        marks: [{year: '2018', text: '盈利与现金流高点'}],
        note: '2018 年海螺 361 亿、中国建材 485 亿；2025 年海螺仍有 166 亿、中国建材 225 亿、天山 123 亿——' +
              '<b>天山与中国建材当年归母净利润是亏的，经营现金流却是大额正数</b>，' +
              '差额主要是折旧摊销（重资产）与资产减值这些不出现金的成本。',
        detail: '<b>为什么现金流好于利润：</b>水泥的成本里折旧与矿山摊销占比大（重资产度 25%—53%），' +
                '这部分成本不流出现金；加上传统上现款现货、预收货款结算，所以经营现金流长期高于净利润。' +
                '数据文件的 <code>ocf_to_revenue</code>（经营现金流 ÷ 营收）可直接看这个含量。<br>' +
                '<b>看现金流要减掉维持性资本开支：</b>窑炉要持续技改与矿山剥离，' +
                '把本图与资本开支强度图相减才是可自由分配的现金——这也是海螺能长期净现金 + 高分红的来源。<br>' +
                '<b>反例是赊销：</b>天山股份 2025 年赊销强度 35.7%，经营现金流靠的是压上游账期（应付票据与账款），' +
                '<b>不是收回了自己的钱</b>；数据文件有 <code>note_accounts_payable</code> 可以对照。'
    },
    {
        id: 'dividend', key: 'dividend_per10', fromDividend: true, scale: 1, unit: '元', decimals: 2,
        title: '每 10 股派现（税前）',
        sub: '仅 A 股五家（东财 A 股分红实施明细接口不覆盖港股）。中期与末期分红按年度合并',
        marks: [{year: '2016', text: '停止新增产能'}],
        note: '<b>停止新增产能的直接后果就是分红。</b>产能审批被关上后，龙头的经营现金流没有扩产去处，' +
              '海螺的每 10 股派现从 2011 年前后的一元级抬到 2018—2021 年的十元级；' +
              '塔牌集团在净现金 + 零负债的状态下也是持续高派现。',
        detail: '<b>口径：</b>东财 <code>RPT_SHAREBONUS_DET</code> 的税前每 10 股派现（<code>PRETAX_BONUS_RMB</code>），' +
                '按分红所属年度归集，一年内多次分红（中期 + 末期）已合并。<b>不是股息率</b>——' +
                '股息率还要除以股价，本站不含行情数据。<br>' +
                '<b>与分红率一起读：</b>2024—2025 年多家分红率（派现 ÷ 归母净利润）大幅抬升，' +
                '主要是分母下滑所致，不宜直接读成加大回报；亏损年份仍能分红的公司靠的是账上净现金与未分配利润。<br>' +
                '<b>港股三家：</b>接口只给派息比率 <code>dividend_payout</code>（小数，非百分数），' +
                '在数据文件里逐年可查，未画成图。'
    }
];

function fmt(v, decimals) {
    if (v === null || v === undefined) return '—';
    return v.toLocaleString('zh-CN', {minimumFractionDigits: decimals, maximumFractionDigits: decimals});
}

function buildChart(cfg, peers, focus) {
    // 全部公司的年份并集，升序；1993—1999 年只有华新/冀东/天山的零散点，统一从 2000 年起画（完整历史仍在 JSON 里）
    const scope = cfg.codes || ORDER;
    const yearSet = new Set();
    for (const code of scope) {
        const p = peers[code];
        if (!p) continue;
        for (const y of Object.keys(cfg.fromDividend ? (p.dividend_per10 || {}) : p.annual)) {
            if (+y >= 2000) yearSet.add(y);
        }
    }
    let years = Array.from(yearSet).sort();

    const series = [], missing = [], unitOf = {};
    scope.filter(c => peers[c]).forEach(code => {
        const p = peers[code];
        const hk = HK_CODES.includes(code);
        const src = cfg.fromDividend ? (p.dividend_per10 || {}) : p.annual;
        const s = {
            name: p.name,
            type: 'line',
            symbol: 'circle',
            symbolSize: 6,
            connectNulls: false,
            lineStyle: {
                width: focus && focus !== code ? 1.5 : 2.6,
                opacity: focus && focus !== code ? 0.45 : 1,
                type: hk ? 'dashed' : 'solid'
            },
            itemStyle: {color: COLORS[code], opacity: focus && focus !== code ? 0.5 : 1},
            emphasis: {focus: 'series'},
            data: years.map(y => {
                const v = cfg.fromDividend ? src[y] : (src[y] ? src[y][cfg.key] : null);
                return (v === null || v === undefined) ? null : +(v / cfg.scale).toFixed(cfg.decimals + 2);
            })
        };
        // 整条全空的公司不进图例（港股 F10 未披露的科目），改在注释里说明缺口
        if (s.data.some(v => v !== null)) series.push(s); else missing.push(code);
    });
    // 另一币种 / 另一披露口径的序列单列，绝不与主序列拼成一条（华润建材科技 2022 年及以前为港元年报）
    (cfg.extraSeries || []).forEach(ex => {
        const p = peers[ex.code];
        if (!p) return;
        const data = years.map(y => {
            const v = p.annual[y] ? p.annual[y][ex.key] : null;
            return (v === null || v === undefined) ? null : +(v / cfg.scale).toFixed(cfg.decimals + 2);
        });
        if (!data.some(v => v !== null)) return;
        unitOf[ex.name] = ex.unit || cfg.unit;
        series.push({
            name: ex.name,
            type: 'line',
            symbol: 'triangle',
            symbolSize: 8,
            connectNulls: false,
            lineStyle: {
                width: focus && focus !== ex.code ? 1.5 : 2.2,
                opacity: focus && focus !== ex.code ? 0.45 : 1,
                type: 'dotted'
            },
            itemStyle: {color: COLORS[ex.code], opacity: focus && focus !== ex.code ? 0.5 : 1},
            emphasis: {focus: 'series'},
            data: data
        });
    });
    // 手工层只覆盖近十几年，裁掉首尾全空的年份列，避免 x 轴拖出一大段空白
    if (cfg.trim && series.length) {
        const hasAny = i => series.some(s => s.data[i] !== null);
        let lo = 0, hi = years.length - 1;
        while (lo < years.length && !hasAny(lo)) lo++;
        while (hi > lo && !hasAny(hi)) hi--;
        if (lo > 0 || hi < years.length - 1) {
            years = years.slice(lo, hi + 1);
            series.forEach(s => { s.data = s.data.slice(lo, hi + 1); });
        }
    }
    // 政策/景气断点竖线 + 阈值横线（净现金分界）：只挂在第一条 series 上，避免每家重复画
    if (series.length && (cfg.marks || cfg.redline)) {
        const lines = (cfg.marks || [])
            .filter(m => years.includes(m.year))
            .map(m => ({xAxis: m.year, label: {formatter: m.text}}));
        if (cfg.redline) {
            lines.push({
                yAxis: cfg.redline.value,
                lineStyle: {color: '#dc2626', width: 1.8, type: 'solid'},
                label: {formatter: cfg.redline.text, position: 'insideStartTop', color: '#dc2626'}
            });
        }
        series[0].markLine = {
            silent: true,
            symbol: 'none',
            lineStyle: {type: 'dashed', color: '#9ca3af', width: 1.4},
            label: {position: 'insideEndTop', fontSize: 13, color: '#6b7280'},
            data: lines
        };
    }

    const gapNote = missing.length
        ? `<br><b>本图无 ${missing.map(c => peers[c].name).join('、')} 序列：</b>` +
          (cfg.gapNote
              || (missing.every(c => HK_CODES.includes(c))
              ? (cfg.fromDividend
                  ? '东财 A 股分红实施明细接口（RPT_SHAREBONUS_DET）不覆盖港股，三家港股公司只有派息比率字段 dividend_payout。'
                  : '东财港股 F10 主要指标接口只给营收、利润、毛利率、ROE、资产负债率与现金流量净额，' +
                    '不提供资产负债表与现金流量表的明细科目（货币资金、有息负债、固定资产、在建工程、应收票据、存货、' +
                    '期间费用均无），故这几张图上没有中国建材 / 华润建材科技 / 亚洲水泥（中国）的线。')
              : '接口该字段全年无值。'))
        : '';
    const wrap = document.createElement('div');
    wrap.className = 'chart-card';
    wrap.innerHTML = `
        <div class="chart-title">${cfg.title}<span class="sub">${cfg.sub}</span></div>
        <div class="chart-box" id="chart-${cfg.id}"></div>
        <div class="note">${cfg.note}${gapNote}${cfg.detail
            ? `<details class="note-more"><summary>展开详细口径与机制</summary><div>${cfg.detail}</div></details>`
            : ''}</div>`;
    chartsEl.value.appendChild(wrap);

    const chart = echarts.init(wrap.querySelector('.chart-box'));
    chart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: {type: 'line'},
            formatter: function (ps) {
                const rows = ps.filter(p => p.value !== null && p.value !== undefined)
                    .sort((a, b) => b.value - a.value)
                    .map(p => `${p.marker}${p.seriesName}　<b>${fmt(p.value, cfg.decimals)}</b> ${unitOf[p.seriesName] || cfg.unit}`);
                return `<b>${ps[0].axisValue} 年</b><br>` + (rows.length ? rows.join('<br>') : '无数据');
            }
        },
        legend: {top: 0, itemGap: 18, textStyle: {fontSize: 15}},
        grid: {left: 78, right: 40, top: 46, bottom: 40},
        xAxis: {
            type: 'category',
            data: years,
            axisLabel: {fontSize: 14, rotate: years.length > 18 ? 45 : 0},
            axisTick: {alignWithLabel: true}
        },
        yAxis: {
            type: 'value',
            name: cfg.unit,
            nameTextStyle: {fontSize: 14},
            axisLabel: {fontSize: 14, formatter: v => v.toLocaleString('zh-CN')},
            splitLine: {lineStyle: {type: 'dashed', color: '#e5e7eb'}}
        },
        series: series
    });
    charts.push(chart);
}

onMounted(async () => {
  try {
    const peers = await apiGet(API)
    loading.value = false
    const focus = new URLSearchParams(window.location.search).get('focus')
    for (const cfg of CHARTS) buildChart(cfg, peers, ORDER.includes(focus) ? focus : null)

    // A 股五家口径说明（caliber_note 一致，取首家展示）
    const A_CODES = ['600585', '000877', '600801', '000401', '002233'];
    const first = peers[A_CODES.find(c => peers[c])];
    if (first && first.caliber_note) {
        const d = document.createElement('details');
        d.className = 'note';
        d.innerHTML = `<summary>A 股五家（海螺 / 天山 / 华新 / 冀东 / 塔牌）口径与来源说明</summary>
            <div>${first.caliber_note}</div>
            <div>${first.unit_note || ''}　来源：${first.source || ''}</div>
            <div>抓取脚本：<code>data/extract/fetch_cement_financials.py</code>，落盘
            <code>data/tables/cement_&lt;code&gt;_annual.json</code>，后端接口 <code>/api/cement_peers</code>。
            海螺水泥（A 600585 / H 00914）与华新水泥（A 600801 / H 06655）两地上市，
            按项目规则同一年份优先取 <b>A 股年报</b>口径。</div>
            <div><b>零负债年份的处理：</b>塔牌集团 2016—2023 年账上没有任何借款与应付债券，接口表现为
            「所有有息负债科目缺失」，与「本年没抓到资产负债表」长得一样。脚本在总资产非空时把缺失的负债科目
            认定为 0，否则净现金 / 净负债率会在这些年出现<b>假缺口</b>。同样原因，现金短债比
            （<code>cash_short_debt</code>）在零负债年份为空、在接近零负债的年份会爆到几百上千倍
            （塔牌 2023 年 1,795 倍），对水泥没有比较意义，<b>本页未画该指标</b>。</div>`;
        chartsEl.value.appendChild(d);
    }

    // 港股三家走另一套接口，口径说明单列
    const hkFirst = peers[HK_CODES.find(c => peers[c])];
    if (hkFirst) {
        const d = document.createElement('details');
        d.className = 'note';
        d.innerHTML = `<summary>港股三家（中国建材 / 华润建材科技 / 亚洲水泥（中国））口径与来源说明</summary>
            <div>${hkFirst.caliber_note || ''}</div>
            <div>${hkFirst.unit_note || ''}　来源：${hkFirst.source || ''}</div>
            <div><b>币种：</b>东财港股 F10 行内一律写 <code>CURRENCY="HKD"</code>、<code>IS_CNY_CODE=0</code>，
            这个标记<b>不可信</b>——金额是年报本位币原值、未做折算，而这三家<b>年报都以人民币编制</b>
            （已用量级反查：中国建材 2025 年营收 1,778.47 亿 / 归母 −37.45 亿，华润建材科技 210.55 亿 / 4.79 亿，
            亚洲水泥（中国）51.09 亿 / 0.857 亿，均与人民币披露口径一致）。因此本页金额类图表可直接比大小；
            <b>但这是量级反查而非逐份年报核对</b>，引用具体数字前建议回原文确认。</div>
            <div><code>roe_weighted</code> 取接口 <code>ROE_AVG</code>（期初期末净资产均值），与 A 股「加权平均 ROE」
            算法不同；<code>asset_turnover</code> 为本脚本按「营收 ÷ 期初期末总资产均值」自算；
            <code>dividend_payout</code>（派息比率）为小数不是百分数。
            <code>RPT_HKF10_FN_BALANCE</code> 是 STD_ITEM_CODE 长表需逐项 pivot，暂未采用，
            所以净现金、重资产度、赊销强度等图上没有这三家。</div>`;
        chartsEl.value.appendChild(d);
    }

    // 吨指标手工层（年报提取）的口径与来源，八家共用一份，单列一块
    const opsFirst = peers[ORDER.find(c => peers[c] && peers[c].ops_meta)];
    if (opsFirst) {
        const om = opsFirst.ops_meta;
        const rows = ORDER.filter(c => peers[c] && peers[c].ops_meta).map(c => {
            const m = peers[c].ops_meta;
            return `<li><b>${peers[c].name} ${c}</b>（${m.years || ''}，${m.currency || 'CNY'}）：` +
                   `销量取<b>${m.sales_key || '—'}</b>；收入口径：${m.rev_caliber || '—'}<br>` +
                   `吨指标算法：${m.unit_rule || '—'}` +
                   (m.breaks ? `<br><b>断点：</b>${m.breaks}` : '') + '</li>';
        }).join('');
        const d = document.createElement('details');
        d.className = 'note';
        d.innerHTML = `<summary>销量 / 吨收入 / 吨成本 / 吨毛利：年报手工提取层的口径与逐家断点（八家）</summary>
            <div>${om.caliber_note || ''}</div>
            <div>${om.unit_note || ''}　来源：${om.source || ''}</div>
            <div>落盘 <code>data/tables/cement_ops_manual.json</code>（行业级单文件，与
            <code>fetch_cement_financials.py</code> 抓的 <code>cement_&lt;code&gt;_annual.json</code> 分离，
            重跑抓取脚本不会覆盖手工数据）；吨指标不落盘，由后端
            <code>_cement_ops_year()</code> 在 <code>/api/cement_peers</code> 里按各家口径现算，
            数据文件只存年报原值。<b>A+H 两地上市的海螺、华新一律取 A 股年报</b>；
            <b>取数四条铁律：</b>只用披露销量（产量不代替）、逐年取该年年报本期数（不用后年重述数）、
            分子分母口径必须一致（不一致就整段置空）、没披露就是空（不插值不倒算）。</div>
            <div><b>逐家口径：</b><ul>${rows}</ul></div>
            <div><b>本层还抓了但未画图的字段：</b>骨料销量 <code>ops_agg_sales_wt</code>（万吨，华新 2025 年 16,069 万吨、
            中国建材 13,956、天山 12,660，量级已超部分公司的水泥销量）、商品混凝土销量
            <code>ops_concrete_sales_wm3</code>（万立方米）、水泥与熟料分列销量
            <code>ops_sales_cement_wt</code> / <code>ops_sales_clinker_wt</code>、
            年报直接披露的吨售价与吨成本 <code>ops_unit_price_disclosed</code> / <code>ops_unit_cost_disclosed</code>、
            以及每条记录的年报页码 <code>ops_page</code> 与逐年备注 <code>ops_note</code>（可回原文核对）。</div>`;
        chartsEl.value.appendChild(d);
    }

    // 行业级缺口：全国产量与区域价格
    const gap = document.createElement('details');
    gap.className = 'note';
    gap.innerHTML = `<summary>本页缺什么：全国产量、区域价格与产能利用率</summary>
        <div><b>全国水泥产量</b>（判断需求中枢的分母）来自国家统计局，
        <code>data.stats.gov.cn</code> 对脚本请求返回 403，本地也没有对应的统计年鉴 PDF，故本页未纳入。
        替代读法：用本页销量图与<a href="../realestate/peers.html">开发商</a>的新开工/营收对照看相对强弱。</div>
        <div><b>区域水泥价格指数</b>（如数字水泥网 / 卓创的 P.O42.5 到位价）是判断区域协同的直接指标，
        属付费数据源，本站不含。本页的吨收入是<b>年度会计口径均价</b>，已含结构（水泥/熟料/海外占比）影响，
        不能当作某个区域的市场价读。</div>
        <div><b>产能与产能利用率</b>：年报披露的多是设计产能或熟料产能（口径逐家不同，且常与在建产能混列），
        与销量不同口径，未纳入；本页用总资产周转率作为利用率的代理。</div>`;
    chartsEl.value.appendChild(gap);

    window.addEventListener('resize', onResize)
  } catch (e) {
    loading.value = false
    error.value = e.message || String(e)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach(c => { try { c.dispose() } catch (_) {} })
  charts = []
})
</script>

<style scoped>
/* 静态模板节点（.page/.lede/.warn/h1）用 scoped，避免 .page 列宽、h1 基调外泄到其他视图；
   .lede 内的链接是静态节点，同块内着色。 */
.page { max-width: 1500px; margin: 0 auto; padding: 20px 16px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin: 12px 0 6px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 20px; }
.lede a { color: #1d4ed8; }
.warn {
    max-width: 1200px;
    margin: 0 auto 18px;
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-left: 4px solid #ea580c;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 17px;
    color: #7c2d12;
    line-height: 1.7;
}
</style>

<style>
/* 图卡与口径说明块由 onMounted 里 createElement/innerHTML 动态注入到 #charts，拿不到 scoped 属性，
   故用非 scoped；全部以 #charts 限定，作用范围等价于源页对 .chart-card/.note/a 的作用，不外泄到其他视图。
   .chart-card 白底/圆角/投影、.chart-title 与 .sub、#loading/#error-msg 已在 common/base.css 全局定义，此处不重复。 */
#charts .chart-card { padding: 16px 18px 22px; margin-bottom: 22px; }
#charts .chart-box { height: 70vh; }
#charts .note { font-size: 16px; color: #6b7280; line-height: 1.7; margin-top: 10px; }
#charts .note b { color: #b45309; }
#charts details.note > summary { cursor: pointer; color: #4b5563; }
#charts details.note-more { margin-top: 6px; }
#charts details.note-more > summary { cursor: pointer; color: #1d4ed8; font-size: 15px; }
#charts details.note-more > div { margin-top: 6px; padding-left: 10px; border-left: 3px solid #e5e7eb; }
#charts a { color: #1d4ed8; }
</style>
