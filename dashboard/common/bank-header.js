/* 银行分组专用导航条注入 —— 仅供 dashboard/company/bank/*.html 使用
 * 每个页面 <head> 里 <script src="<相对路径>/common/bank-header.js" defer></script>
 * 依赖 common/base.css 中的 .site-nav 样式
 *
 * 与 site-header.js（石油分组）完全分开：银行相关页面改动分组/链接时只改这里，
 * 不影响石油页面；反之亦然。company/food/ 等其它行业的公司页各自带轻量导航，不用本文件。
 */
(function () {
    // 本脚本自身的 src（如 '../common/bank-header.js'）→ dashboard/ 根前缀 '../'
    const self = document.currentScript
        || Array.prototype.find.call(document.scripts, s => /common\/bank-header\.js/.test(s.getAttribute('src') || ''));
    const ROOT = self ? (self.getAttribute('src') || '').replace(/common\/bank-header\.js.*$/, '') : '';

    // 导航条只放本银行的页面：业绩 / 资产端 / 负债端 / 风控 / 股东。
    // 回总览的入口挂在左上角 brand 上，不再单独占一个「导航」链接，也不再显示「银行」分组标签。
    const PAGES = [
        {href: 'company/bank/shareholder.html', title: '股东'},
        {href: 'company/bank/index.html', title: '业绩'},
        {href: 'company/bank/asset.html', title: '资产端'},
        {href: 'company/bank/debt.html', title: '负债端'},
        {href: 'company/bank/risk.html', title: '风控'},
        {href: 'company/bank/intro.html', title: '简介'},
        {href: 'company/bank/balance-sheet.html', title: '资产负债表'}
    ];

    // 当前页在 dashboard/ 下的路径，用于高亮
    const path = location.pathname.replace(/\/$/, '/index.html');

    // 银行代码随导航透传：company/bank/*.html 都是同一份 HTML 按 code 渲染不同银行，
    // 链接不带上就会在切页时掉回默认的渝农商行。后端动态渲染时代码已注入
    // window.COMPANY_CODE（charts.js 也读它），静态打开时退回解析地址栏 ?code=。
    const raw = window.COMPANY_CODE
        || new URLSearchParams(location.search).get('code') || '';
    const CODE = /^[0-9]{5,6}$/.test(raw) ? raw : '';

    // 可切换的银行 = data/tables/company_charts_<code>.json 存在的那些，由后端
    // list_banks() 扫目录得出、注入 window.__BANKS（加行只需放数据文件，不用改前端）。
    // 下面这份是 file:// 静态打开时的兜底名单，可能与实际数据文件不同步。
    // tier 用于分组面板分列（参考 dashboard/industry/oil/region_production.html 右侧
    // 按洲分列的 HTML 悬浮图例），与 fetch_bank_financials.py 里的 BANKS 机构类型口径一致。
    const BANKS = Array.isArray(window.__BANKS) && window.__BANKS.length ? window.__BANKS : [
        {code: '601077', name: '渝农商行', tier: '农商行', aListDate: '2019-10-29', hListDate: '2010-12-16'},
        // 国有大行（均 A+H）
        {code: '601398', name: '工商银行', tier: '国有大行', aListDate: '2006-10-27', hListDate: '2006-10-27'},
        {code: '601288', name: '农业银行', tier: '国有大行', aListDate: '2010-07-15', hListDate: '2010-07-16'},
        {code: '601988', name: '中国银行', tier: '国有大行', aListDate: '2006-07-05', hListDate: '2006-06-01'},
        {code: '601939', name: '建设银行', tier: '国有大行', aListDate: '2007-09-25', hListDate: '2005-10-27'},
        {code: '601328', name: '交通银行', tier: '国有大行', aListDate: '2007-05-15', hListDate: '2005-06-23'},
        {code: '601658', name: '邮储银行', tier: '国有大行', aListDate: '2019-12-10', hListDate: '2016-09-28'},
        // 股份行
        {code: '600036', name: '招商银行', tier: '股份行', aListDate: '2002-04-09', hListDate: '2006-09-22'},
        {code: '601166', name: '兴业银行', tier: '股份行', aListDate: '2007-02-05'},
        {code: '600000', name: '浦发银行', tier: '股份行', aListDate: '1999-11-10'},
        {code: '601998', name: '中信银行', tier: '股份行', aListDate: '2007-04-27', hListDate: '2007-04-27'},
        {code: '600016', name: '民生银行', tier: '股份行', aListDate: '2000-12-19', hListDate: '2009-11-26'},
        {code: '000001', name: '平安银行', tier: '股份行', aListDate: '1991-04-03'},
        {code: '600015', name: '华夏银行', tier: '股份行', aListDate: '2003-09-12'},
        {code: '601818', name: '光大银行', tier: '股份行', aListDate: '2010-08-18', hListDate: '2013-12-20'},
        {code: '601916', name: '浙商银行', tier: '股份行', aListDate: '2019-11-26', hListDate: '2016-03-30'},
        // 城商行
        {code: '601169', name: '北京银行', tier: '城商行', aListDate: '2007-09-19'},
        {code: '601229', name: '上海银行', tier: '城商行', aListDate: '2016-11-16'},
        {code: '600919', name: '江苏银行', tier: '城商行', aListDate: '2016-08-02'},
        {code: '002142', name: '宁波银行', tier: '城商行', aListDate: '2007-07-19'},
        {code: '601009', name: '南京银行', tier: '城商行', aListDate: '2007-07-19'},
        {code: '601838', name: '成都银行', tier: '城商行', aListDate: '2018-01-31'},
        {code: '600926', name: '杭州银行', tier: '城商行', aListDate: '2016-10-27'},
        {code: '601187', name: '厦门银行', tier: '城商行', aListDate: '2020-10-27'},
        {code: '002936', name: '郑州银行', tier: '城商行', aListDate: '2018-09-19', hListDate: '2015-12-23'},
        {code: '002948', name: '青岛银行', tier: '城商行', aListDate: '2019-01-16', hListDate: '2015-12-03'},
        {code: '601577', name: '长沙银行', tier: '城商行', aListDate: '2018-09-26'},
        {code: '002966', name: '苏州银行', tier: '城商行', aListDate: '2019-08-02'},
        {code: '601963', name: '重庆银行', tier: '城商行', aListDate: '2021-02-05', hListDate: '2013-11-06'},
        {code: '601665', name: '齐鲁银行', tier: '城商行', aListDate: '2021-06-18'},
        {code: '601997', name: '贵阳银行', tier: '城商行', aListDate: '2016-08-16'},
        {code: '600928', name: '西安银行', tier: '城商行', aListDate: '2019-03-01'},
        {code: '001227', name: '兰州银行', tier: '城商行', aListDate: '2022-01-17'},
        // 农商行
        {code: '601825', name: '沪农商行', tier: '农商行', aListDate: '2021-08-19'},
        {code: '601128', name: '常熟银行', tier: '农商行', aListDate: '2016-09-30'},
        {code: '002958', name: '青农商行', tier: '农商行', aListDate: '2019-03-26'},
        {code: '600908', name: '无锡银行', tier: '农商行', aListDate: '2016-09-23'},
        {code: '002807', name: '江阴银行', tier: '农商行', aListDate: '2016-09-02'},
        {code: '601860', name: '紫金银行', tier: '农商行', aListDate: '2019-01-03'},
        {code: '002839', name: '张家港行', tier: '农商行', aListDate: '2017-01-24'},
        {code: '601528', name: '瑞丰银行', tier: '农商行', aListDate: '2021-06-25'},
        {code: '603323', name: '苏农银行', tier: '农商行', aListDate: '2016-11-29'},
        // 纯 H 股（仅 hListDate）
        {code: '01578', name: '天津银行', tier: '城商行', hListDate: '2016-03-30'},
        {code: '01916', name: '江西银行', tier: '城商行', hListDate: '2018-06-26'}
    ];
    const DEFAULT_CODE = '601077';   // 与 charts.js、后端 DEFAULT_BANK_CODE 一致
    // 分组显示顺序：银行数量最多的国有大行放最前，城商行/农商行数据较薄放最后
    const TIER_ORDER = ['国有大行', '股份行', '城商行', '农商行'];

    // 回填给其它脚本用（charts.js 里 ROE 图的快速切换按钮读它）：
    // 后端渲染时本来就有，静态打开时把上面的兜底名单落到同一个全局变量上，取用方无需各自再抄一份。
    window.__BANKS = BANKS;

    function makeLink(p) {
        const a = document.createElement('a');
        a.href = ROOT + p.href + (CODE ? '?code=' + CODE : '');
        a.textContent = p.title;
        if (path.toLowerCase().endsWith('/' + p.href.toLowerCase())) a.className = 'active';
        return a;
    }

    // 银行切换：换 ?code= 后整页重新加载。7 个页面同一套逻辑，
    // 不做原地重绘——各页图表数量/结构差异大，重载最不容易留下上一行的残留。
    // 交互参考各国石油产量堆叠图右侧的悬浮图例（buildStackLegend）：按分组分列展示，
    // 点击导航条上的黄色按钮展开/收起，面板里每个机构类型一列，列内过长会自动折成子列。
    function makeBankSwitch() {
        const curCode = BANKS.some(b => b.code === CODE) ? CODE : DEFAULT_CODE;
        const box = document.createElement('div');
        box.className = 'nav-banks';

        // 「银行」字样常驻：面板收起时用户只看到一个黄色银行名按钮，容易看不出这里可以换行，
        // 加个标签把它和左边的页面链接区分清楚。
        const label = document.createElement('label');
        label.textContent = '银行';

        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'nav-bank-trigger';
        trigger.title = '点击按机构类型选择银行';
        const curBank = BANKS.find(b => b.code === curCode);
        trigger.innerHTML = '<span class="cur-name"></span><span class="caret">▾</span>';
        trigger.querySelector('.cur-name').textContent = curBank ? curBank.name : curCode;

        const panel = document.createElement('div');
        panel.className = 'nav-bank-panel';
        panel.hidden = true;

        // 按 tier 分组分列；未知 tier 的银行归到末尾的「其他」列，不丢数据
        const groups = new Map();
        for (const b of BANKS) {
            const tier = b.tier || '其他';
            if (!groups.has(tier)) groups.set(tier, []);
            groups.get(tier).push(b);
        }
        const tiers = [...groups.keys()].sort((a, c) => {
            const ia = TIER_ORDER.indexOf(a), ic = TIER_ORDER.indexOf(c);
            return (ia < 0 ? TIER_ORDER.length : ia) - (ic < 0 ? TIER_ORDER.length : ic);
        });
        for (const tier of tiers) {
            const col = document.createElement('div');
            col.className = 'nav-bank-col';
            const head = document.createElement('div');
            head.className = 'bg-head';
            head.textContent = tier + '（' + groups.get(tier).length + '）';
            col.appendChild(head);
            const items = document.createElement('div');
            items.className = 'bg-items';
            for (const b of groups.get(tier)) {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'bg-item' + (b.code === curCode ? ' active' : '');
                // 行名一行，上市日期一行（小号灰字）：A+H 两地上市分列 A/H 两个日期，
                // 只 A 股或只 H 股的各显示一个。layoutBankColumns 按实测行高折列，行数不同不影响。
                const nm = document.createElement('span');
                nm.className = 'bg-name';
                nm.textContent = b.name;
                item.appendChild(nm);
                // A / H 各占一行，避免两地日期挤在一行超出 116px 列宽
                if (b.aListDate) {
                    const a = document.createElement('span');
                    a.className = 'bg-date';
                    a.textContent = 'A ' + b.aListDate;
                    item.appendChild(a);
                }
                if (b.hListDate) {
                    const h = document.createElement('span');
                    h.className = 'bg-date';
                    h.textContent = 'H ' + b.hListDate;
                    item.appendChild(h);
                }
                item.addEventListener('click', () => {
                    const q = new URLSearchParams(location.search);
                    q.set('code', b.code);
                    location.href = location.pathname + '?' + q.toString();
                });
                items.appendChild(item);
            }
            col.appendChild(items);
            panel.appendChild(col);
        }

        // 折列：按面板顶端到视口底部的剩余高度，给每个 .bg-items 设确定的 height，
        // 纵向 wrap 把超出的银行折到右边新起一子列（对应石油图例的 layoutLegendColumns）。
        // 两个坑：① 只设 max-height 时 Chrome 不折列，直接溢出；② 折列后容器的
        // 固有宽度仍按单列算（量到 116px），子列会溢出到面板外，所以宽度也要一起算好写死。
        // 面板 hidden 时量不到尺寸，只在展开后调用。
        function layoutBankColumns() {
            const cols = [...panel.querySelectorAll('.bg-items')];
            for (const items of cols) {
                items.style.height = 'auto';
                items.style.width = 'auto';
            }
            const top = panel.getBoundingClientRect().top;
            const avail = Math.max(200, window.innerHeight - top - 40);
            const COL_GAP = 10;   // 与 base.css 里 .bg-items 的 gap: 2px 10px 保持一致
            for (const items of cols) {
                const kids = [...items.children];
                if (!kids.length) continue;
                const head = items.previousElementSibling;
                const headH = head ? head.getBoundingClientRect().height + 6 : 0;
                const cap = Math.max(140, avail - headH - 28);   // 28 ≈ 面板上下 padding
                const r0 = kids[0].getBoundingClientRect();
                // step = 行高 + 行间距（单列状态下量两项的间距，比读 computed gap 稳）
                const step = kids.length > 1
                    ? kids[1].getBoundingClientRect().top - r0.top
                    : r0.height;
                const perCol = Math.max(1, Math.floor((cap + (step - r0.height)) / step));
                const nCol = Math.ceil(kids.length / perCol);
                const rows = Math.min(kids.length, perCol);
                items.style.height = (rows * step - (step - r0.height)) + 'px';
                items.style.width = (nCol * r0.width + (nCol - 1) * COL_GAP) + 'px';
            }
        }

        // 面板是 position: fixed 且挂在 body 下（导航条 overflow-x: auto 会把绝对定位的
        // 子元素整块裁掉，放里面根本看不见），所以每次展开都要按触发按钮的位置摆一次，
        // 并把右边界夹回视口内——切换器本身靠右，折出子列后面板很容易伸出屏幕。
        function place() {
            const tr = trigger.getBoundingClientRect();
            panel.style.top = (tr.bottom + 6) + 'px';
            panel.style.left = '0px';
            const w = panel.getBoundingClientRect().width;
            panel.style.left = Math.max(12, Math.min(tr.left, window.innerWidth - 12 - w)) + 'px';
        }

        function openPanel(on) {
            panel.hidden = !on;
            if (on) {
                place();              // 先摆好位置，layoutBankColumns 要按面板 top 算可用高度
                layoutBankColumns();
                place();              // 折列后宽度变了，再夹一次左边界
            }
        }

        trigger.addEventListener('click', e => {
            e.stopPropagation();
            openPanel(panel.hidden);
        });
        document.addEventListener('click', e => {
            if (!box.contains(e.target) && !panel.contains(e.target)) panel.hidden = true;
        });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') panel.hidden = true;
        });
        window.addEventListener('resize', () => { if (!panel.hidden) openPanel(true); });
        // 导航条 sticky 在顶部，页面滚动时按钮位置不变；但滚动条出现/消失会改视口宽度，
        // 保险起见滚动时也重新夹一次位置（面板展开时才做，开销可忽略）。
        window.addEventListener('scroll', () => { if (!panel.hidden) place(); }, {passive: true});

        box.append(label, trigger);
        document.body.appendChild(panel);
        return box;
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
        center.appendChild(makeBankSwitch());
        nav.appendChild(center);
        document.body.insertBefore(nav, document.body.firstChild);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
