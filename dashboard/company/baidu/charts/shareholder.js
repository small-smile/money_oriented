/* 百度 · 股权结构页
 *
 * 主图沿用 bank/_preview_holders_merged.html 那套「内圈明细 + 外圈派系 + 右侧手画标注」的双层环形图，
 * 只把数据源换成 20-F Item 6.E.：内圈是明细持股载体（Handsome Reward / 本人 / 配偶 / 员工代理 / 贝莱德），
 * 外圈按控制关系归并成派系，残余「其他股东」用灰斜线纹理垫最后。
 * 所有百分比一律由股数 ÷ 总股本现算，页面与本文件都不手抄比例。
 */
var H = B.holders, P = B.profile;
var SC = H.share_capital.outstanding_as_of_2026_01_31;
var TOTAL = SC.total;
var FN = H.footnotes_and_holding_structure_fy2025;
var TY = H.three_year_comparison.rows;
var FY25 = TY[TY.length - 1];
var TB = H.treasury_and_buyback;

function share2pct(n) { return +(n / TOTAL * 100).toFixed(4); }

/* ==== 明细持股载体：股数全部取自 20-F 脚注，比例现算 ==== */
/* 李彦宏本人直接持有 = 脚注 (1) 里 via 含「本人」的两项（在册 + ESOP 经纪账户 ADS） */
var LI_SELF = FN.robin_li_breakdown.components.filter(function (c) {
    return /本人/.test(c.via || '');
}).reduce(function (a, c) { return a + c.shares; }, 0);
var HR_TOTAL = FY25.handsome_reward.total_ordinary;                       /* B 439.2M + A 10.02M */
var MA_TOTAL = FN.melissa_ma.total_ordinary;                             /* 配偶，SEC 表不并入李彦宏 */
var PROXY = FN.all_directors_officers_group_footnote.included_proxy_shares;
var BLACKROCK = FN.blackrock_footnote.shares_class_a_sole_dispositive_power;
var INTEGRITY = FN.integrity_partners_v.class_b;
var OTHER_DO = FY25.all_directors_officers_group.class_a - FY25.robin_li.class_a;  /* 其余 5 位董事高管合计 */
var LISTED = LI_SELF + HR_TOTAL + MA_TOTAL + PROXY + BLACKROCK;
var RESIDUAL = TOTAL - LISTED;                                           /* 含 Integrity 与其余董事高管 */

var HOLDERS = [
    { name: 'Handsome Reward Limited（BVI，李彦宏 100% 持股）', short: 'Handsome Reward', fac: 'li',
      shares: HR_TOTAL, tag: 'B 类 ' + thou(FY25.handsome_reward.class_b) + ' + A 类 ' + thou(FY25.handsome_reward.class_a) },
    { name: '马东敏（李彦宏配偶，个人身份持有）', short: '马东敏（配偶）', fac: 'li',
      shares: MA_TOTAL, tag: 'B 类 ' + thou(FN.melissa_ma.class_b) + ' + A 类 ' + thou(FN.melissa_ma.class_a) + '；SEC 表不并入李彦宏' },
    { name: '李彦宏本人（在册 + ESOP 经纪账户 ADS）', short: '李彦宏本人', fac: 'li',
      shares: LI_SELF, tag: '全部为 A 类' },
    { name: '部分员工（已授予李彦宏不可撤销投票代理）', short: '员工投票代理', fac: 'proxy',
      shares: PROXY, tag: 'A 类，以 ADS 形式持有；投票权归李彦宏、经济权益属员工' },
    { name: '贝莱德 BlackRock, Inc.', short: '贝莱德', fac: 'br',
      shares: BLACKROCK, tag: 'A 类，股数为 2023-12-31 的 13G/A 口径' },
    { name: '其他股东（ADS 流通盘、港股流通股、未达披露线的机构）', short: '其他股东', fac: 'other',
      shares: RESIDUAL, tag: '含 Integrity Partners V ' + thou(INTEGRITY) + ' 股 B 类与其余 5 位董事高管合计 ' + thou(OTHER_DO) + ' 股 A 类' }
];
var FACTIONS = [
    { key: 'li',    title: '李彦宏家族（Handsome Reward + 本人 + 配偶）', short: '李彦宏家族', color: '#10243e' },
    { key: 'proxy', title: '员工不可撤销投票代理',                        short: '员工投票代理', color: '#c9a24a' },
    { key: 'br',    title: '贝莱德（2023-12-31 口径）',                    short: '贝莱德',      color: '#2980b9' },
    { key: 'other', title: '其他股东（20-F 不披露构成）',                  short: '其他股东',    color: '#95a5a6' }
];
HOLDERS.forEach(function (h) { h.value = share2pct(h.shares); });
/* ==== 双层环形图：派系按合计降序（残余垫最后）、派系内明细降序，两圈共用同一顺序 ==== */
var FAC_ROWS = FACTIONS.map(function (f) {
    var members = HOLDERS.filter(function (h) { return h.fac === f.key; })
                         .sort(function (a, b) { return b.value - a.value; });
    return {
        key: f.key, title: f.title, short: f.short, color: f.color, members: members,
        residual: f.key === 'other',
        value: +members.reduce(function (a, h) { return a + h.value; }, 0).toFixed(4)
    };
}).sort(function (a, b) {
    var ra = a.residual ? 1 : 0, rb = b.residual ? 1 : 0;
    return ra !== rb ? ra - rb : b.value - a.value;
});
/* 明细扇区颜色：残余用灰斜线纹理，其余按所属派系同色系由深到浅 */
function detailColors() {
    var map = {};
    FAC_ROWS.forEach(function (g) {
        g.members.forEach(function (h, k) {
            map[h.name] = g.residual ? RESIDUAL_PATTERN : shade(g.color, k * 0.22);
        });
    });
    return map;
}
function buildSeriesData() {
    var cmap = detailColors(), detail = [], fac = [];
    FAC_ROWS.forEach(function (g) {
        fac.push({
            name: g.title, value: g.value, _members: g.members,
            itemStyle: { color: g.residual ? RESIDUAL_PATTERN : g.color }
        });
        g.members.forEach(function (h) {
            detail.push({
                name: h.name, value: h.value, _shares: h.shares, _tag: h.tag, _fac: g.title,
                itemStyle: { color: cmap[h.name] }
            });
        });
    });
    return { detail: detail, fac: fac, cmap: cmap };
}
var ROW_H = 36, LINE = '#bbb';
var layout = 'cols';                 /* cols = 派系一列 + 明细一列；tree = 树状 */
/* 树状版把残余项也排进右侧清单，左侧不再留注释位，故留白比两列版窄；
 * 右侧要容下股东全称（最长「Handsome Reward Limited（BVI，李彦宏 100% 持股）」）故留得更宽 */
