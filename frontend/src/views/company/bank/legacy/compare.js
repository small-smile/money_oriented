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

/* ────── 1.1c ROE 多行对比 ──────
 * 入参 items = [{ code, name, tier, roe }]，roe 即各行 payload 里的 D['roe']。
 * 每行只画一条线：同一年若新旧准则都披露（2018 年）取新准则，早年缺披露值时退到简单 ROE，
 * 因为十家行叠在一起时再分三段口径会有三十条线，图上根本读不出来；口径拼接在图下说明里写清。
 *
 * 可选到 45 家，一行一色是凑不出来的：改成**按机构类型分配色系**（大行红 / 股份蓝 / 城商青 / 农商橙），
 * 同类型内换深浅、超过色板长度再叠虚线。类型层次一眼可辨，具体是哪家靠悬浮（其余线淡到 0.1）
 * 与 tooltip 分列名单认；tooltip 按类型分栏多排，45 行也不会拉成一条长面条。 */
window.__TIER_ORDER = ['国有大行', '股份行', '城商行', '农商行'];
window.__TIER_COLORS = {
    '国有大行': ['#c0392b', '#e74c3c', '#a93226', '#cd6155', '#7b241c', '#e6b0aa'],
    '股份行':   ['#1f77b4', '#2874a6', '#5dade2', '#154360', '#2e86c1', '#85c1e9', '#1b4f72', '#aed6f1', '#21618c'],
    '城商行':   ['#16a085', '#138d75', '#1abc9c', '#0e6655', '#48c9b0', '#117864', '#76d7c4', '#0b5345',
                 '#45b39d', '#a3e4d7', '#1d8348', '#28b463', '#52be80', '#82e0aa', '#196f3d', '#7dcea0', '#145a32'],
    '农商行':   ['#e67e22', '#d35400', '#f39c12', '#af601a', '#f5b041', '#ca6f1e', '#dc7633', '#e59866', '#873600', '#f8c471'],
    '其他':     ['#7f8c8d', '#95a5a6', '#566573', '#aab7b8']
};
// 不良总额对比图仍用这套轮转色（它一次只画一个类型，不需要类型色系）
window.__ROE_CMP_COLORS = ['#6c3483', '#c0392b', '#1f77b4', '#e67e22', '#16a085', '#2c3e50', '#d81b60'];

// 类型名归一：__BANKS 里没有 tier 或是未知值的行归到「其他」，不丢线
function __tierOf(it) {
    return (it && it.tier && window.__TIER_COLORS[it.tier]) ? it.tier : '其他';
}
// 类型 → 排序权重（未知类型排最后）
function __tierRank(t) {
    const i = window.__TIER_ORDER.indexOf(t);
    return i < 0 ? window.__TIER_ORDER.length : i;
}
// 三段口径拼成一条线用的取值：同年优先新准则 → 旧准则 → 简单 ROE
function __roeAt(R, y) {
    const yy = (R && R.years) || [];
    const k = yy.indexOf(y);
    if (k < 0) return null;
    const pick = function (arr) { return (arr && arr[k] != null) ? arr[k] : null; };
    const v = pick(R.roeNew);
    if (v != null) return v;
    const o = pick(R.roeOld);
    return o != null ? o : pick(R.roeCalc);
}
// 横轴：各行年份跨度不同（渝农商行自 2009，多数行自 2014/2018），取并集，缺的年份留 null 断开
function __roeYears(items) {
    return Array.from(new Set(items.reduce(
        (acc, it) => acc.concat((it.roe && it.roe.years) || []), []))).sort();
}
/* 下面五个多行视图（叠线 / 类型聚合 / 本行位次 / 分类型小图 / 最新年份榜）也给风控页拨贷比对比用：
 * opt.id 是图容器 id，opt.metric 是 tooltip 里写的指标名；不传即业绩页 ROE 图。
 * 别的指标借用 roe 字段，只填 { years, roeNew } 一段口径即可（__roeAt 先取 roeNew）。 */
function __cmpOpt(opt) {
    return Object.assign({ id: 'chart-roe', metric: 'ROE' }, opt || {});
}
/* tooltip 共用样式：必须盖掉 ECharts 默认 white-space:nowrap，否则 grid / 分栏都会被挤成一行 */
function __roeTipCss() {
    return 'white-space:normal;max-width:720px;max-height:70vh;overflow:auto;padding:10px 12px';
}
/* tooltip：按类型 2×2 分块（上排大行/股份，下排城商/农商），块内按 ROE 从高到低；
 * 城商行一类超过 8 家时块内再分两栏，避免单列拉成一条长面条。本页银行加粗并垫底。 */
