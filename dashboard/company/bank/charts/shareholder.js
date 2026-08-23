/* 股东回报与股本：每 10 股分红、历年总股本、历年股东户数。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 1j2. 历年每 10 股分红（元，含税，按年度累计） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsDividend）重绘。 */
window.__renderYnsDividend = function (D) {
    if (!document.getElementById('chart-dividend-per10')) return;   // 仅股东页
    // 2011–2018：03618 港股年报「盈利与股息」披露的内资股/H股每股派息（元）× 10；2010 年董事会未提常规股息（仅 IPO 前特别股息，口径不可比，未纳入）
    // 2019–2025：本行 A 股年度报告「利润分配方案」披露的每 10 股股利
    const years9 = D['dividend-per10'].years9;
    const per10  = D['dividend-per10'].per10;

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
};
window.__renderYnsDividend(D);

/* ────── 1j2b. 历年总股本变动（IPO / 定增 / 增发等资本运作导致的股份数量变化） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsShareCapital）重绘。
 * 载荷 D['share-capital'] = { years, shares(亿股), gaps?, base?, events? }：
 *   · years/shares 为逐年年末总股本，来自资产负债表「股本」科目（面值 1 元，元金额即股数）；
 *   · gaps 为该行披露缺失、整年剔除的年份（如农行 2002–2006），只写进脚注不插值；
 *   · base 为首年之前的期初股本（渝农商 2008 改制时 60 亿股），有它首年才画得出增量；
 *   · events 为 {年: {type, items[]}} 的手工明细（只有渝农商精编了 5 次资本运作的成因）。
 * 生成脚本给不出成因分类（F10 只有股本余额），故 events 缺失时全部点用中性色，
 * 增量标签也只在变动幅度 ≥ 上年 0.1% 时才显示——否则四舍五入的尾差会糊满全图。 */
window.__renderYnsShareCapital = function (D) {
    if (!document.getElementById('chart-share-capital')) return;   // 仅股东页
    const SC = (D && D['share-capital']) || {};
    const years = SC.years || [];
    if (!years.length) { __stub('chart-share-capital'); return; }
    const shares = SC.shares || [];
    const C = { base:'#95a5a6', ipo:'#c0392b', pp:'#e67e22', seo:'#16a085' };
    const EV = SC.events || {};
    let prev = SC.base != null ? SC.base : null;
    const rows = years.map((y, i) => {           // [年, 年末总股本, 当年增量(null=无从计算), 明细[], 色]
        const cur = shares[i];
        const ev = EV[y] || EV[String(y)];
        const d = prev == null ? null : +(cur - prev).toFixed(2);
        prev = cur;
        return [y, cur, d, ev ? (ev.items || []) : [], ev ? (C[ev.type] || C.base) : C.base];
    });
    // 「显著变动」阈值：上年股本的 0.1%（工行 3564 亿股约 3.5 亿股），滤掉四舍五入尾差
    const moved = rows.map((r, i) => r[2] != null && Math.abs(r[2]) >= (i ? shares[i - 1] : r[1]) * 0.001);
    const ax = niceAxis(shares, 1);
    const cum = rows.map(r => ({ value: r[1], itemStyle: { color: r[4] }, label: { color: r[4] } }));
    initChart('chart-share-capital')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: {
            trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => {
                const i = p[0].dataIndex, r = rows[i];
                const detail = r[3].length
                    ? '<br><span style="color:#888">' + r[3].join('<br>') + '</span>'
                    : (moved[i] ? '' : '<br><span style="color:#888">当年无股本变动</span>');
                const dLine = r[2] == null ? ''
                    : '<br>当年增量：' + (moved[i] ? (r[2] > 0 ? '+' : '') + r[2].toFixed(2) + ' 亿股' : '无');
                return `<b>${r[0]} 年末</b><br>总股本：${r[1].toFixed(2)} 亿股` + dLine + detail;
            }
        },
        grid: { left: 88, right: 60, top: 40, bottom: 46 },
        xAxis: {
            type: 'category', data: years, boundaryGap: false,
            axisLabel: { fontSize: 15, color: '#555',
                         interval: Math.max(0, Math.ceil(years.length / 24) - 1) },
            axisLine: { lineStyle: { color: '#bbb' } },
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value', name: '总股本（亿股）',
            min: ax.min, max: ax.max, interval: ax.interval,
            nameTextStyle: { color: '#555', fontSize: 18 },
            axisLabel: { color: '#555', fontSize: 18 },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: [{
            name: '总股本', type: 'line', step: 'end', data: cum,
            symbolSize: 11, lineStyle: { width: 3, color: '#6c3483' },
            areaStyle: { color: 'rgba(108,52,131,0.08)' },
            label: {
                show: true, position: 'top', fontSize: 15, fontWeight: 600,
                formatter: p => {
                    const d = rows[p.dataIndex][2];
                    return moved[p.dataIndex] ? (d > 0 ? '+' : '') + d.toFixed(2) : '';
                }
            },
            endLabel: { show: true, fontSize: 16, color: '#6c3483',
                        formatter: p => `${p.value} 亿股` }
        }]
    }, true);   // notMerge —— 切行时年份跨度不同，避免残留上一行的点
};
window.__renderYnsShareCapital(D);

/* ────── 1j3. 历年股东户数（2017-12 至今：H 股年报 + 历年定期报告披露值） ──────
 * 渝农商默认渲染；股东页银行切换器复用同一函数（window.__renderYnsHolderCount）重绘。 */
