/* 业绩 index.html / 资产端 asset.html / 负债端 debt.html 三页共用本文件：
 * 图容器不在当前页时 initChart 返回 null，配合 ?. 跳过该图，不影响后面的图。 */
function initChart(id) {
    const el = document.getElementById(id);
    return el ? echarts.init(el) : null;
}

/* ────── 1. 业绩走势（2009 年起，2008 年 6 月信用社改制为股份公司致口径断口） ────── */
(function () {
    const years   = ['2009',
                     '2010','2011','2012','2013','2014','2015','2016','2017',
                     '2018','2019','2020','2021','2022','2023','2024','2025'];
    // 2009 年营业收入 56.77 亿、净利润 18.88 亿：取自本行 2010 年 12 月 H 股招股章程 Appendix IB 会计师报告（重组后口径）
    // 2010/2011 归母净利润按 H 股年报「歸屬於本行股東的淨利潤」原文修正为 30.64/42.47 亿（此前误取衍生值 31.13/42.71）
    const revenue = [ 56.77,
                      78.11,110.24,135.54,162.10,197.10,217.43,217.05,239.88,
                     261.16,266.30,281.86,308.42,289.91,279.56,282.31,286.20];
    const profit  = [ 18.88,
                      30.64, 42.47, 53.61, 59.91, 68.28, 72.23, 79.45, 89.36,
                      90.58, 97.60, 84.01, 95.60,102.76,109.02,115.13,121.28];
    initChart('chart-perf')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                p.map(x => `${x.marker}${x.seriesName}：${x.value} 亿元`).join('<br>') },
        legend: { data: ['营业收入','归母净利润'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
            axisLabel: { fontSize: 18, color: '#555', rotate: 40 }, axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
            axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '营业收入', type: 'line', data: revenue, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '归母净利润', type: 'line', data: profit, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } }
        ]
    });
})();

