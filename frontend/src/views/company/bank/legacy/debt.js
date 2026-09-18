/* 负债端：存款付息率与活期占比、已发行债务证券、利率重定价缺口。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 1c-2. 客户存款平均付息率 与 活期存款占比（历年 2019–2025） ────── */
(function () {
    const years = D['depcost'].years;
    // 全行客户存款合计平均付息率（%），取自历年年报「客户存款合计」表
    const cost  = D['depcost'].cost;
    // 活期存款占客户存款总额比重（%）= 公司活期 + 个人活期（期末）
    const demand = D['depcost'].demand;
    // 付息率轴范围随各行数据自适应（原写死 min1.3/max2.1 会裁掉招行1.17、民生2.36 等点）
    const cVals = cost.filter(v => v != null);
    const cMin = Math.floor((Math.min(...cVals) - 0.1) * 10) / 10;
    const cMax = Math.ceil((Math.max(...cVals) + 0.1) * 10) / 10;

    initChart('chart-depcost')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   valueFormatter: v => v + '%' },
        grid: { left: 60, right: 66, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '付息率%', min: cMin, max: cMax,
                 nameTextStyle: { fontSize: 18, color: '#c0392b' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [{
            name: '客户存款平均付息率', type: 'line', data: cost, smooth: true, symbolSize: 7, z: 3,
            lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
            label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%', position: 'top' }
        }]
    });

    initChart('chart-demandratio')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   valueFormatter: v => v + '%' },
        grid: { left: 60, right: 66, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '活期占比%', min: 0,
                 nameTextStyle: { fontSize: 18, color: '#6c3483' },
                 axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [{
            name: '活期存款占比', type: 'line', data: demand, smooth: true, symbolSize: 7, z: 3,
            lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
            areaStyle: { color: 'rgba(108,52,131,0.10)' },
            label: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}%', position: 'top' }
        }]
    });
})();

/* ────── 1c-3. 已发行债务证券：期末余额、平均成本率、逐笔票面利率（2018–2025） ──────
 * 数据来自年报「应付债券」附注（按类别期末余额、逐笔发行条款）与「利息支出——已发行债务证券」
 * 表（平均余额 / 平均成本率）。同业存单发行流量比债券大两个数量级，故不画发行额，只画余额与成本率。 */
