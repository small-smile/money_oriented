<template>
  <div class="wrap">
    <div v-if="error" class="cmcc-fail">
      <b>数据未能加载：</b>{{ error }}<br>本页通过 fetch 读取 <code>data/tables/telecom_00941_*.json</code>，需要用本地服务打开（例如在仓库根执行 <code>python3 -m http.server</code> 后访问 <code>/dashboard/company/cmcc/</code>），直接用 file:// 打开会被浏览器拦截。
    </div>

    <div class="page-head">
      <h1>中国移动有限公司 · 简介与股权</h1>
      <div class="meta">
        1997 年 9 月 3 日在中国香港注册 · 1997 年 10 月在纽交所、港交所上市 · 2021 年 5 月自纽交所退市 · 2022 年 1 月 5 日 A 股在上交所上市<br>
        数据取自公司年报与官网投资者关系页，比例与股本均注明截止日期
      </div>
      <div class="tags"><span>公司概况</span><span>股权结构</span><span>里程碑</span><span>风险</span></div>
    </div>

    <!-- ══════════ 公司概况 ══════════ -->
    <section id="sec-profile">
      <h2>公司概况</h2>
      <p class="sub" id="profile-sub"></p>
      <div class="kpis" id="profile-kpis"></div>
      <div class="cards" id="profile-cards" style="margin-top:14px"></div>
    </section>

    <!-- ══════════ 股权结构 ══════════ -->
    <section id="sec-holders">
      <h2>股权结构</h2>
      <p class="sub" id="holders-sub"></p>
      <div ref="chartHoldersEl" class="chart" style="height:420px"></div>
      <div class="note-generic" id="holders-note"></div>
    </section>

    <!-- ══════════ 里程碑 ══════════ -->
    <section id="sec-milestones">
      <h2>公司大事记（按产品世代着色）</h2>
      <p class="sub">同一条时间线上看两件事：<b>公司的资本动作</b>（上市、省公司注入、A 股回归）与<b>产品的换代</b>（2G/短信 → 3G → 4G 流量 → 5G → 算力与 AI）</p>
      <div class="ms-list" id="ms-list"></div>
    </section>

    <!-- ══════════ 口径与缺口 ══════════ -->
    <section id="sec-gaps">
      <h2>口径提示与披露缺口</h2>
      <ul class="gap-list" id="gaps-list"></ul>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import {
  years, fx, pct, thou, yiTxt,
  setText, setHTML, renderKpis, renderCards, renderList,
  shade, MUTED, ERA_COLORS, PIE_COLORS, RESIDUAL_PATTERN, loadCmcc
} from './charts.js'

// 逐字搬自 dashboard/company/cmcc/charts/intro.js：股权饼图 option 与概况/大事记渲染逻辑原样保留，
// 仅把 mount 的容器由 getElementById 改为组件模板 ref，实例收集到 charts 数组统一 resize/dispose；
// 取数由 loadCmcc() 用绝对路径 fetch 三表合成 C（字段/合并与原 boot.js 一致）。
const error = ref('')
const chartHoldersEl = ref(null)
let charts = []

function mount(el, buildOption) {
  if (!el) return null
  const ins = echarts.init(el)
  ins.setOption(buildOption(ins), true)
  charts.push({ ins, build: buildOption })
  return ins
}
function onResize() {
  charts.forEach(c => { c.ins.resize(); c.ins.setOption(c.build(c.ins), true) })
}

onMounted(async () => {
  try {
    const C = await loadCmcc()
    render(C)
    window.addEventListener('resize', onResize)
  } catch (e) {
    error.value = e && e.message ? e.message : String(e)
  }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach(c => { try { c.ins.dispose() } catch (_) {} })
  charts = []
})