function __roeTierTooltip(axisValue, rows) {
    const groups = {};
    rows.forEach(function (r) { (groups[r.tier] = groups[r.tier] || []).push(r); });
    const tiers = Object.keys(groups).sort((a, b) => __tierRank(a) - __tierRank(b));
    if (!tiers.length) return `<b>${axisValue} 年</b><br>无披露`;
    const nCol = tiers.length >= 2 ? 2 : 1;
    const cards = tiers.map(function (t) {
        const list = groups[t].sort((a, b) => b.value - a.value);
        const inner = list.length > 8 ? 2 : 1;
        const color = (window.__TIER_COLORS[t] || ['#6b7280'])[0];
        const body = list.map(function (r) {
            const bg = r.self ? 'background:#eef2f7;border-radius:3px;padding:0 4px;' : '';
            return `<div style="font-weight:${r.self ? 700 : 400};white-space:nowrap;line-height:1.5;${bg}">` +
                   `${r.marker}${r.name}　${r.value}%</div>`;
        }).join('');
        return `<div><div style="color:${color};font-weight:700;font-size:14px;border-bottom:2px solid ${color};` +
               `margin-bottom:4px;padding-bottom:2px">${t}（${list.length}）</div>` +
               `<div style="columns:${inner};column-gap:14px">${body}</div></div>`;
    }).join('');
    return `<div style="font-weight:700;margin-bottom:8px;font-size:16px">${axisValue} 年</div>` +
           `<div style="display:grid;grid-template-columns:repeat(${nCol},minmax(168px,1fr));` +
           `gap:10px 18px;align-items:start">${cards}</div>`;
}
window.__renderRoeCompare = function (items, opt) {
    opt = __cmpOpt(opt);
    const years = __roeYears(items);
    // 按类型排序：图例里同类型连成一段，色系一眼分块（原来按清单顺序会红蓝青橙交错）
    const sorted = items.slice().sort(function (a, b) {
        return __tierRank(__tierOf(a)) - __tierRank(__tierOf(b));
    });
    const seen = {};    // 类型 → 该类型内已用掉几个色位
    const many = sorted.length > 14;    // 家数多时：拿掉每点的圆点与图例，只留线条
    const series = sorted.map(function (it) {
        const tier = __tierOf(it);
        const P = window.__TIER_COLORS[tier];
        const n = seen[tier] = (seen[tier] == null ? 0 : seen[tier] + 1);
        const color = P[n % P.length];
        const dashed = n >= P.length;   // 同类型内色板用完的那几家改虚线
        const self = it.code === window.COMPANY_CODE;
        return {
            name: it.name, type: 'line', data: years.map(y => __roeAt(it.roe || {}, y)),
            connectNulls: false, tier: tier,
            // 45 条线时每点一个圆圈会把图糊成砂纸；本行始终带点，便于在一片线里找到自己
            symbol: (self || !many) ? 'circle' : 'none', symbolSize: self ? 7 : 4, z: self ? 9 : 2,
            lineStyle: { width: self ? 4.5 : (many ? 1.5 : 2), color: color,
                         type: dashed ? 'dashed' : 'solid', opacity: self ? 1 : 0.85 },
            itemStyle: { color: color },
            // 几十条线叠在一起时点上数字会糊成一片，数值看 tooltip；只给本页银行留末端标注
            endLabel: self ? { show: true, fontSize: 16, color: color, formatter: '{c}%' } : { show: false },
            // focus:'series' 是 blur 生效的前提（只写 blur 不设 focus 不会变暗）
            emphasis: { focus: 'series', lineStyle: { width: self ? 5.5 : 3.5, opacity: 1 } },
            blur: { lineStyle: { opacity: 0.08 }, itemStyle: { opacity: 0.08 } }
        };
    });
    const tierOfName = {};
    series.forEach(function (s) { tierOfName[s.name] = s.tier; });
    const selfName = (sorted.filter(it => it.code === window.COMPANY_CODE)[0] || {}).name || '';
    initChart(opt.id)?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 16 },
            // 几十家行叠一起时这块内容又高又宽，不 confine 会被鼠标带出屏幕外
            confine: true, extraCssText: __roeTipCss(),
            formatter: p => __roeTierTooltip(p[0].axisValue, p.filter(x => x.value != null).map(x => ({
                tier: tierOfName[x.seriesName] || '其他', name: x.seriesName, value: x.value,
                marker: x.marker, self: x.seriesName === selfName
            })))
        },
        // 家数多时不放银行图例：45 条 scroll 图例要翻 5 页、也看不出类型分块，
        // 上方筛选按钮已经是完整清单，认线靠悬浮（其余淡出）+ tooltip 分栏名单；
        // 类型 → 色系的对应关系写在图下 note 的色标里。
        legend: many ? { show: false }
                     : { data: series.map(s => s.name), bottom: 2, textStyle: { fontSize: 17 }, itemGap: 14 },
        grid: { left: 56, right: 72, top: 36, bottom: many ? 60 : 108 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        // 各行 ROE 落在 5%–32%（2011 年邮储 31.8% 是上沿），从 0 起画不至于把差异压扁，
        // 也和单行模式的纵轴口径一致，切换前后读数不会产生错觉
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: series
    }, true);   // notMerge —— 与单行模式的系列结构完全不同
};

