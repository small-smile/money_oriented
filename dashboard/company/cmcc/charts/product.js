/* 中国移动「产品更迭」页：主营业务收入按产品拆分、MOU 与 DOU 的剪刀差、
   语音→流量→算力的收入接棒、ARPU 与客户数，以及产品世代时间线。

   这一页的设计前提：运营商的产品口径二十多年换了几轮，序列天然不连续。
   处理办法不是让线断在那里，而是
   （1）堆叠图里把「主营业务收入 − 已单列各产品线」的差额画成灰斜线「未单列」层，
        任何一年的柱子高度都等于当年主营业务收入，柱子不缺口；
   （2）折线图里把停止披露的区间用 gapMark() 画成带文字的灰带；
   （3）口径变化的原文说明由数据里的 _meta.gaps / _meta.definitions 直接渲染。 */

var AN = (C.annual && C.annual.annual) || {};
var OP = (C.operating && C.operating.annual) || {};
var META = (C.annual && C.annual._meta) || {};
var OMETA = (C.operating && C.operating._meta) || {};
var PROF = C.profile || {};

/* x 轴取所有有营运收入的年份：2013 年前公司未把终端销售单列，
   「营运收入」本身即通信服务口径，用它当分母才不会在 2013 年前留一片空白。 */
var Y = years(AN, 'totalRevenue');
var LAST = Y[Y.length - 1], PREV = Y[Y.length - 2];
var L = AN[LAST] || {}, P = AN[PREV] || {};

/* 产品线定义：顺序即堆叠顺序（老产品在下、新产品在上）。
   哪一年由哪几层构成，不靠这里猜——每年数据里的 mixLayers 明确列出当年的「完全划分」，
   本页只画在 mixLayers 里出现的层，因此绝不会出现「增值业务」与它的子项（短信/无线上网）
   同时入栈的重复计算。 */
var LINES = [
    { field: 'voiceRevenue',     name: '语音（通话费）',   color: ERA_COLORS.voice },
    { field: 'monthlyFee',       name: '月租费',           color: shade(ERA_COLORS.voice, 0.35) },
    { field: 'connectionFee',    name: '入网费',           color: shade(ERA_COLORS.voice, 0.6) },
    { field: 'smsRevenue',       name: '短信及彩信',       color: ERA_COLORS.sms },
    { field: 'vasRevenue',       name: '增值业务（旧口径合计）', color: ERA_COLORS.vas },
    { field: 'dataBusinessRevenue', name: '数据业务（合计口径）', color: shade(ERA_COLORS.data, 0.35) },
    { field: 'dataRevenue',      name: '无线上网（手机流量）', color: ERA_COLORS.data },
    { field: 'broadbandRevenue', name: '有线宽带',         color: ERA_COLORS.broadband },
    { field: 'appInfoRevenue',   name: '应用及信息服务',   color: ERA_COLORS.appInfo },
    { field: 'otherServiceRevenue', name: '其他（主营内）', color: '#8fa0b3' }
];

/* 当年收入拆分的分母：2013 年起用主营业务收入（通信服务收入），
   2013 年之前公司的「营运收入」本身就是通信服务口径（终端销售未单独列示），
   两者不能混用，所以由数据里的 mixBase 指定，缺失时退到 serviceRevenue / totalRevenue。 */
function mixBase(y) {
    var r = AN[y] || {};
    if (r.mixBase != null) return r.mixBase;
    if (r.serviceRevenue != null) return r.serviceRevenue;
    return r.totalRevenue != null ? r.totalRevenue : null;
}
/* 当年参与堆叠的层 */
function layersOf(y) {
    var r = AN[y] || {};
    return r.mixLayers || [];
}
/* 已单列层的合计；一层都没有时返回 null */
function disclosedSum(y) {
    var ls = layersOf(y), got = false, sum = 0;
    ls.forEach(function (f) {
        var v = AN[y] ? AN[y][f] : null;
        if (v !== null && v !== undefined) { got = true; sum += v; }
    });
    return got ? sum : null;
}
/* 分母里没被任何一层覆盖的残余 */
function residual(y) {
    var base = mixBase(y);
    if (base === null) return null;
    var d = disclosedSum(y);
    if (d === null) return base;
    return Math.max(0, +(base - d).toFixed(0));
}

