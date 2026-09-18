<template>
  <div ref="rootEl">
    <div class="wrap">

      <div class="page-head">
        <h1>中饮巴比食品股份有限公司（巴比食品）2025 年报 · 公司概览</h1>
        <div class="meta">
          A 股 605338（上交所主板） · 2020-10-12 上市 · 董事长/实控人 刘会平 · 财务总监/董秘 苏爽<br>
          “中国包子第一股” · 中式面点连锁（特许加盟为主 + 团餐大客户） · 单位：人民币（另标注除外）
        </div>
        <div class="tags"><span>业绩</span><span>盈利能力</span><span>渠道分部</span><span>门店</span><span>区域结构</span><span>三张表</span><span>东鹏扰动</span><span>股东</span><span>并购</span><span>研发</span></div>
      </div>

      <!-- ══════════ 0 审计意见（置顶） ══════════ -->
      <div class="opinion-hero">
        <span class="tick">✓ 标准无保留意见</span>
        <div class="txt">2025 年度财务报告 · 审计机构 容诚会计师事务所（特殊普通合伙） · 签字会计师 孔令莉 / 孙茂藩 / 张勉楼</div>
      </div>
      <!-- ══════════ 0.5 行业背景：全国餐饮收入 ══════════ -->
      <section id="sec-industry">
        <h2>行业背景：历年全国餐饮收入及其占社会消费品零售总额的比重</h2>
        <p class="sub">口径：国家统计局全国餐饮收入额、社会消费品零售总额（当年 12 月月报/年度发布稿数）· 2010–2025 年 · 单位：亿元 / %</p>
        <div class="kpis">
          <div class="kpi"><div class="label">2025 全国餐饮收入</div><div class="value">57,982 亿</div><div class="delta up">▲ 3.2%</div></div>
          <div class="kpi"><div class="label">2025 占社零比重</div><div class="value">11.57%</div><div class="delta up">▲ 0.15pct</div></div>
          <div class="kpi"><div class="label">2025 社零总额</div><div class="value">50.12 万亿</div><div class="delta up">▲ 2.7%</div></div>
          <div class="kpi"><div class="label">区间低点（2022）</div><div class="value">9.99%</div><div class="delta down">▼ 疫情扰动</div></div>
        </div>
        <div id="chart-catering" class="chart" style="height:560px"></div>
        <div class="note">
          餐饮收入 16 年间从 2010 年 1.76 万亿元增至 2025 年 <b>5.80 万亿元</b>（年均复合 +8.3%），
          但<b>占社会消费品零售总额的比重长期在 10%–11.6% 的窄区间内摆动</b>，并非单调上升：
          2010–2014 年由 11.41% 连续回落至 10.62%（2013 年「八项规定」抑制高端餐饮，当年餐饮收入增速降至 9.0%），
          2015–2019 年缓慢修复至 11.35%，2020 年疫情下餐饮收入首次负增长（-16.6%）、比重跌至 10.08%，
          2022 年再度回落至区间低点 <b>9.99%</b>，2023 年报复性反弹（+20.4%）后比重回到 11.22%，
          2024/2025 年进一步升至 11.42% / 11.57%，为有该分组以来最高水平——也就是巴比《2025 年年度报告》引用的「全国餐饮收入占社会消费品零售总额的比重为 11.6%」。
          对巴比的含义：行业餐饮大盘的扩张更多来自总量增长而非份额提升，中式面点连锁的增量主要靠<b>渠道下沉与单店/团餐结构</b>，而不是「餐饮替代零售」这一宏观红利。<br>
          口径说明：<b>序列自 2010 年起</b>——国家统计局自 2010 年起才按「商品零售额」与「餐饮收入额」两种消费形态分组，
          2008/2009 年只有含住宿业的「住宿和餐饮业零售额」（15,404 / 17,998 亿元），与餐饮收入不可接续，故不纳入；
          2010–2013 年同一年度存在两套官方数（次年 1 月发布稿与次年 2 月统计公报，如 2010 年餐饮 17,636 / 17,648 亿元、社零 154,554 / 156,998 亿元），
          本图统一采用<b>发布稿（月报）口径</b>，不与统计公报数混用；三农普/四经普基期修订、限额以上单位年度重新核定会造成同一年份在不同年份出版物中数值不同，跨年比较请以增速为准。<br>
          数据来源：全国餐饮收入取自国家统计局历年「社会消费品零售总额（12 月）」月度发布稿与年度国民经济运行情况新闻稿（www.stats.gov.cn）；
          社会消费品零售总额取自东方财富宏观数据接口 RPT_ECONOMY_TOTAL_RETAIL（12 月累计值，与统计局发布稿一致），取数日期 2026-08-18；
          2024 年 11.4%、2025 年 11.6% 的比重与统计局原文表述及公司年报引用一致。
        </div>
      </section>
      <!-- ══════════ 1 业绩走势 ══════════ -->
      <section id="sec-perf">
        <h2>业绩走势（营收 / 归母净利润 / 扣非归母净利润）</h2>
        <p class="sub">口径：合并数 · 2020 年 10 月上市，图示为上市以来各完整年度 · 单位：亿元</p>
        <div class="kpis">
          <div class="kpi"><div class="label">2025 营业收入</div><div class="value">18.59 亿</div><div class="delta up">▲ 11.22%</div></div>
          <div class="kpi"><div class="label">2025 归母净利润</div><div class="value">2.73 亿</div><div class="delta down">▼ 1.28%</div></div>
          <div class="kpi"><div class="label">2025 扣非归母净利</div><div class="value">2.45 亿</div><div class="delta up">▲ 16.66%</div></div>
          <div class="kpi"><div class="label">2025 加权平均 ROE</div><div class="value">11.97%</div><div class="delta down">▼ 0.27pct</div></div>
        </div>
        <div id="chart-perf" class="chart"></div>
        <div class="note">
          营业收入自 2020 年（上市当年，受疫情影响 9.75 亿元、同比 -8.35%）稳步增至 2025 年 <b>18.59 亿元</b>，
          2021 年疫后强劲反弹 +41.06%，此后主业（特许加盟 + 团餐）驱动的规模扩张较为线性。
          <b>归母净利润与扣非归母净利润的显著背离</b>是本页最需要注意的一点：公司通过天津君正投资间接持有东鹏饮料股份，
          2021 年东鹏上市后其股价波动经「公允价值变动收益」直接计入当期损益，使归母净利润在 2021 年冲高至 3.14 亿、
          2022–2023 年随东鹏回调而回落（增收不增利），2024 年又因东鹏反弹推高至 2.77 亿。扣非归母净利润剔除该扰动后
          上市以来持续上行（2020 1.29 → 2021 1.52 → 2025 2.45 亿），更能反映主业盈利。
          2025 年总资产 28.99 亿元（+1.60%）、归母净资产 23.37 亿元（+3.18%）、经营活动现金流净额 3.19 亿元（+46.93%）、基本每股收益 1.14 元。<br>
          数据来源：2020 年数据取自公司《2020 年年度报告》全文（新浪财经，营收 9.75 亿、归母 1.75 亿）、2021 年取自《2021 年年度报告》（归母 3.14 亿、扣非 1.52 亿）；
          2022/2023/2024 取自公司《年度财务决算报告》（cninfo 巨潮，2024 年营收 167,145 万元、归母 27,659 万元、扣非 21,018 万元）；2025 年取自《2025 年年度报告摘要》（上交所 www.sse.com.cn，2026-04-10 披露，公告编号见摘要正文）。
        </div>
      </section>

      <!-- ══════════ 1.5 分季度业绩 ══════════ -->
      <section id="sec-quarter">
        <h2>2025 年分季度业绩</h2>
        <p class="sub">口径：合并数 · 单位：万元 · 数据取自《2025 年年度报告摘要》「3.2 报告期分季度的主要会计数据」</p>
        <div id="chart-quarter" class="chart" style="height:400px"></div>
        <div class="note">
          营业收入逐季走高（Q1 3.70 亿 → Q2 4.65 亿 → Q3 5.22 亿 → Q4 5.03 亿），呈现下半年团餐旺季 + 加盟门店并购并表的季节性抬升；
          归母净利润在 <b>Q2 达到全年峰值 0.94 亿元</b>（含公允价值变动收益等非经常性因素扰动），Q1 最低仅 0.37 亿元；
          扣非归母净利润走势相对平滑、逐季抬升（Q1 0.39 亿 → Q4 0.70 亿），更贴近主业实际盈利节奏；
          经营活动现金流净额 Q1 罕见为负（-196 万元，春节前备货垫款所致），Q2–Q4 转正且逐季走高，全年经营性现金流与净利润基本匹配。<br>
          数据来源：《2025 年年度报告摘要》「3.2 报告期分季度的主要会计数据」（上交所 www.sse.com.cn，2026-04-10）。
        </div>
      </section>
      <!-- ══════════ 2 盈利能力：归母净利率 vs 扣非净利率 ══════════ -->
      <section id="sec-margin">
        <h2>盈利能力（归母净利率 / 扣非归母净利率）</h2>
        <p class="sub">口径：净利率 = 对应口径净利润 ÷ 营业收入 · 单位：% · 两条线的缺口≈东鹏公允价值等非经常性损益</p>
        <div id="chart-margin" class="chart" style="height:380px"></div>
        <div class="note">
          <b>归母净利率</b>受东鹏公允价值扰动大起大落——2021 年借东鹏上市冲至 <b>22.84%</b> 的历史峰值，2022–2023 年随东鹏回调降至 13–14.6%，
          2024 年又反弹至 16.55%、2025 年回落 14.69%；<b>扣非归母净利率</b>则相对平稳并在近三年持续抬升（2021 11.05% → 2025 13.18%），
          反映精细化管理下的真实盈利改善——2024 年销售费用率同比降 1.34pct 至 4.29%（门店装修补贴、房租物业费下降），综合毛利率 26.71%（+0.36pct）。
          两条线之间的缺口即为以东鹏公允价值变动为主的非经常性损益贡献，缺口在 2021 年最宽（东鹏上市当年）。<br>
          数据来源：各年归母/扣非净利率由「营业收入 / 归母净利润 / 扣非归母净利润」计算（2020–2021 取自历年年报，2022–2024 取自《财务决算报告》，2025 取自业绩快报）；毛利率、费用率取自公司投资者关系活动记录表（2025-03-28 业绩说明会）与年报。
        </div>
      </section>

      <!-- ══════════ 2.5 营业成本构成 ══════════ -->
      <section id="sec-cost">
        <h2>营业成本构成</h2>
        <p class="sub">口径：主营业务成本（不含其他业务成本）· 2020–2025 · 单位：万元 · 数据取自各年年报「管理层讨论与分析——成本分析表」，分别按成本性质与分产品/业务两个口径加总</p>
        <div class="kpis">
          <div class="kpi"><div class="label">2025 主营业务成本合计</div><div class="value">13.28 亿</div><div class="delta up">▲ 8.4%</div></div>
          <div class="kpi"><div class="label">2025 直接材料占比</div><div class="value">68.2%</div><div class="delta down">▼ 2020 为 76.5%</div></div>
          <div class="kpi"><div class="label">2025 直接人工占比</div><div class="value">12.9%</div><div class="delta up">▲ 2020 为 9.0%</div></div>
          <div class="kpi"><div class="label">2025 制造费用占比</div><div class="value">11.9%</div><div class="delta up">▲ 2020 为 8.9%</div></div>
        </div>
        <div class="two-col">
          <div>
            <h3 class="chart-title">按成本性质构成（万元）</h3>
            <div id="chart-cost-nature" class="chart" style="height:400px"></div>
          </div>
          <div>
            <h3 class="chart-title">按成本性质占比（%）</h3>
            <div id="chart-cost-nature-pct" class="chart" style="height:400px"></div>
          </div>
        </div>
        <div class="note">
          主营业务成本从 2020 年 <b>7.03 亿元</b>增至 2025 年 <b>13.28 亿元</b>（六年 +88.9%，与营收扩张同步）。结构上呈现明显的<b>「材料占比下降、人工与制造费用刚性上升」</b>：
          <b>直接材料</b>始终是绝对大头，但占比从 2020 年的 <b>76.5%</b> 一路降至 2025 年的 <b>68.2%</b>——反映集中采购与规模效应对猪肉、面粉、油脂等原料成本的摊薄；
          <b>直接人工</b>占比由 9.0% 升至 12.9%、<b>制造费用</b>由 8.9% 升至 11.9%——中央厨房产能扩张带来的折旧、能源与人力刚性支出持续抬升，是压制综合毛利率的主要成本项；
          <b>合同履约成本</b>（执行新收入准则后计入营业成本的运杂费等）稳定在 5.4%–6.1%，随配送规模同步增长。这一成本结构变化与「盈利能力」章节中扣非净利率靠精细化管理才勉强维稳的判断相互印证。<br>
          口径说明：年报未单列全公司「纯按成本性质」汇总表，本图由「成本分析表——分行业情况」中食品类 / 加盟商管理 / 包装物及辅料三类的同性质项目加总而得（其中「其他费用」仅出现在加盟商管理类）；统计口径为<b>主营业务成本</b>，与利润表「营业成本」总额有微小尾差（如 2020 年主营业务成本 70,281.20 万元 vs 利润表营业成本 70,306.92 万元）；2020 年起「合同履约成本」为新收入准则下新增项目。<br>
          数据来源：巴比食品 A 股各年年度报告「第三节 管理层讨论与分析——成本分析表（分行业情况）」。
        </div>
        <h3 class="chart-title">按产品 / 业务构成（万元）</h3>
        <div id="chart-cost-product" class="chart" style="height:400px"></div>
        <div class="note">
          按<b>产品 / 业务</b>拆分同一口径的主营业务成本可见：<b>食品类三项</b>（面米类 + 馅料类 + 外购食品类）合计约占主营成本<b>九成</b>，是成本的绝对主体。
          <b>面米类</b>（2022 年报起口径由「面点类」改称「面米类」）为最大单项，从 2020 年 <b>2.31 亿元</b>攀升至 2024 年 <b>5.28 亿元</b>，2025 年微降至 <b>5.13 亿元</b>；
          <b>馅料类</b>与<b>外购食品类</b>在 2022 年一度回落后于 2025 年明显反弹（分别 +17.7% / +17.6%），对应终端 SKU 扩充与外采占比回升。
          <b>外购食品类</b>系向第三方采购的成品/半成品，无自有产线加工，故成本仅由直接材料与合同履约成本构成、不含直接人工与制造费用。
          <b>加盟商管理</b>成本（主要为服务加盟体系的人工）随加盟网络扩张持续攀升，从 2020 年 <b>1,477 万元</b>增至 2025 年 <b>5,334 万元</b>（六年 3.6 倍）。<br>
          口径说明：分产品口径与前述按成本性质口径同源、总额一致（均为主营业务成本）；「面点类」自 2022 年年报起统一改称「面米类」，本图按最新口径统一命名；2023 年报「包装物及辅料」部分行次因分页截断，经 2024 年报「上年同期」列交叉补齐。<br>
          数据来源：巴比食品 A 股各年年度报告「第三节 管理层讨论与分析——成本分析表（分产品情况）」，本地存档 data/raw/annual_605338_2020…2025.txt。
        </div>
      </section>
      <!-- ══════════ 3 渠道分部 ══════════ -->
      <section id="sec-channel">
        <h2>渠道分部（特许加盟 / 团餐大客户 / 直营门店）</h2>
        <p class="sub">口径：主营业务分渠道收入 · 2020 年为上市当年、含完整年度 · 单位：亿元</p>
        <div id="chart-channel" class="chart" style="height:400px"></div>
        <div class="note">
          <b>特许加盟</b>是绝对核心渠道，收入由 2020 年 8.13 亿元增至 2024 年 12.46 亿元、2025 年回升至 <b>13.74 亿元</b>（+10.23%），常年占营收七成以上；
          <b>团餐大客户</b>是主要增长引擎，从 2020 年 1.33 亿元一路增至 2024 年 3.80 亿元（连续两年增速超 50% 后趋稳）、2025 年团餐+大客户及零售业务合计 4.32 亿元（+13.54%），2024 年新开发大客户超 300 家（含盒马、美团快驴等），占营收比重升至约 22.8%；
          <b>直营门店</b>收入占比一直很小且逐年收缩（2024 仅 0.21 亿元、-22.83%，门店仅个位数）。
          分产品看，2025 年前三季度食品类收入占比 90.40%（其中面米类 37.51%、馅料类 28.63%、外购食品类 23.98%），包装及辅料占 6.22%、服务费收入占 3.28%。<br>
          数据来源：2020 年分渠道收入（特许加盟 8.13 / 直营 0.12 / 团餐 1.33 亿元）取自公司《2020 年年度报告》主营业务分销售模式明细（新浪财经）；2022 年特许加盟 11.38 亿元取自公司 2022 年报（界面新闻转述，+1.54%）；
          2021/2023/2024 取自历年年报；2025 年特许加盟 13.74 亿元、大客户及零售合计 4.32 亿元取自《2025 年年度报告》全文（新浪财经转述）；分产品占比取自《2025 年第三季度经营数据公告》（2025-10-31）。
        </div>
      </section>

      <!-- ══════════ 4 门店与区域 ══════════ -->
      <section id="sec-store-region">
        <h2>门店规模与区域结构</h2>
        <p class="sub">口径：加盟门店期末总数（家）· 分区域营业收入（亿元 / %，2025 年）</p>
        <div class="two-col">
          <div>
            <h3 class="chart-title">加盟门店期末总数（家）</h3>
            <div id="chart-store" class="chart" style="height:360px"></div>
          </div>
          <div>
            <h3 class="chart-title">2025 年分区域收入占比（华东依赖）</h3>
            <div id="chart-region" class="chart" style="height:360px"></div>
          </div>
        </div>
        <div class="note">
          <b>门店：</b>加盟门店由 2020 年末 3,089 家逐年扩张至 2021 年末 3,461 家、2022 年末 4,473 家、2023 年末 5,043 家、2024 年末 5,143 家、2025 年末 <b>5,909 家</b>，
          上市以来期末门店存量年均复合增长率超 15%；2025 年净增主要靠并购整合（南京「青露」、浙江「馒乡人」等），中银证券指闭店率约为上年存量的 21%、有所上升；单店供货收入则连年被摊薄（见下节「单店营收贡献」）。
          2025 年 7 月起推出「巴比手工小笼包」新店型，日均营业额可达传统店 2 倍，年末已落地 24 家，计划 2026 年末冲刺 600–700 家。<br>
          <b>区域：</b>「华东依赖症」自上市起始终显著（华东以外门店占比由 2020 年末的 11% 升至 2022 年末的 24%）——2025 年华东贡献 15.26 亿元、占 <b>82.08%</b>，华南 1.57 亿（8.46%）、华中 1.13 亿、华北 0.60 亿、其他仅 312 万元。<br>
          数据来源：2018–2025 各年末加盟门店数取自历年 A 股年报「加盟门店平均收入情况」及分区域门店表（口径为期末在业门店，2022 年末 4,473 家为年报确数，此前页面沿用媒体转述的「突破 4,000 家」约数）；2020 年末门店区域占比取自 2022 年报；区域收入取自 2025 年报。
        </div>
      </section>
      <!-- ══════════ 4.2 单店营收贡献 ══════════ -->
      <section id="sec-unit-store">
        <h2>单店营收贡献：加盟 vs 直营</h2>
        <p class="sub">口径：年报披露的「加盟门店平均收入情况」/「直营门店平均收入情况」表 · 平均收入 = 当年该渠道收入 ÷ 期末在业门店数（万元/店）· 两者量级相差一个数量级，故上下各占一屏、不并排压缩</p>
        <h3 class="chart-title">加盟门店平均收入（万元/店）与加盟门店数</h3>
        <div id="chart-unit-franchise" class="chart" style="height:76vh;min-height:420px"></div>
        <h3 class="chart-title" style="margin-top:26px">直营门店平均收入（万元/店）与直营门店数</h3>
        <div id="chart-unit-direct" class="chart" style="height:76vh;min-height:420px"></div>
        <div class="note">
          <b>加盟单店在缩水：</b>加盟门店平均收入从 2018 年的 <b>33.16 万元</b>一路降到 2025 年的 <b>23.26 万元</b>（八年 -29.9%），
          其间只有 2021 年（疫情低基数后的反弹，32.39 万元）逆势回升。加盟渠道收入同期从 8.76 亿增至 13.74 亿（+56.9%），
          但门店数从 2,641 家增至 5,909 家（+123.7%）——<b>增长几乎全部来自铺店，单店供货额被摊薄</b>，且新增门店多在华东以外、并购品牌门店的客单与供货深度更低。
          2024→2025 单店仍降 4.0%，与「巴比手工小笼包」等高日销新店型的放量尚不足以对冲。<br>
          <b>直营是「少而精」的样板店：</b>直营门店数从 2019 年末的 16 家、2021 年末 19 家收缩到 2025 年末仅 <b>5 家</b>，
          单店收入却从 104.83 万元升至 <b>381.47 万元</b>——留下的是核心商圈样板店，关掉的是尾部店，属结构性抬升而非同店高增；
          直营总收入始终不到 2,000 万元（2025 年 1,907.33 万元，占营收约 1%），对报表几无影响，其价值在于新店型试验与品牌展示。<br>
          <b>两者不可直接比较：</b>加盟的「平均收入」是<b>公司对加盟商的批发供货收入</b>÷门店数（不含加盟商管理费，2025 年该项 5,638.54 万元单列于「加盟商管理」），
          并非门店终端零售流水；直营的「平均收入」是<b>门店终端零售收入</b>÷门店数，年报明确<b>不含线上旗舰店</b>（故与「分渠道收入」表中的直营口径自 2021 年起略有差异）。
          门店数均为<b>期末在业门店</b>，年内新开/关店会使分子分母不同步，快速扩张年份的单店值被系统性低估。<br>
          数据来源：巴比食品 A 股各年年度报告「加盟门店平均收入情况」「直营门店平均收入情况」表（2018/2019 取自 2020、2021 年报的可比栏），
          本地存档 data/raw/annual_605338_2020…2025.pdf/.txt。注：2020 年报直营表表头印为「2020/2018/2017 年度」，经与 2021 年报交叉核对，该三栏实为 2020/2019/2018 年度。
        </div>
      </section>

      <!-- ══════════ 4.5 外延并购 ══════════ -->
      <section id="sec-ma">
        <h2>外延并购：2025 年三笔区域品牌收购</h2>
        <p class="sub">口径：报告期内完成的股权收购与合并报表节点 · 数据取自《2025 年年度报告》全文「对外股权投资」章节</p>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>标的</th><th>收购主体</th><th>股权比例</th><th>纳入合并报表日</th><th>门店/供应链情况</th></tr></thead>
          <tbody>
            <tr><td>青露无双（南京「青露」品牌）</td><td>南京中茂</td><td>90%</td><td>2025-03-31</td><td>青露 + 无双品牌门店合计约 500 家，单月供应链收入约 780 万元</td></tr>
            <tr><td>巴比九江</td><td>巴比武汉</td><td>75%</td><td>2025-03-31</td><td>华中区域网点加密</td></tr>
            <tr><td>巴比馒乡人（浙江「馒乡人」品牌）</td><td>公司本级</td><td>70%</td><td>2025-09-30</td><td>门店约 250 家（浙江嘉兴、湖州），供应链端收入约 5,000 万元/年</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note">
          公司「内生开店 + 外延并购」双轮驱动区域整合：青露无双、巴比九江已于 2025 年一季度完成股权工商变更并纳入合并报表；
          馒乡人项目节奏更长——2025 年 6 月签约、7 月完成供应链切换、8–9 月推进股权转让，最终 9 月末并表。
          三笔并购均为控股型收购（70%–90%），保留少数股东权益，帮助公司在华东（南京）、华中（九江）、华东外围（浙江）三个方向补强密度与下沉。<br>
          数据来源：《2025 年年度报告》全文「第三节 管理层讨论与分析」（新浪财经 2026-04 转述）；馒乡人并购节奏另参考公司《投资者关系活动记录表》（2025-08-22）。
        </div>
      </section>
      <!-- ══════════ 5 东鹏饮料公允价值扰动 ══════════ -->
      <section id="sec-fairvalue">
        <h2>东鹏饮料公允价值变动：净利润的“扰动项”</h2>
        <p class="sub">口径：合并利润表「公允价值变动收益」· 单位：亿元 · 通过天津君正投资间接持有东鹏饮料股份</p>
        <div id="chart-fairvalue" class="chart" style="height:360px"></div>
        <div class="note">
          公司通过天津君正投资间接持有东鹏饮料股份（早年成本仅约 3.5 亿元，一度浮盈十余倍）。<b>2020 年（上市当年）东鹏尚未上市，该项对损益基本无扰动</b>；
          东鹏 2021 年 5 月上市后，其股价波动经「公允价值变动收益」直接进当期损益：2021 年贡献约 <b>1.96 亿元</b>（占利润总额 62.34%）、2022 年骤降至 0.35 亿、2023 年 0.14 亿、
          2024 年因东鹏反弹回升至 <b>0.91 亿元</b>（占当年归母净利三成以上，+543.76%）。2025 年天津君正持续减持、已退出东鹏前十大股东（持股降至 1% 以下），
          公允价值变动收益与投资收益合计较上年减少约 0.94 亿元，昔日「业绩引擎」转为短期拖累，直接导致 2025 年归母净利润小幅回落 1.28%（而扣非 +16.66%）。<br>
          数据来源：2024 年公允价值变动收益 9,116.32 万元、2023 年 1,416.11 万元取自《2024 年度财务决算报告》；2021 年约 1.96 亿元取自公司 2021 年报及界面新闻/财闻网报道（其中东鹏部分约 1.47 亿元）；2020 年东鹏未上市、无该项扰动；2025 年变动取自新浪财经 2026-04 报道所引 2025 年报。
        </div>
      </section>

      <!-- ══════════ 6 三张表 ══════════ -->
      <section id="sec-statements">
        <h2>三张财务报表（要点）</h2>
        <p class="sub">合并口径 · 单位：人民币万元 · 括号内为负值 · 数据取自公司《年度财务决算报告》，明细请查阅年报全文</p>

        <h3 style="color:#6c3483;margin:12px 0 8px;font-size:18px">上市以来核心损益一览（2020–2025，亿元）</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>指标</th><th>2020</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>营业收入</td><td>9.75</td><td>13.75</td><td>15.25</td><td>16.30</td><td>16.71</td><td>18.59</td></tr>
            <tr><td>归母净利润</td><td>1.75</td><td>3.14</td><td>2.22</td><td>2.14</td><td>2.77</td><td>2.73</td></tr>
            <tr><td>扣非归母净利润</td><td>1.29</td><td>1.52</td><td>1.85</td><td>1.78</td><td>2.10</td><td>2.45</td></tr>
            <tr class="row-sub"><td>公允价值变动收益（东鹏）</td><td>≈0</td><td>1.96</td><td>0.35</td><td>0.14</td><td>0.91</td><td>↓</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note" style="margin-top:6px">
          2020 年为上市当年、东鹏尚未上市；2025 年公允价值变动收益随天津君正减持大幅下降（与投资收益合计同比减少约 0.94 亿元，年报未单列具体金额，以「↓」示意）。
          营收与扣非归母净利上市以来持续增长，归母净利则因东鹏公允价值损益而波动。数据来源同上（2020/2021 历年年报、2022–2024 财务决算报告、2025 业绩快报/年报）。
        </div>

        <h3 style="color:#6c3483;margin:22px 0 8px;font-size:18px">近三年主要会计数据（2025 / 2024 / 2023，精确值）</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>项目</th><th>2025 年</th><th>2024 年</th><th>2023 年</th><th>25 vs 24</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>营业收入（万元）</td><td>185,905.00</td><td>167,145.00</td><td>163,023.33</td><td class="up">+11.22%</td></tr>
            <tr><td>利润总额（万元）</td><td>35,426.65</td><td>36,627.95</td><td>28,207.65</td><td class="down">-3.28%</td></tr>
            <tr><td>归属于上市公司股东的净利润（万元）</td><td>27,303.91</td><td>27,659.33</td><td>21,371.55</td><td class="down">-1.28%</td></tr>
            <tr><td>扣非归母净利润（万元）</td><td>24,519.05</td><td>21,017.55</td><td>17,803.52</td><td class="up">+16.66%</td></tr>
            <tr><td>经营活动产生的现金流量净额（万元）</td><td>31,941.75</td><td>21,739.04</td><td>24,442.46</td><td class="up">+46.93%</td></tr>
            <tr class="row-sub"><td>加权平均净资产收益率</td><td>11.97%</td><td>12.24%</td><td>10.02%</td><td class="down">-0.27pct</td></tr>
            <tr class="row-sub"><td>基本每股收益（元/股）</td><td>1.14</td><td>1.12</td><td>0.86</td><td class="up">+1.79%</td></tr>
            <tr class="row-total"><td>总资产（万元，期末）</td><td>289,890.73</td><td>285,312.56</td><td>278,119.14</td><td class="up">+1.60%</td></tr>
            <tr class="row-total"><td>归属于上市公司股东的净资产（万元，期末）</td><td>233,746.36</td><td>226,543.73</td><td>220,247.38</td><td class="up">+3.18%</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note" style="margin-top:6px">数据来源：《2025 年年度报告摘要》「3.1 近 3 年的主要会计数据和财务指标」（上交所 www.sse.com.cn，2026-04-10 披露）。</div>
        <h3 style="color:#6c3483;margin:22px 0 8px;font-size:18px">利润表（2024 / 2023 / 2022）</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>项目</th><th>2024 年</th><th>2023 年</th><th>2022 年</th><th>24 vs 23</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>营业收入</td><td>167,145.00</td><td>163,023.33</td><td>152,514.14</td><td class="up">+2.53%</td></tr>
            <tr><td>公允价值变动收益</td><td>9,116.32</td><td>1,416.11</td><td>3,512.00</td><td class="up">+543.76%</td></tr>
            <tr><td>信用减值损失</td><td class="neg">(103.15)</td><td class="neg">(33.53)</td><td>—</td><td class="up">+207.63%</td></tr>
            <tr><td>资产减值损失</td><td class="neg">(29.79)</td><td class="neg">(4.00)</td><td>—</td><td class="up">+643.86%</td></tr>
            <tr class="row-total"><td>营业利润</td><td>35,259.80</td><td>25,226.62</td><td>—</td><td class="up">+39.77%</td></tr>
            <tr><td>营业外收入</td><td>1,667.04</td><td>3,518.73</td><td>—</td><td class="down">-52.62%</td></tr>
            <tr class="row-total"><td>利润总额</td><td>36,627.95</td><td>28,207.65</td><td>—</td><td class="up">+29.85%</td></tr>
            <tr><td>所得税费用</td><td class="neg">(8,625.63)</td><td class="neg">(6,673.38)</td><td>—</td><td class="up">+29.25%</td></tr>
            <tr class="row-total"><td>净利润</td><td>28,002.32</td><td>21,534.27</td><td>—</td><td class="up">+30.04%</td></tr>
            <tr><td>归属于母公司股东净利润</td><td>27,659.33</td><td>21,371.55</td><td>22,271.34</td><td class="up">+29.42%</td></tr>
            <tr><td>扣非归母净利润</td><td>21,017.55</td><td>17,803.52</td><td>18,506.14</td><td class="up">+18.05%</td></tr>
          </tbody>
        </table>
        </div>

        <h3 style="color:#6c3483;margin:22px 0 8px;font-size:18px">资产负债表（期末，2024 / 2023）</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>项目</th><th>2024 年末</th><th>2023 年末</th><th>同比</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>总资产</td><td>285,312.56</td><td>—</td><td>—</td></tr>
            <tr class="row-total"><td>负债合计</td><td>57,180.63</td><td>57,037.77</td><td class="up">+0.25%</td></tr>
            <tr class="row-total"><td>所有者权益合计</td><td>228,131.93</td><td>221,081.37</td><td class="up">+3.19%</td></tr>
            <tr><td>归属于母公司股东权益</td><td>226,543.73</td><td>220,247.38</td><td class="up">+2.86%</td></tr>
            <tr class="row-sub"><td>其中：股本</td><td>24,800.00</td><td>25,011.38</td><td class="down">-0.85%</td></tr>
            <tr class="row-sub"><td>其中：未分配利润</td><td>123,470.10</td><td>105,663.13</td><td class="up">+16.85%</td></tr>
            <tr class="row-sub"><td>减：库存股</td><td>11,988.54</td><td>3,210.79</td><td class="up">+273.38%</td></tr>
            <tr><td>少数股东权益</td><td>1,588.20</td><td>833.99</td><td class="up">+90.43%</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note" style="margin-top:6px">资产负债率约 20%（2024 末 = 负债 5.72 亿 ÷ 总资产 28.53 亿）；每股净资产约 9.13 元（归母权益 22.65 亿 ÷ 2.48 亿股），财务结构稳健、几无有息负债。</div>

        <h3 style="color:#6c3483;margin:22px 0 8px;font-size:18px">现金流量表（经营活动净额）</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>项目</th><th>2024 年</th><th>2023 年</th><th>2022 年</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>经营活动产生的现金流量净额</td><td>21,739.04</td><td>24,442.46</td><td>19,190.36</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note">2024 年经营性现金流净额 2.17 亿元（-11.06%），与净利润基本匹配、现金创造能力稳定。数据来源：公司 2022/2023/2024《年度财务决算报告》（cninfo 巨潮）。</div>
      </section>
      <!-- ══════════ 6.5 股东情况 ══════════ -->
      <section id="sec-holders">
        <h2>股东情况</h2>
        <p class="sub">口径：报告期末（2025-12-31）· 数据取自《2025 年年度报告》全文「股份变动及股东情况」</p>
        <div class="kpis">
          <div class="kpi"><div class="label">报告期末普通股股东总数</div><div class="value">12,120 户</div><div class="delta down">披露日前一月末 12,229 户</div></div>
          <div class="kpi"><div class="label">前十大股东合计</div><div class="value">69.91%</div><div class="delta">高度集中，实控人系占主导</div></div>
          <div class="kpi"><div class="label">实控人 刘会平</div><div class="value">42.24%</div><div class="delta">101,193,300 股，报告期内无变动</div></div>
        </div>
        <div style="overflow-x:auto">
        <table>
          <thead><tr><th>股东名称</th><th>股东性质</th><th>期末持股数量（股）</th><th>持股比例</th><th>报告期内增减（股）</th></tr></thead>
          <tbody>
            <tr class="row-total"><td>刘会平</td><td>境内自然人</td><td>101,193,300</td><td>42.24%</td><td>0</td></tr>
            <tr><td>丁仕梅</td><td>境内自然人</td><td>19,027,800</td><td>7.94%</td><td>0</td></tr>
            <tr><td>天津会平投资管理合伙企业（有限合伙）</td><td>其他</td><td>13,206,242</td><td>5.51%</td><td class="down">-180,900</td></tr>
            <tr><td>天津中饮投资管理合伙企业（有限合伙）</td><td>其他</td><td>9,231,029</td><td>3.85%</td><td class="down">-731,200</td></tr>
            <tr><td>天津巴比投资管理合伙企业（有限合伙）</td><td>其他</td><td>8,160,729</td><td>3.41%</td><td class="down">-1,102,800</td></tr>
            <tr><td>潘和杰</td><td>境内自然人</td><td>5,550,000</td><td>2.32%</td><td class="down">-565,800</td></tr>
            <tr><td>丁仕霞</td><td>境内自然人</td><td>4,555,000</td><td>1.90%</td><td>0</td></tr>
            <tr><td>基本养老保险基金一零零一组合</td><td>其他</td><td>3,000,000</td><td>1.25%</td><td class="down">-3,084,900</td></tr>
            <tr><td>中国平安保险（集团）股份有限公司企业年金计划－招商银行股份有限公司</td><td>其他</td><td>1,986,806</td><td>0.83%</td><td class="up">+1,986,806</td></tr>
            <tr><td>招商银行股份有限公司－易方达裕鑫债券型证券投资基金</td><td>其他</td><td>1,574,400</td><td>0.66%</td><td class="up">+1,574,400</td></tr>
          </tbody>
        </table>
        </div>
        <div class="note">
          股权结构高度集中于创始人家族及其关联持股平台：刘会平（董事长、实控人）直接持股 42.24%，
          配偶丁仕梅持股 7.94%，二人合计约 50.18%；另通过天津会平、天津中饮、天津巴比三个投资平台合计持有 12.77%（报告期内三平台均有小幅减持）。
          丁仕霞（丁仕梅姐妹）持股 1.90%。刘会平系天津巴比、天津会平、天津中饮的有限合伙人。除上述关联关系外，公司未知其他股东间存在关联关系或一致行动。
          前十大股东合计 <b>69.91%</b>（年报该表无「合计」行，此处为逐行比例相加；此前本页写的 70.72% 与原文逐行相加不符，已按原文改正），
          机构类股东（养老金组合、企业年金、债券基金）持股占比均较小（≤1.25%），报告期内养老金一零零一组合大幅减持 308.49 万股，
          两只机构产品（企业年金、易方达裕鑫债券基金）为新进十大股东。<br>
          数据来源：《2025 年年度报告》全文「第六节 股份变动及股东情况」，本地存档 data/raw/annual_605338_2025.pdf/.txt（上交所 www.sse.com.cn）。
          逐年（2020–2025）的股本变动、股东户数、前十名股东与集中度序列见
          <a href="../shareholder.html?code=605338">股权结构页</a>。
        </div>
      </section>
      <!-- ══════════ 8.5 研发投入 ══════════ -->
      <section id="sec-rd">
        <h2>研发与产品创新</h2>
        <p class="sub">口径：报告期内（2025 年）· 数据取自《2025 年年度报告》全文「管理层讨论与分析——工艺革新品质提升」</p>
        <div class="cards three-col">
          <div class="card2">
            <h3>新品开发</h3>
            <p>报告期内各地研发团队开发（含半成品菜）产品 <b>144 款</b>，其中 98 款已上市试销、46 款储备排期后续上市；核心爆款包括南瓜红豆卷、冬笋酱肉包等。</p>
          </div>
          <div class="card2">
            <h3>工艺革新</h3>
            <p>完成 <b>112 款</b>产品改良升级；冷冻生胚包子技术取得重大突破，并持续优化青菜馅保鲜工艺、鲜肉馅保汤技术。</p>
          </div>
          <div class="card2">
            <h3>产学研合作</h3>
            <p>与江南大学共建联合实验室，与河南工业大学建立技术工作站，联合攻克面粉面团品质管控、老面面点现代智造加工技术、米面制品与功能食品研发等课题。</p>
          </div>
          <div class="card2">
            <h3>行业获奖</h3>
            <p>第八届 iSEE 全球奖：冷冻生胚包子技术获评「创新技术百强」，南瓜红豆卷荣获「全球美味奖」三星奖章。</p>
          </div>
          <div class="card2">
            <h3>研发设施投入</h3>
            <p>上海智能制造及功能性面食国际研发中心项目预计 2026 年上半年竣工；五年间在上海、武汉、南京等地布局 5 个中央厨房，累计投入 2.1 亿元引入先进生产与质检设备。</p>
          </div>
          <div class="card2">
            <h3>说明</h3>
            <p>公司《2025 年年度报告摘要》未单列「研发投入总额」「研发投入占营业收入比例」等量化指标，年报全文亦以定性成果描述为主，本页暂以上述定性数据呈现；参考东吴证券预测模型，2024 年研发费用约 1,200 万元量级（研究所测算，非公司披露口径）。</p>
          </div>
        </div>
        <div class="note">数据来源：《2025 年年度报告》全文「第三节 管理层讨论与分析」（新浪财经 2026-04 转述）；研发费用量级参考东吴证券《巴比食品 2025 一季报点评》财务预测表（2025-04-25，非公司官方披露数据，仅供参考）。</div>
      </section>


      <section id="sec-dividend">
        <h2>分红与股东回报</h2>
        <p class="sub">来源：公司历年利润分配预案 / 年报</p>
        <div class="cards">
          <div class="card2">
            <h3>2024 年度分红</h3>
            <ul>
              <li>每 10 股派现金红利 8.00 元（含税）</li>
              <li>折算分红率约 <b>71.43%</b></li>
            </ul>
          </div>
          <div class="card2">
            <h3>2025 年度分红预案</h3>
            <ul>
              <li>每 10 股派现金红利 12.00 元（含税）</li>
              <li>现金分红总额约 2.87 亿元（总股本 2.396 亿股）</li>
              <li>占 2025 年归母净利润比例 <b>105.29%</b>（超额分红）</li>
            </ul>
          </div>
          <div class="card2">
            <h3>股本变动</h3>
            <p>因股权激励与回购注销，总股本由 2.50 亿股降至 2024 末 2.48 亿股、2025 年进一步降至约 2.396 亿股；库存股规模上升。</p>
          </div>
        </div>
        <div class="note">分红预案需经股东会审议通过后实施。数据来源：公司 2024/2025 年度利润分配预案（2026-04-08 第四届董事会第二次会议）、2025 年年报摘要。</div>
      </section>
      <!-- ══════════ 8 业务亮点与前瞻 ══════════ -->
      <section id="sec-outlook">
        <h2>业务亮点与前瞻</h2>
        <p class="sub">来源：2025 年报致股东信、投资者关系活动记录表</p>
        <div class="cards three-col">
          <div class="card2">
            <h3>双轮驱动</h3>
            <p>特许加盟（核心，占七成以上）+ 团餐大客户（增长引擎），协同扩张；直营占比极小。</p>
          </div>
          <div class="card2">
            <h3>新店型：手工小笼包</h3>
            <p>2025 年 7 月推出，日均营业额约为传统店 2 倍；年末 24 家，2026 年目标 600–700 家。</p>
          </div>
          <div class="card2">
            <h3>外延并购整合</h3>
            <p>已完成/推进「蒸全味」「青露（南京）」「馒乡人（浙江）」等区域品牌并购，加速全国化。</p>
          </div>
          <div class="card2">
            <h3>开店节奏</h3>
            <p>2025 年内生仍计划新开约 1,000 家；优先开店质量、降低闭店率，给加盟商信心。</p>
          </div>
          <div class="card2">
            <h3>主要风险</h3>
            <p>华东依赖、行业竞争加剧（便利店/连锁/夫妻店/茶饮跨界）、单店客流下滑、原材料（猪肉/面粉/油脂）成本波动、加盟商管理、食品安全。</p>
          </div>
          <div class="card2">
            <h3>东鹏影响弱化</h3>
            <p>天津君正持续减持东鹏至 1% 以下，公允价值损益对净利润的扰动将逐步下降，业绩“含金量”回归主业。</p>
          </div>
        </div>
        <div class="note">以上为定性经营信息与公司披露的计划，不构成投资建议。</div>
      </section>

      <div class="note" style="text-align:center;margin-top:22px">
        数据来源：中饮巴比食品股份有限公司 2022/2023/2024《年度财务决算报告》及 2025 年年度报告（全文/摘要，上交所 www.sse.com.cn、cninfo 巨潮），
        公司投资者关系活动记录表（2025-03-28），华福证券/天风证券财报点评（转述年报数据），新浪财经/界面新闻/经济参考报等公开报道。
        本页仅作数据可视化，不构成投资建议。
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

