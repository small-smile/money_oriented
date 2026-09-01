/* 股权结构页（company/telecom/shareholder.html）
 * 数据来自 /api/telecom_annual 的 holders（东方财富公司数据接口的前十名股东快照，
 * 只有 holders_end_date 那一期）+ annual 里的 total_share（历年总股本）。
 *
 * 比例列的分母是**总股本**（holders 记录自带 total_shares），不是 A 股股本 ——
 * 中国移动的前十里 68.79% 的 BVI 与 25.96% 的香港中央结算（代理人）都是 H 股，
 * 若按 A 股基数重算会得出荒谬值，故这页一律写「占总股本」。
 */
const STATE_COLOR = {'加仓': '#c0392b', '减仓': '#1e8449', '新进': '#b45309', '不变': '#6b7280'};
const TYPE_COLOR = {'流通A股': '#1f6feb', '流通H股': '#0f766e'};

function shareFmt(v) {
    if (v === null || v === undefined) return '—';
    return (v / 1e8).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' 亿股';
}

/* change 字段是接口原样字符串：数字（含负号）、「不变」「新进」 */
function changeCell(h) {
    const raw = h.change;
    if (raw === null || raw === undefined || raw === '') return '<td class="num" style="color:#9ca3af">—</td>';
    const n = Number(raw);
    if (!isNaN(n) && raw !== '不变' && raw !== '新进') {
        const color = n > 0 ? STATE_COLOR['加仓'] : (n < 0 ? STATE_COLOR['减仓'] : '#6b7280');
        const sign = n > 0 ? '+' : '';
        return '<td class="num" style="color:' + color + '">' + sign + n.toLocaleString('zh-CN') + '</td>';
    }
    return '<td class="num" style="color:' + (STATE_COLOR[raw] || '#6b7280') + '">' + raw + '</td>';
}

function renderHead(d, holders) {
    const base = (holders[0] && holders[0].total_shares) || null;
    const sum10 = holders.reduce((s, h) => s + (h.hold_num || 0), 0);
    const byType = {};
    holders.forEach(h => { byType[h.shares_type || '未标注'] = (byType[h.shares_type || '未标注'] || 0) + (h.hold_num || 0); });
    document.title = d.name + '（' + d.secucode + '）· 股权结构';
    document.getElementById('page-title').textContent = d.name + '（' + d.secucode + '）· 股权结构';
    document.getElementById('page-meta').innerHTML =
        '报告期末 <b>' + (d.holders_end_date || '—') + '</b> 的前十名股东快照 · 比例分母为总股本 ' +
        shareFmt(base) + '<br>' + (d.h_same_entity
            ? '同一法人两地上市，H 股与 A 股同在一张股东名册上，前十里两类股份混排'
            : '<b>600050 与红筹 00762.HK 不是同一法人</b>：本表是 A 股主体的股东名册，红筹在其上层');

    document.getElementById('kpi-title').textContent = '股东结构概览';
    document.getElementById('kpi-sub').textContent =
        '增减与「新进／不变」为接口原样字段，不做推算；比例为占总股本';
    const card = (label, value, sub) => '<div class="kpi"><div class="label">' + label + '</div>' +
        '<div class="value">' + value + '</div>' +
        (sub ? '<div class="delta" style="color:#7f8c8d">' + sub + '</div>' : '') + '</div>';
    const top = holders[0] || {};
    const cards = [
        card('第一大股东持股', fmt(top.ratio, 2) + ' %', (top.name || '').slice(0, 16)),
        card('前十名合计', base ? fmt(sum10 / base * 100, 2) + ' %' : '—', shareFmt(sum10)),
        card('总股本', shareFmt(base), '报告期末口径')
    ];
    Object.keys(byType).sort().forEach(t => {
        cards.push(card('前十中 ' + t, base ? fmt(byType[t] / base * 100, 2) + ' %' : '—', shareFmt(byType[t])));
    });
    document.getElementById('kpis').innerHTML = cards.join('');
    document.getElementById('entity-note').innerHTML = '<b>主体口径：</b>' + mdBold(d.source);
    document.getElementById('sec-kpi').hidden = false;
    return {base: base, sum10: sum10};
}

