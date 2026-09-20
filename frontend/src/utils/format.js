/* 页面共用的小工具：数字格式化与政策时间线渲染。
 * 原先 fmt() 在四个同业对比页各一份、renderTimeline() 在三个行业概览页各一份，逐字相同。 */

/** 千分位 + 固定小数位；null/undefined 一律出「—」，不写 0 也不写 N/A。 */
export function fmt(v, decimals) {
    if (v === null || v === undefined) return '—'
    return v.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    })
}

/** 政策/变革时间线：events = [{time, name, desc, color}]，样式类名见 assets/page.css。 */
export function renderTimeline(wrap, events) {
    if (!wrap) return
    wrap.innerHTML = (events || [])
        .map(
            (e) => `
        <div class="t-item">
            <div class="t-year">${e.time}</div>
            <div class="t-dot" style="color:${e.color}"></div>
            <div class="t-card" style="border-left-color:${e.color}">
                <div class="t-name" style="color:${e.color}">${e.name}</div>
                <div class="t-desc">${e.desc}</div>
            </div>
        </div>
    `
        )
        .join('')
}