// 逐字搬自 dashboard/company/food/overview.html 底部内联 <script>：13 个 ECharts option 与其
// 内联数据（years/catering/retail/nature/product/panels 等）原样保留。数据来源为内联（无 /api、
// 无同目录本地 .js），字段/数值/口径不改。仅两处适配以适应 SPA：initChart 由
// document.getElementById 改为组件根 ref 内 querySelector；window.resize / 卸载 dispose 改为
// 遍历收集到的实例（与原页 resize 里按 id 数组 resize 等价）。
const rootEl = ref(null)
let charts = []

function initChart(id) {
  const el = rootEl.value ? rootEl.value.querySelector('#' + id) : null
  if (!el) return null
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}
const RED = '#c0392b', PURPLE = '#6c3483', ORANGE = '#d35400', BLUE = '#2471a3', GREEN = '#1e8449', GOLD = '#c9a24a';
const AX = { fontSize: 18 };

function onResize() { charts.forEach(c => c.resize()) }

onMounted(() => {
    // 0.5 行业背景：全国餐饮收入及其占社零比重
    (function () {
        const years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017',
                       '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'];
        // 餐饮收入、社零总额均为国家统计局当年 12 月发布稿口径（亿元）
        const catering = [17636, 20543, 23283, 25392, 27860, 32310, 35799, 39644,
                          42716, 46721, 39527, 46895, 43941, 52890, 55718, 57982];
        const retail = [154553.7, 181225.8, 207166.7, 234380, 262394.1, 300930.8, 332316, 366261.6,
                        380986.9, 411649, 391980.6, 440823.2, 439732.5, 471495.2, 487894.8, 501202.4];
        const share = catering.map((v, i) => +(v / retail[i] * 100).toFixed(2));
        initChart('chart-catering')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: {
                trigger: 'axis', axisPointer: { type: 'shadow' },
                formatter: p => {
                    const i = p[0].dataIndex;
                    return years[i] + ' 年<br>餐饮收入：' + catering[i].toLocaleString() + ' 亿元'
                        + '<br>社零总额：' + retail[i].toLocaleString() + ' 亿元'
                        + '<br>占社零比重：' + share[i] + '%';
                }
            },
            legend: { top: 4, textStyle: AX },
            grid: { left: 92, right: 92, top: 52, bottom: 48 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: [
                { type: 'value', name: '亿元', min: 0, axisLabel: AX, nameTextStyle: AX },
                { type: 'value', name: '占社零比重 %', min: 9, max: 12, interval: 0.5,
                  splitLine: { show: false }, axisLabel: AX, nameTextStyle: AX }
            ],
            series: [
                { name: '全国餐饮收入', type: 'bar', yAxisIndex: 0, data: catering, barWidth: '52%',
                  itemStyle: { color: '#aeb6bf' } },
                { name: '占社会消费品零售总额比重', type: 'line', yAxisIndex: 1, data: share,
                  smooth: false, symbolSize: 9, lineStyle: { color: RED, width: 3 }, itemStyle: { color: RED },
                  label: { show: true, position: 'top', fontSize: 15, color: RED, formatter: '{c}' } }
            ]
        });
    })();
    // 1 业绩走势
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024', '2025'];
        initChart('chart-perf')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 64, right: 24, top: 46, bottom: 56 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '亿元', min: 0, axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '营业收入', type: 'bar', data: [9.75, 13.75, 15.25, 16.30, 16.71, 18.59],
                  itemStyle: { color: '#aeb6bf' }, barWidth: '46%' },
                { name: '归母净利润', type: 'line', smooth: true, symbolSize: 8,
                  data: [1.75, 3.14, 2.22, 2.14, 2.77, 2.73], lineStyle: { color: RED, width: 3 }, itemStyle: { color: RED } },
                { name: '扣非归母净利', type: 'line', smooth: true, symbolSize: 8,
                  data: [1.29, 1.52, 1.85, 1.78, 2.10, 2.45], lineStyle: { color: ORANGE, width: 3, type: 'dashed' }, itemStyle: { color: ORANGE } }
            ]
        });
    })();

    // 1.5 分季度业绩
    (function () {
        const qs = ['Q1', 'Q2', 'Q3', 'Q4'];
        initChart('chart-quarter')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 68, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: qs, axisLabel: AX },
            yAxis: { type: 'value', name: '亿元', axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '营业收入', type: 'bar', data: [3.70, 4.65, 5.22, 5.03],
                  itemStyle: { color: '#aeb6bf' }, barWidth: '46%' },
                { name: '归母净利润', type: 'line', smooth: true, symbolSize: 8,
                  data: [0.37, 0.94, 0.70, 0.72], lineStyle: { color: RED, width: 3 }, itemStyle: { color: RED } },
                { name: '扣非归母净利', type: 'line', smooth: true, symbolSize: 8,
                  data: [0.39, 0.62, 0.74, 0.70], lineStyle: { color: ORANGE, width: 3, type: 'dashed' }, itemStyle: { color: ORANGE } }
            ]
        });
    })();
    // 2 盈利能力
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024', '2025'];
        initChart('chart-margin')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '-' : v + '%' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 56, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '%', axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '归母净利率', type: 'line', smooth: true, symbolSize: 8,
                  data: [17.9, 22.84, 14.60, 13.11, 16.55, 14.69], lineStyle: { color: RED, width: 3 }, itemStyle: { color: RED } },
                { name: '扣非归母净利率', type: 'line', smooth: true, symbolSize: 8,
                  data: [13.2, 11.05, 12.13, 10.92, 12.57, 13.18], lineStyle: { color: PURPLE, width: 3 }, itemStyle: { color: PURPLE } }
            ]
        });
    })();

    // 2.5 营业成本构成（按成本性质）
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024', '2025'];
        // 主营业务成本按性质（万元）—— 由年报「成本分析表·分行业」三类同性质项加总
        const nature = [
            { name: '直接材料',     color: RED,        data: [53733.44, 78164.54, 78840.14, 84331.28, 84691.53, 90611.23] },
            { name: '直接人工',     color: BLUE,       data: [6356.32, 10005.67, 15390.84, 16486.74, 16704.94, 17169.69] },
            { name: '制造费用',     color: ORANGE,     data: [6272.43, 8612.72, 9412.78, 11693.11, 12946.37, 15860.03] },
            { name: '合同履约成本', color: GOLD,       data: [3817.84, 5269.38, 6182.35, 6847.72, 7392.49, 8133.10] },
            { name: '其他费用',     color: '#aeb6bf',  data: [101.17, 137.31, 422.47, 700.13, 752.23, 1005.31] }
        ];
        const total = years.map((_, i) => nature.reduce((s, n) => s + n.data[i], 0));

        // 左：金额堆叠
        initChart('chart-cost-nature')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
                valueFormatter: v => v == null ? '-' : (+v).toLocaleString() + ' 万元' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 88, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '万元', min: 0, axisLabel: AX, nameTextStyle: AX },
            series: nature.map(n => ({
                name: n.name, type: 'bar', stack: 'cost', data: n.data, itemStyle: { color: n.color }
            }))
        });

        // 右：占比 100% 堆叠
        initChart('chart-cost-nature-pct')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
                valueFormatter: v => v == null ? '-' : v + '%' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 56, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '%', min: 0, max: 100, axisLabel: AX, nameTextStyle: AX },
            series: nature.map(n => ({
                name: n.name, type: 'bar', stack: 'pct', itemStyle: { color: n.color },
                data: n.data.map((v, i) => +(v / total[i] * 100).toFixed(1))
            }))
        });
    })();
    // 2.6 营业成本构成（按产品 / 业务）
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024', '2025'];
        // 主营业务成本按产品/业务（万元）—— 年报「成本分析表·分产品」，2022 年报起「面点类」改称「面米类」
        const product = [
            { name: '面米类',       color: RED,       data: [23096.72, 36373.50, 48231.76, 51410.23, 52846.24, 51316.09] },
            { name: '馅料类',       color: PURPLE,    data: [21408.66, 27364.00, 23934.49, 27805.39, 29966.90, 35268.32] },
            { name: '外购食品类',   color: ORANGE,    data: [19158.35, 29789.92, 27984.40, 29258.15, 28202.04, 33172.66] },
            { name: '包装物及辅料', color: BLUE,      data: [5140.71, 6439.71, 6563.22, 7041.37, 6970.78, 7688.61] },
            { name: '加盟商管理',   color: '#aeb6bf', data: [1476.76, 2222.49, 3534.71, 4543.85, 4501.62, 5333.69] }
        ];

        initChart('chart-cost-product')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
                valueFormatter: v => v == null ? '-' : (+v).toLocaleString() + ' 万元' },
            legend: { top: 4, textStyle: AX },
            grid: { left: 88, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '万元', min: 0, axisLabel: AX, nameTextStyle: AX },
            series: product.map(p => ({
                name: p.name, type: 'bar', stack: 'prod', data: p.data, itemStyle: { color: p.color }
            }))
        });
    })();

    // 3 渠道分部
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024'];
        initChart('chart-channel')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            legend: { top: 4, textStyle: AX },
            grid: { left: 56, right: 24, top: 46, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '亿元', axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '特许加盟', type: 'bar', stack: 'ch', data: [8.13, 11.21, 11.38, 12.52, 12.46], itemStyle: { color: PURPLE } },
                { name: '团餐大客户', type: 'bar', stack: 'ch', data: [1.33, 2.15, 3.32, 3.30, 3.80], itemStyle: { color: RED } },
                { name: '直营门店', type: 'bar', stack: 'ch', data: [0.12, 0.26, 0.28, 0.27, 0.21], itemStyle: { color: '#aeb6bf' } }
            ]
        });
    })();
    // 4a 门店数
    (function () {
        const years = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'];
        initChart('chart-store')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { left: 66, right: 20, top: 30, bottom: 40 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '家', min: 0, axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '加盟门店', type: 'bar', data: [2641, 2915, 3089, 3461, 4473, 5043, 5143, 5909], barWidth: '46%',
                  itemStyle: { color: PURPLE },
                  label: { show: true, position: 'top', fontSize: 15, formatter: '{c}' } }
            ]
        });
    })();

    // 4b 区域结构
    (function () {
        initChart('chart-region')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'item', formatter: '{b}: {c} 亿元 ({d}%)' },
            legend: { bottom: 0, textStyle: AX },
            series: [{
                type: 'pie', radius: ['38%', '66%'], center: ['50%', '46%'],
                data: [
                    { name: '华东', value: 15.26, itemStyle: { color: RED } },
                    { name: '华南', value: 1.57, itemStyle: { color: PURPLE } },
                    { name: '华中', value: 1.13, itemStyle: { color: BLUE } },
                    { name: '华北', value: 0.60, itemStyle: { color: GOLD } },
                    { name: '其他', value: 0.03, itemStyle: { color: '#aeb6bf' } }
                ],
                label: { fontSize: 18, formatter: '{b} {d}%' }
            }]
        });
    })();
    // 4c 单店营收贡献（加盟 / 直营分列）
    (function () {
        const years = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'];
        // 平均收入 = 当年该渠道收入 ÷ 期末在业门店数（年报直接披露）
        const panels = [
            { id: 'chart-unit-franchise', color: PURPLE, avg: [33.16, 31.49, 26.31, 32.39, 25.45, 24.82, 24.23, 23.26],
              cnt: [2641, 2915, 3089, 3461, 4473, 5043, 5143, 5909], cntName: '加盟门店数', avgName: '加盟单店平均收入' },
            { id: 'chart-unit-direct', color: ORANGE, avg: [114.41, 104.83, 72.70, 130.64, 195.88, 138.10, 252.84, 381.47],
              cnt: [15, 16, 17, 19, 16, 18, 7, 5], cntName: '直营门店数', avgName: '直营单店平均收入' }
        ];
        panels.forEach(p => initChart(p.id)?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            legend: { top: 4, textStyle: AX },
            grid: { left: 88, right: 88, top: 52, bottom: 48 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: [
                { type: 'value', name: '万元/店', min: 0, axisLabel: AX, nameTextStyle: AX },
                { type: 'value', name: '家', min: 0, splitLine: { show: false }, axisLabel: AX, nameTextStyle: AX }
            ],
            series: [
                { name: p.avgName, type: 'bar', yAxisIndex: 0, data: p.avg, barWidth: '46%',
                  itemStyle: { color: p.color },
                  label: { show: true, position: 'top', fontSize: 18, formatter: '{c}' } },
                { name: p.cntName, type: 'line', yAxisIndex: 1, data: p.cnt, smooth: false,
                  symbolSize: 9, lineStyle: { width: 3 }, itemStyle: { color: '#aeb6bf' },
                  label: { show: true, position: 'bottom', fontSize: 16, color: '#7f8c8d', formatter: '{c}' } }
            ]
        }));
    })();

    // 5 东鹏公允价值
    (function () {
        const years = ['2020', '2021', '2022', '2023', '2024'];
        initChart('chart-fairvalue')?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => v + ' 亿元' },
            grid: { left: 60, right: 24, top: 30, bottom: 44 },
            xAxis: { type: 'category', data: years, axisLabel: AX },
            yAxis: { type: 'value', name: '亿元', axisLabel: AX, nameTextStyle: AX },
            series: [
                { name: '公允价值变动收益', type: 'bar', data: [0, 1.96, 0.35, 0.14, 0.91], barWidth: '46%',
                  itemStyle: { color: RED },
                  label: { show: true, position: 'top', fontSize: 18, formatter: '{c}' } }
            ]
        });
    })();

    window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', onResize)
    charts.forEach(c => { try { c.dispose() } catch (_) {} })
    charts = []
})
</script>