/* ────── 1.1b 加权平均 ROE（2009 年起，2018 年新准则切换断口） ────── */
(function () {
    const years = ['2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025'];
    // 2009–2013 简单 ROE = 归母净利润 / 平均归母权益（年报未披露加权平均值）
    // 2009 年净利润 18.88 亿、期末权益 94.77 亿：取自 2010 年 H 股招股章程 Appendix IB 会计师报告（hkexnews.hk），2008 年期末权益 78.92 亿同源
    // 2010 年 12 月 H 股上市募资致权益年内跳升，简单平均偏低；2011–2013 无重大增发，近似加权
    const roeCalc = [21.75, 19.89, 17.01, 18.07, 17.81, null, null, null, null, null, null, null, null, null, null, null, null];
    // 旧准则「加权平均股东权益回报率」(年报披露)，2014–2018
    const roeOld = [null, null, null, null, null, 17.81, 17.27, 17.06, 16.38, 15.99, null, null, null, null, null, null, null];
    // 新准则「加权平均净资产收益率」(年报披露)，自 2018 年首次执行新金融工具准则起
    const roeNew = [null, null, null, null, null, null, null, null, null, 13.55, 12.82, 9.28, 9.87, 9.76, 9.58, 9.28, 9.18];
    initChart('chart-roe')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue} 年</b>`;
                p.forEach(x => { if (x.value != null) s += `<br>${x.marker}${x.seriesName}：${x.value}%`; });
                return s;
            } },
        legend: { data: ['简单ROE（净利/平均权益）', 'ROE（旧准则·年报）', 'ROE（新准则·年报）'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 68 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '简单ROE（净利/平均权益）', type: 'line', data: roeCalc, symbolSize: 6,
              lineStyle: { width: 2.5, color: '#af7ac5', type: 'dotted' }, itemStyle: { color: '#af7ac5' },
              label: { show: true, position: 'top', fontSize: 16, color: '#af7ac5', formatter: '{c}%' } },
            { name: 'ROE（旧准则·年报）', type: 'line', data: roeOld, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483', type: 'dashed' }, itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 16, color: '#6c3483', formatter: '{c}%' } },
            { name: 'ROE（新准则·年报）', type: 'line', data: roeNew, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' },
              label: { show: true, position: 'top', fontSize: 16, color: '#6c3483', formatter: '{c}%' } }
        ]
    });
})();
(function () {
    const years = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025'];
    const deposit = [2055.63, 2461.41, 2945.10, 3478.83, 4097.20, 4702.28, 5181.86, 5721.84, 6161.66, 6734.02, 7250.00, 7593.60, 8249.47, 8962.02, 9419.46, 10287.28];
    const loan    = [1221.45, 1388.22, 1735.59, 2052.52, 2421.98, 2685.86, 3004.21, 3383.47, 3811.36, 4370.85, 5078.90, 5821.67, 6326.77, 6767.11, 7142.73,  7972.87];
    const npl     = [2.38,    1.44,    0.98,    0.80,    0.78,    0.98,    0.96,    0.98,    1.29, 1.25, 1.31, 1.25, 1.22, 1.19, 1.18, 1.08];
    const nplAbc  = [2.03,    1.55,    1.33,    1.22,    1.54,    2.39,    2.37,    1.81,    1.59, 1.40, 1.57, 1.43, 1.37, 1.33, 1.30, 1.27];
    const nplCmb  = [0.68,    0.56,    0.61,    0.83,    1.11,    1.68,    1.87,    1.61,    1.36, 1.16, 1.07, 0.91, 0.96, 0.95, 0.95, 0.94];
    const car     = [null,    null,    null,    null,    12.45,   12.09,   12.70,   13.03,   13.52, 14.88, 14.28, 14.77, 15.62, 15.99, 16.12, 14.46];
    const cet1    = [null,    null,    null,    null,    10.12,   9.88,    9.85,    10.39,   10.95, 12.42, 11.96, 12.47, 13.10, 13.53, 14.24, 12.67];

    // 对数线性回归 ln(y) = a + b·t，回归增速 = exp(b) − 1；返回拟合值供画趋势线
    function logFit(vals) {
        const t = [], ly = [];
        vals.forEach((v, i) => { if (v != null && v > 0) { t.push(i); ly.push(Math.log(v)); } });
        const n = t.length, mt = t.reduce((s, x) => s + x, 0) / n, ml = ly.reduce((s, x) => s + x, 0) / n;
        let sxy = 0, sxx = 0, sst = 0;
        for (let i = 0; i < n; i++) { sxy += (t[i] - mt) * (ly[i] - ml); sxx += (t[i] - mt) ** 2; sst += (ly[i] - ml) ** 2; }
        const b = sxy / sxx, a = ml - b * mt;
        let sse = 0;
        for (let i = 0; i < n; i++) sse += (ly[i] - (a + b * t[i])) ** 2;
        return { cagr: Math.exp(b) - 1, r2: 1 - sse / sst,
                 fit: vals.map((_, i) => +Math.exp(a + b * i).toFixed(2)) };
    }
    // 线性回归 y = a + b·t，增速为固定斜率（亿元/年）
    function linFit(vals) {
        const t = [], ys = [];
        vals.forEach((v, i) => { if (v != null) { t.push(i); ys.push(v); } });
        const n = t.length, mt = t.reduce((s, x) => s + x, 0) / n, my = ys.reduce((s, x) => s + x, 0) / n;
        let sxy = 0, sxx = 0, sst = 0;
        for (let i = 0; i < n; i++) { sxy += (t[i] - mt) * (ys[i] - my); sxx += (t[i] - mt) ** 2; sst += (ys[i] - my) ** 2; }
        const b = sxy / sxx, a = my - b * mt;
        let sse = 0;
        for (let i = 0; i < n; i++) sse += (ys[i] - (a + b * t[i])) ** 2;
        return { slope: b, r2: 1 - sse / sst, fit: vals.map((_, i) => +(a + b * i).toFixed(2)),
                 rate: `+${Math.round(b).toLocaleString()} 亿/年` };
    }
    const fits = {
        log: { dep: logFit(deposit),  loan: logFit(loan)  },
        lin: { dep: linFit(deposit),  loan: linFit(loan)  }
    };
    fits.log.dep.rate = `+${(fits.log.dep.cagr * 100).toFixed(2)}%/年`;
    fits.log.loan.rate = `+${(fits.log.loan.cagr * 100).toFixed(2)}%/年`;

    // 存款、贷款各占一张图、各自回归；每张图同时画指数回归与线性回归两条趋势线
    function makeScaleChart(domId, label, vals, key, color, areaColor) {
        const chart = initChart(domId);
        if (!chart) return;                       // 存款图在负债端页、贷款图在资产端页
        const exp = fits.log[key], lin = fits.lin[key];
        chart.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                formatter: p => {
                    const i = p[0].dataIndex, act = vals[i];
                    if (act == null) return `<b>${p[0].axisValue} 年</b><br>${label}：缺口`;
                    const prev = i > 0 ? vals[i - 1] : null;
                    const yoy = prev ? ((act / prev - 1) * 100).toFixed(2) + '%' : '—';
                    const dev = f => { const d = ((act / f.fit[i] - 1) * 100).toFixed(1); return `${d > 0 ? '+' : ''}${d}%`; };
                    return `<b>${p[0].axisValue} 年</b><br>` +
                           `<span style="color:${color}">●</span> ${label}：<b>${act.toLocaleString()}</b> 亿 · 同比 ${yoy}` +
                           `<br>　指数趋势 ${exp.fit[i].toLocaleString()} 亿 · 偏离 ${dev(exp)}` +
                           `<br>　线性趋势 ${lin.fit[i].toLocaleString()} 亿 · 偏离 ${dev(lin)}`;
                } },
            legend: { data: [label, '指数回归', '线性回归'], bottom: 2, textStyle: { fontSize: 18 } },
            grid: { left: 64, right: 170, top: 30, bottom: 52 },
            xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series: [
                { name: label, type: 'line', data: vals, smooth: true, connectNulls: true, symbolSize: 6,
                  lineStyle: { width: 3, color }, itemStyle: { color },
                  areaStyle: { color: areaColor } },
                { name: '指数回归', type: 'line', data: exp.fit, symbol: 'none', z: 3, silent: true,
                  lineStyle: { width: 2, type: 'dashed', color, opacity: 0.8 }, itemStyle: { color },
                  endLabel: { show: true, fontSize: 18, color, distance: 6,
                      formatter: `指数 ${exp.rate}` } },
                { name: '线性回归', type: 'line', data: lin.fit, symbol: 'none', z: 3, silent: true,
                  lineStyle: { width: 2, type: 'dotted', color: '#7f8c8d' }, itemStyle: { color: '#7f8c8d' },
                  endLabel: { show: true, fontSize: 18, color: '#7f8c8d', distance: 6,
                      formatter: `线性 ${lin.rate}` } }
            ]
        });
        document.getElementById('fit-note-' + key).innerHTML =
            `指数回归 ln(y)=a+b·t：<b>${exp.rate}</b>（R²=${exp.r2.toFixed(3)}）` +
            ` · 线性回归 y=a+b·t：<b>${lin.rate}</b>（R²=${lin.r2.toFixed(3)}）`;
    }
    makeScaleChart('chart-scale-dep',  '客户存款',      deposit, 'dep',  '#6c3483', 'rgba(108,52,131,0.08)');
    makeScaleChart('chart-scale-loan', '客户贷款及垫款', loan,    'loan', '#e67e22', 'rgba(230,126,34,0.08)');

    initChart('chart-npl')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['渝农商行', '农业银行', '招商银行'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '不良率%', min: 0, max: 3, nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '渝农商行', type: 'line', data: npl, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.07)' },
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
            { name: '农业银行', type: 'line', data: nplAbc, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#2874a6', type: 'dashed' }, itemStyle: { color: '#2874a6' } },
            { name: '招商银行', type: 'line', data: nplCmb, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#229954', type: 'dashed' }, itemStyle: { color: '#229954' } }
        ]
    });

    initChart('chart-quality')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['资本充足率', '核心一级资本充足率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 20, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, max: 18, nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '资本充足率', type: 'line', data: car, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '核心一级资本充足率', type: 'line', data: cet1, smooth: true, connectNulls: true, symbolSize: 5,
              lineStyle: { width: 2, color: '#27ae60', type: 'dashed' }, itemStyle: { color: '#27ae60' } }
        ]
    });
})();

/* ────── 1e. 盈利质量与效率（2010–2025） ────── */
(function () {
    const years10  = ['2010','2011','2012','2013','2014','2015','2016','2017',
                       '2018','2019','2020','2021','2022','2023','2024','2025'];
    // NIM/NIS：H 股 03618 历年年报「財務摘要—盈利能力指標」及本行 2010–2025 年年度报告披露值
    // 2018 年改用新准则（IFRS9）值 2.45/2.40（此前误取"經調整"IAS39 口径 2.65/2.44，与后续年份口径不一致）
    const nim  = [3.07, 3.36, 3.50, 3.41, 3.37, 3.20, 2.74, 2.62, 2.45, 2.33, 2.25, 2.17, 1.97, 1.73, 1.61, 1.60];
    const nis  = [2.97, 3.13, 3.26, 3.19, 3.14, 2.99, 2.57, 2.44, 2.40, 2.16, 2.08, 2.01, 1.84, 1.64, 1.51, 1.51];

    initChart('chart-nim-trend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['净息差 NIM', '净利差 NIS'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years10, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
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
    const nonInt     = [3.14, 5.52, 4.11, 3.75, 7.34, 7.87, 10.42, 10.30, 23.37, 12.23, 13.97, 14.94, 12.37, 15.96, 20.41, 15.32];
    // 成本收入比：2010–2017 为 H 股年报「成本佔收入比率」披露值（总营业支出扣除税金及附加/其他业务成本 ÷ 营业收入）；2018–2025 为本行年报「成本收入比」披露值（业务及管理费/营业收入），两段定义不同、不完全可比
    const costIncome = [44.40,36.64,37.70,37.66,35.74,34.69,35.95,33.96,30.33,28.54,27.09,27.52,31.84,33.94,31.86,31.22];

    initChart('chart-costincome')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['非息收入占比', '成本收入比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years10, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '非息收入占比', type: 'line', data: nonInt, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#16a085' }, itemStyle: { color: '#16a085' } },
            { name: '成本收入比', type: 'line', data: costIncome, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } }
        ]
    });

    const yearsCC  = ['2010','2011','2012','2013','2014','2015','2016','2017',
                       '2018','2019','2020','2021','2022','2023','2024','2025'];
    // 旧准则「资产减值损失 / 营业收入」(2010–2017)——港股 03618 年报英文合并利润表 Impairment losses on assets / Operating income
    // 2010 为减值净转回(+45.2 百万), 故比率为负
    const impOld   = [-0.58, 7.63, 3.75, 7.24, 11.60, 14.78, 12.36, 15.48,
                       null, null, null, null, null, null, null, null];
    // 新准则「信用减值损失 / 营业收入」(2018–2025)——A股年报, 2018 年起执行 IFRS9/新金融工具准则
    const impNew   = [null, null, null, null, null, null, null, null,
                       23.70, 24.68, 36.22, 35.19, 27.04, 21.25, 21.08, 19.00];
    // 天津银行（01578.HK）「减值损失 / 营业收入」(2018–2025)——港交所年度业绩公告「会计数据及财务指标概要」
    // 2018 年起执行 IFRS9，减值损失科目口径与渝农商行新准则可比；2010–2017 未追溯查证故留空
    const impTcb   = [null, null, null, null, null, null, null, null,
                       28.69, 43.57, 47.86, 55.68, 47.75, 47.22, 45.39, 45.37];
    // 农业银行（601288.SH）「资产/信用减值损失 / 营业收入」——历年年报（abchina.com 官网 PDF，合并口径），口径切换与渝农商行一致（2018 年起 IFRS9）
    const impAbcOld = [14.95, 17.00, 12.85, 11.45, 13.05, 15.70, 17.08, 18.28,
                       null, null, null, null, null, null, null, null];
    const impAbcNew = [null, null, null, null, null, null, null, null,
                       22.83, 22.10, 25.03, 23.04, 20.91, 19.53, 18.41, 17.54];

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
            xAxis: { type: 'category', data: yearsCC, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
            yAxis: { type: 'value', name: '%', nameTextStyle: { fontSize: 18 }, axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series
        };
    }
    // 三张图平铺在同一条横向滚动带里（不做 tab 切换）：直接左右滑动/拖拽即可浏览
    initChart('chart-creditcost')?.setOption(creditcostOption(baseSeries()));
    initChart('chart-creditcost-tcb')?.setOption(creditcostOption([
        ...baseSeries(),
        { name: '天津银行·减值/营收', type: 'line', data: impTcb, smooth: true, connectNulls: false, symbolSize: 6,
          lineStyle: { width: 3, color: '#2874a6', type: 'dashed' }, itemStyle: { color: '#2874a6' },
          label: { show: true, fontSize: 18, color: '#2874a6', formatter: '{c}%' } }
    ]));
    initChart('chart-creditcost-abc')?.setOption(creditcostOption([
        ...baseSeries(),
        { name: '农业银行·旧准则', type: 'line', data: impAbcOld, smooth: true, connectNulls: false, symbolSize: 6,
          lineStyle: { width: 2.5, color: '#229954', type: 'dashed' }, itemStyle: { color: '#229954' },
          label: { show: true, fontSize: 18, color: '#229954', formatter: '{c}%' } },
        { name: '农业银行·新准则', type: 'line', data: impAbcNew, smooth: true, connectNulls: false, symbolSize: 6,
          lineStyle: { width: 3, color: '#196f3d', type: 'dashed' }, itemStyle: { color: '#196f3d' },
          label: { show: true, fontSize: 18, color: '#196f3d', formatter: '{c}%' } }
    ]));

    // 平铺 + 左右滑动（参考 Apple TV 那种横向内容带）：三张图并排，鼠标可直接按住拖动横向滚动，
    // 触控板/触屏原生横滑，配合 CSS scroll-snap 让每张图停到位。不再有 tab 切换按钮。
    (function () {
        const slider = document.querySelector('#chart-creditcost')?.closest('.compare-slider');
        if (!slider) return;
        // 满屏横滑带用 100vw 会把竖向滚动条那 ~15px 也算进去，导致整页多出一条横向滚动条。
        // documentElement.clientWidth 是「不含竖向滚动条」的真实可视宽，写进 --app-vw 供 CSS 用，
        // 这样既铺满可视宽、又不会溢出（避开在 html 上加 overflow-x:hidden——那会破坏吸顶导航的 sticky）。
        const setVW = () => document.documentElement.style.setProperty(
            '--app-vw', document.documentElement.clientWidth + 'px');
        setVW();
        window.addEventListener('resize', () => {
            setVW();
            ['chart-creditcost', 'chart-creditcost-tcb', 'chart-creditcost-abc'].forEach(id => {
                const el = document.getElementById(id);
                if (el) echarts.getInstanceByDom(el)?.resize();
            });
        });
        // 三张图都在滚动带内已按各自宽度布局，补一次 resize 保证宽度正确
        ['chart-creditcost', 'chart-creditcost-tcb', 'chart-creditcost-abc'].forEach(id => {
            const el = document.getElementById(id);
            if (el) echarts.getInstanceByDom(el)?.resize();
        });

        // 鼠标按住拖动横向滚动（桌面端；触屏/触控板走原生横滑，无需接管）
        let down = false, startX = 0, startLeft = 0, moved = false;
        slider.addEventListener('pointerdown', e => {
            if (e.pointerType && e.pointerType !== 'mouse') return;
            down = true; moved = false;
            startX = e.clientX; startLeft = slider.scrollLeft;
            slider.classList.add('dragging');
        });
        slider.addEventListener('pointermove', e => {
            if (!down) return;
            const dx = e.clientX - startX;
            if (Math.abs(dx) > 3) moved = true;
            slider.scrollLeft = startLeft - dx;
        });
        function endDrag() {
            if (!down) return;
            down = false;
            slider.classList.remove('dragging');
        }
        slider.addEventListener('pointerup', endDrag);
        slider.addEventListener('pointerleave', endDrag);
        // 拖动过程中吞掉点击，避免误触发图例等交互
        slider.addEventListener('click', e => { if (moved) { e.stopPropagation(); e.preventDefault(); } }, true);
    })();

    const years13   = ['2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025'];
    const provCov13 = [430.60,459.79,420.03,428.37,431.24,347.79,380.31,314.95,340.25,357.74,366.70,363.44,367.26];
    const provRatio = [3.46, 3.58, 4.11, 4.10, 4.21, 4.50, 4.75, 4.12, 4.27, 4.36, 4.37, 4.28, 3.96];

    initChart('chart-provision')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['拨备覆盖率', '拨贷比'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 64, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years13, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '拨备覆盖率%', min: 0, nameTextStyle: { color: '#1e8449', fontSize: 18 },
              axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '拨贷比%', min: 0, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '拨备覆盖率', type: 'line', data: provCov13, smooth: true, symbolSize: 6,
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
    const yearsWO   = ['2018','2019','2020','2021','2022','2023','2024','2025'];
    const writeOff  = [867.8, 1943.4, 10051.6, 7933.3, 7064.8, 4209.8, 5805.2, 6619.1];
    const recovery  = [null,  null,   null,    null,   2112.0, 1931.6, 1328.5, 2477.9];
    const netWO     = [867.8, 1943.4, 10051.6, 7933.3, null,   null,   null,   null];
    initChart('chart-writeoff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 百万' },
        legend: { data: ['本期核销', '收回已核销', '净核销（2018–2021）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: yearsWO, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
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

/* ────── 1i. 其他综合收益（OCI）与净利润 ────── */
(function () {
    // 取自本行 2018-2025 年年度报告「贷款减值准备变动」附注（HKEXnews 03618.HK / cqrcb.com 官网 PDF），2026-08-14 核对
    // 2022 年起「本期核销」「收回已核销」分项披露；2018-2021 仅披露合并净额（本期核销及其他转出），以净核销虚线呈现
    const yearsWO   = ['2018','2019','2020','2021','2022','2023','2024','2025'];
    const writeOff  = [867.8, 1943.4, 10051.6, 7933.3, 7064.8, 4209.8, 5805.2, 6619.1];
    const recovery  = [null,  null,   null,    null,   2112.0, 1931.6, 1328.5, 2477.9];
    const netWO     = [867.8, 1943.4, 10051.6, 7933.3, null,   null,   null,   null];
    initChart('chart-writeoff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 百万' },
        legend: { data: ['本期核销', '收回已核销', '净核销（2018–2021）'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: yearsWO, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
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

/* ────── 1i. 其他综合收益（OCI）与净利润 ────── */
(function () {
    const years16  = ['2010','2011','2012','2013','2014','2015','2016','2017',
                       '2018','2019','2020','2021','2022','2023','2024','2025'];
    const oci      = [-0.49, -0.35, 0.09, -0.66, 1.13, -0.26, -2.54, 0.20,
                       -0.87, -1.82, -2.44, 2.47, -4.77, 8.98, 41.72, -28.97];
    initChart('chart-oci')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + ' 亿' },
        legend: { data: ['其他综合收益'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 64, right: 64, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years16, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '其他综合收益(亿元)', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '其他综合收益', type: 'line', data: oci, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              areaStyle: { color: 'rgba(192,57,43,0.08)' },
              markLine: {
                  symbol: 'none', silent: true,
                  lineStyle: { color: '#8e8e8e', type: 'dashed', width: 1.5 },
                  label: { formatter: '2018 IFRS9 新准则', position: 'end', distance: 6,
                           fontSize: 16, color: '#8e8e8e' },
                  data: [
                      { xAxis: '2018' },
                      { yAxis: 0, lineStyle: { color: '#bbb', type: 'solid', width: 1 },
                        label: { show: false } }
                  ]
              },
              markPoint: {
                  symbol: 'circle', symbolSize: 11, silent: true,
                  label: { fontSize: 16, fontWeight: 'bold', position: 'left', distance: 8,
                           formatter: '{c} 亿' },
                  data: [
                      { type: 'max', name: '最大', itemStyle: { color: '#c0392b' },
                        label: { color: '#c0392b' } },
                      { type: 'min', name: '最小', itemStyle: { color: '#2c6fb3' },
                        label: { color: '#2c6fb3' } }
                  ]
              } }
        ]
    });
})();

/* ────── 1j. 每股指标 EPS / BVPS ────── */
(function () {
    const years16 = ['2010','2011','2012','2013','2014','2015','2016','2017',
                     '2018','2019','2020','2021','2022','2023','2024','2025'];
    const eps  = [0.45, 0.46, 0.58, 0.64, 0.73, 0.78, 0.85, 0.94,
                  0.91, 0.95, 0.74, 0.84, 0.89, 0.94, 0.99, 1.05];
    // BVPS：港交所 03618 历年年报「歸屬於本行股東的每股淨資產」披露值（2010 年为加权口径，2011 起为期末口径）
    const bvps = [3.26, 3.00, 3.43, 3.90, 4.45, 5.03, 5.66, 6.37,
                  7.07, 7.73, 8.21, 8.85, 9.45, 10.19, 11.07, 11.55];

    initChart('chart-pershare')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 元' },
        legend: { data: ['基本每股收益(EPS)', '每股净资产(BVPS)'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 60, right: 60, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years16, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: 'EPS(元)', min: 0, nameTextStyle: { color: '#6c3483', fontSize: 18 },
              axisLabel: { color: '#6c3483', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: 'BVPS(元)', min: 0, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '基本每股收益(EPS)', type: 'line', data: eps, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              endLabel: { show: true, fontSize: 18, color: '#6c3483', formatter: '{c}' } },
            { name: '每股净资产(BVPS)', type: 'line', yAxisIndex: 1, data: bvps, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1j2. 历年每 10 股分红（元，含税，按年度累计） ────── */
(function () {
    if (!document.getElementById('chart-dividend-per10')) return;   // 仅股东页
    // 2011–2018：03618 港股年报「盈利与股息」披露的内资股/H股每股派息（元）× 10；2010 年董事会未提常规股息（仅 IPO 前特别股息，口径不可比，未纳入）
    // 2019–2025：本行 A 股年度报告「利润分配方案」披露的每 10 股股利
    const years9 = ['2011','2012','2013','2014','2015','2016','2017','2018',
                    '2019','2020','2021','2022','2023','2024','2025'];
    const per10  = [1.40, 1.70, 1.90, 2.00, 2.00, 2.00, 2.00, 2.00,
                     2.30, 2.22, 2.525, 2.714, 2.885, 3.046, 3.2091];

    initChart('chart-dividend-per10')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + ' 元' },
        grid: { left: 60, right: 40, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years9, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '每10股分红(元)', min: 0, nameTextStyle: { color: '#555', fontSize: 18 },
                 axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '每10股分红(含税)', type: 'bar', data: per10, itemStyle: { color: '#c0392b' },
              barMaxWidth: 44,
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1j3. 历年股东户数（2017-12 至今：H 股年报 + 历年定期报告披露值） ────── */
(function () {
    if (!document.getElementById('chart-holder-count')) return;   // 仅股东页
    // [披露日, 股东总数, A 股股东, H 股股东] —— A/H 部分披露点未拆分, 保留 null
    // 数据源:
    //   · A 股 IPO 后 (2019-10 至今, 43 期): 本行历年定期报告（年报/中报/季报）「股东情况」章节披露值
    //   · A 股 IPO 前 H 股登记股东数 (2017/2018 年末, 2 期): 03618 港股年报「股本变动及股东情况」章节脚注
    //     -> data/tables/holder_count_hshare_2010_2018.json  (2010-2016 年报未披露该项)
    const raw = [
        ['2017-12-31', null,   null,   1420],   // 03618 2017 年报 p.85: "H 股登记股东 1,420 户"
        ['2018-12-31', null,   null,   1316],   // 03618 2018 年报 p.89: "H 股登记股东 1,316 户"
        ['2019-10-29', 948725, null,   null],
        ['2019-10-31', 583060, null,   null],
        ['2019-11-20', 452600, null,   null],
        ['2019-12-10', 419500, null,   null],
        ['2019-12-31', 394155, 392874, 1281],
        ['2020-02-29', 332330, 331053, 1277],
        ['2020-03-31', 314762, 313482, 1280],
        ['2020-06-30', 303597, 302319, 1278],
        ['2020-07-31', 292747, 291477, 1270],
        ['2020-09-30', 277555, 276289, 1266],
        ['2020-12-31', 275965, 274714, 1251],
        ['2021-02-28', 274738, 273496, 1242],
        ['2021-03-31', 271460, null,   null],
        ['2021-06-30', 266913, 265687, 1226],
        ['2021-07-31', 262138, 260914, 1224],
        ['2021-09-30', 254077, null,   null],
        ['2021-12-31', 252817, 251605, 1212],
        ['2022-02-28', 244222, 243013, 1209],
        ['2022-03-31', 241964, null,   null],
        ['2022-06-30', 237764, 236567, 1197],
        ['2022-07-31', 236283, 235093, 1190],
        ['2022-09-30', 230787, null,   null],
        ['2022-12-31', 228767, 227580, 1187],
        ['2023-02-28', 227672, 226485, 1187],
        ['2023-03-31', 225817, null,   null],
        ['2023-06-30', 216900, 215719, 1181],
        ['2023-07-31', 214738, 213559, 1179],
        ['2023-09-30', 207940, null,   null],
        ['2023-12-31', 195606, 194439, 1167],
        ['2024-02-29', 189461, 188300, 1161],
        ['2024-03-31', 186110, null,   null],
        ['2024-06-30', 175010, 173852, 1158],
        ['2024-07-31', 169389, 168232, 1157],
        ['2024-09-30', 186110, null,   null],   // 数据源该期回填前值, 图中保留原样
        ['2024-12-31', 149711, 148580, 1131],
        ['2025-02-28', 146121, 144998, 1123],
        ['2025-03-31', 137910, null,   null],
        ['2025-06-30', 124514, 123409, 1105],
        ['2025-07-31', 125825, 124727, 1098],
        ['2025-09-30', 123765, null,   null],
        ['2025-12-31', 116634, 115547, 1087],
        ['2026-02-28', 112716, 111633, 1083],
        ['2026-03-31', 107028, null,   null]
    ];
    const dates  = raw.map(r => r[0]);
    const total  = raw.map(r => r[1]);
    const aNum   = raw.map(r => r[2]);
    const hNum   = raw.map(r => r[3]);
    const fmt    = v => v == null ? '—' : v.toLocaleString('en-US');
    const wan    = v => v == null ? '—' : (v / 10000).toFixed(2) + ' 万';

    initChart('chart-holder-count')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        legend: {
            data: ['股东总数（A+H · 左轴 · 万户）', 'H 股登记股东数（右轴 · 户）'],
            top: 4, right: 20, textStyle: { fontSize: 16 },
            icon: 'roundRect'
        },
        tooltip: {
            trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex;
                // 找出前一个有 total 值的披露点用于环比
                let prev = null;
                for (let k = i - 1; k >= 0; k--) { if (total[k] != null) { prev = total[k]; break; } }
                const chg  = (prev == null || total[i] == null) ? '' :
                             (total[i] - prev >= 0 ? '+' : '') + (total[i] - prev).toLocaleString('en-US');
                const pct  = (prev == null || total[i] == null) ? '' :
                             ((total[i] - prev) / prev * 100).toFixed(2) + '%';
                const totalLine = total[i] == null
                    ? `股东总数：— <span style="color:#888">（A 股尚未上市）</span>`
                    : `股东总数：${fmt(total[i])} 户（${wan(total[i])}）` +
                      (prev == null ? '' : `<br>环比：${chg} 户（${pct}）`);
                return `<b>${dates[i]}</b><br>` + totalLine +
                       (aNum[i] != null ? `<br>其中 A 股：${fmt(aNum[i])} 户` : '') +
                       (hNum[i] != null ? `<br>H 股登记股东：${fmt(hNum[i])} 户` : '');
            }
        },
        grid: { left: 88, right: 160, top: 56, bottom: 70 },
        xAxis: {
            type: 'category', data: dates, boundaryGap: false,
            axisLabel: { fontSize: 16, color: '#555', rotate: 40, interval: 2 },
            axisLine: { lineStyle: { color: '#bbb' } }
        },
        yAxis: [
            {
                type: 'value', name: '股东总数（万户）', min: 0,
                position: 'left',
                nameTextStyle: { color: '#6c3483', fontSize: 18 },
                axisLabel: { color: '#6c3483', fontSize: 18, formatter: v => (v / 10000).toFixed(0) },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            {
                type: 'value', name: 'H 股股东（户）', min: 1000, max: 1500, interval: 100,
                position: 'right',
                nameTextStyle: { color: '#16a085', fontSize: 18 },
                axisLabel: { color: '#16a085', fontSize: 18, formatter: v => v.toLocaleString('en-US') },
                splitLine: { show: false }
            }
        ],
        series: [{
            name: '股东总数（A+H · 左轴 · 万户）',
            type: 'line', data: total, smooth: true, symbolSize: 7,
            connectNulls: false,
            lineStyle: { width: 3, color: '#6c3483' },
            itemStyle: { color: '#6c3483' },
            areaStyle: { color: 'rgba(108,52,131,0.10)' },
            endLabel: { show: true, fontSize: 18, color: '#6c3483',
                        formatter: p => p.value == null ? '' : `${(p.value / 10000).toFixed(2)} 万` },
            markPoint: {
                symbol: 'circle', symbolSize: 11, silent: true,
                label: { fontSize: 16, fontWeight: 'bold', color: '#fff',
                         formatter: p => (p.value / 10000).toFixed(1) + ' 万' },
                data: [
                    { type: 'max', name: 'IPO 峰值', itemStyle: { color: '#c0392b' },
                      label: { color: '#fff' } },
                    { type: 'min', name: '当前最低', itemStyle: { color: '#2c6fb3' },
                      label: { color: '#fff' } }
                ]
            },
            markLine: {
                symbol: 'none', silent: true,
                lineStyle: { color: '#8e8e8e', type: 'dashed', width: 1.5 },
                label: { fontSize: 16, color: '#8e8e8e', position: 'insideEndTop',
                         formatter: '{b}' },
                data: [
                    { name: '2019-10-29 A 股上市', xAxis: '2019-10-29' }
                ]
            }
        }, {
            name: 'H 股登记股东数（右轴 · 户）',
            type: 'line', yAxisIndex: 1, data: hNum,
            smooth: true, symbolSize: 8,
            connectNulls: true,       // H 股只在年末/半年末披露, 跨越缺口连线
            lineStyle: { width: 2.5, color: '#16a085', type: 'solid' },
            itemStyle: { color: '#16a085' },
            endLabel: { show: true, fontSize: 16, color: '#16a085',
                        formatter: p => p.value == null ? '' : `${p.value.toLocaleString('en-US')} 户` }
        }]
    });
})();

/* ────── 1j4. 历年处理消费投诉数（件）与客户满意度（%） ────── */
(function () {
    if (!document.getElementById('chart-complaint')) return;   // 仅简介页
    const years3 = ['2023', '2024', '2025'];
    const complaints   = [1615, 1662, 2602];
    const satisfaction = [86.07, 83.51, 70.88];

    initChart('chart-complaint')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 } },
        legend: { data: ['处理消费投诉数', '消费投诉处理客户满意度'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 60, right: 60, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years3, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '投诉数(件)', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '满意度(%)', min: 0, max: 100, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '处理消费投诉数', type: 'bar', data: complaints, itemStyle: { color: '#c0392b' },
              barMaxWidth: 60,
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '消费投诉处理客户满意度', type: 'line', yAxisIndex: 1, data: satisfaction, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#2980b9' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}%' } }
        ]
    });
})();


/* ────── 1k. 金融投资分类结构 AC / FVOCI / FVTPL ────── */
(function () {
    const years8 = ['2018','2019','2020','2021','2022','2023','2024','2025'];
    const ac        = [2895.6, 3464.2, 3831.6, 4244.2, 4011.4, 3217.7, 2972.5, 2489.0];
    const fvociDebt = [71.0, 66.8, 160.6, 480.4, 1053.7, 1649.3, 2448.2, 3111.7];
    const fvociEq   = [6.2, 5.8, 5.7, 8.0, 6.3, 13.1, 13.8, 24.4];
    const fvtpl     = [150.9, 236.8, 301.6, 483.5, 658.4, 1107.7, 845.5, 811.2];

    initChart('chart-invest')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   valueFormatter: v => v + ' 亿' },
        legend: { data: ['债权投资(AC/摊余成本)', '其他债权投资(FVOCI债)', '其他权益工具(FVOCI股)', '交易性金融资产(FVTPL)'],
                  bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years8, axisLabel: { fontSize: 18, color: '#555' } },
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
    const cats  = ['其他投资', '信托计划', '资产管理计划', '理财产品投资', '债券投资', '同业存单', '基金投资'];
    const y2025 = [2.98, 4.58, 9.73, 15.75, 152.50, 154.39, 471.26];
    const y2024 = [3.29, 3.24, 8.57, 8.48, 149.41, 100.86, 571.70];

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
    const years = ['2024 年末', '2025 年末'];
    const l1  = [373.16, 312.50];
    const l2  = [2926.37, 3632.83];
    const l3  = [644.41, 624.28];
    const tot = [3943.94, 4569.60];

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

/* ────── 1l. 员工人数与人均效能 ────── */
(function () {
    const years15 = ['2011','2012','2013','2014','2015','2016','2017','2018',
                     '2019','2020','2021','2022','2023','2024','2025'];
    // 员工数：2011–2018 为本行口径「在岗员工」（H 股年报「員工及人力資源管理」）；2019–2025 为本集团口径「在岗员工」（A 股年报「员工和机构情况」，含子公司），2018→2019 口径切换处不连续
    const staff = [13524, 14800, 15443, 15740, 16182, 16245, 15892, 15688,
                   15653, 15431, 15270, 15167, 15017, 14542, 14266];
    // 人均营业收入/人均归母净利润 = 营业收入/归母净利润(本行历年年度报告「合并利润表」披露值) ÷ 对应口径员工数
    const perOI = [81.5, 91.6, 105.0, 125.2, 134.4, 133.6, 150.9, 166.5,
                   170.1, 182.7, 202.0, 191.1, 186.2, 194.3, 200.8];
    const perNP = [31.6, 36.2, 38.8, 43.4, 44.6, 48.9, 56.2, 57.7,
                   62.4, 54.4, 62.6, 67.7, 72.6, 79.2, 85.0];

    initChart('chart-staff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   formatter: p => {
                       const rows = p.map(s => s.seriesName + '：' + s.value +
                           (s.seriesName === '年末员工数' ? ' 人' : ' 万元/人'));
                       return p[0].axisValue + '<br>' + rows.join('<br>');
                   } },
        legend: { data: ['年末员工数', '人均营业收入', '人均归母净利润'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 66, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years15, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '员工数(人)', min: 0, nameTextStyle: { color: '#95a5a6', fontSize: 18 },
              axisLabel: { color: '#95a5a6', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '万元/人', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#555', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '年末员工数', type: 'bar', data: staff, itemStyle: { color: '#d5dbdb' },
              barWidth: '55%', z: 1 },
            { name: '人均营业收入', type: 'line', yAxisIndex: 1, data: perOI, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '人均归母净利润', type: 'line', yAxisIndex: 1, data: perNP, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
              endLabel: { show: true, fontSize: 18, color: '#e67e22', formatter: '{c}' } }
        ]
    });
})();

/* ────── 1c. 公司/个人 存贷款结构与利率 ────── */
(function () {
    const loanYears = ['2021', '2022', '2023', '2024', '2025'];
    // 公司贷款 / 零售贷款 / 票据贴现 / 合计 平均余额（亿元），取自各年年报「利息收入分析」表
    const balCorp = [2866.10, 2907.41, 3215.47, 3486.93, 4051.26];
    const balRetail = [2514.68, 2749.60, 2897.81, 2904.71, 2978.51];
    const balBill = [173.07, 467.76, 550.68, 620.59, 529.70];
    const balTotal = [5553.85, 6124.77, 6663.95, 7012.22, 7559.47];
    // 同表平均收益率（%）
    const yldCorp = [4.93, 4.68, 4.45, 4.15, 3.87];
    const yldRetail = [5.70, 5.48, 4.83, 4.21, 3.81];
    const yldBill = [2.57, 1.76, 1.51, 1.29, 0.89];
    const yldTotal = [5.20, 4.82, 4.37, 3.92, 3.64];
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
        xAxis: { type: 'category', data: loanYears, axisLabel: { fontSize: 18, color: '#555' } },
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
        xAxis: { type: 'category', data: loanYears, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '平均收益率%', min: 0, max: 6, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [yldCorp, yldRetail, yldBill, yldTotal].map(
            // 2025 年三条线收于 3.64%–3.87%，端点标签手动错开纵向位置避免相互压盖
            (d, i) => loanMixLine(loanMixNames[i], d, loanMixColors[i], '%', [-14, 8, 0, 28][i]))
    });

    // 存款期限结构：活期 vs 定期 占比（2025 年末）
    initChart('chart-depterm')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        title: [
            { text: '定期 74.27%\n活期 25.30%', left: 'center', top: 'center', textAlign: 'center',
              textStyle: { fontSize: 18, color: '#6c3483', fontWeight: 700, lineHeight: 22 } }
        ],
        tooltip: { trigger: 'item', formatter: '{b}: {c} 亿元 ({d}%)', textStyle: { fontSize: 18 } },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        series: [{
            name: '存款期限结构', type: 'pie', radius: ['46%', '68%'], center: ['50%', '52%'],
            avoidLabelOverlap: true, label: { show: true, fontSize: 18, formatter: '{b}\n{d}%' },
            data: [
                { value: 7640.86, name: '定期存款', itemStyle: { color: '#6c3483' } },
                { value: 2601.74, name: '活期存款', itemStyle: { color: '#e67e22' } },
                { value: 44.68,   name: '保证金及其他', itemStyle: { color: '#b0a0bd' } }
            ]
        }]
    });
})();

/* ────── 1c-2. 客户存款平均付息率 与 活期存款占比（历年 2019–2025） ────── */
(function () {
    const years = ['2019','2020','2021','2022','2023','2024','2025'];
    // 全行客户存款合计平均付息率（%），取自历年年报「客户存款合计」表
    const cost  = [1.93, 1.97, 1.98, 1.97, 1.88, 1.73, 1.45];
    // 活期存款占客户存款总额比重（%）= 公司活期 + 个人活期（期末）
    const demand = [35.81, 34.66, 30.48, 30.40, 26.90, 26.14, 25.30];

    initChart('chart-depcost')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   valueFormatter: v => v + '%' },
        grid: { left: 60, right: 66, top: 30, bottom: 40 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '付息率%', min: 1.3, max: 2.1,
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

/* ────── 10b. 利率重定价缺口（按重定价期限，2025 vs 2024） ────── */
(function () {
    const el = document.getElementById('chart-repricing');
    if (!el) return;
    const buckets = ['3个月以内', '3个月至1年', '1年至5年', '5年以上', '不计息'];
    // 单位：亿元（年报为人民币百万元，÷100 换算）；负值＝负债敏感（重定价负债多于资产）
    const g2025 = [-1887.4, -1359.7, 1978.1, 2250.6, 266.6];
    const g2024 = [-1747.6,  -990.3, 1649.7, 1959.0, 357.5];
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

/* ────── 1d2. 公司贷款 / 零售贷款期末余额（2012–2025） ────── */
(function () {
    const years = ['2012','2013','2014','2015','2016','2017','2018','2019',
                    '2020','2021','2022','2023','2024','2025'];
    // 期末余额（亿元）——按产品类型划分的贷款及不良贷款分布情况 / 客户贷款和垫款的构成情况
    const corp   = [1062.05,1188.17,1395.85,1653.02,1899.12,2147.53,2276.87,2547.60,
                    2736.31,2802.85,2986.87,3277.84,3581.33,4349.74];
    const retail = [ 620.98, 849.28, 971.51, 963.01, 981.82,1135.51,1332.56,1622.38,
                    2165.44,2755.55,2827.69,2909.20,2925.06,3010.22];
    // 公司贷款和垫款不良率（%）——「按产品类型划分的贷款及不良贷款分布情况」表「公司贷款和垫款」行
    const nplCorp = [0.88, 0.81, 0.92, 0.74, 0.78, 0.96, 1.59, 1.69,
                     1.94, 1.95, 1.47, 1.04, 1.04, 0.55];
    initChart('chart-loantrend')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                   formatter: ps => ps[0].axisValue + '<br>' + ps.map(p =>
                       `${p.marker}${p.seriesName}：${p.value == null ? '—'
                         : p.value + (p.seriesName === '公司贷款不良率' ? '%' : ' 亿元')}`).join('<br>') },
        legend: { data: ['公司贷款', '零售贷款', '公司贷款不良率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 60, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '不良率%', min: 0, position: 'right', nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { fontSize: 18, color: '#c0392b' }, splitLine: { show: false } }
        ],
        series: [
            { name: '公司贷款', type: 'line', data: corp, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.08)' } },
            { name: '零售贷款', type: 'line', data: retail, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' } },
            { name: '公司贷款不良率', type: 'line', yAxisIndex: 1, data: nplCorp, smooth: true, symbolSize: 6,
              lineStyle: { width: 2, color: '#c0392b', type: 'dashed' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}%' } }
        ]
    });
})();

/* ────── 1d. 个人贷款按用途细分（2018–2025） ────── */
(function () {
    const years = ['2018','2019','2020','2021','2022','2023','2024','2025'];
    // 期末余额（亿元）——按揭 / 经营 / 信用卡 全区间；消费贷 2018–2022 未单独披露
    const balMortgage = [603.74, 730.91, 913.37,1009.80, 969.65, 914.89, 886.98, 874.53];
    const balBusiness = [429.98, 505.16, 668.00, 897.96,1018.80,1201.19,1235.83,1186.22];
    const balCard     = [ 39.55,  45.06,  50.03,  91.43, 124.64, 149.99, 166.83, 167.82];
    const balConsume  = [  null,   null,   null,   null,   null, 643.12, 635.43, 781.66];

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
    const nplMortgage = [0.43, 0.33, 0.31, 0.46, 0.77, 1.11, 1.15, 1.60];
    const nplBusiness = [1.36, 0.87, 0.82, 0.73, 1.49, 2.05, 1.67, 1.97];
    const nplOthers   = [1.55, 1.23, 0.86, 0.83, 1.25, 1.49, 2.00, 2.61];

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
})();

/* ────── 3. 前十大股东 ────── */
(function () {
    if (!document.getElementById('chart-holders')) return;   // 仅业绩页
    const holders = [
        { name: '香港中央结算（代理人）',   pct: 22.08, chg: '+79.14 万股',   type: 'H 股 · 境外法人' },
        { name: '重庆渝富资本运营集团',     pct: 8.70,  chg: '不变',          type: 'A 股 · 国有法人' },
        { name: '重庆市城市建设投资集团',   pct: 7.02,  chg: '不变',          type: 'A 股 · 国有法人' },
        { name: '重庆发展置业管理',         pct: 5.19,  chg: '不变',          type: 'A 股 · 国有法人' },
        { name: '重庆市水利投资集团',       pct: 4.99,  chg: '不变',          type: 'A 股 · 国有法人' },
        { name: '重庆发展投资',             pct: 4.60,  chg: '+5,200 万股',   type: 'A 股 · 国有法人' },
        { name: '香港中央结算（沪股通）',   pct: 2.79,  chg: '-1.17 亿股',    type: 'A 股 · 境外法人' },
        { name: '重庆水务集团',             pct: 1.10,  chg: '不变',          type: 'A 股 · 国有法人' },
        { name: '重庆财信企业集团',         pct: 0.99,  chg: '-4,750 万股',   type: 'A 股 · 非国有' },
        { name: '全国社保基金一一六组合',   pct: 0.83,  chg: '+3,283 万股',   type: 'A 股 · 其他' }
    ];
    // 表格
    const tb = document.getElementById('holder-tbody');
    const chgColor = c => c === '不变' ? '#888' : (c[0] === '+' ? '#c0392b' : '#1e8449');
    tb.innerHTML = holders.map(h =>
        `<tr><td>${h.name}</td><td>${h.pct.toFixed(2)}%</td>` +
        `<td style="color:${chgColor(h.chg)}">${h.chg}</td><td style="font-size:18px;color:#777">${h.type}</td></tr>`
    ).join('');
    // 股东结构单层环形图：全部股东在同一个环、按比例铺满整圈；「其他流通股东」也按普通股东参与、严格按持股比例从大到小排序
    // 派系配色：香港中央结算 #16a085 · 渝富系 #6c3483 · 发展系 #2980b9 · 城投 #e67e22 · 财信 #c0392b · 社保 #f1c40f · 其他 #95a5a6
    const holderData = [
        { name: '其他流通股东',    value: 41.71, itemStyle: { color: '#95a5a6' } },
        { name: '香港代理人(H股)', value: 22.08, itemStyle: { color: '#16a085' } },
        { name: '渝富资本',        value: 8.70,  itemStyle: { color: '#6c3483' } },
        { name: '城投集团',        value: 7.02,  itemStyle: { color: '#e67e22' } },
        { name: '发展置业',        value: 5.19,  itemStyle: { color: '#2980b9' } },
        { name: '水利投资',        value: 4.99,  itemStyle: { color: '#6c3483' } },
        { name: '发展投资',        value: 4.60,  itemStyle: { color: '#2980b9' } },
        { name: '沪股通(A股)',     value: 2.79,  itemStyle: { color: '#16a085' } },
        { name: '水务集团',        value: 1.10,  itemStyle: { color: '#6c3483' } },
        { name: '财信集团',        value: 0.99,  itemStyle: { color: '#c0392b' } },
        { name: '社保116',         value: 0.83,  itemStyle: { color: '#f1c40f' } }
    ];
    const holderTip = { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占总股本）` };
    initChart('chart-holders')?.setOption({
        backgroundColor: '#fff',
        title: [
            { text: '前十大\n58.29%', left: 'center', top: 'center', textAlign: 'center',
              textStyle: { fontSize: 20, color: '#6c3483', fontWeight: 700, lineHeight: 24 } }
        ],
        tooltip: holderTip,
        series: [{
            type: 'pie', radius: ['40%', '74%'], center: ['50%', '54%'], startAngle: 90,
            sort: null, minShowLabelAngle: 12, avoidLabelOverlap: true,
            data: holderData,
            label: { show: true, position: 'outside', formatter: '{b}\n{c}%', fontSize: 18, color: '#333' },
            labelLine: { show: true, length: 12, length2: 10 },
            itemStyle: { borderColor: '#fff', borderWidth: 2 }
        }]
    });

    // 图外清单：确保每位股东信息清晰可读（不受扇区大小影响），按派系分组
    const factions = [
        { title: '香港中央结算', color: '#16a085', names: ['香港代理人(H股)', '沪股通(A股)'] },
        { title: '渝富系（一致行动）', color: '#6c3483', names: ['渝富资本', '水利投资', '水务集团'] },
        { title: '发展系（一致行动）', color: '#2980b9', names: ['发展置业', '发展投资'] },
        { title: '城投集团', color: '#e67e22', names: ['城投集团'] },
        { title: '财信集团', color: '#c0392b', names: ['财信集团'] },
        { title: '社保116', color: '#f1c40f', names: ['社保116'] },
        { title: '其他流通股东', color: '#95a5a6', names: ['其他流通股东'] }
    ];
    const val = n => holderData.find(d => d.name === n).value;
    document.getElementById('holders-legend').innerHTML = factions.map(f => {
        const sum = f.names.reduce((a, n) => a + val(n), 0);
        const items = f.names.map(n => `${n} ${val(n)}%`).join('　');
        return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${f.color};vertical-align:-1px;margin-right:6px"></span>` +
               `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#6c3483;font-weight:600">${sum.toFixed(2)}%</span>` +
               (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
    }).join('');

    // 「己」字形折叠条：3 行横条首尾相连成一条蛇形；三横之间的「连接段」（圆角转折）不计入占比，用灰色特殊标注。
    (function buildFold() {
        const W = 520, t = 44, m = t / 2, r = 30;      // 宽、条厚、留边、转折圆角半径
        const vg = 30;                                 // 行间距（连接段竖向跨度）
        const xL = m, xR = W - m;
        const y0 = m, y1 = y0 + t + vg, y2 = y1 + t + vg, H = y2 + m;
        const CONN = '#b7b1c4';                        // 连接段特殊色（不计入占比）

        // 三行数据段的宽度（转折圆角占掉的部分归入连接段，不计比例）
        const w1 = (xR - r) - xL;                      // 第1行：左端起，右端进圆角
        const w2 = (xR - r) - (xL + r);                // 第2行：两端都进圆角
        const w3 = xR - (xL + r);                      // 第3行：左端出圆角，右端到底
        const dataLen = w1 + w2 + w3;                  // 100% 只摊在三横上

        // 数据轨（横条），按弧长区间映射；第2行从右向左画以保持蛇形连续
        const rails = [
            { s: 0,        e: w1,           rect: (a, b) => ({ x: xL + a, y: y0 - t / 2, w: b - a }) },
            { s: w1,       e: w1 + w2,      rect: (a, b) => { const la = a - w1, lb = b - w1, xr = xR - r; return { x: xr - lb, y: y1 - t / 2, w: lb - la }; } },
            { s: w1 + w2,  e: dataLen,      rect: (a, b) => { const la = a - w1 - w2; return { x: (xL + r) + la, y: y2 - t / 2, w: b - a }; } }
        ];

        const gap = 2;                                 // 相邻股东留白
        const FS = 16;                                 // 标签字号（≥16px 下限）
        let d = 0;
        const parts = [], inside = [], callouts = [];
        holderData.forEach(hd => {
            const d0 = d, d1 = d + hd.value / 100 * dataLen;
            let best = null;
            rails.forEach(rl => {
                const a = Math.max(d0, rl.s), b = Math.min(d1, rl.e);
                if (b > a + 0.01) {
                    const rc = rl.rect(a + gap / 2, b - gap / 2);
                    if (rc.w > 0.5) {
                        parts.push({ ...rc, color: hd.itemStyle.color, name: hd.name, value: hd.value });
                        if (!best || rc.w > best.w) best = rc;   // 该股东最宽的一段
                    }
                }
            });
            if (best) {
                if (best.w > 60) {   // 段够宽，16px 文字放得下 → 段内标注
                    inside.push({ x: best.x + best.w / 2, y: best.y + t / 2, text: best.w > 240 ? `${hd.name} ${hd.value}%` : `${hd.value}%` });
                } else {             // 太窄 → 拉箭头到外面标注
                    callouts.push({ name: hd.name, value: hd.value, color: hd.itemStyle.color, ax: best.x + best.w / 2, ay: best.y + t });
                }
            }
            d = d1;
        });

        // 连接段（圆角转折，特殊色，不占比例）
        const connA = `M ${xR - r} ${y0} Q ${xR} ${y0} ${xR} ${y0 + r} L ${xR} ${y1 - r} Q ${xR} ${y1} ${xR - r} ${y1}`; // 右侧：1行→2行
        const connB = `M ${xL + r} ${y1} Q ${xL} ${y1} ${xL} ${y1 + r} L ${xL} ${y2 - r} Q ${xL} ${y2} ${xL + r} ${y2}`; // 左侧：2行→3行

        // 引出标注布局：窄段标签排到底部，按锚点从左到右打包，放不下自动换行
        const dotR = 5, rowH = 30, padX = 4;
        const estW = c => {
            let w = dotR * 2 + 10;                      // 圆点 + 间距
            for (const ch of `${c.name} ${c.value}%`) w += ch.charCodeAt(0) > 255 ? FS : FS * 0.56;
            return w + 8;
        };
        callouts.sort((a, b) => a.ax - b.ax);
        let cx = padX, row = 0;
        callouts.forEach(c => {
            const w = estW(c);
            if (cx + w > W - padX && cx > padX) { cx = padX; row++; }
            c.lx = cx; c.row = row; c.w = w;
            cx += w + 6;
        });
        const rows = callouts.length ? row + 1 : 0;
        const baseY = H + 20;                           // 第一行标签基线
        const svgH = H + (rows ? rows * rowH + 10 : 6);

        let svg = `<svg viewBox="-3 -3 ${W + 6} ${svgH + 6}" width="100%" style="max-width:760px;display:block;margin:0 auto;height:auto">`;
        [connA, connB].forEach(dstr => {
            svg += `<path d="${dstr}" fill="none" stroke="${CONN}" stroke-width="${t}" stroke-linecap="butt" stroke-linejoin="round"><title>连接段（不计入占比）</title></path>`;
        });
        parts.forEach(p => {
            svg += `<rect x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" width="${p.w.toFixed(1)}" height="${t}" fill="${p.color}" stroke="#fff" stroke-width="2"><title>${p.name}：${p.value}%（占总股本）</title></rect>`;
        });
        inside.forEach(l => {
            svg += `<text x="${l.x.toFixed(1)}" y="${l.y.toFixed(1)}" text-anchor="middle" dominant-baseline="central" font-size="${FS}" fill="#fff" font-weight="600">${l.text}</text>`;
        });
        // 引出线 + 箭头 + 外部标签（每个股东都标注）
        callouts.forEach(c => {
            const ly = baseY + c.row * rowH;             // 该标签基线
            const dotX = c.lx + dotR, dotY = ly - FS / 2 + 1;
            const ax = c.ax.toFixed(1);
            svg += `<line x1="${dotX.toFixed(1)}" y1="${(dotY - dotR).toFixed(1)}" x2="${ax}" y2="${(c.ay + 9).toFixed(1)}" stroke="${c.color}" stroke-width="1.4"/>`;
            svg += `<polygon points="${ax},${c.ay.toFixed(1)} ${(c.ax - 5).toFixed(1)},${(c.ay + 9).toFixed(1)} ${(c.ax + 5).toFixed(1)},${(c.ay + 9).toFixed(1)}" fill="${c.color}"/>`;
            svg += `<circle cx="${dotX.toFixed(1)}" cy="${dotY.toFixed(1)}" r="${dotR}" fill="${c.color}"/>`;
            svg += `<text x="${(c.lx + dotR * 2 + 6).toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="start" font-size="${FS}" fill="#333" font-weight="600">${c.name} ${c.value}%</text>`;
        });
        svg += '</svg>';
        document.getElementById('chart-holders-fold').innerHTML = svg;
    })();

    // 横向条形图：按比例排序，同派系同色；≥4% 条内显示股东名（白字），<4% 名称显示在条右侧；底部滑块可左右拉伸放大
    (function buildBar() {
        const names = holderData.map(h => h.name);
        const barData = holderData.map(h => ({
            value: h.value,
            itemStyle: { color: h.itemStyle.color },
            label: h.value >= 4
                ? { show: true, position: 'insideLeft', distance: 8, color: '#fff', fontSize: 18, fontWeight: 600, formatter: `${h.name}  ${h.value}%` }
                : { show: true, position: 'right', distance: 6, color: '#333', fontSize: 18, fontWeight: 600, formatter: `${h.name}  ${h.value}%` }
        }));
        initChart('chart-holders-bar')?.setOption({
            backgroundColor: '#fff',
            grid: { left: 14, right: 170, top: 16, bottom: 16, containLabel: true },
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${names[p.dataIndex]}：${p.value}%（占总股本）` },
            xAxis: {
                type: 'value', min: 0, max: 44, name: '占总股本 %', nameTextStyle: { fontSize: 18 },
                axisLabel: { fontSize: 18, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eee' } }
            },
            yAxis: {
                type: 'category', data: names, inverse: true,
                axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#ccc' } }
            },
            // 不加 dataZoom：股东数量有限，x 轴已固定 0-44%，一次看全
            series: [{
                type: 'bar', data: barData, barCategoryGap: '35%',
                itemStyle: { borderColor: '#fff', borderWidth: 1 }
            }]
    });
})();
})();

// 可排序表格：点击表头按该列排序，"合计"等 data-nosort 行固定在最后不参与排序。
// 数值列按 data-sort="num" 解析（去掉千分位逗号），文本列按 localeCompare。
(function initSortableTables() {
    document.querySelectorAll('table.sortable').forEach(table => {
        const headers = table.querySelectorAll('thead th');
        const tbody = table.querySelector('tbody');
        headers.forEach((th, colIndex) => {
            if (th.dataset.sort === 'none') return;   // 序号列：固定顺序，不参与排序
            th.addEventListener('click', () => {
                const type = th.dataset.sort || 'text';
                const curDir = th.dataset.sortDir;
                const dir = curDir === 'asc' ? 'desc' : 'asc';
                headers.forEach(h => delete h.dataset.sortDir);
                th.dataset.sortDir = dir;

                const rows = Array.from(tbody.querySelectorAll('tr'));
                const fixedRows = rows.filter(r => r.dataset.nosort !== undefined);
                const sortRows = rows.filter(r => r.dataset.nosort === undefined);

                sortRows.sort((ra, rb) => {
                    const a = ra.children[colIndex].textContent.trim();
                    const b = rb.children[colIndex].textContent.trim();
                    let cmp;
                    if (type === 'num') {
                        cmp = parseFloat(a.replace(/,/g, '')) - parseFloat(b.replace(/,/g, ''));
                    } else {
                        cmp = a.localeCompare(b, 'zh-Hans-CN');
                    }
                    return dir === 'asc' ? cmp : -cmp;
                });

                sortRows.concat(fixedRows).forEach(r => tbody.appendChild(r));
            });
        });
    });
})();

/* ────── 6. 分部信息 ────── */
(function () {
    const segs = ['公司金融', '零售金融', '金融市场', '未分配'];
    const rev25 = [9351.1, 12138.5, 7027.0, 103.4];
    const rev24 = [8633.8, 11832.4, 7699.2, 65.9];
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
        xAxis: { type: 'category', data: ['存款', '贷款', '资产'], axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', max: 100, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '县域', type: 'bar', stack: 'geo', data: [73.30, 50.78, 52.60], itemStyle: { color: '#1e8449' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } },
            { name: '主城', type: 'bar', stack: 'geo', data: [26.70, 49.22, 47.40], itemStyle: { color: '#e67e22' },
              label: { show: true, position: 'inside', fontSize: 18, color: '#fff', formatter: '{c}%' } }
        ]
    });
})();

/* ────── 7. 贷款行业分布 ────── */
(function () {
    const inds = ['租赁商务', '水利环境', '制造业', '交通仓储', '批发零售', '电力燃气', '建筑业', '房地产', '卫生社会', '农林牧渔', '其他'];
    const bal25 = [112105.4, 82317.3, 78384.5, 43794.5, 30826.3, 30683.1, 18149.8, 7226.6, 6375.5, 5858.1, 19253.3];
    const bal24 = [93852.9, 65673.1, 76096.3, 34806.5, 21350.0, 27601.5, 11911.1, 4422.4, 6828.8, 3893.2, 11697.6];
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

/* ────── 8. 五级分类 ────── */
(function () {
    initChart('chart-5tier')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: '{b}: {c} 百万 ({d}%)' },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['36%', '64%'], center: ['50%', '48%'],
            label: { show: true, fontSize: 18, formatter: '{b}\n{d}%' },
            data: [
                { value: 777351.2, name: '正常', itemStyle: { color: '#1e8449' } },
                { value: 11346.4,  name: '关注', itemStyle: { color: '#f39c12' } },
                { value: 3759.4,   name: '次级', itemStyle: { color: '#e67e22' } },
                { value: 2888.4,   name: '可疑', itemStyle: { color: '#c0392b' } },
                { value: 1941.6,   name: '损失', itemStyle: { color: '#7b241c' } }
            ]
        }]
    });
})();

/* ────── 8b. 贷款迁徙率（渝农商行 2019–2025，正常类对比农业银行 2010–2023） ────── */
(function () {
    // 渝农商行: 2019-2025 逐年迁徙率(%), 取自历年A股年报「贷款迁徙率」表 (dfcfw.com PDF, pdftotext -layout 抽取)
    // 2019/2020 已按银保监发[2022]2号文追溯调整口径; 相邻年报重叠年份数值已交叉核对一致, 2026-08-14 提取核对
    const yrsMigrate = ['2019', '2020', '2021', '2022', '2023', '2024', '2025'];
    initChart('chart-migrate')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: yrsMigrate, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '关注类', type: 'line', data: [9.64, 49.53, 60.98, 38.49, 26.60, 31.39, 19.73], symbolSize: 7, lineStyle: { width: 3, color: '#f39c12' }, itemStyle: { color: '#f39c12' } },
            { name: '次级类', type: 'line', data: [21.36, 10.89, 65.23, 29.81, 51.25, 41.55, 73.54], symbolSize: 7, lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' } },
            { name: '可疑类', type: 'line', data: [2.67, 2.04, 1.78, 2.77, 16.98, 19.75, 36.21], symbolSize: 7, lineStyle: { width: 2.5, color: '#7b241c', type: 'dashed' }, itemStyle: { color: '#7b241c' } }
        ]
    });

    // 正常类迁徙率对比: 渝农商行(2019-2025) vs 农业银行(2010-2023, 历年A股年报摘要/全文「其他财务指标」表)
    // 农行2017取自2019年报追溯值2.13%(非2017半年报摘要的年中数2.00%); 2018/2019两年在2019/2020两份年报重叠核对一致
    // 2021取2023年报口径1.10%(与2022/2023同表可比); 2024/2025年报未检索到该表，序列止于2023
    const yrsNormal = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025'];
    const ynshbNormal = [null,null,null,null,null,null,null,null,null,1.70,3.20,1.93,1.54,1.43,1.73,1.31];
    const abcNormal   = [3.10,2.26,2.49,2.53,3.60,4.96,3.00,2.13,1.72,1.54,3.19,1.10,1.30,1.39,null,null];
    initChart('chart-migrate-normal')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['渝农商行', '农业银行'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: yrsNormal, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '渝农商行', type: 'line', data: ynshbNormal, connectNulls: false, symbolSize: 7, lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '农业银行', type: 'line', data: abcNormal, connectNulls: false, symbolSize: 6, lineStyle: { width: 2.5, color: '#2980b9', type: 'dashed' }, itemStyle: { color: '#2980b9' } }
        ]
    });
})();


/* ────── 13. NIM 分解 ────── */
(function () {
    const items = ['贷款3.64%', '金融投资2.73%', '央行1.60%', '同业1.93%', '生息资产3.06%', '存款1.45%', '央行借款1.86%', '同业1.66%', '债券1.87%', '计息负债1.55%'];
    const rate25 = [3.64, 2.73, 1.60, 1.93, 3.06, 1.45, 1.86, 1.66, 1.87, 1.55];
    const rate24 = [3.92, 3.08, 1.57, 2.25, 3.37, 1.73, 2.20, 2.05, 2.28, 1.86];
    initChart('chart-nim')?.setOption({
        backgroundColor: '#fff', textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v + '%' },
        legend: { data: ['2025 收益率/成本率', '2024 收益率/成本率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 56 },
        xAxis: { type: 'category', data: items, axisLabel: { fontSize: 18, color: '#555', rotate: 35 } },
        yAxis: { type: 'value', name: '%', min: 0, max: 5, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '2025 收益率/成本率', type: 'bar', data: rate25, itemStyle: { color: '#6c3483' },
              label: { show: true, position: 'top', fontSize: 18, formatter: '{c}%' } },
            { name: '2024 收益率/成本率', type: 'bar', data: rate24, itemStyle: { color: '#b39ddb' } }
        ]
    });
})();

/* ────── 5-② 资产负债表结构 (2025) ────── */
(function () {
    const assets = [
        { name: '客户贷款和垫款（净额）', value: 765892.7 },
        { name: '金融投资',             value: 643629.0 },
        { name: '存放同业及拆出资金',    value: 142441.0 },
        { name: '现金及存放中央银行',    value:  55091.0 },
        { name: '买入返售金融资产',      value:  34197.0 },
        { name: '其他资产',             value:  24493.4 }
    ];
    const claims = [
        { name: '客户存款',             value: 1028727.5 },
        { name: '其他负债',             value:  497720.8 },
        { name: '归属于本行股东权益',    value:  137126.7 },
        { name: '少数股东权益',          value:    2169.1 }
    ];
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
        series: [{ type: 'bar', data: [22569.6, -19134.4, 15532.8, -18595.7], barWidth: '48%',
            itemStyle: { color: p => p.value >= 0 ? '#8e44ad' : '#e74c3c', borderRadius: [4,4,0,0] },
            label: { show: true, position: 'top', fontSize: 18,
                     formatter: p => Number(p.value).toLocaleString() } }]
    });
})();

window.addEventListener('resize', () => {
    document.querySelectorAll('.chart').forEach(el => {
        const inst = echarts.getInstanceByDom(el);
        if (inst) inst.resize();
    });
});

/* ────── intro.html · 员工岗位结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-role')) return;
    // 数据来源：2025 年报「第四章 五、（一）员工情况」PDF 第 119 页；本行口径合计 13,853 人
    const roles = [
        { value: 10411, name: '业务发展' },
        { value:  1834, name: '运营及综合管理' },
        { value:  1025, name: '风险控制' },
        { value:   583, name: '科技信息' }
    ];
    initChart('chart-staff-role')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: roles,
            color: ['#6c3483', '#af7ac5', '#c0392b', '#e67e22']
        }]
    });
})();

/* ────── intro.html · 员工学历结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-edu')) return;
    const edu = [
        { value: 10413, name: '本科' },
        { value:  2212, name: '专科及以下' },
        { value:  1228, name: '硕士研究生及以上' }
    ];
    initChart('chart-staff-edu')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: edu,
            color: ['#6c3483', '#95a5a6', '#af7ac5']
        }]
    });
})();

/* ────── intro.html · 历年董事长 / 行长薪酬披露（2010-2025，税前，万元） ──────
 * 2010-2018: H股03618年报「董事、监事及高级管理层人员」章节；2019-2025: A股601077年报「公司治理报告」章节。
 * 董事长换人：2022年4月刘建忠→谢文辉；2024年10月谢文辉离任后行长隋军代行董事长职务
 * （年报"董事长及行长"章节原文："谢文辉先生于2024年10月离任后，董事会推举隋军先生代行董事长职务"，
 * 2025年"隋军...并经董事会推举短暂代行董事长职务"），2024/2025两年董事长栏均取隋军的行长薪酬数
 * （年报薪酬表职务栏对代行期间未单列"代行董事长"报酬，隋军实际以行长身份领取同一份薪酬）；
 * 2026-01-08刘小军任职资格获监管核准，但2025年度隋军仍是全年代行董事长的实际人选，故2025年
 * 董事长栏仍用隋军59.75万元，刘小军42.07万元(候任身份取得)在图中不作为该年"董事长"代表数值。
 * 行长换人：2013年12月谭远胜退休→谢文辉（任职资格待核准，2013年谢文辉当年确实未在任何身份下
 * 领取报酬，年报本身未披露任何数字，非因职务代行而留空，故该点保留空缺并在note注明原因）；
 * 2014-2023年3月为谢文辉；2023年4月起为隋军。
 * 注意：2010-2021年董事长(刘建忠)与行长(谢文辉/谭远胜)始终是两个不同的人，2014年报"董事长及行长"
 * 一节原文强调"角色相互分立"；"一人兼两职"发生在2022年(谢文辉升任董事长兼行长)及2024-2025年
 * (隋军以行长身份代行董事长职务)——这几年两条线数值相同，图上用虚线叠画并标注"一人兼两职/代行"。
 * 各年数值均为年报"税前薪酬合计"列，历年年报均注明非最终考核数。 */
(function () {
    if (!document.getElementById('chart-chairman-pay')) return;
    const years = ['2010','2011','2012','2013','2014','2015','2016','2017','2018',
                    '2019','2020','2021','2022','2023','2024','2025'];
    const chairmanNames = ['刘建忠','刘建忠','刘建忠','刘建忠','刘建忠','刘建忠','刘建忠','刘建忠','刘建忠',
                    '刘建忠','刘建忠','刘建忠','谢文辉','谢文辉','隋军(代行)','隋军(代行)'];
    const chairmanPay   = [ 77.4, 90.5,111.7,121.7,130.4, 77.3, 34.6, 42.0, 79.6,
                     49.14, 44.58, 52.04, 52.79, 54.29, 59.75, 60.84];
    // 2013 谢文辉当年刚获聘行长、任职资格未获监管核准，年报本身未披露其任何报酬数（非代行职务留空，是确无数据）
    const presidentNames = ['谭远胜','谭远胜','谭远胜','谭远胜','谢文辉','谢文辉','谢文辉','谢文辉','谢文辉',
                    '谢文辉','谢文辉','谢文辉','谢文辉(兼董事长)','隋军','隋军(代行董事长)','隋军(代行董事长)'];
    const presidentPay   = [ 77.4, 89.9,111.8, null, 79.4, 77.8, 34.6, 42.0, 90.8,
                     49.14, 44.58, 52.04, 52.79, 43.38, 59.75, 60.84];
    // 一人兼两职/代行区间：2022(谢文辉兼)、2024-2025(隋军代行)。用虚线线型标注这些年两条线数值相同
    const dashedIdx = new Set([12, 14, 15]);

    initChart('chart-chairman-pay')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` + p.map(x => {
                const idx = x.dataIndex;
                const who = x.seriesIndex === 0 ? chairmanNames[idx] : presidentNames[idx];
                const note = dashedIdx.has(idx) ? '（一人兼两职/代行）' : '';
                return x.value == null ? '' : `${x.marker}${x.seriesName}（${who}）${note}：${x.value} 万元`;
            }).filter(Boolean).join('<br>') },
        legend: { data: ['董事长', '行长'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 52, bottom: 40 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '万元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            {
                name: '董事长', type: 'line', data: chairmanPay, smooth: true, symbolSize: 8,
                lineStyle: {
                    width: 2.5, color: '#c9a24a',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#c9a24a' },
                markLine: {
                    symbol: 'none', silent: true,
                    lineStyle: { color: '#999', type: 'dashed', width: 1 },
                    label: { fontSize: 16, color: '#888', formatter: p => p.name },
                    data: [
                        { xAxis: '2022', name: '谢文辉接任' },
                        { xAxis: '2024', name: '隋军代行' }
                    ]
                },
                label: { show: true, position: 'top', fontSize: 15, color: '#8a6d1f', formatter: '{c}' }
            },
            {
                name: '行长', type: 'line', data: presidentPay, smooth: true, symbolSize: 8,
                connectNulls: true,   // 仅2013年谢文辉当年确无薪酬数据(非代行留空), 跨越该点连线并在note说明
                lineStyle: {
                    width: 2.5, color: '#2980b9',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#2980b9' },
                label: { show: true, position: 'bottom', fontSize: 15, color: '#1f618d',
                         formatter: p => p.value == null ? '' : p.value }
            }
        ]
    });
})();

/* ────── intro.html · 员工年龄结构（横向堆叠条） ────── */
(function () {
    if (!document.getElementById('chart-staff-age')) return;
    const buckets = ['30 岁以下', '31–40 岁', '41–50 岁', '51 岁以上'];
    const vals    = [1515, 6431, 3351, 2556];
    const total   = vals.reduce((s, v) => s + v, 0);
    initChart('chart-staff-age')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            textStyle: { fontSize: 18 },
            formatter: p => {
                const x = p[0];
                const pct = (x.value / total * 100).toFixed(1);
                return `<b>${x.axisValue}</b><br>${x.marker}人数：${x.value.toLocaleString()} 人（${pct}%）`;
            } },
        grid: { left: 100, right: 60, top: 20, bottom: 40 },
        xAxis: { type: 'value', name: '人数', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: buckets, inverse: true,
                 axisLabel: { fontSize: 18, color: '#333' } },
        series: [{
            type: 'bar', data: vals,
            itemStyle: { color: '#6c3483' },
            barWidth: 26,
            label: { show: true, position: 'right', fontSize: 17, color: '#333',
                formatter: p => `${p.value.toLocaleString()}（${(p.value / total * 100).toFixed(1)}%）` }
        }]
    });
})();

