/* ROE / 不良贷款总额：可复用的单图渲染函数。
 * 定义在分区体系之外（不走 __section）：除了 renderAll 首次渲染，charts-switcher.js 里的
 * 「快速切换银行」按钮也会拿别家银行的数据重绘同一张图，所以挂在 window 上供两边共用。 */

/* ────── 1.1b 加权平均 ROE（2009 年起，2018 年新准则切换断口） ──────
 * 定义在 renderAll 外面：业绩页 ROE 图上方有一排「快速切换银行」按钮，点击时拿别家银行的
 * payload 只重画这一张图（不整页重载），所以渲染逻辑必须能被独立调用。入参只用到 D['roe']。 */
window.__renderRoe = function (D) {
    const R = (D && D['roe']) || {};
    const years = R.years || [];
    // 2009–2013 简单 ROE = 归母净利润 / 平均归母权益（年报未披露加权平均值）
    // 2009 年净利润 18.88 亿、期末权益 94.77 亿：取自 2010 年 H 股招股章程 Appendix IB 会计师报告（hkexnews.hk），2008 年期末权益 78.92 亿同源
    // 2010 年 12 月 H 股上市募资致权益年内跳升，简单平均偏低；2011–2013 无重大增发，近似加权
    const roeCalc = R.roeCalc || [];
    // 旧准则「加权平均股东权益回报率」(年报披露)，2014–2018
    const roeOld = R.roeOld || [];
    // 新准则「加权平均净资产收益率」(年报披露)，自 2018 年首次执行新金融工具准则起
    const roeNew = R.roeNew || [];
    // 只有渝农商行手工补了 2009–2013 的简单 ROE，其余行该段全空——用 live() 把空系列连图例一起摘掉，
    // 免得快速切换到别家行时图例里挂着一条画不出来的线
    const roeSeries = live([
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
    ]);
    initChart('chart-roe')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                let s = `<b>${p[0].axisValue} 年</b>`;
                p.forEach(x => { if (x.value != null) s += `<br>${x.marker}${x.seriesName}：${x.value}%`; });
                return s;
            } },
        legend: { data: roeSeries.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 56, right: 24, top: 36, bottom: 68 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: roeSeries
    }, true);   // notMerge —— 切行时年份跨度/系列长度不同，避免残留上一行的点
};

/* ────── 1.1c ROE 一键对比：所有可切换银行画在同一张图上 ──────
 * 入参 items = [{ code, name, roe }]，roe 即各行 payload 里的 D['roe']。
 * 每行只画一条线：同一年若新旧准则都披露（2018 年）取新准则，早年缺披露值时退到简单 ROE，
 * 因为十家行叠在一起时再分三段口径会有三十条线，图上根本读不出来；口径拼接在图下说明里写清。 */
/* 银行数量已到 13 家且还会加，凑不出这么多一眼可分的颜色：用 7 色 × 实线/虚线两轮 = 14 条可辨曲线，
 * 图例本身带线型，所以第二轮的虚线在图例里也认得出是哪家 */
window.__ROE_CMP_COLORS = ['#6c3483', '#c0392b', '#1f77b4', '#e67e22', '#16a085', '#2c3e50', '#d81b60'];
window.__renderRoeCompare = function (items) {
    // 各行年份跨度不同（渝农商行自 2009，多数行自 2014/2018），取并集做横轴，缺的年份留 null 断开
    const years = Array.from(new Set(items.reduce(
        (acc, it) => acc.concat((it.roe && it.roe.years) || []), []))).sort();
    const series = items.map(function (it, i) {
        const R = it.roe || {};
        const yy = R.years || [];
        const at = function (arr, y) {
            const k = yy.indexOf(y);
            return (k < 0 || !arr) ? null : (arr[k] == null ? null : arr[k]);
        };
        const data = years.map(function (y) {
            const v = at(R.roeNew, y);
            if (v != null) return v;
            const o = at(R.roeOld, y);
            return o != null ? o : at(R.roeCalc, y);
        });
        const self = it.code === window.COMPANY_CODE;
        const P = window.__ROE_CMP_COLORS;
        const color = P[i % P.length];
        const dashed = i >= P.length;   // 第二轮改虚线，避免与第一轮同色的行混淆
        return {
            name: it.name, type: 'line', data: data, connectNulls: false,
            symbolSize: self ? 7 : 5, z: self ? 9 : 2,
            lineStyle: { width: self ? 4.5 : 2, color: color, type: dashed ? 'dashed' : 'solid' },
            itemStyle: { color: color },
            // 十条线叠在一起时点上数字会糊成一片，数值看 tooltip；只给本页银行留末端标注
            endLabel: self ? { show: true, fontSize: 16, color: color, formatter: '{c}%' } : { show: false },
            emphasis: { focus: 'series', lineStyle: { width: self ? 5.5 : 3.5 } }
        };
    });
    initChart('chart-roe')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 17 },
            // 十几家行叠一起时这块内容又高又宽，不 confine 会被鼠标带出屏幕外
            confine: true,
            formatter: p => {
                // 同一年十家行的值按高低排，一眼看出座次
                const rows = p.filter(x => x.value != null)
                    .sort((a, b) => b.value - a.value)
                    .map(x => `${x.marker}${x.seriesName}：${x.value}%`);
                return `<b>${p[0].axisValue} 年</b><br>` + (rows.join('<br>') || '无披露');
            } },
        legend: { data: series.map(s => s.name), bottom: 2, textStyle: { fontSize: 17 }, itemGap: 14 },
        grid: { left: 56, right: 72, top: 36, bottom: 108 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        // 各行 ROE 落在 5%–32%（2011 年邮储 31.8% 是上沿），从 0 起画不至于把差异压扁，
        // 也和单行模式的纵轴口径一致，切换前后读数不会产生错觉
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: series
    }, true);   // notMerge —— 与单行模式的系列结构完全不同
};

