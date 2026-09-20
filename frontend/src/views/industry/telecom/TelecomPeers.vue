<template>
  <div class="page">
    <h1>三大运营商同业对比</h1>
    <div class="lede">
      中国移动 600941 · 中国电信 601728 · 中国联通 600050 —— 金额与比率取自东方财富公司数据接口的
      <b>A 股年报合并数</b>，三家 2025 年营业收入／归母净利润／加权 ROE 已逐项对照上交所年报原文核验一致；<br>
      用户数、ARPU、年报口径资本开支、云与第二曲线收入来自<b>上交所 A 股年报原文</b>逐份通读录入（共 21 份，
      移动／电信 2021—2025、联通 2015—2025）；<a href="overview.html">名录与行业变革时间线</a><br>
      <b>上市前年份单列虚线</b>：移动与电信 A 股年报自 2021 年度起，更早年份是接口按发行人上市前披露回填的，
      与 A 股年报口径不同源，按项目规则分 series 披露、不拼成一条线
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

// 逐字搬自 dashboard/industry/telecom/peers.html：CHARTS 配置、buildChart 渲染逻辑与
// 每个 ECharts option 原样保留，仅把取数改走统一 apiGet、容器改用组件 ref。图与数据一律不变。
const loading = ref(true)
const error = ref('')
const chartsEl = ref(null)
let charts = []

const API = '/api/telecom_peers'
const ORDER = ['600941', '601728', '600050']
const COLORS = {'600941': '#1f6feb', '601728': '#c0392b', '600050': '#0f766e'}
// 上市前回填年份用同色系浅色虚线，与 A 股年报口径分开成两条 series
const PRE_COLORS = {'600941': '#93c5fd', '601728': '#f0a9a0', '600050': '#7fc3bb'}

/* 每张图：key 取 annual 记录里的字段；scale 除数（1e8 = 亿元，1 = 原值）；unit 轴单位；
 * decimals 提示框小数位；kind='fin' 财务接口字段（画 A + 上市前两段）、'ops' 年报手工层（只有 A 股年报年份）；
 * marks 竖向 markLine 标注制度/口径断点年；note 常显一句话，detail 折叠 */
