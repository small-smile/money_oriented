/* 资产端：金融投资三分类与公允价值、贷款结构与投向。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 1k. 金融投资分类结构 AC / FVOCI / FVTPL ────── */
(function () {
    const years = D['invest'].years;
    const ac        = D['invest'].ac;
    const fvociDebt = D['invest'].fvociDebt;
    const fvociEq   = D['invest'].fvociEq;
    const fvtpl     = D['invest'].fvtpl;

    initChart('chart-invest')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   valueFormatter: v => v + ' 亿' },
        legend: { data: ['债权投资(AC/摊余成本)', '其他债权投资(FVOCI债)', '其他权益工具(FVOCI股)', '交易性金融资产(FVTPL)'],
                  bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '债权投资(AC/摊余成本)', type: 'bar', stack: 'inv', data: ac, itemStyle: { color: '#2980b9' } },
            { name: '其他债权投资(FVOCI债)', type: 'bar', stack: 'inv', data: fvociDebt, itemStyle: { color: '#16a085' } },
            { name: '其他权益工具(FVOCI股)', type: 'bar', stack: 'inv', data: fvociEq, itemStyle: { color: '#f39c12' } },
            { name: '交易性金融资产(FVTPL)', type: 'bar', stack: 'inv', data: fvtpl, itemStyle: { color: '#c0392b' } }
        ]
    });
})();

/* ────── 1k-2. FVTPL 内部构成（本集团, 亿元, 2025 vs 2024） ────── */
(function () {
    // 2025年报附注「金融投资(1) 交易性金融资产」(第55页), 千元 → 亿元
    const cats  = D['fvtpl-mix'].cats;
    const y2025 = D['fvtpl-mix'].y2025;
    const y2024 = D['fvtpl-mix'].y2024;

    initChart('chart-fvtpl-mix')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   valueFormatter: v => v + ' 亿' },
        legend: { data: ['2025 年末', '2024 年末'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 116, right: 84, top: 20, bottom: 48 },
        xAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: cats, axisLabel: { fontSize: 18, color: '#555' } },
        series: [
            { name: '2025 年末', type: 'bar', data: y2025, itemStyle: { color: '#c0392b' },
              label: { show: true, position: 'right', fontSize: 18, color: '#c0392b' } },
            { name: '2024 年末', type: 'bar', data: y2024, itemStyle: { color: '#e8a49c' } }
        ]
    });
})();

/* ────── 1k-3. 公允价值计量层级 L1/L2/L3（本集团, 亿元） ────── */
(function () {
    // 2025年报附注「公允价值层次」(第139页), 千元 → 亿元
    const years = D['fvlevel'].years;
    const l1  = D['fvlevel'].l1;
    const l2  = D['fvlevel'].l2;
    const l3  = D['fvlevel'].l3;
    const tot = D['fvlevel'].tot;

    initChart('chart-fvlevel')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: {
            trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex;
                return p[0].name + '　合计 ' + tot[i].toFixed(2) + ' 亿<br>' + p.map(s =>
                    s.marker + s.seriesName + '：<b>' + s.value.toFixed(2) + ' 亿</b>（' +
                    (s.value / tot[i] * 100).toFixed(1) + '%）').join('<br>');
            }
        },
        legend: { data: ['第一层次 L1', '第二层次 L2', '第三层次 L3'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 84, right: 30, top: 30, bottom: 48 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '第一层次 L1', type: 'bar', stack: 'fv', barWidth: '46%', data: l1,
              itemStyle: { color: '#2980b9' } },
            { name: '第二层次 L2', type: 'bar', stack: 'fv', data: l2, itemStyle: { color: '#16a085' } },
            { name: '第三层次 L3', type: 'bar', stack: 'fv', data: l3, itemStyle: { color: '#f39c12' },
              label: { show: true, position: 'top', fontSize: 18, color: '#555',
                       formatter: p => '合计 ' + tot[p.dataIndex].toFixed(0) + ' 亿' } }
        ]
    });
})();

});