function leftPad() { return layout === 'cols' ? 160 : 40; }
function rightPad() { return layout === 'cols' ? 640 : 720; }
function pt(cx, cy, r, deg) {
    var a = deg * Math.PI / 180;
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
}
/* 引线：扇区在右半边时拐一次直接接标注；在左半边时先贴着外环画一段圆弧绕到右侧，
 * 否则直线会横穿整个环。弧的出口角取与标注行等高的角度，出来正好是一段水平线。 */
function leaderPoints(geo, deg, rowY, elbowX, endX) {
    var cx = geo.cx, cy = geo.cy, r0 = geo.rEdge + 6, r1 = geo.rEdge + 14;
    var start = pt(cx, cy, r0, deg);
    if (Math.cos(deg * Math.PI / 180) > 0.08) return [start, [elbowX, rowY], [endX, rowY]];
    var s = Math.max(-1, Math.min(1, (cy - rowY) / r1));
    var exit = Math.asin(s) * 180 / Math.PI;
    var norm = ((deg % 360) + 360) % 360, dlt = exit - norm;
    while (dlt > 180) dlt -= 360;
    while (dlt < -180) dlt += 360;
    var pts = [start];
    for (var i = 0; i <= 18; i++) pts.push(pt(cx, cy, r1, deg + dlt * i / 18));
    pts.push([endX, rowY]);
    return pts;
}
/* graphic 小工具：饼图 label 只能一层，排不出「派系 → 载体」的层级，所以标注全手画 */
function gfx() {
    var g = [];
    return {
        list: g,
        text: function (x, y, str, opt) {
            g.push({ type: 'text', x: x, y: y, silent: true, style: Object.assign({
                text: str, fill: '#333', fontSize: 21, align: 'left', verticalAlign: 'middle'
            }, opt || {}) });
        },
        poly: function (points) {
            g.push({ type: 'polyline', silent: true, shape: { points: points },
                     style: { stroke: LINE, fill: 'none', lineWidth: 1 } });
        },
        line: function (x1, y1, x2, y2) {
            g.push({ type: 'line', silent: true, shape: { x1: x1, y1: y1, x2: x2, y2: y2 },
                     style: { stroke: LINE, lineWidth: 1 } });
        },
        rect: function (x, y, w, h, fill, r) {
            g.push({ type: 'rect', silent: true, shape: { x: x, y: y, width: w, height: h, r: r || 3 },
                     style: { fill: fill } });
        }
    };
}
/* 残余项（其他股东）：两列版单独挂左侧、名称与比例分两行排；树状版直接排进右侧清单末尾 */
function residualNote(G, geo) {
    var res = FAC_ROWS.filter(function (f) { return f.residual; })[0];
    if (!res) return;
    var rp = pt(geo.cx, geo.cy, geo.rEdge + 6, res.mid), ry = rp[1] + 16;
    G.poly([rp, [rp[0] - 20, ry], [leftPad() - 14, ry]]);
    G.rect(6, ry - 22, 18, 18, RESIDUAL_PATTERN);
    G.text(32, ry - 13, res.short, { fill: '#555' });
    G.text(32, ry + 15, fx(res.value) + '%', { fill: '#555' });
}
/* 引线锚点：默认取扇区中心角；跨度很大的扇区（残余项占七成圆周）取与标注行同高、
 * 且落在扇区内的右侧角度，这样引线是一段平直短线，不必沿环底绕一大圈 */
