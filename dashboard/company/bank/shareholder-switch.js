/* 股东页·银行切换器
 * 渝农商行（默认 yns）由 charts.js 从后端 /api/company_charts 渲染并缓存到 window.__companyD；
 * 其余 4 家对比银行（农业/招商/民生/天津）数据不再内置于本文件，改为点击时按需向
 * /api/company_charts?code=<code> 拉取（data/tables/company_charts_<code>.json，
 * 由 data/extract/gen_bank_shareholder_data.js 从旧内置数据一次性抽取），拉到后缓存复用。
 * 股东结构环形/条形图 + 历年分红复用 charts.js 暴露的 window.__renderYnsHolders / __renderYnsDividend；
 * 股东户数图各行 A/H 量级不同，用本文件的通用渲染器 renderHolderCount（轴自适应）。 */
(function () {
    'use strict';

    // 派系/性质配色（与渝农商图例风格一致）
    var CAT = {
        soe:   { title: '国有股东',      color: '#c0392b' },
        hk:    { title: '境外 / H 股',   color: '#16a085' },
        ssf:   { title: '社保基金',      color: '#f1c40f' },
        ins:   { title: '保险资金',      color: '#2980b9' },
        corp:  { title: '内资法人',      color: '#e67e22' },
        other: { title: '其他',          color: '#6c3483' },
        float: { title: '其他流通股东',  color: '#95a5a6' }
    };

    // ── 由 top10 + 其他流通股东 构造 __renderYnsHolders 所需的 holders 载荷 ──
    function buildHolders(b) {
        var holderData = b.top10.map(function (h) {
            return { name: h[0], value: h[1], itemStyle: { color: CAT[h[4]].color } };
        });
        var floatPct = +(100 - b.top10Sum).toFixed(2);
        holderData.push({ name: '其他流通股东', value: floatPct, itemStyle: { color: CAT.float.color } });

        var holders = b.top10.map(function (h) {
            return { name: h[0], pct: h[1], chg: h[2], type: h[3] };
        });
        holders.push({ name: '其他流通股东', pct: floatPct, chg: '—', type: '流通股' });

        var order = [], grp = {};
        b.top10.forEach(function (h) {
            var k = h[4];
            if (!grp[k]) { grp[k] = { title: CAT[k].title, color: CAT[k].color, names: [] }; order.push(k); }
            grp[k].names.push(h[0]);
        });
        grp.float = { title: CAT.float.title, color: CAT.float.color, names: ['其他流通股东'] };
        order.push('float');
        var factions = order.map(function (k) { return grp[k]; });

        return { holders: holders, holderData: holderData, factions: factions,
                 centerText: '前十大\n' + b.top10Sum.toFixed(2) + '%' };
    }

    // ── 通用历年股东户数渲染器：A 股股东数 + H 股股东数（各行 A/H 量级不同，轴自适应；不加 dataZoom） ──
    function renderHolderCount(b) {
        var el = document.getElementById('chart-holder-count');
        if (!el) return;
        var inst = echarts.getInstanceByDom(el) || echarts.init(el);
        var rows = b.holderCount;
        var dates = rows.map(function (r) { return r[0]; });
        var aNum  = rows.map(function (r) { return r[1]; });
        var hNum  = rows.map(function (r) { return r[2]; });
        var hasA  = aNum.some(function (v) { return v != null; });
        var hasH  = hNum.some(function (v) { return v != null; });
        var isWan = b.holderUnit === 'wan';
        var A = '#2c6fb3', H = '#16a085';   // 与渝农商 __renderYnsHolderCount 一致：A 股蓝、H 股青
        var aName = isWan ? 'A 股股东数（万户）' : 'A 股股东数（户）';
        var hName = 'H 股股东数（户）';
        var wanLabel = function (v) { return isWan ? (v / 10000).toFixed(0) : v.toLocaleString('en-US'); };
        var showA = function (v) {
            if (v == null) return '—';
            return isWan ? (v / 10000).toFixed(2) + ' 万户（' + v.toLocaleString('en-US') + ' 户）'
                         : v.toLocaleString('en-US') + ' 户';
        };

        var yAxis = [], series = [], legendData = [];
        if (hasA) {
            yAxis.push({
                type: 'value', name: aName, min: 0, position: 'left',
                nameTextStyle: { color: A, fontSize: 18 },
                axisLabel: { color: A, fontSize: 18, formatter: wanLabel },
                splitLine: { lineStyle: { color: '#eee' } }
            });
            series.push({
                name: aName, type: 'line', data: aNum, smooth: true, symbolSize: 6,
                connectNulls: false,
                lineStyle: { width: 3, color: A },
                itemStyle: { color: A },
                areaStyle: { color: 'rgba(44,111,179,0.10)' },
                endLabel: { show: true, fontSize: 16, color: A,
                    formatter: function (p) { return p.value == null ? '' : (isWan ? (p.value / 10000).toFixed(2) + ' 万' : p.value.toLocaleString('en-US')); } }
            });
            legendData.push(aName);
        }
        if (hasH) {
            var onLeft = !hasA;   // 无 A 股（天津仅 H 股）时，H 股占据主轴
            yAxis.push({
                type: 'value', name: hName, min: 0, position: onLeft ? 'left' : 'right',
                nameTextStyle: { color: H, fontSize: 18 },
                axisLabel: { color: H, fontSize: 18, formatter: function (v) { return v.toLocaleString('en-US'); } },
                splitLine: onLeft ? { lineStyle: { color: '#eee' } } : { show: false }
            });
            series.push({
                name: hName, type: 'line', yAxisIndex: hasA ? 1 : 0, data: hNum,
                smooth: true, symbolSize: onLeft ? 6 : 8, connectNulls: true,
                lineStyle: { width: onLeft ? 3 : 2.5, color: H },
                itemStyle: { color: H },
                areaStyle: onLeft ? { color: 'rgba(22,160,133,0.10)' } : undefined,
                endLabel: { show: true, fontSize: 16, color: H,
                    formatter: function (p) { return p.value == null ? '' : p.value.toLocaleString('en-US') + ' 户'; } }
            });
            legendData.push(hName);
        }

        inst.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            legend: { data: legendData, top: 4, left: 'center', textStyle: { fontSize: 16 }, icon: 'roundRect' },
            tooltip: {
                trigger: 'axis', textStyle: { fontSize: 18 },
                formatter: function (p) {
                    var i = p[0].dataIndex;
                    var parts = ['<b>' + dates[i] + '</b>'];
                    if (hasA) parts.push('A 股股东数：' + showA(aNum[i]));
                    if (hasH) parts.push('H 股股东数：' + (hNum[i] == null ? '—' : hNum[i].toLocaleString('en-US') + ' 户'));
                    if (aNum[i] == null && hNum[i] == null) parts.push('<span style="color:#888">（该年未披露）</span>');
                    return parts.join('<br>');
                }
            },
            grid: { left: 92, right: (hasA && hasH) ? 160 : 60, top: 56, bottom: 70 },
            xAxis: {
                type: 'category', data: dates, boundaryGap: false,
                axisLabel: { fontSize: 16, color: '#555', rotate: 40 },
                axisLine: { lineStyle: { color: '#bbb' } }
            },
            yAxis: yAxis,
            series: series
        }, true);   // notMerge —— 切行时清掉上一行的轴/系列，避免残留合并
    }

    // ─────────────────────── 切换逻辑 ───────────────────────
    // 切换按钮挂在顶部导航条居中的页面链接簇里（common/bank-header.js 注入 .site-nav 之后再插入 .nav-center），
    // 正文里不再放胶囊控件：点导航栏的银行名，本页所有图表/文案即整体切成该行数据。
    var NAV_BANKS = [
        { bank: 'yns',    label: '渝农商行' },
        { bank: '601288', label: '农业银行' },
        { bank: '600036', label: '招商银行' },
        { bank: '600016', label: '民生银行' },
        { bank: '01578',  label: '天津银行' }
    ];
    var navBtns = [];

    var elH1   = document.getElementById('page-h1');
    var elMeta = document.getElementById('page-meta');
    var elHSub = document.getElementById('holders-sub');
    var elDSub = document.getElementById('dividend-sub');
    var noteHC = document.getElementById('note-holder-count-g');
    var noteHD = document.getElementById('note-holders-g');
    var noteDV = document.getElementById('note-dividend-g');

    // 缓存渝农商默认文案（页面初始即 yns，charts.js 已渲染其图表）。
    // h1/title 不缓存——它们由 charts.js 的 __applyBankIdentity 按 ?code= 的银行元信息拼出，
    // 本文件加载时后端数据还没回来，缓存到的会是 HTML 里的兜底文案。
    var YNS = {
        meta: elMeta ? elMeta.innerHTML : '',
        holdersSub: elHSub ? elHSub.innerHTML : '',
        dividendSub: elDSub ? elDSub.innerHTML : ''
    };

    // yns 专属说明/折叠条/分红卡片显隐；对比银行改用通用说明块
    function toggleYns(showYns) {
        [].forEach.call(document.querySelectorAll('.yns-only'), function (el) {
            el.style.display = showYns ? '' : 'none';
        });
        [noteHC, noteHD, noteDV].forEach(function (el) {
            if (el) el.style.display = showYns ? 'none' : '';
        });
    }

    // 切行前销毁 4 张图，避免不同结构的 option 发生残留合并
    function disposeCharts() {
        ['chart-holder-count', 'chart-holders', 'chart-holders-h', 'chart-holders-h-only', 'chart-holders-bar', 'chart-dividend-per10', 'chart-share-capital'].forEach(function (id) {
            var el = document.getElementById(id);
            var inst = el && echarts.getInstanceByDom(el);
            if (inst) inst.dispose();
        });
    }

    function renderYns() {
        var D = window.__companyD;
        if (!D) return;   // 后端数据尚未就绪
        window.__applyBankIdentity(D);   // 复位 h1/title 到本页 ?code= 对应的银行
        if (elMeta) elMeta.innerHTML = YNS.meta;
        if (elHSub) elHSub.innerHTML = YNS.holdersSub;
        if (elDSub) elDSub.innerHTML = YNS.dividendSub;
        toggleYns(true);
        disposeCharts();
        window.__renderYnsHolderCount(D);
        window.__renderYnsHolders(D);
        window.__renderYnsDividend(D);
        window.__renderYnsShareCapital();
    }

    function renderBank(b) {
        if (!b) return;
        if (elH1)   elH1.innerHTML = b.h1;
        if (elMeta) elMeta.innerHTML = b.meta;
        document.title = b.title;
        if (elHSub) elHSub.innerHTML = b.holdersSub;
        if (elDSub) elDSub.innerHTML = b.dividendSub;
        if (noteHC) noteHC.innerHTML = b.holderNote;
        if (noteHD) noteHD.innerHTML = b.holdersNote;
        if (noteDV) noteDV.innerHTML = b.dividendNote;
        toggleYns(false);
        disposeCharts();
        renderHolderCount(b);
        window.__renderYnsHolders({ holders: buildHolders(b) });
        window.__renderYnsDividend({ 'dividend-per10': b.dividend });
    }

    // 对比行数据按需拉取：点击时才向 /api/company_charts?code=<code> 请求（与渝农商行同一端点），
    // 拉到后缓存到 BANK_CACHE，二次点击直接复用不再发请求。
    var BANK_API = 'http://127.0.0.1:5000/api/company_charts?code=';
    var BANK_CACHE = {};

    function loadBank(code) {
        if (BANK_CACHE[code]) { renderBank(BANK_CACHE[code]); return; }
        axios.get(BANK_API + code).then(function (res) {
            if (!res.data || res.data.code !== 200) {
                throw new Error(res.data && res.data.msg || 'company_charts load failed');
            }
            BANK_CACHE[code] = res.data.data;
            renderBank(res.data.data);
        }).catch(function (e) { console.error('对比行 ' + code + ' 数据拉取失败', e); });
    }

    function select(btn) {
        if (btn.classList.contains('active')) return;
        navBtns.forEach(function (t) { t.classList.remove('active'); });
        btn.classList.add('active');
        var bank = btn.getAttribute('data-bank');
        if (bank === 'yns') renderYns();
        else loadBank(bank);
    }

    // 导航条由 common/bank-header.js（defer）注入，本文件在解析期就执行，
    // 所以按钮要等 DOMContentLoaded——那时 defer 脚本已跑完，.site-nav 一定在。
    // 渝农商行为默认选中项，其图表已由 charts.js 渲染，这里不重绘。
    function buildNavSwitch() {
        var nav = document.querySelector('.site-nav');
        if (!nav || nav.querySelector('.nav-banks')) return;
        // 放进 .nav-center（页面链接所在的居中簇）而不是 .site-nav 直下：
        // 导航「链接真正居中」靠的是右侧隐藏镜像抵消左侧 brand，右侧再多一个不可压缩的
        // 488px 按钮组会把链接簇挤偏（1440 视口偏 -70px）。同簇内则两侧仍对称。
        var box = document.createElement('div');
        box.className = 'nav-banks';
        NAV_BANKS.forEach(function (b, i) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'nav-bank' + (i === 0 ? ' active' : '');
            btn.setAttribute('data-bank', b.bank);
            btn.textContent = b.label;
            btn.addEventListener('click', function () { select(btn); });
            box.appendChild(btn);
            navBtns.push(btn);
        });
        (nav.querySelector('.nav-center') || nav).appendChild(box);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildNavSwitch);
    } else {
        buildNavSwitch();
    }
})();
