/* 股权结构页（dashboard/company/bank/shareholder.html）—— 全站唯一一份，银行/险企/开发商/水泥/
 * 运营商/百度/巴比共用；各板块只有顶部 header 不同（银行 bank-header.js，其余 site-header.js），
 * 正文、图、表完全一样。页面文件放在 bank/ 目录下，脚本与样式在上一级（../shareholder.js|css）。
 *
 * 各板块的 <板块>_<code>_annual.json 里 holders 字段结构完全相同（东方财富公司数据接口的
 * 前十名股东快照），所以股权结构不按板块各写一份，全部走 /api/holders?industry=&code=。
 * 百度（tech:09888，20-F beneficial ownership 口径）与巴比食品（food:605338，年报名册）没有
 * annual 表，股东块整份来自 data/tables/holders_manual.json，页面照样这一套。
 * 银行的历年股本／每 10 股分红来自 company_charts_<code>.json（原先画在银行自己的年报口径
 * 股东页里，那一页已并入本页），户数与集中度序列来自 bank 表，手工层公司则来自年报原文抽取件 ——
 * 字段名一律与银行表对齐，所以图随数据层增减，不用为板块写分支。
 *
 * 比例列的分母是**总股本**（holders 记录自带 total_shares）：A+H 公司的名册上两类股份混排
 * （如中国移动前两名 BVI 68.79% 与香港中央结算(代理人) 25.96% 都是 H 股），
 * 按 A 股基数重算会得出荒谬值。年报口径的「占 A 股」在银行详情页那套里。
 */
const INDUSTRIES = [
    {id: 'bank', label: '银行'},
    {id: 'insurer', label: '险企'},
    {id: 'developer', label: '开发商'},
    {id: 'cement', label: '水泥'},
    {id: 'telecom', label: '运营商'},
    {id: 'tech', label: '百度'},
    {id: 'food', label: '食品'}
];
const Q = new URLSearchParams(location.search);
const IND = INDUSTRIES.some(i => i.id === Q.get('industry')) ? Q.get('industry') : 'bank';
const CODE = Q.get('code') || '';

const STATE_COLOR = {'加仓': '#c0392b', '减仓': '#1e8449', '新进': '#b45309', '不变': '#6b7280'};
const IND_COLOR = {bank: '#b45309', insurer: '#7c3aed', developer: '#c0392b', cement: '#475569',
    telecom: '#1f6feb', tech: '#0f766e', food: '#b91c1c'};

function fmt(v, d) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    return v.toLocaleString('zh-CN', {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0});
}

function mdBold(s) {
    return (s || '').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
}

function shareFmt(v) {
    if (v === null || v === undefined) return '—';
    return fmt(v / 1e8, 2) + ' 亿股';
}

/* 导航自己画：板块与公司都靠 query 切换，站点导航的固定链接带不了参数。
 * 成员多的板块（银行 45 家）用下拉，少的用按钮，省得导航条被 45 个链接撑爆。 */
function buildNav(data) {
    const nav = document.createElement('nav');
    nav.className = 'site-nav';
    // header 已经带了「行业看板」品牌，这一行就不重复挂，只有没有 header 时（食品板块）才挂
    const hdNav = document.querySelector('nav.site-nav');
    if (!hdNav) {
        const brand = document.createElement('a');
        brand.className = 'brand';
        // 本页是 dashboard/company/bank/shareholder.html（全站唯一一份股权结构页），回首页退两级
        brand.href = '../../index.html';
        brand.textContent = '📊 行业看板';
        nav.appendChild(brand);
    }
    for (const i of INDUSTRIES) {
        const a = document.createElement('a');
        a.href = '?industry=' + i.id;
        a.textContent = i.label;
        if (i.id === IND) a.className = 'active';
        nav.appendChild(a);
    }
    const sep = document.createElement('span');
    sep.className = 'sep';
    nav.appendChild(sep);
    const cur = data.company.code;
    if (data.roster.length > 8) {
        const sel = document.createElement('select');
        data.roster.forEach(r => {
            const o = document.createElement('option');
            o.value = r.code;
            o.textContent = r.name + (r.has_holders ? '' : '（无股东数据）');
            o.disabled = !r.has_holders;
            o.selected = r.code === cur;
            sel.appendChild(o);
        });
        sel.onchange = () => { location.search = '?industry=' + IND + '&code=' + sel.value; };
        nav.appendChild(sel);
    } else {
        data.roster.forEach(r => {
            const a = document.createElement('a');
            if (r.has_holders) {
                a.href = '?industry=' + IND + '&code=' + r.code;
            } else {
                a.style.cssText = 'opacity:.45;cursor:not-allowed';
                a.title = '接口不返回该公司股东数据（纯 H 股）';
            }
            a.textContent = r.name;
            if (r.code === cur) a.className = 'active';
            nav.appendChild(a);
        });
    }
    /* 这条切换行排在 header 下面：header 由页面按 ?industry= 选（银行 bank-header.js／
     * 其余 site-header.js），两个脚本都是动态注入、执行时机不定，所以这里不抢 body 首位，
     * 有 header 就插到它后面，没有（如食品板块）才自己占首位。 */
    if (hdNav) {
        hdNav.insertAdjacentElement('afterend', nav);
    } else {
        document.body.insertBefore(nav, document.body.firstChild);
    }
}

/* change 字段是接口原样字符串：数字（含负号）、「不变」「新进」 */
function changeCell(h) {
    const raw = h.change;
    if (raw === null || raw === undefined || raw === '') return '<td class="num" style="color:#9ca3af">—</td>';
    const n = Number(raw);
    if (!isNaN(n) && raw !== '不变' && raw !== '新进') {
        const color = n > 0 ? STATE_COLOR['加仓'] : (n < 0 ? STATE_COLOR['减仓'] : '#6b7280');
        return '<td class="num" style="color:' + color + '">' + (n > 0 ? '+' : '') + n.toLocaleString('zh-CN') + '</td>';
    }
    return '<td class="num" style="color:' + (STATE_COLOR[raw] || '#6b7280') + '">' + raw + '</td>';
}

function chartCard(cfg, height) {
    const wrap = document.createElement('div');
    wrap.className = 'chart-card';
    wrap.innerHTML = '<div class="chart-title">' + cfg.title +
        (cfg.sub ? '<span class="sub">' + cfg.sub + '</span>' : '') + '</div>' +
        '<div id="chart-' + cfg.id + '" style="height:' + (height || '58vh') + '"></div>' +
        (cfg.note ? '<div class="note" style="max-width:1100px;color:#6b7280;font-size:16px">' + cfg.note +
            (cfg.detail ? '<details class="note-more"><summary>展开详细口径</summary><div>' +
                cfg.detail + '</div></details>' : '') + '</div>' : '');
    document.getElementById('charts').appendChild(wrap);
    const chart = echarts.init(document.getElementById('chart-' + cfg.id));
    window.addEventListener('resize', () => chart.resize());
    return chart;
}

const AXIS = {
    type: 'value', nameTextStyle: {fontSize: 14},
    axisLabel: {fontSize: 14, formatter: v => v.toLocaleString('zh-CN')},
    splitLine: {lineStyle: {type: 'dashed', color: '#e5e7eb'}}
};

function renderHead(d) {
    const c = d.company, holders = c.holders;
    const base = (holders[0] && holders[0].total_shares) || null;
    const sum10 = holders.reduce((s, h) => s + (h.hold_num || 0), 0);
    const byType = {};
    holders.forEach(h => {
        const k = h.shares_type || '未标注';
        byType[k] = (byType[k] || 0) + (h.hold_num || 0);
    });
    const title = c.name + '（' + (c.secucode || c.code) + '）· 股权结构';
    document.title = title;
    document.getElementById('page-title').textContent = title;
    /* 两地代码：同一家公司在 A 股／港交所／美股各有一个代码，?code= 给哪个都落到这一家
     * （company_codes.json 的对应表）；两地不是同一法人的（中国联通 A 股与红筹）接口会拒绝互换 */
    const cd = c.codes || {};
    const mkts = [cd.a ? 'A 股 ' + cd.a : '', cd.h ? 'H 股 ' + cd.h : '', cd.us ? '美股 ' + cd.us : '']
        .filter(Boolean).join(' · ');
    document.getElementById('page-meta').innerHTML =
        d.label + (c.tag ? ' · ' + c.tag : '') + (mkts ? ' · ' + mkts : '') +
        ' · 报告期末 <b>' + (c.holders_end_date || '—') +
        '</b> 的前十名股东快照 · 比例分母为总股本 ' + shareFmt(base) + '<br>' +
        (c.code_note ? '<b>' + c.code_note + '</b><br>' : '') +
        '全站只有这一页股权结构（' + INDUSTRIES.map(i => i.label).join(' / ') +
        ' 共用，只有顶部导航按板块不同），数据层有多少就画多少图';

    document.getElementById('kpi-title').textContent = '股东结构概览';
    document.getElementById('kpi-sub').textContent =
        '增减与「新进／不变」为接口原样字段，不做推算；比例为占总股本';
    const card = (label, value, sub) => '<div class="kpi"><div class="label">' + label + '</div>' +
        '<div class="value">' + value + '</div>' +
        (sub ? '<div class="delta" style="color:#7f8c8d">' + sub + '</div>' : '') + '</div>';
    const top = holders[0] || {};
    const cards = [
        card('第一大股东持股', fmt(top.ratio, 2) + ' %', (top.name || '').slice(0, 18)),
        card('前十名合计', base ? fmt(sum10 / base * 100, 2) + ' %' : '—', shareFmt(sum10)),
        card('总股本', shareFmt(base), '报告期末口径')
    ];
    Object.keys(byType).sort().forEach(t => {
        cards.push(card('前十中 ' + t, base ? fmt(byType[t] / base * 100, 2) + ' %' : '—', shareFmt(byType[t])));
    });
    if (c.holder_num && c.holder_num.length) {
        const last = c.holder_num[c.holder_num.length - 1];
        cards.push(card('股东户数', fmt(last[1], 0) + ' 户', last[0] + ' 披露'));
        document.getElementById('tag-extra').hidden = false;
    }
    document.getElementById('kpis').innerHTML = cards.join('');
    document.getElementById('entity-note').innerHTML = '<b>主体口径：</b>' + mdBold(c.source);
    document.getElementById('sec-kpi').hidden = false;
    return {base: base, sum10: sum10};
}

/* 名册里的「股份类别」写法各板块不一：A 股公司是「流通A股／限售流通A股／流通H股」，
 * 百度那份 20-F 名册写的是「A 类 xxx + B 类 xxx」这种长句 —— 所以按关键字归几个大类着色，
 * 认不出来的一律灰色，不给每行都发一个新颜色（那样图上颜色比信息多）。 */
