/* 石油分组专用导航条注入 —— 供 dashboard/industry/oil/*.html 使用
 * 每个页面 <head> 里 <script src="<相对路径>/common/site-header.js" defer></script>
 * 依赖 common/base.css 中的 .site-nav 样式
 *
 * 银行相关页面（dashboard/company/*.html）改用独立的 bank-header.js，
 * 两个分组的导航逻辑/配置完全分开，改一个不影响另一个。
 *
 * 下面 href 一律写成「相对 dashboard/ 根目录」的路径，由脚本按自身 src 推算前缀，
 * 因此页面放在任意层级都不需要改这里。
 */
(function () {
    // 本脚本自身的 src（如 '../../common/site-header.js'）→ dashboard/ 根前缀 '../../'
    const self = document.currentScript
        || Array.prototype.find.call(document.scripts, s => /common\/site-header\.js/.test(s.getAttribute('src') || ''));
    const ROOT = self ? (self.getAttribute('src') || '').replace(/common\/site-header\.js.*$/, '') : '';

    const HOME = {href: 'index.html', title: '导航'};
    const GROUPS = [
        {
            label: '石油',
            pages: [
                {href: 'industry/oil/price_history.html',                title: '油价 K 线'},
                {href: 'industry/oil/region_production.html',            title: '产量总览'},
                {href: 'industry/oil/country_consumption.html',          title: '消费总览'},
                {href: 'industry/oil/country_change_2001_2024.html',     title: '2001 vs 2024'},
                {href: 'industry/oil/china_oil_majors.html',             title: '油企'},
                {href: 'industry/oil/cnooc_roa_oil.html',                title: '中海油 油价·ROA'}
            ]
        },
        {
            label: '银行',
            pages: [
                {href: 'industry/bank/overview.html',                    title: 'A/H 股概览'},
                {href: 'industry/bank/reform_timeline.html',             title: '重要变革时间线'}
            ]
        },
        {
            label: '保险',
            pages: [
                {href: 'industry/insurance/overview.html',               title: 'A/H 股概览'},
                {href: 'industry/insurance/peers.html',                  title: '五大险企对比'}
            ]
        }
    ];

    // 当前页在 dashboard/ 下的路径，用于高亮
    const path = location.pathname.replace(/\/$/, '/index.html');

    function makeLink(p) {
        const a = document.createElement('a');
        a.href = ROOT + p.href;
        a.textContent = p.title;
        if (path.toLowerCase().endsWith('/' + p.href.toLowerCase())) a.className = 'active';
        return a;
    }

    function build() {
        if (document.querySelector('.site-nav')) return;   // 幂等：避免重复注入
        const nav = document.createElement('nav');
        nav.className = 'site-nav';
        const brand = document.createElement('span');
        brand.className = 'brand';
        brand.textContent = '📊 行业看板';
        nav.appendChild(brand);
        nav.appendChild(makeLink(HOME));
        for (const g of GROUPS) {
            const label = document.createElement('span');
            label.className = 'nav-group';
            label.textContent = g.label;
            nav.appendChild(label);
            for (const p of g.pages) nav.appendChild(makeLink(p));
        }
        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
