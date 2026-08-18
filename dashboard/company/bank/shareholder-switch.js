/* 股东页·银行切换器
 * 渝农商行（默认 yns）由 charts.js 从后端 /api/company_charts 渲染并缓存到 window.__companyD；
 * 其余 4 家对比银行（农业/招商/民生/天津）数据静态内置于本文件——每年一个股东户数点、
 * 取各行历年年报（A+H 两地上市优先 A 股年报，天津仅 H 股）。
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

    function years(from, to) {
        var a = [];
        for (var y = from; y <= to; y++) a.push('' + y);
        return a;
    }

    var BANKS = {};

    // ────── 农业银行 601288（A 股 2010-07-15 / H 股 2010-07-16） ──────
    BANKS['601288'] = {
        h1: '中国农业银行（农业银行）2025 年报 · 股东',
        title: '农业银行（601288 / 01288）2025 年报 · 股东',
        meta: 'A 股 601288（上交所） · H 股 01288（港交所） · A 股上市 2010-07-15 · 国有大型商业银行 · 单位：人民币百万元（另标注除外）',
        holdersSub: '报告期末股东总数 573,979 户（A 股 555,177 户、H 股 18,802 户）· 前十名股东合计 94.91%（按总股本 3,499.83 亿股）',
        dividendSub: '来源：本行历年 A 股年度报告「利润分配方案」· 2010 年 A+H 上市以来历年每 10 股现金分红（含税）',
        holderUnit: 'wan',
        holderNote: '数据来源：农业银行历年 A 股年度报告「普通股股东情况」章节，A 股股东数为股东总数扣除 H 股登记股东。2010-07-15 A 股、07-16 H 股同步上市；本图取各年年末年报口径。A+H 两地上市，同一年份优先采用 A 股年报数据。',
        holderCount: [
            ['2010',587690,32609],['2011',364394,30814],['2012',270341,29953],['2013',270427,28585],
            ['2014',348611,27749],['2015',566284,26288],['2016',451484,25969],['2017',327868,24555],
            ['2018',413427,23162],['2019',366871,22819],['2020',441542,22168],['2021',472971,21435],
            ['2022',464338,21030],['2023',411529,20541],['2024',421966,19807],['2025',555177,18802]
        ],
        top10Sum: 94.91,
        top10: [
            ['中央汇金',40.14,'—','国有股东','soe'],
            ['财政部',35.29,'—','国有股东','soe'],
            ['香港中央结算(代理人)',8.73,'—','境外/H股','hk'],
            ['全国社保基金',6.72,'—','社保基金','ssf'],
            ['中国平安人寿',1.67,'—','保险资金','ins'],
            ['中国烟草',0.72,'—','国有股东','soe'],
            ['中国证券金融',0.53,'—','国有股东','soe'],
            ['香港中央结算(沪股通)',0.39,'—','境外/H股','hk'],
            ['上海海烟',0.36,'—','国有股东','soe'],
            ['中央汇金资产',0.36,'—','国有股东','soe']
        ],
        holdersNote: '十大股东与占比取自 2025 年 A 股年度报告「前 10 名股东持股情况」。红=国有股东、青=境外/H 股、黄=社保基金、蓝=保险资金、灰=其他流通股东。前十大合计 94.91%，中央汇金 + 财政部合计 75.43%，国有绝对控股。',
        dividend: { years9: years(2010, 2025),
            per10: [0.54,1.315,1.565,1.77,1.82,1.668,1.70,1.783,1.739,1.819,1.851,2.068,2.222,2.309,2.419,2.495] },
        dividendNote: '2010-2025 每 10 股现金分红（含税），取自本行历年 A 股年度报告「利润分配方案」。农业银行长期维持约 30% 现金分红率，每股派息随盈利稳步提升。'
    };

    /* __BANKS_CMB__ */

    // ────── 招商银行 600036（A 股 2002-04-09 / H 股 2006-09-22） ──────
    BANKS['600036'] = {
        h1: '招商银行 2025 年报 · 股东',
        title: '招商银行（600036 / 03968）2025 年报 · 股东',
        meta: 'A 股 600036（上交所） · H 股 03968（港交所） · A 股上市 2002-04-09 · 股份制商业银行 · 单位：人民币百万元（另标注除外）',
        holdersSub: '报告期末股东总数 479,538 户（A 股 453,281 户、H 股 26,257 户）· 前十名股东合计 64.78%（按总股本 252.20 亿股）',
        dividendSub: '来源：本行历年 A 股年度报告「利润分配方案」· 2002 年 A 股上市以来历年每 10 股现金分红（含税）',
        holderUnit: 'wan',
        holderNote: '数据来源：招商银行历年 A 股年度报告「股东情况」章节，A 股股东数为股东总数扣除 H 股登记股东（2006 年 H 股上市前仅 A 股）。2002-04-09 A 股上市、2006-09-22 H 股上市；2013 年年度报告缺失，该年股东户数留空。A+H 两地上市，优先采用 A 股年报。',
        holderCount: [
            ['2002',135879,null],['2003',160917,null],['2004',158951,null],['2005',150832,null],
            ['2006',127028,70247],['2007',323917,47789],['2008',436457,45109],['2009',592946,44728],
            ['2010',697136,41715],['2011',551710,44327],['2012',485297,48567],['2013',null,null],
            ['2014',401536,41289],['2015',228756,37967],['2016',177249,37347],['2017',192451,35281],
            ['2018',255217,33602],['2019',231096,32767],['2020',377267,31494],['2021',491920,29976],
            ['2022',541363,29271],['2023',647881,28569],['2024',431886,27289],['2025',453281,26257]
        ],
        top10Sum: 64.78,
        top10: [
            ['香港中央结算(代理人)',18.06,'—','境外/H股','hk'],
            ['招商局轮船',13.04,'—','国有股东','soe'],
            ['中国远洋运输',6.24,'—','国有股东','soe'],
            ['深圳市晏清投资',4.99,'—','国有股东','soe'],
            ['香港中央结算(沪股通)',4.84,'—','境外/H股','hk'],
            ['招商局金融控股',4.55,'—','国有股东','soe'],
            ['和谐健康保险',4.48,'—','保险资金','ins'],
            ['深圳市楚源投资',3.74,'—','国有股东','soe'],
            ['中远海运(广州)',2.76,'—','国有股东','soe'],
            ['中国证券金融',2.08,'—','国有股东','soe']
        ],
        holdersNote: '十大股东取自 2025 年 A 股年度报告。招商局集团系（招商局轮船 + 招商局金融控股 + 中远海运系等）为实际控制人；红=国有、青=境外/H 股、蓝=保险、灰=其他流通股东。前十大合计 64.78%。',
        dividend: { years9: years(2002, 2025),
            per10: [1.2,0.92,1.1,0.8,1.2,2.8,1.0,2.1,2.9,4.2,6.3,6.2,6.7,6.9,7.4,8.4,9.4,12.0,12.53,15.22,17.38,19.72,20.0,20.16] },
        dividendNote: '2002-2025 每 10 股现金分红（含税），取自本行历年 A 股年度报告。2013 年年报缺失，该年数值取自 2014 年报「近三年利润分配」表。招商银行分红逐年提升，2025 年度每 10 股派 20.16 元。'
    };

    /* __BANKS_MS__ */

    // ────── 民生银行 600016（A 股 2000-12-19 / H 股 2009-11-26） ──────
    BANKS['600016'] = {
        h1: '中国民生银行（民生银行）2025 年报 · 股东',
        title: '民生银行（600016 / 01988）2025 年报 · 股东',
        meta: 'A 股 600016（上交所） · H 股 01988（港交所） · A 股上市 2000-12-19 · 首家民营股份制商业银行 · 单位：人民币百万元（另标注除外）',
        holdersSub: '报告期末股东总数 390,707 户（A 股 374,201 户、H 股 16,506 户）· 前十名股东合计 59.74%（按总股本 437.82 亿股）',
        dividendSub: '来源：本行历年 A 股年度报告「利润分配方案」· 2001 年以来历年每 10 股现金分红（含税，仅现金部分）',
        holderUnit: 'wan',
        holderNote: '数据来源：民生银行历年 A 股年度报告「股东情况」章节。2000-12-19 A 股上市、2009-11-26 H 股上市；A/H 分列自 2023 年报起披露，2023 起「A 股股东数」为股东总数扣除 H 股口径，此前年度仅披露股东总数（H 股占比极小，该线即披露的股东总数）。A+H 两地上市，优先采用 A 股年报。',
        holderCount: [
            ['2001',186115,null],['2002',178475,null],['2003',284316,null],['2004',315232,null],
            ['2005',277224,null],['2006',180102,null],['2007',1132682,null],['2008',1176563,null],
            ['2009',1221486,null],['2010',1123423,null],['2011',836369,null],['2012',691909,null],
            ['2013',681695,null],['2014',713958,null],['2015',395998,null],['2016',321080,null],
            ['2017',380550,null],['2018',389603,null],['2019',373372,null],['2020',421463,null],
            ['2021',435689,null],['2022',392914,null],['2023',322498,17782],['2024',325385,17251],
            ['2025',374201,16506]
        ],
        top10Sum: 59.74,
        top10: [
            ['香港中央结算(代理人)',18.93,'—','境外/H股','hk'],
            ['大家人寿-万能',10.30,'—','保险资金','ins'],
            ['大家人寿-传统',6.49,'—','保险资金','ins'],
            ['深圳市立业集团',4.49,'—','内资法人','corp'],
            ['新希望六和',4.18,'—','内资法人','corp'],
            ['中国长城资产',3.66,'—','国有股东','soe'],
            ['同方国信投资',3.36,'—','内资法人','corp'],
            ['上海健特生命',3.15,'—','内资法人','corp'],
            ['中国船东互保协会',3.02,'—','保险资金','ins'],
            ['香港中央结算(沪股通)',2.16,'—','境外/H股','hk']
        ],
        holdersNote: '十大股东取自 2025 年 A 股年度报告。民生银行为首家民营股份制银行，股权高度分散：青=境外/H 股、蓝=保险（大家人寿系）、橙=内资民营法人、红=国有、灰=其他流通股东。前十大合计 59.74%。',
        dividend: { years9: years(2001, 2025),
            per10: [0.70,0.60,1.20,0.70,0.50,0.0,0.50,0.80,0.50,1.00,3.00,3.00,2.58,1.85,2.35,2.80,1.50,3.45,3.70,2.13,2.13,2.14,2.16,1.92,1.89] },
        dividendNote: '2001-2025 每 10 股现金分红（含税，仅现金部分，不含送转股）。2006 年度未派现（记 0）。取自本行历年 A 股年度报告「利润分配方案」。'
    };

    // ────── 天津银行 01578.HK（仅 H 股 2016-03-30，无 A 股） ──────
    BANKS['01578'] = {
        h1: '天津银行 2025 年报 · 股东',
        title: '天津银行（01578.HK）2025 年报 · 股东',
        meta: 'H 股 01578（港交所） · H 股上市 2016-03-30 · 城市商业银行 · 仅 H 股上市（无 A 股） · 单位：人民币百万元（另标注除外）',
        holdersSub: '报告期末前十名股东合计 59.72%（按总股本 60.71 亿股）· 仅披露 H 股登记股东总数',
        dividendSub: '来源：本行历年年度报告「利润分配」· 2016 年 H 股上市以来历年每 10 股现金分红（含税）',
        holderUnit: 'hu',
        holderNote: '数据来源：天津银行历年年度报告「股东情况」。仅 H 股上市（01578.HK，2016-03-30），无 A 股，「H 股股东数」为 H 股登记股东；2016/2017 年报未披露登记股东总数，2018 年起披露约 7,200-7,300 户（单位：户，非万户）。',
        holderCount: [
            ['2016',null,null],['2017',null,null],['2018',null,7309],['2019',null,7312],
            ['2020',null,7330],['2021',null,7264],['2022',null,7243],['2023',null,7230],
            ['2024',null,7223],['2025',null,7249]
        ],
        top10Sum: 59.72,
        top10: [
            ['天津保税区投资',15.94,'—','国有股东','soe'],
            ['澳新银行',11.95,'—','境外/H股','hk'],
            ['天津医药集团',8.03,'—','国有股东','soe'],
            ['天津渤海化工',8.02,'—','国有股东','soe'],
            ['中船国际控股',4.99,'—','境外/H股','hk'],
            ['哈尔滨经济开发',2.75,'—','内资法人','corp'],
            ['天津海泰控股',2.46,'—','国有股东','soe'],
            ['天津津融投资',1.93,'—','国有股东','soe'],
            ['天津宁福投资',1.88,'—','内资法人','corp'],
            ['香港渤海租赁',1.76,'—','境外/H股','hk']
        ],
        holdersNote: '十大股东取自 2025 年年度报告「主要股东权益」。天津国资系（天津保税区投资 + 天津医药 + 渤海化工 + 海泰 + 津融等）为主导，澳新银行为境外战投；红=国有、青=境外/H 股、橙=内资法人、灰=其他流通股东。前十大合计 59.72%。',
        dividend: { years9: years(2016, 2025),
            per10: [2.0,1.8,1.8,1.8,0,0,0,1.2,1.368,1.368] },
        dividendNote: '2016-2025 每 10 股现金分红（含税），取自本行历年年度报告「利润分配」。2020-2022 三年受疫情及经营影响未派息（记 0），2023 年起恢复分红。'
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
    var switchEl = document.getElementById('bank-switch');
    if (!switchEl) return;
    var slider = switchEl.querySelector('.tab-slider');
    var tabs = [].slice.call(switchEl.querySelectorAll('.stack-tab'));

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

    function moveSlider(btn) {
        slider.style.width = btn.offsetWidth + 'px';
        slider.style.transform = 'translateX(' + btn.offsetLeft + 'px)';
    }

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

    function renderBank(code) {
        var b = BANKS[code];
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

    tabs.forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (btn.classList.contains('active')) return;
            tabs.forEach(function (t) { t.classList.remove('active'); });
            btn.classList.add('active');
            moveSlider(btn);
            var bank = btn.getAttribute('data-bank');
            if (bank === 'yns') renderYns();
            else renderBank(bank);
        });
    });

    // 初始：把滑块摆到 active 页签下（渝农商图表已由 charts.js 渲染，无需重绘）
    function initSlider() {
        var active = switchEl.querySelector('.stack-tab.active') || tabs[0];
        if (active) moveSlider(active);
    }
    initSlider();
    window.addEventListener('resize', initSlider);
    if (document.fonts) document.fonts.ready.then(initSlider);
})();
