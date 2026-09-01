/* 中国移动「客户与网络」页：移动客户与净增、制式渗透（3G/4G/5G）、
   有线宽带与家庭市场、物联网与政企、网络规模与员工。
   数据全部来自 window.CMCC.operating（历年年报「主要运营数据」与官网营运数据页）。

   本页所有序列都可能有披露起点差异（4G 从 2013、5G 从 2019/2020、千兆宽带从 2020 前后），
   一律留 null 不插值；起点差异用图上的说明与「口径提示」段落解释。 */

var OP = (C.operating && C.operating.annual) || {};
var AN = (C.annual && C.annual.annual) || {};
var OMETA = (C.operating && C.operating._meta) || {};

var Y = years(OP, 'mobileSubs');
var LAST = Y[Y.length - 1], PREV = Y[Y.length - 2];
var L = OP[LAST] || {}, P = OP[PREV] || {};

/* 最新一代制式：5G 有披露就用 5G，否则退到 4G */
var GEN = years(OP, 'subs5G').length ? { field: 'subs5G', name: '5G 网络客户' }
        : years(OP, 'subs4G').length ? { field: 'subs4G', name: '4G 客户' }
        : null;

/* ==== 概览 ==== */
setText('kpi-sub',
    '口径：' + LAST + ' 年末数 · 移动客户数与宽带客户数为公司披露的期末口径 · '
    + (L._reportBasis || OMETA.sourcePrimary || '公司年报「业务概览－主要运营数据」'));
renderKpis('main-kpis', [
    { label: LAST + ' 移动客户数', value: L.mobileSubs == null ? '—' : fx(L.mobileSubs, 2) + ' 亿户',
      delta: L.netAddSubs == null ? yoyTxt(L.mobileSubs, P.mobileSubs)
                                  : '当年净增 ' + thou(L.netAddSubs) + ' 万户' },
    GEN ? { label: LAST + ' ' + GEN.name,
            value: L[GEN.field] == null ? '—' : fx(L[GEN.field], 2) + ' 亿户',
            delta: (L[GEN.field] != null && L.mobileSubs)
                ? '渗透率 ' + pct(L[GEN.field] / L.mobileSubs * 100) : '' }
        : { label: '制式客户数', value: '—' },
    { label: LAST + ' 有线宽带客户数',
      value: L.broadbandSubs == null ? '—' : fx(L.broadbandSubs, 2) + ' 亿户',
      delta: yoyTxt(L.broadbandSubs, P.broadbandSubs) },
    { label: LAST + ' 物联网卡连接数',
      value: L.iotConnections == null ? '—' : fx(L.iotConnections, 2) + ' 亿',
      delta: yoyTxt(L.iotConnections, P.iotConnections) },
    { label: LAST + ' 移动 ARPU',
      value: L.arpu == null ? '—' : fx(L.arpu, 1) + ' 元/户/月', delta: yoyTxt(L.arpu, P.arpu) },
    { label: LAST + ' 员工总数',
      value: L.employees == null ? '—' : thou(L.employees) + ' 人', delta: yoyTxt(L.employees, P.employees) }
]);

/* ==== 移动客户与净增 ==== */
mount('chart-subs', function () {
    var o = axisBase({ x: Y, left: 84, right: 104 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('当年净增（万户）', { position: 'right', splitLine: false })];
    o.series = [
        { name: '移动客户总数（亿户）', type: 'bar', barWidth: '56%', itemStyle: { color: NAVY },
          data: pick(OP, Y, 'mobileSubs') },
        { name: '当年净增客户数（万户）', type: 'line', yAxisIndex: 1, symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD }, connectNulls: false,
          data: pick(OP, Y, 'netAddSubs') }
    ];
    return o;
});

/* ==== 制式渗透 ==== */
/* 三代客户数不能堆叠——5G 客户同时也是移动客户，堆起来会重复计算。
   这里画的是「当年已升级到最新一代」与「尚未升级」两层，柱高恒等于移动客户总数；
   「最新一代」逐年取该年披露过的最高制式（5G→4G→3G），因此 2001 年至今每一年都有柱子，
   不会因为某代还没出现而留下一片空白。 */