function anchorDeg(geo, f, rowY) {
    if (f.a1 === undefined) return f.mid;
    var s = Math.max(-1, Math.min(1, (geo.cy - rowY) / (geo.rEdge + 14)));
    var cand = Math.asin(s) * 180 / Math.PI;
    return (cand <= f.a0 && cand >= f.a1) ? cand : f.mid;
}
/* 树状标注：引线 → 派系节点 → 分叉出持股载体；名称一律用全称，残余派系无明细、单占一行垫最后 */
function buildTree(geo, cmap) {
    var G = gfx(), cy = geo.cy;
    var elbowX = geo.cx + geo.R + 26, facX = geo.cx + geo.R + 62, valRight = geo.w - 12;
    var rows = 0;
    FAC_ROWS.forEach(function (f) { rows += 1 + (f.members.length > 1 ? f.members.length : 0); });
    var y = cy - (rows - 1) * ROW_H / 2;
    FAC_ROWS.forEach(function (f) {
        var facY = y, ink = f.residual ? '#555' : NAVY;
        G.poly(leaderPoints(geo, anchorDeg(geo, f, facY), facY, elbowX, facX - 8));
        if (f.residual) G.rect(facX - 2, facY - 9, 18, 18, RESIDUAL_PATTERN);
        else G.rect(facX, facY - 10, 6, 20, f.color, 2);
        G.text(facX + (f.residual ? 24 : 14), facY, f.title,
               { fontSize: 20, fontWeight: 'bold', fill: ink });
        G.text(valRight, facY, fx(f.value) + '%',
               { fontSize: 20, fontWeight: 'bold', fill: ink, align: 'right' });
        y += ROW_H;
        if (f.members.length > 1) {
            var trunkX = facX + 18, last = y + (f.members.length - 1) * ROW_H;
            G.line(trunkX, facY + 12, trunkX, last);
            f.members.forEach(function (m) {
                G.line(trunkX, y, trunkX + 16, y);
                G.rect(trunkX + 22, y - 8, 16, 16, cmap[m.name]);
                G.text(trunkX + 46, y, m.name, { fontSize: 18, fill: '#444' });
                G.text(valRight, y, fx(m.value) + '%', { fontSize: 18, fill: '#444', align: 'right' });
                y += ROW_H;
            });
        }
    });
    return G.list;
}
/* 两列标注：左列派系（引线接到派系扇区），右列持股载体，中间用括号连起来 */
function buildCols(geo, cmap) {
    var G = gfx(), cy = geo.cy;
    var elbowX = geo.cx + geo.R + 24, facX = geo.cx + geo.R + 56;
    /* 派系名最长「员工投票代理」6 字 21px 加粗 ≈ 126px，占比右对齐要留到 +238 才不贴字。
     * 两列版横向被两组「名称 + 占比」占满，全称（最长约 490px）确实排不下，只能用简称 */
    var facValRight = facX + 238, brX = facValRight + 26, detX = brX + 24, valRight = geo.w - 12;
    var named = FAC_ROWS.filter(function (f) { return !f.residual; });
    var rows = 0;
    named.forEach(function (f) { rows += f.members.length; });
    var top = cy - (rows - 1) * ROW_H / 2, y = top;
    G.text(facX, top - 38, '派系（按控制关系归并）', { fontSize: 17, fill: '#888' });
    G.text(detX, top - 38, '持股载体', { fontSize: 17, fill: '#888' });
    named.forEach(function (f) {
        var first = y, last = y + (f.members.length - 1) * ROW_H, mid = (first + last) / 2;
        G.poly(leaderPoints(geo, f.mid, mid, elbowX, facX - 8));
        G.rect(facX, mid - 10, 6, 20, f.color, 2);
        G.text(facX + 14, mid, f.short, { fontWeight: 'bold', fill: NAVY });
        G.text(facValRight, mid, fx(f.value) + '%', { fontWeight: 'bold', fill: NAVY, align: 'right' });
        if (f.members.length > 1) G.line(brX, first, brX, last);
        else G.line(facValRight + 8, mid, brX, mid);
        f.members.forEach(function (m) {
            G.line(brX, y, brX + 14, y);
            G.rect(detX, y - 8, 16, 16, cmap[m.name]);
            G.text(detX + 24, y, m.short, { fontSize: 19, fill: '#444' });
            G.text(valRight, y, fx(m.value) + '%', { fontSize: 19, fill: '#444', align: 'right' });
            y += ROW_H;
        });
    });
    residualNote(G, geo);
    return G.list;
}
function buildHolders(ins) {
    var d = buildSeriesData();
    var w = ins.getWidth(), h = ins.getHeight();
    var boxW = w - leftPad() - rightPad();
    var cx = leftPad() + boxW / 2, cy = h / 2;
    var R = Math.min(boxW / 2, h / 2 - 24);
    /* 外圈（派系）留窄环带，内圈（明细载体）厚一些 */
    var outBand = [R * 0.80, R * 0.98], inBand = [R * 0.44, R * 0.76];
    /* 派系扇区中心角与起止角（12 点起顺时针），引线起点靠它算 */
    var a = 90;
    FAC_ROWS.forEach(function (f) {
        var span = f.value * 3.6;
        f.a0 = a; f.a1 = a - span; f.mid = a - span / 2;
        a -= span;
    });
    function ring(radius, data) {
        return { type: 'pie', radius: radius, center: [cx, cy], startAngle: 90, sort: null,
                 label: { show: false }, labelLine: { show: false },
                 itemStyle: { borderColor: '#fff', borderWidth: 2 },
                 data: data, z: 2, animation: false };
    }
    var el = $('holders-legend');
    if (el) el.style.display = '';
    return {
        tooltip: {
            trigger: 'item', textStyle: { fontSize: 17 },
            formatter: function (p) {
                var it = p.data;
                if (it._members) {
                    var lines = it._members.length > 1 ? '<br>' + it._members.map(function (m) {
                        return m.short + '　' + thou(m.shares) + ' 股　' + fx(m.value) + '%';
                    }).join('<br>') : '';
                    return '<b>派系</b> ' + p.name + '：' + fx(p.value) + '%（占总股本）' + lines;
                }
                return p.name + '<br>' + thou(it._shares) + ' 股　' + fx(it.value) + '%（占总股本）'
                    + '<br><span style="color:#888">派系：' + it._fac + '</span>'
                    + '<br><span style="color:#888">' + it._tag + '</span>';
            }
        },
        series: [ring(outBand, d.fac), ring(inBand, d.detail)],
        graphic: (layout === 'cols' ? buildCols : buildTree)(
            { cx: cx, cy: cy, R: R, rEdge: outBand[1], w: w }, d.cmap)
    };
}
var holdersChart = mount('chart-holders', buildHolders);
/* 图下清单：派系一行，括号里列全称——两列排布图内只放得下简称，全称靠这里补齐 */
function renderHoldersLegend() {
    setHTML('holders-legend', FAC_ROWS.map(function (g) {
        var swatch = g.residual ? RESIDUAL_SWATCH_CSS : g.color;
        var items = g.members.map(function (m) { return m.name + ' ' + fx(m.value) + '%'; }).join('　');
        return '<div style="margin:3px 0"><span style="display:inline-block;width:12px;height:12px;'
            + 'border-radius:3px;background:' + swatch + ';vertical-align:-1px;margin-right:6px"></span>'
            + '<b style="color:' + NAVY + '">' + g.title + '</b> '
            + '<span style="color:' + NAVY + ';font-weight:600">' + fx(g.value) + '%</span>'
            + (g.members.length > 1 ? '　<span style="color:#777">（' + items + '）</span>' : '')
            + '</div>';
    }).join(''));
}
renderHoldersLegend();
document.querySelectorAll('[data-layout]').forEach(function (b) {
    b.addEventListener('click', function () {
        layout = b.getAttribute('data-layout');
        document.querySelectorAll('[data-layout]').forEach(function (x) {
            x.classList.toggle('active', x.getAttribute('data-layout') === layout);
        });
        holdersChart.setOption(buildHolders(holdersChart), true);
    });
});