__section(function (D, SELF, notes) {
/* ────── 1c. 公司/个人 存贷款结构与利率 ────── */
(function () {
    const years = D['loanmix-bal'].years;
    // 公司贷款 / 零售贷款 / 票据贴现 / 合计 平均余额（亿元），取自各年年报「利息收入分析」表
    const balCorp = D['loanmix-bal'].balCorp;
    const balRetail = D['loanmix-bal'].balRetail;
    const balBill = D['loanmix-bal'].balBill;
    const balTotal = D['loanmix-bal'].balTotal;
    // 同表平均收益率（%）
    const yldCorp = D['loanmix-bal'].yldCorp;
    const yldRetail = D['loanmix-bal'].yldRetail;
    const yldBill = D['loanmix-bal'].yldBill;
    const yldTotal = D['loanmix-bal'].yldTotal;
    const loanMixNames = ['公司贷款', '个人(零售)贷款', '票据贴现', '客户贷款合计'];
    const loanMixColors = ['#6c3483', '#2980b9', '#16a085', '#c0392b'];
    const loanMixLine = (name, data, color, unit, dy) => ({
        name, type: 'line', data, symbolSize: name === '客户贷款合计' ? 7 : 6,
        lineStyle: { width: name === '客户贷款合计' ? 3 : 2, color }, itemStyle: { color },
        endLabel: { show: true, fontSize: 18, color, offset: [0, dy || 0],
                    formatter: p => p.value + unit }
    });

    initChart('chart-loanmix-bal')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 亿' },
        legend: { data: loanMixNames, bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 128, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [balCorp, balRetail, balBill, balTotal].map(
            (d, i) => loanMixLine(loanMixNames[i], d, loanMixColors[i], ' 亿'))
    });

    initChart('chart-loanmix-yld')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: loanMixNames, bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 128, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '平均收益率%', min: 0, max: 6, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [yldCorp, yldRetail, yldBill, yldTotal].map(
            // 2025 年三条线收于 3.64%–3.87%，端点标签手动错开纵向位置避免相互压盖
            (d, i) => loanMixLine(loanMixNames[i], d, loanMixColors[i], '%', [-14, 8, 0, 28][i]))
    });

    // 存款期限结构：活期 vs 定期 占比（2025 年末）
    (function () {
        // 样式沿用全站统一的 PIE_BASE / PIE_LABEL（基准是股东页 A+H 合并图）：圆心不写字、
        // 不另配 legend，名称与占比都在边缘对齐的标注里；value 是亿元绝对值，故比例取 p.percent
        initChart('chart-depterm')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', formatter: '{b}: {c} 亿元 ({d}%)', textStyle: { fontSize: 18 } },
        series: pieSeries({
            name: '存款期限结构',
            data: [
                { value: D['depterm'].vals[0], name: '定期存款', itemStyle: { color: '#6c3483' } },
                { value: D['depterm'].vals[1], name: '活期存款', itemStyle: { color: '#e67e22' } },
                { value: D['depterm'].vals[2],   name: '保证金及其他', itemStyle: { color: '#b0a0bd' } }
            ]
        }, PIE_LABEL_PCT)
    });
    })();
})();

});

