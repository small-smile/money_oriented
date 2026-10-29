<template>
  <div class="page">
    <h1>银行业重要变革时间线</h1>
    <div class="lede">2013–2025 · 监管制度与会计准则变革 · 以渝农商行(601077)年报披露口径为主线，兼引同业通行监管规则</div>

    <!-- 竖向时间线：原页 renderTimeline() 逐条拼 innerHTML，这里改用 v-for 渲染，生成的 DOM 与内联样式完全一致 -->
    <div class="timeline" id="timeline">
      <div class="t-item" v-for="(e, i) in EVENTS" :key="'t-' + i">
        <div class="t-year">{{ e.time }}</div>
        <div class="t-dot" :style="{ color: e.color }"></div>
        <div class="t-card" :style="{ borderLeftColor: e.color }">
          <div class="t-name" :style="{ color: e.color }">{{ e.name }}</div>
          <div class="t-desc">{{ e.desc }}</div>
        </div>
      </div>
    </div>

    <section id="reform-section">
      <h2>变革事件对照表</h2>
      <table id="reform-table">
        <thead>
        <tr>
          <th style="width: 14%">时间</th>
          <th style="width: 20%">事件</th>
          <th>说明</th>
        </tr>
        </thead>
        <tbody>
        <!-- 原页 renderTable() 逐条拼 innerHTML，这里改用 v-for 渲染 -->
        <tr v-for="(e, i) in EVENTS" :key="'r-' + i">
          <td class="time">{{ e.time }}</td>
          <td class="event" :style="{ borderLeftColor: e.color, color: e.color }">{{ e.name }}</td>
          <td>{{ e.desc }}</td>
        </tr>
        </tbody>
      </table>
    </section>

    <div class="note">
      本页汇总的变革事件均在本行「银行」相关数据页（<a href="../../company/bank/risk.html">风控</a>、
      <a href="../../company/bank/intro.html">简介</a>、<a href="../../company/bank/index.html">业绩</a>）图表说明中已有引用，
      此处按时间顺序集中呈现；具体数据来源见各页面对应图表下方备注。仅整理已披露事实，不作监管解读或投资建议。
    </div>
  </div>
</template>