function genOf(y) {
    var r = OP[y] || {};
    if (r.subs5G != null) return { v: r.subs5G, name: '5G' };
    if (r.subs4G != null) return { v: r.subs4G, name: '4G' };
    if (r.subs3G != null) return { v: r.subs3G, name: '3G' };
    return { v: null, name: null };
}
mount('chart-tech', function () {
    var o = axisBase({ x: Y, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('最新一代渗透率 %', { position: 'right', splitLine: false, min: 0, max: 100 })];
    o.series = [
        { name: '当年最新制式客户（亿户）', type: 'bar', stack: 't', barWidth: '58%',
          itemStyle: { color: '#c0392b' },
          data: Y.map(function (y) { return genOf(y).v; }) },
        { name: '尚未升级到最新制式（亿户）', type: 'bar', stack: 't',
          itemStyle: { color: shade(NAVY, 0.55) },
          data: Y.map(function (y) {
              var r = OP[y], g = genOf(y).v;
              if (r.mobileSubs == null) return null;
              return +Math.max(0, r.mobileSubs - (g || 0)).toFixed(2);
          }) },
        { name: '最新一代渗透率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
          lineStyle: { width: 3 }, itemStyle: { color: GOLD }, connectNulls: false,
          data: Y.map(function (y) {
              var r = OP[y], g = genOf(y).v;
              if (!r.mobileSubs || g == null) return null;
              return +(g / r.mobileSubs * 100).toFixed(1);
          }) },
        { name: '3G 客户（亿户）', type: 'line', symbolSize: 6,
          lineStyle: { width: 2.5, type: 'dotted' }, itemStyle: { color: MUTED },
          connectNulls: false, data: pick(OP, Y, 'subs3G') },
        { name: '4G 客户（亿户）', type: 'line', symbolSize: 6,
          lineStyle: { width: 2.5, type: 'dashed' }, itemStyle: { color: ERA_COLORS.data },
          connectNulls: false, data: pick(OP, Y, 'subs4G') },
        { name: '5G 套餐客户（亿户，另一口径）', type: 'line', symbolSize: 6,
          lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#e67e22' },
          connectNulls: false, data: pick(OP, Y, 'subs5GPackage') }
    ];
    o.legend.type = 'scroll';
    return o;
});

/* ==== 宽带与家庭 ==== */
mount('chart-broadband', function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].broadbandSubs != null || OP[y].homeArpu != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('元/户/月', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '有线宽带客户数（亿户）', type: 'bar', barWidth: '26%',
          itemStyle: { color: ERA_COLORS.broadband }, data: pick(OP, xs, 'broadbandSubs') },
        { name: '其中家庭宽带（亿户）', type: 'bar', barWidth: '26%',
          itemStyle: { color: shade(ERA_COLORS.broadband, 0.4) }, data: pick(OP, xs, 'homeBroadbandSubs') },
        { name: '千兆宽带（亿户）', type: 'bar', barWidth: '26%',
          itemStyle: { color: GOLD }, data: pick(OP, xs, 'gigabitSubs') },
        { name: '家庭客户综合 ARPU（元/户/月）', type: 'line', yAxisIndex: 1, symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: NAVY }, connectNulls: false,
          data: pick(OP, xs, 'homeArpu') }
    ];
    o.legend.type = 'scroll';
    return o;
});

/* ==== 物联网与政企 ==== */
mount('chart-iot', function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].iotConnections != null || OP[y].govEntSubs != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108 });
    o.yAxis = [valueAxis('亿（连接）', { min: 0 }),
               valueAxis('百万（政企客户）', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '物联网卡连接数（亿）', type: 'bar', barWidth: '54%',
          itemStyle: { color: ERA_COLORS.appInfo }, data: pick(OP, xs, 'iotConnections') },
        { name: '政企客户数（百万）', type: 'line', yAxisIndex: 1, symbolSize: 8,
          lineStyle: { width: 3 }, itemStyle: { color: NAVY }, connectNulls: false,
          data: pick(OP, xs, 'govEntSubs') },
        { name: '移动客户数（亿户，参照线）', type: 'line', symbolSize: 6,
          lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: MUTED }, connectNulls: false,
          data: pick(OP, xs, 'mobileSubs') }
    ];
    o.legend.type = 'scroll';
    return o;
});