/* ────── 1. 业绩走势（2009 年起，2008 年 6 月信用社改制为股份公司致口径断口） ────── */

/* 不良贷款总额（亿元）：单行 / 多行对比。风控页第一张，按钮切换与 ROE 图同一套交互。 */
window.__renderNplAmt = function (D) {
    const sd = (D && D['scale-dep']) || {};
    const years = sd.years || [];
    const nplAmt = sd.nplAmt || [];
    const name = (D._bank && D._bank.shortName) || '不良贷款';
    const ser = live([
        { name: name, type: 'line', data: nplAmt, smooth: true, connectNulls: true, symbolSize: 6,
          lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
          areaStyle: { color: 'rgba(192,57,43,0.08)' },
          endLabel: { show: true, fontSize: 18, color: '#c0392b', distance: 6, formatter: '{c}' } }
    ]);
    if (!ser.length) return;
    const el = document.getElementById('chart-npl-amt');
    if (el) el.style.height = '420px';
    initChart('chart-npl-amt')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` +
                p.map(x => x.value == null ? `${x.marker}${x.seriesName}：未披露`
                    : `${x.marker}${x.seriesName}：${x.value} 亿元`).join('<br>') },
        legend: { data: ser.map(s => s.name), bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 88, top: 46, bottom: 60 },
        xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { color: '#555', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
        series: ser
    }, true);
};

window.__renderNplAmtCompare = function (items) {
    const years = Array.from(new Set(items.reduce(function (acc, it) {
        return acc.concat((it.years) || []);
    }, []))).sort();
    const P = window.__ROE_CMP_COLORS;
    const series = items.map(function (it, i) {
        const yy = it.years || [];
        const arr = it.nplAmt || [];
        const data = years.map(function (y) {
            const k = yy.indexOf(y);
            return (k < 0) ? null : (arr[k] == null ? null : arr[k]);
        });
        const self = it.code === window.COMPANY_CODE;
        const color = P[i % P.length];
        const dashed = i >= P.length;
        return {
            name: it.name, type: 'line', data: data, connectNulls: false,
            symbolSize: self ? 7 : 5, z: self ? 9 : 2,
            lineStyle: { width: self ? 4.5 : 2, color: color, type: dashed ? 'dashed' : 'solid' },
            itemStyle: { color: color },
            endLabel: (self || items.length <= 8)
                ? { show: true, fontSize: 15, color: color, formatter: items.length <= 8 ? '{c}' : '{c}' }
                : { show: false },
            emphasis: { focus: 'series', lineStyle: { width: self ? 5.5 : 3.5 } }
        };
    }).filter(function (s) { return s.data.some(function (v) { return v != null; }); });
    const el = document.getElementById('chart-npl-amt');
    if (el) el.style.height = '600px';
    initChart('chart-npl-amt')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 17 }, confine: true,
            formatter: p => {
                const rows = p.filter(x => x.value != null)
                    .sort((a, b) => b.value - a.value)
                    .map(x => `${x.marker}${x.seriesName}：${x.value} 亿`);
                return `<b>${p[0].axisValue} 年</b><br>` + (rows.join('<br>') || '无披露');
            } },
        legend: { data: series.map(s => s.name), bottom: 2, textStyle: { fontSize: 17 }, itemGap: 14 },
        grid: { left: 72, right: 88, top: 36, bottom: 108 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '亿元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: series
    }, true);
    const inst = el && window.echarts && echarts.getInstanceByDom(el);
    if (inst) inst.resize();
};