/* ==== 持股全景的小标题与 KPI ==== */
var LI_FAC = FAC_ROWS.filter(function (f) { return f.key === 'li'; })[0];
setText('holders-sub', '口径日 ' + H.beneficial_ownership_fy2025.as_of + ' · 总股本 ' + thou(TOTAL)
    + ' 股（A 类 ' + thou(SC.class_a) + ' + B 类 ' + thou(SC.class_b) + '）'
    + ' · 20-F 只披露董事高管与「据公司所知」持任一类别 5% 以上者，故可穿透部分仅 '
    + fx(share2pct(LISTED)) + '%');
renderKpis('holders-kpis', [
    { label: '李彦宏家族经济权益', value: fx(LI_FAC.value) + '%',
      delta: thou(LI_FAC.value / 100 * TOTAL) + ' 股 · 含配偶马东敏' },
    { label: '其中 SEC 表口径（不含配偶）', value: fx(FY25.robin_li.pct_of_total_ordinary, 1) + '%',
      delta: '20-F 原文值 · ' + thou(FY25.robin_li.total_ordinary) + ' 股' },
    { label: '李彦宏投票权', value: fx(FY25.robin_li.pct_of_voting_power, 1) + '%',
      delta: '与经济权益背离 ' + fx(FN.voting_concentration.wedge_multiple, 1) + ' 倍' },
    { label: 'B 类股占总股本', value: fx(SC.class_b / TOTAL * 100) + '%',
      delta: '却对应 ' + fx(SC.class_b * 10 / H.share_capital.total_voting_power_as_of_2026_01_31.votes * 100)
             + '% 投票权' },
    { label: '唯一披露的机构股东', value: fx(share2pct(BLACKROCK)) + '%',
      delta: '贝莱德 · 数据日 ' + FN.blackrock_footnote.data_as_of },
    { label: '不可穿透的残余', value: fx(share2pct(RESIDUAL)) + '%',
      delta: 'ADS 存托 + 港股流通 + 未达披露线' }
]);
/* ==== 经济权益 vs 投票权 ==== */
var WVR = H.wvr_beneficiaries_tables.fy2025.rows;
var WVR_TOTAL = WVR[WVR.length - 1];
var VC = FN.voting_concentration;
var MA_PCT = share2pct(MA_TOTAL);
setText('ma-pct-inline', fx(MA_PCT) + '%');
var VOTE_ROWS = [
    { name: '李彦宏\n（SEC 表口径）', econ: FY25.robin_li.pct_of_total_ordinary, vote: FY25.robin_li.pct_of_voting_power },
    { name: '马东敏\n（配偶）', econ: MA_PCT, vote: FN.melissa_ma.pct_of_voting_power, calc: true },
    { name: 'Handsome\nReward', econ: FY25.handsome_reward.pct_of_total_ordinary, vote: FY25.handsome_reward.pct_of_voting_power },
    { name: '贝莱德', econ: FY25.blackrock.pct_of_total_ordinary, vote: FY25.blackrock.pct_of_voting_power },
    { name: 'WVR 受益人\n合计', econ: share2pct(WVR_TOTAL.class_a + WVR_TOTAL.class_b),
      vote: WVR_TOTAL.pct_of_voting_rights, calc: true }
];
renderCards('voting-cards', [
    { title: 'B 类的 10 票放大器',
      body: 'B 类 ' + thou(SC.class_b) + ' 股只占总股本 ' + fx(SC.class_b / TOTAL * 100)
          + '%，按每股 10 票折算却占总投票权 '
          + fx(SC.class_b * 10 / H.share_capital.total_voting_power_as_of_2026_01_31.votes * 100)
          + '%（总投票权 ' + thou(H.share_capital.total_voting_power_as_of_2026_01_31.votes)
          + ' 票为自算：A×1 + B×10）。B 类不上市、不流通，港股与 ADS 交易的都是 A 类。' },
    { title: '一个人过普通决议，一对夫妇过特别决议',
      body: '李彦宏单人投票权 ' + fx(VC.li_voting_pct, 1) + '% 已超过普通决议所需的简单多数；'
          + '夫妇合计 ' + fx(VC.li_plus_wife_voting_pct, 1) + '%（自算：WVR 合计 '
          + fx(VC.all_wvr_beneficiaries_voting_pct, 1) + '% 扣除 Integrity）已超过特别决议的三分之二门槛。'
          + '经济权益 ' + fx(VC.li_economic_pct, 1) + '% 与投票权 ' + fx(VC.li_voting_pct, 1)
          + '% 相差约 ' + fx(VC.wedge_multiple, 1) + ' 倍。' },
    { title: '投票权里有 3/4 不是自己的钱',
      body: '李彦宏 A 类 ' + thou(FY25.robin_li.class_a) + ' 股中，' + thou(PROXY) + ' 股（约 '
          + fx(PROXY / FY25.robin_li.class_a * 100, 1) + '%）只是员工授予的不可撤销投票代理，'
          + '经济权益属员工。剔除代理后其本人与 Handsome Reward 的经济权益约 '
          + fx(share2pct(LI_SELF + HR_TOTAL)) + '%。' },
    { title: 'B 类的第三方持有人',
      body: FN.integrity_partners_v.name_en + ' 持 ' + thou(INTEGRITY) + ' 股 B 类（占 B 类约 '
          + fx(INTEGRITY / SC.class_b * 100, 3) + '%，投票权四舍五入后为 0.0%），'
          + '是唯一非李彦宏家族的 B 类持有人，与 2005 年美股 IPO 前的早期投资人有关联，公司确认其为独立第三方。' }
]);
mount('chart-voting', function () {
    var base = axisBase({ x: VOTE_ROWS.map(function (r) { return r.name; }), right: 40, bottom: 52 });
    base.xAxis.axisLabel.lineHeight = 22;
    base.tooltip.formatter = function (ps) {
        var r = VOTE_ROWS[ps[0].dataIndex];
        return ps[0].name.replace('\n', '') + '<br>经济权益 ' + fx(r.econ) + '%<br>投票权 ' + fx(r.vote, 1) + '%'
            + (r.calc ? '<br><span style="color:#888">经济权益为自算值</span>' : '');
    };
    base.yAxis = valueAxis('%', { max: 80, formatter: '{value}' });
    base.series = [
        { name: '经济权益 %', type: 'bar', barGap: '12%', itemStyle: { color: NAVY },
          data: VOTE_ROWS.map(function (r) { return r.econ; }),
          label: { show: true, position: 'top', fontSize: 16, formatter: function (p) { return fx(p.value); } } },
        { name: '投票权 %', type: 'bar', itemStyle: { color: GOLD },
          data: VOTE_ROWS.map(function (r) { return r.vote; }),
          label: { show: true, position: 'top', fontSize: 16, formatter: function (p) { return fx(p.value, 1); } } }
    ];
    return base;
});
/* ==== 三年变化 ==== */
var YRS = TY.map(function (r) { return r.fiscal_year + '\n(' + r.as_of + ')'; });
mount('chart-3y', function () {
    var base = axisBase({ x: YRS, left: 88, right: 96, bottom: 52 });
    base.xAxis.axisLabel.lineHeight = 22;
    base.tooltip.formatter = function (ps) {
        var r = TY[ps[0].dataIndex];
        return r.fiscal_year + '（口径日 ' + r.as_of + '）<br>总股本 ' + thou(r.basis_total_ordinary)
            + ' 股<br>其中 B 类 ' + thou(r.basis_class_b) + ' 股<br>李彦宏经济权益 '
            + fx(r.robin_li.pct_of_total_ordinary, 1) + '%　投票权 ' + fx(r.robin_li.pct_of_voting_power, 1) + '%';
    };
    base.yAxis = [
        valueAxis('总股本（亿股）', { min: 26, max: 29 }),
        valueAxis('%', { position: 'right', splitLine: false, min: 0, max: 70 })
    ];
    base.series = [
        { name: '总股本（亿股）', type: 'bar', barWidth: '38%', itemStyle: { color: '#c3cdd8' },
          data: TY.map(function (r) { return +(r.basis_total_ordinary / 1e8).toFixed(3); }),
          label: { show: true, position: 'top', fontSize: 16, color: '#555',
                   formatter: function (p) { return fx(p.value, 2); } } },
        { name: '李彦宏经济权益 %', type: 'line', yAxisIndex: 1, symbolSize: 9, lineStyle: { width: 3 },
          itemStyle: { color: NAVY }, data: TY.map(function (r) { return r.robin_li.pct_of_total_ordinary; }),
          label: { show: true, fontSize: 16, formatter: '{c}%' } },
        { name: '李彦宏投票权 %', type: 'line', yAxisIndex: 1, symbolSize: 9, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: TY.map(function (r) { return r.robin_li.pct_of_voting_power; }),
          label: { show: true, fontSize: 16, formatter: '{c}%' } }
    ];
    return base;
});
mount('chart-proxy', function () {
    var base = axisBase({ x: YRS, left: 88, right: 96, bottom: 52 });
    base.xAxis.axisLabel.lineHeight = 22;
    base.tooltip.formatter = function (ps) {
        var r = TY[ps[0].dataIndex], p = r.robin_li.employee_proxy_class_a_included;
        return r.fiscal_year + '<br>员工投票代理 ' + thou(p) + ' 股 A 类<br>李彦宏 A 类合计 '
            + thou(r.robin_li.class_a) + ' 股<br>代理占其 A 类 ' + fx(p / r.robin_li.class_a * 100, 1) + '%';
    };
    base.yAxis = [
        valueAxis('百万股', { min: 0, max: 100 }),
        /* 右轴上限压到 80，让占比线整体骑在柱顶之上，避免线标签压住柱顶数字 */
        valueAxis('占李彦宏 A 类 %', { position: 'right', splitLine: false, min: 60, max: 80 })
    ];
    base.series = [
        { name: '员工投票代理 A 类股（百万股）', type: 'bar', barWidth: '38%', itemStyle: { color: NAVY },
          data: TY.map(function (r) { return +(r.robin_li.employee_proxy_class_a_included / 1e6).toFixed(2); }),
          label: { show: true, position: 'insideTop', distance: 8, fontSize: 16, color: '#fff', formatter: '{c}' } },
        { name: '占李彦宏 A 类持股 %', type: 'line', yAxisIndex: 1, symbolSize: 9, lineStyle: { width: 3 },
          itemStyle: { color: GOLD },
          data: TY.map(function (r) {
              return +(r.robin_li.employee_proxy_class_a_included / r.robin_li.class_a * 100).toFixed(1);
          }),
          label: { show: true, fontSize: 16, formatter: '{c}%' } }
    ];
    return base;
});
setHTML('trend-note', TY.map(function (r) {
    return '<b>' + r.fiscal_year + '</b>（' + r.as_of + '）：总股本 ' + thou(r.basis_total_ordinary)
        + ' 股，李彦宏 ' + thou(r.robin_li.total_ordinary) + ' 股 / '
        + fx(r.robin_li.pct_of_total_ordinary, 1) + '%，投票权 ' + fx(r.robin_li.pct_of_voting_power, 1)
        + '%，其中员工投票代理 ' + thou(r.robin_li.employee_proxy_class_a_included)
        + ' 股；在美在册持有人持股 ' + fx(r.us_record_holders.pct, 1) + '%（' + r.us_record_holders.count + ' 名）。';
}).join('<br>') + '<br><span style="color:#777">在美在册持股占比 '
    + TY.map(function (r) { return fx(r.us_record_holders.pct, 1) + '%'; }).join(' → ')
    + ' 的下降反映 ADS 仓位向港股迁移；这是在册口径，不能直接换算成两地流通仓位。</span>');
