/* 顶部通用导航条注入 —— 所有 demo 页面共享
 * 每个页面 <head> 里 <script src="common/site-header.js" defer></script>
 * 依赖 common/base.css 中的 .site-nav 样式
 */
(function () {
    // 首页单独放在最前面，其余页面按行业分组
    const HOME = {href: 'index.html', title: '导航'};
    const GROUPS = [
        {
            industry: '石油',
            pages: [
                {href: 'oil_history_price.html',                title: '油价 K 线'},
                {href: 'region_production.html',                title: '地区产量'},
                {href: 'country_production_stack.html',         title: '各国产量'},
                {href: 'country_production_percent.html',       title: '产量占比'},
                {href: 'country_consumption_stack.html',        title: '各国消费'},
                {href: 'country_change_2001_vs_2024.html',      title: '2001 vs 2024'},
                {href: 'country_change_2001_vs_2024_area.html', title: '洲对比 (面积)'},
                {href: 'petro_balance_sheet.html',              title: '中石油 资产'},
                {href: 'petro_income_waterfall.html',           title: '中石油 利润'},
                {href: 'petro_reserves.html',                   title: '中石油 储量'}
            ]
        },
        {
            industry: '银行',
            pages: [
                {href: 'abc_detail.html',                       title: '农行 详情'},
                {href: 'company.html',                          title: '渝农商行 年报'}
            ]
        }
    ];

    const current = (location.pathname.split('/').pop() || 'index.html').toLowerCase();

    function makeLink(p) {
        const a = document.createElement('a');
        a.href = p.href;
        a.textContent = p.title;
        if (p.href.toLowerCase() === current) a.className = 'active';
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
            label.textContent = g.industry;
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