/* ────── 1.1d ROE 类型聚合：每个机构类型一条中位数线 + 25–75 分位带 + 本行 ──────
 * 45 家叠线即使按类型着色也只能看出层次、读不出个体；这个模式换个问法——
 * 「本行相对同类型处在什么位置」：类型内分布收成一条中位线和一条带，图上最多 4 条线 + 本行，
 * 本行落在带内还是带外一眼可见。分位数按每年参与披露的行现算（各行起始年份不同，n 逐年变）。 */
function __quantile(sortedVals, q) {
    const n = sortedVals.length;
    if (!n) return null;
    if (n === 1) return sortedVals[0];
    const pos = (n - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
    return +(sortedVals[lo] + (sortedVals[hi] - sortedVals[lo]) * (pos - lo)).toFixed(2);
}
window.__renderRoeTierAgg = function (items, opt) {
    opt = __cmpOpt(opt);
    const years = __roeYears(items);
    const byTier = {};
    items.forEach(function (it) { (byTier[__tierOf(it)] = byTier[__tierOf(it)] || []).push(it); });
    const tiers = Object.keys(byTier).sort((a, b) => __tierRank(a) - __tierRank(b));
    const stat = {};    // tier → { p25:[], p50:[], p75:[], n:[] }
    tiers.forEach(function (t) {
        const rows = { p25: [], p50: [], p75: [], n: [] };
        years.forEach(function (y) {
            const vals = byTier[t].map(it => __roeAt(it.roe || {}, y))
                .filter(v => v != null).sort((a, b) => a - b);
            rows.n.push(vals.length);
            rows.p25.push(__quantile(vals, 0.25));
            rows.p50.push(__quantile(vals, 0.5));
            rows.p75.push(__quantile(vals, 0.75));
        });
        stat[t] = rows;
    });
    const self = items.filter(it => it.code === window.COMPANY_CODE)[0];
    const selfName = self ? self.name : '';
    const series = [];
    const selfTier = self ? __tierOf(self) : '';
    tiers.forEach(function (t) {
        const color = window.__TIER_COLORS[t][0];
        const s = stat[t];
        // 四条分位带叠在一起会糊成一团：只给本行所属类型留 25–75 带，其余类型只画中位线
        if (t === selfTier) {
            series.push({ name: t + '·p25', type: 'line', stack: 'band-' + t, data: s.p25,
                lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, symbol: 'none',
                silent: true, z: 1, tooltip: { show: false } });
            series.push({ name: t + '·带', type: 'line', stack: 'band-' + t,
                data: s.p75.map((v, i) => (v == null || s.p25[i] == null) ? null : +(v - s.p25[i]).toFixed(2)),
                lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, symbol: 'none',
                areaStyle: { color: color, opacity: 0.16 }, silent: true, z: 1, tooltip: { show: false } });
        }
        series.push({ name: t, type: 'line', data: s.p50, connectNulls: false, symbolSize: 5, z: 5,
            lineStyle: { width: 3, color: color }, itemStyle: { color: color },
            endLabel: { show: true, fontSize: 15, color: color, formatter: '{c}%' },
            labelLayout: { moveOverlap: 'shiftY' },
            emphasis: { focus: 'series', lineStyle: { width: 4.5 } },
            blur: { lineStyle: { opacity: 0.15 } } });
    });
    if (self) {
        series.push({ name: selfName, type: 'line', data: years.map(y => __roeAt(self.roe || {}, y)),
            connectNulls: false, symbolSize: 7, z: 9,
            lineStyle: { width: 4.5, color: '#10243e' }, itemStyle: { color: '#10243e' },
            endLabel: { show: true, fontSize: 16, color: '#10243e', fontWeight: 700, formatter: '{c}%' },
            labelLayout: { moveOverlap: 'shiftY' },
            emphasis: { focus: 'series', lineStyle: { width: 5.5 } } });
    }
    initChart(opt.id)?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 16 }, confine: true, extraCssText: __roeTipCss(),
            formatter: function (p) {
                const idx = p[0].dataIndex;
                const year = p[0].axisValue;
                const cards = tiers.map(function (t) {
                    const st = stat[t];
                    if (st.p50[idx] == null) return '';
                    const color = window.__TIER_COLORS[t][0];
                    let extra = '';
                    if (self && __tierOf(self) === t) {
                        const mv = __roeAt(self.roe || {}, years[idx]);
                        if (mv != null) extra = `<div style="font-weight:700;margin-top:3px">${selfName}　${mv}%</div>`;
                    }
                    return `<div><div style="color:${color};font-weight:700;border-bottom:2px solid ${color};` +
                           `margin-bottom:4px;padding-bottom:2px">${t}（${st.n[idx]} 家）</div>` +
                           `<div>中位 <b>${st.p50[idx]}%</b></div>` +
                           `<div style="color:#6b7280">25–75　${st.p25[idx]}–${st.p75[idx]}%</div>${extra}</div>`;
                }).filter(Boolean).join('');
                return `<div style="font-weight:700;margin-bottom:8px;font-size:16px">${year} 年</div>` +
                       `<div style="display:grid;grid-template-columns:repeat(2,minmax(160px,1fr));` +
                       `gap:10px 18px;align-items:start">${cards}</div>`;
            } },
        legend: { data: (self ? [selfName] : []).concat(tiers), bottom: 2,
                  textStyle: { fontSize: 17 }, itemGap: 16 },
        grid: { left: 56, right: 88, top: 36, bottom: 68 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        yAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: series
    }, true);
};