function typeColor(t) {
    const s = String(t || '').replace(/\s/g, '');
    if (/H股|限售流通H/.test(s)) return '#b45309';
    if (/B类/.test(s)) return '#0f766e';
    if (/限售/.test(s)) return '#7c3aed';
    if (/A股|A类/.test(s)) return IND_COLOR[IND] || '#1f6feb';
    return '#94a3b8';
}

function buildCharts(d, agg) {
    const c = d.company, holders = c.holders || [];
    /* 每张图下那段解读由接口按本公司自己的序列现算（narrative.<图 id>），
     * 原先银行那套年报口径股东页把这些话写死在 HTML 里，只对渝农商行成立；
     * 现在缺哪层数据就少哪段话，通用说明照旧接在后面。 */
    const NAR = c.narrative || {};
    const nar = id => (NAR[id] && NAR[id].text) ? mdBold(NAR[id].text) + ' ' : '';
    const narDetail = id => (NAR[id] && NAR[id].detail) ? mdBold(NAR[id].detail) + '<br>' : '';

    // ① 前十名股东各自的比例（横向条形，按股份类别着色）
    if (holders.length) {
        const rows = holders.slice().reverse();   // 横向条形从下往上画，倒序让第一名在顶
        const ch = chartCard({
            id: 'holders', title: '前十名股东持股比例',
            sub: '横条：占总股本（%）· 颜色按股份类别（A 股／H 股／限售股，百度按 A 类／B 类）',
            note: nar('holders') +
                '这张图与上面环形图是同一批数字的两种读法：环形图看的是<b>分组结构</b>' +
                '（谁和谁是一伙的、名册外还剩多少），横条看的是<b>逐名股东的量级差</b> —— ' +
                '第一名与第二名差几倍，这在环形图的角度上不好比。',
            detail: '<b>比例分母是总股本：</b>H 股与 A 股同在一张名册上，按 A 股基数重算会把 H 股股东的比例放大到荒谬值。<br>' +
                '<b>「港股股东A／B」不是本项目起的名：</b>接口对部分港股股东不给具体名称，原样保留，不猜不补全。'
        }, '58vh');
        ch.setOption({
            tooltip: {
                trigger: 'item',
                formatter: p => p.name + '<br><b>' + fmt(p.value, 2) + ' %</b>　' +
                    shareFmt(rows[p.dataIndex].hold_num) +
                    (rows[p.dataIndex].shares_type ? '<br><span style="color:#888">' +
                        rows[p.dataIndex].shares_type + '</span>' : '')
            },
            grid: {left: 300, right: 90, top: 20, bottom: 40},
            xAxis: Object.assign({}, AXIS, {name: '%'}),
            yAxis: {
                type: 'category',
                data: rows.map(h => (h.name || '').length > 24 ? (h.name || '').slice(0, 23) + '…' : h.name),
                axisLabel: {fontSize: 13}, axisTick: {show: false}
            },
            series: [{
                type: 'bar', barMaxWidth: 22,
                label: {show: true, position: 'right', fontSize: 13, formatter: p => fmt(p.value, 2) + '%'},
                itemStyle: {color: p => typeColor(rows[p.dataIndex].shares_type)},
                data: rows.map(h => h.ratio)
            }]
        });
    }

    // ② 持股集中度：第一大股东 / 第 2—10 名 / 名册外其余股份，一条 100% 横条
    if (agg && agg.base && holders.length) {
        const first = holders[0].hold_num || 0;
        const pct = v => +(v / agg.base * 100).toFixed(2);
        const seg = [
            {name: '第一大股东', value: pct(first), color: '#10243e'},
            {name: '第 2—10 名股东', value: pct(agg.sum10 - first), color: IND_COLOR[IND] || '#1f6feb'},
            {name: (c.residual_label || '名册外其余股份'), value: pct(agg.base - agg.sum10), color: '#cbd5e1'}
        ];
        const ch = chartCard({
            id: 'concentration', title: '持股集中度',
            sub: '一条 100% 横条：第一大股东／第 2—10 名／名册之外的全部股份（占总股本 %）',
            note: '第一大股东与名册外股份的比例，是判断这家公司「实际可流通筹码」的第一个数。',
            detail: '<b>「名册外其余股份」不等于自由流通盘：</b>它只是总股本减去名册合计，里面仍包含第 11 名之后的' +
                '国资平台、战投、指数基金与港股代理人未穿透的部分 —— 名册只给到前十名，无法再往下拆。' +
                (c.caliber_note ? '<br>' + mdBold(c.caliber_note) : '')
        }, '26vh');
        ch.setOption({
            tooltip: {trigger: 'axis', axisPointer: {type: 'shadow'}, valueFormatter: v => fmt(v, 2) + ' %'},
            legend: {top: 0, itemGap: 16, textStyle: {fontSize: 15}},
            grid: {left: 40, right: 40, top: 48, bottom: 30},
            xAxis: Object.assign({}, AXIS, {max: 100, name: '%'}),
            yAxis: {type: 'category', data: [''], axisTick: {show: false}},
            series: seg.map(s => ({
                name: s.name, type: 'bar', stack: 'all', barWidth: 46,
                itemStyle: {color: s.color},
                label: {show: s.value >= 4, fontSize: 14,
                    color: s.color === '#cbd5e1' ? '#374151' : '#fff',
                    formatter: () => fmt(s.value, 1) + '%'},
                data: [s.value]
            }))
        });
    }

    // ③ 股东户数（只有银行表有 holder_num：逐披露期 [日期, 总数, A 股, H 股]）
    if (c.holder_num && c.holder_num.length > 1) {
        const rows = c.holder_num;
        const dates = rows.map(r => r[0]);
        const line = (name, idx, color, type) => ({
            name: name, type: 'line', symbol: 'circle', symbolSize: 5, connectNulls: false,
            lineStyle: {width: type ? 1.8 : 2.4, type: type || 'solid'}, itemStyle: {color: color},
            data: rows.map(r => (r[idx] === null || r[idx] === undefined) ? null : r[idx])
        });
        const s = [line('股东总数', 1, IND_COLOR[IND] || '#1f6feb'),
            line('A 股股东数', 2, '#0891b2', 'dashed'),
            line('H 股股东数', 3, '#b45309', 'dotted')].filter(x => x.data.some(v => v !== null));
        const ch = chartCard({
            id: 'holdernum', title: '股东户数（逐披露期）',
            sub: '线：定期报告披露的股东总数（户）· A/H 拆分只有少数期次披露，其余留空断线',
            note: nar('holdernum') +
                '户数下行通常意味着筹码集中（散户离场或被机构吸收），上行意味着分散。' +
                '上市首日附近的高点是打新账户尚未离场的峰值，' +
                '<b>本图保留这类非报告期快照</b>，因为那正是户数曲线最有信息量的一个点。',
            detail: narDetail('holdernum') +
                '<b>口径：</b>HOLDER_TOTAL_NUM 为该期定期报告披露的股东总数（A 股上市公司口径，' +
                'A+H 行含 H 股登记股东）；A/H 拆分字段多数期次为空，不插值。' +
                '目前只有银行板块的数据表带这一层，其余板块缺省。'
        }, '52vh');
        ch.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 0) + ' 户'},
            legend: {top: 0, itemGap: 16, textStyle: {fontSize: 15}},
            grid: {left: 96, right: 40, top: 56, bottom: 60},
            xAxis: {type: 'category', data: dates, axisTick: {alignWithLabel: true},
                axisLabel: {fontSize: 13, rotate: dates.length > 14 ? 45 : 0}},
            yAxis: Object.assign({}, AXIS, {name: '户', scale: true}),
            series: s
        });
    }

    // ④ 集中度序列（holder_concentration：逐期 top1/top3/top10，另有剔除代理人的口径）
    if (c.holder_concentration && c.holder_concentration.length > 1) {
        const rows = c.holder_concentration;
        const dates = rows.map(r => r.date);
        const line = (name, key, color, type) => ({
            name: name, type: 'line', symbol: 'circle', symbolSize: 5, connectNulls: false,
            lineStyle: {width: type ? 1.8 : 2.4, type: type || 'solid'}, itemStyle: {color: color},
            data: rows.map(r => (r[key] === null || r[key] === undefined) ? null : r[key])
        });
        const s = [line('前十名合计', 'top10', '#10243e'),
            line('前三名合计', 'top3', IND_COLOR[IND] || '#1f6feb'),
            line('第一大股东', 'top1', '#c0392b'),
            line('前三名（剔代理人）', 'top3_ex', '#0891b2', 'dashed'),
            line('第一大股东（剔代理人）', 'top1_ex', '#b45309', 'dashed'),
            /* 同股不同权的公司（百度 A 类 1 票 / B 类 10 票）才有这条：与实线的差额就是投票权楔子 */
            line('第一大股东投票权', 'top1_vote', '#7c3aed', 'dotted')]
            .filter(x => x.data.some(v => v !== null));
        const last = rows[rows.length - 1] || {};
        const hasEx = s.some(x => x.name.indexOf('剔代理人') >= 0);
        const hasVote = s.some(x => x.name === '第一大股东投票权');
        /* 说明文字跟着实际画出来的线走：剔代理人那两条与投票权那条都只有部分公司有，
         * 对着一张没有虚线的图讲「实线与虚线的差额」，是把银行页的话原样搬过来的错 */
        const notes = [];
        if (hasEx) {
            notes.push('实线与虚线的差额就是港股代理人（香港中央结算（代理人）有限公司）代持的那一块 —— ' +
                'A+H 公司的「第一大股东」在接口口径下常常是代理人，剔除后才看得到真实控股方。' +
                '本公司最新一期第一大股东为 <b>' + (last.top1_name || '—') +
                '</b>，剔代理人后为 <b>' + (last.top1_ex_name || '—') + '</b>。');
        } else {
            notes.push('本公司这一层<b>没有剔代理人的口径</b> —— 名册里没有港股代理人' +
                '（香港中央结算（代理人）有限公司）这一行。' +
                (last.top1_name ? '最新一期第一大股东为 <b>' + last.top1_name + '</b>。' : ''));
        }
        if (hasVote) {
            notes.push('<b>点线是第一大股东的投票权比例</b>：同股不同权的公司（百度 A 类 1 票 / B 类 10 票），' +
                '投票权与持股比例的差额就是超额表决权 —— 看控制权读点线，看经济利益读实线。');
        }
        const ch = chartCard({
            id: 'concseries', title: '持股集中度（逐披露期）',
            sub: '线：' + s.map(x => x.name).join('／') + '（%）· 分母为总股本' +
                (hasVote ? '，投票权那条的分母为总表决权' : ''),
            note: nar('concseries') + notes.join(' '),
            detail: '这一层<b>银行表自带</b>（<code>holder_concentration</code>），其余板块由手工层' +
                '（逐年年报「前十名股东」表原文）补齐后同样会出现 —— 页面结构一套，图随数据层增减。' +
                '剔代理人那两条只有名册里确有港股代理人时才画，投票权那条只有同股不同权的公司才有。'
        }, '52vh');
        ch.setOption({
            tooltip: {trigger: 'axis', valueFormatter: v => fmt(v, 2) + ' %'},
            legend: {top: 0, itemGap: 14, textStyle: {fontSize: 14}},
            grid: {left: 80, right: 40, top: 80, bottom: 60},
            xAxis: {type: 'category', data: dates, axisTick: {alignWithLabel: true},
                axisLabel: {fontSize: 13, rotate: dates.length > 14 ? 45 : 0}},
            yAxis: Object.assign({}, AXIS, {name: '%', scale: true}),
            series: s
        });
    }

    // ⑤ 历年总股本变动（手工层从年报「股份变动情况表」抄来的才有；银行在自己的年报口径页里已有此图）
    if (c.share_capital && c.share_capital.length > 1) {
        const rows = c.share_capital;
        /* 拆股／并股会让断点前后两段的股数完全不可比（百度 1 拆 80：3,500 万股 → 27 亿股），
         * 在断点年份上画一条界线；数据层给了 factor 时，把界线左侧各年折算到断点后的口径 ——
         * 不折算的话前 15 年在同一根 y 轴上全被压成看不见的贴地条，图等于只剩最近几年 */
        const brk = (c.share_capital_break &&
            rows.some(r => String(r[0]) === String(c.share_capital_break.at)))
            ? c.share_capital_break : null;
        const brkIdx = brk ? rows.findIndex(r => String(r[0]) === String(brk.at)) : -1;
        const scaled = i => !!(brk && brk.factor && brkIdx > 0 && i < brkIdx);
        const shares = i => rows[i][1] * (scaled(i) ? brk.factor : 1);
        /* 有变动原因的年份单独上色并把原因写进 tooltip —— 股本台阶（IPO／定增／回购注销）
         * 是这张图唯一的看点，平年一律同色，免得颜色多到看不出哪年动过 */
        const ch = chartCard({
            id: 'sharecap', title: '历年总股本变动',
            sub: '柱：各年末股份总数（亿股）· 有色柱 = 当年股本发生变动（IPO／定增／回购注销），灰柱 = 未变动' +
                (brk ? (brk.factor
                    ? ' · 竖虚线为口径断点，左侧各年按 1 拆 ' + brk.factor + ' 折算（描边浅柱）'
                    : ' · 竖虚线为口径断点') : ''),
            note: (brk ? mdBold(brk.text) + ' ' : '') + nar('sharecap') +
                '股本台阶是判断摊薄与融资节奏的第一层信息。' +
                '<b>本图不用接口的 total_share</b>：那是当前值被回填到每一年（历年完全相同），' +
                '台阶在那份数据里根本看不出来；这里逐年取自年报「股份变动情况表」。',
            detail: narDetail('sharecap') + (c.history_source ? mdBold(c.history_source) : '') +
                '<br>「变动原因」为年报原文摘要，未变动的年份原文写「未变动」，不做推测。'
        }, '46vh');
        ch.setOption({
            tooltip: {
                trigger: 'axis',
                formatter: p => {
                    const i = p[0].dataIndex, r = rows[i];
                    return r[0] + '<br><b>' + fmt(shares(i) / 1e8, 4) + ' 亿股</b>（' +
                        shares(i).toLocaleString('zh-CN') + ' 股）' +
                        (scaled(i) ? '<br><span style="color:#888">年报原文 ' +
                            r[1].toLocaleString('zh-CN') + ' 股 × ' + brk.factor +
                            '（拆细前口径）</span>' : '') +
                        (r[2] ? '<br><span style="color:#888">' + r[2] + '</span>' : '');
                }
            },
            grid: {left: 92, right: 40, top: 30, bottom: 50},
            xAxis: {type: 'category', data: rows.map(r => r[0]), axisTick: {alignWithLabel: true},
                axisLabel: {fontSize: 13, rotate: rows.length > 14 ? 45 : 0}},
            yAxis: Object.assign({}, AXIS, {name: '亿股', scale: true}),
            series: [{
                type: 'bar', barMaxWidth: 46,
                markLine: brk ? {
                    symbol: 'none', silent: true,
                    lineStyle: {color: '#8e8e8e', type: 'dashed', width: 1.5},
                    label: {formatter: brk.at + ' 起口径变更', position: 'insideEndTop',
                        fontSize: 13, color: '#8e8e8e'},
                    data: [{xAxis: String(brk.at)}]
                } : undefined,
                label: {show: rows.length <= 12, position: 'top', fontSize: 13,
                    formatter: p => fmt(p.value, 2)},
                itemStyle: {
                    color: p => scaled(p.dataIndex) ? '#e8eef7'
                        : ((rows[p.dataIndex][2] && rows[p.dataIndex][2] !== '未变动')
                            ? (IND_COLOR[IND] || '#1f6feb') : '#cbd5e1'),
                    // 折算过的柱子描个虚边：值是本页算的，不是年报原文写的那个数
                    borderColor: p => scaled(p.dataIndex) ? '#94a3b8' : 'transparent',
                    borderType: 'dashed', borderWidth: 1
                },
                data: rows.map((r, i) => +(shares(i) / 1e8).toFixed(4))
            }]
        });
    }

    // ⑥ 历年每 10 股分红（同上：手工层补齐后才画）
    if (c.dividend_per10 && c.dividend_per10.length > 1) {
        const rows = c.dividend_per10.filter(r => r[1] !== null && r[1] !== undefined);
        const ch = chartCard({
            id: 'divper10', title: '历年每 10 股分红',
            sub: '柱：各年度每 10 股派现（' + (c.dividend_unit || '元') +
                '，含税 · 按年度累计，中期＋末期合并）',
            note: nar('divper10') +
                '与股东结构一起看：股东高度集中的公司，分红更像是向控股方的现金回流；' +
                '分散持股的公司，分红率变化直接影响二级市场的持有成本。',
            detail: narDetail('divper10') + (c.history_source ? mdBold(c.history_source) : '') +
                '<br>只画年报／分红公告里明确写出的数，未分红的年份记 0（原文依据在数据层里），不插值。' +
                (c.dividend_unit === '港元' ? '<br><b>本公司的股息以港元宣派</b>，年报明确人民币金额要按' +
                    '股东周年大会前一周的汇率折算，所以这里照港元画，<b>不做汇率换算</b>。' : '')
        }, '40vh');
        ch.setOption({
            tooltip: {trigger: 'axis',
                valueFormatter: v => fmt(v, 4) + ' ' + (c.dividend_unit || '元') + ' / 10 股'},
            grid: {left: 80, right: 40, top: 30, bottom: 50},
            xAxis: {type: 'category', data: rows.map(r => r[0]), axisTick: {alignWithLabel: true},
                axisLabel: {fontSize: 13, rotate: rows.length > 14 ? 45 : 0}},
            yAxis: Object.assign({}, AXIS, {name: c.dividend_unit || '元'}),
            series: [{
                type: 'bar', barMaxWidth: 40, itemStyle: {color: '#c9a24a'},
                label: {show: rows.length <= 14, position: 'top', fontSize: 13,
                    formatter: p => fmt(p.value, 2)},
                data: rows.map(r => r[1])
            }]
        });
    }
}