function render(C) {
  /* ==== 以下逐字搬自 charts/intro.js ==== */
  var PROF = C.profile || {};
  var SH = PROF.shareholding || {};
  var PMETA = PROF._meta || {};
  var OP = (C.operating && C.operating.annual) || {};
  var AN = (C.annual && C.annual.annual) || {};

  /* 世代配色：与 product.js 的时间线保持一致 */
  var ERA_STYLE = {
    '语音': ERA_COLORS.voice,
    '短信': ERA_COLORS.sms,
    '数据': shade(ERA_COLORS.data, 0.25),
    '流量': ERA_COLORS.data,
    '宽带': ERA_COLORS.broadband,
    '5G':   '#c0392b',
    '算力': ERA_COLORS.appInfo,
    'AI':   '#8e44ad',
    '资本': MUTED
  };
  function eraColor(era) {
    var k = Object.keys(ERA_STYLE).find(function (key) { return (era || '').indexOf(key) >= 0; });
    return k ? ERA_STYLE[k] : '#94a3b8';
  }

  /* ==== 公司概况 ==== */
  (function () {
    var p = PROF.profile || {};
    setText('profile-sub', (p.summary || '') + (p.asOf ? '　（数据截至 ' + p.asOf + '）' : ''));

    var lastFin = (function () {
        var ys = years(AN, 'totalRevenue');
        return ys.length ? { y: ys[ys.length - 1], r: AN[ys[ys.length - 1]] } : null;
    })();
    var lastOp = (function () {
        var ys = years(OP, 'mobileSubs');
        return ys.length ? { y: ys[ys.length - 1], r: OP[ys[ys.length - 1]] } : null;
    })();

    var kpis = [
        { label: '注册地与成立日期', value: p.incorporation || '—', delta: p.incorporationDate || '' },
        { label: '上市地与代码', value: p.tickers || '—', delta: p.listingNote || '' },
        { label: '实际控制人', value: p.controller || '—',
          delta: SH.groupStake != null ? '持股 ' + pct(SH.groupStake, 2) + (SH.asOf ? '（' + SH.asOf + '）' : '') : '' }
    ];
    if (lastFin) kpis.push({ label: lastFin.y + ' 营运收入', value: yiTxt(lastFin.r.totalRevenue) });
    if (lastOp) kpis.push({ label: lastOp.y + ' 移动客户数',
                            value: lastOp.r.mobileSubs == null ? '—' : fx(lastOp.r.mobileSubs, 2) + ' 亿户' });
    if (p.employees != null) kpis.push({ label: '员工总数', value: thou(p.employees) + ' 人',
                                         delta: p.employeesAsOf || '' });
    renderKpis('profile-kpis', kpis);

    var cards = [];
    if (p.business) cards.push({ title: '主营业务', body: p.business });
    if (p.threeServices) cards.push({ title: '2025 年起的三项主营口径', body: p.threeServices });
    if (p.strategy) cards.push({ title: '战略与规划', body: p.strategy });
    if ((PROF.risks || []).length) {
        cards.push({ title: '年报披露的主要风险', body: '<ul>' + PROF.risks.map(function (r) {
            return '<li>' + r + '</li>'; }).join('') + '</ul>' });
    }
    renderCards('profile-cards', cards);
  })();
  /* ==== 股权结构 ==== */
  mount(chartHoldersEl.value, function () {
    var parts = SH.breakdown || [];
    if (!parts.length) return { title: { text: '数据源中暂无股权结构明细', left: 'center', top: 'middle',
                                         textStyle: { fontSize: 18, color: MUTED } } };
    return {
        tooltip: { trigger: 'item', textStyle: { fontSize: 17 },
                   formatter: function (p) { return p.name + '<br>' + pct(p.value, 2); } },
        legend: { bottom: 6, textStyle: { fontSize: 17, color: '#444' }, type: 'scroll' },
        series: [{
            type: 'pie', radius: ['38%', '66%'], center: ['50%', '46%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, formatter: '{b}\n{d}%' },
            data: parts.map(function (p, i) {
                return { name: p.name, value: p.stake,
                         itemStyle: { color: p.residual ? RESIDUAL_PATTERN : PIE_COLORS[i % PIE_COLORS.length] } };
            })
        }]
    };
  });
  setText('holders-sub',
    '口径：占已发行总股数比例' + (SH.asOf ? '，截至 ' + SH.asOf : '')
    + (SH.totalShares ? ' · 总股本 ' + thou(SH.totalShares) + ' 股' : ''));
  setHTML('holders-note',
    (SH.note || '')
    + (SH.groupStake != null
        ? '<b>中国移动通信集团有限公司直接与间接合计持股 ' + pct(SH.groupStake, 2) + '</b>，'
          + '余下由公众股东持有。'
        : '')
    + ' A 股与 H 股同股同权，但两地估值长期存在折溢价；'
    + '读股权结构时要注意「集团持股」包含通过全资子公司间接持有的部分，'
    + '年报会在股权结构图的脚注里逐层说明。');

  /* ==== 大事记 ==== */
  (function () {
    var ms = (PROF.milestones || []).slice().sort(function (a, b) {
        return a.year - b.year || (a.month || 0) - (b.month || 0);
    });
    if (!ms.length) { setHTML('ms-list', '<p class="note">数据源中暂无里程碑记录。</p>'); return; }
    setHTML('ms-list', ms.map(function (m) {
        return '<div class="ms-row">'
            + '<div class="ms-yr">' + m.year + (m.month ? '.' + (m.month < 10 ? '0' : '') + m.month : '') + '</div>'
            + '<div class="ms-era" style="background:' + eraColor(m.era) + '">' + (m.era || '—') + '</div>'
            + '<div class="ms-txt"><b>' + m.title + '</b>' + (m.detail ? '　' + m.detail : '') + '</div>'
            + '</div>';
    }).join(''));
  })();

  /* ==== 口径与缺口 ==== */
  (function () {
    var items = [];
    if (PMETA.gaps) {
        Object.keys(PMETA.gaps).forEach(function (k) { items.push('<b>' + k + '</b>：' + PMETA.gaps[k]); });
    }
    if (PMETA.sources) items.push('<b>来源</b>：' + PMETA.sources);
    items.push('<b>股权比例的时点</b>：股权结构随增发、回购、股东增减持变化，'
        + '本页比例只对应上面标注的截止日期，跨期引用需回查当期年报或月报表。');
    items.push('<b>里程碑的世代标签</b>：世代（语音／短信／流量／5G／算力／AI）是本项目为便于阅读所加的归类，'
        + '不是公司年报的正式分类；同一件事可能同时属于两代（如 4G 发牌既是网络也是流量产品的起点）。');
    renderList('gaps-list', items);
  })();
}
</script>

<!-- 静态骨架逐字取自 company/page.css 与源页 <head> 内联样式（.note-generic/.gap-list/.ms-list）；
     base.css 已全局引入，此处不重复其 reset/body/.chart-title 等规则。 -->
<style scoped>
section > h2 {
    font-size: 22px; color: #1f2937; margin-bottom: 4px;
    border-left: 4px solid #10243e; padding-left: 10px;
}
section > h2 { font-size: 22px; color: #1f2937; margin-bottom: 4px; border-left: 4px solid #10243e; padding-left: 10px; }

section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
          padding: 20px 22px; margin-top: 22px; scroll-margin-top: 116px; }

.chart { width: 100%; height: 428px; }   /* 各图容器内联 height 覆盖此默认值 */

.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }
/* 里程碑列表容器（静态） */
.ms-list { margin-top: 10px; }
</style>

<!-- 动态节点（renderKpis/renderCards/renderList 与 ms-list 的 innerHTML 注入，无 data-v）：非 scoped，
     用 .wrap 前缀收敛作用域；取值逐字取自 company/page.css（.kpi/.card2）与源页内联 .ms-*/.gap-list b。 -->
<style>

.wrap .ms-row { display: flex; gap: 16px; padding: 9px 0; border-bottom: 1px dashed #e5e7eb; }
.wrap .ms-row:last-child { border-bottom: none; }
.wrap .ms-yr { flex: 0 0 96px; font-size: 18px; font-weight: 700; color: #10243e; }
.wrap .ms-era { flex: 0 0 96px; font-size: 16px; color: #fff; border-radius: 4px;
                text-align: center; height: 26px; line-height: 26px; }
.wrap .ms-txt { font-size: 18px; color: #444; line-height: 1.7; }
.wrap .ms-txt b { color: #10243e; }
</style>

