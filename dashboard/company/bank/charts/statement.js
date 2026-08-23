/* 报表：分部信息与地域分布、资产负债表趋势与结构、现金流。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {

/* ────── 6. 分部信息 ────── */
(function () {
    const segs = D['seg-rev'].segs;
    const rev25 = D['seg-rev'].rev25;
    const rev24 = D['seg-rev'].rev24;
    initChart('chart-seg-rev')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 } },
        legend: { data: ['2025', '2024'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: segs, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '百万元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025', type: 'bar', data: rev25, itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 18, formatter: p => (p.value/1000).toFixed(1)+'亿' } },
            { name: '2024', type: 'bar', data: rev24, itemStyle: { color: '#b39ddb' } }
        ]
    });

    // 地域：存贷款占比
    initChart('chart-geo')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: ['县域', '主城'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 36, bottom: 50 },
        xAxis: { type: 'category', data: D['geo'].cats, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', max: 100, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '县域', type: 'bar', stack: 'geo', data: D['geo'].county, itemStyle: { color: '#1e8449' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } },
            { name: '主城', type: 'bar', stack: 'geo', data: D['geo'].urban, itemStyle: { color: '#e67e22' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } }
        ]
    });
})();
});

__section(function (D, SELF, notes) {

/* ────── 5-① 资产负债表历年趋势（2010–2025，CAS 口径，balance-sheet.html） ────── */
(function () {
    const years = D['bs-trend'].years;
    // 资产总额 / 负债总额 / 股东权益合计（百万元），中国企业会计准则(CAS)合并口径期末数
    // 2010-2018 取自 H 股 03618 历年年报「合并财务状况表」；2019-2025 取自 A 股 601077 历年年报「合并资产负债表」
    // 均已与本行历年年报正式报表逐年交叉核对一致，2026-08-15 提取核对
    const assets = D['bs-trend'].assets;
    const liab   = D['bs-trend'].liab;
    const equity = D['bs-trend'].equity;
    initChart('chart-bs-trend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue} 年</b>`;
                p.forEach(x => { s += `<br>${x.marker}${x.seriesName}：${x.value.toLocaleString()} 百万元`; });
                return s;
            } },
        legend: { data: ['资产总额', '负债总额', '股东权益合计'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 88, right: 24, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        // 单一 Y 轴：权益与资产/负债共用同一刻度，如实呈现「银行权益仅占资产 6~10%」的结构
        // （原来把权益放右轴独立缩放，会让权益线看着与资产/负债一样高，误导量级——见 ⑥ 整改 H1）
        yAxis: { type: 'value', name: '百万元', min: 0, nameTextStyle: { fontSize: 16, color: '#555' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: v => (v/10000).toFixed(0) + '万' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '资产总额', type: 'line', data: assets, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '负债总额', type: 'line', data: liab, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '股东权益合计', type: 'line', data: equity, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } }
        ]
    });
})();

/* ────── 5-② 资产负债表结构 (2025) ────── */
(function () {
    const assets = D['bs'].assets;
    const claims = D['bs'].claims;
    const CAT = ['资产', '负债 + 权益'];
    const total = assets.reduce((s, it) => s + it.value, 0);
    const mk = (items, col) => items.map(it => ({
        name: it.name, type: 'bar', stack: 'bs', barMaxWidth: 160,
        emphasis: { focus: 'series' },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 18,
                 formatter: p => (p.value/total*100) < 4 ? '' : it.name },
        data: CAT.map((_, i) => i === col ? it.value : '-')
    }));
    initChart('chart-bs')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            valueFormatter: v => (v === '-' || v == null) ? '' : Number(v).toLocaleString() },
        legend: { type: 'scroll', bottom: 2, textStyle: { fontSize: 18 }, itemWidth: 14, itemHeight: 12 },
        grid: { left: 76, right: 30, top: 26, bottom: 54 },
        xAxis: { type: 'category', data: CAT, axisLabel: { fontSize: 18, fontWeight: 600, color: '#333' } },
        yAxis: { type: 'value', axisLabel: { fontSize: 18, formatter: v => (v/10000).toFixed(0) + '万', color: '#555' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        color: ['#8e44ad','#9b59b6','#af7ac5','#c39bd3','#d7bde2','#ebdef0','#e74c3c','#ec7063','#27ae60','#7dcea0'],
        series: [...mk(assets, 0), ...mk(claims, 1)]
    });
})();

/* ────── 5-③ 现金流量（2025 分季度经营净额） ────── */
(function () {
    initChart('chart-cf')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', valueFormatter: v => Number(v).toLocaleString(), textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 24, top: 26, bottom: 36 },
        xAxis: { type: 'category', data: ['Q1','Q2','Q3','Q4'],
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [{ type: 'bar', data: D['cf'].vals, barWidth: '48%',
            itemStyle: { color: p => p.value >= 0 ? '#8e44ad' : '#e74c3c', borderRadius: [4,4,0,0] },
            label: { show: true, position: 'top', fontSize: 18,
                     formatter: p => Number(p.value).toLocaleString() } }]
    });
})();
});