function renderTable(d, agg) {
    const c = d.company, holders = c.holders;
    const hasPledge = holders.some(h => h.pledged !== null && h.pledged !== undefined);
    /* 「所属分组」列：后端把派系表的名字对到这张名册上（用年报简称的几家银行靠手工层
     * faction_aliases 接），对不上的成员后端已剔除，所以这里出现的分组都是核对过的。 */
    const facOf = {};
    (c.factions || []).forEach(f => (f.names || []).forEach(n => { facOf[n] = f.title; }));
    const hasFac = Object.keys(facOf).length > 0;
    document.getElementById('tbl-head').innerHTML =
        '<th class="num">序号</th><th>股东名称</th><th class="num">持股数（股）</th>' +
        '<th class="num">报告期内增减（股）</th><th class="num">占总股本</th>' +
        (hasPledge ? '<th class="num">质押/冻结（股）</th>' : '') +
        (hasFac ? '<th>所属分组</th>' : '') + '<th>类别</th>';
    document.getElementById('tbl-sub').innerHTML =
        '报告期末 ' + (c.holders_end_date || '—') + ' · 「报告期内增减」与「新进／不变」为接口原样字段' +
        '（增红／减绿／新进橙），缺失显示「—」，不做推算 · 占比分母为总股本 ' + shareFmt(agg.base) +
        (hasFac ? ' · 「所属分组」为一致行动人／同类归并，依据见环形图下方说明' : '');
    document.getElementById('tbl-body').innerHTML = holders.map(h =>
        '<tr><td class="num">' + h.rank + '</td>' +
        '<td class="nm">' + (h.name || '—') + '</td>' +
        '<td class="num">' + (h.hold_num === null || h.hold_num === undefined ? '—' : h.hold_num.toLocaleString('zh-CN')) + '</td>' +
        changeCell(h) +
        '<td class="num">' + fmt(h.ratio, 2) + '%</td>' +
        (hasPledge ? '<td class="num">' + (h.pledged ? h.pledged.toLocaleString('zh-CN') : '—') + '</td>' : '') +
        (hasFac ? '<td class="nat">' + (facOf[h.name] || '—') + '</td>' : '') +
        '<td class="nat">' + (h.shares_type || '—') + '</td></tr>').join('');
    document.getElementById('tbl-foot').innerHTML =
        '<tr class="row-total"><td class="num"></td><td class="nm">前十名合计</td>' +
        '<td class="num">' + agg.sum10.toLocaleString('zh-CN') + '</td>' +
        '<td class="num" style="color:#6b7280">见各行</td>' +
        '<td class="num">' + (agg.base ? fmt(agg.sum10 / agg.base * 100, 2) : '—') + '%</td>' +
        (hasPledge ? '<td class="num"></td>' : '') +
        (hasFac ? '<td class="nat"></td>' : '') + '<td class="nat"></td></tr>';
    document.getElementById('sec-table').hidden = false;
}