const HOLDER_NOTES = {
    '600941': '<b>前十名里前三位都是 H 股</b>：中国移动香港（BVI）68.79%、香港中央结算（代理人）25.96% —— ' +
        '后者是港股中央结算的名义持有人，代持全部港股散户与机构，不是一个真实股东。' +
        'A 股股东从第 4 位起，全部是央企与保险／指数基金，单家不超过 0.2%，' +
        '说明 2022 年回 A 发行的股份高度分散。',
    '601728': '中国电信集团直接持股 63.9%，加上香港中央结算（代理人）15.11% 后前两名已占 79%。' +
        '第 3—7 位是广东广晟、浙江财开、江苏国信、福建投资开发等<b>地方国资平台</b>，' +
        '这是 2002 年电信南北分拆重组时地方资本入股留下的结构。',
    '600050': '<b>混改的痕迹全在这张表里</b>：联通集团只直接持股 36.46%，' +
        '腾讯信达 5.15%、阿里创业投资 2.03%、百度鹏寰 1.40% 等 2017 年混改引入的战投仍在名册上，' +
        '中国人寿 10.20% 与结构调整基金 5.69% 是同期的财务投资人。' +
        '注意本表是 A 股主体 600050 的股东，红筹 00762.HK 在其上层。'
};

function buildCharts(d, holders, agg) {
    const host = document.getElementById('charts');

    // ① 十大股东持股比例（横向条形，按股份类别着色）
    (function () {
        const rows = holders.slice().reverse();   // 横向条形从下往上画，倒序让第一名在顶
        const c = chartCard(host, {
            id: 'holders', title: '前十名股东持股比例', sub: '横条：占总股本（%）· 颜色区分流通 A 股与流通 H 股',
            note: HOLDER_NOTES[CODE],
            detail: '<b>比例分母是总股本：</b>H 股与 A 股同在一张名册上，若按 A 股基数重算会把 H 股股东的比例放大到荒谬值。<br>' +
                '<b>「港股股东A／B」不是我起的名：</b>接口对部分港股股东不给具体名称，原样保留，' +
                '不去猜测或补全。'
        }, '58vh');
        c.setOption({
            tooltip: {
                trigger: 'item',
                formatter: p => p.name + '<br><b>' + fmt(p.value, 2) + ' %</b>　' +
                    shareFmt(rows[p.dataIndex].hold_num) + '<br>' +
                    (rows[p.dataIndex].shares_type || '') + '　' + (rows[p.dataIndex].state || '')
            },
            grid: {left: 300, right: 90, top: 20, bottom: 40},
            xAxis: Object.assign({}, AXIS_Y, {name: '% ', type: 'value'}),
            yAxis: {
                type: 'category',
                data: rows.map(h => (h.name || '').length > 24 ? (h.name || '').slice(0, 23) + '…' : h.name),
                axisLabel: {fontSize: 13}, axisTick: {show: false}
            },
            series: [{
                type: 'bar', barMaxWidth: 22,
                label: {show: true, position: 'right', fontSize: 13, formatter: p => fmt(p.value, 2) + '%'},
                itemStyle: {color: p => TYPE_COLOR[rows[p.dataIndex].shares_type] || '#94a3b8'},
                data: rows.map(h => h.ratio)
            }]
        });
    })();

    // ② 持股集中度：第一大股东 / 第 2—10 名 / 名册外其余股份，一条 100% 横条
    (function () {
        if (!agg.base) return;
        const first = holders[0] ? holders[0].hold_num : 0;
        const next9 = agg.sum10 - first;
        const rest = agg.base - agg.sum10;
        const pct = v => +(v / agg.base * 100).toFixed(2);
        const seg = [
            {name: '第一大股东', value: pct(first), color: '#10243e'},
            {name: '第 2—10 名股东', value: pct(next9), color: META.color},
            {name: '名册外其余股份', value: pct(rest), color: '#cbd5e1'}
        ];
        const c = chartCard(host, {
            id: 'concentration', title: '持股集中度', sub: '一条 100% 横条：第一大股东／第 2—10 名／前十名之外的全部股份（占总股本 %）',
            note: '第一大股东与名册外股份的比例，是判断这家公司「实际可流通筹码」的第一个数：' +
                (CODE === '600941' ? '中国移动的名册外股份不足 6%，绝大部分股权集中在控股 BVI 与港股代理人手里。'
                    : CODE === '601728' ? '中国电信除集团与港股代理人外，还有一批地方国资长期持有，真正的自由流通盘不大。'
                        : '中国联通名册外股份超过三成，是三家里筹码最分散的，也与其 A 股上市最早、混改引入多家战投有关。'),
            detail: '<b>「名册外其余股份」不等于自由流通盘：</b>它只是总股本减去前十名，里面仍包含第 11 名之后的' +
                '国资平台、战投、指数基金与港股代理人未穿透的部分。接口只给前十名，无法再往下拆。'
        }, '26vh');
        c.setOption({
            tooltip: {trigger: 'axis', axisPointer: {type: 'shadow'}, valueFormatter: v => fmt(v, 2) + ' %'},
            legend: {top: 0, itemGap: 16, textStyle: {fontSize: 15}},
            grid: {left: 40, right: 40, top: 48, bottom: 30},
            xAxis: Object.assign({}, AXIS_Y, {type: 'value', max: 100, name: '%'}),
            yAxis: {type: 'category', data: [''], axisTick: {show: false}},
            series: seg.map(s => ({
                name: s.name, type: 'bar', stack: 'all', barWidth: 46,
                itemStyle: {color: s.color},
                label: {show: s.value >= 4, fontSize: 14, color: s.color === '#cbd5e1' ? '#374151' : '#fff',
                    formatter: () => fmt(s.value, 1) + '%'},
                data: [s.value]
            }))
        });
    })();
}

