/* 图表上方的「快速切换银行」按钮面板（不属于 renderAll 分区，脚本加载即自行建按钮）：
 *   · #npl-amt-banks / #npl-amt-tiers —— 风控页不良贷款总额图，按行或按类型筛选对比；
 *   · #roe-banks —— 业绩页 ROE 图，单行切换或一键对比全部。
 * 两者都复用 charts-compare.js 里的渲染函数，数据按需向同一个 /api/company_charts 端点拉并缓存。 */


/* ────── 
不良贷款总额图·筛选对比银行 ──────
 * 只有风控页（risk.html）里有 #npl-amt-banks；#npl-amt-tiers 是按类型勾选（国有大行等）。
 * 点单家银行：只画那一行。勾选类型：该类型全部叠线，可多选。一键对比全部仍可用。 */
(function () {
    var box = document.getElementById('npl-amt-banks');
    if (!box) return;
    var tierBox = document.getElementById('npl-amt-tiers');

    var BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
    var CACHE = {};
    var cur = document.getElementById('npl-amt-current');
    var note = document.getElementById('note-npl-amt');
    var OWN_NOTE = note ? note.innerHTML : '';
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
            note.style.display = '';
            note.innerHTML = code === window.COMPANY_CODE ? OWN_NOTE :
                ('当前显示 <b>' + name + '</b> 的不良贷款余额（亿元），口径为该行年报「五级分类」次级+可疑+损失合计。' +
                 '勾选上方类型可一次对比国有大行 / 股份行 / 城商行 / 农商行。');
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

/* ────── ROE 图·快速切换银行 ──────
 * 只有业绩页（index.html）里有 #roe-banks 这排按钮，其余页面本块直接跳过。
 * 与导航条上的银行下拉框分工：下拉框换 ?code= 整页重载（整页都变成那家行），
 * 这排按钮不动页面主体，只把 ROE 一张图换成别家行的曲线 —— 用来快速对照 ROE 高低。
 * 数据按需向 /api/company_charts?code=<code> 拉（与主数据同一端点）并缓存，二次点击不再发请求。 */
(function () {
    var box = document.getElementById('roe-banks');
    if (!box) return;

    var BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
    var CACHE = {};          // code → payload；本页自身那家行进来时用 window.__companyD 填
    var cur = document.getElementById('roe-current');
    var note = document.getElementById('note-roe');
    var OWN_NOTE = note ? note.innerHTML : '';   // 本页银行的三段口径说明，切回来时还原
    var btns = [];

    // 可切换清单与导航下拉框同源：后端注入 window.__BANKS，静态打开时由 bank-header.js 兜底赋值。
    // bank-header.js 是 defer、本文件是普通脚本，所以按钮要等 DOMContentLoaded 再建。
    function banks() {
        return (Array.isArray(window.__BANKS) && window.__BANKS.length) ? window.__BANKS : [];
    }

    function setActive(code) {
        btns.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-code') === code); });
    }

    // 对比模式要塞十条线加两行图例，400px 高度不够；切回单行时还原，避免图被拉得空旷
    function setHeight(px) {
        var el = document.getElementById('chart-roe');
        if (!el || el.style.height === px) return;
        el.style.height = px;
        var ins = window.echarts && echarts.getInstanceByDom(el);
        if (ins) ins.resize();   // 容器高度是 JS 改的，ECharts 不会自己知道
    }

    function draw(code, name, D) {
        if (!document.getElementById('chart-roe')) return;   // 本页该图已被 __stub 摘掉 id
        setHeight('400px');
        window.__renderRoe(D);
        if (cur) cur.textContent = name;
        if (note) {
            note.innerHTML = code === window.COMPANY_CODE ? OWN_NOTE :
                ('当前显示 <b>' + name + '</b> 的 ROE，三段口径同上（简单 ROE / 旧准则 / 新准则加权平均净资产收益率）。' +
                 '数据来源：该行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_' + code + '.json</code>。' +
                 '按钮切回本页银行可看完整口径说明。');
        }
    }

    function drawCompare(items) {
        if (!document.getElementById('chart-roe')) return;
        setHeight('600px');
        window.__renderRoeCompare(items);
        if (cur) cur.textContent = '全部对比（' + items.length + ' 家）';
        if (note) {
            note.innerHTML = '一键对比：' + items.length + ' 家银行的 ROE 画在同一张图，每行一条线。' +
                '口径拼接规则——同一年优先取年报披露的<b>新准则加权平均净资产收益率</b>，' +
                '该年未披露时退到<b>旧准则加权平均股东权益回报率</b>，仍无则用<b>简单 ROE</b>（净利/平均权益，' +
                '仅渝农商行 2009–2013 手工补算）。因此 2018 年前后同一条线存在准则切换断口，跨段比较请留意。' +
                '各行起始年份不同（多数行数据自 2014 或 2018 年起），缺披露的年份线段断开。' +
                '本页银行画粗线并在末端标数值；银行家数超过配色轮数时，第二轮改用虚线区分。' +
                '数据来源：各行历年年度报告「主要财务指标」，经 <code>data/tables/company_charts_&lt;code&gt;.json</code>。';
        }
    }

    function pick(code, name) {
        setActive(code);
        // 本页自身那家行：主数据已在 window.__companyD 里，不再发请求
        var D = code === window.COMPANY_CODE ? window.__companyD : CACHE[code];
        if (D) { draw(code, name, D); return; }
        if (typeof axios === 'undefined') return;
        if (cur) cur.textContent = name + '（加载中…）';
        axios.get(BASE + '/api/company_charts?code=' + code).then(function (res) {
            if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
            CACHE[code] = res.data.data;
            draw(code, name, res.data.data);
        }).catch(function (e) {
            console.error('ROE 快速切换：' + code + ' 数据拉取失败', e);
            if (cur) cur.textContent = name + '（数据拉取失败）';
        });
    }

    // 一键对比：把清单里所有行的数据凑齐（缓存里没有的并发拉），谁失败就跳过谁，不因一家挂掉整图空白
    function pickAll() {
        setActive('__all');
        if (typeof axios === 'undefined') return;
        var list = banks();
        if (cur) cur.textContent = '全部对比（加载中…）';
        var jobs = list.map(function (b) {
            var D = b.code === window.COMPANY_CODE ? window.__companyD : CACHE[b.code];
            if (D) return Promise.resolve({ code: b.code, name: b.name, roe: D['roe'] });
            return axios.get(BASE + '/api/company_charts?code=' + b.code).then(function (res) {
                if (!res.data || res.data.code !== 200 || !res.data.data) throw new Error(res.data && res.data.msg);
                CACHE[b.code] = res.data.data;
                return { code: b.code, name: b.name, roe: res.data.data['roe'] };
            }).catch(function (e) {
                console.error('ROE 一键对比：' + b.code + ' 数据拉取失败', e);
                return null;
            });
        });
        Promise.all(jobs).then(function (rows) {
            // 没有 roe 这一项的行（该行数据里缺这块）也一并剔掉，免得图例挂空名字
            var items = rows.filter(function (r) { return r && r.roe && (r.roe.years || []).length; });
            if (!items.length) { if (cur) cur.textContent = '全部对比（无可用数据）'; return; }
            drawCompare(items);
        });
    }

    function build() {
        var list = banks();
        if (!list.length || box.querySelector('button')) return;
        list.forEach(function (b) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.setAttribute('data-code', b.code);
            btn.textContent = b.name;
            btn.addEventListener('click', function () { pick(b.code, b.name); });
            box.appendChild(btn);
            btns.push(btn);
        });
        // 对比按钮排在最后，用 .cmp 与单行按钮区分（样式里给了实心边框）
        var all = document.createElement('button');
        all.type = 'button';
        all.className = 'cmp';
        all.setAttribute('data-code', '__all');
        all.textContent = '一键对比全部';
        all.addEventListener('click', pickAll);
        box.appendChild(all);
        btns.push(all);
        setActive(window.COMPANY_CODE);
        // 本页银行的名字由数据里的 _bank 元信息给（HTML 里的静态文案是渝农商行版本）
        var own = list.filter(function (b) { return b.code === window.COMPANY_CODE; })[0];
        if (own && cur) cur.textContent = own.name;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }
})();
