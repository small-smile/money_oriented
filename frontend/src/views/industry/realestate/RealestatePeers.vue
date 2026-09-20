<template>
  <div class="realestate-peers page">
    <h1>六家头部央企开发商同业对比</h1>
    <div class="lede">
      保利发展 600048 · 招商蛇口 001979 · 华侨城A 000069 —— A 股上市，取<b>各期 A 股年报</b>合并口径，三张表明细科目齐全<br>
      中国海外发展 00688 · 华润置地 01109 · 中国金茂 00817（<span style="border-bottom: 2px dashed #0e7490">虚线</span>）——
      仅港交所上市、无 A 股年报，走港股 F10 主要指标，只有收入/利润/比率类序列；
      已售未结与剔预收资产负债率由<b>年报原文取数</b>补齐，<b>六家均为人民币口径</b>，<a href="overview.html">名录与政策时间线</a><br>
      上游对照：<a href="../cement/peers.html">八家水泥企业同业对比</a>（净负债率同口径，可直接与本页对比杠杆姿态）
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
import { fmt } from '../../../utils/format'

// 逐字搬自 dashboard/industry/realestate/peers.html：CHARTS/ORDER/COLORS/HK_CODES、fmt、buildChart
// 与 onMounted 渲染逻辑原样保留，仅取数改走统一 apiGet（解包后返回 peers），容器改用组件 ref、
// 每张图的 resize/dispose 归拢到组件生命周期。图与数据一律不变，含三道红线等口径。
const loading = ref(true)
const error = ref('')
const chartsEl = ref(null)
let charts = []

const API = '/api/developer_peers'
const ORDER = ['600048', '001979', '000069', '00688', '01109', '00817']
const COLORS = {
    '600048': '#c0392b',   // 保利发展
    '001979': '#1f6feb',   // 招商蛇口
    '000069': '#b45309',   // 华侨城A
    '00688': '#0e7490',    // 中国海外发展
    '01109': '#0f766e',    // 华润置地
    '00817': '#6c3483'     // 中国金茂
}
// 非 A 股年报口径的公司：线型改虚线，提醒数据来自港股 F10 主要指标 + 年报原文补录
const HK_CODES = ['00688', '01109', '00817']

/* 每张图：key 取 annual 记录里的字段，scale 除数（1e8 = 亿元），unit 轴单位，decimals 提示框小数位
 * marks 画竖向 markLine 标注政策/口径断点年；note 常显，detail 折叠展开
 * redline 画横向红线（三道红线阈值） */
