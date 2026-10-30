/* 风控：盈利质量与信用减值、核销与收回、五级分类与迁徙率、到期结构、权益资产比。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 1e. 盈利质量与效率（2010–2025） ────── */
(function () {
    const years  = D['nim-trend'].years;
    // NIM/NIS：H 股 03618 历年年报「財務摘要—盈利能力指標」及本行 2010–2025 年年度报告披露值
    // 2018 年改用新准则（IFRS9）值 2.45/2.40（此前误取"經調整"IAS39 口径 2.65/2.44，与后续年份口径不一致）
    const nim  = D['nim-trend'].nim;
    const nis  = D['nim-trend'].nis;

    initChart('chart-nim-trend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['净息差 NIM', '净利差 NIS'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '净息差 NIM', type: 'line', data: nim, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '净利差 NIS', type: 'line', data: nis, smooth: true, connectNulls: true, symbolSize: 5,
              lineStyle: { width: 2, color: '#9b59b6', type: 'dashed' }, itemStyle: { color: '#9b59b6' } }
        ]
    });

    // 非息收入占比：2010–2018 由 H 股年报「淨利息收入佔營業收入總額」反算（100% − 该比率）；2019–2025 为本行年报「非利息净收入/营业收入」披露值
    // 2018 年为 H 股口径 23.29%，A 股 2019 年报比较列重述为 23.37%（此处衔接 2019 起的 A 股序列口径取 23.37%）
    const nonInt     = D['nim-trend'].nonInt;
    // 成本收入比：2010–2017 为 H 股年报「成本佔收入比率」披露值（总营业支出扣除税金及附加/其他业务成本 ÷ 营业收入）；2018–2025 为本行年报「成本收入比」披露值（业务及管理费/营业收入），两段定义不同、不完全可比
    const costIncome = D['nim-trend'].costIncome;

    initChart('chart-costincome')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['非息收入占比', '成本收入比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '非息收入占比', type: 'line', data: nonInt, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#16a085' }, itemStyle: { color: '#16a085' } },
            { name: '成本收入比', type: 'line', data: costIncome, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } }
        ]
    });

    // 旧准则「资产减值损失 / 营业收入」(2010–2017)——港股 03618 年报英文合并利润表 Impairment losses on assets / Operating income
    // 2010 为减值净转回(+45.2 百万), 故比率为负
    const impOld   = D['nim-trend'].impOld;
    // 新准则「信用减值损失 / 营业收入」(2018–2025)——A股年报, 2018 年起执行 IFRS9/新金融工具准则
    const impNew   = D['nim-trend'].impNew;

    function baseSeries() {
        return [
            { name: '资产减值/营收（旧准则）', type: 'line', data: impOld, smooth: true, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
              label: { show: true, fontSize: 18, color: '#e67e22', formatter: '{c}%' } },
            { name: '信用减值/营收（新准则）', type: 'line', data: impNew, smooth: true, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' },
              label: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } }
        ];
    }
    function creditcostOption(series) {
        return {
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '—' : v + '%' },
            legend: { data: series.map(s => s.name), top: 4, textStyle: { fontSize: 18 } },
            grid: { left: 48, right: 24, top: 46, bottom: 52 },
            xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
            yAxis: { type: 'value', name: '%', nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series
        };
    }
    // 只展示渝农商行单行数据（新旧准则两段），不再与天津银行/农业银行横向对比
    initChart('chart-creditcost')?.setOption(creditcostOption(baseSeries()));

    const provYears   = D['nim-trend'].provYears;
    const provCov = D['nim-trend'].provCov;
    const provRatio = D['nim-trend'].provRatio;

    initChart('chart-provision')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['拨备覆盖率', '拨贷比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 64, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: provYears, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '拨备覆盖率%', min: 0, nameTextStyle: { color: '#1e8449', fontSize: 18 },
              axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '拨贷比%', min: 0, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '拨备覆盖率', type: 'line', data: provCov, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' },
              areaStyle: { color: 'rgba(30,132,73,0.08)' } },
            { name: '拨贷比', type: 'line', yAxisIndex: 1, data: provRatio, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' } }
        ]
    });
})();