/* ────── debt.html · 到期期限结构（金融资产 vs 金融负债，2025 年末，7 档） ──────
 * 数据来源：2025 年报财务报表附注「金融风险管理 · 流动性风险 · (1) 剩余到期日分析」
 * PDF 第 131–133 页；单位：亿元（原表为人民币千元，÷100,000 换算）。
 * 报告未披露 Macaulay / 修正久期数值——本行利率风险计量采用重定价缺口 + 敏感性 + 情景分析。
 */
(function () {
    if (!document.getElementById('chart-maturity')) return;
    const buckets = ['逾期/无期限', '即期偿还', '1 个月内', '1–3 个月', '3 个月至 1 年', '1–5 年', '5 年以上'];
    // 2025-12-31 金融资产 / 金融负债（亿元）
    const asset2025 = [ 572.93,   453.99,   953.75,   958.57, 3706.18, 5156.38, 4633.39];
    const debt2025  = [   0.00,  2963.90,  2349.41,  2955.91, 5020.12, 1891.77,    5.90];
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


/* ────── 0. 宏观背景：社会融资规模 TSF（2015–2026.7，人民银行调查统计司月度） ────── */
(function () {
    if (!document.getElementById('chart-tsf-stock')) return;  // 非本页跳过

    /* ---------- 数据（139 月，2015-01 → 2026-07） ---------- */
    const months     = ['2015-01','2015-02','2015-03','2015-04','2015-05','2015-06','2015-07','2015-08','2015-09','2015-10','2015-11','2015-12','2016-01','2016-02','2016-03','2016-04','2016-05','2016-06','2016-07','2016-08','2016-09','2016-10','2016-11','2016-12','2017-01','2017-02','2017-03','2017-04','2017-05','2017-06','2017-07','2017-08','2017-09','2017-10','2017-11','2017-12','2018-01','2018-02','2018-03','2018-04','2018-05','2018-06','2018-07','2018-08','2018-09','2018-10','2018-11','2018-12','2019-01','2019-02','2019-03','2019-04','2019-05','2019-06','2019-07','2019-08','2019-09','2019-10','2019-11','2019-12','2020-01','2020-02','2020-03','2020-04','2020-05','2020-06','2020-07','2020-08','2020-09','2020-10','2020-11','2020-12','2021-01','2021-02','2021-03','2021-04','2021-05','2021-06','2021-07','2021-08','2021-09','2021-10','2021-11','2021-12','2022-01','2022-02','2022-03','2022-04','2022-05','2022-06','2022-07','2022-08','2022-09','2022-10','2022-11','2022-12','2023-01','2023-02','2023-03','2023-04','2023-05','2023-06','2023-07','2023-08','2023-09','2023-10','2023-11','2023-12','2024-01','2024-02','2024-03','2024-04','2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11','2024-12','2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07','2025-08','2025-09','2025-10','2025-11','2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07'];
    const stock      = [null,null,127.68,null,null,131.7,null,null,134.7,null,null,138.28,141.57,142.52,144.75,145.59,146.33,147.99,148.37,149.81,151.51,152.43,154.35,156,159.61,160.69,162.8,164.14,165.17,166.86,167.95,169.36,171.14,172.11,173.66,174.71,185.77,186.92,188.37,190.02,190.94,192.37,193.46,195.24,197.27,197.89,199.29,200.75,231.55,232.41,235.24,236.81,238.5,241.05,242.19,244.31,246.68,247.42,249.27,251.41,256.34,257.17,262.27,265.22,268.38,271.78,273.33,276.73,280.05,281.25,283.25,284.75,289.74,291.36,294.56,296.15,297.98,301.56,302.47,305.29,308.05,309.45,311.9,314.12,320.03,321.12,325.63,326.47,329.2,334.28,334.9,337.22,340.65,341.42,343.19,344.22,350.93,353.97,359.02,359.95,361.42,365.45,365.77,368.61,372.5,374.17,376.39,378.08,384.32,385.71,390.32,389.93,391.93,395.1,395.72,398.56,402.19,403.45,405.6,408.34,415.19,417.29,422.97,424,426.16,430.24,431.25,433.65,437.08,437.71,440.07,442.12,449.11,451.4,456.46,456.88,458.81,462.06,463.27];
    const yoy        = [null,null,13.1,null,null,12,null,null,12.5,null,null,12.5,13.1,12.7,13.4,13.1,12.6,12.4,12.2,12.3,12.5,12.8,13.3,12.8,12.7,12.8,12.5,12.7,12.9,12.8,13.2,13.1,13,12.9,12.5,12,12.7,12.7,11.9,11.9,11.6,11.1,10.8,10.8,10.6,10.2,9.9,9.8,10.9,10.6,11.2,10.8,11,11.2,10.8,10.7,10.7,10.6,10.7,10.7,10.7,10.7,11.5,12,12.5,12.8,12.9,13.3,13.5,13.7,13.6,13.3,13,13.3,12.3,11.7,11,11,10.7,10.3,10,10,10.1,10.3,10.5,10.2,10.5,10.2,10.5,10.8,10.7,10.5,10.6,10.3,10,9.6,9.4,9.9,10,10,9.5,9,8.9,9,9,9.3,9.4,9.5,9.5,9,8.7,8.3,8.4,8.1,8.2,8.1,8,7.8,7.8,8,8,8.2,8.4,8.7,8.7,8.9,9,8.8,8.7,8.5,8.5,8.3,8.2,8.2,7.9,7.8,7.7,7.4,7.4];
    const flow_total = [20516,13609,12433,10582,12397,18384,7511,11097,13571,5593,10255,18114,34758,8312,23931,7809,6770,16479,4791,14605,17115,8865,18328,16397,36970,10908,21186,13880,10631,17718,11956,14895,18335,10357,16128,11481,30793,11894,15848,17761,9518,14877,12254,19391,21691,7420,15239,15898,46791,9665,29602,16710,17124,26243,12872,21956,25142,8680,19937,22013,50535,8737,51838,31027,31866,34681,16928,35853,34693,13929,21355,16476,51884,17243,33762,18570,19522,37017,10752,29893,29026,16176,25983,23580,61759,12170,46565,9327,28415,51926,7785,24712,35411,9134,19837,13063,59956,31610,53867,12249,15560,42265,5366,31279,41326,18441,24554,19326,64734,14959,48335,-658,20623,32985,7707,30323,37635,14120,23288,28537,70546,22331,58961,11599,22900,42251,11307,25660,35299,8178,24926,22132,72185,23837,52240,6238,20293,33671,14017];
    const rmb_loans  = [14708,11437,9920,8045,8510,13240,5890,7756,10417,5574,8873,8323,25370,8105,13176,5642,9374,13141,4550,7969,12628,6010,8463,9943,23133,10317,11586,10806,11780,14474,9152,11466,11885,6635,11428,5769,26850,10199,11425,10987,11396,16787,12861,13140,14341,7141,12302,9281,35668,7641,19584,8733,11855,16737,8086,13045,17612,5470,13633,10770,34924,7202,30390,16239,15502,19029,10221,14201,19171,6663,15309,11458,38182,13413,27511,12840,14294,23182,8391,12713,17755,7752,13021,10350,41988,9084,32291,3616,18230,30540,4088,13344,25686,4431,11448,14401,49314,18184,39487,4431,12219,32413,364,13412,25369,4837,11120,11092,48401,9773,32920,3349,8197,21927,-808,10411,19742,2965,5216,8402,52194,6528,38234,884,5923,23600,-4296,6253,16081,-154,4096,9804,49016,8458,31522,-4006,4965,17650,-5896];
    const gov_bonds  = [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,0,108,662,808,1012,1019,1851,4106,7389,868,-332,362,1700,4347,3412,4433,3857,6867,6427,5059,3777,1871,1716,3738,7613,1824,6344,3357,11362,7450,5459,13788,10116,4931,4000,6973,2437,1017,3131,3739,6701,7508,1820,9738,8066,6167,8158,11674,6026,2722,7074,3912,10582,16216,3998,3045,5533,2791,6520,2809,4140,8138,6015,4548,5571,5371,4109,11759,9920,15638,11512,9324,2947,6011,4626,-937,12266,8476,6881,16177,15357,10495,13089,17566,6933,16939,14866,9729,14585,13508,12482,13672,11893,4852,12077,6833,9764,14014,11658,9041,12236,7683,13176];
    const corp_bonds = [1868,716,1344,1616,1710,2132,2832,3121,3805,3331,3378,3535,5083,1386,7081,2366,-250,2008,2208,3236,2872,2192,3859,-2016,-510,-1125,129,501,-2488,-169,2621,1137,1654,1482,853,337,1222,644,3536,4047,-382,1349,2195,3402,382,1476,3127,3757,4829,875,3546,3949,1033,1439,2944,3384,2431,2032,3330,3593,3967,3894,9931,9237,2879,3686,2358,3659,1316,2263,840,-281,3917,1356,3807,3624,-1077,3927,3091,4649,1137,2261,4006,2167,5838,3610,3750,3652,366,2346,960,1512,345,2413,604,-4887,1638,3662,3357,2940,-2144,2249,1290,2788,650,1178,1388,-2741,4320,1423,4237,1707,285,2100,2036,1703,-1926,987,2381,-159,4454,1702,-905,2340,1496,2422,2748,1338,136,2500,4145,1541,5033,1522,3910,4520,1680,4012,4536];
    const und_ba     = [1946,-592,-910,-74,961,-1028,-3317,-1577,-1279,-3697,-2545,1546,1327,-3705,173,-2776,-5067,-2720,-5118,-376,-2230,-1801,1171,1606,6130,-1719,2390,345,-1245,-230,-2037,242,784,12,15,676,1437,106,-323,1454,-1741,-3649,-2744,-779,-548,-453,-127,1023,3787,-3103,1365,-357,-768,-1311,-4562,157,-431,-1053,570,951,1403,-3961,2818,577,836,2190,-1130,1441,1503,-1089,-625,-2216,4902,639,-2296,-2152,-926,-221,-2316,127,14,-886,-383,-1419,4733,-4228,287,-2557,-1068,1066,-2744,3486,132,-2156,191,-554,2963,-69,1792,-1345,-1795,-691,-1963,1129,2397,-2536,202,-1865,5636,-3686,3552,-4490,-1331,-2045,-1075,651,1312,-1396,910,-1330,4654,-2987,3632,-2794,-1164,-1900,-1638,1973,3234,-2895,1488,-1492,6293,-1755,1258,-5284,-685,-1084,-530];
    const trust_ln   = [52,38,-77,-46,-195,536,99,317,-159,-201,-301,370,552,308,732,269,121,809,210,736,1057,530,1625,1643,3175,1062,3113,1473,1812,2481,1232,1143,2368,1019,1434,2245,455,660,-357,-94,-904,-1623,-1192,-688,-909,-1273,-467,-509,345,-37,528,129,-52,15,-676,-658,-672,-624,-673,-1092,432,-540,-21,23,-337,-852,-1367,-316,-1159,-875,-1387,-4620,-842,-936,-1791,-1328,-1295,-1046,-1571,-1362,-2098,-1061,-2190,-4553,-680,-751,-259,-615,-619,-828,-398,-472,-191,-61,-365,-764,-62,66,-45,119,303,-154,230,-221,402,393,197,347,732,571,681,142,224,748,-26,484,6,172,91,151,623,-330,238,-77,173,816,149,350,62,155,843,679,-4,310,-173,-129,53,-503,-226];
    const entrust    = [832,1299,1111,344,324,1414,1137,1198,2422,1390,910,3530,2175,1650,1660,1694,1566,1721,1775,1432,1451,725,1994,4011,3136,1172,2039,-48,-278,-32,163,-82,775,43,280,601,-714,-750,-1850,-1481,-1570,-1642,-950,-1207,-1432,-949,-1310,-2210,-699,-508,-1070,-1197,-631,-827,-987,-513,-22,-667,-959,-1316,-26,-356,-588,-579,-273,-484,-152,-415,-317,-174,-31,-559,91,-100,-42,-213,-408,-474,-151,177,-22,-173,35,-416,428,-74,107,-2,-132,-380,89,1755,1508,470,-88,-101,584,-77,175,83,35,-56,8,97,208,-429,-386,-43,-359,-172,-465,89,-9,-3,345,25,392,-219,-183,-20,449,-228,-165,-2,-166,-400,-177,-165,283,1654,-187,308,-192,-181,-284,-283,-90,243,-22];
    const equity     = [526,542,639,597,584,1051,615,479,349,121,568,1518,1469,810,562,951,1073,1158,1135,1075,1368,1125,861,828,1225,570,800,769,458,487,536,653,519,601,1324,817,500,379,404,533,438,258,175,141,272,176,200,130,289,119,122,262,259,153,593,256,289,180,524,432,609,449,198,315,353,538,1215,1282,1141,927,771,1126,991,693,783,814,717,956,938,1478,772,846,1294,1851,1439,585,958,1166,292,589,1437,1251,1022,788,788,1443,964,571,614,993,753,700,786,1036,326,321,359,508,422,114,227,186,111,154,231,132,128,284,428,484,473,76,412,391,152,203,505,456,499,695,341,559,291,454,428,835,298,628,1128];

    /* 只在每年 1 月显示年份 */
    const xLabel = { fontSize: 18, color: '#555',
        formatter: (v, i) => (v.slice(-2) === '01' ? v.slice(0, 4) : ''),
        interval: 0 };

    /* ---------- 图 1：存量 + 同比 ---------- */
    initChart('chart-tsf-stock')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                const d = p[0].axisValue;
                let s = `<b>${d}</b>`;
                p.forEach(x => {
                    if (x.value == null) return;
                    const unit = x.seriesName === '同比 YoY' ? '%' : ' 万亿';
                    s += `<br>${x.marker}${x.seriesName}：${x.value}${unit}`;
                });
                return s;
            } },
        legend: { data: ['社融存量', '同比 YoY'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 64, top: 42, bottom: 40 },
        xAxis: { type: 'category', data: months, boundaryGap: false,
            axisLabel: xLabel, axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: [
            { type: 'value', name: '万亿元', min: 0, nameTextStyle: { fontSize: 18, color: '#555' },
              axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: 'YoY %', min: 0, max: 16, nameTextStyle: { fontSize: 18, color: '#c0392b' },
              axisLabel: { fontSize: 18, color: '#c0392b', formatter: '{value}%' }, splitLine: { show: false } }
        ],
        series: [
            { name: '社融存量', type: 'line', data: stock, connectNulls: true,
              yAxisIndex: 0, showSymbol: false, smooth: true,
              lineStyle: { width: 2.5, color: '#6c3483' }, itemStyle: { color: '#6c3483' },
              areaStyle: { color: 'rgba(108,52,131,0.10)' } },
            { name: '同比 YoY', type: 'line', data: yoy, connectNulls: true,
              yAxisIndex: 1, showSymbol: false, smooth: true,
              lineStyle: { width: 2, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              markLine: { silent: true, symbol: 'none', label: { show: false },
                data: [
                    { xAxis: '2018-07', lineStyle: { color: '#999', type: 'dashed' },
                      label: { show: true, formatter: '2018.07\nABS+核销', position: 'insideEndTop', fontSize: 14, color: '#666' } },
                    { xAxis: '2018-09', lineStyle: { color: '#999', type: 'dashed' },
                      label: { show: true, formatter: '2018.09\n政府专项债', position: 'insideEndBottom', fontSize: 14, color: '#666' } },
                    { xAxis: '2020-03', lineStyle: { color: '#999', type: 'dashed' },
                      label: { show: true, formatter: '2020Q1\n疫情信用扩张', position: 'insideEndTop', fontSize: 14, color: '#666' } },
                    { xAxis: '2023-01', lineStyle: { color: '#999', type: 'dashed' },
                      label: { show: true, formatter: '2023\n三类非存款金融纳入', position: 'insideEndBottom', fontSize: 14, color: '#666' } }
                ] } }
        ]
    });

    /* ---------- 图 2：当月新增分项（堆叠柱 + 总量线） ---------- */
    /* 分项配色：贷款主体走紫，政府债走橙，企业债走蓝，影子银行三剑客走灰，其他走浅色 */
    initChart('chart-tsf-flow')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
            formatter: p => {
                const d = p[0].axisValue;
                let s = `<b>${d}</b>`;
                // 从大到小排
                p.filter(x => x.value != null && x.value !== 0)
                 .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
                 .forEach(x => { s += `<br>${x.marker}${x.seriesName}：${Number(x.value).toLocaleString()} 亿`; });
                return s;
            } },
        legend: { top: 4, textStyle: { fontSize: 18 },
            data: ['人民币贷款','政府债券','企业债券','未贴现票据','委托贷款','信托贷款','非金融企业股票','社融合计'] },
        grid: { left: 80, right: 24, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: months, axisLabel: xLabel,
            axisLine: { lineStyle: { color: '#bbb' } } },
        yAxis: { type: 'value', name: '亿元', nameTextStyle: { fontSize: 18, color: '#555' },
            axisLabel: { fontSize: 18, color: '#555',
                formatter: v => (Math.abs(v) >= 10000 ? (v / 10000).toFixed(1) + '万' : v) },
            splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '人民币贷款',   type: 'bar', stack: 'flow', data: rmb_loans,
              itemStyle: { color: '#6c3483' } },
            { name: '政府债券',     type: 'bar', stack: 'flow', data: gov_bonds,
              itemStyle: { color: '#e67e22' } },
            { name: '企业债券',     type: 'bar', stack: 'flow', data: corp_bonds,
              itemStyle: { color: '#2980b9' } },
            { name: '未贴现票据',   type: 'bar', stack: 'flow', data: und_ba,
              itemStyle: { color: '#7f8c8d' } },
            { name: '委托贷款',     type: 'bar', stack: 'flow', data: entrust,
              itemStyle: { color: '#95a5a6' } },
            { name: '信托贷款',     type: 'bar', stack: 'flow', data: trust_ln,
              itemStyle: { color: '#bdc3c7' } },
            { name: '非金融企业股票', type: 'bar', stack: 'flow', data: equity,
              itemStyle: { color: '#af7ac5' } },
            { name: '社融合计',     type: 'line', data: flow_total, showSymbol: false, smooth: false,
              lineStyle: { width: 2, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              z: 5 }
        ]
    });
})();