<script setup>
// 逐字搬自 dashboard/industry/bank/reform_timeline.html：纯 HTML 时间线/内容页，无 ECharts、无 /api 取数。
// 内联常量 EVENTS 原样保留；原页 renderTimeline()/renderTable() 的 innerHTML 拼装改用模板 v-for 渲染，
// 生成的 DOM 结构、文案、内联样式与原页完全一致，文案与样式一律不改。
// 色彩语义：会计准则/披露口径变更 = 蓝色 #0369a1 · 监管处罚/薪酬类新规 = 紫色 #6c3483 · 长期趋势性变革 = 灰绿 #0f766e
const EVENTS = [
  {
    time: '2013',
    name: 'CBRC 新资本监管办法实施',
    color: '#0369a1',
    desc: '原银监会自 2013 年起执行新资本监管办法（对标巴塞尔 III），资本充足率 / 核心一级资本充足率计算口径改变，与此前年份不可比，本行「风控」页资本充足率图表统一自 2014 年起可比展示，2010–2013 未纳入。'
  },
  {
    time: '2015.1.1',
    name: '企业负责人薪酬制度改革（限薪）',
    color: '#6c3483',
    desc: '监管部门对国有商业银行董事长、监事长、行长及其他负责人薪酬实施制度改革，本行董事长、行长薪酬自 2015 年起同步大幅下降（董事长税前薪酬合计由 2014 年 130.4 万元降至 2015 年 77.3 万元，约 -41%），A 股年报薪酬表脚注明确援引该项监管规定作为降薪的直接制度原因，详见「简介」页历年董事长/行长薪酬图表。'
  },
  {
    time: '2018',
    name: 'IFRS9／新金融工具准则切换',
    color: '#0369a1',
    desc: '本行 2018 年首次执行新金融工具准则（对标 IFRS9），金融资产分类由「四分类」改为 AC／FVOCI／FVTPL「三分类」，减值计量由「已发生损失法」改为「预期信用损失法（ECL）」。影响多条序列口径：利润表「资产减值损失」改列「信用减值损失」（2018 年该比率跳升至 23.70%）；净资产收益率按新准则为 13.55%（年报未披露旧准则口径）；非息收入占比因投资收益计入口径变化跳升至 23.37%；其他综合收益（OCI）构成从单一 AFS 公允价值变动扩展为债务工具 FVOCI 公允价值变动、权益工具 FVOCI 公允价值变动、FVOCI 预期信用损失准备三部分，波动幅度显著放大。详见「业绩」「风控」页多处准则切换标注线。'
  },
  {
    time: '2018',
    name: '资管新规（理财净值化）',
    color: '#0369a1',
    desc: '资管新规发布，推动保本理财压降、老产品（摊余成本／面值法）整改回表，回表资产在 IFRS9 下多计入自营 FVOCI 账簿，与同期 OCI 波动放大同源但非直接因果；增量社融结构中「未贴现票据」「信托贷款」「委托贷款」（影子银行三剑客）自此长期收缩。详见「业绩」页备注。'
  },
  {
    time: '2019',
    name: '贷款迁徙率纳入统一披露体例',
    color: '#0f766e',
    desc: '贷款迁徙率并非 2019 年才新增的监管指标（同业如农业银行 2011 年报已披露，同为 1104 报表口径），而是本行「贷款质量分析」章节体例自 2019 年起单列迁徙率表格，此前年份数据缺失系本行自身披露口径问题，非行业统一新规所致。详见「风控」页贷款迁徙率图表备注。'
  },
  {
    time: '2012–2025',
    name: '利率市场化：净息差长期收窄',
    color: '#0f766e',
    desc: '净息差 2012 年 3.50% 见顶后持续收窄，2025 年降至 1.60%，反映利率市场化推进与资产端收益率下行的长期压力，是贯穿本行近十余年经营的结构性变革，而非单一年份事件。详见「业绩」页净息差图表。'
  },
  {
    time: '2025.10',
    name: '投诉管理体制调整：客服中心统一"首触"',
    color: '#6c3483',
    desc: '本行自 2025 年 10 月起，监管渠道转办投诉统一由客服中心"首触"承接，与同期处理消费投诉数同比大幅上升、满意度同步下滑同期发生；具体成因年报未见披露说明，仅作现象记录。详见「简介」页历年投诉数据。'
  }
]
</script>

<style scoped>
/* 逐字搬自源页 <head><style>；仅省略 body { padding: 0; }——base.css 的 * 重置已置 body padding 为 0，
   属「勿重复 base.css 规则」。.chart-card / #loading / #error-msg 等未用到，不引入。
   本页所有节点均为模板静态元素（v-for 生成的也带 scoped 属性），故用 scoped。 */
.page { max-width: var(--content-w, 1200px); margin: 0 auto; padding: 32px 20px 48px; }
h1 { text-align: center; color: #2c3e50; font-size: 29px; margin-bottom: 8px; }
.lede { text-align: center; color: #6b7280; font-size: 17px; margin-bottom: 28px; }

.t-desc {
    font-size: 18px;
    color: #374151;
    line-height: 1.7;
}
.t-tag {
    display: inline-block;
    font-size: 14px;
    font-weight: 500;
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 8px;
    vertical-align: middle;
}

/* === 底部完整事件表（同 price_history.html 的标注表设计） === */
#reform-section {
    margin-top: 40px;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px 24px;
}
#reform-section h2 {
    margin: 0 0 16px;
    font-size: 20px;
    color: #111827;
    font-weight: bold;
}
#reform-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 18px;
    color: #1f2937;
}
#reform-table th {
    background: #f3f4f6;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 18px;
    color: #4b5563;
    border-bottom: 2px solid #d1d5db;
    white-space: nowrap;
}
#reform-table td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    line-height: 1.7;
}
#reform-table tr:hover td {
    background: #fafafa;
}
#reform-table td.time {
    font-family: "SF Mono", Consolas, monospace;
    white-space: nowrap;
    color: #4b5563;
    font-size: 18px;
}
#reform-table td.event {
    border-left: 4px solid transparent;
    font-weight: 600;
    padding-left: 12px;
    white-space: nowrap;
}

.note {
    font-size: 17px;
    color: #6b7280;
    line-height: 1.7;
    margin-top: 14px;
}
</style>