window.__renderYnsHolderCount = function (D) {
    if (!document.getElementById('chart-holder-count')) return;   // 仅股东页
    // [披露日, 股东总数, A 股股东, H 股股东] —— A/H 部分披露点未拆分, 保留 null
    // 数据源:
    //   · A 股 IPO 后 (2019-10 至今, 43 期): 本行历年定期报告（年报/中报/季报）「股东情况」章节披露值
    //   · A 股 IPO 前 H 股登记股东数 (2017/2018 年末, 2 期): 03618 港股年报「股本变动及股东情况」章节脚注
    //     -> data/tables/holder_count_hshare_2010_2018.json  (2010-2016 年报未披露该项)
    const raw = D['holder-count'].raw;
    const dates  = raw.map(r => r[0]);
    const total  = raw.map(r => r[1]);
    const aNum   = raw.map(r => r[2]);
    const hNum   = raw.map(r => r[3]);
    const fmt    = v => v == null ? '—' : v.toLocaleString('en-US');
    const wan    = v => v == null ? '—' : (v / 10000).toFixed(2) + ' 万';

    // 左轴单位随各行量级：大行 A 股几十万户按万户标，户数少的行直接按户标
    const inWan  = (D['holder-count'].unit || 'wan') === 'wan';
    const aName  = 'A 股股东数（左轴 · ' + (inWan ? '万户' : '户') + '）';

    /* H 股登记股东数各行差两三个数量级（渝农商 ~1.4 千户、招行 ~7 万户），
     * 原来写死的 1000/1500/100 只合渝农商；改用顶层 niceAxis 按数据取「整」区间。 */
    const hAx = niceAxis(hNum);

    /* 主线按各行实际披露的列挑：
     *   · 多数期次只有股东总数、没有 A/H 拆分（工行/中行/交行的早年季报）→ 主线用股东总数；
     *   · 纯 H 股上市行（天津银行 01578）年报只有 H 股登记股东数，总数与 A 股列整列为空
     *     → 把 H 股序列提为左轴主线并收起右轴，否则左轴一条线都画不出来。 */
    const uHu = inWan ? '万户' : '户';
    const aAll = aNum.every(v => v == null);
    const hOnly = aAll && total.every(v => v == null);
    const main = hOnly ? hNum : (aAll ? total : aNum);
    const mainName = hOnly ? ('H 股登记股东数（左轴 · ' + uHu + '）')
                   : aAll ? ('股东总数（A+H · 左轴 · ' + uHu + '）') : aName;

    const serHC = live([{
        name: mainName,
        type: 'line', data: main, smooth: true, symbolSize: 6,
        connectNulls: false,      // A 股仅定期报告披露, 未拆分的季报点留空断线
        lineStyle: { width: 3, color: '#2c6fb3' },
        itemStyle: { color: '#2c6fb3' },
        areaStyle: { color: 'rgba(44,111,179,0.10)' },
        endLabel: { show: true, fontSize: 18, color: '#2c6fb3',
                    formatter: p => p.value == null ? '' :
                        (inWan ? (p.value / 10000).toFixed(2) + ' 万' : p.value.toLocaleString('en-US') + ' 户') }
    }, {
        name: 'H 股登记股东数（右轴 · 户）',
        type: 'line', yAxisIndex: 1, data: hOnly ? [] : hNum,   // 已提为左轴主线时不再重复画
        smooth: true, symbolSize: 8,
        connectNulls: true,       // H 股只在年末/半年末披露, 跨越缺口连线
        lineStyle: { width: 2.5, color: '#16a085', type: 'solid' },
        itemStyle: { color: '#16a085' },
        endLabel: { show: true, fontSize: 16, color: '#16a085',
                    formatter: p => p.value == null ? '' : `${p.value.toLocaleString('en-US')} 户` }
    }]);

    initChart('chart-holder-count')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        legend: {
            data: serHC.map(s => s.name),
            top: 4, left: 'center', textStyle: { fontSize: 16 },
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
            // 披露期数各行差得远（渝农商 43 期、工行 93 期），固定 interval:2 在大行上会糊成一片
            axisLabel: { fontSize: 16, color: '#555', rotate: 40,
                         interval: Math.max(2, Math.ceil(dates.length / 18) - 1) },
            axisLine: { lineStyle: { color: '#bbb' } }
        },
        yAxis: [
            {
                type: 'value',
                name: (hOnly ? 'H 股登记股东（' : aAll ? '股东总数（' : 'A 股股东数（') + uHu + '）',
                min: 0, position: 'left',
                nameTextStyle: { color: '#2c6fb3', fontSize: 18 },
                axisLabel: { color: '#2c6fb3', fontSize: 18,
                             formatter: v => inWan ? (v / 10000).toFixed(0) : v.toLocaleString('en-US') },
                splitLine: { lineStyle: { color: '#eee' } }
            },
            {
                type: 'value', name: 'H 股股东（户）', show: !hOnly && hAx.min != null,
                min: hAx.min, max: hAx.max, interval: hAx.interval,
                position: 'right',
                nameTextStyle: { color: '#16a085', fontSize: 18 },
                axisLabel: { color: '#16a085', fontSize: 18, formatter: v => v.toLocaleString('en-US') },
                splitLine: { show: false }
            }
        ],
        series: serHC
    });
};
window.__renderYnsHolderCount(D);

});