/* ────── 10b. 贷款核销与收回（2018–2025，人民币百万元） ────── */
(function () {
    // 取自本行 2018-2025 年年度报告「贷款减值准备变动」附注（HKEXnews 03618.HK / cqrcb.com 官网 PDF），2026-08-14 核对
    // 2022 年起「本期核销」「收回已核销」分项披露；2018-2021 仅披露合并净额（本期核销及其他转出），以净核销虚线呈现
    const years   = D['writeoff'].years;
    const writeOff  = D['writeoff'].writeOff;
    const recovery  = D['writeoff'].recovery;
    const netWO     = D['writeoff'].netWO;
    initChart('chart-writeoff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 百万' },
        legend: { data: ['本期核销', '收回已核销', '净核销（2018–2021）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '人民币百万元', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
                 axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '本期核销', type: 'line', data: writeOff, connectNulls: true, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' } },
            { name: '收回已核销', type: 'line', data: recovery, connectNulls: false, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '净核销（2018–2021）', type: 'line', data: netWO, connectNulls: false, symbolSize: 6,
              lineStyle: { width: 2, color: '#8e8e8e', type: 'dashed' }, itemStyle: { color: '#8e8e8e' } }
        ]
    });
})();

/* ────── 10c. 信用减值损失绝对值与总资产占比（2010–2025，人民币百万元） ────── */
(function () {
    const years = D['creditamount'].years;
    // 资产减值损失(2010-2017,旧准则)/信用减值损失(2018-2025,新准则)绝对值——本行/H股03618历年年报「财务摘要」，与已披露的减值/营收比率反算核对一致
    // 2010 年为净转回(-45.2百万)
    const impAmt = D['creditamount'].impAmt;
    // 资产总额（年末数）——同上来源「财务摘要」；2018 年取 A 股 2019 年报比较列口径（950,177.9），与 2019 年起序列衔接
    const totalAssetsY = D['creditamount'].totalAssetsY;
    const impOverAsset = impAmt.map((v, i) => +(v / totalAssetsY[i] * 100).toFixed(2));

    initChart('chart-creditamount')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                p.map(x => x.seriesName === '信用减值/总资产'
                    ? `${x.marker}${x.seriesName}：${x.value}%`
                    : `${x.marker}${x.seriesName}：${x.value} 百万元`).join('<br>') },
        legend: { data: ['信用减值损失（绝对值）', '信用减值/总资产'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 72, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '百万元', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '%', nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '信用减值损失（绝对值）', type: 'line', data: impAmt, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' } },
            { name: '信用减值/总资产', type: 'line', yAxisIndex: 1, data: impOverAsset, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' } }
        ]
    });
})();

});

__section(function (D, SELF, notes) {

/* ────── 8. 五级分类 ────── */
(function () {
    initChart('chart-5tier')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: '{b}: {c} 百万 ({d}%)' },
        // 样式沿用全站统一的 PIE_BASE / PIE_LABEL；次级/可疑/损失三档只占一两度，
        // 靠 minShowLabelAngle:0 + minMargin 才能各自出一条标注（原样式下它们的标注会叠在一起）
        series: pieSeries({
            data: [
                { value: D['5tier'].vals[0], name: '正常', itemStyle: { color: '#1e8449' } },
                { value: D['5tier'].vals[1],  name: '关注', itemStyle: { color: '#f39c12' } },
                { value: D['5tier'].vals[2],   name: '次级', itemStyle: { color: '#e67e22' } },
                { value: D['5tier'].vals[3],   name: '可疑', itemStyle: { color: '#c0392b' } },
                { value: D['5tier'].vals[4],   name: '损失', itemStyle: { color: '#7b241c' } }
            ]
        }, PIE_LABEL_PCT)
    });
})();

/* ────── 8b. 贷款迁徙率（渝农商行 2019–2025，正常类对比农业银行 2010–2023） ────── */
(function () {
    // 渝农商行: 2019-2025 逐年迁徙率(%), 取自历年A股年报「贷款迁徙率」表 (dfcfw.com PDF, pdftotext -layout 抽取)
    // 2019/2020 已按银保监发[2022]2号文追溯调整口径; 相邻年报重叠年份数值已交叉核对一致, 2026-08-14 提取核对
    const years = D['migrate'].years;
    // 关注/次级/可疑三档年末迁徙率随行取值（渝农商 2019-2025 已入 migrate 键；其余行 migrate 为空时整图已被 __stub 占位）
    const mgGuanzhu = D['migrate'].guanzhu || [];
    const mgCiji    = D['migrate'].ciji || [];
    const mgKeyi    = D['migrate'].keyi || [];
    initChart('chart-migrate')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '关注类', type: 'line', data: mgGuanzhu, symbolSize: 7, lineStyle: { width: 3, color: '#f39c12' }, itemStyle: { color: '#f39c12' } },
            { name: '次级类', type: 'line', data: mgCiji, symbolSize: 7, lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '可疑类', type: 'line', data: mgKeyi, symbolSize: 7, lineStyle: { width: 2.5, color: '#7b241c', type: 'dashed' }, itemStyle: { color: '#7b241c' } }
        ]
    });

    // 正常类迁徙率对比: 本行 vs 农业银行。农行那条由后端取农行自己的明细覆盖层（2010-2025 历年A股年报
    // 「其他财务指标」表，2020/2021 用 2022 年报追溯调整值），按本行 normalYears 对齐成 abcNormal
    const normalYears = D['migrate'].normalYears;
    const ynshbNormal = D['migrate'].ynshbNormal;
    const abcNormal   = D['migrate'].abcNormal;
    const serMg = live([
        { name: SELF, type: 'line', data: ynshbNormal, connectNulls: false, symbolSize: 7, lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
        { name: '农业银行', type: 'line', data: abcNormal, connectNulls: false, symbolSize: 6, lineStyle: { width: 2.5, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' },
          endLabel: { show: true, formatter: '{a}', fontSize: 15, color: '#2980b9', distance: 4 } }
    ]);
    initChart('chart-migrate-normal')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: serMg.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 88, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: normalYears, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serMg
    });
})();

});