<style scoped>
/* 迁移 dashboard/company/page.css（该表未随 base.css 全局引入，需内联本页才能复现）。
   本页全部为静态模板节点（图容器亦为静态 <div>，ECharts 只在其中渲染 canvas），
   故整体用 scoped 收敛、不外泄到其它路由。base.css 已全局引入，其规则
   （.chart-title / .chart-card / #loading / #error-msg / .site-nav 等）此处不重复。
   page.css 原首行 body{min-height:100vh;overflow-y:auto} 未迁移——本页高度远超一屏，
   min-height 无可见影响、overflow-y:auto 为默认值，且全局 body 规则不宜由单页组件注入。
   末尾另附原页 <head> 内联的 .mini-nav 顶栏样式。 */
.wrap { max-width: var(--content-w, 1200px);   /* 正文列宽由 base.css 的 --content-w 统一管，不随全局 1.125 字号放大同比加宽 */ margin: 0 auto; padding: 24px 24px 60px; }
.page-head { text-align: center; margin-bottom: 8px; }
.page-head h1 { font-size: 29px; color: #1f2937; margin-bottom: 6px; }
.page-head .meta { color: #6b7280; font-size: 18px; line-height: 1.7; }
.page-head .tags { margin-top: 8px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.page-head .tags span {
    background: #dde8f3; color: #10243e; border-radius: 12px;
    padding: 3px 12px; font-size: 18px; font-weight: 500;
}
section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
          padding: 20px 22px; margin-top: 22px; }
section > h2 {
    font-size: 22px; color: #1f2937; margin-bottom: 4px;
    border-left: 4px solid #10243e; padding-left: 10px;
}
section > .sub { color: #6b7280; font-size: 18px; margin: 0 0 14px 14px; }
.chart { width: 100%; height: 428px; }   /* 380 × 1.125 */
/* 图上方的一排切换按钮（如 ROE 图的快速切换银行）：与石油页 .btn-row 同一视觉，
 * 选中态用深底白字，和 KPI 卡片的浅蓝底区分开 */
.chart-btns { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 10px 14px; }
.chart-btns .label { font-size: 18px; color: #6b7280; margin-right: 2px; }
.chart-btns button {
    font: inherit; font-size: 18px; color: #10243e; background: #f3f6fa;
    border: 1px solid #dde8f3; border-radius: 14px; padding: 4px 14px; cursor: pointer;
}
.chart-btns button:hover { background: #e6eef7; }
.chart-btns button.active { background: #10243e; border-color: #10243e; color: #fff; font-weight: 600; }
/* 一键对比：和「换成某一家行」不是同类动作，用白底描边+左侧留空跟单行按钮拉开距离 */
.chart-btns button.tier { background: #fff; border-color: #10243e; font-weight: 600; }
.chart-btns button.tier.active { background: #10243e; color: #fff; }
.chart-btns button.cmp { margin-left: 6px; background: #fff; border-color: #10243e; font-weight: 600; }
.chart-btns button.cmp:hover { background: #eef3f9; }
.chart-btns button.cmp.active { background: #10243e; color: #fff; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; margin-bottom: 16px; }
.kpi { background: #f3f6fa; border: 1px solid #dde8f3; border-radius: 8px; padding: 12px 14px; }
.kpi .label { font-size: 18px; color: #7f8c8d; }
.kpi .value { font-size: 25px; font-weight: 700; color: #10243e; margin-top: 4px; }
.kpi .delta { font-size: 18px; margin-top: 2px; }
.up { color: #c0392b; } .down { color: #1e8449; }
table { width: 100%; border-collapse: collapse; font-size: 18px; }
th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid #eee; }
th:first-child, td:first-child { text-align: left; }
thead th { background: #eef2f7; color: #10243e; font-weight: 600; border-bottom: 2px solid #c9a24a; }
tbody tr:hover { background: #f3f6fa; }
.row-total td { font-weight: 700; background: #f6f8fb; border-top: 2px solid #c9a24a; }
.row-sub td:first-child { padding-left: 26px; color: #555; font-weight: 400; }
/* 可排序表格：表头可点，箭头提示当前排序列及方向；data-sort="none" 列（如序号）不参与排序，无箭头/手型 */
table.sortable thead th { cursor: pointer; user-select: none; white-space: nowrap; }
table.sortable thead th:hover { background: #e3e9f0; }
table.sortable thead th::after { content: '⇕'; display: inline-block; margin-left: 5px; font-size: 14px; color: #b0bac5; }
table.sortable thead th[data-sort-dir="asc"]::after { content: '▲'; color: #c9a24a; }
table.sortable thead th[data-sort-dir="desc"]::after { content: '▼'; color: #c9a24a; }
table.sortable thead th[data-sort="none"] { cursor: default; }
table.sortable thead th[data-sort="none"]:hover { background: inherit; }
table.sortable thead th[data-sort="none"]::after { content: none; }
.neg { color: #c0392b; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px,420px)); gap: 14px; }
.card2 { background: #f3f6fa; border: 1px solid #dde8f3; border-radius: 8px; padding: 14px 16px; }
.card2 h3 { font-size: 18px; color: #10243e; margin-bottom: 6px; }
.card2 p { font-size: 18px; color: #444; line-height: 1.65; }
.card2 ul { margin: 4px 0 0 18px; font-size: 18px; color: #444; line-height: 1.7; }
.opinion-hero { margin: 18px 0 0; background: #f7faf8;
           border: 1px solid #dde8f3; border-left: 4px solid #1e8449; border-radius: 10px;
           padding: 10px 16px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.opinion-hero .tick { flex: 0 0 auto; background: #e3f2e8; color: #14663c;
           font-size: 18px; font-weight: 700; border-radius: 4px; padding: 3px 10px; }
.opinion-hero .txt { font-size: 18px; color: #37474f; }
.note { font-size: 18px; color: #9ca3af; margin: 10px auto 0; line-height: 1.6; max-width: 900px; }
/* 注释默认折叠：<details class="note"><summary>...</summary>正文</details>
 * 长注释展开后才占地方，避免默认状态就把阅读节奏拉得很长 */
.note summary { cursor: pointer; color: #6b7280; font-weight: 500; list-style: none; }
.note summary::-webkit-details-marker { display: none; }
.note summary::before { content: '▸ '; color: #9ca3af; }
.note[open] summary::before { content: '▾ '; }
.note summary:hover { color: #374151; }
/* 回归结果说明：右对齐，紧贴图表标题下方 */
.fit-note { font-size: 18px; color: #6b7280; text-align: right; margin-bottom: 2px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 22px; }
@media (max-width: 820px) { .two-col { grid-template-columns: 1fr; } .three-col { grid-template-columns: 1fr; } }
section { scroll-margin-top: 116px; }   /* 锚点跳转时让 section 顶部露在吸顶导航（site-nav 50 + 风险子导航 ~52）下方 */
/* ══════ 风险类型分组：大标题 + 吸顶子导航（风控页专用） ══════ */
/* 子导航吸顶在通用 site-nav（height:50px, top:0）正下方，点击滚到对应风险大类 */
.risk-subnav {
    position: sticky;
    top: 50px;                 /* 紧贴 site-nav 底边 */
    z-index: 9;                /* 低于 site-nav(10)，高于卡片 */
    background: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-radius: 10px;
    padding: 8px 12px;
    margin-top: 16px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}
.risk-subnav a {
    color: #10243e;
    text-decoration: none;
    font-size: 18px;
    font-weight: 500;
    padding: 5px 15px;
    border-radius: 16px;
    background: #eef2f7;
    transition: background .15s, color .15s;
}
.risk-subnav a:hover { background: #dde8f3; }
/* 风险大类分区标题：金色左边框 + 大字号，与 section 卡片区隔 */
.grp-head {
    margin-top: 30px;
    padding: 6px 0 6px 14px;
    border-left: 6px solid #c9a24a;
    font-size: 26px;
    font-weight: 700;
    color: #10243e;
    scroll-margin-top: 116px;  /* 与 section 同步：让分区标题露在吸顶导航下方 */
}
.grp-head .grp-sub { display: block; font-size: 18px; font-weight: 400; color: #6b7280; margin-top: 4px; }
/* 对比内容横向平铺、可左右滑动（参考 Apple TV 那种横滑内容带）：
 * 三张图并排放在一条横向滚动带里，鼠标按住可拖动、触控板/触屏原生横滑，
 * scroll-snap 让每张图滑到位；每张图右侧留出一小截「探头」提示还能继续滑。
/* 整条带子撑出 section 卡片、铺满可视宽（铺到格子外面），首/尾图仍用 padding 对齐正文列。
 * 宽度用 --app-vw（由 charts.js 写入 documentElement.clientWidth，不含竖向滚动条）而非 100vw，
 * 否则会比真实可视宽多出滚动条那 ~15px、整页底部冒出一条横向滚动条；--app-vw 缺失时回退 100vw。 */
.compare-slider {
    /* 左右探头等宽 → 当前那张图正好落在可视区中央。
     * 之前左侧 padding 跟正文列对齐、右侧却是「剩下多少算多少」，
     * 两边不等宽，默认停在第一张时整张图看起来偏左、不居中。 */
    --peek: 60px;
    display: flex;
    gap: 32px;
    width: var(--app-vw, 100vw);
    margin-left: calc(50% - var(--app-vw, 100vw) / 2);
    padding: 0 var(--peek) 8px;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
    cursor: grab;
}
.compare-slider.dragging {
    cursor: grabbing;
    scroll-behavior: auto;
    scroll-snap-type: none;   /* 拖动时关掉吸附，跟手更顺 */
}
.compare-track { display: contents; }   /* 让三张 slide 直接成为滚动带的 flex 项 */
.compare-slide {
    /* 100% = 滚动带内容宽 = 可视宽 - 左右探头；配合 snap center，每张图都居中停靠 */
    flex: 0 0 100%;
    min-width: 0;
    scroll-snap-align: center;
}
/* 纤细滚动条，明确「可以左右滑」的信号 */
.compare-slider::-webkit-scrollbar { height: 8px; }
.compare-slider::-webkit-scrollbar-track { background: transparent; }
.compare-slider::-webkit-scrollbar-thumb { background: #cbd6e2; border-radius: 4px; }
.compare-slider::-webkit-scrollbar-thumb:hover { background: #aebfd0; }
.compare-slider { scrollbar-width: thin; scrollbar-color: #cbd6e2 transparent; }

/* 原页 <head> 内联的轻量导航条：品牌回首页（巴比是食品公司，不复用银行分组的 bank-header.js） */
.mini-nav { background:#1f2937; height:50px; display:flex; align-items:center;
            padding:0 20px; margin:0 0 8px; }
.mini-nav a { color:#fbbf24; text-decoration:none; font-size:18px; font-weight:600; }
.mini-nav .crumb { color:#cbd5e1; font-size:18px; margin-left:14px; font-weight:400; }
</style>

