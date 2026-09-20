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

/* ────── 5-② 资产负债表结构 (2025)：拆成两个瀑布 —— 资产结构 / 负债+权益结构 ──────
 * 各科目按百万元逐段累加（此处 ÷100 换成亿元）成瀑布：资产各类 → 总资产；负债各类(红)+权益(绿) → 总负债+权益，
 * 两侧合计相等（＝总资产）。透明底柱 + 可见柱实现瀑布（底柱 silent、不触发 tooltip/高亮）。 */
(function () {
    const assets = D['bs'].assets;
    const claims = D['bs'].claims;
    const fmt = vy => Math.round(vy).toLocaleString('zh-CN');
    function drawWF(id, items, totalName, colorOf) {
        const cats = [], base = [], vals = [], labels = [], colors = [];
        let acc = 0;
        items.forEach(it => {
            const v = it.value / 100;               // 百万元 → 亿元
            cats.push(it.name); base.push(acc); vals.push(v);
            labels.push(fmt(v)); colors.push(colorOf(it)); acc += v;
        });
        cats.push(totalName); base.push(0); vals.push(acc); labels.push(fmt(acc)); colors.push('#2c3e50');
        const many = cats.length > 5;
        initChart(id)?.setOption({
            backgroundColor: '#fff', textStyle: { fontSize: 18 },
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
                formatter: p => `${p.name}<br/>${labels[p.dataIndex]} 亿元` },
            grid: { left: 76, right: 30, top: 24, bottom: many ? 92 : 54 },
            xAxis: { type: 'category', data: cats,
                     axisLabel: { fontSize: 14, color: '#555', interval: 0, rotate: many ? 24 : 0 } },
            yAxis: { type: 'value', name: '亿元', nameTextStyle: { fontSize: 14, color: '#555' },
                     axisLabel: { fontSize: 14, color: '#555', formatter: v => Number(v).toLocaleString() },
                     splitLine: { lineStyle: { color: '#eee' } } },
            series: [
                { type: 'bar', stack: 'wf', silent: true, itemStyle: { color: 'transparent' },
                  emphasis: { disabled: true }, data: base },
                { type: 'bar', stack: 'wf', barMaxWidth: 70,
                  data: vals.map((v, k) => ({ value: v, itemStyle: { color: colors[k] } })),
                  label: { show: true, position: 'top', color: '#333', fontSize: 14,
                           formatter: p => labels[p.dataIndex] } }
            ]
        });
    }
    drawWF('chart-bs', assets, '总资产', () => '#1f4e79');
    drawWF('chart-bs-claims', claims, '总负债 + 权益', it => /权益/.test(it.name) ? '#1e8449' : '#c0392b');
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