function renderGaps(d) {
    const c = d.company;
    const noHolders = d.roster.filter(r => !r.has_holders);
    /* 逐年抽取时记下的披露缺口排在最前：它们是这家公司特有的，比通用口径提醒更值得先读 */
    const gaps = (c.history_gaps || []).map(mdBold).concat([
        '<b>名册只有一期</b>：本页的股东名册是 ' + (c.holders_end_date || '—') + ' 那一期（' +
        (c.holders_caliber || '接口口径的前十名股东快照') + '），历史各期的<b>逐个股东</b>没有入库；' +
        '有历年数据的公司在上面画的是股本／户数／集中度三条序列，不是历年名册。',
        '<b>比例分母是总股本</b>，不是 A 股股本 —— A+H 公司名册上两类股份混排，' +
        '按 A 股基数重算会把 H 股股东的比例放大到荒谬值。',
        '<b>香港中央结算（代理人）有限公司不是真实股东</b>，是港股中央结算的名义持有人，穿透不了；' +
        '接口对部分港股股东也不给名称（「港股股东A／B」），原样保留。'
    ]);
    if (noHolders.length) {
        gaps.push('<b>本板块有 ' + noHolders.length + ' 家取不到股东数据</b>（' +
            noHolders.map(r => r.name).join('、') + '）：接口不返回纯 H 股公司的前十名股东，' +
            '导航里置灰，不是取数遗漏。');
    }
    if (!c.holder_num) {
        gaps.push('<b>本公司的数据层还没有股东户数与集中度序列</b>（银行表自带 ' +
            '<code>holder_num</code> / <code>holder_concentration</code>，其余板块要按' +
            '<b>年报口径逐年抄「股东情况」章节</b>才有），所以少这两张图。');
    }
    if (c.ring && c.ring.caliber) {
        /* 银行原先另有一页年报口径股东页，已并入本页：环形图这一圈就是那份数据
         * （一致行动人归并、含「其他流通股东」铺满 100%），下面的名册仍是接口快照口径 */
        gaps.push('本页<b>两套口径同页呈现</b>：环形图与右侧分组是<b>年报口径</b>' +
            '（一致行动人归并，含「其他流通股东」铺满 100%），下方「前十名股东明细」表是' +
            '<b>接口口径</b>的报告期末快照 —— 两处的名字与增减写法本就不同，不要相互对齐着读。');
    }
    document.getElementById('gaps').innerHTML = gaps.map(g => '<li>' + g + '</li>').join('');
    document.getElementById('sec-gaps').hidden = false;
}

/* ══════════ 双层环形图：内圈股东明细 / 外圈股东分组（可互换） ══════════
 * 与「哪家公司／哪个行业」无关，只吃一个标准数据块：
 *   { holderData: [{name, value, type, shares, chg}], factions: [{title, color, names, basis}] }
 * 容错：分组可以缺、可以只覆盖部分股东、点名的股东可以不在名册里、合计可以不到 100%。
 * 版面（行高、字号、列宽、左右留白、圆环半径、画布高度）全部由数据量 + 文字实测宽度算出，
 * 没有任何按公司手调的常量。原型见 bank/_preview_holders_merged.html。
 */
var RING_ORDER = 'detail-in';    /* detail-in = 明细在内 / 分组在外；fac-in = 反过来 */
/* -1 = 主口径（最新年报／接口快照），>=0 = ring_alt 里的第几个附加口径 */
var RING_ALT_I = -1;
var RING_LABEL = '占总股本';      /* 比例口径，跟本页其余部分一致（分母为总股本） */
var HATCH_CACHE = {};
/* 斜线纹理工厂：底色 + 斜线色，10×10 平铺；同一组合只画一次 */
function hatch(base, line) {
    var key = base + '|' + line;
    if (HATCH_CACHE[key]) return HATCH_CACHE[key];
    var c = document.createElement('canvas');
    c.width = 10; c.height = 10;
    var x = c.getContext('2d');
    x.fillStyle = base; x.fillRect(0, 0, 10, 10);
    x.strokeStyle = line; x.lineWidth = 1.5;
    x.beginPath(); x.moveTo(0, 10); x.lineTo(10, 0); x.stroke();
    x.beginPath(); x.moveTo(-2, 2); x.lineTo(2, -2); x.stroke();
    x.beginPath(); x.moveTo(8, 12); x.lineTo(12, 8); x.stroke();
    return (HATCH_CACHE[key] = {image: c, repeat: 'repeat'});
}
function hatchCss(base, line) {
    return 'repeating-linear-gradient(45deg,' + line + ' 0 1.5px,' + base + ' 1.5px 7.1px)';
}
/* 残余项（名册外股份）：灰底灰斜线 */
var RESIDUAL_PATTERN = hatch('#f0f0f0', '#999');
var RESIDUAL_SWATCH_CSS = hatchCss('#f0f0f0', '#999');
/* 名义持有人（香港中央结算／代理人）：蓝底 + 白斜线。这个蓝为名义持有人专用，
 * 不进 PIE_COLORS，数据里自带的同色系蓝也会被换掉，避免两者撞色。 */
var NOMINEE_COLOR = '#3d7ebf';
var NOMINEE_PATTERN = hatch(NOMINEE_COLOR, '#fff');
var NOMINEE_SWATCH_CSS = hatchCss(NOMINEE_COLOR, '#fff');
var RESERVED_NOMINEE = ['#3d7ebf', '#2980b9', '#3498db', '#2471a3'];
var PIE_COLORS = ['#6c3483', '#e67e22', '#16a085', '#c0392b', '#f1c40f',
    '#8e44ad', '#27ae60', '#d35400', '#2c3e50', '#c2185b', '#00838f'];
