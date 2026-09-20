/* 业绩与盈利：营收/净利、规模与资产质量、OCI、每股指标、NIM 分解。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
(function () {
    const years   = D['perf'].years;
    // 2009 年营业收入 56.77 亿、净利润 18.88 亿：取自本行 2010 年 12 月 H 股招股章程 Appendix IB 会计师报告（重组后口径）
    // 2010/2011 归母净利润按 H 股年报「歸屬於本行股東的淨利潤」原文修正为 30.64/42.47 亿（此前误取衍生值 31.13/42.71）
    const revenue = D['perf'].revenue;
    const profit  = D['perf'].profit;
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

/* 1.1b ROE：渲染逻辑已提到文件顶部 window.__renderRoe（供快速切换银行按钮复用） */
window.__renderRoe(D);
});

__section(function (D, SELF, notes) {
(function () {
    const years = D['scale-dep'].years;
    const deposit = D['scale-dep'].deposit;
    const loan    = D['scale-dep'].loan;
    const npl     = D['scale-dep'].npl;
    const nplAbc  = D['scale-dep'].nplAbc;
    const nplCmb  = D['scale-dep'].nplCmb;
    const nplPsb  = D['scale-dep'].nplPsb;          // 邮储银行 不良率%
    const overdue    = D['scale-dep'].overdue;      // 逾期率%（渝农商行）2014 起披露
    const overdueAbc = D['scale-dep'].overdueAbc;   // 农业银行
    const overdueCmb = D['scale-dep'].overdueCmb;   // 招商银行
    const overduePsb = D['scale-dep'].overduePsb;   // 邮储银行
    const overdueAmt = D['scale-dep'].overdueAmt;   // 逾期贷款总额（亿元）
    const nplAmt     = D['scale-dep'].nplAmt;       // 不良贷款余额（亿元）
    const woRate     = D['scale-dep'].writeoffRate;     // 核销率% = 本期核销 ÷ 贷款总额（渝农商行）2018 起披露
    const woRateAbc  = D['scale-dep'].writeoffRateAbc;  // 农业银行
    const woRateCmb  = D['scale-dep'].writeoffRateCmb;  // 招商银行
    const woRatePsb  = D['scale-dep'].writeoffRatePsb;  // 邮储银行
    const formation    = D['scale-dep'].formation;     // 不良生成率%（渝农商行）2018 起披露
    const formationAbc = D['scale-dep'].formationAbc;  // 农业银行
    const formationCmb = D['scale-dep'].formationCmb;  // 招商银行
    const formationPsb = D['scale-dep'].formationPsb;  // 邮储银行
    const car     = D['scale-dep'].car;
    const cet1    = D['scale-dep'].cet1;

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

    // 存款、贷款各占一张图、各自回归；expOnly 时只画指数回归（存款图），否则指数 + 线性两条
    function makeScaleChart(domId, label, vals, key, color, areaColor, expOnly) {
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
                           (expOnly ? '' : `<br>　线性趋势 ${lin.fit[i].toLocaleString()} 亿 · 偏离 ${dev(lin)}`);
                } },
            legend: { data: expOnly ? [label, '指数回归'] : [label, '指数回归', '线性回归'],
                      bottom: 2, textStyle: { fontSize: 18 } },
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
                      formatter: expOnly ? `年均 +${(exp.cagr * 100).toFixed(2)}%` : `指数 ${exp.rate}` } },
                expOnly ? null :
                { name: '线性回归', type: 'line', data: lin.fit, symbol: 'none', z: 3, silent: true,
                  lineStyle: { width: 2, type: 'dotted', color: '#7f8c8d' }, itemStyle: { color: '#7f8c8d' },
                  endLabel: { show: true, fontSize: 18, color: '#7f8c8d', distance: 6,
                      formatter: `线性 ${lin.rate}` } }
            ].filter(Boolean)
        });
        // 只标注最关心的一个数：指数趋势的年均增长率（a、b 系数对读图没帮助，不印）
        const span = `${years[0]}–${years[years.length - 1]}`;
        document.getElementById('fit-note-' + key).innerHTML = expOnly
            ? `指数趋势（${span} 最小二乘）：年均增长 <b>+${(exp.cagr * 100).toFixed(2)}%</b>（R²=${exp.r2.toFixed(3)}）`
            : `指数回归 ln(y)=a+b·t：<b>${exp.rate}</b>（R²=${exp.r2.toFixed(3)}）` +
              ` · 线性回归 y=a+b·t：<b>${lin.rate}</b>（R²=${lin.r2.toFixed(3)}）`;
    }
    makeScaleChart('chart-scale-dep',  '客户存款',      deposit, 'dep',  '#6c3483', 'rgba(108,52,131,0.08)', true);
    makeScaleChart('chart-scale-loan', '客户贷款及垫款', loan,    'loan', '#e67e22', 'rgba(230,126,34,0.08)', true);

    // 同业四行里本行那条实线名字随 ?code= 变；同业线若本行自己就是该行会重复，live() 只滤空线，重名无害
    const serNpl = live([
        { name: SELF, type: 'line', data: npl, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
          areaStyle: { color: 'rgba(192,57,43,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
        peerLine('农业银行', nplAbc, '#2874a6'),
        peerLine('招商银行', nplCmb, '#229954'),
        peerLine('邮储银行', nplPsb, '#d68910')
    ]);
    initChart('chart-npl')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: serNpl.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '不良率%', min: 0, max: axMax(3, npl, nplAbc, nplCmb, nplPsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serNpl
    });

    // 逾期率 = 逾期贷款 / 贷款总额（各行年报「贷款质量—逾期贷款」披露，渝农商 2014 起有此项）
    const serOd = live([
        { name: SELF, type: 'line', data: overdue, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
          areaStyle: { color: 'rgba(230,126,34,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#e67e22', formatter: '{c}%' } },
        peerLine('农业银行', overdueAbc, '#2874a6'),
        peerLine('招商银行', overdueCmb, '#229954'),
        peerLine('邮储银行', overduePsb, '#d68910')
    ]);
    initChart('chart-overdue')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serOd.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '逾期率%', min: 0, max: axMax(3.5, overdue, overdueAbc, overdueCmb, overduePsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#e67e22', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serOd
    });

    window.__renderNplAmt(D);

    // 逾期贷款总额（亿元）= 年报「贷款质量分析—逾期贷款」余额；同图画不良贷款余额便于看逾期/不良缺口
    const serOdAmt = live([
        { name: '逾期贷款', type: 'line', data: overdueAmt, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
          areaStyle: { color: 'rgba(230,126,34,0.08)' },
          endLabel: { show: true, fontSize: 18, color: '#e67e22', distance: 6, formatter: '{c}' } },
        { name: '不良贷款', type: 'line', data: nplAmt, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 2, color: '#c0392b', type: 'dashed' }, itemStyle: { color: '#c0392b' },
          endLabel: { show: true, fontSize: 18, color: '#c0392b', distance: 6, formatter: '{c}' } }
    ]);
    if (serOdAmt.length) {
        initChart('chart-overdue-amt')?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                    p.map(x => x.value == null ? `${x.marker}${x.seriesName}：未披露`
                        : `${x.marker}${x.seriesName}：${x.value} 亿元`).join('<br>') },
            legend: { data: serOdAmt.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
            grid: { left: 72, right: 88, top: 46, bottom: 60 },
            xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
            yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                     axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            series: serOdAmt
        });
    }

    // 逾期贷款按逾期天数分档：年报分档口径逐年变化，故整块图仅在该行录入了分档数据时才显示
    (function () {
        const blk = document.getElementById('blk-overdue-band');
        if (!blk) return;
        const B = D['overdue-band'] || {};
        if (__emptyPayload(B) || !(B.years || []).length) { blk.style.display = 'none'; return; }
        const yrsB = B.years;
        // 图例默认按常见「1–90天 / 91天–1年 / 1–5年 / 5年以上」；本行年报档名不同时
        // 用 overdue-band.names 覆盖（渝农商行全年都是 3个月 / 3个月至1年 / 1至3年 / 3年以上）
        const nm = B.names || {};
        // 「1年及以上（未细分）」为早年年报缺细分时的残余档，浅灰蓝并垫在最后
        const serBand = live([
            { key: 'b90',  name: nm.b90  || '逾期 1至90天',   color: '#f5b041' },
            { key: 'b91y', name: nm.b91y || '逾期 91天至1年', color: '#e59866' },
            { key: 'b1_5', name: nm.b1_5 || '逾期 1至5年',    color: '#cb4335' },
            { key: 'b5up', name: nm.b5up || '逾期 5年以上',   color: '#7b241c' },
            { key: 'b1up', name: nm.b1up || '逾期 1年及以上（年报未细分）', color: '#aab7c4' }
        ].map(c => ({
            name: c.name, type: 'bar', stack: 'od', data: B[c.key] || [],
            itemStyle: { color: c.color }, barMaxWidth: 42
        })));
        if (serBand.length) {
            const marks = B.marks || [];
            if (marks.length) {
                // 口径断点竖线：只挂在第一条 series 上，避免每档重复画
                serBand[0].markLine = {
                    silent: true, symbol: 'none',
                    lineStyle: { type: 'dashed', color: '#9ca3af', width: 1.4 },
                    label: { show: true, fontSize: 14, color: '#6b7280' },
                    data: marks.map(m => ({ xAxis: m.year,
                        label: { formatter: m.text, position: m.pos || 'insideEndTop' } }))
                };
            }
            initChart('chart-overdue-band')?.setOption({
                backgroundColor: '#fff',
                textStyle: { fontSize: 18 },
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                    formatter: p => {
                        const live_ = p.filter(x => x.value != null);
                        const tot = live_.reduce((s, x) => s + x.value, 0);
                        return `<b>${p[0].axisValue} 年</b><br>` +
                            live_.map(x => `${x.marker}${x.seriesName}：${x.value} 亿元`).join('<br>') +
                            `<br>合计：<b>${tot.toFixed(2)}</b> 亿元`;
                    } },
                legend: { data: serBand.map(s => s.name), bottom: 2, textStyle: { fontSize: 16 } },
                grid: { left: 72, right: 40, top: 46, bottom: 78 },
                xAxis: { type: 'category', data: yrsB, axisLabel: { fontSize: 18, color: '#555' } },
                yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                         axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
                series: serBand
            });
        } else {
            blk.style.display = 'none';
        }
    })();

    // 核销率 = 本期核销（含其他转出） ÷ 发放贷款和垫款总额（各行年报「贷款减值准备变动」披露本期核销额）
    const serWo = live([
        { name: SELF, type: 'line', data: woRate, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#8e44ad' }, itemStyle: { color: '#8e44ad' },
          areaStyle: { color: 'rgba(142,68,173,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#8e44ad', formatter: '{c}%' } },
        peerLine('农业银行', woRateAbc, '#2874a6'),
        peerLine('招商银行', woRateCmb, '#229954'),
        peerLine('邮储银行', woRatePsb, '#d68910')
    ]);
    initChart('chart-writeoff-rate')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serWo.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '核销率%', min: 0, max: axMax(2.2, woRate, woRateAbc, woRateCmb, woRatePsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#8e44ad', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serWo
    });

    // 不良生成率 = 不良生成额 ÷ 期初贷款总额（不良生成额 = 期末不良 − 期初不良 + 核销净额），衡量新增不良的速度
    const serFm = live([
        { name: SELF, type: 'line', data: formation, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
          areaStyle: { color: 'rgba(192,57,43,0.07)' },
          label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}%' } },
        peerLine('农业银行', formationAbc, '#2874a6'),
        peerLine('招商银行', formationCmb, '#229954'),
        peerLine('邮储银行', formationPsb, '#d68910')
    ]);
    initChart('chart-npl-formation')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '未披露' : v + '%' },
        legend: { data: serFm.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 88, top: 56, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '不良生成率%', min: 0,
                 max: axMax(3, formation, formationAbc, formationCmb, formationPsb),
                 nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: serFm
    });

    initChart('chart-quality')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 }, valueFormatter: v => v == null ? '缺口' : v + '%' },
        legend: { data: ['资本充足率', '核心一级资本充足率'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 48, right: 20, top: 36, bottom: 52 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '%', min: 0, max: axMax(18, car, cet1), nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#1e8449', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '资本充足率', type: 'line', data: car, smooth: true, connectNulls: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
            { name: '核心一级资本充足率', type: 'line', data: cet1, smooth: true, connectNulls: true, symbolSize: 5,
              lineStyle: { width: 2, color: '#27ae60', type: 'dashed' }, itemStyle: { color: '#27ae60' } }
        ]
    });
})();

});

__section(function (D, SELF, notes) {
/* ────── 1i. 其他综合收益（OCI）与净利润 ────── */
(function () {
    const years16  = D['oci'].years16;
    const oci      = D['oci'].oci;
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
    const years16 = D['pershare'].years16;
    const eps  = D['pershare'].eps;
    // BVPS：港交所 03618 历年年报「歸屬於本行股東的每股淨資產」披露值（2010 年为加权口径，2011 起为期末口径）
    const bvps = D['pershare'].bvps;

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

});

__section(function (D, SELF, notes) {

/* ────── 13. NIM 分解 ────── */
(function () {
    const items = D['nim'].items;
    const rate25 = D['nim'].rate25;
    const rate24 = D['nim'].rate24;
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
});
