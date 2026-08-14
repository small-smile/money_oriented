/* 银行分组专用导航条注入 —— 仅供 dashboard/company/*.html 使用
 * 每个页面 <head> 里 <script src="<相对路径>/common/bank-header.js" defer></script>
 * 依赖 common/base.css 中的 .site-nav 样式
 *
 * 与 site-header.js（石油分组）完全分开：银行相关页面改动分组/链接时只改这里，
 * 不影响石油页面；反之亦然。
 */
(function () {
    // 本脚本自身的 src（如 '../common/bank-header.js'）→ dashboard/ 根前缀 '../'
    const self = document.currentScript
        || Array.prototype.find.call(document.scripts, s => /common\/bank-header\.js/.test(s.getAttribute('src') || ''));
    const ROOT = self ? (self.getAttribute('src') || '').replace(/common\/bank-header\.js.*$/, '') : '';

    // 导航条只放本银行的页面：业绩 / 资产端 / 负债端 / 风控 / 股东。
    // 回总览的入口挂在左上角 brand 上，不再单独占一个「导航」链接，也不再显示「银行」分组标签。
    const PAGES = [
        {href: 'company/index.html', title: '业绩'},
        {href: 'company/asset.html', title: '资产端'},
        {href: 'company/debt.html', title: '负债端'},
        {href: 'company/risk.html', title: '风控'},
        {href: 'company/shareholder.html', title: '股东'},
        {href: 'company/intro.html', title: '简介'}
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
        const brand = document.createElement('a');
        brand.className = 'brand';
        brand.href = ROOT + 'index.html';
        brand.textContent = '📊 行业看板';
        nav.appendChild(brand);
        // 主链接（业绩/资产端/负债端/风控/股东）居中放在 .nav-center 里，
        // 与左侧 brand 分开，方便靠 margin: auto 居中
        const center = document.createElement('div');
        center.className = 'nav-center';
        for (const p of PAGES) center.appendChild(makeLink(p));
        nav.appendChild(center);
        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