var RESIDUAL_RE = /其他|其它|未披露|未达披露|other/i;
/* 名义持有人：只是代人登记的通道，不算真分组，单独配色并垫在残余项之前 */
var NOMINEE_RE = /香港中央结算|香港中央結算|香港.{0,6}代理人|HKSCC|nominee/i;
var DROP_TAIL_RE = /(股份有限公司|有限责任公司|有限合伙|有限公司|公司)$/;
var DROP_LEAD_RE = /^(中国|中國)(?=.{2,})/;
var DROP_TRADE_RE = /(保险资产管理|资产管理|保险|保險|银行|銀行|证券|證券|基金|信托|信託)$/;
/* 色相（0-360），自动配色靠它挑一个离已用色最远的颜色 */
function hueOf(hex) {
    var n = parseInt(String(hex).replace('#', ''), 16);
    var r = ((n >> 16) & 255) / 255, g = ((n >> 8) & 255) / 255, b = (n & 255) / 255;
    var mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, h = 0;
    if (d) {
        if (mx === r) h = 60 * (((g - b) / d) % 6);
        else if (mx === g) h = 60 * ((b - r) / d + 2);
        else h = 60 * ((r - g) / d + 4);
    }
    return (h + 360) % 360;
}
/* 数据里自带的颜色若撞上名义持有人专用色，弃用、回落到调色板 */
function keepColor(color) {
    if (!color) return '';
    return RESERVED_NOMINEE.indexOf(String(color).toLowerCase()) >= 0 ? '' : color;
}
function facFill(g) {
    return g.residual ? RESIDUAL_PATTERN : (g.nominee ? NOMINEE_PATTERN : g.color);
}
/* 同色系变浅：t=0 原色，t 越大越接近白 */
function shade(hex, t) {
    var n = parseInt(String(hex).replace('#', ''), 16);
    var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    r = Math.round(r + (255 - r) * t);
    g = Math.round(g + (255 - g) * t);
    b = Math.round(b + (255 - b) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}
/* 分组色拿来当文字色：同一组的股东名称同色，一眼能归堆。直接用原色不行——
 * 社保基金的黄 #f1c40f 在白底上几乎读不出来，所以按感知亮度等比压暗到 0.42（保持色相）。 */
function facTextColor(g) {
    if (g.residual) return '#777';
    var hex = g.nominee ? NOMINEE_COLOR : g.color;
    var n = parseInt(String(hex).replace('#', ''), 16);
    var r = (n >> 16) & 255, gg = (n >> 8) & 255, b = n & 255;
    var lum = (0.299 * r + 0.587 * gg + 0.114 * b) / 255;
    if (!(lum > 0.42)) return hex;
    var k = 0.42 / lum;
    return 'rgb(' + Math.round(r * k) + ',' + Math.round(gg * k) + ',' + Math.round(b * k) + ')';
}
/* 自动简称：多段名（「托管人-产品」「集团-本级-自有资金」）取信息量最大的一段，
 * 再砍掉通用后缀、压缩基金全称。不够短的话由 fit() 按实测宽度再截。 */
function autoShort(name) {
    var s = String(name || '').replace(/（/g, '(').replace(/）/g, ')').trim();
    var segs = s.split(/[-—－]/).map(function (x) { return x.trim(); }).filter(Boolean);
    /* 只有每一段都够长时才认为这是「托管人-产品」那种多段名 —— 否则「20-F 未列示…」
     * 会被拆成「20」和「F 未列示…」，取最长段后开头那个字就没了 */
    if (segs.length > 1 && segs.every(function (x) { return x.length >= 3; })) {
        s = segs.reduce(function (a, b) { return b.length > a.length ? b : a; }, segs[0]);
    }
    s = s.replace(/交易型开放式指数(发起式)?证券投资基金/g, 'ETF')
        .replace(/(债券型)?证券投资基金/g, '基金')
        .replace(DROP_TAIL_RE, '');
    return s || String(name || '');
}
/* 简称撞车时补一个区分段：「中国平安人寿保险-自有资金」和「…-传统-普通保险产品」
 * autoShort 都取到公司名那一段，会出现两行同名，这里把各自剩下的尾段接回来。
 * 撞车的几行公司名一样，真正要看的是尾段，所以公司名这一半再压一次（去「中国」、去行业词）。 */
function tightShort(name) {
    var s = autoShort(name).replace(DROP_LEAD_RE, '');
    var cut = s.replace(DROP_TRADE_RE, '');
    return cut.length >= 2 ? cut : s;
}
function segsOf(name) {
    return String(name || '').replace(/（/g, '(').replace(/）/g, ')')
        .split(/[-—－]/).map(function (x) { return x.trim(); }).filter(Boolean);
}
function dedupeShorts(members) {
    var cnt = {};
    members.forEach(function (m) { cnt[m.short] = (cnt[m.short] || 0) + 1; });
    members.forEach(function (m, i) {
        if (cnt[m.short] < 2) return;
        var segs = segsOf(m.name), main = segs.reduce(function (a, b) {
            return b.length > a.length ? b : a;
        }, segs[0] || '');
        var rest = segs.filter(function (x) { return x !== main; });
        m.short = tightShort(main) + '·'
            + (rest.length ? autoShort(rest[rest.length - 1]) : String(i + 1));
    });
    return members;
}

/* 数据块 → 分组行：分组合计降序、残余垫最后、组内明细降序 */
function normalizeRing(block) {
    var holders = (block.holderData || []).map(function (h) {
        return {
            name: h.name, pct: +h.value || 0, type: h.type || '', shares: +h.shares || 0,
            short: autoShort(h.name), chgText: h.chgText || '',
            /* chg：数字 = 报告期内增减股数，0 = 披露为「不变」，null = 未披露，表里显示不同 */
            chg: (h.chg === null || h.chg === undefined ? null : +h.chg)
        };
    });
    var byName = {}, used = {}, groups = [], ci = 0, taken = {};
    holders.forEach(function (h) { byName[h.name] = h; });
    taken[NOMINEE_COLOR.toLowerCase()] = 1;
    (block.factions || []).forEach(function (f) {
        var c = keepColor(f.color);
        if (c) taken[String(c).toLowerCase()] = 1;
    });
    /* 取一个色相离已用色最远的未用色：去掉名义持有人专用色后按调色板顺序会连出两个紫 */
    function nextColor() {
        var hs = Object.keys(taken).map(hueOf), best = null, bestD = -1;
        PIE_COLORS.forEach(function (c) {
            if (taken[c.toLowerCase()]) return;
            var h = hueOf(c);
            var d = hs.length ? Math.min.apply(null, hs.map(function (x) {
                var v = Math.abs(x - h); return v > 180 ? 360 - v : v;
            })) : 999;
            if (d > bestD) { bestD = d; best = c; }
        });
        if (!best) best = PIE_COLORS[ci++ % PIE_COLORS.length];
        taken[best.toLowerCase()] = 1;
        return best;
    }
    function push(title, color, members, basis) {
        var val = +members.reduce(function (a, m) { return a + m.pct; }, 0).toFixed(2);
        var res = RESIDUAL_RE.test(title) ||
            (members.length === 1 && RESIDUAL_RE.test(members[0].name));
        /* 组名点明是代理人，或组里每一家都是代理人 → 名义持有人组（混编的组不算） */
        var nom = !res && (NOMINEE_RE.test(title) || (members.length > 0 &&
            members.every(function (x) { return NOMINEE_RE.test(x.name); })));
        groups.push({
            title: title, short: autoShort(title), members: members, value: val,
            residual: res, nominee: nom, basis: basis || (members.length > 1 ? '' : '单独一家'),
            color: res ? '#95a5a6' : (nom ? NOMINEE_COLOR : (keepColor(color) || nextColor()))
        });
    }
    (block.factions || []).forEach(function (f) {
        var ms = (f.names || []).map(function (n) { return byName[n]; }).filter(Boolean);
        if (!ms.length) return;                    /* 组里点名的股东不在名册 → 整组丢掉 */
        ms.forEach(function (m) { used[m.name] = 1; });
        ms.sort(function (a, b) { return b.pct - a.pct; });
        push(f.title, f.color, dedupeShorts(ms), f.basis);
    });
    holders.forEach(function (h) {                 /* 没被任何组认领的股东各自成组 */
        if (!used[h.name]) push(h.name, '', [h], '单独一家');
    });
    var named = groups.filter(function (g) { return !g.residual; });
    var res = groups.filter(function (g) { return g.residual; });
    var sum = groups.reduce(function (a, g) { return a + g.value; }, 0);
    var gap = +(100 - sum).toFixed(2);
    var resMembers = [], resVal = 0;
    var resTitle = res.length ? res[0].title : (block.residualLabel || '其他股东');
    res.forEach(function (g) { resMembers = resMembers.concat(g.members); resVal += g.value; });
    if (gap > 0.01) {                              /* 披露合计不足 100% → 自动补差额 */
        resMembers.push({
            name: block.residualLabel || '其他股东', short: '其他股东', pct: gap,
            type: '披露合计 ' + sum.toFixed(2) + '% 以外的部分', chg: null, shares: 0
        });
        resVal += gap;
    }
    named.sort(function (a, b) { return b.value - a.value; });
    var nomRows = named.filter(function (g) { return g.nominee; });
    if (nomRows.length) {                          /* 名义持有人排在所有实名分组之后 */
        named = named.filter(function (g) { return !g.nominee; }).concat(nomRows);
    }
    if (resVal > 0.01) {
        named.push({
            title: resTitle, short: autoShort(resTitle), members: resMembers,
            value: +resVal.toFixed(2), residual: true, color: '#95a5a6', basis: ''
        });
    }
    return named;
}
var FAC_ROWS = [], RING_BLOCK = null, RCHART = null;
/* 明细扇区颜色：残余用纹理，其余同组由深到浅 */
function detailColors() {
    var map = {};
    FAC_ROWS.forEach(function (g) {
        var step = g.members.length > 4 ? 0.15 : 0.22, nk = 0;
        g.members.forEach(function (h, k) {
            /* 名义持有人一律蓝底斜线：整组是代理人时按组、混编组里只给代理人那几家上纹理 */
            var nom = g.nominee || (!g.residual && NOMINEE_RE.test(h.name));
            if (g.residual) map[h.name] = RESIDUAL_PATTERN;
            else if (nom) map[h.name] = hatch(shade(NOMINEE_COLOR, Math.min(0.5, nk++ * step)), '#fff');
            else map[h.name] = shade(g.color, Math.min(0.72, k * step));
        });
    });
    return map;
}
/* 两圈数据：顺序一致，所以明细扇区在角度上正好落在所属分组扇区里 */
function buildSeriesData() {
    var cmap = detailColors();
    var detail = [], fac = [];
    FAC_ROWS.forEach(function (g) {
        g._fi = fac.length;      /* _fi：分组行悬浮时按 dataIndex 反查外圈扇区 */
        fac.push({
            name: g.title, value: g.value, itemStyle: {color: facFill(g)},
            _short: g.short, _members: g.members, _residual: g.residual, _nominee: g.nominee,
            _basis: g.basis
        });
        g.members.forEach(function (h) {
            /* _di：右侧标注悬浮时按 dataIndex 反查扇区；_swatch：纹理的 CSS 版，表格色块用它 */
            h._di = detail.length;
            h._swatch = g.residual ? RESIDUAL_SWATCH_CSS
                : (g.nominee ? hatchCss(shade(g.color, 0), '#fff') : cmap[h.name]);
            detail.push({
                name: h.name, value: h.pct, itemStyle: {color: cmap[h.name]},
                _short: h.short, _fac: g.title, _tag: h.type, _shares: h.shares, _swatch: h._swatch
            });
        });
    });
    return {detail: detail, fac: fac, cmap: cmap};
}

/* ==== 文字实测 + 版面度量 ==== */
var RING_LINE = '#bbb';
var HIT_BG = 'rgba(0,0,0,0)';
var ROW_HOVER_BG = 'rgba(108,52,131,.12)';
var RING_FONT = '-apple-system,"PingFang SC","Microsoft YaHei",sans-serif';
var MEAS = document.createElement('canvas').getContext('2d');
function measure(s, fs, bold) {
    MEAS.font = (bold ? 'bold ' : '') + fs + 'px ' + RING_FONT;
    return MEAS.measureText(String(s)).width;
}
/* 超预算就从尾巴截，只在末尾留一个「…」——不做中间省略；撞名那几行靠 tightShort 在上游压短 */
function fit(s, fs, bold, maxW) {
    s = String(s);
    if (measure(s, fs, bold) <= maxW) return s;
    while (s.length > 1 && measure(s + '…', fs, bold) > maxW) s = s.slice(0, -1);
    return s + '…';
}
function rowCount() {
    var n = 0;
    FAC_ROWS.filter(function (f) { return !f.residual; }).forEach(function (f) {
        n += f.members.length;
    });
    return Math.max(1, n);
}
/* 行高/字号随行数缩放，列宽取该列最长文字的实测宽度（超预算就截断），
 * 左侧留白由左挂标注的宽度决定 —— 换一家公司、换一个行业都不用改数。 */
function metrics(w, h) {
    var named = FAC_ROWS.filter(function (f) { return !f.residual; });
    var n = rowCount();
    var rowH = Math.max(24, Math.min(38, Math.floor((h - 96) / n)));
    var fsDet = Math.max(13, Math.min(20, rowH - 15));
    var fsFac = fsDet + 2;
    var facBudget = w * 0.13, detBudget = w * 0.19;
    var facW = 0, detW = 0, m = {fac: {}, det: {}};
    named.forEach(function (f) {
        m.fac[f.title] = fit(f.short, fsFac, true, facBudget);
        facW = Math.max(facW, measure(m.fac[f.title], fsFac, true));
        f.members.forEach(function (x) {
            m.det[x.name] = fit(x.short, fsDet, false, detBudget);
            detW = Math.max(detW, measure(m.det[x.name], fsDet, false));
        });
    });
    var vw = measure('88.88%', fsFac, true), vwd = measure('88.88%', fsDet, false);
    var right = 26 + 14 + facW + 16 + vw + 18 + 18 + 22 + detW + 14 + vwd + 10;
    /* 左侧留白：只有残余项挂在左边，按它那两行文字里最宽的一条留 */
    var leftW = 0;
    m.leftTxt = {};
    leftRows().forEach(function (f) {
        m.leftTxt[f.title] = fit(f.short, fsDet, false, w * 0.13);
        leftW = Math.max(leftW, measure(m.leftTxt[f.title], fsDet, false),
            measure(f.value.toFixed(2) + '%', fsDet, false));
    });
    m.rowH = rowH; m.fsDet = fsDet; m.fsFac = fsFac; m.facW = facW; m.detW = detW;
    m.vw = vw; m.vwd = vwd; m.left = leftW ? 18 + leftW + 18 : 20; m.right = right;
    m.named = named;
    return m;
}
function pt(cx, cy, r, deg) {
    var a = deg * Math.PI / 180;
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
}
/* 引线起点角：在这个扇区自己的角度区间里挑离标注行最近的角度，而不是死用中点角 ——
 * 占比很大的扇区中点常落在左半边，死用中点时引线得贴着圆环绕半圈才到右侧标注。
 * 两端各留一点内缩，免得起点正好压在两个扇区的分界上分不清归属。 */
function anchorDeg(geo, f, rowY) {
    var r1 = geo.rEdge + 14;
    var sn = Math.max(-1, Math.min(1, (geo.cy - rowY) / r1));
    var exit = Math.asin(sn) * 180 / Math.PI;      /* 标注行对应的出线角，必在右半边 */
    var lo = Math.min(f.a0, f.a1), hi = Math.max(f.a0, f.a1);
    var pad = Math.min(6, (hi - lo) / 4);
    lo += pad; hi -= pad;
    var e = exit;
    while (e < lo - 180) e += 360;
    while (e > hi + 180) e -= 360;
    return Math.max(lo, Math.min(hi, e));
}
/* 整段落在左半边的分组：引线得绕过圆环外侧。多条一起绕时按 lane 逐条外扩半径，
 * 不然几段弧叠在同一条环线上，跟到中途就分不清哪条是哪条。 */
function wrapRows() {
    return FAC_ROWS.filter(function (f) {
        if (f.residual) return false;
        var lo = Math.min(f.a0, f.a1), hi = Math.max(f.a0, f.a1);
        var pad = Math.min(6, (hi - lo) / 4);
        lo += pad; hi -= pad;
        var best = Math.cos(hi * Math.PI / 180);   /* 区间内 cos 的最大值 = 最靠右的那一点 */
        for (var d = lo; d < hi; d += 1) best = Math.max(best, Math.cos(d * Math.PI / 180));
        return best <= 0.08;
    });
}
/* 引线点：扇区落在右半边时拐一次直接接标注；整段落在左半边时先贴着外环画一段圆弧绕到右侧，
 * 否则直线会横穿整个环。绕行方向一律逆时针 —— 选「短的一边」会让上下两半的弧迎头对撞。 */
function leaderPoints(geo, deg, rowY, elbowX, endX, lane) {
    var cx = geo.cx, cy = geo.cy, r0 = geo.rEdge + 6;
    /* 外扩到画布边就不再让 lane 加半径，否则弧顶会被裁掉 */
    var room = Math.min(cy, geo.h - cy, cx) - 6;
    var r1 = Math.min(geo.rEdge + 14 + (lane > 0 ? lane * 7 : 0),
        Math.max(geo.rEdge + 10, room));
    var start = pt(cx, cy, r0, deg);
    if (Math.cos(deg * Math.PI / 180) > 0.08) return [start, [elbowX, rowY], [endX, rowY]];
    var s = Math.max(-1, Math.min(1, (cy - rowY) / r1));
    var exit = Math.asin(s) * 180 / Math.PI;          /* -90..90，必在右半边 */
    var a0 = deg, norm = ((deg % 360) + 360) % 360, dlt = exit - norm;
    while (dlt < 0) dlt += 360;
    while (dlt >= 360) dlt -= 360;
    var pts = [start];
    var n = Math.max(18, Math.ceil(Math.abs(dlt) / 6));   /* 约 6°/段，绕大半圈也看不出是折线 */
    for (var i = 0; i <= n; i++) pts.push(pt(cx, cy, r1, a0 + dlt * i / n));
    pts.push([endX, rowY]);
    return pts;
}
/* 左挂标注只留残余项：分组一律在右侧标注表里，出线角由 anchorDeg 就近挑 */
function leftRows() { return FAC_ROWS.filter(function (f) { return f.residual; }); }
/* 一条分组引线：走本组颜色的虚线，起点再点个同色小圆点，钉住它连的是哪块扇区。
 * 用色+虚线是因为绕环的弧彼此只隔几个像素，同灰实线跟到中途就分不清哪条是哪条。 */
function drawLeader(p, geo, f, rowY, elbowX, endX) {
    if (f.residual) return;
    var deg = anchorDeg(geo, f, rowY);
    p.poly(leaderPoints(geo, deg, rowY, elbowX, endX, wrapRows().indexOf(f)), f.color, [6, 4]);
    var s = pt(geo.cx, geo.cy, geo.rEdge + 6, deg);
    p.dot(s[0], s[1], f.color);
}
/* 画笔：graphic 元素都是 silent，交互只走另盖的透明命中区 */
function pen(g, m) {
    return {
        text: function (x, y, str, opt) {
            g.push({type: 'text', x: x, y: y, silent: true, style: Object.assign({
                text: str, fill: '#333', fontSize: m.fsDet, fontFamily: RING_FONT,
                align: 'left', verticalAlign: 'middle'
            }, opt || {})});
        },
        poly: function (points, color, dash) {
            g.push({type: 'polyline', silent: true, shape: {points: points},
                style: {stroke: color || RING_LINE, fill: 'none',
                    lineWidth: color ? 1.5 : 1, lineDash: dash || null}});
        },
        dot: function (x, y, color) {
            g.push({type: 'circle', silent: true, shape: {cx: x, cy: y, r: 2.5},
                style: {fill: color || RING_LINE}});
        },
        line: function (x1, y1, x2, y2) {
            g.push({type: 'line', silent: true, shape: {x1: x1, y1: y1, x2: x2, y2: y2},
                style: {stroke: RING_LINE, lineWidth: 1}});
        },
        rect: function (x, y, w, h, fill) {
            g.push({type: 'rect', silent: true, shape: {x: x, y: y, width: w, height: h, r: 3},
                style: {fill: fill}});
        },
        /* 透明命中区：标注本身是 silent，需要交互的行/入口另盖一块看不见的矩形。
         * hot = 这一行正被点亮（鼠标在环上或在这一行上），底色从透明换成淡紫。 */
        hit: function (x, y, w, h, on, hot) {
            g.push(Object.assign({
                type: 'rect', shape: {x: x, y: y, width: w, height: h, r: 4},
                style: {fill: hot ? ROW_HOVER_BG : HIT_BG}, z: 30
            }, on || {}));
        },
        dash: function (x1, y1, x2, y2, color) {
            g.push({type: 'line', silent: true, shape: {x1: x1, y1: y1, x2: x2, y2: y2},
                style: {stroke: color, lineWidth: 1, lineDash: [3, 2]}});
        }
    };
}
function fmtNum(n) { return Math.round(n).toLocaleString('en-US'); }
/* ==== 悬浮联动：环上的扇区 ←→ 右侧标注的那一行 ====
 * HOT = 当前点亮的数据 {si, di}；si 0 = 外圈那份（股东分组），1 = 股东明细。
 * 环上悬浮和标注行悬浮都只往 HOT 里写，标注的底色/字色全由 HOT 推出来。 */
var HOT = null, LAST = null, PIN = '';
function hotFac() {
    if (!HOT) return -1;
    if (HOT.si === 0) return HOT.di;
    var hit = -1;
    FAC_ROWS.forEach(function (f) {
        f.members.forEach(function (x) { if (x._di === HOT.di) hit = f._fi; });
    });
    return hit;
}
function hotDets() {
    var out = {};
    if (!HOT) return out;
    if (HOT.si === 1) { out[HOT.di] = 1; return out; }
    FAC_ROWS.forEach(function (f) {
        if (f._fi !== HOT.di) return;
        f.members.forEach(function (x) { out[x._di] = 1; });
    });
    return out;
}
/* 只重画 graphic 这一层：不动饼图、不重算版面，免得悬浮时圆环和列宽跟着跳 */
function paintAnno() {
    if (!LAST) return;
    RCHART.setOption({graphic: buildCols(LAST.geo, LAST.cmap, LAST.m)});
}
function setHot(si, di) {
    if (HOT && HOT.si === si && HOT.di === di) return;
    HOT = {si: si, di: di};
    paintAnno();
}
function clearHot() {
    if (!HOT) return;
    HOT = null;
    paintAnno();
}
/* 点击标注行 → 在那一行下方弹一个框，里面是全称 + 占比（列里的名字是截断的）。
 * 用点击而不是悬浮：鼠标扫过一列时框会跟着一行行闪。弹框是 DOM 元素而不是画布图元，
 * 所以不受画布裁剪限制，位置按行算再夹进画布范围。 */
function showFull(spec) {
    if (!spec) return;
    var el = document.getElementById('row-full');
    var r = RCHART.getDom().getBoundingClientRect();
    /* 用 createElement 而不是 innerHTML —— 股东名是数据里来的，不拼 HTML */
    el.textContent = '';
    var a = document.createElement('span');
    a.textContent = spec.text;
    a.style.color = '#333';
    el.appendChild(a);
    if (spec.val) {
        var b = document.createElement('span');
        b.textContent = '\u3000' + spec.val;
        b.style.color = '#6c3483';
        b.style.fontWeight = 'bold';
        b.style.whiteSpace = 'nowrap';
        el.appendChild(b);
    }
    /* 先显示出来才量得到框的大小，再把位置夹进画布范围：默认贴这一行下面，
     * 下面放不下就翻到行上面；左边界顶到画布右侧就往左挪。 */
    el.style.display = 'block';
    el.style.left = '0px';
    el.style.top = '0px';
    var bw = el.offsetWidth, bh = el.offsetHeight;
    var x = Math.max(8, Math.min(spec.x, RCHART.getWidth() - bw - 8));
    var y = spec.y + spec.h / 2 + 6;
    if (y + bh > RCHART.getHeight() - 4) y = spec.y - spec.h / 2 - bh - 6;
    el.style.left = (r.left + window.scrollX + x) + 'px';
    el.style.top = (r.top + window.scrollY + Math.max(4, y)) + 'px';
}
function hideFull() {
    PIN = '';
    document.getElementById('row-full').style.display = 'none';
}
function toggleFull(key, spec) {
    if (PIN === key) { hideFull(); return; }
    PIN = key;
    showFull(spec);
}
/* 悬浮某一行 → 点亮对应扇区；点一下才在原地补出全称（列里的名字是截断的）。
 * highlight/downplay 是为了跟直接悬浮环上扇区完全一致 —— 不发的话扇区不会放大加阴影。
 * box：这一行的命中框。paintAnno 会重建 graphic，zrender 可能借机补一个 mouseout，
 * 而鼠标其实还在框里 —— 落在框内的 mouseout 一律忽略，否则高亮会自己闪。 */
function rowHover(di, si, box, full) {
    var idx = si === null || si === undefined ? 1 : si;
    return {
        cursor: 'pointer',
        onclick: function () { toggleFull(idx + ':' + di, full); },
        onmouseover: function () {
            setHot(idx, di);
            RCHART.dispatchAction({type: 'downplay'});
            RCHART.dispatchAction({type: 'highlight', seriesIndex: idx, dataIndex: di});
        },
        onmouseout: function (e) {
            if (box && e.offsetX >= box[0] && e.offsetX <= box[0] + box[2]
                && e.offsetY >= box[1] && e.offsetY <= box[1] + box[3]) return;
            clearHot();
            if (PIN === idx + ':' + di) hideFull();
            RCHART.dispatchAction({type: 'downplay', seriesIndex: idx, dataIndex: di});
        }
    };
}
/* 左挂标注（残余项）：色块 + 名称 / 占比两行，引线从扇区边缘就近折两下过来。
 * 按扇区中点高度排序后逐个下推避免叠压，排到画布外时整体上移。 */
function drawLeftSide(g, geo, m) {
    var rows = leftRows();
    if (!rows.length) return;
    var p = pen(g, m), gap = Math.max(m.rowH, m.fsDet * 2 + 12), top = gap / 2 + 6;
    var items = rows.map(function (f) {
        return {f: f, s: pt(geo.cx, geo.cy, geo.rEdge + 6, f.mid)};
    }).sort(function (u, v) { return u.s[1] - v.s[1]; });
    var y = top;
    items.forEach(function (it) { it.y = Math.max(y, it.s[1]); y = it.y + gap; });
    var over = items[items.length - 1].y + gap / 2 - geo.h;
    if (over > 0) {
        var shift = Math.min(over, items[0].y - top);
        items.forEach(function (it) { it.y -= shift; });
    }
    items.forEach(function (it) {
        var f = it.f, ry = it.y;
        /* 残余项没有分组色，线保持灰，但虚线笔段与右侧引线一致 */
        p.poly([it.s, [it.s[0] - 20, ry], [m.left - 14, ry]], f.residual ? null : f.color, [6, 4]);
        if (!f.residual) p.dot(it.s[0], it.s[1], f.color);
        p.rect(6, ry - 22, 18, 18, facFill(f));
        p.text(30, ry - m.fsDet * 0.6, m.leftTxt[f.title], {fill: '#555'});
        p.text(30, ry + m.fsDet * 0.75, f.value.toFixed(2) + '%', {fill: '#555'});
    });
}
/* 两列标注：左边一列分组、右边一列明细，中间用括号连起来 */
function buildCols(geo, cmap, m) {
    var g = [], p = pen(g, m), rowH = m.rowH;
    var x0 = geo.w - m.right + 26, nameX = x0 + 14;
    var facValRight = nameX + m.facW + 16 + m.vw;
    var brX = facValRight + 18, swX = brX + 18, detX = swX + 22;
    var valRight = detX + m.detW + 14 + m.vwd;
    var top = geo.cy - (rowCount() - 1) * rowH / 2, y = top;
    var fsHead = Math.max(12, m.fsDet - 4);
    var hf = hotFac(), hd = hotDets();
    p.text(x0, top - rowH - 4, '股东分组', {fontSize: fsHead, fill: '#888'});
    /* 「股东明细」四个字是入口：点一下出全量明细表 */
    var headY = top - rowH - 4, headW = measure('股东明细', fsHead, true);
    p.text(swX, headY, '股东明细', {fontSize: fsHead, fontWeight: 'bold', fill: '#6c3483'});
    p.dash(swX, headY + fsHead * 0.85, swX + headW, headY + fsHead * 0.85, '#6c3483');
    p.hit(swX - 6, headY - 13, headW + 12, 26, {cursor: 'pointer', onclick: openDetail});
    m.named.forEach(function (f) {
        var first = y, last = y + (f.members.length - 1) * rowH, mid = (first + last) / 2;
        var fhot = f._fi === hf;
        drawLeader(p, geo, f, mid, x0 - 30, x0 - 8);
        p.rect(x0, mid - 10, 6, 20, facFill(f));
        p.text(nameX, mid, m.fac[f.title],
            {fontSize: m.fsFac, fontWeight: 'bold', fill: '#4a2a5a'});
        p.text(facValRight, mid, f.value.toFixed(2) + '%',
            {fontSize: m.fsFac, fontWeight: 'bold', fill: '#6c3483', align: 'right'});
        var fbox = [x0 - 8, first - rowH / 2, facValRight + 16 - x0, last - first + rowH];
        p.hit(fbox[0], fbox[1], fbox[2], fbox[3],
            rowHover(f._fi, 0, fbox, {x: nameX, y: mid, h: rowH,
                text: f.title + (f.basis ? '（归类依据：' + f.basis + '）' : ''),
                val: f.value.toFixed(2) + '%'}), fhot);
        if (f.members.length > 1) p.line(brX, first, brX, last);
        else p.line(facValRight + 8, mid, brX, mid);
        f.members.forEach(function (x) {
            var hot = !!hd[x._di];
            p.line(brX, y, brX + 14, y);
            p.rect(swX, y - 8, 16, 16, cmap[x.name]);
            p.text(detX, y, m.det[x.name], {fill: hot ? '#111' : '#444'});
            p.text(valRight, y, x.pct.toFixed(2) + '%', {fill: hot ? '#111' : '#444', align: 'right'});
            var box = [swX - 6, y - rowH / 2, valRight - swX + 12, rowH];
            p.hit(box[0], box[1], box[2], box[3],
                rowHover(x._di, 1, box, {x: detX, y: y, h: rowH, text: x.name,
                    val: x.pct.toFixed(2) + '%'}), hot);
            y += rowH;
        });
    });
    drawLeftSide(g, geo, m);
    return g;
}
function ringRender() {
    hideFull();                  /* 换排布/改窗口宽度后行位置全变了，钉住的全称先收掉 */
    FAC_ROWS = normalizeRing(RING_BLOCK);
    var dom = RCHART.getDom();
    /* 画布高度自适应：先按标注行数算一个够放行的高度，再看圆能不能吃满剩下的横向空间 */
    var rowsH = Math.max(460, rowCount() * 38 + 130);
    var m0 = metrics(RCHART.getWidth(), rowsH);
    var wantH = Math.min(980, Math.max(rowsH, RCHART.getWidth() - m0.left - m0.right + 48));
    if (Math.abs(dom.clientHeight - wantH) > 2) { dom.style.height = wantH + 'px'; RCHART.resize(); }
    var d = buildSeriesData(), w = RCHART.getWidth(), h = RCHART.getHeight();
    /* a0/a1：扇区起止角（12 点起顺时针递减，1% = 3.6°）；mid 是中点角。角度要在量尺寸之前算好 ——
     * 左侧留白取决于有几个分组得挂到左边，而那是看扇区落在哪半边定的。 */
    var a = 90;
    FAC_ROWS.forEach(function (f) {
        var s = f.value * 3.6;
        f.a0 = a; f.a1 = a - s; f.mid = a - s / 2; a -= s;
    });
    var m = metrics(w, h);
    var boxW = w - m.left - m.right;
    var cx = m.left + boxW / 2, cy = h / 2;
    var R = Math.max(70, Math.min(boxW / 2, h / 2 - 24));
    /* 外圈留窄环带、内圈厚一些；切换圈序时圆心与半径都不动 */
    var outBand = [R * 0.80, R * 0.98], inBand = [R * 0.44, R * 0.76];
    var facR = RING_ORDER === 'detail-in' ? outBand : inBand;
    var detR = RING_ORDER === 'detail-in' ? inBand : outBand;
    function pie(radius, data, sc) {
        return {type: 'pie', radius: radius, center: [cx, cy], startAngle: 90, sort: null,
            label: {show: false}, labelLine: {show: false},
            itemStyle: {borderColor: '#fff', borderWidth: 2}, data: data,
            /* 悬浮反馈：默认只推出 10px 加点阴影，0.2% 的细扇区几乎看不出变化。这里把扇区多推出去、
             * 阴影加重、白边加粗，同时让同圈其余扇区淡到 30% ——「亮一块」不如「暗一片」显眼。
             * blur 不设 global：另一圈保持原样，父子关系（明细落在哪个分组里）还看得见。 */
            emphasis: {focus: 'self', scaleSize: sc,
                itemStyle: {borderWidth: 3, shadowBlur: 24, shadowColor: 'rgba(40,20,50,.5)'}},
            blur: {itemStyle: {opacity: 0.3}},
            z: 2, animation: false};
    }
    function scaleOut(band) {
        /* 外圈推 12：引线弧的第一条车道在 rEdge + 14，推到 14 就会被扇区盖住 */
        return band === outBand ? 12 : Math.max(4, Math.floor(outBand[0] - inBand[1]) - 2);
    }
    var geo = {cx: cx, cy: cy, R: R, rEdge: outBand[1], w: w, h: h};
    RCHART.setOption({
        backgroundColor: '#fff',
        /* 浮层整个关掉（triggerOn: 'none'，也没有任何地方再发 showTip）：
         * 悬浮环上扇区 → 点亮右侧对应的明细行、分组行；悬浮标注行 → 在原地补出全称。
         * 配置留着不删，是因为格式化函数里记着比例口径，将来要恢复浮层直接改 triggerOn。 */
        tooltip: {
            trigger: 'item', triggerOn: 'none', textStyle: {fontSize: 16},
            extraCssText: 'white-space:nowrap;line-height:1.6',
            formatter: function (q) {
                var it = q.data;
                if (it._members) {
                    var sub = it._members.length > 1 ? '<br>' + it._members.map(function (x) {
                        return x.name + ' ' + x.pct.toFixed(2) + '%';
                    }).join('<br>') : '';
                    return '<b>股东分组</b> ' + q.name + '：' + q.value + '%（' + RING_LABEL + '）'
                        + '　<span style="color:#888">' + it._members.length + ' 家</span>' + sub;
                }
                return q.name + '：' + (+q.value).toFixed(2) + '%（' + RING_LABEL + '）'
                    + (it._shares ? '<br><span style="color:#888">持股 '
                        + shareFmt(it._shares) + '</span>' : '')
                    + '<br><span style="color:#888">所属分组：' + it._fac
                    + (it._tag ? '　' + it._tag : '') + '</span>';
            }
        },
        /* 推出量：外圈往外是空地，可以推狠一点；内圈往外只有两圈之间那道缝 */
        series: [pie(facR, d.fac, scaleOut(facR)), pie(detR, d.detail, scaleOut(detR))],
        graphic: buildCols(geo, d.cmap, m)
    }, true);
    LAST = {geo: geo, cmap: d.cmap, m: m};
}
/* ==== 股东明细表格：图上按分组归堆、名字截断，这里给一份全量长名清单 ==== */
/* 报告期内增减：红涨绿跌、0 写「不变」、没披露写「—」，与本页表格同一套配色 */
function chgCell(v) {
    if (v === null || v === undefined) return '<td class="num" style="color:#bbb">—</td>';
    if (!v) return '<td class="num" style="color:#888">不变</td>';
    return '<td class="num" style="color:' + (v > 0 ? '#c0392b' : '#1e8449') + '">'
        + (v > 0 ? '+' : '-') + fmtNum(Math.abs(v)) + '</td>';
}
/* 年报口径的增减是文字（「+79.14 万股」「不变」「新进」），只上色不解析 */
function chgCellOf(h) {
    if (h.chg !== null && h.chg !== undefined) return chgCell(h.chg);
    if (!h.chgText) return '<td class="num" style="color:#bbb">—</td>';
    var t = h.chgText, c = '#888';
    if (/^\+|增/.test(t)) c = '#c0392b';
    else if (/^[-−]|减/.test(t)) c = '#1e8449';
    else if (/新进/.test(t)) c = '#b45309';
    return '<td class="num" style="color:' + c + '">' + t + '</td>';
}
/* 哪几列出现由数据块里有没有值决定 —— 换行业/换公司都不用改代码 */
function detailTableHTML() {
    var hasType = false, hasNum = false, hasChg = false, textChg = false;
    FAC_ROWS.forEach(function (g) {
        g.members.forEach(function (h) {
            if (h.type) hasType = true;
            if (h.shares) hasNum = true;
            if (h.chg !== null && h.chg !== undefined) hasChg = true;
            if (h.chgText) { hasChg = true; textChg = true; }
        });
    });
    var rows = [], n = 0, tot = 0, totNum = 0, lack = 0, totChg = 0;
    FAC_ROWS.forEach(function (g) {
        var txt = facTextColor(g);
        g.members.forEach(function (h) {
            n++; tot += h.pct;
            if (h.shares) totNum += h.shares; else lack++;
            if (h.chg) totChg += h.chg;
            /* 色块并进名称格（本页那张表没有单独的色块列）；名称与分组两列都用分组色 */
            rows.push('<tr><td class="idx">' + n + '</td>'
                + '<td class="tl" style="color:' + txt + '"><span class="sw" style="background:'
                + (h._swatch || '#ccc') + '"></span>' + h.name + '</td>'
                + '<td class="tl fac" style="color:' + txt + '">' + g.title + '</td>'
                + (hasNum ? '<td class="num">' + (h.shares ? fmtNum(h.shares) : '—') + '</td>' : '')
                + (hasChg ? chgCellOf(h) : '')
                + '<td class="num">' + h.pct.toFixed(2) + '%</td>'
                // 类别放最后一列：它是定性标签，摆在数字列中间会把「持股数—增减—占比」这串数字截断
                + (hasType ? '<td class="nat">' + (h.type || '—') + '</td>' : '')
                + '</tr>');
        });
    });
    return '<table><thead><tr><th></th><th class="tl">股东名称</th><th class="tl fac">所属分组</th>'
        + (hasNum ? '<th class="num">持股数（股）</th>' : '')
        + (hasChg ? '<th class="num">报告期内增减' + (textChg ? '' : '（股）') + '</th>' : '')
        + '<th class="num">' + RING_LABEL + '</th>'
        + (hasType ? '<th class="nat">类别</th>' : '')
        + '</tr></thead><tbody>' + rows.join('')
        + '</tbody><tfoot><tr><td colspan="3">合计</td>'
        + (hasNum ? '<td class="num">' + fmtNum(totNum)
            + (lack ? '<span class="tag">未披露 ' + lack + ' 项</span>' : '') + '</td>' : '')
        /* 年报口径那份增减是文字，加不起来，合计格里写「见各行」 */
        + (hasChg ? (textChg ? '<td class="num" style="color:#888">见各行</td>' : chgCell(totChg)) : '')
        + '<td class="num">' + tot.toFixed(2) + '%</td>'
        + (hasType ? '<td class="nat"></td>' : '')
        + '</tr></tfoot></table>';
}
function openDetail() {
    document.getElementById('det-body').innerHTML = detailTableHTML();
    document.getElementById('det-modal').classList.add('on');
}
function closeDetail() { document.getElementById('det-modal').classList.remove('on'); }
/* 名册 → 环形图要的标准数据块。优先用后端下发的 ring（年报口径，bank/shareholder.html
 * 那套标准模板画的就是这一份：holderData 已含「其他流通股东」、factions 引用同一套名字）；
 * 没有 ring 的板块退回接口快照 + 手工分组，前十名之外那一块由 normalizeRing 自动补差额。 */
function ringBlock(c) {
    /* 切到附加口径（H 股年报那两张）时用那一块的数据与残余项叫法 */
    var alt = (c.ring_alt || [])[RING_ALT_I];
    if (alt) {
        RING_LABEL = alt.caliber || '占总股本';
        return {
            residualLabel: alt.residual_label || c.residual_label || '其他股东',
            factions: alt.factions || [],
            holderData: alt.holderData.map(function (h) {
                return {name: h.name, value: h.value, type: h.type || '', shares: 0,
                    chg: null, chgText: h.chgText || ''};
            })
        };
    }
    if (c.ring && c.ring.holderData && c.ring.holderData.length) {
        RING_LABEL = c.ring.caliber || '占总股本';
        return {
            residualLabel: c.residual_label || '其他股东',
            factions: c.ring.factions || [],
            holderData: c.ring.holderData.map(function (h) {
                return {
                    name: h.name, value: h.value, type: h.type || '', shares: 0, chg: null,
                    /* 年报口径这份增减是文字（「+79.14 万股」「不变」），不是股数 */
                    chgText: h.chgText || ''
                };
            })
        };
    }
    RING_LABEL = '占总股本';
    return {
        residualLabel: c.residual_label || '其他股东',
        factions: c.factions || [],
        holderData: (c.holders || []).map(function (h) {
            var n = Number(h.change);
            return {
                name: h.name, value: h.ratio, shares: h.hold_num, chgText: '',
                /* 「新进」接口只给状态不给股数，接到类别里，免得当成未披露 */
                type: (h.shares_type || '') + (h.state === '新进' ? ' · 新进' : ''),
                chg: h.change === '不变' ? 0 : (isNaN(n) || h.change === null
                    || h.change === undefined || h.change === '' ? null : n)
            };
        })
    };
}
/* 环形图上方那行说明：口径切换后要跟着换（附加口径的分母、年份都与主口径不同） */
function ringSub(d) {
    var c = d.company, alt = (c.ring_alt || [])[RING_ALT_I];
    document.getElementById('ring-sub').innerHTML =
        '内圈每一块是一名股东，外圈把他们归成分组（点右上角按钮两圈互换）· 比例为' + RING_LABEL +
        '，合计不足 100% 的部分自动补成「' + RING_BLOCK.residualLabel + '」· ' +
        '点右侧任一行看全称，点「股东明细」出全量表格<br>' +
        (alt ? '当前口径：<b>' + alt.label + '</b>（与主口径不是同一年、也不一定是同一个分母，' +
            '见图下说明）'
            : (c.ring ? '数据为<b>' + (c.ring_label || '年报口径') +
                '</b>（一致行动人归并、含「其他流通股东」铺满 100%，' +
                '就是原先银行那一页年报口径股东页画的那份）'
                : '数据为<b>' + (c.holders_caliber || '接口口径的前十名股东快照') + '</b>（报告期末 ' +
                (c.holders_end_date || '—') + '）'));
}

function buildRing(d) {
    var c = d.company;
    if (!c.holders || !c.holders.length) return;
    RING_BLOCK = ringBlock(c);
    document.getElementById('sec-ring').hidden = false;
    ringSub(d);
    RCHART = echarts.init(document.getElementById('chart-ring'));
    /* 环上悬浮：不弹浮层，只把对应的明细行 / 分组行点亮；
     * 移出图外时 zrender 只给 globalout，series 的 mouseout 不一定到，两个都接。 */
    RCHART.on('mouseover', function (q) {
        if (q.componentType !== 'series') return;
        setHot(q.seriesIndex, q.dataIndex);
    });
    RCHART.on('mouseout', function (q) {
        if (q.componentType === 'series') clearHot();
    });
    RCHART.getZr().on('globalout', clearHot);
    RCHART.getZr().on('click', function (e) { if (!e.target) hideFull(); });
    document.addEventListener('click', function (e) {
        if (!RCHART.getDom().contains(e.target)) hideFull();
    });
    var btn = document.getElementById('btn-order');
    btn.textContent = '内圈：股东明细';
    btn.onclick = function () {
        RING_ORDER = RING_ORDER === 'detail-in' ? 'fac-in' : 'detail-in';
        btn.textContent = RING_ORDER === 'detail-in' ? '内圈：股东明细' : '内圈：股东分组';
        ringRender();
    };
    /* 口径切换按钮：只有数据层给了附加口径的公司才出现（渝农商行的两张 H 股年报环形图）。
     * 切口径要连带换掉上方说明与图下的口径注 —— 分母与年份都不一样，说明不换就成了串口径。 */
    if (c.ring_alt && c.ring_alt.length) {
        var hd = document.querySelector('#sec-ring .ring-hd');
        var labels = [c.ring_label || '最新年报 · 占总股本'].concat(
            c.ring_alt.map(function (a) { return a.label; }));
        var btns = labels.map(function (label, k) {
            var b = document.createElement('button');
            b.type = 'button';
            b.textContent = label;
            b.title = '切换环形图口径';
            b.onclick = function () {
                RING_ALT_I = k - 1;
                RING_BLOCK = ringBlock(c);
                btns.forEach(function (x, j) { x.style.opacity = (j === k) ? '1' : '.55'; });
                ringRender();
                ringSub(d);
                renderRingNote(d);
            };
            hd.appendChild(b);
            return b;
        });
        btns.forEach(function (x, j) { x.style.opacity = j === 0 ? '1' : '.55'; });
    }
    document.getElementById('det-close').onclick = closeDetail;
    document.getElementById('det-modal').onclick = function (e) {
        if (e.target.id === 'det-modal') closeDetail();
    };
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { closeDetail(); hideFull(); }
    });
    window.addEventListener('resize', function () { RCHART.resize(); ringRender(); });
    ringRender();
    renderRingNote(d);
}
/* 图下说明：先说清「分组是谁归的」，再逐组列出归类依据 —— 年报披露的一致行动人/关联方
 * 与本项目按股东性质做的同类归并是两件事，混着读会把后者当成前者。 */