__section(function (D, SELF, notes) {
/* ────── 1d2. 公司贷款 / 零售贷款期末余额（2012–2025） ────── */
(function () {
    const years = D['loantrend'].years;
    // 期末余额（亿元）——按产品类型划分的贷款及不良贷款分布情况 / 客户贷款和垫款的构成情况
    const corp   = D['loantrend'].corp;
    const retail = D['loantrend'].retail;
    // 公司 / 零售贷款和垫款不良率（%）——同表「公司贷款和垫款」「个人（零售）贷款和垫款」两行；
    // 零售不良率有的年份未披露（只给余额不给分类不良），缺口留 null、线段断开
    const nplCorp   = D['loantrend'].nplCorp;
    const nplRetail = D['loantrend'].nplRetail;
    initChart('chart-loantrend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   formatter: ps => ps[0].axisValue + '<br>' + ps.map(p =>
                       `${p.marker}${p.seriesName}：${p.value == null ? '未披露'
                         : p.value + (p.seriesName.endsWith('不良率') ? '%' : ' 亿元')}`).join('<br>') },
        legend: { data: ['公司贷款', '零售贷款', '公司贷款不良率', '零售贷款不良率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 60, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
            // 右轴同时承载公司/零售两条不良率，轴名与刻度改中性灰，不再跟其中一条同色
            { type: 'value', name: '不良率%', min: 0, position: 'right', nameTextStyle: { color: '#555', fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#555' }, splitLine: { show: false } }
        ],
        series: [
            { name: '公司贷款', type: 'line', data: corp, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '零售贷款', type: 'line', data: retail, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } },
            { name: '公司贷款不良率', type: 'line', yAxisIndex: 1, data: nplCorp, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#c0392b', type: 'dashed' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
            { name: '零售贷款不良率', type: 'line', yAxisIndex: 1, data: nplRetail, smooth: true, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}%' } }
        ]
    });
})();

/* ────── 1d. 个人贷款按用途细分（2018–2025） ────── */
(function () {
    const years = D['perloan-bal'].years;
    // 期末余额（亿元）——按揭 / 经营 / 信用卡 全区间；消费贷 2018–2022 未单独披露
    const balMortgage = D['perloan-bal'].balMortgage;
    const balBusiness = D['perloan-bal'].balBusiness;
    const balCard     = D['perloan-bal'].balCard;
    const balConsume  = D['perloan-bal'].balConsume;

    initChart('chart-perloan-bal')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '未披露' : v + ' 亿', textStyle: { fontSize: 18 } },
        legend: { data: ['住房按揭', '个人经营', '信用卡', '个人消费'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 66, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '住房按揭', type: 'line', data: balMortgage, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' } },
            { name: '个人经营', type: 'line', data: balBusiness, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '信用卡', type: 'line', data: balCard, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' } },
            { name: '个人消费', type: 'line', data: balConsume, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#1e8449', type: 'dashed' }, itemStyle: { color: '#1e8449' } }
        ]
    });

    // 不良率（%）——按揭 / 经营 / 其他（其他口径 2018–2022 vs 2023–2025 不同，见说明）
    const nplMortgage = D['perloan-bal'].nplMortgage;
    const nplBusiness = D['perloan-bal'].nplBusiness;
    const nplOthers   = D['perloan-bal'].nplOthers;

    // 分产品余额有披露、但分产品不良率整份缺失（多数农商行不单列各产品不良率）：三条线全空时
    // 别留一张只有坐标轴、没有线的空图（同 ⑥ H3 口径），改贴「该行暂无此项数据」占位。
    const __nplHasData = [nplMortgage, nplBusiness, nplOthers].some(
        a => Array.isArray(a) && a.some(v => v != null));
    if (!__nplHasData) {
        __stub('chart-perloan-npl');
    } else {
    initChart('chart-perloan-npl')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '缺口' : v + '%', textStyle: { fontSize: 18 } },
        legend: { data: ['住房按揭', '个人经营', '其他（含消费/信用卡）'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '住房按揭', type: 'line', data: nplMortgage, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              label: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}%' } },
            { name: '个人经营', type: 'line', data: nplBusiness, smooth: true, connectNulls: true, symbolSize: 7,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
            { name: '其他（含消费/信用卡）', type: 'line', data: nplOthers, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#7f8c8d', type: 'dashed' }, itemStyle: { color: '#7f8c8d' } }
        ]
    });
    }
})();

});

__section(function (D, SELF, notes) {

/* ────── 7. 贷款行业分布 ────── */
(function () {
    const inds = D['loan-industry'].inds;
    const bal25 = D['loan-industry'].bal25;
    const bal24 = D['loan-industry'].bal24;
    initChart('chart-loan-industry')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            valueFormatter: v => v == null ? '' : (v/10000).toFixed(1) + ' 万亿' },
        legend: { data: ['2025 余额', '2024 余额'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 90, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: inds, axisLabel: { fontSize: 18, color: '#555', rotate: 30 } },
        yAxis: { type: 'value', name: '百万元', nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025 余额', type: 'bar', data: bal25, itemStyle: { color: '#6c3483' } },
            { name: '2024 余额', type: 'bar', data: bal24, itemStyle: { color: '#b39ddb' } }
        ]
    });
})();
});