const CHARTS = [
    {
        id: 'revenue', key: 'total_operate_income', scale: 1e8, unit: '亿元', decimals: 0,
        title: '营业收入',
        sub: '开发商收入按竣工交付结转，反映的是 2—3 年前的销售，不是当年销售',
        marks: [{year: '2021', text: '销售端见顶'}],
        note: '<b>时滞：</b>房地产开发收入在交付时一次性确认，2021 年销售见顶后，收入端的下滑普遍要到 2023—2024 年才显现。' +
              '<b>币种：</b>六家均为人民币口径（港股三家近年年报也以人民币编制），金额可直接比大小。',
        detail: '<b>为什么收入滞后销售：</b>预售制下客户款先记入合同负债（预收），要等项目竣工备案、交付业主才转为收入，' +
                '住宅从预售到交付通常 24—36 个月。所以「营收下滑」这条线读到的是两三年前拿地与销售的结果，' +
                '要看当期经营，得看合同销售金额（本页数据源不含）与下一张图的合同负债蓄水池。<br>' +
                '<b>不同质：</b>华侨城 A 含文旅（主题公园门票与综合体）业务，招商蛇口含物业管理（招商积余）、园区与邮轮，' +
                '华润置地含经营性不动产（万象城租金）与物业，中国金茂含城市运营与酒店 —— 收入结构差异会同步反映在毛利率上。'
    },
    {
        id: 'profit', key: 'parent_netprofit', scale: 1e8, unit: '亿元', decimals: 0,
        title: '归母净利润',
        sub: '2021 年起计提存货减值与合作项目损失，利润降幅远大于收入降幅',
        marks: [{year: '2021', text: '减值集中计提'}],
        note: '利润被三件事同时压：结转毛利率下行（高价地进入结算期）、存货跌价与信用减值计提、少数股东（合作方）分走的比例上升。',
        detail: '<b>三重挤压：</b>2016—2021 年高价拿地的项目在 2022 年后进入结算，地价占售价比高、限价下售价被压，' +
                '结转毛利率从 30% 级别掉到 10%—15%；同时对货值按可变现净值计提存货跌价准备、对合作方往来计提信用减值；' +
                '再加上并表少数权益（合作开发与明股实债）分走利润，归母口径的降幅被放大到收入降幅的数倍。<br>' +
                '<b>配合看少数股东损益占比：</b>本页「少数股东损益占净利润比」一图能看出归母被摊薄的程度；' +
                '该比值在亏损年会出现负值或异常大值（分母接近 0），只看方向不看数值。'
    },
    {
        id: 'gross-margin', key: 'gross_margin', scale: 1, unit: '%', decimals: 2,
        title: '销售毛利率',
        sub: '东财主要指标口径（XSMLL），港股为 GROSS_PROFIT_RATIO；六家可同图直读',
        marks: [{year: '2021', text: '结转毛利率下行'}],
        note: '<b>本页最可比的一张图：</b>毛利率是比值，不受接口口径差异影响。' +
              '2018—2020 年的高毛利来自 2015—2016 年的低价土地，2021 年后集中回落到 10%—20% 区间。',
        detail: '<b>回落机制：</b>毛利率的分子分母都锁定在项目结算时点 —— 2020 年结算的是 2016—2017 年拿的地，' +
                '2024 年结算的是 2021—2022 年高点拿的地，而售价受限价与降价去化压制，地价房价比抬升直接吃掉毛利。<br>' +
                '<b>业务结构差异：</b>持有型资产占比高的公司毛利率更抗跌 —— 华润置地的购物中心租金、中海的商业物业、' +
                '华侨城的文旅门票毛利率结构与住宅开发不同，横比毛利率高低要先看收入构成，不能直接当开发业务的盈利能力比。<br>' +
                '<b>互校：</b>本页数据同时保留了按「（营业收入 − 营业成本）÷ 营业收入」自算的 gross_margin_calc，' +
                'A 股三家与接口 XSMLL 逐年一致，说明接口口径就是营业总成本里的营业成本项。'
    },
    {
        id: 'roe', key: 'roe_weighted', scale: 1, unit: '%', decimals: 2,
        title: '净资产收益率（ROE）',
        sub: 'A 股为加权平均 ROE（ROEJQ），港股为接口 ROE_AVG（平均净资产口径），两者算法不完全一致',
        note: '2018—2020 年普遍 15%—20%，2024—2025 年多家落到 5% 以下。' +
              '<b>口径提醒：</b>A 股「加权平均」按净资产的时间加权，港股 ROE_AVG 为期初期末均值，横比只看量级与方向。',
        detail: '<b>ROE 下行的分解：</b>杜邦看三项 —— 净利率（结转毛利率下行 + 减值）大幅下降是主因；' +
                '总资产周转率随销售放缓也在降（存货去化变慢）；权益乘数因为三道红线约束下的主动降杠杆而下降。' +
                '三项同向往下，ROE 的降幅比任一单项都大。<br>' +
                '<b>不要用 total_equity 反推 ROE：</b>接口 total_equity 是股东权益合计含少数股东权益，' +
                '开发商合作开发普遍、少数权益占比可达三四成，拿合计做分母会显著低估 ROE。'
    },
    {
        id: 'adj-debt', key: 'adj_debt_ratio', scale: 1, unit: '%', decimals: 2,
        title: '三道红线①　剔除预收后的资产负债率',
        sub: '（总负债 − 合同负债 − 预收账款）/（总资产 − 合同负债 − 预收账款），红线 70%',
        marks: [{year: '2020', text: '三道红线出台'}],
        note: '<b>自算值不是披露值：</b>本图由资产负债表科目按公开定义自算（招商蛇口 2025 年报披露 64.17%，本页自算 61.74%）。' +
              '港股三家的已售未结取自年度业绩公告原文（接口无负债明细），起点为各家改以人民币编制之后的年份。',
        redline: {value: 70, text: '红线 70%'},
        detail: '<b>为什么要剔预收：</b>预售款（合同负债/预收账款）在会计上是负债，但它是已锁定的未来收入而非债务，' +
                '不剔除会让销售好的公司显得杠杆更高。三道红线因此以剔预收后的资产负债率为准。<br>' +
                '<b>与自算值的偏差来源：</b>年报披露口径会做更细的调整（如剔除部分应付款项、按监管口径认定预收范围），' +
                '本页只做「合同负债 + 预收账款」的简单剔除，因此系统性略低于披露值 2—3 个百分点。' +
                '跨公司比较与趋势判断有效，引用具体数值请回年报。<br>' +
                '<b>2019 年科目重分类：</b>收入准则把「预收账款」改记「合同负债」，本页把两者相加以保持跨年连续，' +
                '所以 2019 年前后这条线没有台阶。'
    },
    {
        id: 'net-gearing', key: 'net_gearing', scale: 1, unit: '%', decimals: 2,
        title: '三道红线②　净负债率',
        sub: '（有息负债 − 货币资金）/ 股东权益合计，红线 100%',
        marks: [{year: '2020', text: '三道红线出台'}],
        note: '<b>自算值系统性偏低：</b>永续债在接口里计入权益、未从分母剔除（招商蛇口 2025 年报披露 72.46%，本页自算 59.05%）。' +
              '分母为股东权益合计含少数股东权益，合作开发多的公司会被垫高分母、显得杠杆更低。',
        redline: {value: 100, text: '红线 100%'},
        detail: '<b>有息负债的取法：</b>短期借款 + 一年内到期的非流动负债 + 应付短期债券 + 长期借款 + 应付债券。' +
                '其中「一年内到期的非流动负债」含租赁负债等非有息项，所以自算的有息负债略偏大；' +
                '而永续债留在权益分母里、少数股东权益也在分母里，两者方向相反但后者影响更大，净效果是自算值偏低。<br>' +
                '<b>永续债为什么重要：</b>永续债会计上计入权益、经济实质接近债，是三道红线出台后的常见腾挪工具；' +
                '严格口径应把永续债从权益移到有息负债，那样净负债率会明显上升。要看真实杠杆，' +
                '需回年报附注里的「其他权益工具」明细（本页保留了 perpetual_bond / other_equity_tool 原始字段）。<br>' +
                '<b>华侨城 A 的高位：</b>这条线上华侨城显著高于两家同业，与其文旅重资产投入 + 去化偏慢、存货沉淀多有关。'
    },
    {
        id: 'cash-short', key: 'cash_short_debt', scale: 1, unit: '倍', decimals: 2,
        title: '三道红线③　现金短债比',
        sub: '货币资金 / 短期有息负债，红线 1 倍（低于 1 即短债缺口）',
        marks: [{year: '2020', text: '三道红线出台'}],
        note: '<b>自算值偏松：</b>货币资金含预售资金监管账户与其它受限资金，实际可自由调动的现金更少' +
              '（招商蛇口 2025 年报披露 1.19，本页自算 1.39）。跌破 1 倍是流动性预警，但受限资金口径下真实压力更早出现。',
        redline: {value: 1, text: '红线 1 倍'},
        detail: '<b>预售资金监管：</b>2021 年后各地普遍收紧预售资金监管，账上货币资金有相当比例锁在项目所在城市的监管账户里，' +
                '只能按工程进度提取、不能上划集团统筹。所以「集团层面的货币资金」高估了可用于偿债的现金 ——' +
                '这也是 2021—2022 年多家民营开发商账面现金充裕却违约的直接原因。<br>' +
                '<b>央企的差异：</b>央企开发商的融资渠道（银行间债券、中票、超短融、股东借款）比民企通畅，' +
                '现金短债比即使接近 1 也不等同于违约风险；这个指标对央企更多是融资节奏的刻度，对民企才是生死线。<br>' +
                '<b>短期有息负债的取法：</b>短期借款 + 一年内到期的非流动负债 + 应付短期债券；未剔除其中的非有息项，' +
                '因此分母略偏大、比值略偏保守（与货币资金未剔受限的方向相反）。'
    },
    {
        id: 'presale-cover', key: 'presale_cover', scale: 1, unit: '倍', decimals: 2,
        title: '已售未结蓄水池（合同负债 ÷ 当年营业收入）',
        sub: '衡量未来 1—2 年收入的锁定程度，>1 表示已售未结可覆盖一年以上结算',
        marks: [{year: '2019', text: '预收账款→合同负债'}],
        note: '这是本页最前瞻的一张图：合同负债是已收款未交付的房子，会在未来 1—3 年逐步转为营业收入。' +
              '该比值下行说明未来可结转资源在消耗、收入端的压力尚未出完。' +
              '港股三家的分子从年度业绩公告原文逐年取数（中海「预售楼款」、华润「合约负债」、' +
              '金茂在「其他应付款项和应计款项」附注里的合约负债 + 预收款项）。',
        detail: '<b>怎么读：</b>分子是资产负债表上的售房预收（2019 年前记预收账款、2019 年起记合同负债，本页相加），' +
                '分母是当年营业收入。比值 1.0 意味着「手上已售未结的房子刚好等于一年的结算量」。' +
                '销售扩张期这个比值上升（卖得比结得快），销售下行期下降（结转消耗蓄水池而新销售补不上）。<br>' +
                '<b>比销售额更可得：</b>合同销售金额（全口径/权益口径）是月度经营公告披露的，不在财报三张表里，' +
                '本页数据源（东财 F10）取不到，所以用合同负债这个财报内的代理指标观察销售端。<br>' +
                '<b>局限：</b>合同负债只含并表项目，合作开发中不并表的项目（记在长期股权投资里）的销售不体现在这里；' +
                '本页保留了 long_equity_invest 字段，可侧面看表外项目的规模。'
    },
    {
        id: 'inventory-ratio', key: 'inventory_ratio', scale: 1, unit: '%', decimals: 2,
        title: '存货占总资产比',
        sub: '开发商的存货 = 在建开发成本 + 已完工待售，是最大的资产科目',
        note: '存货占比长期在 45%—70%（保利发展最高、2015—2019 年一度超七成），是开发商重资产、慢周转的直接体现；占比下降通常来自主动缩表（少拿地、加快去化）而非结构优化。' +
              '仅 A 股三家有序列。',
        detail: '<b>存货的两块：</b>「开发成本」（在建、含土地）与「开发产品」（已竣工未售）。后者占比上升是危险信号 ——' +
                '意味着房子建好卖不掉、要计提跌价准备。财报附注里有这两项的拆分，本页只取存货合计。<br>' +
                '<b>与周转率同读：</b>本页数据保留了 inventory_turnover（存货周转率）与 inventory_days（周转天数），' +
                '开发商的存货周转天数常在 1,000 天以上（三年），与制造业不可类比。<br>' +
                '<b>减值：</b>2021 年后存货跌价准备是利润的主要拖累项之一，但计提金额在附注里，' +
                '利润表上的 asset_impairment（资产减值损失）字段本页有保留，可作近似观察。'
    },
    {
        id: 'minority', key: 'minority_share', scale: 1, unit: '%', decimals: 2,
        title: '少数股东损益占净利润比',
        sub: '并表项目中合作方（含明股实债）分走的利润比例，越高说明归母被摊薄越多',
        note: '<b>异常值请忽略数值只看方向：</b>净利润接近 0 或转负的年份，这个比值会出现极大值或负值（招商蛇口 2025 年为 −45%），' +
              '是分母塌缩导致的，不代表少数股东真的拿走了负的利润份额。仅 A 股三家有序列。',
        detail: '<b>为什么要看这个：</b>开发商普遍合作开发，项目公司里合作方持股。少数股东损益占比持续高于少数股东权益占比，' +
                '意味着并表的好项目里外部权益多、归母能拿到的少；反过来若占比远低于权益占比，' +
                '常被质疑是「明股实债」—— 名义股东只拿固定回报（实为利息），不分享真实利润。<br>' +
                '<b>与净负债率联读：</b>明股实债同时压低了净负债率（钱进了权益而非有息负债），' +
                '所以净负债率好看 + 少数股东权益占比高 + 少数股东损益占比低，这个组合是需要警惕的信号。'
    },
    {
        id: 'ocf', key: 'netcash_operate', scale: 1e8, unit: '亿元', decimals: 0,
        title: '经营活动现金流净额',
        sub: '开发商的经营现金流 = 销售回款 − 拿地与工程支出，主动少拿地就会转正',
        note: '<b>正数未必是好事：</b>2022 年后多家经营现金流转正，主要来自缩减土地投资而非销售改善 ——' +
              '对开发商而言持续大额净流入通常意味着在收缩规模。',
        detail: '<b>开发商的现金流特殊性：</b>购地款计入经营活动（存货支出）而非投资活动，所以扩张期经营现金流天然为负、' +
                '收缩期为正。这与制造业「经营现金流越高越健康」的直觉相反 ——' +
                '要判断是良性还是收缩，需同时看拿地金额与合同销售，单看这条线会误读。<br>' +
                '<b>与净利润的背离：</b>销售回款在预售时就到账、收入在交付时才确认，' +
                '所以现金流的拐点领先利润表 2—3 年；2021 年的回款下滑对应的是 2023—2024 年的利润塌方。'
    },
    {
        id: 'cash-collect', key: 'cash_collect_ratio', scale: 1, unit: '倍', decimals: 2,
        title: '销售回款 ÷ 营业收入',
        sub: '销售商品、提供劳务收到的现金 / 营业收入，>1 表示当期回款快于结转',
        note: '预售制下回款先于收入确认，扩张期这个比值长期大于 1；跌到 1 以下说明当期销售回款已经补不上结算规模，' +
              '是收入端下滑将持续的先行信号。仅 A 股三家有序列。',
        detail: '<b>口径：</b>分子取现金流量表「销售商品、提供劳务收到的现金」，含预售款与本期交付款、含代收税费，' +
                '也含物业/文旅等其它业务的现金收入，因此不等于合同销售金额；分母为营业收入（已结转口径）。<br>' +
                '<b>怎么用：</b>这个比值把「当期真实收现」与「当期账面收入」放在一起，' +
                '比单看营业收入更早反映销售市场的变化 —— 营业收入是历史，回款是当下。'
    },
    {
        id: 'assets', key: 'total_assets', scale: 1e8, unit: '亿元', decimals: 0,
        title: '总资产',
        sub: '2021 年后普遍进入缩表期：存货减少 + 主动降杠杆',
        marks: [{year: '2020', text: '三道红线出台'}],
        note: '开发商的总资产主要是存货与合同负债支撑的，缩表既来自少拿地也来自减值。',
        detail: '<b>缩表的构成：</b>资产端是存货下降（拿地少于交付结转）与货币资金调节；' +
                '负债端是有息负债压降与合同负债消耗。三道红线设定的是比率约束，' +
                '在销售下行时想达标只能压缩分子（降负债）而非扩大分母，因此行业整体从「加杠杆扩表」转向「降杠杆缩表」。<br>' +
                '<b>央企的相对位置：</b>央企在 2021—2023 年是行业里少数还能逆势拿地的主体（融资成本低、信用背书强），' +
                '所以缩表幅度小于民营同业，市占率被动上升。'
    },
    {
        id: 'equity-asset', key: 'equity_asset_ratio', scale: 1, unit: '%', decimals: 2,
        title: '权益资产比（股东权益 ÷ 总资产）',
        sub: '= 1 − 资产负债率 = 1 / 权益乘数；A 股为股东权益合计含少数股东权益，港股按（总资产 − 总负债）反推',
        note: '<b>不要当杠杆的唯一刻度：</b>开发商资产负债率里有很大一块是合同负债（预售款），' +
              '不是真债；看真实杠杆要用本页的剔预收资产负债率与净负债率。比值不受币种影响，六家可同图直读。',
        detail: '<b>为什么开发商这个比值天然低：</b>预售制让「未交付房款」以合同负债形式挂在负债端，' +
                '一家销售旺盛的公司资产负债率会更高、权益资产比更低 —— 这正是三道红线要剔预收的原因。' +
                '开发商权益资产比常年 20%—35%（权益乘数约 3—5 倍），低于制造业但远高于银行保险。<br>' +
                '<b>少数股东权益的影响：</b>A 股三家分子为股东权益合计，合作开发多的公司这里被少数股东权益垫高，' +
                '归母口径的权益资产比会明显更低；港股三家按（总资产 − 总负债）反推，同为全口径，与 A 股三家同义。'
    },
    {
        id: 'dividend', key: 'dividend_per10', scale: 1, unit: '元', decimals: 2,
        title: '每 10 股派现（含税，按分配所属年度）',
        sub: '取 A 股分红实施明细 RPT_SHAREBONUS_DET，同一年度中期 + 末期合并',
        fromDividend: true,
        note: '央企开发商在利润下滑期普遍维持分红（国资考核含分红要求），因此派现降幅小于利润降幅、分红率被动抬升。' +
              '港股三家不在此图（A 股分红明细接口不适用），其派息比率见数据文件的 dividend_payout 字段。',
        detail: '<b>口径：</b>按分红方案归属的报告年度归集（不是除权年度），只统计「实施分配」状态的方案，' +
                '金额为税前每 10 股派现（PRETAX_BONUS_RMB）。中期与末期分红在同一年度合并计入。<br>' +
                '<b>与分红率一起读：</b>每 10 股派现是绝对额，分红率（派现总额 ÷ 归母净利润）才反映政策取向；' +
                '2023—2025 年多家分红率从 30% 抬到 40%—50% 以上，主要是分母（利润）下降所致，' +
                '不宜直接读成「加大回报」。'
    }
];