function renderRingNote(d) {
    var c = d.company, rows = FAC_ROWS.filter(function (g) { return !g.residual; });
    var alt = (c.ring_alt || [])[RING_ALT_I];
    var byBasis = {};
    rows.forEach(function (g) {
        var k = g.basis || '未标注依据';
        (byBasis[k] = byBasis[k] || []).push(g.title + ' ' + g.value.toFixed(2) + '%');
    });
    var lines = Object.keys(byBasis).map(function (k) {
        return '<b>' + k + '</b>：' + byBasis[k].join('、');
    });
    document.getElementById('ring-note').innerHTML =
        (alt && alt.note ? mdBold(alt.note) + '<br>' : '') +
        '外圈一共 ' + rows.length + ' 组' +
        (leftRows().length ? '（名册外的那一块挂在图左边）' : '') + '。' +
        '<b>「同类归并」不是年报披露的一致行动人</b>，只是本项目按股东性质归的堆；' +
        '「年报披露」「20-F 披露」那几组才是原文认定的关联方／一致行动人／控股股东。' +
        (c.caliber_note ? '<br>' + mdBold(c.caliber_note) : '') +
        '<details class="note-more"><summary>展开各组归类依据与来源</summary><div>' +
        lines.join('<br>') +
        (c.factions_source ? '<br><b>分组来源：</b>' + mdBold(c.factions_source) : '') +
        '</div></details>';
}

axios.get('/api/holders?industry=' + IND + (CODE ? '&code=' + CODE : '')).then(function (res) {

    if (!res.data || res.data.code !== 200) throw new Error((res.data && res.data.msg) || 'load failed');
    const d = res.data.data;
    document.getElementById('loading').style.display = 'none';
    buildNav(d);
    if (!d.company.holders.length) {
        const box = document.getElementById('error-msg');
        box.style.display = 'block';
        box.textContent = d.company.name + '（' + d.company.code + '）接口不返回前十名股东数据（纯 H 股公司），请在导航里换一家。';
        renderGaps(d);
        return;
    }
    const agg = renderHead(d);
    buildRing(d);
    buildCharts(d, agg);
    renderTable(d, agg);
    renderGaps(d);
}).catch(function (e) {
    console.error('fetch error', e);
    document.getElementById('loading').style.display = 'none';
    const box = document.getElementById('error-msg');
    box.style.display = 'block';
    box.textContent = '数据加载失败：' + e.message + '（请确认 backend_python.py 已启动）';
});