/* ────── 1.1e ROE 本行位次：本行在所选样本里排第几（不看绝对值，只看座次） ──────
 * 两条线：在全部所选行中的位次、在同类型内的位次。纵轴反向（1 名在上），
 * 分母逐年变（当年有披露的行才计入），故 tooltip 里带出「第 a / n 名」。 */
window.__renderRoeRank = function (items, opt) {
    opt = __cmpOpt(opt);
    const years = __roeYears(items);
    const self = items.filter(it => it.code === window.COMPANY_CODE)[0];
    if (!self) { window.__renderRoeCompare(items, opt); return; }   // 本行不在样本里就退回叠线
    const tier = __tierOf(self);
    const peers = items.filter(it => __tierOf(it) === tier);
    // 位次 = 比本行高的家数 + 1（并列取靠前的名次）；本行当年没披露则整点留空
    function rankIn(pool, y) {
        const mine = __roeAt(self.roe || {}, y);
        if (mine == null) return [null, 0];
        const vals = pool.map(it => __roeAt(it.roe || {}, y)).filter(v => v != null);
        return [vals.filter(v => v > mine).length + 1, vals.length];
    }
    const all = years.map(y => rankIn(items, y));
    const own = years.map(y => rankIn(peers, y));
    const tierColor = window.__TIER_COLORS[tier][0];
    const maxN = Math.max.apply(null, all.map(r => r[1]).concat([2]));
    initChart(opt.id)?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 17 }, confine: true,
            formatter: function (p) {
                const i = p[0].dataIndex, v = __roeAt(self.roe || {}, years[i]);
                if (v == null) return `<b>${years[i]} 年</b><br>本行未披露`;
                return `<div style="font-weight:700;margin-bottom:4px">${years[i]} 年　` +
                       `${self.name} ${opt.metric} ${v}%</div>` +
                       `<div style="line-height:1.6">全部样本：第 <b>${all[i][0]}</b> / ${all[i][1]} 名</div>` +
                       `<div style="line-height:1.6">${tier}内：第 <b>${own[i][0]}</b> / ${own[i][1]} 名</div>`;
            } },
        legend: { data: ['全部样本位次', tier + '内位次'], bottom: 2, textStyle: { fontSize: 17 }, itemGap: 18 },
        grid: { left: 68, right: 80, top: 36, bottom: 68 },
        xAxis: { type: 'category', data: years, boundaryGap: false,
                 axisLabel: { fontSize: 18, color: '#555', rotate: 40 } },
        // inverse：第 1 名画在最上面，符合「榜首在上」的直觉；轴名放顶端，否则会压在 2009 标签上
        yAxis: { type: 'value', name: '位次', nameLocation: 'start', nameGap: 16,
                 inverse: true, min: 1, max: maxN,
                 minInterval: 1, nameTextStyle: { fontSize: 17, color: '#6b7280' },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            { name: '全部样本位次', type: 'line', data: all.map(r => r[0]), connectNulls: false,
              symbolSize: 7, lineStyle: { width: 4, color: '#10243e' }, itemStyle: { color: '#10243e' },
              endLabel: { show: true, fontSize: 16, color: '#10243e', fontWeight: 700, formatter: '第{c}名' },
              labelLayout: { moveOverlap: 'shiftY' } },
            { name: tier + '内位次', type: 'line', data: own.map(r => r[0]), connectNulls: false,
              symbolSize: 6, lineStyle: { width: 3, color: tierColor, type: 'dashed' },
              itemStyle: { color: tierColor },
              endLabel: { show: true, fontSize: 15, color: tierColor, formatter: '第{c}名' },
              labelLayout: { moveOverlap: 'shiftY' } }
        ]
    }, true);
};