/* ==== 双重股权架构 ==== */
var DC = H.dual_class_structure;
var VOTES = H.share_capital.total_voting_power_as_of_2026_01_31.votes;
renderRows('dual-tbody', [
    { _th: true, cells: ['每股投票权', DC.class_a.votes_per_share + ' 票', '<b>' + DC.class_b.votes_per_share + ' 票</b>'] },
    { _th: true, cells: ['在外股数（' + H.beneficial_ownership_fy2025.as_of + '）',
        thou(SC.class_a) + '<br><span style="color:#777">占总股本 ' + fx(SC.class_a / TOTAL * 100) + '%</span>',
        thou(SC.class_b) + '<br><span style="color:#777">占总股本 ' + fx(SC.class_b / TOTAL * 100) + '%</span>'] },
    { _th: true, cells: ['对应投票权（自算）',
        thou(SC.class_a) + ' 票<br><span style="color:#777">' + fx(SC.class_a / VOTES * 100) + '%</span>',
        thou(SC.class_b * 10) + ' 票<br><span style="color:#777">' + fx(SC.class_b * 10 / VOTES * 100) + '%</span>'] },
    { _th: true, cells: ['上市与流通', DC.class_a.listed_where, DC.class_b.listed_where] },
    { _th: true, cells: ['转换权', '任何情况下均不可转为 B 类', DC.class_b.convertible_into_class_a] },
    { _th: true, cells: ['表决方式', DC.voting_together, '同左（合并计票）'] },
    { _th: true, cells: ['股息与清算等其他权利', '与 B 类完全相同', '与 A 类完全相同'] }
]);
renderList('dual-triggers', DC.class_b.auto_conversion_triggers);
var CONV = DC.class_b_converted_to_class_a_by_year;
renderRows('dual-conv', ['2023', '2024', '2025'].map(function (y) {
    return { _th: true, cells: [y + ' 年', thou(CONV[y])] };
}));
setHTML('dual-note', '若全部 B 类转换，将发行 ' + thou(DC.hypothetical_full_conversion.class_a_to_be_issued)
    + ' 股 A 类，相当于 ' + DC.hypothetical_full_conversion.as_of + ' 已发行 A 类的约 '
    + fx(DC.hypothetical_full_conversion.pct_of_existing_class_a, 1) + '%（20-F 原文值）。'
    + 'sunset 条款的距离：李彦宏经 Handsome Reward 持有 ' + thou(FY25.handsome_reward.class_b) + ' / '
    + thou(SC.class_b) + ' ≈ ' + fx(FY25.handsome_reward.class_b / SC.class_b * 100, 1)
    + '% 的 B 类（自算），距「李彦宏及其联属人士合计不足 5% 即全体强制转为 A 类」的触发线极远，'
    + '架构在可预见期内不会自动终止。三年实际转换量合计仅 '
    + thou(CONV['2023'] + CONV['2024'] + CONV['2025']) + ' 股，'
    + 'B 类总量从 ' + thou(TY[0].basis_class_b) + ' 股降至 ' + thou(SC.class_b) + ' 股——回购只作用于 A 类。'
    + '<br><span style="color:#777">优先股：' + DC.preferred_shares + '</span>');