/* ==== 主线 KPI ==== */
(function () {
    var dY = years(AN, 'dataRevenue');
    var vY = years(AN, 'voiceRevenue');
    setText('thesis-sub',
        '口径：主营业务收入（不含终端销售等其他业务）· 单位人民币亿元 · '
        + '语音收入披露区间 ' + (vY.length ? vY[0] + '–' + vY[vY.length - 1] : '无')
        + '，无线上网收入披露区间 ' + (dY.length ? dY[0] + '–' + dY[dY.length - 1] : '无'));

    var items = [];
    if (vY.length) {
        var vFirst = AN[vY[0]], vLast = AN[vY[vY.length - 1]];
        items.push({
            label: '语音收入峰值 → 停止单列前',
            value: yiTxt(Math.max.apply(null, vY.map(function (y) { return AN[y].voiceRevenue; }))),
            delta: vY[vY.length - 1] + ' 年最后一次单列 ' + yiTxt(vLast.voiceRevenue)
        });
    }
    if (dY.length) {
        items.push({
            label: '无线上网收入（' + dY[dY.length - 1] + '）',
            value: yiTxt(AN[dY[dY.length - 1]].dataRevenue),
            delta: dY[0] + ' 年为 ' + yiTxt(AN[dY[0]].dataRevenue)
        });
        var peak = dY.reduce(function (a, y) { return AN[y].dataRevenue > AN[a].dataRevenue ? y : a; }, dY[0]);
        items.push({ label: '无线上网收入峰值年', value: peak, delta: yiTxt(AN[peak].dataRevenue) });
    }
    var mouY = years(OP, 'mou'), douY = years(OP, 'dou');
    if (mouY.length) {
        items.push({
            label: 'MOU 峰值 → ' + mouY[mouY.length - 1],
            value: fx(Math.max.apply(null, mouY.map(function (y) { return OP[y].mou; })), 0) + ' → '
                + fx(OP[mouY[mouY.length - 1]].mou, 0) + ' 分钟',
            delta: '分钟/户/月'
        });
    }
    if (douY.length) {
        items.push({
            label: 'DOU ' + douY[0] + ' → ' + douY[douY.length - 1],
            value: fx(OP[douY[0]].dou, 1) + ' → ' + fx(OP[douY[douY.length - 1]].dou, 1) + ' GB',
            delta: 'GB/户/月'
        });
    }
    items.push({
        label: LAST + ' 主营业务收入',
        value: yiTxt(L.serviceRevenue),
        delta: yoyTxt(L.serviceRevenue, P.serviceRevenue)
    });
    renderKpis('thesis-kpis', items);
})();

/* ==== 收入构成：绝对额堆叠 ==== */
/* 每根柱子 = 当年主营业务收入；已单列的产品线各占一层，剩下的画成灰斜线「未单列」。
   这样任何一年都不会出现「柱子缺一块」的视觉断点，读者看到的是口径的厚薄变化。 */
function mixSeries(asShare) {
    var base = Y.map(function (y) { return mixBase(y); });
    function conv(v, i) {
        if (v === null || v === undefined) return null;
        if (!asShare) return toYi(v);
        return base[i] ? +(v / base[i] * 100).toFixed(1) : null;
    }
    var ss = LINES.map(function (ln, k) {
        return {
            name: ln.name, type: 'bar', stack: 'p',
            barWidth: k === 0 ? '60%' : undefined,
            itemStyle: { color: ln.color },
            data: Y.map(function (y, i) {
                /* 只画当年「完全划分」里包含的层，其余留 null —— 避免合计口径与子项重复入栈 */
                if (layersOf(y).indexOf(ln.field) < 0) return null;
                return conv(AN[y][ln.field], i);
            })
        };
    });
    ss.push({
        name: '未单列（并入主营其他）', type: 'bar', stack: 'p',
        itemStyle: { color: RESIDUAL_PATTERN, borderColor: '#c9cdd4', borderWidth: 1 },
        data: Y.map(function (y, i) { return conv(residual(y), i); })
    });
    return ss;
}
mount('chart-mix', function () {
    var o = axisBase({ x: Y, left: 88, right: 96, top: 56 });
    o.yAxis = [valueAxis('亿元', { min: 0 })];
    o.series = mixSeries(false);
    o.legend.type = 'scroll';
    return o;
});
mount('chart-mix-share', function () {
    var o = axisBase({ x: Y, left: 84, right: 96, top: 56 });
    o.yAxis = [valueAxis('占主营业务收入 %', { min: 0, max: 100 })];
    o.series = mixSeries(true);
    o.legend.type = 'scroll';
    return o;
});

