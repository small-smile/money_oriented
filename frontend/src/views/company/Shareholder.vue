<template>
  <div class="shareholder-view" ref="rootEl">
    <div class="wrap">
      <div class="page-head">
        <h1 id="page-title" data-page="股东">股权结构</h1>
        <div class="meta" id="page-meta"></div>
      </div>

      <div id="loading">加载中…（需先启动 app.py，端口 5000）</div>
      <div id="error-msg"></div>

      <!-- 双层环形图：内圈一名股东一块、外圈按分组归并（圈序固定）。版面（行高、字号、列宽、
           圆环半径、画布高度）全部由数据量与文字实测宽度算出，这里只给一个空容器。 -->
      <section id="sec-ring" hidden>
        <div class="ring-hd">
          <h2 style="margin-bottom:0">股东构成</h2>
          <!-- 右侧一组按钮：只剩（数据层给了附加口径时的）口径切换，由 shareholder 逻辑补进来 -->
          <div class="ring-btns" id="ring-btns"></div>
        </div>
        <div class="chart-card" style="padding:8px 10px 14px">
          <div id="chart-ring" style="height:640px"></div>
        </div>
        <div class="note" id="ring-note" style="max-width:1100px;color:#6b7280;font-size:16px"></div>
      </section>

      <div id="charts"></div>
    </div>
    <!-- 点击环形图右侧标注行时在那一行下面弹出全称（列里的名字是按实测宽度截断的） -->
    <div id="row-full"></div>
    <!-- 股东明细弹层：点图上「股东明细」出全量长名清单，含所属分组与色块 -->
    <div class="modal" id="det-modal">
      <div class="modal-box">
        <div class="modal-hd">
          <button type="button" id="det-close" title="关闭">✕</button>
        </div>
        <div id="det-body"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../api'
import { createShareholder } from './shareholder-logic'

// 1:1 迁移 dashboard/company/shareholder.html 主体：模板逐字搬自源页 <body>（去掉源页 head 里
// 按 /api/nav 注入 header 脚本那段——顶部导航交给共享 App.vue<SiteHeader/>，本组件不注入导航）。
// 图表/表格/环形/派系/历年序列/解读全逻辑在 ./shareholder-logic.js 里逐字保留，仅做迁移必需的适配。
const rootEl = ref(null)
let app = null
let prevBodyBg = ''

onMounted(() => {
  // 复现 shareholder.css 的 body { background:#f5f6f8 }：body 是全局共享节点，改由生命周期设置内联样式、
  // 卸载时还原，避免非 scoped 的 body 规则泄漏到别的视图（可见效果一致）。
  prevBodyBg = document.body.style.background
  document.body.style.background = '#f5f6f8'
  app = createShareholder(rootEl.value, echarts, apiGet)
  app.start()
})

onBeforeUnmount(() => {
  document.body.style.background = prevBodyBg
  if (app) app.dispose()
  app = null
})
</script>

<style scoped>
/* 静态模板节点依赖的 page.css 结构规则（源页 <head> link 了 common/base.css + page.css + shareholder.css；
   base.css 已全局引入不重复）。仅静态节点用 scoped，防止 .wrap / section 等通用选择器泄漏到别的视图。 */
.wrap { max-width: var(--content-w, 1200px); margin: 0 auto; padding: 24px 24px 60px; }
.page-head { text-align: center; margin-bottom: 8px; }
.page-head h1 { font-size: 29px; color: #1f2937; margin-bottom: 6px; }
.page-head .meta { color: #6b7280; font-size: 18px; line-height: 1.7; }
section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); padding: 20px 22px; margin-top: 22px; }
</style>

<style>
/* 动态节点（chartCard / attachSourceTag / detailTableHTML / showFull / 环形口径按钮 由 JS
   createElement/innerHTML 生成，拿不到 scoped 的 data-v）依赖的规则必须放非 scoped 块。
   ① 源页 page.css 里本页动态节点用到的部分：.note（含 details 折叠标记）与表格规则——全站只有
      股东明细弹层这一张 table，故把 page.css 的裸 table/th/td 限定在 .modal 下，避免泄漏到别的视图；
   ② 源页 shareholder.css 逐字搬入（仅去掉 body{background} 一条，改由 <script> 生命周期设置）。
   base.css（.chart-card 白底圆角投影、.chart-title/.sub、#loading/#error-msg）已全局引入不重复。
   cascade 顺序按源页：page.css 规则在 shareholder.css 之前。 */