/* ==== 回购与库存股 ==== */
var RB = TB.repurchases_by_year, BY = ['2023', '2024', '2025'];
var TS = TB.treasury_shares_outstanding, MV = TB.treasury_movement_2025;
var RB_SH = BY.reduce(function (a, y) { return a + RB[y].class_a_shares_repurchased; }, 0);
var RB_AMT = BY.reduce(function (a, y) { return a + RB[y].aggregate_price_rmb_bn; }, 0);
renderKpis('buyback-kpis', [
    { label: '三年累计回购股数', value: fx(RB_SH / 1e6, 1) + ' 百万股',
      delta: '占 2024-01-31 总股本 ' + fx(RB_SH / TY[0].basis_total_ordinary * 100) + '%' },
    { label: '三年累计回购金额', value: '¥' + fx(RB_AMT, 1) + ' 十亿',
      delta: 'FY2025 折 US$' + thou(RB['2025'].aggregate_price_usd_mn) + ' 百万' },
    { label: '总股本三年净减少', value: fx((TY[0].basis_total_ordinary - TOTAL) / 1e6, 1) + ' 百万股',
      delta: thou(TY[0].basis_total_ordinary) + ' → ' + thou(TOTAL) },
    { label: '库存股余额（2025-12-31）', value: thou(TS['2025-12-31']) + ' 股',
      delta: '上年末 ' + thou(TS['2024-12-31']) + ' 股' },
    { label: '2025 年注销', value: thou(MV.cancelled_during_2025) + ' 股',
      delta: '2026 年 1—2 月又注销 ' + thou(MV.cancelled_after_period_end.shares) + ' 股' },
    { label: '2025 年重新发行给员工', value: thou(MV.reissued_to_employees_and_directors) + ' 股',
      delta: MV.reissued_reason }
]);
mount('chart-buyback', function () {
    var base = axisBase({ x: BY.map(function (y) { return y + ' 年'; }), left: 88, right: 96 });
    base.tooltip.formatter = function (ps) {
        var y = BY[ps[0].dataIndex], r = RB[y];
        return y + ' 年<br>回购 ' + thou(r.class_a_shares_repurchased) + ' 股 A 类（或等量 ADS）<br>金额 ¥'
            + fx(r.aggregate_price_rmb_bn, 1) + ' 十亿'
            + (r.aggregate_price_usd_mn ? '（约 US$' + thou(r.aggregate_price_usd_mn) + ' 百万）' : '')
            + '<br><span style="color:#888">均价约 ¥' + fx(r.aggregate_price_rmb_bn * 1e9 / r.class_a_shares_repurchased)
            + ' / 股</span>';
    };
    base.yAxis = [
        valueAxis('百万股', { min: 0, max: 100 }),
        valueAxis('人民币十亿元', { position: 'right', splitLine: false, min: 0, max: 8 })
    ];
    base.series = [
        { name: '回购股数（百万股）', type: 'bar', barWidth: '40%', itemStyle: { color: NAVY },
          data: BY.map(function (y) { return +(RB[y].class_a_shares_repurchased / 1e6).toFixed(2); }),
          /* 柱标签放柱内白字，腾出柱顶给金额线的标签 */
          label: { show: true, position: 'insideTop', distance: 8, fontSize: 16, color: '#fff', formatter: '{c}' } },
        { name: '回购金额（人民币十亿元）', type: 'line', yAxisIndex: 1, symbolSize: 9, lineStyle: { width: 3 },
          itemStyle: { color: GOLD }, data: BY.map(function (y) { return RB[y].aggregate_price_rmb_bn; }),
          label: { show: true, fontSize: 16, formatter: '{c}' } }
    ];
    return base;
});
renderCards('buyback-cards', TB.repurchase_programs.map(function (p) {
    return { title: p.name + '（US$' + fx(p.size_usd_bn, 1) + ' 十亿）',
             body: p.authorized + '，标的为 ' + p.scope + '，有效期至 ' + p.effective_until
                 + '。<br><span style="color:#777">' + p.status + '</span>' };
}).concat([
    { title: '回购如何抬高控制权比例',
      body: '回购标的全是 A 类，B 类三年只因持有人转换减少 '
          + thou(TY[0].basis_class_b - SC.class_b) + ' 股，'
          + '所以分母缩小机械地抬高了 B 类与李彦宏的占比——'
          + '李彦宏经济权益 ' + fx(TY[0].robin_li.pct_of_total_ordinary, 1) + '% → '
          + fx(FY25.robin_li.pct_of_total_ordinary, 1) + '% 里含这一成分，并非增持。' },
    { title: '库存股不分类别、无 issued/outstanding 对账',
      body: '20-F 以 ordinary shares 表述库存股余额、未标 A/B，也未提供已发行与在外股数的对账表。'
          + '按库存股会计政策（成本法、注销时仅冲减面值）与「回购标的均为 A 类」可推断库存股全为 A 类，但原文未明示。' }
]));
/* ==== 披露缺口与口径说明 ==== */
renderList('gaps-list', H.disclosure_gaps.map(function (g) {
    return '<b>' + g.gap + '</b>：' + g.detail;
}));
setHTML('caliber-note', '<ul class="gap-list">'
    + H.hk_disclosure.caliber_difference_sfo_vs_sec.map(function (t) { return '<li>' + t + '</li>'; }).join('')
    + '</ul><p style="margin:8px 0 0;color:#777">港交所年报性质：'
    + H.hk_disclosure.sfo_substantial_shareholder_table.reason
    + '　HKSCC Nominees 持股同样缺失（' + H.hk_disclosure.hkscc_nominees.reason.slice(0, 60) + '……）。</p>');