/* ────── 1.1f ROE 分类型小图：一个类型一格，2×2 四格共用纵轴范围 ──────
 * 同一张 ECharts 实例里放 4 个 grid（小倍数）。每格只画该类型的行，家数落到十家以内，
 * 线就分得开了；本行不属于该类型时也叠一条深色细线做参照，四格之间才能横比。 */
window.__renderRoeFacet = function (items, opt) {
    opt = __cmpOpt(opt);
    const years = __roeYears(items);
    const self = items.filter(it => it.code === window.COMPANY_CODE)[0];
    const byTier = {};
    items.forEach(function (it) { (byTier[__tierOf(it)] = byTier[__tierOf(it)] || []).push(it); });
    const tiers = Object.keys(byTier).sort((a, b) => __tierRank(a) - __tierRank(b));
    // 四格共用同一纵轴上限，否则「城商行看着比大行高」是坐标轴造成的错觉
    let hi = 0;
    items.forEach(it => years.forEach(function (y) {
        const v = __roeAt(it.roe || {}, y);
        if (v != null && v > hi) hi = v;
    }));
    hi = Math.ceil(hi / 5) * 5;
    const cols = tiers.length > 2 ? 2 : 1, rows = Math.ceil(tiers.length / cols);
    const grids = [], xAxes = [], yAxes = [], titles = [], series = [];
    tiers.forEach(function (t, gi) {
        const r = Math.floor(gi / cols), c = gi % cols;
        // 每格高度留够旋转 40° 的年份标签，否则下排两格的轴标签会被容器底边裁掉
        const w = cols === 2 ? 40 : 84, h = 66 / rows;
        const left = 7 + c * 48, top = 7 + r * (h + 17);
        grids.push({ left: left + '%', top: top + '%', width: w + '%', height: h + '%' });
        xAxes.push({ gridIndex: gi, type: 'category', data: years, boundaryGap: false,
                     axisLabel: { fontSize: 14, color: '#666', interval: 3, rotate: 40 } });
        yAxes.push({ gridIndex: gi, type: 'value', min: 0, max: hi,
                     axisLabel: { fontSize: 14, color: '#666', formatter: '{value}%' },
                     splitLine: { lineStyle: { color: '#eee' } } });
        titles.push({ text: t + '（' + byTier[t].length + ' 家）', left: (left + 1) + '%',
                      top: (top - 6) + '%', textStyle: { fontSize: 17, color: '#10243e' } });
        const P = window.__TIER_COLORS[t];
        byTier[t].forEach(function (it, i) {
            const me = it.code === window.COMPANY_CODE;
            series.push({ name: it.name + '@' + t, type: 'line', xAxisIndex: gi, yAxisIndex: gi,
                data: years.map(y => __roeAt(it.roe || {}, y)), connectNulls: false, symbol: 'none',
                z: me ? 9 : 2,
                lineStyle: { width: me ? 3.5 : 1.6, color: me ? '#10243e' : P[i % P.length], opacity: 0.9 },
                itemStyle: { color: me ? '#10243e' : P[i % P.length] },
                emphasis: { focus: 'series', lineStyle: { width: me ? 4.5 : 3 } },
                blur: { lineStyle: { opacity: 0.12 } } });
        });
        // 本行不在这一格的类型里：补一条参照线（虚线），四格都能看出本行相对位置
        if (self && __tierOf(self) !== t) {
            series.push({ name: self.name + '（参照）@' + t, type: 'line', xAxisIndex: gi, yAxisIndex: gi,
                data: years.map(y => __roeAt(self.roe || {}, y)), connectNulls: false, symbol: 'none',
                z: 8, lineStyle: { width: 2.5, color: '#10243e', type: 'dashed', opacity: 0.85 },
                itemStyle: { color: '#10243e' }, emphasis: { focus: 'series' },
                blur: { lineStyle: { opacity: 0.12 } } });
        }
    });
    initChart(opt.id)?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 16 },
        title: titles,
        // 每格自己一套坐标：axisPointer 只联动本格，tooltip 里就是这一格的名单
        tooltip: { trigger: 'axis', textStyle: { fontSize: 16 }, confine: true,
            extraCssText: __roeTipCss(),
            formatter: function (p) {
                const rows = p.filter(x => x.value != null)
                    .sort((a, b) => b.value - a.value)
                    .map(x => `<div style="line-height:1.5;white-space:nowrap">${x.marker}` +
                              `${x.seriesName.split('@')[0]}　${x.value}%</div>`);
                const nCol = rows.length > 8 ? 2 : 1;
                return `<div style="font-weight:700;margin-bottom:4px">${p[0].axisValue} 年</div>` +
                       `<div style="columns:${nCol};column-gap:18px">${rows.join('') || '无披露'}</div>`;
            } },
        legend: { show: false },
        grid: grids, xAxis: xAxes, yAxis: yAxes, series: series
    }, true);
};