/* —— 源页 page.css 中本页动态节点用到的部分 —— */
.note { font-size: 18px; color: #9ca3af; margin: 10px auto 0; line-height: 1.6; max-width: 900px; }
.note summary { cursor: pointer; color: #6b7280; font-weight: 500; list-style: none; }
.note summary::-webkit-details-marker { display: none; }
.note summary::before { content: '▸ '; color: #9ca3af; }
.note[open] summary::before { content: '▾ '; }
.note summary:hover { color: #374151; }
.modal table { width: 100%; border-collapse: collapse; font-size: 18px; }
.modal th, .modal td { padding: 8px 10px; text-align: right; border-bottom: 1px solid #eee; }
.modal th:first-child, .modal td:first-child { text-align: left; }
.modal thead th { background: #eef2f7; color: #10243e; font-weight: 600; border-bottom: 2px solid #c9a24a; }
.modal tbody tr:hover { background: #f3f6fa; }

/* —— 源页 shareholder.css 逐字搬入（body{background} 见 <script>）—— */
/* 主体口径那条提示：琥珀色左边框，与页面正文的灰蓝区分开 */
.entity { margin: 10px 0 0; padding: 12px 16px; background: #fff7ed;
          border-left: 4px solid #f59e0b; border-radius: 6px;
          font-size: 17px; color: #78350f; line-height: 1.7; }

/* 成员多的板块（银行 45 家）用下拉切换，导航条里的 select 跟着深色导航配色 */
.site-nav select { font-size: 15px; padding: 3px 6px; border-radius: 6px;
                   border: 1px solid #4b5563; background: #1f2937; color: #f9fafb; max-width: 220px; }
.site-nav .sep { flex: 0 0 14px; }

td.num, th.num { white-space: nowrap; }
td.nm { text-align: left; }
td.nat { text-align: left; color: #6b7280; }
.gap-list { margin: 6px 0 0 18px; font-size: 17px; color: #555; line-height: 1.8; }
.chart-card { padding: 14px 18px 20px; margin-bottom: 20px; position: relative; }
/* 数据源标识（试点：目前只有中国移动 600941 的分红图挂它）—— 出处不再单占一节，
 * 每张图自己在卡片右上角标一行：出处 + 口径，**只是标识，不可点、不弹层**；
 * 完整出处仍在图下那段「展开详细口径」里，不在这里重复一遍。
 * 颜色按口径分：绿 = 交易所年报原文，蓝 = 第三方接口，琥珀 = 手工抽取层。
 * 第三方接口那档额外画虚线边（.todo）—— 它是临时口径，最终要换成年报原文，
 * 虚线是「这张图的底稿还欠一次年报抽取」的记号，实线才算到位。 */
.src-tag { position: absolute; right: 14px; top: 14px; z-index: 5; white-space: nowrap;
           padding: 2px 10px; border: 1px solid #d1d5db; border-radius: 12px;
           background: #fff; color: #374151; font-size: 13px; line-height: 1.5; }
.src-tag .ver { margin-left: 6px; padding-left: 6px; border-left: 1px solid currentColor;
                opacity: .75; font-variant-numeric: tabular-nums; }
.src-tag.k-annual { border-color: #bbf7d0; background: #f0fdf4; color: #166534; }
.src-tag.k-api { border-color: #bfdbfe; background: #eff6ff; color: #1e40af; }
.src-tag.k-manual { border-color: #e6dcc8; background: #fffbf2; color: #78350f; }
/* 待升级为年报口径：虚线边 —— 与实线的年报口径标签一眼能分开，颜色仍按来源类型 */
.src-tag.todo { border-style: dashed; }
.note-more > summary { cursor: pointer; color: #1d4ed8; font-size: 15px; }
.note-more > div { margin-top: 6px; padding-left: 10px; border-left: 3px solid #e5e7eb; }
/* 环形图右上角的按钮：只是开关，字号比正文小一档，免得抢掉图的注意力 */
/* 标题居中、按钮仍靠右：三栏网格（两边等宽的空列夹住标题），标题的中点因此落在
 * 整节的中线上，不会被右边那组口径按钮的宽度带偏 —— flex 的 space-between 做不到这点。 */
.ring-hd { display: grid; align-items: baseline; gap: 12px;
           grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); }
.ring-hd h2 { grid-column: 2; text-align: center; }
/* 按钮必须成组：直接当 .ring-hd 的子元素会自己占掉一列，把标题挤离中线
 * （圈序按钮飘到标题右边、口径按钮各据一方），组内自己排、放不下就折行 */
.ring-btns { grid-column: 3; display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.ring-hd button { font: inherit; font-size: 14px; line-height: 1.5; padding: 3px 10px;
                  border: 1px solid #cfc6d8; background: #fff; color: #4a2a5a;
                  border-radius: 12px; cursor: pointer; white-space: nowrap; }
/* 口径切换是单选组：当前那个填色，其余留白 —— 调淡透明度会被当成禁用态 */
.ring-hd button.cal.on { background: #4a2a5a; border-color: #4a2a5a; color: #fff; }

/* 点击标注行弹出的全称框：贴在那一行下面（下面放不下就翻到上面），太长就折行。
 * 带边框和投影，跟画布上的文字明显分层，不假装是同一行。 */
#row-full { position: absolute; display: none; z-index: 60; max-width: 560px;
            background: #fff; border: 1px solid #d8cfe0; border-radius: 10px;
            padding: 12px 16px; box-shadow: 0 6px 20px rgba(0,0,0,.2);
            font-size: 20px; line-height: 1.6; word-break: break-all; pointer-events: none; }

/* 股东明细弹层：表比一屏长时在框内滚，滚动区是内层 #det-body ——
 * 让 .modal-box 自己滚会把竖滚动条压在右侧圆角上、看着右边被切平；交给内层后
 * 滚动条落在 22px 的内边距里，四角完好。表头 sticky 钉在滚动区顶部。 */
.modal { position: fixed; left: 0; top: 0; right: 0; bottom: 0; background: rgba(0,0,0,.35);
         display: none; z-index: 99; overflow: auto; }
.modal.on { display: block; }
.modal-box { position: relative; margin: 2vh auto; width: 1320px; max-width: 96vw;
             box-sizing: border-box; max-height: 92vh; display: flex; flex-direction: column;
             overflow: hidden; background: #fff; border-radius: 10px; padding: 14px 22px 22px;
             box-shadow: 0 6px 24px rgba(0,0,0,.25); }
#det-body { overflow: auto; flex: 1; min-height: 0; }
/* 只剩一个关闭按钮，靠右；标题与口径说明那一行不要（图上方已有同样的信息） */
.modal-hd { display: flex; justify-content: flex-end; margin-bottom: 4px; }
.modal-hd button { font: inherit; font-size: 18px; line-height: 1; color: #888;
                   background: none; border: 0; cursor: pointer; padding: 4px 6px; }
.modal thead th { position: sticky; top: 0; z-index: 1; }
.modal th.tl, .modal td.tl { text-align: left; }
/* 只有数字列不许折行（金额折成两半就读不成数了）；文字列该折就折 */
.modal th.num, .modal td.num { white-space: nowrap; }
/* 分组列的值都很短（汇金系／社保基金／ETF），却会被挤成「社保基 金」，一律不折 */
.modal th.fac, .modal td.fac { text-align: left; white-space: nowrap; }
.modal td.nat { text-align: left; color: #777; }
.modal td.idx { color: #aaa; width: 34px; }
.modal .sw { display: inline-block; width: 14px; height: 14px; border-radius: 3px;
             vertical-align: -2px; margin-right: 6px; }
.modal .tag { color: #999; font-size: 14px; margin-left: 6px; }
</style>