/* ==== 网络与员工 ==== */
mount('chart-network', function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].base5G != null || OP[y].idcRacks != null || OP[y].employees != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('万（站 / 架）', { min: 0 }),
               valueAxis('万人', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '5G 基站数（万站）', type: 'bar', barWidth: '30%', itemStyle: { color: '#c0392b' },
          data: pick(OP, xs, 'base5G') },
        { name: '对外服务 IDC 标准机架（万架）', type: 'bar', barWidth: '30%',
          itemStyle: { color: ERA_COLORS.appInfo }, data: pick(OP, xs, 'idcRacks') },
        { name: '员工总数（万人）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
          itemStyle: { color: NAVY }, connectNulls: false,
          data: xs.map(function (y) {
              var v = OP[y].employees;
              return v == null ? null : +(v / 10000).toFixed(1);
          }) }
    ];
    o.legend.type = 'scroll';
    return o;
});

/* ==== 明细表 ==== */
(function () {
    var TY = Y.slice(-12);
    setHTML('tbl-head', '<th>指标</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
    var ROWS = [
        { label: '移动客户数（亿户）', field: 'mobileSubs', dec: 2, total: true },
        { label: '　当年净增（万户）', field: 'netAddSubs', dec: 0, sub: true },
        { label: '　3G 客户（亿户）', field: 'subs3G', dec: 2, sub: true },
        { label: '　4G 客户（亿户）', field: 'subs4G', dec: 2, sub: true },
        { label: '　5G 网络客户（亿户）', field: 'subs5G', dec: 2, sub: true },
        { label: '　5G 套餐客户（亿户）', field: 'subs5GPackage', dec: 2, sub: true },
        { label: 'MOU（分钟/户/月）', field: 'mou', dec: 0 },
        { label: 'DOU（GB/户/月）', field: 'dou', dec: 1 },
        { label: '移动 ARPU（元/户/月）', field: 'arpu', dec: 1 },
        { label: '有线宽带客户数（亿户）', field: 'broadbandSubs', dec: 2, total: true },
        { label: '　其中家庭宽带（亿户）', field: 'homeBroadbandSubs', dec: 2, sub: true },
        { label: '　千兆宽带（亿户）', field: 'gigabitSubs', dec: 2, sub: true },
        { label: '家庭客户综合 ARPU（元/户/月）', field: 'homeArpu', dec: 1 },
        { label: '政企客户数（百万）', field: 'govEntSubs', dec: 2 },
        { label: '物联网卡连接数（亿）', field: 'iotConnections', dec: 2 },
        { label: '5G 基站数（万站）', field: 'base5G', dec: 1 },
        { label: '员工总数（人）', field: 'employees' }
    ];
    renderRows('tbl-body', ROWS.map(function (r) {
        return {
            _th: true,
            _cls: r.total ? 'row-total' : (r.sub ? 'row-sub' : ''),
            cells: [r.label].concat(TY.map(function (y) {
                var v = OP[y] ? OP[y][r.field] : null;
                if (v == null) return '—';
                return r.dec !== undefined ? fx(v, r.dec) : thou(v);
            }))
        };
    }));
})();

/* ==== 说明文字 ==== */
(function () {
    var naY = years(OP, 'netAddSubs');
    var iotY = years(OP, 'iotConnections');

    setHTML('kpi-note',
        '<b>客户数这条线在 ' + LAST + ' 年已经基本走平。</b>'
        + (naY.length >= 3
            ? '净增客户数从 ' + naY[0] + ' 年的 ' + thou(OP[naY[0]].netAddSubs) + ' 万户，到 '
              + naY[naY.length - 1] + ' 年的 ' + thou(OP[naY[naY.length - 1]].netAddSubs) + ' 万户；'
            : '')
        + '在移动客户已超过 10 亿户、渗透率接近饱和之后，'
        + '「连接数」的增量主要来自物联网与宽带，而不是手机用户——这也是收入结构必须换代的直接原因。');

    setHTML('subs-note',
        '柱子是存量、线是增量。<b>存量看起来一直在涨，但增量早就掉了一个数量级</b>：'
        + '存量图的斜率变化不明显，增量线的落差才是真实的经营压力。'
        + (OMETA.definitions && OMETA.definitions.subsBasis ? '口径：' + OMETA.definitions.subsBasis : ''));

    setHTML('tech-note',
        '柱子只分「当年最新制式」与「尚未升级」两层，<b>柱高恒等于当年移动客户总数</b>——'
        + '不把 3G/4G/5G 三代堆在一起，因为 5G 客户同时也是移动客户，堆叠会重复计算。'
        + '「最新制式」逐年取该年披露过的最高制式（3G→4G→5G），所以 2001 年至今每年都有柱子，'
        + '不会因为某一代还没出现而出现空档；换代的加速度就体现在深色部分吃满柱子的速度上。'
        + '<b>橙色虚线是「5G 套餐客户」，与红柱的「5G 网络客户」是两个口径</b>，'
        + '2021–2023 年两者同时披露、相差 1.8 至 3.3 亿户；'
        + '把 2023 的套餐口径直接接到 2024 的网络口径上，会读出一次并不存在的负增长。'
        + (OMETA.definitions && OMETA.definitions.gen5GBasis
            ? '<b>口径提示：</b>' + OMETA.definitions.gen5GBasis : ''));

    setHTML('broadband-note',
        '宽带是产品更迭里「接棒流量」的那一环：<b>它的 ARPU 比移动 ARPU 更稳</b>，'
        + '因为家庭宽带是按户订阅、迁移成本高。千兆宽带与 FTTR 是同一批客户里的升级，'
        + '不是新增客户——看渗透而不是看总数。'
        + (OMETA.definitions && OMETA.definitions.broadbandBasis
            ? '<b>口径提示：</b>' + OMETA.definitions.broadbandBasis : ''));

    setHTML('iot-note',
        (iotY.length
            ? '物联网连接数从 ' + iotY[0] + ' 年的 ' + fx(OP[iotY[0]].iotConnections, 2) + ' 亿涨到 '
              + iotY[iotY.length - 1] + ' 年的 ' + fx(OP[iotY[iotY.length - 1]].iotConnections, 2) + ' 亿，'
              + '<b>已经是移动客户数的 '
              + (L.iotConnections && L.mobileSubs ? fx(L.iotConnections / L.mobileSubs, 1) : '—')
              + ' 倍。</b>'
            : '')
        + '但要注意：物联网卡的单卡 ARPU 远低于手机用户，连接数的增长与收入的增长不是同一个量级——'
        + '这是读运营商「连接数」时最容易被误导的地方。');

    setHTML('network-note',
        '网络规模与员工放在一起看：<b>每一轮制式换代都是先加基站、再加机架，人却基本不加</b>。'
        + '缺披露的年份留空不插值（早年年报未披露 5G/IDC 这类指标是自然的，因为业务还不存在）。');

    /* 口径缺口 */
    var FIELDS = [
        ['mobileSubs', '移动客户数'], ['netAddSubs', '净增客户数'],
        ['subs3G', '3G 客户数'], ['subs4G', '4G 客户数'],
        ['subs5G', '5G 网络客户数'], ['subs5GPackage', '5G 套餐客户数'],
        ['mou', 'MOU'], ['dou', 'DOU'], ['arpu', '移动 ARPU'],
        ['broadbandSubs', '有线宽带客户数'], ['homeArpu', '家庭客户综合 ARPU'],
        ['govEntSubs', '政企客户数'], ['iotConnections', '物联网卡连接数'],
        ['base5G', '5G 基站数'], ['idcRacks', 'IDC 标准机架'], ['employees', '员工总数']
    ];
    var allY = Object.keys(OP).sort();
    var items = FIELDS.map(function (p) {
        var ys = years(OP, p[0]);
        if (!ys.length) return '<b>' + p[1] + '</b>：数据源中无任何年份披露。';
        var missing = allY.filter(function (y) {
            return +y > +ys[0] && +y < +ys[ys.length - 1] && OP[y][p[0]] == null;
        });
        return '<b>' + p[1] + '</b>：披露 ' + ys[0] + '–' + ys[ys.length - 1] + '（' + ys.length + ' 年）'
            + (missing.length ? '，区间内缺 ' + missing.join('、') : '') + '。';
    });
    if (OMETA.gaps) {
        Object.keys(OMETA.gaps).forEach(function (k) { items.push('<b>' + k + '</b>：' + OMETA.gaps[k]); });
    }
    if (OMETA.definitions) {
        Object.keys(OMETA.definitions).forEach(function (k) {
            items.push('<b>' + k + '</b>：' + OMETA.definitions[k]);
        });
    }
    renderList('gaps-list', items);
})();