function buildChart(cfg, peers, focus, container) {
    // 全部公司的年份并集，升序；2005 年以前只有华侨城有零散数据，统一从 2005 年起画
    const yearSet = new Set();
    for (const code of ORDER) {
        const p = peers[code];
        if (!p) continue;
        for (const y of Object.keys(cfg.fromDividend ? (p.dividend_per10 || {}) : p.annual)) {
            if (+y >= 2005) yearSet.add(y);
        }
    }
    const years = Array.from(yearSet).sort();
    const series = [], missing = [];
    ORDER.filter(c => peers[c]).forEach(code => {
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
        // 整条全空的公司不进图例（港股 F10 未披露的指标），改在注释里说明缺口
        if (s.data.some(v => v !== null)) series.push(s); else missing.push(code);
    });

    // 政策/口径断点竖线 + 三道红线阈值横线：只挂在第一条 series 上，避免每家重复画
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
          (missing.every(c => HK_CODES.includes(c))
              ? (cfg.fromDividend
                  ? '东财 A 股分红实施明细接口（RPT_SHAREBONUS_DET）不覆盖港股，三家港股公司的派息只有比率字段 dividend_payout。'
                  : '东财港股 F10 主要指标接口不提供资产负债表与现金流量表明细科目（存货、有息负债、销售回款、少数股东损益均无），故这几张图上没有这三家的线；已售未结与剔预收资产负债率已用年报原文补齐，不在此列。')
              : '接口该字段全年无值。')
        : '';
    const wrap = document.createElement('div');
    wrap.className = 'chart-card';
    wrap.innerHTML = `
        <div class="chart-title">${cfg.title}<span class="sub">${cfg.sub}</span></div>
        <div class="chart-box" id="chart-${cfg.id}"></div>
        <div class="note">${cfg.note}${gapNote}${cfg.detail
            ? `<details class="note-more"><summary>展开详细口径与机制</summary><div>${cfg.detail}</div></details>`
            : ''}</div>`;
    container.appendChild(wrap);

    const chart = echarts.init(wrap.querySelector('#chart-' + cfg.id));
    chart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: {type: 'line'},
            formatter: function (ps) {
                const rows = ps.filter(p => p.value !== null && p.value !== undefined)
                    .sort((a, b) => b.value - a.value)
                    .map(p => `${p.marker}${p.seriesName}　<b>${fmt(p.value, cfg.decimals)}</b> ${cfg.unit}`);
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
function onResize() { charts.forEach(c => { try { c.resize() } catch (_) {} }) }

onMounted(async () => {
  try {
    const peers = await apiGet(API)
    loading.value = false
    const focus = new URLSearchParams(location.search).get('focus')
    for (const cfg of CHARTS) buildChart(cfg, peers, ORDER.includes(focus) ? focus : null, chartsEl.value)

    // A 股三家口径说明（caliber_note 一致，取首家展示）
    const first = peers[['600048', '001979', '000069'].find(c => peers[c])];
    if (first && first.caliber_note) {
        const d = document.createElement('details');
        d.className = 'note';
        d.innerHTML = `<summary>A 股三家（保利 / 招商蛇口 / 华侨城A）口径与来源说明</summary>
            <div>${first.caliber_note}</div>
            <div>${first.unit_note || ''}　来源：${first.source || ''}</div>
            <div>抓取脚本：<code>data/extract/fetch_developer_financials.py</code>，落盘
            <code>data/tables/developer_&lt;code&gt;_annual.json</code>，后端接口 <code>/api/developer_peers</code>。
            三家同一年份 A/H 年报都存在时按项目规则优先取 A 股口径（保利与华侨城无 H 股上市，招商蛇口亦仅 A 股）。</div>
            <div><b>三道红线自算值与披露值的对照（招商蛇口 2025 年）：</b>年报披露 剔预收资产负债率 64.17% /
            净负债率 72.46% / 现金短债比 1.19，本页自算 61.74% / 59.05% / 1.39。偏差方向可解释：
            净负债率偏低因为永续债留在权益分母未剔除、现金短债比偏高因为货币资金未剔除预售监管资金。
            <b>三张红线图请读趋势与公司间相对位置，不要当披露值引用。</b></div>`;
        chartsEl.value.appendChild(d);
    }
    // 港股三家走另一套接口，口径说明单列
    const hkFirst = peers[HK_CODES.find(c => peers[c])];
    if (hkFirst) {
        const d = document.createElement('details');
        d.className = 'note';
        d.innerHTML = `<summary>港股三家（中海外 / 华润置地 / 中国金茂）口径与来源说明</summary>
            <div>${hkFirst.caliber_note || ''}</div>
            <div>${hkFirst.unit_note || ''}　来源：${hkFirst.source || ''}</div>
            <div><b>币种核验（2026-08-19，已修正早前结论）：</b>东财港股 F10 行内一律写 <code>CURRENCY="HKD"</code>、
            <code>IS_CNY_CODE=0</code>，这个标记<b>不可信</b>——金额是年报本位币原值、未做折算，而三家近年年报
            <b>都以人民币编制</b>：中海外 00688 自 <b>FY2019 年报起改以人民币编制</b>（同时把 2018-12-31 与 2018-01-01
            比较数重列为人民币），FY2024 公告「本集团收入为人民币 1,851.5 亿元」、报表栏头「人民币千元」，与接口
            185,154,027 千一致；华润置地 01109 自 FY2018 年报起（把 2017 年预售物业已收垫款由港币 142,805,881 千
            重列为人民币 119,372,967 千）；中国金茂 00817 自 <b>FY2016 年报起</b>（FY2016 公告附注 2.2「呈列货币变更」：
            「于 2016 年 12 月 31 日，本集团将其编制综合财务报表之货币由港元改为人民币」，追溯重列 FY2015 比较数；
            早前本页写 FY2015，2026-08-19 已按该附注修正）。因此<b>本页金额类图表六家可直接比大小</b>。</div>
            <div><b>已售未结的补录方式：</b>港股 F10 主要指标不含负债明细科目，presale 逐年从 HKEXnews 年度业绩公告
            语义通读后硬编码在 <code>HK_PRESALE_THOUSANDS</code>（口径对齐 A 股的「合同负债 + 预收账款」）：
            中海外取综合财务状况表的<b>预售楼款</b>（2018 年称合同负债、更早称预售按金）；华润置地取<b>合约负债</b>
            （2017 年前称预售物业已收垫款）；中国金茂表面上没有该科目，藏在<b>「其他应付款项和应计款项」附注</b>里，
            取该附注的合约负债总额 + 预收款项。已重列年份取最新重列值（唯一例外：金茂 2018/2019 取原披露值，
            因为重列后的预收款项拆分未单独披露，差额约 0.5%）；序列起点为金额可与人民币序列同口径比较的首年
            （中海外 2017、华润 2017、<b>金茂 2015</b> —— 接口的金茂 2015 年资产负债表数已是 FY2016 年报重列后的
            人民币值，已核总资产 133,126,399 千元与该年报重列值一致），更早年份接口值为港元原值、不入列。
            <b>不要用接口的 <code>004011009 预收款项</code> 代替</b>——实测它等于「预售按金 + 租务及其他按金」，被租赁押金污染。</div>
            <div>存货、净负债率、现金短债比、销售回款、少数股东损益仍缺明细科目，这几张图上没有这三家的序列；
            <code>RPT_HKF10_FN_BALANCE</code> 是 STD_ITEM_CODE 长表需逐项 pivot，暂未采用。
            <code>roe_weighted</code> 取接口 <code>ROE_AVG</code>（期初期末净资产均值），与 A 股「加权平均 ROE」算法不同；
            <code>dividend_payout</code>（派息比率）为小数不是百分数。</div>`;
        chartsEl.value.appendChild(d);
    }

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
/* 静态模板节点（.page / h1 / .lede / 其中的 <a>）——逐字搬自源页 <style>。
   * 重置、body、#loading / #error-msg、.chart-card 的白底/圆角/投影、.chart-title / .sub
   已在全局引入的 common/base.css 定义，这里不重复。 */
.page { max-width: 1800px; margin: 0 auto; padding: 20px 16px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin: 12px 0 6px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 20px; }
a { color: #1d4ed8; }
</style>

<style>
/* 以下针对 onMounted 里 document.createElement / innerHTML 动态生成的节点：每张图的
   .chart-card（本页专属的 padding/margin）、.chart-box、.note 与两块 details 口径说明。
   动态节点拿不到 scoped 的 data-v 属性，规则必须放非 scoped 块；为免 .chart-card / .chart-box /
   .note 这类公共类名泄漏到别的页面，全部限定在本页根节点 .realestate-peers 之下。逐字搬自源页 <style>。 */
.realestate-peers .chart-card { padding: 16px 18px 22px; margin-bottom: 22px; }
.realestate-peers .chart-box { height: 70vh; }
.realestate-peers .note { font-size: 16px; color: #6b7280; line-height: 1.7; margin-top: 10px; }
.realestate-peers .note b { color: #b45309; }
.realestate-peers details.note > summary { cursor: pointer; color: #4b5563; }
.realestate-peers details.note-more { margin-top: 6px; }
.realestate-peers details.note-more > summary { cursor: pointer; color: #1d4ed8; font-size: 15px; }
.realestate-peers details.note-more > div { margin-top: 6px; padding-left: 10px; border-left: 3px solid #e5e7eb; }
</style>

