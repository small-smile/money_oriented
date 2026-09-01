/* 中国移动「简介与股权」页：公司概况、股权结构、按产品世代着色的大事记。
   数据全部来自 window.CMCC.profile（公司年报「公司简介」「股本结构」章节与官网大事记）。 */

var PROF = C.profile || {};
var SH = PROF.shareholding || {};
var PMETA = PROF._meta || {};
var OP = (C.operating && C.operating.annual) || {};
var AN = (C.annual && C.annual.annual) || {};

/* 世代配色：与 product.js 的时间线保持一致 */
var ERA_STYLE = {
    '语音': ERA_COLORS.voice,
    '短信': ERA_COLORS.sms,
    '数据': shade(ERA_COLORS.data, 0.25),
    '流量': ERA_COLORS.data,
    '宽带': ERA_COLORS.broadband,
    '5G':   '#c0392b',
    '算力': ERA_COLORS.appInfo,
    'AI':   '#8e44ad',
    '资本': MUTED
};
function eraColor(era) {
    var k = Object.keys(ERA_STYLE).find(function (key) { return (era || '').indexOf(key) >= 0; });
    return k ? ERA_STYLE[k] : '#94a3b8';
}

/* ==== 公司概况 ==== */
(function () {
    var p = PROF.profile || {};
    setText('profile-sub', (p.summary || '') + (p.asOf ? '　（数据截至 ' + p.asOf + '）' : ''));

    var lastFin = (function () {
        var ys = years(AN, 'totalRevenue');
        return ys.length ? { y: ys[ys.length - 1], r: AN[ys[ys.length - 1]] } : null;
    })();
    var lastOp = (function () {
        var ys = years(OP, 'mobileSubs');
        return ys.length ? { y: ys[ys.length - 1], r: OP[ys[ys.length - 1]] } : null;
    })();

    var kpis = [
        { label: '注册地与成立日期', value: p.incorporation || '—', delta: p.incorporationDate || '' },
        { label: '上市地与代码', value: p.tickers || '—', delta: p.listingNote || '' },
        { label: '实际控制人', value: p.controller || '—',
          delta: SH.groupStake != null ? '持股 ' + pct(SH.groupStake, 2) + (SH.asOf ? '（' + SH.asOf + '）' : '') : '' }
    ];
    if (lastFin) kpis.push({ label: lastFin.y + ' 营运收入', value: yiTxt(lastFin.r.totalRevenue) });
    if (lastOp) kpis.push({ label: lastOp.y + ' 移动客户数',
                            value: lastOp.r.mobileSubs == null ? '—' : fx(lastOp.r.mobileSubs, 2) + ' 亿户' });
    if (p.employees != null) kpis.push({ label: '员工总数', value: thou(p.employees) + ' 人',
                                         delta: p.employeesAsOf || '' });
    renderKpis('profile-kpis', kpis);

    var cards = [];
    if (p.business) cards.push({ title: '主营业务', body: p.business });
    if (p.threeServices) cards.push({ title: '2025 年起的三项主营口径', body: p.threeServices });
    if (p.strategy) cards.push({ title: '战略与规划', body: p.strategy });
    if ((PROF.risks || []).length) {
        cards.push({ title: '年报披露的主要风险', body: '<ul>' + PROF.risks.map(function (r) {
            return '<li>' + r + '</li>'; }).join('') + '</ul>' });
    }
    renderCards('profile-cards', cards);
})();

/* ==== 股权结构 ==== */
mount('chart-holders', function () {
    var parts = SH.breakdown || [];
    if (!parts.length) return { title: { text: '数据源中暂无股权结构明细', left: 'center', top: 'middle',
                                         textStyle: { fontSize: 18, color: MUTED } } };
    return {
        tooltip: { trigger: 'item', textStyle: { fontSize: 17 },
                   formatter: function (p) { return p.name + '<br>' + pct(p.value, 2); } },
        legend: { bottom: 6, textStyle: { fontSize: 17, color: '#444' }, type: 'scroll' },
        series: [{
            type: 'pie', radius: ['38%', '66%'], center: ['50%', '46%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, formatter: '{b}\n{d}%' },
            data: parts.map(function (p, i) {
                return { name: p.name, value: p.stake,
                         itemStyle: { color: p.residual ? RESIDUAL_PATTERN : PIE_COLORS[i % PIE_COLORS.length] } };
            })
        }]
    };
});
setText('holders-sub',
    '口径：占已发行总股数比例' + (SH.asOf ? '，截至 ' + SH.asOf : '')
    + (SH.totalShares ? ' · 总股本 ' + thou(SH.totalShares) + ' 股' : ''));
setHTML('holders-note',
    (SH.note || '')
    + (SH.groupStake != null
        ? '<b>中国移动通信集团有限公司直接与间接合计持股 ' + pct(SH.groupStake, 2) + '</b>，'
          + '余下由公众股东持有。'
        : '')
    + ' A 股与 H 股同股同权，但两地估值长期存在折溢价；'
    + '读股权结构时要注意「集团持股」包含通过全资子公司间接持有的部分，'
    + '年报会在股权结构图的脚注里逐层说明。');

/* ==== 大事记 ==== */
(function () {
    var ms = (PROF.milestones || []).slice().sort(function (a, b) {
        return a.year - b.year || (a.month || 0) - (b.month || 0);
    });
    if (!ms.length) { setHTML('ms-list', '<p class="note">数据源中暂无里程碑记录。</p>'); return; }
    setHTML('ms-list', ms.map(function (m) {
        return '<div class="ms-row">'
            + '<div class="ms-yr">' + m.year + (m.month ? '.' + (m.month < 10 ? '0' : '') + m.month : '') + '</div>'
            + '<div class="ms-era" style="background:' + eraColor(m.era) + '">' + (m.era || '—') + '</div>'
            + '<div class="ms-txt"><b>' + m.title + '</b>' + (m.detail ? '　' + m.detail : '') + '</div>'
            + '</div>';
    }).join(''));
})();

/* ==== 口径与缺口 ==== */
(function () {
    var items = [];
    if (PMETA.gaps) {
        Object.keys(PMETA.gaps).forEach(function (k) { items.push('<b>' + k + '</b>：' + PMETA.gaps[k]); });
    }
    if (PMETA.sources) items.push('<b>来源</b>：' + PMETA.sources);
    items.push('<b>股权比例的时点</b>：股权结构随增发、回购、股东增减持变化，'
        + '本页比例只对应上面标注的截止日期，跨期引用需回查当期年报或月报表。');
    items.push('<b>里程碑的世代标签</b>：世代（语音／短信／流量／5G／算力／AI）是本项目为便于阅读所加的归类，'
        + '不是公司年报的正式分类；同一件事可能同时属于两代（如 4G 发牌既是网络也是流量产品的起点）。');
    renderList('gaps-list', items);
})();