/* ==== 用量剪刀差：MOU vs DOU ==== */
mount('chart-scissors', function () {
    /* x 轴取两个指标披露年份的并集，缺的一端留 null —— 起点不同本身就是信息 */
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].mou !== null && OP[y].mou !== undefined
            || OP[y].dou !== null && OP[y].dou !== undefined);
    }).sort();
    var mouY = years(OP, 'mou'), douY = years(OP, 'dou');
    var o = axisBase({ x: xs, left: 88, right: 100 });
    o.yAxis = [valueAxis('MOU 分钟/户/月', { min: 0 }),
               valueAxis('DOU GB/户/月', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: 'DOU 手机上网流量（GB/户/月）', type: 'bar', yAxisIndex: 1, barWidth: '54%',
          itemStyle: { color: ERA_COLORS.data }, data: pick(OP, xs, 'dou') },
        { name: 'MOU 通话分钟（分钟/户/月）', type: 'line', symbolSize: 8, lineStyle: { width: 3.5 },
          itemStyle: { color: ERA_COLORS.voice }, connectNulls: false, data: pick(OP, xs, 'mou'),
          markArea: (douY.length && +douY[0] > +xs[0])
              ? gapMark(xs, xs[0], String(+douY[0] - 1), 'DOU 尚未披露：流量还不是主要产品')
              : undefined }
    ];
    return o;
});

/* ==== 收入端的替代 ==== */
mount('chart-substitute', function () {
    var o = axisBase({ x: Y, left: 88, right: 108, top: 56 });
    o.yAxis = [valueAxis('亿元', { min: 0 })];
    var vLast = lastYear(AN, 'voiceRevenue');
    var sLast = lastYear(AN, 'smsRevenue');
    o.series = [
        { name: '语音业务收入', type: 'line', symbolSize: 8, lineStyle: { width: 3.5 },
          itemStyle: { color: ERA_COLORS.voice }, connectNulls: false,
          data: pick(AN, Y, 'voiceRevenue', toYi),
          markArea: (vLast && +vLast < +LAST)
              ? gapMark(Y, String(+vLast + 1), LAST, '语音收入自此不再单列')
              : undefined },
        { name: '短信及彩信收入', type: 'line', symbolSize: 7, lineStyle: { width: 2.5 },
          itemStyle: { color: ERA_COLORS.sms }, connectNulls: false,
          data: pick(AN, Y, 'smsRevenue', toYi) },
        { name: '无线上网业务收入', type: 'line', symbolSize: 8, lineStyle: { width: 3.5 },
          itemStyle: { color: ERA_COLORS.data }, connectNulls: false,
          data: pick(AN, Y, 'dataRevenue', toYi) },
        { name: '有线宽带业务收入', type: 'line', symbolSize: 7, lineStyle: { width: 2.5 },
          itemStyle: { color: ERA_COLORS.broadband }, connectNulls: false,
          data: pick(AN, Y, 'broadbandRevenue', toYi) },
        { name: '应用及信息服务收入', type: 'line', symbolSize: 7, lineStyle: { width: 2.5 },
          itemStyle: { color: ERA_COLORS.appInfo }, connectNulls: false,
          data: pick(AN, Y, 'appInfoRevenue', toYi) }
    ];
    /* 产品世代的关键年份用竖虚线标出来，读者不必记时间点 */
    var evs = (PROF.eraMarks || []).filter(function (e) { return Y.indexOf(String(e.year)) >= 0; });
    if (evs.length) o.series[0].markLine = eventMark(evs);
    return o;
});

/* ==== ARPU 与客户数 ==== */
mount('chart-arpu', function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].arpu != null || OP[y].mobileSubs != null);
    }).sort();
    var o = axisBase({ x: xs, left: 88, right: 104 });
    o.yAxis = [valueAxis('元/户/月', { min: 0 }),
               valueAxis('亿户', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
        { name: '移动客户数（亿户）', type: 'bar', yAxisIndex: 1, barWidth: '54%',
          itemStyle: { color: shade(NAVY, 0.62) }, data: pick(OP, xs, 'mobileSubs') },
        { name: '移动 ARPU（元/户/月）', type: 'line', symbolSize: 8, lineStyle: { width: 3.5 },
          itemStyle: { color: NAVY }, connectNulls: false, data: pick(OP, xs, 'arpu') },
        { name: '家庭客户综合 ARPU（元/户/月）', type: 'line', symbolSize: 7, lineStyle: { width: 2.5 },
          itemStyle: { color: ERA_COLORS.broadband }, connectNulls: false, data: pick(OP, xs, 'homeArpu') }
    ];
    return o;
});