const CHARTS = [
    {
        id: 'revenue', key: 'revenue', scale: 1e8, unit: '亿元', decimals: 0, kind: 'fin',
        title: '营业收入',
        sub: '营业总收入，含销售终端等非服务收入',
        marks: [{year: '2014', text: '电信业营改增'}, {year: '2021', text: '电信/移动回 A'}],
        note: '<b>2014-06-01 电信业营改增</b>（基础电信 11%、增值电信 6%）后营收由含税转不含税，2014 年前后的收入不严格可比 —— ' +
              '联通 2014 年营收 2,885.7 亿元、2015 年 2,770.5 亿元的连续两年下滑里含这层口径因素。' +
              '中国移动的营收体量长期是电信的两倍、联通的 2.7 倍，行业格局在 4G/5G 两代里没有实质改变。',
        detail: '<b>营业收入 vs 服务收入：</b>年报另披露「主营业务收入／服务收入」（剔除销售手机等终端），' +
                '2025 年移动 8,955 亿元（占营收 85.3%）、电信 4,854 亿元（92.7%）—— 终端销售占比不同，' +
                '直接比营业收入会高估移动的服务体量。<br>' +
                '<b>2008 年重组的影响：</b>2008-10 中国电信以 1,100 亿元（网络 438 亿＋业务 662 亿）收购联通 CDMA 网络与用户，' +
                '联通同期与网通合并，两家的收入结构在 2008—2009 年被一次性重排。<br>' +
                '<b>上市前段（虚线）：</b>移动 1999—2011、电信 2002—2020 的行由接口按发行人上市前披露回填，' +
                '其中移动 2012—2017 年整段缺失、2011 年营业收入与营业总收入两字段差一个量级（本页取营业总收入 5,280 亿元，' +
                '并把该年以收入为分母的比率与自由现金流一并置空，否则会算出毛利率 −412%），' +
                '故上市前段只可看量级与趋势，不作精确同比。'
    },
    {
        id: 'profit', key: 'parent_netprofit', scale: 1e8, unit: '亿元', decimals: 0, kind: 'fin',
        title: '归母净利润',
        sub: '联通 2008 年的高点来自出售 CDMA 网络的一次性收益',
        marks: [{year: '2008', text: '联通售 CDMA'}, {year: '2016', text: '联通利润见底'}],
        note: '<b>联通 2008 年 202.4 亿元不是经营性利润</b>：当年向中国电信出售 CDMA 网络及业务（总价 1,100 亿元）产生处置收益，' +
              '次年即回落到 31.4 亿元。联通 2016 年 1.5 亿元、2017 年 4.3 亿元是三家 20 余年里的绝对低点，' +
              '对应 3G 制式劣势叠加 4G 建设滞后，也是 2017 年混改的直接背景。',
        detail: '<b>三家的利润量级不同质：</b>移动 2025 年归母 1,371 亿元，是电信（331.8 亿）的 4.1 倍、联通（91.3 亿）的 15 倍，' +
                '差距大于收入差距（2.0 倍／2.7 倍），来源是网络规模摊薄后的折旧率与用户结构。<br>' +
                '<b>联通口径提醒：</b>600050 是 A 股主体，其归母净利润小于红筹 00762 合并口径下的股东应占利润 —— ' +
                '红筹在上、A 股在下的多层持股结构里，A 股主体的少数股东权益占比很高，切勿把两者混比。'
    },
    {
        id: 'roe', key: 'roe_weighted', scale: 1, unit: '%', decimals: 2, kind: 'fin',
        title: '加权平均净资产收益率（ROE）',
        sub: '2025 年：移动 9.9% · 电信 7.2% · 联通 5.39%，已对齐年报原文',
        note: '三家的 ROE 排序二十年未变，且都低于 A 股制造业龙头 —— 运营商是重资产、低杠杆（净现金）、受管制定价的生意，' +
              'ROE 的上限由折旧率与 ARPU 决定。联通 2016—2017 年 0.2%／0.49% 的谷底，是混改前网络投资回报最差的两年。',
        detail: '<b>为什么低杠杆反而压低 ROE：</b>三家常年净现金（有息负债少于货币资金），权益乘数在 1.4—1.9 倍之间，' +
                '几乎没有财务杠杆放大；而资产端的固定资产＋在建工程占总资产四成以上，折旧摊销吃掉大部分毛利。<br>' +
                '<b>上市前段没有 ROE：</b>接口的加权 ROE 字段在移动 2018 年前、电信 2018 年前基本为空，' +
                '不是没有盈利而是该指标未回填。'
    },
    {
        id: 'gross', key: 'gross_margin', scale: 1, unit: '%', decimals: 2, kind: 'fin',
        title: '销售毛利率',
        sub: '接口 XSMLL 口径；运营商的成本里折旧摊销与网络运维占大头',
        note: '三家毛利率长期下行：联通从 2002 年 50.8% 降到 2025 年 23.5%，移动从 2018 年 32.6% 降到 28.9%。' +
              '驱动力是 ARPU 下行（提速降费）叠加折旧刚性 —— 收入端降价、成本端的网络折旧却按年限摊完。',
        detail: '<b>2015 年铁塔资产注入是个结构性拐点：</b>2015-10 三家把 152 万座存量铁塔（评估值合计约 2,314 亿元）' +
                '注入中国铁塔，换股后移动持 38%、联通 28.1%、电信 27.9%、国新 6%。此后自建铁塔改为向铁塔公司租用，' +
                '资产负债表上的固定资产折旧被替换成经营租赁／使用权资产摊销与租费，毛利率口径因此不完全跨期可比。<br>' +
                '<b>联通的毛利率最低且最先见底：</b>2016 年 22.8% 是全样本最低点，与其当年归母仅 1.5 亿元同期。'
    },
    {
        id: 'capex-yr', key: 'ops_capex_yr', scale: 1, unit: '亿元', decimals: 0, kind: 'ops',
        title: '资本开支（年报披露口径）',
        sub: '年报「当年累计完成资本开支」，不是现金流量表的购建长期资产现金',
        marks: [{year: '2019', text: '5G 发牌'}, {year: '2025', text: '算力占比抬升'}],
        note: '<b>5G 周期已经过顶：</b>移动 2022 年 1,852 亿元见顶后连降三年到 2025 年 1,509 亿元，2026 年指引 1,366 亿元；' +
              '电信 2023 年 988 亿元见顶、2025 年 804 亿元；联通 2022 年 742 亿元见顶、2025 年 541.5 亿元，2026 年指引约 500 亿元。' +
              '三家同时把投向从通信网络切向算力（联通 2026 年资本开支指引中算力投资占比超 35%）。',
        detail: '<b>与财务口径的差别：</b>本图是年报按发生额披露的资本开支；「资本开支强度」那张图用的是现金流量表' +
                '「购建固定资产、无形资产和其他长期资产支付的现金」，两者因预算制、应付工程款与租赁处理不同而有出入，' +
                '数据表里两套都保留（ops_capex_yr 与 capex_ratio）。<br>' +
                '<b>联通 2015→2017 的断崖：</b>1,338.8 亿元降到 421.3 亿元（−68%），既有 4G 投资高峰过去的因素，' +
                '也有铁塔资产注入后自建支出转为租费的口径因素。<br>' +
                '<b>共建共享：</b>2019-09 电信与联通共建共享 5G 接入网，联通 2023 年报称当年节省运营开支约 390 亿元、' +
                '<b>累计节省资本开支约 3,400 亿元</b>，是两家 capex 长期低于移动的制度性原因。'
    },
    {
        id: 'capex-ratio', key: 'capex_ratio', scale: 1, unit: '%', decimals: 1, kind: 'fin',
        title: '资本开支强度（购建长期资产现金 / 营业收入）',
        sub: '财务口径，可回溯到上市前；看重资产行业的投资周期',
        note: '联通 2001 年 100.9%、2009—2012 年 35%—51% 的高位对应 2G→3G→4G 三轮网络建设；' +
              '三家近年一致降到 15%—20%，是本行业自由现金流改善的直接来源。',
        detail: '<b>怎么读这条线：</b>资本开支强度下行且收入平稳时，自由现金流（经营净现金 − 购建长期资产现金）会明显改善 —— ' +
                '联通 2025 年自由现金流 373 亿元（年报口径，同比 +24.7%），电信与移动同样处在这个阶段。<br>' +
                '<b>口径提醒：</b>分母用营业收入（含终端销售），若改用服务收入，强度会略高。'
    },
    {
        id: 'mobile-users', key: 'ops_mobile_users_mn', scale: 1, unit: '百万户', decimals: 1, kind: 'ops',
        title: '移动用户数',
        sub: '移动客户数（移动）／移动用户（电信）／移动出账用户（联通）',
        note: '<b>2025 年：移动 10.05 亿户 · 电信 4.39 亿户 · 联通 3.57 亿户（联通为「超 3.57 亿」近似披露，本图未录入）。</b>' +
              '移动的用户规模是电信的 2.3 倍，且 2021 年以来每年净增已降到千万级以内 —— 人口与手机普及率已到顶，' +
              '增量竞争转为存量 ARPU 与融合套餐竞争。',
        detail: '<b>联通的用户数为什么在 2020 年反而下降：</b>2019 年 3.18 亿户 → 2020 年 3.058 亿户，' +
                '是清理低效／不活跃用户与 2G 退网并行的结果，同期 ARPU 由 40.4 元回升到 42.1 元。<br>' +
                '<b>2022 年起联通不再披露精确值：</b>A 股年报改为「移动出账用户超过 3.2 亿户」这类表述，' +
                '2024 年「超 3.4 亿户」、2025 年「超 3.57 亿户」，本图对近似表述<b>不录入</b>也不按净增数推算，' +
                '所以联通这条线止于 2021 年 —— 这是发行人披露口径收窄，不是取数遗漏。'
    },
    {
        id: 'mobile-arpu', key: 'ops_mobile_arpu', scale: 1, unit: '元/户/月', decimals: 1, kind: 'ops',
        title: '移动 ARPU',
        sub: '移动 ARPU（移动）／移动用户 ARPU（电信）／移动出账用户 ARPU（联通）',
        note: '三家 ARPU 都在 45—49 元的窄带里横盘：移动 2025 年 46.8 元（同比 −3.5%）、电信 45.1 元、联通 2021 年 43.9 元。' +
              '<b>ARPU 不再增长是运营商估值的核心约束</b> —— 收入增长只能靠用户数、融合套餐与第二曲线，不能靠单价。',
        detail: '<b>移动 2025 年 ARPU 转跌：</b>由 48.5 元降到 46.8 元，年报把营收同比口径差异归因于套餐收入分拆纳税影响' +
                '（剔除后归母同口径增长 2.0%），ARPU 的下行则与低价副卡、融合套餐分摊有关。<br>' +
                '<b>联通 2019 年 40.4 元的跳水：</b>由 2018 年 45.7 元降 11.6%，是提速降费（2017-09 取消手机国内长途漫游费、' +
                '2018-07 取消流量漫游费）与 4G 价格战叠加的一年，年报未给口径变更说明，视为真实下滑。<br>' +
                '<b>横比谨慎：</b>三家 ARPU 的分母（出账用户／付费用户）与分子（是否含增值业务）定义并不完全一致，' +
                '看趋势可以，比小数点后的高下不成立。'
    },
    {
        id: 'bb-users', key: 'ops_broadband_users_mn', scale: 1, unit: '百万户', decimals: 1, kind: 'ops',
        title: '有线宽带用户数',
        sub: '移动 2015 年后从零起步反超两家老牌固网运营商',
        note: '<b>宽带是移动这十年唯一的份额逆转战：</b>移动 2021 年 2.40 亿户已超过电信（1.70 亿）与联通（0.95 亿）之和，' +
              '2024 年 3.15 亿户。电信与联通的固网基本盘被移动用「宽带＋移动融合套餐＋赠送」打穿。',
        detail: '<b>2025 年移动这条线断掉：</b>2025 年报不再披露有线宽带客户数，改披露千兆宽带客户数（1.09 亿户），' +
                '因此本图移动止于 2024 年 —— 披露口径变更，不是用户流失。<br>' +
                '<b>联通 2022—2024 年缺口：</b>同样是近似表述（「超过 1 亿户」「超 1.2 亿户」），只有 2023 年给了 1.13 亿户。'
    },
    {
        id: 'bb-arpu', key: 'ops_bb_arpu', scale: 1, unit: '元/户/月', decimals: 1, kind: 'ops',
        title: '宽带 ARPU（三家口径不同，仅看各自趋势）',
        sub: '移动=有线宽带 ARPU · 电信=宽带综合 ARPU（含智慧家庭）· 联通=宽带用户接入 ARPU（仅接入）',
        note: '<b>这三条线不能比高低</b>：电信的 47 元含天翼高清与智家应用，联通的 41 元只含接入，移动的 34 元是纯有线宽带、' +
              '其含增值的「家庭客户综合 ARPU」2025 年为 44.5 元。可比的只有各自的方向：' +
              '联通从 2015 年 63.6 元一路降到 41.3 元，电信自 2021 年起小幅回升，移动横盘。',
        detail: '<b>联通 2015→2016 的落差（63.6→49.4 元）：</b>年报未给拆分，同期发生的是 2014-06 营改增后收入转不含税、' +
                '2015 年提速降费与光改后低价套餐放量。<br>' +
                '<b>移动的两个口径都保留：</b>数据表里 ops_bb_arpu（有线宽带 ARPU，2021—2023）与 ops_home_arpu' +
                '（家庭客户综合 ARPU，2021—2025）分开存，2024 年起前者停止披露。'
    },
    {
        id: 'users-5g', key: 'ops_users_5g_pkg_mn', scale: 1, unit: '百万户', decimals: 0, kind: 'ops',
        title: '5G 用户（套餐口径）',
        sub: '2024 年起移动改披露「5G 网络客户数」，与套餐口径不是同一指标，单列在下方注释',
        marks: [{year: '2019', text: '5G 发牌'}, {year: '2024', text: '移动改网络口径'}],
        extraKeys: [{key: 'ops_users_5g_net_mn', suffix: '（5G 网络口径）', lineType: 'dotted'}],
        note: '<b>套餐用户 ≠ 网络用户：</b>移动 2023 年同时披露 5G 套餐客户 7.95 亿户与 5G 网络客户 4.65 亿户，' +
              '差额是「买了 5G 套餐但未在 5G 网络上」的用户。2024 年起移动只披露网络口径（2025 年 6.42 亿户），' +
              '故本图移动有两条线（实线=套餐、点线=网络）。',
        detail: '<b>电信与联通 2023 年起只给渗透率：</b>电信 2023 年 5G 套餐渗透率 70.4%、2025 年改为「5G 网络用户渗透率」68.8%；' +
                '联通 2023 年 5G 套餐渗透率 78%。渗透率乘用户数得到的绝对值属推算，本页不做推算，' +
                '因此两家的 5G 绝对户数序列分别止于 2022 年。<br>' +
                '<b>5G 发牌时间：</b>2019-06-06 工信部向移动、电信、联通、中国广电发放 5G 商用牌照；' +
                '2019-09 电信与联通宣布共建共享 5G 接入网；2021-01 移动与中国广电签署 700MHz 共建共享协议。'
    },
    {
        id: 'cloud', key: 'ops_cloud_rev', scale: 1, unit: '亿元', decimals: 0, kind: 'ops',
        title: '云业务收入（移动云 / 天翼云 / 联通云）',
        sub: '三家各自的云品牌收入，口径不同、只比量级与增速',
        note: '<b>天翼云是三家里最大且披露最连续的：</b>2021 年 279 亿元 → 2025 年 1,207 亿元（四年 4.3 倍）。' +
              '移动云 2021—2023 年 242→503→833 亿元、增速更快但 2024 年起不再披露绝对值；' +
              '联通云 2022—2024 年 361→510→686 亿元，2025 年只披露同比 +5.2%。',
        detail: '<b>为什么这张图会断：</b>三家都在把云并入更大的口径披露 —— 移动改用「数字化转型收入」与云算服务增速，' +
                '联通 2024 年起把联通云口径「优化为融合创新解决方案产生的云 IDC／云资源／云平台…」，' +
                '与 2023 年及以前不完全可比。绝对值缺失的年份本页留空，不用增速反推。<br>' +
                '<b>与互联网云厂商的关系：</b>运营商云的增长很大一部分来自政务、央国企与自有 IDC 资源，' +
                '与公有云厂商的市场口径（IaaS＋PaaS 份额）不是一回事。'
    },
    {
        id: 'dx', key: 'ops_dx_rev', scale: 1, unit: '亿元', decimals: 0, kind: 'ops',
        title: '第二曲线收入（口径分列：数字化转型 / 产数 / 算网数智）',
        sub: '移动=数字化转型收入 · 电信=产业数字化收入 · 联通=算网数智收入',
        note: '<b>三个名字不是同一个筐</b>：移动的「数字化转型收入」把个人新业务、智慧家庭、政企 DICT、物联网、专线都算进去，' +
              '2024 年 2,788 亿元（占主营 45.6%）；电信「产数」2025 年 1,473 亿元（占服务收入约 30%）；' +
              '联通「算网数智」2023 年 752 亿元。范围差异大于经营差异，横比只看各自占比与增速。',
        detail: '<b>增速已经换挡：</b>电信产数 2021—2023 年年增速接近 20%，2024 年 +5.5%、2025 年 +0.5% —— ' +
                '第二曲线从高增长进入平台期，这是三家 2025 年收入几乎零增长（移动 +0.9%、电信 +0.1%、联通 +0.7%）的直接原因。<br>' +
                '<b>披露不连续：</b>移动只有 2022（2,076 亿）与 2024（2,788 亿）两年在年报正文给了绝对值，' +
                '其余年份只给同比或占比，本图留空。'
    },
    {
        id: 'net-cash', key: 'net_cash', scale: 1e8, unit: '亿元', decimals: 0, kind: 'fin',
        title: '净现金（货币资金＋交易性金融资产 − 有息负债）',
        sub: '为正即净现金状态；运营商是典型的净现金行业',
        note: '<b>移动常年 2,500—4,400 亿元净现金</b>，电信近年由负转正到 869 亿元（2025），' +
              '联通 2012 年曾是 −1,236 亿元（4G 建设期靠借款）、2019 年起转正。净现金是三家能持续提高派息率的底气。',
        detail: '<b>口径：</b>有息负债取「短期借款＋一年内到期非流动负债＋应付短期债券＋长期借款＋应付债券」，' +
                '比年报口径粗（一年内到期非流动负债含租赁负债等非有息项，货币资金含受限资金），' +
                '故绝对值不宜与年报「净现金」直接对数，只看方向与量级。<br>' +
                '<b>租赁的影响：</b>2019 年起新租赁准则把铁塔／站址租赁计入使用权资产与租赁负债，' +
                '租赁负债不在本口径的有息负债里，若计入则三家的净现金都会明显下降。'
    },
    {
        id: 'staff', key: 'staff_num', scale: 1, unit: '人', decimals: 0, kind: 'fin',
        title: '员工人数',
        sub: '接口快照，含子公司；移动约 46 万人、电信约 27.8 万人、联通约 23.7 万人',
        note: '三家员工规模十年基本持平（联通 2016 年 25.4 万人的高点后缓降），而收入翻倍 —— 人效提升几乎全部来自收入端，' +
              '不是减员。联通 2008 年员工由 4.8 万跳到 20.4 万，是与网通合并并表所致。',
        detail: '<b>与人均指标配合看：</b>数据表里 rev_per_staff／np_per_staff（万元/人）由营业收入与归母净利润除以员工数得到，' +
                '2025 年人均营收移动 228 万元、电信 189 万元、联通 165 万元。<br>' +
                '<b>口径提醒：</b>三家均含大量子公司（移动含咪咕、中移金科等；电信含天翼云科技；联通含智网创新等），' +
                '与「通信主业员工」不是一回事；外包与代理渠道人员不计入。'
    },
    {
        id: 'dividend', key: 'dividend_per10', scale: 1, unit: '元/10股', decimals: 2, kind: 'div',
        title: '每 10 股派现（含税，按报告年度）',
        sub: '取历年分红实施明细，按报告年度归集（含中期与末期）',
        note: '<b>回 A 后三家都在提派息率：</b>电信 2025 年度以现金分配的利润为股东应占利润的 <b>75%</b>' +
              '（每股末期 0.0908 元＋中期 0.1812 元＝全年 0.2720 元）；移动与联通同期亦逐年提高派息比例。' +
              '这一轮「高股息中特估」行情的基本面依据就是这张图叠加上一张净现金图。',
        detail: '<b>口径：</b>本图按「报告年度」归集当年实施的分红，与「宣派年度」错开一年时会与年报口径不同；' +
                '联通有 23 个年度的分红记录（A 股上市最早），移动与电信只有回 A 后的 5 年。<br>' +
                '<b>不要用每 10 股派现横比股息率：</b>三家股本与股价不同，比派息率（分红／归母净利润）或股息率才有意义。'
    }

]