/* ────── 1.1g ROE 最新年份榜：所选行按最新披露年份的 ROE 排条形榜 ──────
 * 时间序列看不出「今年到底谁高谁低」，这个模式把最新一年拉平成横条、按类型着色、本行加深。
 * 取「有披露值的最后一个年份」，个别行当年年报未出时以其自身最新年份补位并在标签上标年份。 */
window.__renderRoeBar = function (items, opt) {
    opt = __cmpOpt(opt);
    const years = __roeYears(items);
    const rows = items.map(function (it) {
        // 从最新年份往前找该行第一个有值的年份，避免年报未出的行整条缺失
        for (let i = years.length - 1; i >= 0; i--) {
            const v = __roeAt(it.roe || {}, years[i]);
            if (v != null) return { name: it.name, tier: __tierOf(it), value: v, year: years[i],
                                    self: it.code === window.COMPANY_CODE };
        }
        return null;
    }).filter(Boolean).sort((a, b) => a.value - b.value);   // 条形图纵轴自下而上，升序才是「高的在上」
    const latest = years[years.length - 1];
    initChart(opt.id)?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 16 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 17 }, confine: true,
            formatter: function (p) {
                const r = rows[p.dataIndex];
                return `<b>${r.name}</b>　${r.tier}<br>${r.year} 年 ${opt.metric} <b>${r.value}%</b>` +
                       (r.year === latest ? '' : '　<span style="color:#c0392b">（最新披露年份非 ' + latest + '）</span>');
            } },
        grid: { left: 100, right: 96, top: 16, bottom: 40 },
        xAxis: { type: 'value', name: '%', min: 0, nameTextStyle: { fontSize: 17 },
                 axisLabel: { fontSize: 16, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: rows.map(r => r.name),
                 axisLabel: { fontSize: 16, color: '#555',
                     formatter: function (v, i) { return rows[i].self ? '{me|' + v + '}' : v; },
                     rich: { me: { fontSize: 17, fontWeight: 700, color: '#10243e' } } },
                 axisTick: { show: false } },
        series: [{
            type: 'bar', barMaxWidth: 18,
            data: rows.map(function (r) {
                return { value: r.value,
                         itemStyle: { color: r.self ? '#10243e' : window.__TIER_COLORS[r.tier][0],
                                      opacity: r.self ? 1 : 0.82 } };
            }),
            label: { show: true, position: 'right', fontSize: 16,
                     formatter: function (p) {
                         const r = rows[p.dataIndex];
                         return r.value + '%' + (r.year === latest ? '' : '（' + r.year + '）');
                     } },
            emphasis: { focus: 'self' }
        }]
    }, true);
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
