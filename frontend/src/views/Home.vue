<template>
  <div class="hub">
    <h1>📊 行业数据看板</h1>
    <div class="legend">
        <span class="l-done"><i></i>已完成</span>
        <span class="l-wip"><i></i>开发中</span>
        <span class="l-empty"><i></i>待开发（仅占位）</span>
    </div>

    <h2>食品</h2>
    <div class="grid">
        <router-link class="card card-wip" to="/company/food/overview">
            <span class="tag tag-consumption">食品</span>
            <span class="title">食品</span>
            <span class="desc">巴比食品 605338 年报 · 同业对比</span>
        </router-link>
    </div>

    <h2>地产链<span class="hint">上游 → 下游</span></h2>
    <div class="flow">
        <code>水泥（上游）</code> → 发货当期确认收入 → <code>地产（下游）</code> → 竣工结转后确认收入。
        水泥的营收拐点<b>领先</b>开发商约 2 年。
        注意水泥需求里还有很大一块来自基建（公路、桥梁、水利），不随地产销售同步，读水泥时别只对着地产看。
        <b>地产（开发商）板块已不再维护</b>，卡片已从本页隐藏。
    </div>
    <div class="grid">
        <router-link class="card card-wip" to="/industry/cement/overview">
            <span class="tag tag-cement">水泥</span>
            <span class="title">水泥<span class="pos">　上游</span></span>
            <span class="desc">八家水泥企业名录 · 供给侧政策线 · 净现金分化与吨毛利代理指标</span>
        </router-link>

        <!-- 地产（开发商）板块 2026-09-01 起不再维护：卡片隐藏，页面与数据仍在
             （industry/realestate/*、developer_* 数据表、/api/developer_*），需要时直接输 URL。
        <a class="card card-wip" href="industry/realestate/overview.html">
            <span class="tag tag-realestate">地产</span>
            <span class="title">地产<span class="pos">　下游</span></span>
            <span class="desc">六家头部央企开发商名录 · 政策线 · 历年财务与三道红线横向对比</span>
        </a>
        -->

        <div class="card card-empty">
            <span class="tag tag-decor">装修</span>
            <span class="title">装修</span>
        </div>
    </div>

    <h2>金融<span class="hint">为上下游提供杠杆</span></h2>
    <div class="grid">
        <router-link class="card card-wip" to="/industry/bank/overview">
            <span class="tag tag-bank">银行</span>
            <span class="title">银行</span>
            <span class="desc">A/H 股上市银行名录 · 渝农商行 601077 年报全景</span>
        </router-link>

        <router-link class="card card-wip" to="/industry/insurance/overview">
            <span class="tag tag-insurance">保险</span>
            <span class="title">保险</span>
            <span class="desc">A/H 股上市险企名录 · 五大险企历年数据横向对比</span>
        </router-link>
    </div>

    <h2>科技<span class="hint">广告收入是上面各板块景气的同步指标</span></h2>
    <div class="grid">
        <router-link class="card card-wip" to="/company/baidu/index">
            <span class="tag tag-tech">互联网</span>
            <span class="title">百度集团<span class="pos">　09888 / BIDU</span></span>
            <span class="desc">FY2025 20-F · 业绩 / 分部与运营 / 资产与现金 / 股权结构 / 简介</span>
        </router-link>
    </div>

    <h2>能源<span class="hint">全行业的成本项</span></h2>
    <div class="flow">
        煤炭与电力占水泥吨成本的五到六成，油价则决定运输与化工成本——
        <code>能源</code>是读上面所有板块毛利率时的共同外生变量。
    </div>
    <div class="grid">
        <router-link class="card card-done" to="/subject/oil/price">
            <span class="tag tag-price">石油</span>
            <span class="title">石油</span>
            <span class="desc">量价 · 产量 · 消费 · 储量 · 油企盈利</span>
        </router-link>
    </div>

    <h2>酒店<span class="hint">消费服务，不并入地产</span></h2>
    <div class="grid">
        <div class="card card-empty">
            <span class="tag tag-hotel">酒店</span>
            <span class="title">酒店</span>
        </div>
    </div>

    <h2>通信<span class="hint">上游 → 下游</span></h2>
    <div class="flow">
        <code>三大运营商（上游）</code> 提供接入与流量 → <code>互联网（下游）</code> 把流量变现为广告与电商成交。
        运营商的资本开支与 ARPU 是读互联网板块用户增长天花板时的参照。
    </div>
    <div class="grid">
        <router-link class="card card-wip" to="/industry/telecom/overview">
            <span class="tag tag-telecom">运营商</span>
            <span class="title">三大运营商<span class="pos">　上游</span></span>
            <span class="desc">移动/电信/联通名录与变革时间线 · 三家对比 · 各家公司详情（业绩／收入构成／运营与资本开支）</span>
        </router-link>

        <router-link class="card card-wip" to="/company/cmcc/index">
            <span class="tag tag-telecom">运营商</span>
            <span class="title">中国移动<span class="pos">　941 / 600941　上游</span></span>
            <span class="desc">1997 年上市至今 · 业绩 / 产品更迭（语音→流量→算力）/ 客户与网络 / 简介与股权</span>
        </router-link>
    </div>

    <h2>互联网</h2>
    <div class="grid">
        <div class="card card-empty">
            <span class="tag tag-ad">在线广告</span>
            <span class="title">在线广告<span class="pos">　下游</span></span>
        </div>

        <div class="card card-empty">
            <span class="tag tag-ecommerce">电商</span>
            <span class="title">电商<span class="pos">　下游</span></span>
        </div>
    </div>
  </div>
</template>

<script setup></script>

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
