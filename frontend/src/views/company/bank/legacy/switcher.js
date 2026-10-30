/* 图表上方的「快速切换银行」按钮面板（不属于 renderAll 分区，脚本加载即自行建按钮）：
 *   · #npl-amt-banks / #npl-amt-tiers —— 风控页不良贷款总额图，按行或按类型筛选对比；
 *   · #roe-banks —— 业绩页 ROE 图，单行切换或一键对比全部；
 *   · #provratio-banks —— 风控页拨贷比对比图，与 ROE 图同一套面板（__bankCmpPanel）。
 * 都复用 charts-compare.js 里的渲染函数，数据按需向同一个 /api/company_charts 端点拉并缓存。 */


/* ────── 
不良贷款总额图·筛选对比银行 ──────
 * 只有风控页（risk.html）里有 #npl-amt-banks；#npl-amt-tiers 是按类型勾选（国有大行等）。
 * 点单家银行：只画那一行。勾选类型：该类型全部叠线，可多选。一键对比全部仍可用。 */
(function () {
    var box = document.getElementById('npl-amt-banks');
    if (!box) return;
    var tierBox = document.getElementById('npl-amt-tiers');

    var BASE = '';
    var CACHE = {};
    var cur = document.getElementById('npl-amt-current');
    var note = document.getElementById('note-npl-amt');
    var OWN_NOTE = note ? note.innerHTML : '';
    // 本行那段说明在 _notes 里（模板只有空壳，charts.js 拉到数后才填），切回本行时从那里取
    function ownNote() {
        var n = (window.__companyD && window.__companyD._notes) || {};
        return n['note-npl-amt'] != null ? n['note-npl-amt'] : OWN_NOTE;
    }
    var btns = [];
    var TIER_ORDER = ['国有大行', '股份行', '城商行', '农商行'];
    var selected = {};      // code → true，当前要画的银行
    var checkedTiers = {};  // tier → true，勾选的类型

    function banks() {
        return (Array.isArray(window.__BANKS) && window.__BANKS.length) ? window.__BANKS : [];
    }
    function listByTier(tier) {
        return banks().filter(function (b) { return b.tier === tier; });
    }
    function nplSlice(D, code, name) {
        var sd = (D && D['scale-dep']) || {};
        return { code: code, name: name, years: sd.years || [], nplAmt: sd.nplAmt || [] };
    }
    function selectedList() {
        return banks().filter(function (b) { return selected[b.code]; });
    }
    function syncActive() {
        var list = banks();
        var nSel = selectedList().length;
        btns.forEach(function (b) {
            var code = b.getAttribute('data-code');
            var tier = b.getAttribute('data-tier');
            if (code === '__all') {
                b.classList.toggle('active', nSel === list.length && list.length > 0);
            } else if (tier) {
                var grp = listByTier(tier);
                b.classList.toggle('active', !!(checkedTiers[tier] && grp.length &&
                    grp.every(function (x) { return selected[x.code]; })));
            } else {
                b.classList.toggle('active', !!selected[code]);
            }
        });
    }
    function curLabel() {
        var tiers = TIER_ORDER.filter(function (x) { return checkedTiers[x]; });
        var n = selectedList().length;
        if (tiers.length) return tiers.join(' + ') + '（' + n + ' 家）';
        if (n === banks().length) return '全部对比（' + n + ' 家）';
        var one = selectedList()[0];
        return one ? one.name : '';
    }
    function drawOne(code, name, D) {
        if (!document.getElementById('chart-npl-amt')) return;
        window.__renderNplAmt(D);
        if (cur) cur.textContent = name;
        if (note) {
            var html = code === window.COMPANY_CODE ? ownNote() :
                ('当前显示 <b>' + name + '</b> 的不良贷款余额（亿元），口径为该行年报「五级分类」次级+可疑+损失合计。' +
                 '勾选上方类型可一次对比国有大行 / 股份行 / 城商行 / 农商行。');
            note.innerHTML = html;
            note.style.display = html ? '' : 'none';
        }
    }
    function drawCompare(items, label) {
        if (!document.getElementById('chart-npl-amt')) return;
        window.__renderNplAmtCompare(items);
        if (cur) cur.textContent = label || ('对比（' + items.length + ' 家）');
        if (note) {
            note.style.display = '';
            note.innerHTML = '正在对比 <b>' + (label || (items.length + ' 家')) + '</b> 的不良贷款余额，每行一条线。' +
                '口径均为各行年报「五级分类」不良合计。同类型内规模仍可能差一截；跨类型（大行 vs 农商行）量级差一个数量级，小行会贴底。' +
                '数据来源：各行历年年度报告「贷款五级分类」。';
        }
    }
    function fetchOne(b) {
        var D = b.code === window.COMPANY_CODE ? window.__companyD : CACHE[b.code];
        if (D) return Promise.resolve(nplSlice(D, b.code, b.name));
        if (typeof axios === 'undefined') return Promise.resolve(null);
        return axios.get(BASE + '/api/company_charts?code=' + b.code).then(function (res) {
            if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
            CACHE[b.code] = res.data.data;
            return nplSlice(res.data.data, b.code, b.name);
        }).catch(function (e) {
            console.error('不良总额：' + b.code + ' 数据拉取失败', e);
            return null;
        });
    }
    function paint() {
        var list = selectedList();
        if (!list.length) {
            var own = banks().filter(function (b) { return b.code === window.COMPANY_CODE; })[0];
            if (own) { selected[own.code] = true; list = [own]; }
        }
        syncActive();
        var label = curLabel();
        if (cur) cur.textContent = label + (list.length > 1 ? '（加载中…）' : '');
        Promise.all(list.map(fetchOne)).then(function (rows) {
            var items = rows.filter(function (r) {
                return r && r.nplAmt && r.nplAmt.some(function (v) { return v != null; });
            });
            if (!items.length) { if (cur) cur.textContent = '无可用数据'; return; }
            if (items.length === 1) {
                var b = list.filter(function (x) { return x.code === items[0].code; })[0] || list[0];
                var D = b.code === window.COMPANY_CODE ? window.__companyD : CACHE[b.code];
                if (D) drawOne(b.code, b.name, D);
            } else {
                drawCompare(items, label);
            }
        });
    }
    function pick(code) {
        selected = {};
        checkedTiers = {};
        selected[code] = true;
        paint();
    }
    function pickTier(tier) {
        if (checkedTiers[tier]) {
            delete checkedTiers[tier];
        } else {
            checkedTiers[tier] = true;
        }
        selected = {};
        var any = false;
        TIER_ORDER.forEach(function (tr) {
            if (!checkedTiers[tr]) return;
            listByTier(tr).forEach(function (b) { selected[b.code] = true; any = true; });
        });
        if (!any) {
            selected[window.COMPANY_CODE] = true;
        }
        paint();
    }
    function pickAll() {
        selected = {};
        checkedTiers = {};
        banks().forEach(function (b) { selected[b.code] = true; });
        TIER_ORDER.forEach(function (tr) {
            if (listByTier(tr).length) checkedTiers[tr] = true;
        });
        paint();
    }
    function build() {
        var list = banks();
        if (!list.length || box.querySelector('button')) return;
        if (tierBox && !tierBox.querySelector('button')) {
            TIER_ORDER.forEach(function (tr) {
                var n = listByTier(tr).length;
                if (!n) return;
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'tier';
                btn.setAttribute('data-tier', tr);
                btn.textContent = tr + '（' + n + '）';
                btn.addEventListener('click', function () { pickTier(tr); });
                tierBox.appendChild(btn);
                btns.push(btn);
            });
        }
        list.forEach(function (b) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.setAttribute('data-code', b.code);
            btn.textContent = b.name;
            btn.addEventListener('click', function () { pick(b.code); });
            box.appendChild(btn);
            btns.push(btn);
        });
        var all = document.createElement('button');
        all.type = 'button';
        all.className = 'cmp';
        all.setAttribute('data-code', '__all');
        all.textContent = '一键对比全部';
        all.addEventListener('click', pickAll);
        box.appendChild(all);
        btns.push(all);
        selected[window.COMPANY_CODE] = true;
        syncActive();
        var own = list.filter(function (b) { return b.code === window.COMPANY_CODE; })[0];
        if (own && cur) cur.textContent = own.name;
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();

/* ────── 多行对比面板·筛选银行（多选 / 按类型全选 / 五种视图） ──────
 * 业绩页 ROE 图（#roe-banks）与风控页拨贷比图（#provratio-banks）共用，页面上没有那排按钮的直接跳过。
 * 与导航条上的银行下拉框分工：下拉框换 ?code= 整页重载（整页都变成那家行），
 * 这排按钮不动页面主体，只把一张图换成别家行的曲线 —— 用来快速对照 ROE / 拨贷比高低。
 *
 * 选择：银行按钮是**多选开关**（点第二次取消），类型按钮一次勾/取消整组，
 *       「只看本行」「全部（45）」是两个批量动作。
 * 视图（选中 ≥2 家时才有意义，切换不改选择）：
 *   · 类型聚合（ROE 默认）每类型中位线 + 25–75 分位带 + 本行 —— 45 家时唯一读得动的画法
 *   · 逐家叠线   每行一条线、按类型分色系、悬浮淡化其余
 *   · 本行位次   本行在样本内 / 同类型内的历年名次（纵轴反向）
 *   · 分类型小图 2×2 小倍数，每类型一格、共用纵轴
 *   · 最新年份榜 取最新披露年份拉平成横条榜
 * 选中 1 家时忽略视图，交给 cfg.drawOne（ROE 画三段口径图）。
 * 数据按需向 /api/company_charts?code=<code> 拉（与主数据同一端点）并缓存，二次点击不再发请求。
 *
 * cfg：ids      { banks, tiers, views, current, note, chart } 页面元素 id
 *      metric   指标名，写进图下说明 / tooltip / 报错日志
 *      slice    (D) → { years, roeNew[, roeOld, roeCalc] }，喂给 compare.js 的多行渲染函数
 *      caliber  图下说明末尾的口径与数据来源
 *      oneHeight / drawOne(b, D, opt)  选中 1 家时的图高与画法（b 是 __BANKS 里那一项），返回图下说明
 *      view     多家时的默认视图
 *      initTier true 时首屏就画本行所属类型（图不在 renderAll 里，没人替它画首屏） */
function __bankCmpPanel(cfg) {
    var box = document.getElementById(cfg.ids.banks);
    if (!box) return;
    var tierBox = document.getElementById(cfg.ids.tiers);
    var viewBox = document.getElementById(cfg.ids.views);

    var BASE = '';
    var CACHE = {};          // code → payload；本页自身那家行进来时用 window.__companyD 填
    var cur = document.getElementById(cfg.ids.current);
    var note = document.getElementById(cfg.ids.note);
    var OWN_NOTE = note ? note.innerHTML : '';   // 本页银行的三段口径说明，切回来时还原
    function ownNote() {                          // 本行在 _notes 里给了这段就用它（模板里只剩空壳）
        var n = (window.__companyD && window.__companyD._notes) || {};
        return n[cfg.ids.note] != null ? n[cfg.ids.note] : OWN_NOTE;
    }
    var OPT = { id: cfg.ids.chart, metric: cfg.metric };
    var M = /^[A-Za-z]/.test(cfg.metric) ? ' ' + cfg.metric + ' ' : cfg.metric;   // 说明文字里嵌指标名：英文两侧留空格，中文不留
    var btns = [];
    var TIER_ORDER = window.__TIER_ORDER || ['国有大行', '股份行', '城商行', '农商行'];
    var selected = {};       // code → true，当前要画的银行
    var view = cfg.view || 'agg';   // agg | lines | rank | facet | bar —— 多家时的呈现方式
    var VIEWS = [
        { id: 'agg',   label: '类型聚合' },
        { id: 'lines', label: '逐家叠线' },
        { id: 'rank',  label: '本行位次' },
        { id: 'facet', label: '分类型小图' },
        { id: 'bar',   label: '最新年份榜' }
    ];

    // 可切换清单与导航下拉框同源：后端注入 window.__BANKS，静态打开时由 bank-header.js 兜底赋值。
    // bank-header.js 是 defer、本文件是普通脚本，所以按钮要等 DOMContentLoaded 再建。
    function banks() {
        return (Array.isArray(window.__BANKS) && window.__BANKS.length) ? window.__BANKS : [];
    }
    function listByTier(tier) {
        return banks().filter(function (b) { return (b.tier || '其他') === tier; });
    }
    function selectedList() {
        return banks().filter(function (b) { return selected[b.code]; });
    }
    function ownBank() {
        return banks().filter(function (b) { return b.code === window.COMPANY_CODE; })[0];
    }

    function syncActive() {
        var n = selectedList().length, total = banks().length;
        var onlyOwn = n === 1 && selected[window.COMPANY_CODE];
        btns.forEach(function (b) {
            var code = b.getAttribute('data-code');
            var tier = b.getAttribute('data-tier');
            var v = b.getAttribute('data-view');
            if (v) {
                b.classList.toggle('active', n > 1 && v === view);
                b.style.opacity = n < 2 ? 0.5 : '';
            } else if (code === '__all') {
                b.classList.toggle('active', n === total && total > 0);
            } else if (code === '__own') {
                b.classList.toggle('active', onlyOwn);
            } else if (tier) {
                var grp = listByTier(tier);
                b.classList.toggle('active', !!(grp.length &&
                    grp.every(function (x) { return selected[x.code]; })));
            } else {
                b.classList.toggle('active', !!selected[code]);
            }
        });
    }
    function viewLabel() {
        var v = VIEWS.filter(function (x) { return x.id === view; })[0];
        return v ? v.label : '';
    }
    function curLabel() {
        var n = selectedList().length;
        if (n === 1) return selectedList()[0].name;
        var tiers = TIER_ORDER.filter(function (t) {
            var g = listByTier(t);
            return g.length && g.every(function (x) { return selected[x.code]; });
        });
        var who = (n === banks().length) ? ('全部 ' + n + ' 家')
                : ((tiers.length ? tiers.join(' + ') + ' ' : '') + n + ' 家');
        return viewLabel() + '　' + who;
    }

    // 各视图对图高的需求不同：条形榜按家数算高度，小倍数要四格，聚合/位次一屏就够
    function setHeight(px) {
        var el = document.getElementById(cfg.ids.chart);
        if (!el || el.style.height === px) return;
        el.style.height = px;
        var ins = window.echarts && echarts.getInstanceByDom(el);
        if (ins) ins.resize();   // 容器高度是 JS 改的，ECharts 不会自己知道
    }

    // 图下说明里的类型色标：与 compare.js 的 __TIER_COLORS 同源，家数多时图上没有银行图例，
    // 靠这行认「哪个色系是哪类机构」
    function tierKey() {
        var C = window.__TIER_COLORS || {};
        return TIER_ORDER.filter(function (t) { return C[t]; }).map(function (t) {
            return '<span style="display:inline-block;width:26px;height:3px;vertical-align:middle;' +
                   'background:' + C[t][0] + ';margin:0 5px 0 12px"></span>' + t;
        }).join('');
    }
    var CALIBER = cfg.caliber;

    function draw(b, D) {
        if (!document.getElementById(cfg.ids.chart)) return;   // 本页该图已被 __stub 摘掉 id
        setHeight(cfg.oneHeight);
        var txt = cfg.drawOne(b, D, OPT);
        if (cur) cur.textContent = b.name;
        if (note) note.innerHTML = (b.code === window.COMPANY_CODE && ownNote()) ? ownNote() : txt;
    }

    // 各视图：渲染函数 + 图高 + 图下说明，一处配齐，paint 只管派发
    var RENDER = {
        agg: function (items, label) {
            setHeight('520px');
            window.__renderRoeTierAgg(items, OPT);
            return '<b>类型聚合</b>：选中的 ' + items.length + ' 家按机构类型收成每类型一条<b>中位数线</b>，' +
                '本行所属类型再加一条<b>25–75 分位带</b>（其余类型不画带，四条带叠在一起会糊）。' +
                '深色粗线是本页银行：落在带内属中游，带上/带下即高于/低于四分之三同类。' +
                '分位数按<b>每年实际有披露的行</b>现算；悬停按类型 2×2 分块。色标：' + tierKey() + '。' + CALIBER;
        },
        lines: function (items, label) {
            setHeight(items.length > 14 ? '560px' : '520px');
            window.__renderRoeCompare(items, OPT);
            return '<b>逐家叠线</b>：' + items.length + ' 家各一条线，按机构类型分配色系：' + tierKey() +
                '（同类型内换深浅、色板用尽再叠虚线，深粗线是本页银行）。悬浮某条线时其余线淡出；' +
                'tooltip 按类型 2×2 分块、块内由高到低，超过 8 家的类型再分两栏。超过 14 家时不放银行图例，' +
                '认线靠悬浮与 tooltip。家数多时更适合「类型聚合」或「分类型小图」。' + CALIBER;
        },
        rank: function (items, label) {
            setHeight('480px');
            window.__renderRoeRank(items, OPT);
            return '<b>本行位次</b>：不看' + M + '绝对值，只看本页银行在样本里排第几 —— 实线是在选中的 ' +
                items.length + ' 家中的名次，虚线是在<b>同类型内</b>的名次，纵轴反向（第 1 名在最上）。' +
                '分母逐年变（当年有披露的行才计入），tooltip 里给出「第 a / n 名」与当年' + M.replace(/ $/, '') + '。' +
                '并列时取靠前的名次。' + CALIBER;
        },
        facet: function (items, label) {
            setHeight('720px');
            window.__renderRoeFacet(items, OPT);
            return '<b>分类型小图</b>：一个机构类型一格（2×2 小倍数），每格家数落到十家上下、线就分得开。' +
                '四格<b>共用同一纵轴上限</b>，格与格之间可以直接横比（否则轴不同会造成「城商行更高」的错觉）。' +
                '本页银行在自己那一格是深色实线，其余三格补一条深色虚线做参照。' + CALIBER;
        },
        bar: function (items, label) {
            setHeight(Math.max(360, items.length * 24 + 90) + 'px');
            window.__renderRoeBar(items, OPT);
            return '<b>最新年份榜</b>：把最新披露年份的' + M + '拉平成横条、由高到低排，按类型着色，' +
                '本页银行深色加粗 —— 回答「今年谁高谁低」。个别行年报未出时取<b>它自己最新的披露年份</b>' +
                '并在数值后标出该年份，读数时注意年份不齐。' + CALIBER;
        }
    };

    function fetchOne(b) {
        var D = b.code === window.COMPANY_CODE ? window.__companyD : CACHE[b.code];
        if (D) return Promise.resolve({ code: b.code, name: b.name, tier: b.tier || '其他', roe: cfg.slice(D) });
        if (typeof axios === 'undefined') return Promise.resolve(null);
        return axios.get(BASE + '/api/company_charts?code=' + b.code).then(function (res) {
            if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
            CACHE[b.code] = res.data.data;
            return { code: b.code, name: b.name, tier: b.tier || '其他', roe: cfg.slice(res.data.data) };
        }).catch(function (e) {
            console.error(cfg.metric + ' 对比：' + b.code + ' 数据拉取失败', e);
            return null;   // 谁失败就跳过谁，不因一家挂掉整图空白
        });
    }

    function paint() {
        var list = selectedList();
        if (!list.length) {                     // 全部取消后退回本行，不留空图
            var own = ownBank();
            if (own) { selected[own.code] = true; list = [own]; }
        }
        syncActive();
        var label = curLabel();
        if (cur) cur.textContent = label + (list.length > 1 ? '（加载中…）' : '');
        Promise.all(list.map(fetchOne)).then(function (rows) {
            var items = rows.filter(function (r) { return r && r.roe && (r.roe.years || []).length; });
            if (!items.length) { if (cur) cur.textContent = label + '（无可用数据）'; return; }
            if (!document.getElementById(cfg.ids.chart)) return;
            if (items.length === 1) {
                var b = list.filter(function (x) { return x.code === items[0].code; })[0] || list[0];
                // 首屏就画的面板可能赶在主数据回来之前，本行 payload 此时只在 CACHE 里
                var D = (b.code === window.COMPANY_CODE && window.__companyD) || CACHE[b.code];
                if (D) draw(b, D);
                return;
            }
            var txt = (RENDER[view] || RENDER.agg)(items, label);
            if (cur) cur.textContent = label;
            if (note) note.innerHTML = txt;
        });
    }

    function toggleBank(code) {
        if (selected[code]) { delete selected[code]; } else { selected[code] = true; }
        paint();
    }
    function toggleTier(tier) {
        var grp = listByTier(tier);
        var all = grp.length && grp.every(function (b) { return selected[b.code]; });
        grp.forEach(function (b) { if (all) { delete selected[b.code]; } else { selected[b.code] = true; } });
        paint();
    }
    function pickOwn() {
        selected = {};
        selected[window.COMPANY_CODE] = true;
        paint();
    }
    function pickAll() {
        selected = {};
        banks().forEach(function (b) { selected[b.code] = true; });
        // 45 家叠线读不动；点「全部」落到类型聚合（四条中位线 + 本行带）
        if (view === 'lines') view = 'agg';
        paint();
    }
    function pickView(id) {
        view = id;
        // 视图只对多家有意义：单家时收进本行所属类型，不要偷偷勾上全部 45 家
        if (selectedList().length < 2) {
            var own = ownBank();
            var grp = own ? listByTier(own.tier || '') : [];
            if (grp.length) grp.forEach(function (b) { selected[b.code] = true; });
        }
        paint();
    }

    function mkBtn(parent, text, cls, attrs, onClick) {
        var btn = document.createElement('button');
        btn.type = 'button';
        if (cls) btn.className = cls;
        Object.keys(attrs || {}).forEach(function (k) { btn.setAttribute(k, attrs[k]); });
        btn.textContent = text;
        btn.addEventListener('click', onClick);
        parent.appendChild(btn);
        btns.push(btn);
        return btn;
    }

    function build() {
        var list = banks();
        if (!list.length || box.querySelector('button')) return;
        if (tierBox && !tierBox.querySelector('button')) {
            TIER_ORDER.forEach(function (t) {
                var n = listByTier(t).length;
                if (!n) return;
                mkBtn(tierBox, t + '（' + n + '）', 'tier', { 'data-tier': t },
                    function () { toggleTier(t); });
            });
            mkBtn(tierBox, '只看本行', 'cmp', { 'data-code': '__own' }, pickOwn);
            mkBtn(tierBox, '全部（' + list.length + '）', 'cmp', { 'data-code': '__all' }, pickAll);
        }
        if (viewBox && !viewBox.querySelector('button')) {
            VIEWS.forEach(function (v) {
                mkBtn(viewBox, v.label, 'tier', { 'data-view': v.id }, function () { pickView(v.id); });
            });
        }
        list.forEach(function (b) {
            mkBtn(box, b.name, '', { 'data-code': b.code }, function () { toggleBank(b.code); });
        });
        selected[window.COMPANY_CODE] = true;
        var own = ownBank();
        if (cfg.initTier && own) {
            listByTier(own.tier || '其他').forEach(function (b) { selected[b.code] = true; });
            paint();
            return;
        }
        syncActive();
        // 本页银行的名字由数据里的 _bank 元信息给（HTML 里的静态文案是渝农商行版本）
        if (own && cur) cur.textContent = own.name;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
}

__bankCmpPanel({
    ids: { banks: 'roe-banks', tiers: 'roe-tiers', views: 'roe-views',
           current: 'roe-current', note: 'note-roe', chart: 'chart-roe' },
    metric: 'ROE',
    slice: function (D) { return D['roe']; },
    caliber: '口径拼接规则——同一年优先取年报披露的<b>新准则加权平均净资产收益率</b>，' +
        '该年未披露时退到<b>旧准则加权平均股东权益回报率</b>，仍无则用<b>简单 ROE</b>（净利/平均权益，' +
        '仅渝农商行 2009–2013 手工补算）；2018 年前后同一条线存在准则切换断口。' +
        '各行起始年份不同（多数行数据自 2014 或 2018 年起），缺披露的年份断开。' +
        '数据来源：各行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_&lt;code&gt;.json</code>。',
    oneHeight: '400px',
    drawOne: function (b, D) {
        window.__renderRoe(D);
        return '当前显示 <b>' + b.name + '</b> 的 ROE，三段口径同上（简单 ROE / 旧准则 / 新准则加权平均净资产收益率）。' +
            '数据来源：该行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_' + b.code + '.json</code>。' +
            '按钮切回本页银行可看完整口径说明。';
    }
});

/* 风控页拨贷比：比率指标、各行可直接横比，首屏就叠出本行所属类型，点「全部」「最新年份榜」看全样本排名 */
__bankCmpPanel({
    ids: { banks: 'provratio-banks', tiers: 'provratio-tiers', views: 'provratio-views',
           current: 'provratio-current', note: 'note-provratio', chart: 'chart-provratio' },
    metric: '拨贷比',
    slice: function (D) {
        var n = (D && D['nim-trend']) || {};
        return { years: n.provYears || [], roeNew: n.provRatio || [] };
    },
    caliber: '拨贷比 = 贷款损失准备 ÷ 各项贷款余额，取各行年报披露值；各行起始年份不同（多数自 2013 年起），' +
        '缺披露的年份断开。拨贷比 = 不良率 × 拨备覆盖率，读高低时可对照本页不良率与上方拨备覆盖率。' +
        '数据来源：各行历年年度报告「财务摘要」「主要监管指标」，经 <code>data/tables/company_charts_&lt;code&gt;.json</code>。',
    oneHeight: '420px',
    drawOne: function (b, D, opt) {
        window.__renderRoeCompare([{ code: b.code, name: b.name, tier: b.tier || '其他',
                                     roe: this.slice(D) }], opt);
        return '当前只显示 <b>' + b.name + '</b> 的拨贷比。点上方类型或银行叠加对比，' +
            '「最新年份榜」看当年谁高谁低。' + this.caliber;
    },
    view: 'lines',
    initTier: true
});