(function () {
    const B = D['bondpay'] || EMPTY_D;
    const years = B.years || [];

    /* 期末余额（亿元）：同业存单 + 应付债券堆叠，叠加平均余额合计（同量级，可同轴）。
     * 不少中小行只把「应付债券」当一个整体披露（内含同业存单），此时只有 balTotal，画一根合计柱。 */
    (function () {
        if (!document.getElementById('chart-bond-bal')) return;
        const balNcd = B.balNcd || [], balBond = B.balBond || [], avgTotal = B.avgTotal || [];
        const split = balNcd.some(v => v != null) || balBond.some(v => v != null);
        const balTotal = split ? [] : (B.balTotal || []);
        if (!split && !balTotal.some(v => v != null)) { __stub('chart-bond-bal'); return; }
        const tot = years.map((_, i) => split ? (balNcd[i] || 0) + (balBond[i] || 0) : (balTotal[i] || 0));
        // 存单压降到很小时柱内白字会压出柱外（无锡银行 2024/2025），矮于合计 9% 就不标，数值看 tooltip
        const thin = Math.max.apply(null, tot.concat([0])) * 0.09;
        const bigOnly = p => (p.value != null && p.value >= thin) ? p.value : '';
        const ser = live([
            { name: '已发行同业存单', type: 'bar', stack: 'bal', data: balNcd,
              itemStyle: { color: '#6c3483' },
              label: { show: true, fontSize: 16, color: '#fff', formatter: bigOnly } },
            { name: '应付债券（金融债/二级资本债）', type: 'bar', stack: 'bal', data: balBond,
              itemStyle: { color: '#e67e22' } },
            { name: '已发行债务证券合计', type: 'bar', stack: 'bal', data: balTotal,
              itemStyle: { color: '#6c3483' } },
            { name: '平均余额合计', type: 'line', data: avgTotal, smooth: true, symbolSize: 7, z: 3,
              lineStyle: { width: 2.5, color: '#95a5a6', type: 'dashed' }, itemStyle: { color: '#95a5a6' } }
        ]);
        const legendNames = ser.map(s => s.name);
        // 合计数值挂在一根零高透明柱上，z 抬到虚线之上，平均余额线才不会从数字中间穿过（招行 2024/2025）
        ser.push({ name: '期末合计', type: 'bar', stack: 'bal', data: years.map(() => 0),
                   itemStyle: { color: 'transparent' }, z: 10, silent: true,
                   label: { show: true, fontSize: 16, color: '#555', position: 'top', distance: 5,
                            formatter: p => tot[p.dataIndex] ? tot[p.dataIndex].toFixed(2) : '' } });
        initChart('chart-bond-bal')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                       formatter: ps => ps[0].axisValue + ' 年<br>' + ps
                           .filter(p => p.seriesName !== '期末合计').map(p =>
                           `${p.marker}${p.seriesName}：${p.value == null ? '—' : p.value + ' 亿元'}`).join('<br>') +
                           (split ? '<br>期末合计：' + tot[ps[0].dataIndex].toFixed(2) + ' 亿元' : '') },
            legend: { bottom: 2, data: legendNames, textStyle: { fontSize: 18 } },
            grid: { left: 76, right: 30, top: 36, bottom: 52 },
            xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                     axisLabel: { fontSize: 18, color: '#555' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            series: ser
        });
    })();

    /* 平均成本率（%）：同业存单 / 应付债券 / 合计 */
    (function () {
        if (!document.getElementById('chart-bond-cost')) return;
        const rNcd = B.rateNcd || [], rBond = B.rateBond || [], rTot = B.rateTotal || [];
        if (![rNcd, rBond, rTot].some(a => a.some(v => v != null))) { __stub('chart-bond-cost'); return; }
        const ax = niceAxis([].concat(rNcd, rBond, rTot), 1);
        // 首末两点的数值标签会压到纵轴刻度／右边界上，改成贴着点向内排
        const totData = rTot.map((v, i) => (i === 0 || i === rTot.length - 1)
            ? { value: v, label: { align: i === 0 ? 'left' : 'right',
                                   position: i === 0 ? 'top' : 'bottom' } } : v);
        initChart('chart-bond-cost')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '—' : v + '%' },
            legend: { bottom: 2, textStyle: { fontSize: 18 } },
            grid: { left: 70, right: 66, top: 32, bottom: 52 },
            xAxis: { type: 'category', data: years, boundaryGap: false,
                     axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '成本率%', min: ax.min, max: ax.max, interval: ax.interval,
                     nameTextStyle: { fontSize: 18, color: '#c0392b' },
                     axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            series: live([
                { name: '合计', type: 'line', data: totData, smooth: true, symbolSize: 8, z: 4,
                  lineStyle: { width: 3.5, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
                  // 统一两位小数，3.4% 与 3.99% 混排容易看成不同口径
                  label: { show: true, fontSize: 18, color: '#c0392b', position: 'top',
                           formatter: p => p.value == null ? '' : p.value.toFixed(2) + '%' } },
                { name: '已发行同业存单', type: 'line', data: rNcd, smooth: true, symbolSize: 6,
                  lineStyle: { width: 2.5, color: '#6c3483' }, itemStyle: { color: '#6c3483' } },
                { name: '应付债券', type: 'line', data: rBond, smooth: true, symbolSize: 6,
                  lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' } }
            ])
        });
    })();

    /* 逐笔债券票面利率（横向条形，按发行日自上而下）。存续/已到期/已赎回用颜色区分 */
    (function () {
        const el = document.getElementById('chart-bond-list');
        if (!el) return;
        const bonds = (B.bonds || []).slice().sort((a, b) => (a.issueDate || '') < (b.issueDate || '') ? 1 : -1);
        if (!bonds.length) { __stub('chart-bond-list'); return; }
        // 各行发行笔数从 0 到 20 不等，图高按条数给（HTML 里的固定高度只是渝农商行的默认值）
        el.style.height = Math.max(320, bonds.length * 40 + 70) + 'px';
        const COLOR = { '存续': '#6c3483', '已到期': '#95a5a6', '已赎回': '#b0a0bd' };
        // 债券简称长短不一（可转债带一串累进票面），超长的截断，全称在 tooltip 里
        const cut = s => (s || '').length > 15 ? (s || '').slice(0, 15) + '…' : (s || '');
        const labels = bonds.map(b => (b.issueDate || '') + '\n' + cut(b.name));
        initChart('chart-bond-list')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
                       formatter: p => {
                           const b = bonds[p.dataIndex];
                           return `<b>${b.name}</b><br>发行日：${b.issueDate}<br>期限：${b.tenor || '—'}` +
                                  `<br>票面利率：${b.coupon == null ? '未披露' : b.coupon + '%'}` +
                                  `<br>发行额：${b.amount} 亿元` +
                                  `<br>到期：${b.maturity || '—'}（${b.status || '—'}）`;
                       } },
            grid: { left: 250, right: 130, top: 20, bottom: 40 },
            xAxis: { type: 'value', name: '票面利率%', min: 0, nameTextStyle: { fontSize: 18 },
                     axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                     splitLine: { lineStyle: { color: '#eee' } } },
            yAxis: { type: 'category', data: labels,
                     axisLabel: { fontSize: 15, color: '#555', lineHeight: 18, interval: 0 } },
            series: [{
                name: '票面利率', type: 'bar', barWidth: '62%',
                // 票面未披露的（如无锡银行 14 二级资本债）画成零长条，用标签写明，不然那一行是空白
                data: bonds.map(b => ({ value: b.coupon == null ? 0 : b.coupon,
                                        itemStyle: { color: COLOR[b.status] || '#95a5a6' } })),
                label: { show: true, position: 'right', fontSize: 16, color: '#555',
                         // 票面统一两位小数，不然 4% 和 4.65% 混排看起来像两种口径
                         formatter: p => (bonds[p.dataIndex].coupon == null ? '票面未披露' : p.value.toFixed(2) + '%') +
                                         '　' + bonds[p.dataIndex].amount + ' 亿' }
            }]
        });
    })();
})();

/* ────── 10b. 利率重定价缺口（按重定价期限，2025 vs 2024） ────── */
(function () {
    const el = document.getElementById('chart-repricing');
    if (!el) return;
    const buckets = D['repricing'].buckets;
    // 单位：亿元（年报为人民币百万元，÷100 换算）；负值＝负债敏感（重定价负债多于资产）
    const g2025 = D['repricing'].g2025;
    const g2024 = D['repricing'].g2024;
    echarts.init(el).setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
                   textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 亿' },
        legend: { data: ['2025', '2024'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 76, right: 24, top: 44, bottom: 40 },
        xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '缺口 亿元', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025', type: 'bar', data: g2025, barGap: '10%',
              itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 16, color: '#555',
                       position: p => p.value >= 0 ? 'top' : 'bottom', formatter: '{c}' } },
            { name: '2024', type: 'bar', data: g2024,
              itemStyle: { color: '#95a5a6' },
              label: { show: true, fontSize: 16, color: '#888',
                       position: p => p.value >= 0 ? 'top' : 'bottom', formatter: '{c}' } }
        ]
    });
})();

});