function renderTable(d, holders, agg) {
    document.getElementById('tbl-sub').innerHTML =
        '报告期末 ' + (d.holders_end_date || '—') + ' · 「报告期内增减」与「新进／不变」为接口原样字段' +
        '（增红／减绿／新进橙），缺失显示「—」，不做推算 · 占比分母为总股本 ' + shareFmt(agg.base);
    document.getElementById('tbl-body').innerHTML = holders.map(h =>
        '<tr><td class="num">' + h.rank + '</td>' +
        '<td class="nm">' + (h.name || '—') + '</td>' +
        '<td class="num">' + (h.hold_num === null || h.hold_num === undefined ? '—' : h.hold_num.toLocaleString('zh-CN')) + '</td>' +
        changeCell(h) +
        '<td class="num">' + fmt(h.ratio, 2) + '%</td>' +
        '<td class="nat">' + (h.shares_type || '—') + '</td></tr>').join('');
    document.getElementById('tbl-foot').innerHTML =
        '<tr class="row-total"><td class="num"></td><td class="nm">前十名合计</td>' +
        '<td class="num">' + agg.sum10.toLocaleString('zh-CN') + '</td>' +
        '<td class="num" style="color:#6b7280">见各行</td>' +
        '<td class="num">' + (agg.base ? fmt(agg.sum10 / agg.base * 100, 2) : '—') + '%</td>' +
        '<td class="nat"></td></tr>';
    document.getElementById('sec-table').hidden = false;
}

function renderGaps(d) {
    const gaps = [
        '<b>只有一期快照</b>：接口的前十名股东只返回最新报告期（本页为 ' + (d.holders_end_date || '—') +
        '），历年各期未入库，因此这页没有股东结构的时间序列。',
        '<b>总股本字段不可当历史看</b>：接口的 <code>total_share</code> 是当前值、被回填到每一年' +
        '（三家的历年值都完全相同），所以本页<b>不画</b>历年总股本 —— 回 A 发行与 2017 年混改定增造成的股本台阶' +
        '在这份数据里看不出来，要看得回年报的股本变动表。',
        '<b>香港中央结算（代理人）有限公司不是真实股东</b>：它是港股中央结算的名义持有人，' +
        '代持全部港股投资者的股份，穿透不了。',
        '<b>接口对部分港股股东不给名称</b>（如「港股股东A／B」），原样保留、不猜测补全。'
    ];
    if (!d.h_same_entity) {
        gaps.push('<b>主体口径</b>：本表是 A 股主体 600050 的股东名册；红筹 00762.HK 是另一法人、在其上层，' +
            '两张名册不可混看。');
    }
    document.getElementById('gaps').innerHTML = gaps.map(g => '<li>' + g + '</li>').join('');
    document.getElementById('sec-gaps').hidden = false;
}

loadCompany(function (d) {
    const holders = (d.holders || []).slice().sort((a, b) => (a.rank || 99) - (b.rank || 99));
    if (!holders.length) {
        const box = document.getElementById('error-msg');
        box.style.display = 'block';
        box.textContent = '本公司暂无股东数据，请重跑 data/extract/fetch_telecom_financials.py';
        return;
    }
    const agg = renderHead(d, holders);
    buildCharts(d, holders, agg);
    renderTable(d, holders, agg);
    renderGaps(d);
});