/* ==== 产品世代时间线：按 era 分组渲染 profile.milestones ==== */
(function () {
    var ERA_ORDER = [
        { key: '语音',  color: ERA_COLORS.voice },
        { key: '短信',  color: ERA_COLORS.sms },
        { key: '数据',  color: shade(ERA_COLORS.data, 0.25) },
        { key: '流量',  color: ERA_COLORS.data },
        { key: '宽带',  color: ERA_COLORS.broadband },
        { key: '5G',    color: '#c0392b' },
        { key: '算力',  color: ERA_COLORS.appInfo },
        { key: 'AI',    color: '#8e44ad' },
        { key: '资本',  color: MUTED }
    ];
    var ms = PROF.milestones || [];
    if (!ms.length) { setHTML('era-line', '<p class="note">数据源中暂无里程碑记录。</p>'); return; }
    var html = ERA_ORDER.map(function (e) {
        var rows = ms.filter(function (m) { return (m.era || '').indexOf(e.key) >= 0; })
                     .sort(function (a, b) { return a.year - b.year; });
        if (!rows.length) return '';
        return '<div class="era-row">'
            + '<div class="era-tag" style="background:' + e.color + '">' + e.key + '</div>'
            + '<div class="era-body">' + rows.map(function (m) {
                return '<div><span class="yr">' + m.year + (m.month ? '.' + m.month : '') + '</span>'
                    + '<b>' + m.title + '</b>' + (m.detail ? '　' + m.detail : '') + '</div>';
            }).join('') + '</div></div>';
    }).join('');
    /* 没归到上面任何世代的条目单列一组，免得数据里新增 era 就悄悄丢掉 */
    var known = ERA_ORDER.map(function (e) { return e.key; });
    var rest = ms.filter(function (m) {
        return !known.some(function (k) { return (m.era || '').indexOf(k) >= 0; });
    }).sort(function (a, b) { return a.year - b.year; });
    if (rest.length) {
        html += '<div class="era-row"><div class="era-tag" style="background:#94a3b8">其他</div>'
            + '<div class="era-body">' + rest.map(function (m) {
                return '<div><span class="yr">' + m.year + (m.month ? '.' + m.month : '') + '</span>'
                    + '<b>' + m.title + '</b>' + (m.detail ? '　' + m.detail : '') + '</div>';
            }).join('') + '</div></div>';
    }
    setHTML('era-line', html);
})();