__section(function (D, SELF, notes) {

/* ────── debt.html · 到期期限结构（金融资产 vs 金融负债，2025 年末，7 档） ──────
 * 数据来源：2025 年报财务报表附注「金融风险管理 · 流动性风险 · (1) 剩余到期日分析」
 * PDF 第 131–133 页；单位：亿元（原表为人民币千元，÷100,000 换算）。
 * 报告未披露 Macaulay / 修正久期数值——本行利率风险计量采用重定价缺口 + 敏感性 + 情景分析。
 */
(function () {
    if (!document.getElementById('chart-maturity')) return;
    const buckets = D['maturity'].buckets;
    // 2025-12-31 金融资产 / 金融负债（亿元）
    const asset2025 = D['maturity'].asset2025;
    const debt2025  = D['maturity'].debt2025;
    const net2025   = asset2025.map((a, i) => +(a - debt2025[i]).toFixed(2));

    initChart('chart-maturity')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue}</b>`;
                p.forEach(x => {
                    if (x.value == null) return;
                    s += `<br>${x.marker}${x.seriesName}：${Number(x.value).toLocaleString()} 亿`;
                });
                return s;
            } },
        legend: { data: ['金融资产', '金融负债', '净头寸（资产 − 负债）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 80, right: 24, top: 46, bottom: 60 },
        xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 17, color: '#555', interval: 0 },
                 axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: { type: 'value', name: '亿元', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555',
                     formatter: v => (Math.abs(v) >= 1000 ? (v / 1000).toFixed(1) + '千' : v) },
                 splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '金融资产', type: 'bar', data: asset2025, barGap: '10%',
              itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 14, color: '#555',
                       formatter: p => Number(p.value).toLocaleString() } },
            { name: '金融负债', type: 'bar', data: debt2025,
              itemStyle: { color: '#95a5a6' },
              label: { show: true, position: 'top', fontSize: 14, color: '#888',
                       formatter: p => Number(p.value).toLocaleString() } },
            { name: '净头寸（资产 − 负债）', type: 'line', data: net2025, smooth: false,
              symbolSize: 8, lineStyle: { width: 2.5, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              label: { show: true, fontSize: 14, color: '#c0392b',
                       position: p => p.value >= 0 ? 'top' : 'bottom',
                       formatter: p => Number(p.value).toLocaleString() } }
        ]
    });
})();


/* ────── risk.html · 权益资产比（股东权益合计 ÷ 资产总额，2010–2025，四行对比） ──────
 * = 1 − 资产负债率 = 1/权益乘数，最直观的财务杠杆指标；全口径权益（含少数股东权益）÷ 账面总资产。
 * 数据来源：东方财富 F10 各行历年年报合并资产负债表（data/tables/bank_<code>_annual.json 的 equity_asset_ratio）。
 */
(function () {
    if (!document.getElementById('chart-equity-asset')) return;
    const years = D['equity-asset'].years;
    const yrcb  = D['equity-asset'].yrcb;   // 本行（键名沿用 yrcb，换行时只换系列名）
    const abc   = D['equity-asset'].abc;    // 农业银行
    const cmb   = D['equity-asset'].cmb;    // 招商银行
    const psb   = D['equity-asset'].psb;    // 邮储银行

    const serEA = live([
        { name: SELF, type: 'line', data: yrcb, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#16a085' }, itemStyle: { color: '#16a085' },
          areaStyle: { color: 'rgba(22,160,133,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#16a085', formatter: '{c}%' } },
        peerLine('农业银行', abc, '#2874a6'),
        peerLine('招商银行', cmb, '#229954'),
        peerLine('邮储银行', psb, '#d68910')
    ]);
    initChart('chart-equity-asset')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serEA.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '权益资产比%', min: 0, max: axMax(11, yrcb, abc, cmb, psb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#16a085', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serEA
    });
})();

});