function onResize() { charts.forEach(c => { try { c.resize() } catch (_) {} }) }

onMounted(async () => {
  const container = chartsEl.value
  try {
    const peers = await apiGet(API)
    loading.value = false
    const focus = new URLSearchParams(location.search).get('focus')
    for (const cfg of CHARTS) buildChart(cfg, peers, ORDER.includes(focus) ? focus : null, container)

    const first = peers[ORDER.find(c => peers[c])]
    if (first) {
      const d = document.createElement('details')
      d.className = 'note'
      d.innerHTML = `<summary>数据口径与来源说明</summary>
            <div><b>财务层：</b>${first.caliber_note || ''}</div>
            <div>${first.unit_note || ''}　来源：${first.source || ''}</div>
            <div><b>经营层（用户数／ARPU／年报资本开支／云与第二曲线收入）：</b>
            ${(first.ops_meta && first.ops_meta.caliber_note) || ''}</div>
            <div>${(first.ops_meta && first.ops_meta.source) || ''}</div>
            <div><b>中国联通的主体口径（最容易踩的坑）：</b>${peers['600050'] ? peers['600050'].source : ''}</div>
            <div><b>交叉核验（2026-09-01）：</b>三家 2025 年营业收入／归母净利润／加权平均 ROE 已逐项对照上交所年报原文：
            移动 10,501.87 亿元／1,370.95 亿元／9.9%，电信 5,239.2 亿元／331.8 亿元／7.2%，
            联通 3,922 亿元／91.3 亿元／5.39%，与接口值一致。
            抓取脚本：<code>data/extract/fetch_telecom_financials.py</code>（财务层）与
            <code>data/extract/fetch_telecom_reports.py</code>（上交所年报 PDF 下载＋转 txt，含阿里云 WAF 挑战求解），
            落盘 <code>data/tables/telecom_&lt;code&gt;_annual.json</code> 与 <code>data/tables/telecom_ops_manual.json</code>，
            后端接口 <code>/api/telecom_peers</code>。</div>`
      container.appendChild(d)
    }
    window.addEventListener('resize', onResize)
  } catch (e) {
    console.error('fetch error', e)
    loading.value = false
    error.value = e.message || String(e)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach(c => { try { c.dispose() } catch (_) {} })
  charts = []
})

function buildChart(cfg, peers, focus, container) {
    const yearSet = new Set();
    for (const code of ORDER) {
        const p = peers[code];
        if (!p) continue;
        for (const y of Object.keys(p.annual)) yearSet.add(y);
        if (cfg.kind === 'div') for (const y of Object.keys(p.dividend_per10 || {})) yearSet.add(y);
    }
    let years = Array.from(yearSet).sort();

    // 取值：kind='div' 走 dividend_per10，其余走 annual[year][key]；srcFilter 用于分段（A / 上市前）
    const valuesOf = (p, key, srcFilter) => years.map(y => {
        let v;
        if (cfg.kind === 'div') {
            v = (p.dividend_per10 || {})[y];
        } else {
            const rec = p.annual[y];
            if (!rec) return null;
            if (srcFilter && (rec.src || 'A') !== srcFilter) return null;
            v = rec[key];
        }
        if (v === null || v === undefined) return null;
        return +(v / cfg.scale).toFixed(cfg.decimals + 2);
    });

    const series = [], missing = [];
    const line = (name, data, color, dim, type, width) => ({
        name: name, type: 'line', symbol: 'circle', symbolSize: dim ? 5 : 6, connectNulls: false,
        lineStyle: {width: width || (dim ? 1.5 : 2.6), opacity: dim ? 0.5 : 1, type: type || 'solid'},
        itemStyle: {color: color, opacity: dim ? 0.55 : 1},
        emphasis: {focus: 'series'}, data: data
    });

    ORDER.filter(c => peers[c]).forEach(code => {
        const p = peers[code];
        const dim = focus && focus !== code;
        // 财务字段分两段：A 股年报口径（实线）与上市前回填（浅色虚线）；ops/div 只有 A 股年报年份
        const mainData = valuesOf(p, cfg.key, cfg.kind === 'fin' ? 'A' : null);
        if (mainData.some(v => v !== null)) {
            series.push(line(p.name, mainData, COLORS[code], dim));
        } else {
            missing.push(code);
        }
        if (cfg.kind === 'fin') {
            const preData = valuesOf(p, cfg.key, 'PRE');
            if (preData.some(v => v !== null)) {
                series.push(line(p.name + '（上市前·回填）', preData, PRE_COLORS[code], dim, 'dashed', 1.8));
            }
        }
        (cfg.extraKeys || []).forEach(ex => {
            const d = valuesOf(p, ex.key, cfg.kind === 'fin' ? 'A' : null);
            if (d.some(v => v !== null)) {
                series.push(line(p.name + ex.suffix, d, COLORS[code], dim, ex.lineType || 'dotted', 2));
            }
        });
    });

    // 裁掉首尾整列无值的年份：经营层字段只覆盖 2015／2021 年起，
    // 若沿用财务层的 1999—2025 全区间，横轴会白留十几年空白
    if (series.length) {
        const has = years.map((_, i) => series.some(s => s.data[i] !== null && s.data[i] !== undefined));
        const from = has.indexOf(true), to = has.lastIndexOf(true);
        if (from > 0 || to < years.length - 1) {
            years = years.slice(from, to + 1);
            series.forEach(s => { s.data = s.data.slice(from, to + 1); });
        }
    }

    if (cfg.marks && series.length) {
        series[0].markLine = {
            silent: true, symbol: 'none',
            lineStyle: {type: 'dashed', color: '#9ca3af', width: 1.4},
            label: {position: 'insideEndTop', fontSize: 13, color: '#6b7280'},
            data: cfg.marks.filter(m => years.includes(m.year))
                .map(m => ({xAxis: m.year, label: {formatter: m.text}}))
        };
    }

    const gapNote = missing.length
        ? `<br><b>本图无 ${missing.map(c => peers[c].name).join('、')} 序列：</b>` +
          (cfg.gapNote || '该字段在年报与接口里均无可用值（口径见展开）。')
        : '';
    const wrap = document.createElement('div');
    wrap.className = 'chart-card';
    wrap.innerHTML = `
        <div class="chart-title">${cfg.title}<span class="sub">${cfg.sub}</span></div>
        <div class="chart-box" id="chart-${cfg.id}"></div>
        <div class="note">${cfg.note}${gapNote}${cfg.detail
            ? `<details class="note-more"><summary>展开详细口径与核对记录</summary><div>${cfg.detail}</div></details>`
            : ''}</div>`;
    container.appendChild(wrap);

    const chart = echarts.init(wrap.querySelector('#chart-' + cfg.id));
    chart.setOption({
        tooltip: {
            trigger: 'axis', axisPointer: {type: 'line'},
            formatter: function (ps) {
                const rows = ps.filter(p => p.value !== null && p.value !== undefined)
                    .sort((a, b) => b.value - a.value)
                    .map(p => `${p.marker}${p.seriesName}　<b>${fmt(p.value, cfg.decimals)}</b> ${cfg.unit}`);
                return `<b>${ps[0].axisValue} 年</b><br>` + (rows.length ? rows.join('<br>') : '无数据');
            }
        },
        legend: {top: 0, itemGap: 16, textStyle: {fontSize: 15}},
        grid: {left: 84, right: 40, top: 66, bottom: 40},
        xAxis: {
            type: 'category', data: years,
            axisLabel: {fontSize: 14, rotate: years.length > 18 ? 45 : 0},
            axisTick: {alignWithLabel: true}
        },
        yAxis: {
            type: 'value', name: cfg.unit, nameTextStyle: {fontSize: 14},
            // 比率与 ARPU 这类窄幅指标不从 0 起画，否则 40—50 元的波动会被压成一条直线
            scale: cfg.unit === '%' || cfg.unit === '元/户/月',
            axisLabel: {fontSize: 14, formatter: v => v.toLocaleString('zh-CN')},
            splitLine: {lineStyle: {type: 'dashed', color: '#e5e7eb'}}
        },
        series: series
    });
    charts.push(chart);
}
</script>

<style scoped>
/* 逐字搬自源页 <style>：仅静态模板节点（.page / h1 / .lede）用 scoped，避免全站泄漏；
 * base.css 已定义的规则（.chart-card 底色/圆角/投影、.chart-title/.sub、#loading、#error-msg）不重复 */
.page { max-width: 1500px; margin: 0 auto; padding: 20px 16px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin: 12px 0 6px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 20px; }
.lede b { color: #b45309; }
</style>

<style>
/* onMounted 里 createElement / innerHTML 生成的节点不带 scoped 属性，样式必须非 scoped 才生效；
 * .chart-card 只补 padding/margin，底色圆角投影仍来自 base.css，不重复 */
.chart-card { padding: 16px 18px 22px; margin-bottom: 22px; }
.chart-box { height: 70vh; }
.note { font-size: 16px; color: #6b7280; line-height: 1.7; margin-top: 10px; max-width: 1100px; }
.note b { color: #b45309; }
details.note > summary { cursor: pointer; color: #4b5563; }
details.note-more { margin-top: 6px; }
details.note-more > summary { cursor: pointer; color: #1d4ed8; font-size: 15px; }
details.note-more > div { margin-top: 6px; padding-left: 10px; border-left: 3px solid #e5e7eb; }
.page a { color: #1d4ed8; }
</style>