/* ==== 明细表：产品线收入 + 用量，一年一列（近十二年） ==== */
(function () {
    var TY = Y.slice(-12);
    setHTML('tbl-head', '<th>指标</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
    var ROWS = [
        { label: '收入拆分分母（主营业务收入）', field: '_mixBase', src: AN, total: true },
        { label: '　语音（通话费）', field: 'voiceRevenue', src: AN, sub: true },
        { label: '　月租费', field: 'monthlyFee', src: AN, sub: true },
        { label: '　短信及彩信', field: 'smsRevenue', src: AN, sub: true },
        { label: '　增值业务（旧口径合计）', field: 'vasRevenue', src: AN, sub: true },
        { label: '　数据业务（合计口径）', field: 'dataBusinessRevenue', src: AN, sub: true },
        { label: '　无线上网', field: 'dataRevenue', src: AN, sub: true },
        { label: '　有线宽带', field: 'broadbandRevenue', src: AN, sub: true },
        { label: '　应用及信息服务', field: 'appInfoRevenue', src: AN, sub: true },
        { label: '　未单列（现算）', field: '_residual', src: AN, sub: true },
        { label: 'MOU（分钟/户/月）', field: 'mou', src: OP, dec: 0 },
        { label: 'DOU（GB/户/月）', field: 'dou', src: OP, dec: 1 },
        { label: '移动 ARPU（元/户/月）', field: 'arpu', src: OP, dec: 1 },
        { label: '移动客户数（亿户）', field: 'mobileSubs', src: OP, dec: 2 }
    ];
    renderRows('tbl-body', ROWS.map(function (r) {
        return {
            _th: true,
            _cls: r.total ? 'row-total' : (r.sub ? 'row-sub' : ''),
            cells: [r.label].concat(TY.map(function (y) {
                var v;
                if (r.field === '_residual') v = residual(y);
                else if (r.field === '_mixBase') v = mixBase(y);
                else v = r.src[y] ? r.src[y][r.field] : null;
                if (v === null || v === undefined) return '—';
                return r.dec !== undefined ? fx(v, r.dec) : thou(v);
            }))
        };
    }));
})();

/* ==== 说明文字：全部由数据现算 ==== */
(function () {
    var vY = years(AN, 'voiceRevenue'), dY = years(AN, 'dataRevenue');
    var bY = years(AN, 'broadbandRevenue'), aY = years(AN, 'appInfoRevenue');
    var mouY = years(OP, 'mou'), douY = years(OP, 'dou');

    function peakYear(field, dict) {
        var ys = years(dict, field);
        if (!ys.length) return null;
        return ys.reduce(function (a, y) { return dict[y][field] > dict[a][field] ? y : a; }, ys[0]);
    }

    var mouPeak = peakYear('mou', OP), dataPeak = peakYear('dataRevenue', AN);

    setHTML('thesis-note',
        '<b>这一页要看的是柱子里颜色的更替，不是柱子的高度。</b>'
        + (vY.length && dY.length
            ? '语音业务收入 ' + vY[0] + '–' + vY[vY.length - 1] + ' 年有单列披露，'
              + '无线上网业务收入自 ' + dY[0] + ' 年起单列；两条序列在 '
              + (Math.max(+vY[0], +dY[0]) <= Math.min(+vY[vY.length - 1], +dY[dY.length - 1])
                 ? Math.max(+vY[0], +dY[0]) + '–' + Math.min(+vY[vY.length - 1], +dY[dY.length - 1]) + ' 年重叠，'
                   + '正好覆盖「流量替代通话」发生的那几年。'
                 : '披露期没有重叠，替代过程只能靠占比与用量指标推断。')
            : '')
        + (mouPeak && douY.length
            ? ' 用量侧更直白：MOU 在 ' + mouPeak + ' 年见顶（' + fx(OP[mouPeak].mou, 0) + ' 分钟/户/月），'
              + '此后逐年下行；DOU 从 ' + douY[0] + ' 年的 ' + fx(OP[douY[0]].dou, 1) + ' GB 涨到 '
              + douY[douY.length - 1] + ' 年的 ' + fx(OP[douY[douY.length - 1]].dou, 1) + ' GB。'
            : ''));

    setHTML('mix-note',
        '灰斜线那一层是「当年主营业务收入 − 已单列的各产品线」，<b>它厚的年份说明公司当年披露得粗，'
        + '不是这部分收入不存在</b>。这样处理之后每根柱子的总高度都等于当年主营业务收入，'
        + '不会出现「某几年柱子突然矮一截」的假断点。'
        + (aY.length ? '「应用及信息服务」自 ' + aY[0] + ' 年起单列，是算力（IDC/云）与智能（AI、数智文化）'
            + '两块新业务的主要落点；' : '')
        + (META.definitions && META.definitions.serviceRevenueBasis2025
            ? '<b>2025 年起口径又换了一次：</b>' + META.definitions.serviceRevenueBasis2025 : ''));

    setHTML('mix-share-note',
        '占比图去掉了规模的干扰，只看结构。'
        + (dY.length && dataPeak
            ? '无线上网收入占主营业务收入的比重在 ' + dataPeak + ' 年前后见顶（当年 '
              + yiTxt(AN[dataPeak].dataRevenue) + '，占 '
              + (AN[dataPeak].serviceRevenue
                 ? pct(AN[dataPeak].dataRevenue / AN[dataPeak].serviceRevenue * 100) : '—')
              + '），此后<b>流量本身也从增长引擎变成了守存量的业务</b>——'
              + '接棒的是有线宽带与应用及信息服务。'
            : ''));

    setHTML('scissors-note',
        '<b>这张图是「流量替代通话」最直接的证据。</b>MOU 与 DOU 不是同一个量纲，同轴只是为了看方向：'
        + '一条在降、一条在涨。注意 DOU 的序列起点晚——'
        + (douY.length ? douY[0] + ' 年之前公司并未把户均流量作为主要运营指标披露，' : '')
        + '这个「起点差」本身就说明了产品重心是什么时候转过去的。'
        + (OMETA.definitions && OMETA.definitions.douBasis ? '口径：' + OMETA.definitions.douBasis : ''));

    setHTML('substitute-note',
        (function () {
            /* 交叉年：无线上网收入首次超过语音收入 */
            var cross = null;
            Y.forEach(function (y) {
                var r = AN[y] || {};
                if (cross === null && r.voiceRevenue != null && r.dataRevenue != null
                    && r.dataRevenue > r.voiceRevenue) cross = y;
            });
            var txt = cross
                ? '<b>' + cross + ' 年是收入端的交叉点</b>：这一年无线上网收入（'
                  + yiTxt(AN[cross].dataRevenue) + '）第一次超过语音收入（'
                  + yiTxt(AN[cross].voiceRevenue) + '），此后语音再没回来过。'
                : '';
            txt += (vY.length
                ? '语音这条线没有断点——' + vY[0] + '–' + vY[vY.length - 1]
                  + ' 年每年都有数，但<b>披露的位置换了</b>：2022 年起年报正文不再把语音单列，'
                  + '数字只留在收入分解附注里。产品退场的最后一步往往是「从正文里消失」，'
                  + '这比收入下滑更能说明公司已经不拿它当主线讲了。'
                : '');
            txt += (bY.length ? ' 有线宽带自 ' + bY[0] + ' 年起单列，' : '');
            txt += (aY.length ? '应用及信息服务自 ' + aY[0] + ' 年起单列。' : '');
            txt += '读这张图时把它和上面的占比图对着看：绝对额还在涨的产品，占比可能已经在退。';
            return txt;
        })());

    setHTML('arpu-note',
        '<b>ARPU 与客户数是一对反向的力。</b>客户数见顶之后，收入只能靠 ARPU；'
        + '而 ARPU 在流量单价长期下行的背景下很难往上走——'
        + (years(OP, 'arpu').length
            ? '本页数据里移动 ARPU 从 ' + fx(OP[years(OP, 'arpu')[0]].arpu, 1) + ' 元降到 '
              + fx(OP[years(OP, 'arpu')[years(OP, 'arpu').length - 1]].arpu, 1) + ' 元。'
            : '')
        + '这正是公司把重心挪到家庭（宽带+智慧家庭）、政企（算力+行业应用）的原因：'
        + '<b>个人市场的户均收入撑不住增长，就得换一个「户」的定义。</b>');

    /* 口径缺口清单：字段覆盖区间现算 + 数据源里的原文说明 */
    var GF = [
        ['voiceRevenue', '语音业务收入'],
        ['smsRevenue', '短信及彩信收入'],
        ['vasRevenue', '增值业务收入（旧口径）'],
        ['dataRevenue', '无线上网业务收入'],
        ['broadbandRevenue', '有线宽带业务收入'],
        ['appInfoRevenue', '应用及信息服务收入']
    ];
    var items = GF.map(function (p) {
        var ys = years(AN, p[0]);
        if (!ys.length) return '<b>' + p[1] + '</b>：数据源中无任何年份单列披露。';
        var missing = Y.filter(function (y) {
            return +y > +ys[0] && +y < +ys[ys.length - 1] && AN[y][p[0]] == null;
        });
        return '<b>' + p[1] + '</b>：单列披露 ' + ys[0] + '–' + ys[ys.length - 1]
            + '（' + ys.length + ' 年）'
            + (+ys[ys.length - 1] < +LAST ? '，' + (+ys[ys.length - 1] + 1) + ' 年起不再单列' : '')
            + (missing.length ? '，区间内缺 ' + missing.join('、') : '') + '。';
    });
    ['mou', 'dou', 'arpu', 'homeArpu'].forEach(function (f) {
        var ys = years(OP, f);
        items.push('<b>' + f.toUpperCase() + '</b>：'
            + (ys.length ? '披露 ' + ys[0] + '–' + ys[ys.length - 1] + '（' + ys.length + ' 年）。'
                         : '数据源中无披露。'));
    });
    [META.gaps, OMETA.gaps, META.definitions, OMETA.definitions].forEach(function (obj) {
        if (!obj) return;
        Object.keys(obj).forEach(function (k) { items.push('<b>' + k + '</b>：' + obj[k]); });
    });
    renderList('gaps-list', items);
})();
