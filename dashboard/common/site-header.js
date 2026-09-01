/* 页面导航条注入 —— 供 dashboard/subject/<专题>/*.html 与 dashboard/industry/<行业>/*.html 使用
 * 每个页面 <head> 里 <script src="<相对路径>/common/site-header.js" defer></script>
 * 依赖 common/base.css 中的 .site-nav 样式
 *
 * 导航条只列出**当前页所属行业**的页面：按页面所在目录（subject/oil、industry/bank …）
 * 匹配下面的分组，其它行业的链接不出现，避免一条导航塞满全站页面。
 * 回总览的入口挂在左上角 brand 上（与 bank-header.js 一致）。
 * dashboard/index.html 本身不挂导航条。
 *
 * 银行公司页（dashboard/company/bank/*.html）改用独立的 bank-header.js，
 * 两套导航逻辑/配置完全分开，改一个不影响另一个。
 *
 * 下面 href 一律写成「相对 dashboard/ 根目录」的路径，由脚本按自身 src 推算前缀，
 * 因此页面放在任意层级都不需要改这里。
 */
(function () {
    // 本脚本自身的 src（如 '../../common/site-header.js'）→ dashboard/ 根前缀 '../../'
    const self = document.currentScript
        || Array.prototype.find.call(document.scripts, s => /common\/site-header\.js/.test(s.getAttribute('src') || ''));
    const ROOT = self ? (self.getAttribute('src') || '').replace(/common\/site-header\.js.*$/, '') : '';

    const GROUPS = [
        {
            dir: 'subject/oil/',
            pages: [
                {href: 'subject/oil/price_history.html',                title: '油价 K 线'},
                {href: 'subject/oil/region_production.html',            title: '产量总览'},
                {href: 'subject/oil/country_consumption.html',          title: '消费总览'},
                {href: 'subject/oil/country_change_2001_2024.html',     title: '2001 vs 2024'},
                {href: 'subject/oil/china_oil_majors.html',             title: '油企'},
                {href: 'subject/oil/cnooc_roa_oil.html',                title: '中海油 油价·ROA'}
            ]
        },
        {
            dir: 'industry/bank/',
            pages: [
                {href: 'industry/bank/overview.html',                    title: 'A/H 股概览'},
                {href: 'industry/bank/tsf.html',                         title: '社会融资规模'},
                {href: 'industry/bank/npl-formation.html',               title: '息差与不良生成对比'},
                {href: 'industry/bank/reform_timeline.html',             title: '重要变革时间线'},
                {href: 'company/bank/shareholder.html?industry=bank',         title: '股权结构'}
            ]
        },
        {
            dir: 'industry/insurance/',
            pages: [
                {href: 'industry/insurance/overview.html',               title: 'A/H 股概览'},
                {href: 'industry/insurance/peers.html',                  title: '五大险企对比'},
                {href: 'company/bank/shareholder.html?industry=insurer',      title: '股权结构'}
            ]
        },
        {
            dir: 'industry/realestate/',
            pages: [
                {href: 'industry/realestate/overview.html',              title: '央企名录与政策线'},
                {href: 'industry/realestate/peers.html',                 title: '六家央企开发商对比'},
                {href: 'company/bank/shareholder.html?industry=developer',    title: '股权结构'}
            ]
        },
        {
            dir: 'industry/cement/',
            pages: [
                {href: 'industry/cement/overview.html',                  title: '名录与供给侧政策线'},
                {href: 'industry/cement/peers.html',                     title: '八家水泥企业对比'},
                {href: 'company/bank/shareholder.html?industry=cement',       title: '股权结构'}
            ]
        },
        {
            dir: 'industry/telecom/',
            pages: [
                {href: 'industry/telecom/overview.html',                 title: '名录与变革时间线'},
                {href: 'industry/telecom/peers.html',                    title: '三大运营商对比'},
                {href: 'company/telecom/index.html',                     title: '公司详情'},
                {href: 'company/bank/shareholder.html?industry=telecom',      title: '股权结构'}
            ]
        },
        {
            // 百度（09888 / BIDU）公司详情页：只有一家公司、数据全在 company/baidu/data.js，
            // 不像银行页要按 ?code= 切换上百家，所以复用本文件而不再单开一个 header 脚本
            dir: 'company/baidu/',
            pages: [
                {href: 'company/baidu/index.html',                       title: '业绩'},
                {href: 'company/baidu/segment.html',                     title: '分部与运营'},
                {href: 'company/baidu/balance-sheet.html',               title: '资产与现金'},
                {href: 'company/bank/shareholder.html?industry=tech',                 title: '股权结构'},
                {href: 'company/baidu/intro.html',                       title: '简介'}
            ]
        },
        {
            // 中国移动（941 / 600941）公司详情页：charts/boot.js 在页面加载时拉 data/tables/telecom_00941_*.json
            dir: 'company/cmcc/',
            pages: [
                {href: 'company/cmcc/index.html',                        title: '业绩'},
                {href: 'company/cmcc/product.html',                      title: '产品更迭'},
                {href: 'company/cmcc/operation.html',                    title: '客户与网络'},
                {href: 'company/cmcc/intro.html',                        title: '简介与股权'}
            ]
        }
    ];

    // 当前页在 dashboard/ 下的路径，用于判定所属行业 + 高亮
    const path = location.pathname.replace(/\/$/, '/index.html');
    /* 当前页所属行业分组；不在任何行业目录下（如 dashboard/index.html）时不注入导航。
     * 例外：股权结构页只有一份（company/bank/shareholder.html，按 ?industry= 服务七个板块），
     * 它的目录判不出板块，所以允许页面自己用 window.__HEADER_GROUP 指定用哪一组。 */
    const GROUP = GROUPS.find(g => (window.__HEADER_GROUP
        ? g.dir === window.__HEADER_GROUP
        : path.toLowerCase().includes('/' + g.dir.toLowerCase())));

    function makeLink(p) {
        const a = document.createElement('a');
        a.href = ROOT + p.href;
        a.textContent = p.title;
        if (path.toLowerCase().endsWith('/' + p.href.toLowerCase())) a.className = 'active';
        return a;
    }

    function build() {
        if (!GROUP) return;                                // 非行业页（首页等）不加导航条
        // 幂等只针对本脚本自己注入的那条：股权结构页另有一条自己画的板块/公司切换行，
        // 那条也用 .site-nav 样式，不能因为它存在就不注入 header
        if (document.querySelector('nav.site-nav[data-site-header]')) return;
        const nav = document.createElement('nav');
        nav.className = 'site-nav';
        nav.dataset.siteHeader = '1';
        const brand = document.createElement('a');
        brand.className = 'brand';
        brand.href = ROOT + 'index.html';
        brand.textContent = '📊 行业看板';
        nav.appendChild(brand);
        for (const p of GROUP.pages) nav.appendChild(makeLink(p));
        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
