<template>
  <div class="hub">
    <h1>📊 行业数据看板</h1>
    <div class="legend">
        <span class="l-done"><i></i>已完成</span>
        <span class="l-wip"><i></i>开发中</span>
        <span class="l-empty"><i></i>待开发（仅占位）</span>
    </div>

    <template v-for="sec in hubSections" :key="sec.title">
      <h2>{{ sec.title }}<span v-if="sec.hint" class="hint">{{ sec.hint }}</span></h2>
      <div v-if="sec.flow" class="flow" v-html="sec.flow"></div>
      <div class="grid">
        <template v-for="c in sec.cards" :key="c.name">
          <router-link v-if="c.to" class="card" :class="'card-' + c.status" :to="c.to">
            <span class="tag" :class="c.tagClass">{{ c.tag }}</span>
            <span class="title">{{ c.name }}<span v-if="c.pos" class="pos">{{ c.pos }}</span></span>
            <span v-if="c.desc" class="desc">{{ c.desc }}</span>
          </router-link>
          <div v-else class="card" :class="'card-' + c.status">
            <span class="tag" :class="c.tagClass">{{ c.tag }}</span>
            <span class="title">{{ c.name }}<span v-if="c.pos" class="pos">{{ c.pos }}</span></span>
            <span v-if="c.desc" class="desc">{{ c.desc }}</span>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
// 首页卡片数据抽到 src/site.config.js（与 router / SiteHeader 同源）；本页只负责按数据渲染 + 保留原样式。
import { hubSections } from '../site.config'
</script>

<style scoped>
/* 逐字搬自 dashboard/index.html <head> 的 <style>：
   - `*{}` reset 未搬（base.css 已有）；
   - 原 body 规则：padding 移到根包裹 .hub，背景 #f5f7fa 交给全局 base.css，
     字体族保留自原页 body 以保证渲染一致；其余规则一字不改。 */
.hub {
    font-family: -apple-system, "Microsoft YaHei", sans-serif;
    padding: 40px 20px;
}
h1 {
    text-align: center;
    margin-bottom: 36px;
    color: #2c3e50;
    font-size: 32px;
}
h2 {
    max-width: var(--content-w, 1200px);
    margin: 44px auto 6px;
    color: #2c3e50;
    font-size: 25px;
    border-left: 5px solid #1f2937;
    padding-left: 12px;
}
/* h2 右侧的产业链方向提示 */
h2 .hint {
    font-size: 17px;
    font-weight: 400;
    color: #9ca3af;
    margin-left: 12px;
}
/* 板块下方的传导链条说明：只在有上下游关系的板块出现 */
.flow {
    max-width: var(--content-w, 1200px);
    margin: 0 auto 16px;
    padding-left: 17px;
    font-size: 17px;
    color: #6b7280;
    line-height: 1.7;
}
.flow code {
    background: #eef2f7;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 16px;
    color: #334155;
}
/* 卡片在链条中的位置标记（上游 / 下游） */
.card .pos {
    font-size: 16px;
    color: #94a3b8;
    font-weight: 600;
    letter-spacing: 1px;
}
h3 {
    max-width: var(--content-w, 1200px);
    margin: 24px auto 14px;
    color: #4b5563;
    font-size: 20px;
    font-weight: 600;
    padding-left: 17px;
}
/* h3 里的板块补充说明（产业链方向等），与 h2 .hint 同一套灰度 */
h3 .sub {
    font-size: 16px;
    font-weight: 400;
    color: #9ca3af;
    margin-left: 10px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    max-width: var(--content-w, 1200px);
    margin: 0 auto;
}
.card {
    background: #fff;
    border-radius: 10px;
    border: 2px solid #e5e7eb;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}
/* 建设状态用边框颜色标识，配色见页首图例 */
.card.card-done { border-color: #1e8449; }
.card.card-wip  { border-color: #d97706; }
.card .title {
    font-size: 19px;
    font-weight: 600;
    color: #2c3e50;
}
.card .desc {
    font-size: 18px;
    color: #7f8c8d;
}
.card .tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 500;
    width: fit-content;
}
.tag-price { background: #fdebd0; color: #d35400; }
.tag-production { background: #d5f5e3; color: #1e8449; }
.tag-consumption { background: #fce4ec; color: #ad1457; }
.tag-reserve { background: #fdf2d0; color: #9a6700; }
.tag-company { background: #d6eaf8; color: #1a5276; }
.tag-bank { background: #e8daef; color: #6c3483; }
.tag-insurance { background: #d1f2eb; color: #0e6655; }
.tag-realestate { background: #fde2e4; color: #9d174d; }
.tag-cement { background: #e2e8f0; color: #334155; }
.tag-decor { background: #ffe8d6; color: #9a3412; }
.tag-ad { background: #ddd6fe; color: #5b21b6; }
.tag-tech { background: #dbeafe; color: #1e40af; }
.tag-ecommerce { background: #ccfbf1; color: #115e59; }
.tag-hotel { background: #fef3c7; color: #92400e; }
.tag-telecom { background: #dbeafe; color: #1e40af; }
/* 只占位的板块：尚无任何页面，整卡不可点击 */
.card.card-empty {
    border: 2px dashed #cbd5e1;
    box-shadow: none;
    background: #fafbfc;
    pointer-events: none;
}
/* 边框配色图例 */
.legend {
    max-width: var(--content-w, 1200px);
    margin: 0 auto 8px;
    display: flex;
    gap: 20px;
    padding-left: 17px;
    font-size: 17px;
    color: #6b7280;
    flex-wrap: wrap;
}
.legend i {
    display: inline-block;
    width: 26px;
    height: 0;
    border-top: 3px solid #e5e7eb;
    vertical-align: middle;
    margin-right: 7px;
}
.legend .l-done i { border-top-color: #1e8449; }
.legend .l-wip i  { border-top-color: #d97706; }
.legend .l-empty i { border-top-style: dashed; border-top-color: #cbd5e1; }
</style>
