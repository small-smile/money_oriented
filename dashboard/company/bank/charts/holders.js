/* 股东结构：前十大股东（含 A+H 穿透）、历年持股集中度、可排序表格。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 3. 前十大股东 ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolders）重绘。 */
window.__renderYnsHolders = function (D) {
    if (!document.getElementById('chart-holders')) return;   // 仅业绩页
    const holders = D['holders'].holders;
    // 表格
    const tb = document.getElementById('holder-tbody');
    const chgColor = c => c === '不变' ? '#888' : (c[0] === '+' ? '#c0392b' : '#1e8449');
    tb.innerHTML = holders.map(h =>
        `<tr><td>${h.name}</td><td>${h.pct.toFixed(2)}%</td>` +
        `<td style="color:${chgColor(h.chg)}">${h.chg}</td><td style="font-size:18px;color:#777">${h.type}</td></tr>`
    ).join('');
    // 股东结构单层环形图：全部股东在同一个环、按比例铺满整圈；「其他流通股东」也按普通股东参与、严格按持股比例从大到小排序
    // 派系配色：香港中央结算 #16a085 · 渝富系 #6c3483 · 发展系 #2980b9 · 城投 #e67e22 · 财信 #c0392b · 社保 #f1c40f · 其他 #95a5a6
    const holderData = D['holders'].holderData;
    // 第一幅图（前十名股东）：剔除香港中央结算（代理人）/ 香港中央结算有限公司 / 其他流通股东 后，
    // 其余持股最多的具名股东放到时钟 0 点；其余按持股比例降序；上述三类放到最后（完整法定名称）。
    function isHksccNominees(name) {
        var n = String(name || '');
        if (/代理人|Nominees/i.test(n)) return true;
        // 短名「香港代理人(H股)」「香港中央结算(H股)」= H 股名义持有人，不是沪股通
        if (/H股/.test(n) && /香港中央結算|香港中央结算|香港代理人/.test(n)) return true;
        return false;
    }
    function isHksccConnect(name) {
        var n = String(name || '');
        if (isHksccNominees(n)) return false;
        return /沪股通|滬股通|香港中央結算|香港中央结算|HKSCC/i.test(n);
    }
    function isHksccSlice(name) { return isHksccNominees(name) || isHksccConnect(name); }
    function isResidualSlice(name) {
        return /其他流通|其他股东|其他股東/.test(String(name || ''));
    }
    function pieFullName(slice, roster, used) {
        var n = slice && slice.name;
        if (isResidualSlice(n)) return '其他流通股东';
        if (isHksccNominees(n)) return '香港中央结算（代理人）有限公司';
        if (isHksccConnect(n)) return '香港中央结算有限公司';
        var list = roster || [];
        // 先按名字对齐：holderData 里多是去掉「有限公司」的简称，整名或前缀能命中就不必靠比例猜
        var hit = list.find(function (h) { return h && h.name === n; }) ||
            list.find(function (h) {
                if (!h || !h.name || !n) return false;
                return h.name.indexOf(n) === 0 || String(n).indexOf(h.name) === 0;
            });
        // 名字对不上才按持股比例回填全称。同比例的两家股东（如江西银行的中国烟草总公司江西省
        // 公司与江西江投资本都是 2.99%）不能都认到第一家去，已被认走的 roster 项要跳过，
        // 否则环形图会画出两块同名扇区、另一家股东凭空消失。
        if (!hit) {
            hit = list.find(function (h) {
                return h && Math.abs((h.pct || 0) - (slice.value || 0)) < 0.005 &&
                    !(used && used[h.name]);
            });
        }
        if (hit && used) used[hit.name] = true;
        return (hit && hit.name) || n;
    }
    function pieOrderTopAtNoon(data, roster) {
        var used = {};
        var arr = (data || []).map(function (d) {
            return Object.assign({}, d, { name: pieFullName(d, roster, used) });
        });
        var tail = [], residual = [], named = [];
        arr.forEach(function (d) {
            if (!d) return;
            if (isResidualSlice(d.name)) residual.push(d);
            else if (isHksccSlice(d.name)) tail.push(d);
            else named.push(d);
        });
        named.sort(function (a, b) { return (b.value || 0) - (a.value || 0); });
        tail.sort(function (a, b) { return (b.value || 0) - (a.value || 0); });
        residual.sort(function (a, b) { return (b.value || 0) - (a.value || 0); });
        // named 已按持股降序，第一名即 0 点；接着两家香港中央结算（名义持有人）；
        // 「其他流通股东」不是具名股东、只是残余项，垫在最后一位
        return named.concat(tail, residual);
    }
    const pieData = pieOrderTopAtNoon(holderData, D['holders'].holders);
    // 环形图配色：这幅图不要求「同派系同色」——每家股东各给一色，免得渝富系/发展系内部
    // 几块相邻扇区糊成一片；派系归属改看图下清单（那里仍是同派系同色）。
    // 「其他流通股东」是残余项、不是一家公司，固定用灰色斜线纹理（见下面 RESIDUAL_PATTERN）：
    // 早先用过 #95a5a6 / #cfd8dc 这类纯色，纯色再淡也还是像「一家股东」，纹理才一眼看出是残余。
    const PIE_COLORS = [
        '#6c3483', '#e67e22', '#2980b9', '#16a085', '#c0392b', '#f1c40f',
        '#8e44ad', '#27ae60', '#d35400', '#2c3e50', '#c2185b', '#00838f'
    ];
    // 残余项（「其他流通股东」/「其他股东」）用灰色斜线纹理填充，样式**照搬**
    // dashboard/subject/oil/china_oil_majors.html 储量瀑布图里那段灰斜线：10×10 画布、
    // #f0f0f0 底、#999 细线 1.5px、斜线垂直间距约 7px。
    // 之前试过的改良版（加深/加密斜线、rgba 半透明纹理、毛玻璃渐变）都不如原版，已回退，
    // 别再自行调深浅。唯一保留的偏离：canvas 直接交给 ECharts（而不是 toDataURL 的 Image），
    // 省掉图片异步解码、首帧画不出纹理的风险。
    const RESIDUAL_PATTERN = (function () {
        var c = document.createElement('canvas');
        c.width = 10; c.height = 10;
        var x = c.getContext('2d');
        x.fillStyle = '#f0f0f0'; x.fillRect(0, 0, 10, 10);
        x.strokeStyle = '#999'; x.lineWidth = 1.5;
        // 主对角线 x+y=10，另加两角的补线（x+y=0 / x+y=20），保证平铺接缝处斜线不断
        x.beginPath(); x.moveTo(0, 10); x.lineTo(10, 0); x.stroke();
        x.beginPath(); x.moveTo(-2, 2); x.lineTo(2, -2); x.stroke();
        x.beginPath(); x.moveTo(8, 12); x.lineTo(12, 8); x.stroke();
        return { image: c, repeat: 'repeat' };
    })();
    const RESIDUAL_SWATCH_CSS = 'repeating-linear-gradient(45deg,#999 0 1.5px,#f0f0f0 1.5px 7.1px)';
    function residualFill() { return RESIDUAL_PATTERN; }
    // 图例色块：残余项换成 CSS 斜线渐变（itemStyle.color 此时是 ECharts 的 pattern 对象，
    // 直接插到 style 里会变成 [object Object]）
    function swatchCss(name, color) {
        return isResidualSlice(name) ? RESIDUAL_SWATCH_CSS : color;
    }
    // 两张 H 股环形图的残余项叫「其他H股股东」，不在 isResidualSlice 的口径里（那个口径还兼管
    // 排序和名称还原，不宜放宽），这里按「其他…」前缀就地把纹理套上去，保留原有的其他颜色
    function stripeResidual(arr) {
        return (arr || []).map(function (d) {
            if (!d || !/^其他/.test(String(d.name || ''))) return d;
            return Object.assign({}, d, { itemStyle: Object.assign({}, d.itemStyle, { color: residualFill() }) });
        });
    }
    function pieColorize(arr) {
        var i = 0;
        return (arr || []).map(function (d) {
            var color = isResidualSlice(d.name) ? residualFill() : PIE_COLORS[i++ % PIE_COLORS.length];
            return Object.assign({}, d, { itemStyle: Object.assign({}, d.itemStyle, { color: color }) });
        });
    }
    // 饼图样式统一收在 charts/core.js 的 PIE_BASE / PIE_LABEL（基准就是本页的 A+H 合并图），
    // 这里只留个别名，图与图之间不再各写一份 radius/label。
    const holderPieSeries = pieSeries;
    const holderTip = { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占总股本）` };
    // 圆心标注（原「前十大 58.29%」）已去掉：口径写在图上方标题和图下清单里，圆心再写一遍重复
    initChart('chart-holders')?.setOption({
        backgroundColor: '#fff',
        title: [],
        tooltip: holderTip,
        series: holderPieSeries({ data: pieColorize(pieData) })
    });

    // 图外清单：确保每位股东信息清晰可读（不受扇区大小影响），按派系分组
    const factions = D['holders'].factions;
    const val = n => holderData.find(d => d.name === n).value;
    document.getElementById('holders-legend').innerHTML = factions.map(f => {
        const sum = f.names.reduce((a, n) => a + val(n), 0);
        const items = f.names.map(n => `${n} ${val(n)}%`).join('　');
        // 残余项的色块跟着环形图一起换成灰色斜线纹理，别和派系色一样醒目
        const swatch = isResidualSlice(f.title) ? RESIDUAL_SWATCH_CSS : f.color;
        return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${swatch};vertical-align:-1px;margin-right:6px"></span>` +
               `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#6c3483;font-weight:600">${sum.toFixed(2)}%</span>` +
               (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
    }).join('');

    // 「A 股披露 TOP10 · 按派系合并」：同一派系（一致行动人 / 同一名义持有人）的股东合并成一个扇区，
    // 按派系合计持股比例降序铺满整圈。这幅图才是「同派系同色」——直接用 payload 的派系色，
    // 与图下清单对得上；上面那幅「A 股披露 TOP10」每家一色，两者互补。
    if (document.getElementById('chart-holders-faction')) {
        const facData = factions.map(f => ({
            name: f.title,
            value: +f.names.reduce((a, n) => a + val(n), 0).toFixed(2),
            itemStyle: { color: isResidualSlice(f.title) ? residualFill() : f.color }
        })).sort((a, b) => {
            // 「其他流通股东」是残余项、不是一个真派系，不参与比例排序，一律垫到最后
            const ra = isResidualSlice(a.name) ? 1 : 0, rb = isResidualSlice(b.name) ? 1 : 0;
            return ra !== rb ? ra - rb : b.value - a.value;
        });
        initChart('chart-holders-faction')?.setOption({
            backgroundColor: '#fff',
            title: [],
            tooltip: {
                trigger: 'item', textStyle: { fontSize: 18 },
                formatter: p => {
                    const f = factions.find(x => x.title === p.name) || { names: [] };
                    const detail = f.names.length > 1
                        ? '<br>' + f.names.map(n => `${n} ${val(n)}%`).join('<br>') : '';
                    return `${p.name}：${p.value}%（占总股本）${detail}`;
                }
            },
            series: holderPieSeries({ data: facData })
        });
    }

    // A+H 合并明细图：H 股名义持有人账户（香港中央结算（代理人））按港交所 SFO 披露拆开，
    // H 股持股折算成占总股本比例后与 A 股具名股东并列；沪股通（香港中央结算有限公司）与
    // 未达披露线的 H 股股东一起并入「其他股东」。数据由页面注入 D['holders-through']，
    // 只有注入了该键、且页面上有对应容器时才画（其余银行页 / 正式股东页不受影响）。
    if (D['holders-through'] && document.getElementById('chart-holders-through')) {
        const thr = D['holders-through'];
        const thrData = pieColorize((thr.holderData || []).slice().sort((a, b) => {
            // 「其他股东」是残余项，不参与比例排序，垫最后一位
            const ra = isResidualSlice(a.name) ? 1 : 0, rb = isResidualSlice(b.name) ? 1 : 0;
            return ra !== rb ? ra - rb : (b.value || 0) - (a.value || 0);
        }));
        initChart('chart-holders-through')?.setOption({
            backgroundColor: '#fff',
            title: [],
            tooltip: {
                trigger: 'item', textStyle: { fontSize: 18 },
                formatter: p => {
                    const d = thrData[p.dataIndex] || {};
                    return `${p.name}：${p.value}%（占总股本）` + (d.tag ? `<br><span style="color:#888">${d.tag}</span>` : '');
                }
            },
            series: holderPieSeries({ data: thrData })
        });
    }

    // A+H 合并明细图 · 按派系合并：把上面那张里同一派系（一致行动人 / 同一控股股东）的股东
    // 合并成一个扇区，口径仍是折算后的「占总股本比例」。派系划分随 D['holders-through'].factions
    // 由页面注入（合并后多了复星系、JPMorgan 等 H 股股东，和 A 股口径的派系表不是一份），
    // 颜色沿用派系色、「其他股东」仍垫最后一位。
    if (D['holders-through'] && (D['holders-through'].factions || []).length &&
        document.getElementById('chart-holders-through-faction')) {
        const thrF = D['holders-through'];
        const rawT = thrF.holderData || [];
        const valT = n => (rawT.find(d => d.name === n) || {}).value || 0;
        const facT = thrF.factions.map(f => ({
            name: f.title,
            short: f.short,
            value: +f.names.reduce((a, n) => a + valT(n), 0).toFixed(2),
            itemStyle: { color: isResidualSlice(f.title) ? residualFill() : f.color },
            members: f.names
        })).sort((a, b) => {
            const ra = isResidualSlice(a.name) ? 1 : 0, rb = isResidualSlice(b.name) ? 1 : 0;
            return ra !== rb ? ra - rb : b.value - a.value;
        });
        initChart('chart-holders-through-faction')?.setOption({
            backgroundColor: '#fff',
            title: [],
            tooltip: {
                trigger: 'item', textStyle: { fontSize: 18 },
                formatter: p => {
                    const f = facT[p.dataIndex] || { members: [] };
                    const detail = f.members.length > 1
                        ? '<br>' + f.members.map(n => `${n} ${valT(n).toFixed(2)}%`).join('<br>') : '';
                    return `${p.name}：${p.value}%（占总股本）${detail}`;
                }
            },
            series: holderPieSeries({ data: facT })
        });
    }

    if (D['holders-h'] && document.getElementById('chart-holders-h')) {
        const hH = D['holders-h'];
        initChart('chart-holders-h')?.setOption({
            backgroundColor: '#fff',
            title: [],
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占总股本）` },
            series: holderPieSeries({ data: stripeResidual(pieOrderTopAtNoon(hH.holderData, D['holders'].holders)) })
        });
        const valH = n => hH.holderData.find(d => d.name === n).value;
        const legH = document.getElementById('holders-legend-h');
        if (legH) legH.innerHTML = hH.factions.map(f => {
            const sum = f.names.reduce((a, n) => a + valH(n), 0);
            const items = f.names.map(n => `${n} ${valH(n)}%`).join('　');
            return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${/^其他/.test(f.title) ? RESIDUAL_SWATCH_CSS : f.color};vertical-align:-1px;margin-right:6px"></span>` +
                   `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#16a085;font-weight:600">${sum.toFixed(2)}%</span>` +
                   (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
        }).join('');
    }

    // 只看 H 股内部：SFO 披露的持 H 股 ≥5% 主要股东，占 H 股总股本口径，数据取自 D['holders-h-only']
    if (D['holders-h-only'] && document.getElementById('chart-holders-h-only')) {
        const hO = D['holders-h-only'];
        initChart('chart-holders-h-only')?.setOption({
            backgroundColor: '#fff',
            title: [],
            tooltip: { trigger: 'item', textStyle: { fontSize: 18 }, formatter: p => `${p.name}：${p.value}%（占 H 股总股本）` },
            series: holderPieSeries({ data: stripeResidual(hO.holderData) })
        });
        const valO = n => hO.holderData.find(d => d.name === n).value;
        const legO = document.getElementById('holders-legend-h-only');
        if (legO) legO.innerHTML = hO.factions.map(f => {
            const sum = f.names.reduce((a, n) => a + valO(n), 0);
            const items = f.names.map(n => `${n} ${valO(n)}%`).join('　');
            return `<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${/^其他/.test(f.title) ? RESIDUAL_SWATCH_CSS : f.color};vertical-align:-1px;margin-right:6px"></span>` +
                   `<b style="color:#4a2a5a">${f.title}</b> <span style="color:#16a085;font-weight:600">${sum.toFixed(2)}%</span>` +
                   (f.names.length > 1 ? `　<span style="color:#777;font-size:18px">（${items}）</span>` : '') + `</div>`;
        }).join('');
    }

    // 原「股东持股比例条形图」（横向 · 同派系同色）已删：与上面几张环形/派系图口径完全一样，
    // 明细数值看图下派系清单和底部明细表即可，条形图只是同一份数据换个画法。
};
window.__renderYnsHolders(D);

/* ────── 3b. 历年股东持股集中度（独立板块 · 第一大 / 前三大 / 前十大 三张柱状图） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolderConcentration）重绘。
 * 数据来源：东方财富 F10「前十名股东」接口按报告期（含季报）汇总，只取 IS_REPORT=1 的定期报告期。
 * 接口里还混着 IS_REPORT=0 的事件型快照（如 2022-12-22——隆鑫控股 4.33 亿股过户给重庆发展投资那天），
 * 这类快照只列受影响的前几名（2022-12-22 仅 4 行），算不出前十大合计，已在生成阶段整期剔除。
 * 三个口径各占一张全宽柱状图，而不是叠在一张图里：量级差得远（渝农商第一大 22% 上下、前三大 37.8%、
 * 前十大 55%~67%），共用一条 15~70 的轴时第一大 / 前三大那点年际差（<0.2pp）会被完全压平。
 * 横轴改成「每年一根柱」：原先按报告期画，一年四个点里三个是季报的重复值，柱子只会更密而不更有信息；
 * 每年取该年最后一个已披露报告期（最新年份即最近一期，柱标签里注明月日）。
 * 2010–2018 的港交所（03618 H 股年报）口径单独作为一个 series 披露（holder-concentration-hist，
 * 图例「港交所披露」、同色系浅色柱），与 2019 年起的 A 股定期报告口径分开；
 * 其中 2010–2017 是重构合并 A+H 口径，柱身再加红色虚线框，与 2018 年报披露原值区分。 */
window.__renderYnsHolderConcentration = function (D) {
    if (!document.getElementById('chart-conc-top10')) return;   // 仅股东页
    const IDS = ['chart-conc-top1', 'chart-conc-top3', 'chart-conc-top10'];
    const cur  = (D['holder-concentration'] || {}).raw || [];
    const hist = (D['holder-concentration-hist'] || {}).raw || [];
    if (!cur.length && !hist.length) { IDS.forEach(__stub); return; }
    // 第一大股东逐期可能换人/改名（工行的汇金 vs 财政部、招行的招商局系），并行数组按期给名字
    const t1Names = (D['holder-concentration'] || {}).top1Names || [];
    // 剔除「香港中央结算」名义持有人后的第一大 / 前三大（占总股本 %）与其第一大实益股东名：
    // A+H 银行的名义第一大恒为香港中央结算（代理人 / 沪深股通），剔除后才看得出真正的实益股东。
    // 只有 A 股定期报告口径（cur）算得出（有逐户明细），港交所 H 股年报口径（hist）无此数据。
    const t1Ex   = (D['holder-concentration'] || {}).top1Ex || [];
    const t3Ex   = (D['holder-concentration'] || {}).top3Ex || [];
    const t1ExNm = (D['holder-concentration'] || {}).top1ExNames || [];

    // hist(年度) + cur(报告期) 合成一条序列，再按年取该年最后一期；
    // 同一年两边都有时后 push 的 cur（A 股披露原值）覆盖 hist 重构值（用 >= 保证）
    // src 记住这一年的数据出自哪个交易所的披露：'H' = 港交所年报，'A' = 沪/深交易所定期报告。
    // 两者分成两个 series 单独画（见下），不再混进同一根序列里。
    const rows = hist.map(r => ({ date: r[0], t1: r[1], t3: r[2], t10: r[3],
                                  recon: r[4] === 'recon', t1name: '', src: 'H',
                                  t1ex: null, t3ex: null, t1exname: '' }))
        .concat(cur.map((r, i) => ({ date: r[0], t1: r[1], t3: r[2], t10: r[3],
                                     recon: false, t1name: t1Names[i] || '', src: 'A',
                                     t1ex: t1Ex[i], t3ex: t3Ex[i], t1exname: t1ExNm[i] || '' })));
    const byYear = new Map();
    rows.forEach(r => {
        const y = String(r.date).slice(0, 4);
        const prev = byYear.get(y);
        if (!prev || r.date >= prev.date) byYear.set(y, r);
    });
    const items = Array.from(byYear.keys()).sort().map(y => byYear.get(y));
    // 年末口径的柱只写年份；非年末（最新一期）补上月日，免得当成整年数
    const labels = items.map(it => it.date.slice(5) === '12-31'
        ? it.date.slice(0, 4) : it.date.slice(0, 4) + '\n(' + it.date.slice(5) + ')');

    // 港交所上市（H 股年报）口径的数据单独作为一个 series 披露，不与 A 股定期报告口径合成一根柱：
    // 两者披露主体、股东表范围都不同（H 股年报里 HKSCC 名义持有人代持全部 H 股，A 股定期报告的
    // 前十大是登记在册股东），混成一条序列会让人误以为是同一张表的连续读数。
    // 图例里各占一项、颜色深浅区分，legend 只列本行实际存在的来源。
    const SRC = {
        H: { name: '港交所披露（H 股年报口径）', tip: '港交所 H 股年报披露' },
        A: { name: 'A 股定期报告披露（沪 / 深交易所）', tip: 'A 股定期报告披露' }
    };
    const srcOrder = ['H', 'A'].filter(s => items.some(it => it.src === s));

    // 三张图共用这一个 formatter：四个口径（第一大 / 前三大 / 前十大 / 其他流通股东）一次列全，
    // 当前图画的那个加粗，其余灰显作参照——否则切到另一张图就查不到同年的别的口径。
    // 表头写明这一年的数据取自哪个交易所的披露（港交所年报 / A 股定期报告），口径不同不要看串。
    const pct = v => v == null ? '缺口' : v + '%';
    const concFormatter = own => p => {
        const it = items[p[0].dataIndex];
        const head = it.date
            + ' <span style="color:#888">· ' + SRC[it.src].tip + '</span>'
            + (it.recon ? ' <span style="color:#c0392b">（重构合并 A+H 口径）</span>' : '');
        const rs = [
            ['第一大股东' + (it.t1name ? '（' + it.t1name + '）' : ''), pct(it.t1), '第一大']
        ];
        // 剔除香港中央结算名义持有人后的第一大实益股东，仅 A 股口径且与含 HKSCC 值不同时才列
        if (it.t1ex != null && it.t1ex !== it.t1)
            rs.push(['　└ 剔除香港中央结算' + (it.t1exname ? '（' + it.t1exname + '）' : ''),
                     pct(it.t1ex), '第一大剔除']);
        rs.push(['前三大股东合计', pct(it.t3), '前三大']);
        if (it.t3ex != null && it.t3ex !== it.t3)
            rs.push(['　└ 剔除香港中央结算', pct(it.t3ex), '前三大剔除']);
        rs.push(['前十大股东合计', pct(it.t10), '前十大']);
        rs.push(['其他流通股东', it.t10 == null ? '缺口' : (100 - it.t10).toFixed(2) + '%', '其他']);
        return head + '<br/>' + rs.map(([k, v, tag]) => (tag === own || tag === own + '剔除')
            ? k + ' <b>' + v + '</b>'
            : '<span style="color:#999">' + k + ' ' + v + '</span>').join('<br/>');
    };

    /* 一张柱图：key 取 items 里的字段，own 决定 tooltip 里哪行加粗。
     * 轴按数据取整、不从 0 起（各行水平差得远：渝农商前十大 54~67%、招行 60%+、天津银行 80%+；
     * 从 0 起画时 5pp 的 U 形只占图高一成），绝对水平看柱顶数值。
     * 按披露来源拆成两个 series（港交所 H 股年报 / A 股定期报告）：同一年只会落在其中一个 series，
     * 故用 barGap:'-100%' 让两个 series 占同一个槽位，柱子仍居中、仍是满宽。 */
    const mkBar = (id, key, own, colors, exKey) => {
        if (!document.getElementById(id)) return;
        const vals = items.map(it => it[key]);
        if (!vals.some(v => v != null)) { __stub(id); return; }
        // 剔除香港中央结算后的实益股东占比：仅 A 股口径有、且与含 HKSCC 值不同的年份才画红线。
        // 纯 A 股行（HKSCC 不在前列）ex 恒等于含值，此时不画线、退化成普通单序列柱图。
        const exVals = exKey ? items.map(it => it[exKey]) : [];
        const showEx = exKey && items.some((it, i) => exVals[i] != null && exVals[i] !== vals[i]);
        // 红线 ex 值恒小于柱高（剔除了名义第一大），轴范围要把 ex 一并纳入，否则线落到轴下看不见；
        // 两者同轴（都是「占总股本 %」）直接可比，柱顶是名义值、红线是剔除 HKSCC 的真实实益值。
        const ax = niceAxis(showEx ? vals.concat(exVals).filter(v => v != null) : vals, 1);
        // 柱多了柱顶横排数值会连成一串（招行 2001 起 26 根柱时 "17.95%17.95%…" 直接叠住），
        // 超过 20 根就把数值竖排：柱宽 46px 容得下一列字，仍能逐柱读数；同时给顶部多留白。
        // （20 根以内横排还留得下——渝农商 17 根柱时 "58.91%" 各占 70px 互不相碰。）
        const dense = items.length > 20;
        const EX_NAME = '剔除香港中央结算';
        const hasLegend = srcOrder.length > 1 || showEx;   // 单一来源且无红线时不占图例行
        const legendData = srcOrder.map(s => SRC[s].name).concat(showEx ? [EX_NAME] : []);
        const series = srcOrder.map(s => ({
            name: SRC[s].name, type: 'bar', barMaxWidth: 46,
            barGap: '-100%',   // 两个来源共用同一个槽位（同一年只有一个来源有值）
            // 港交所口径里 2010–2017 是重构值，柱身再加红色虚线框，与年报披露原值区分
            data: items.map(it => it.src !== s ? null : ({
                value: it[key],
                itemStyle: it.recon
                    ? { color: colors[s], borderColor: '#c0392b',
                        borderType: 'dashed', borderWidth: 2 }
                    : { color: colors[s] }
            })),
            label: { show: true, position: 'top', fontSize: dense ? 14 : 15, fontWeight: 600,
                     color: colors[s], rotate: dense ? 90 : 0,
                     align: dense ? 'left' : 'center', verticalAlign: 'middle',
                     distance: dense ? 8 : 5,
                     formatter: p => p.value == null ? '' : p.value + '%' }
        }));
        // 红线：剔除香港中央结算名义持有人后的真实第一大 / 前三大实益占比（H 口径年份断线）
        if (showEx) series.push({
            name: EX_NAME, type: 'line', symbol: 'circle', symbolSize: 7, z: 5,
            lineStyle: { color: '#c0392b', width: 2 }, itemStyle: { color: '#c0392b' },
            data: exVals.map(v => v == null ? null : v),
            label: { show: !dense, position: 'bottom', fontSize: 14, fontWeight: 600,
                     color: '#c0392b', formatter: p => p.value == null ? '' : p.value + '%' }
        });
        initChart(id)?.setOption({
            backgroundColor: '#fff',
            textStyle: { fontSize: 18 },
            tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
                       axisPointer: { type: 'shadow' }, formatter: concFormatter(own) },
            legend: hasLegend
                ? { top: 0, itemGap: 24, textStyle: { fontSize: 16, color: '#555' },
                    data: legendData }
                : { show: false },
            grid: { left: 72, right: 32,
                    top: (dense ? 70 : 34) + (hasLegend ? 30 : 0), bottom: 78 },
            xAxis: {
                type: 'category', data: labels,
                axisLabel: { fontSize: 16, color: '#555', interval: 0, lineHeight: 18 },
                axisTick: { alignWithLabel: true },
                axisLine: { lineStyle: { color: '#bbb' } }
            },
            yAxis: {
                type: 'value', name: '占总股本 %',
                min: ax.min, max: ax.max, interval: ax.interval,
                nameTextStyle: { fontSize: 18 },
                axisLabel: { fontSize: 18, color: '#555', formatter: '{value}%' },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            series
        }, true);   // notMerge —— 切行时年份跨度不同，避免残留上一行的柱
    };

    // 每张图一个色系：A 股定期报告口径用深色（本行主色），港交所年报口径用同色系浅色。
    // 第一大 / 前三大再叠一条红线：剔除香港中央结算名义持有人后的真实实益占比（前十大不叠）。
    mkBar('chart-conc-top1',  't1',  '第一大', { A: '#16a085', H: '#8ccfc4' }, 't1ex');
    mkBar('chart-conc-top3',  't3',  '前三大', { A: '#2c6fb3', H: '#9dc0e3' }, 't3ex');
    mkBar('chart-conc-top10', 't10', '前十大', { A: '#6c3483', H: '#b99ac8' });
};
window.__renderYnsHolderConcentration(D);



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
});
