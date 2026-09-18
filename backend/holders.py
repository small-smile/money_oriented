import os
import re
import json

from flask import Blueprint, jsonify, request

from backend.shared import (
    TABLES_DIR, _holders_manual, _company_codes, _company_entity,
    _resolve_company_code, _cross_industry_redirect,
    success, error,
)
from backend.bank import BANK_ORDER
from backend.industry import INSURER_PEERS, DEVELOPER_PEERS
from backend.cement_ops import CEMENT_PEERS
from backend.telecom_ops import TELECOM_PEERS

holders_bp = Blueprint("holders", __name__)

# ── 股权结构：银行/险企/开发商/水泥/运营商共用一套 ─────────────────────────────
# 五个板块的 <板块>_<code>_annual.json 里 holders（接口前十名股东快照）字段结构完全相同，
# 所以股权结构不按板块各写一页，统一由 dashboard/company/shareholder.html 一页读这份 payload（各板块只有 header 不同），
# 靠 ?industry=&code= 切换。银行表另有 holder_num（逐期股东户数）与 holder_concentration
# （集中度序列）两层，有就下发、页面多画两张图，其余板块自然缺省。
HOLDER_INDUSTRIES = {
    "bank": {"label": "银行", "codes": list(BANK_ORDER)},
    "insurer": {"label": "险企", "codes": INSURER_PEERS},
    "developer": {"label": "开发商", "codes": DEVELOPER_PEERS},
    "cement": {"label": "水泥企业", "codes": CEMENT_PEERS},
    "telecom": {"label": "运营商", "codes": TELECOM_PEERS},
    # 下面两个板块没有 <板块>_<code>_annual.json，股东块整份来自手工层（年报／20-F 原文抽取）
    "tech": {"label": "科技（百度）", "codes": ["09888"]},
    "food": {"label": "食品", "codes": ["605338"]},
}

# 顶部导航：股权结构页只有一份（dashboard/company/shareholder.html 一页服务七个板块），
# 它躺在 company/bank/ 目录下，site-header.js 那套「按目录判板块」的办法判不出来，所以由本接口
# 按 ?code= 判定板块，再告诉页面该载哪个 header 脚本、用哪一组链接 —— 页面上只保留这一条全局导航。
# header 路径相对 dashboard/ 根；group 是 site-header.js 里 GROUPS[].dir，页面据它设 __HEADER_GROUP。
NAV_HEADERS = {
    "bank": {"header": "common/bank-header.js", "group": None},
    "insurer": {"header": "common/site-header.js", "group": "industry/insurance/"},
    "developer": {"header": "common/site-header.js", "group": "industry/realestate/"},
    "cement": {"header": "common/site-header.js", "group": "industry/cement/"},
    "telecom": {"header": "common/site-header.js", "group": "industry/telecom/"},
    "tech": {"header": "common/site-header.js", "group": "company/baidu/"},
    # 食品板块没有行业页分组，页面自己画一条只有品牌与公司切换的导航
    "food": {"header": None, "group": None},
}


DEFAULT_HOLDER_INDUSTRY = "bank"


def _industry_of_code(code):
    """任意一地的代码 → 所属板块：先查 company_codes.json 的 industry 字段
    （H 股 01398 / 美股 BIDU 这类另一地代码照样认得出），表里没有的退回按各板块名单反查。
    代码与板块本来就是一对一的，所以吃 ?code= 的接口都不必再收 industry 参数。"""
    ent = _company_entity(code) if code else None
    hit = ent.get("industry") if ent else None
    if not hit and code:
        hit = next((k for k, v in HOLDER_INDUSTRIES.items() if code in v["codes"]), None)
    return hit if hit in HOLDER_INDUSTRIES else None


def industry_default_code(industry):
    """板块的默认公司：名单里第一家真有股东名册的（纯 H 股那几家接口不返回名册，跳过）。
    没给 ?code= 时用它兜底，老链接 ?industry= 也靠它换成代码。"""
    spec = HOLDER_INDUSTRIES.get(industry) or {}
    manual = _holders_manual()
    fallback = None
    for c in spec.get("codes") or []:
        d = _holder_table(industry, c) or {}
        man = manual.get(f"{industry}:{c}") or {}
        if not d and not man.get("holders"):
            continue
        fallback = fallback or c
        if man.get("holders") or d.get("holders"):
            return c
    return fallback


def read_nav(code=None, industry=None):
    """按公司代码判定所属板块，并给出页面该渲染哪一条全局导航 + 该板块的默认公司代码。
    代码优先于 industry 参数：?code=600941 一个参数就够；industry 只是老链接
    （site-header 里那种 ?industry=cement）的兜底，页面拿到 data.code 后一律按代码取数。
    两个参数都没给（或都认不出）时落到 bank，与页面原先的默认一致。"""
    ind = industry if industry in HOLDER_INDUSTRIES else None
    note = None
    hit = _industry_of_code(code)
    if hit:
        if ind and hit != ind:
            note = (f"{code} 属 {hit} 板块（{HOLDER_INDUSTRIES[hit]['label']}），"
                    f"导航按代码判定，传进来的 industry={ind} 不作准")
        ind = hit
    elif code:
        note = f"{code} 不在任何板块的名单里，导航按 industry={ind or 'bank'} 渲染"
    if not ind:
        ind = DEFAULT_HOLDER_INDUSTRY
    nav = NAV_HEADERS[ind]
    return success({
        "industry": ind,
        "label": HOLDER_INDUSTRIES[ind]["label"],
        "header": nav["header"],
        "group": nav["group"],
        # 页面拿这个代码去 /api/holders：给了 ?code= 就用它，只给 ?industry= 的老链接用默认公司
        "code": code if hit else industry_default_code(ind),
        "note": note,
    })


def _company_charts_block(code, key):
    """company_charts_<code>.json 里的任意一块（银行年报口径页的数据源）。"""
    path = os.path.join(TABLES_DIR, f"company_charts_{code}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get(key) or None


def _company_charts_holders(code):
    """company_charts_<code>.json 里的 holders 块（年报口径：holders / holderData / factions）。"""
    return _company_charts_block(code, "holders")


def _bank_history_from_charts(code, annual_div=None):
    """银行的历年股本与历年每 10 股分红 —— 原先画在银行自己的年报口径股东页里，
    数据在 company_charts_<code>.json 的 share-capital / dividend-per10 两块。
    股权结构合成一页后这两张图也由接口下发，字段名与手工层保持一致：
      share_capital  [[年, 股数(股), 变动原因, 类型]]  ← share-capital.years / shares(亿股) / events
      dividend_per10 [[年, 每 10 股(元)]]        ← dividend-per10.years9 / per10
                                                 ∪ bank 表的 dividend_per10（年→值的字典）
    events 给的是当年资本运作的原文摘要，没有 events 的年份写「未变动」（与手工层同约定，
    前端按这个字段给柱子上色）。分红取两源并集：company_charts 那份是逐年抄年报的，
    bank 表那份来自公司数据接口，**重叠年份以年报口径（company_charts）为准**（信息源优先级），
    接口那份只补年报口径缺的年份（渝农商行 2011–2018 只有年报口径有、民生银行 2000 只有接口有）。
    44 家逐年比对过，重叠年份只有 600016 的 2017 两源不一致（接口 2.10 / 年报口径 1.50）：
    民生 2017 年报「普通股股利」段写明上半年每 10 股 1.20 元 + 下半年 0.30 元（另送股 2 股），
    全年现金 1.50 元，接口那个 2.10 在年报里没有对应口径 —— 所以这里取 1.50。"""
    cap = _company_charts_block(code, "share-capital") or {}
    div = _company_charts_block(code, "dividend-per10") or {}
    events = cap.get("events") or {}
    sc = []
    for y, v in zip(cap.get("years") or [], cap.get("shares") or []):
        if v is None:
            continue
        ev = events.get(str(y)) or {}
        items = ev.get("items") or []
        # 第 4 位是资本运作类型（ipo/pp/seo，只有精编过成因的行才有）—— 页面据它按银行原先那页
        # 的调色板给点上色；没有这一层的公司退回「动过／未动过」两色
        sc.append([str(y), int(round(float(v) * 1e8)),
                   "；".join(items) if items else "未变动", ev.get("type")])
    dp = {}
    if isinstance(annual_div, dict):
        dp.update({str(y): v for y, v in annual_div.items() if v is not None})
    # 年报口径后写，重叠年份就覆盖掉接口那份
    dp.update({str(y): v for y, v in zip(div.get("years9") or [], div.get("per10") or [])
               if v is not None})
    return (sc or None), ([[y, dp[y]] for y in sorted(dp)] or None)


def _bank_factions(code):
    """银行的一致行动人早就画在年报口径股东页里，派系表就存在 company_charts_<code>.json。
    那份 names 是年报「前十名股东」的长名，与接口快照的名字大体同源、但不保证全部对得上；
    对不上的股东在前端各自成组（normalize 容错），不影响其余派系。"""
    blk = _company_charts_holders(code)
    return (blk or {}).get("factions") or None


def _holder_table(industry, code):
    """只读 annual 表里股权结构要用的那几块，不做手工层合并（股东数据与经营口径无关）。"""
    path = os.path.join(TABLES_DIR, f"{industry}_{code}_annual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm_holder_name(s):
    """比对股东名用的归一化：全角括号/破折号折半角、去空白、砍掉通用公司后缀。
    年报原文与接口名册在这三处系统性不同（年报写「太平人寿保险有限公司－传统－…－022L－CT001 沪」，
    接口写「太平人寿保险有限公司-传统-…-022L-CT001沪」），不折一下没有一个名字能对上。
    银行那 45 份派系表里另有 5 家用的是年报页面上的简称（「渝富资本」「大家人寿-万能」），
    那类差异归一化救不回来，只能靠唯一前缀匹配或干脆不归组。"""
    s = (s or "")
    for a, b in (("（", "("), ("）", ")"), ("－", "-"), ("—", "-"), ("‐", "-"), ("–", "-")):
        s = s.replace(a, b)
    s = re.sub(r"\s+", "", s)
    for tail in ("股份有限公司", "有限责任公司", "有限公司", "公司"):
        if s.endswith(tail) and len(s) > len(tail) + 1:
            return s[: -len(tail)]
    return s


def _resolve_factions(holders, factions, aliases=None):
    """把派系表里的股东名对到名册里的真实名字上；对不上的成员直接丢掉，整组空了就丢整组。
    只认三种命中：别名表里给定、归一化后完全相同、或名册里唯一一个以它开头的名字（唯一才算）。
    宁可少归一个成员（那家股东在前端自成一组），也不猜——猜错就是把股份记到别人名下。

    aliases 是手工层的 faction_aliases（「年报页面简称」→「接口名册全称」），
    给那几家派系表用简称的银行（渝农商行、农行、招行、民生、天津）人工核对后写死，
    build_holders_manual.py 在生成时会断言每个目标名字确实在该行的接口名册里。"""
    if not factions or not holders:
        return None
    alias = {_norm_holder_name(k): v for k, v in (aliases or {}).items()}
    exact, out = {}, []
    for h in holders:
        exact.setdefault(_norm_holder_name(h.get("name")), h.get("name"))
    for f in factions:
        hit = []
        for n in f.get("names") or []:
            key = _norm_holder_name(n)
            if key in alias:
                key = _norm_holder_name(alias[key])
            if key in exact:
                hit.append(exact[key])
                continue
            cand = [v for k, v in exact.items() if k.startswith(key)]
            if len(cand) == 1:
                hit.append(cand[0])
        if hit:
            g = dict(f)
            g["names"] = hit
            out.append(g)
    return out or None


def _ring_block_from_charts(code):
    """年报口径的环形图数据块 —— 取 company_charts_<code>.json 的 holders 块。
    shareholder.html（各行业的标准模板）画的就是这一份：holderData 是图上的名字 +
    占总股本比例、已含「其他流通股东」那一块，factions 引用的正是这套名字；
    另一份 holders 带类别与报告期内增减（文字，如「+79.14 万股」「不变」）。
    两份名字 44 家银行完全一致，个别行（渝农商行）图上用简称、表里用另一套简称，
    这时按比例值唯一对上 —— 对不上就只是少两列，不猜。"""
    blk = _company_charts_holders(code)
    if not blk or not blk.get("holderData"):
        return None
    by_name, by_pct = {}, {}
    for h in blk.get("holders") or []:
        by_name[h.get("name")] = h
        by_pct.setdefault(round(float(h.get("pct") or 0), 2), []).append(h)
    out = []
    for x in blk["holderData"]:
        m = by_name.get(x.get("name"))
        if m is None:
            cand = by_pct.get(round(float(x.get("value") or 0), 2)) or []
            m = cand[0] if len(cand) == 1 else None
        out.append({"name": x.get("name"), "value": x.get("value"),
                    "type": (m or {}).get("type") or "",
                    # 年报口径这份增减是文字（「+79.14 万股」），不是股数，原样传给前端
                    "chgText": (m or {}).get("chg") or ""})
    return {"caliber": "占总股本", "holderData": out, "factions": blk.get("factions") or []}


# 环形图的附加口径：company_charts_<code>.json 里除 holders 之外的股东块。
# 渝农商行 2010 年在港上市、2019 年才上 A 股，H 股年报只到 2018、A 股年报从 2019 起，
# 两边没有重叠年份 —— 原先那一页把这两张环形图并排画在主图右边，并写了一段口径说明；
# 页面合成一页后改成图上切口径，说明文字（label/caliber/note）在手工层 ring_alt_meta 里。
_RING_ALT_KEYS = ("holders-h", "holders-h-only")


def _ring_alt_from_charts(code, meta):
    """附加口径的环形图数据块，按 ring_alt_meta 里给了说明的那几块下发（没有说明就不下发 ——
    分母是总股本还是 H 股股本、取的是哪一年年报，这些不写清楚的图不该让人切过去看）。"""
    out = []
    for key in _RING_ALT_KEYS:
        m = (meta or {}).get(key)
        blk = _company_charts_block(code, key) if m else None
        if not blk or not blk.get("holderData"):
            continue
        out.append({
            "key": key,
            "label": m.get("label") or key,
            "caliber": m.get("caliber") or "占总股本",
            "residual_label": m.get("residual_label"),
            "note": m.get("note"),
            "holderData": [{"name": x.get("name"), "value": x.get("value"),
                            "type": "", "chgText": ""} for x in blk["holderData"]],
            "factions": blk.get("factions") or [],
        })
    return out or None


# ── 逐公司的解读文字 ───────────────────────────────────────────────────────────
# 银行原先那套年报口径股东页上每张图下都有一段解读（本年分红多少、股本哪几年动过、
# 户数从多少到多少、集中度区间与第一大股东是谁）。页面合成一页后这些话不能再写死在 HTML 里，
# 全部由下面几个函数**从本公司自己的序列现算**——所以任何板块、任何 code 都有话可说，
# 数据层缺哪一层就少哪一段，绝不会串到别家公司的数字。
# 文字里的加粗用 **…**（前端 mdBold 转 <b>），接口不下发 HTML。
YI = 1e8


def _n(v, nd=2):
    return f"{v:,.{nd}f}"


def _narr_dividend(name, div, unit, annual, cap_by_year):
    """分红解读：最近年度每 10 股派现 → 现金分红总额与分红率，再给近五年累计与派现年份数。
    分红总额 = 每 10 股 ÷ 10 × 当年末股份总数；分红率 = 分红总额 ÷ 当年归母净利润。
    股份总数优先用本页那条股本序列（逐年抄年报「股份变动情况表」的股数），只有没有序列的板块
    才退回年度表的 share_capital —— 那个字段是「股本」科目的元金额，面值 1 元的公司才等于股数，
    中国移动那样两者差 20 倍以上的（股本科目里含发行溢价）会被下面的合理性检查挡掉，宁可不给
    分红总额，也不拿一个错了一个量级的分母去算分红率。
    以港元宣派的公司（中国移动）不算分红率——港元派现除人民币利润是混币种，只说明原因。"""
    rows = [(str(y), float(v)) for y, v in (div or []) if v is not None]
    if not rows:
        return None

    def shares(y):
        if y in cap_by_year:
            return cap_by_year[y]
        v = (annual or {}).get(y, {}).get("share_capital")
        now = (annual or {}).get(y, {}).get("total_share")
        if v and now and abs(float(v) / float(now) - 1) > 0.25:
            return None          # 股本科目的元金额与接口总股本差得太远，不是股数，弃用
        return float(v) if v else None

    def yi(v):
        return _n(v, 2 if v < 100 else 0)

    ly, lp = rows[-1]
    paid = [r for r in rows if r[1] > 0]
    bits = [f"{name} **{ly} 年度每 10 股派现 {_n(lp, 4)} {unit}**（含税）"]
    amt = (lp / 10 * shares(ly) / YI) if shares(ly) else None
    if amt:
        bits.append(f"对应现金分红约 **{yi(amt)} 亿{unit}**")
        np_ = (annual or {}).get(ly, {}).get("parent_netprofit")
        if np_ and unit == "元":
            bits.append(f"分红率（占归母净利润）约 **{_n(amt * YI / float(np_) * 100, 1)}%**")
        elif np_:
            bits.append(f"归母净利润以人民币计、派现以{unit}宣派，两者不同币种，**不算分红率**")
    five = [(y, p) for y, p in rows if int(y) >= int(ly) - 4]
    cum = [(lp2 / 10 * shares(y2) / YI) if shares(y2) else None for y2, lp2 in five]
    if len(five) > 1 and all(x is not None for x in cum):
        bits.append(f"近 {len(five)} 年（{five[0][0]}–{ly}）累计分红约 **{yi(sum(cum))} 亿{unit}**")
    text = "；".join(bits) + "。"
    text += (f"图上 {rows[0][0]}–{rows[-1][0]} 共 {len(rows)} 个年度，其中 **{len(paid)} 个年度派现**"
             f"、{len(rows) - len(paid)} 个年度为 0。")
    if amt is None:
        text += "（当年末股份总数取不到可信值，分红总额与分红率算不出来，只给每 10 股金额。）"
    return text


def _narr_share_capital(name, rows, brk):
    """股本解读：区间两端的股数、哪几年动过、各动了多少，以及有原文成因的那几次。
    有口径断点（拆股／并股）时按断点后的口径折算再比，否则「1 拆 80」会被读成一次增发。"""
    if not rows or len(rows) < 2:
        return None, None
    at = str((brk or {}).get("at") or "")
    factor = float((brk or {}).get("factor") or 0) or None
    idx = next((i for i, r in enumerate(rows) if str(r[0]) == at), -1)
    val = [float(r[1]) * (factor if (factor and 0 <= i < idx) else 1) / YI
           for i, r in enumerate(rows)]
    chg = [(str(rows[i][0]), round(val[i] - val[i - 1], 4)) for i in range(1, len(rows))
           if abs(val[i] - val[i - 1]) >= 0.005 and not (idx > 0 and i == idx and factor)]
    text = (f"{name} {rows[0][0]}–{rows[-1][0]} 年股份总数由 **{_n(val[0])} 亿股**"
            f"{'增' if val[-1] >= val[0] else '减'}至 **{_n(val[-1])} 亿股**，"
            f"其间 **{len(chg)} 个年份**发生变动")
    if chg:
        # 变动年份多的公司（百度 21 年里动过 19 次）逐年列会把这段读成一串数字，
        # 超过 10 次就只列幅度最大的 8 次，其余给个上限值，逐年数值本来就在 tooltip 里
        show, rest = chg, []
        if len(chg) > 10:
            big = sorted(chg, key=lambda x: -abs(x[1]))[:8]
            show = [x for x in chg if x in big]
            rest = [x for x in chg if x not in big]
        text += "：" + "、".join(f"{y} 年 {d:+,.2f} 亿股" for y, d in show)
        text += (f"，其余 {len(rest)} 个年份每年变动不超过 "
                 f"{_n(max(abs(d) for _, d in rest))} 亿股。" if rest else "。")
    else:
        text += "。"
    if factor and idx > 0:
        text += f"（{at} 年为 1 拆 {factor:.0f} 的口径断点，不计入上面的逐年增减。）"
    why = [(str(r[0]), r[2]) for r in rows if len(r) > 2 and r[2] and r[2] != "未变动"]
    detail = None
    if why:
        detail = ("**各次变动的年报原文成因：**" +
                  "；".join(f"{y} 年 {t}" for y, t in why) + "。")
    else:
        detail = ("本公司的数据层只有逐年股数、**没有逐次成因**（IPO／定增／配股／转增要读当年年报"
                  "「股本变动及股东情况」章节），所以变动年份的原因一律写「未变动」以外的空缺。")
    return text, detail


def _narr_holder_num(name, rows):
    """户数解读：披露期数、区间、起止与极值，以及 A/H 拆分覆盖到哪几期。"""
    rows = [r for r in (rows or []) if r and len(r) > 1]
    if len(rows) < 2:
        return None
    tot = [r[1] for r in rows if r[1] is not None]
    if not tot:                       # 手工年报层只给 A/H 拆分、不给合计（天津银行只有 H 股登记股东数）
        tot = [v for r in rows for v in r[2:4] if v is not None]
    if not tot:
        return None
    na = len([r for r in rows if len(r) > 2 and r[2] is not None])
    nh = len([r for r in rows if len(r) > 3 and r[3] is not None])
    text = (f"{name} 共 **{len(rows)} 个披露期**（{rows[0][0]} ~ {rows[-1][0]}）："
            f"由 **{tot[0]:,} 户**到 **{tot[-1]:,} 户**，区间最高 {max(tot):,} 户、"
            f"最低 {min(tot):,} 户，"
            f"{'累计' + ('减少' if tot[-1] < tot[0] else '增加') + f' {abs(tot[-1] - tot[0]):,} 户'}"
            f"（{_n(abs(tot[-1] - tot[0]) / tot[0] * 100, 1)}%）。")
    text += (f"A 股拆分 {na} 期、H 股拆分 {nh} 期有披露，其余期次留空断线，不插值。"
             if (na or nh) else "本公司各期只披露股东总数、没有 A/H 拆分。")
    return text


def _narr_concentration(name, rows):
    """集中度解读：期数、前十大区间（含出现的期次）、期末第一大股东，有剔代理人口径就一并说。"""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if len(rows) < 2:
        return None
    t10 = [(r.get("date"), r.get("top10")) for r in rows if r.get("top10") is not None]
    last = rows[-1]
    bits = [f"{name} 共 **{len(rows)} 个报告期**（{rows[0].get('date')} ~ {last.get('date')}）"]
    if t10:
        lo = min(t10, key=lambda x: x[1])
        hi = max(t10, key=lambda x: x[1])
        bits.append(f"前十大股东合计占比在 **{_n(lo[1])}%**（{lo[0]}）~ **{_n(hi[1])}%**（{hi[0]}）之间")
    if last.get("top1_name"):
        bits.append(f"期末第一大股东为 **{last['top1_name']}**"
                    + (f"（{_n(float(last['top1']))}%）" if last.get("top1") is not None else ""))
    if last.get("top1_ex_name") and last.get("top1_ex_name") != last.get("top1_name"):
        bits.append(f"剔除港股代理人后为 **{last['top1_ex_name']}**"
                    + (f"（{_n(float(last['top1_ex']))}%）" if last.get("top1_ex") is not None else ""))
    return "；".join(bits) + "。"


def _narr_holders(name, holders, end_date, caliber, hn):
    """名册解读：这一期名册的口径、前十大合计、第一大股东，能配上户数就配一句。"""
    holders = holders or []
    if not holders:
        return None
    base = holders[0].get("total_shares") or None
    s10 = sum(h.get("hold_num") or 0 for h in holders)
    bits = [f"{name} **{end_date or '最新一期'}** 的{caliber}共 {len(holders)} 名"]
    if base:
        bits.append(f"合计持股 **{_n(s10 / base * 100)}%**（{_n(s10 / YI)} 亿股，分母为总股本 "
                    f"{_n(base / YI)} 亿股）")
    top = holders[0]
    if top.get("ratio") is not None:
        bits.append(f"第一大股东 **{top.get('name') or '—'}** 持 **{_n(float(top['ratio']))}%**")
    hn = [r for r in (hn or []) if r and r[1] is not None]
    if hn:
        bits.append(f"同期股东总数 {hn[-1][1]:,} 户（{hn[-1][0]} 披露）")
    return "；".join(bits) + "。"


def _company_narrative(rec, industry, code):
    """把上面几段合成一个块下发：{图/段落: {text, detail?}}，缺数据的段落直接不出现。
    页面把 text 接在该图原有的通用说明前面，detail 收进「展开详细口径」里。"""
    cap = rec.get("share_capital") or []
    cap_by_year = {str(r[0]): float(r[1]) for r in cap if r and r[1] is not None}
    annual = rec.get("annual") if isinstance(rec.get("annual"), dict) else None
    name = rec.get("name") or code
    out = {}
    t = _narr_holders(name, rec.get("holders"), rec.get("holders_end_date"),
                      rec.get("holders_caliber") or "接口口径的前十名股东名册", rec.get("holder_num"))
    if t:
        out["holders"] = {"text": t}
    t = _narr_concentration(name, rec.get("holder_concentration"))
    if t:
        out["concseries"] = {"text": t}
    t = _narr_holder_num(name, rec.get("holder_num"))
    if t:
        out["holdernum"] = {"text": t}
    t, detail = _narr_share_capital(name, cap, rec.get("share_capital_break"))
    if t:
        out["sharecap"] = {"text": t, "detail": detail}
    t = _narr_dividend(name, rec.get("dividend_per10"), rec.get("dividend_unit") or "元",
                       annual, cap_by_year)
    if t:
        out["divper10"] = {"text": t}
    return out or None


def _as_year_pairs(v):
    """分红序列统一成 [[年, 值]]：银行以外的板块，annual 表里的 dividend_per10 是「年→值」的字典，
    手工层给的却是逐年数组 —— 前端只吃数组，两种形态在这里合一（原先字典直接被当数组，
    length 为 undefined，险企/开发商/水泥三个板块的分红图静默不画）。"""
    if isinstance(v, dict):
        return [[str(y), v[y]] for y in sorted(v, key=str) if v[y] is not None] or None
    return v or None


# ── 合并后的每公司股东表 ────────────────────────────────────────────────────────
# 「新建 shareholder 表」：原先每次请求都现拼三处来源 —— <板块>_<code>_annual.json（东财接口
# 前十名快照）、company_charts_<code>.json（银行年报口径环形图/股本/分红）、holders_manual.json
# （手工层）。现在把它们按公司合并落地成一份 data/tables/<板块>_<code>_shareholder.json，另带
# 一个 sources 块逐层记下出处（tier 同前端 SRC_TIER：annual 年报 / api 第三方接口 / manual 手工层，
# 认不出的按 prompt 约定降到 api）。生成脚本 data/extract/build_shareholder_tables.py；接口有这份表
# 就直接读，没有就退回 _stitch_rec 现拼 —— 落地的正是 _stitch_rec 的结果，两条路给出的 rec 一致。
SHAREHOLDER_TABLE = "{industry}_{code}_shareholder.json"
_HOLDERS_MANUAL_BASENAME = "holders_manual.json"


def _provenance(industry, code, rec, man, annual):
    """合并表的 sources 块：逐层记下出处 {图/字段: {tier, label, from}}。
    tier 三档同前端 SRC_TIER（annual 年报 / api 第三方接口 / manual 手工层），认不出的按 prompt
    约定降到 api（待升级年报）。label 只给一句短出处（供卡片角标用；长口径另在 history_source /
    factions_source 里），from 记来源文件。只据实记录，不臆测口径。"""
    ann_file = f"{industry}_{code}_annual.json"
    charts_file = f"company_charts_{code}.json"
    ann_src = (annual or {}).get("source")
    mf = _HOLDERS_MANUAL_BASENAME
    out = {}

    def ann_tier():
        return "annual" if any(w in (ann_src or "") for w in ("年报", "年度报告", "20-F", "招股")) else "api"

    def put(sid, tier, label, frm):
        out[sid] = {"tier": tier, "label": label, "from": frm}

    if rec.get("holders"):
        put("holders", "manual", "年报/20-F 名册", mf) if man.get("holders") \
            else put("holders", "api", "东方财富接口快照", ann_file)
    if rec.get("ring"):
        if man.get("ring"):
            put("ring", "manual", "年报口径环形图", mf)
        elif industry == "bank":
            put("ring", "annual", "A 股年报持股表", charts_file)
    if rec.get("dividend_per10"):
        if man.get("dividend_per10"):
            put("divper10", "manual", "年报·分红方案", mf)
        elif industry == "bank":
            put("divper10", "annual", "A 股年报·分红", charts_file)
        else:
            t = ann_tier()
            put("divper10", t, "年报·分红" if t == "annual" else "东财接口·分红", ann_file)
    if rec.get("share_capital"):
        if man.get("share_capital"):
            put("sharecap", "manual", "年报·股份变动", mf)
        elif industry == "bank":
            put("sharecap", "annual", "A 股年报·股本", charts_file)
        else:
            t = ann_tier()
            put("sharecap", t, "年报·股本" if t == "annual" else "东财接口·股本", ann_file)
    if rec.get("holder_num"):
        if man.get("holder_num"):
            put("holdernum", "manual", "年报·股东户数", mf)
        else:
            t = ann_tier()
            put("holdernum", t, "年报·户数" if t == "annual" else "东财接口·户数", ann_file)
    if rec.get("holder_concentration"):
        if man.get("holder_concentration"):
            put("concseries", "manual", "年报·前十名", mf)
        else:
            t = ann_tier()
            put("concseries", t, "年报·集中度" if t == "annual" else "东财接口·集中度", ann_file)
    if rec.get("factions"):
        if man.get("factions"):
            put("factions", "manual", "手工·一致行动人", mf)
        elif industry == "bank":
            put("factions", "annual", "年报·一致行动人", charts_file)
        else:
            put("factions", "api", "分组（接口现拼）", ann_file)
    return out or None


def _stitch_rec(industry, code, man):
    """把三处来源现拼成一份原始 rec（原 read_holders 循环体的逻辑，独立出来供合并表复用）。
    man 是 holders_manual.json 里 "<板块>:<代码>" 那条（没有就传 {}）。返回 None 表示不进名单。"""
    d = _holder_table(industry, code)
    if d is None:
        if not man.get("holders"):
            return None          # 既无 annual 表又无手工层 holders：不进名单
        d = {}
    rec = dict(d)
    for k in ("name", "secucode", "holders_end_date", "holders", "holder_num", "source", "ring",
              # 下面三层是照 shareholder.html 那套模板补的历史序列（手工层才有）
              "holder_concentration", "share_capital", "dividend_per10",
              # 股本序列中间跨了口径断点（百度 1 拆 80）时，图上要打一条界线
              "share_capital_break"):
        if man.get(k):
            rec[k] = man[k]
    rec["factions"] = man.get("factions") or (_bank_factions(code) if industry == "bank" else None)
    # 派系表用年报简称、接口名册用全称的那几家，靠手工层的别名表接上（见 _resolve_factions）
    rec["faction_aliases"] = man.get("faction_aliases")
    rec["factions_source"] = man.get("factions_source") or (
        f"银行年报口径股东页的一致行动人表（data/tables/company_charts_{code}.json）"
        if rec["factions"] and industry == "bank" else None)
    rec["caliber_note"] = man.get("caliber_note")
    rec["residual_label"] = man.get("residual_label")
    rec["ring_alt_meta"] = man.get("ring_alt_meta")
    rec["history_source"] = man.get("history_source")
    if industry == "bank":
        # 银行的股本与分红原来画在自己的年报口径股东页里；bank 表的 dividend_per10 是「年→每 10 股」
        # 的字典，前端要逐年数组，在这里并成一份（年报口径与接口口径取并集，重叠以年报为准）
        sc, dp = _bank_history_from_charts(code, rec.get("dividend_per10"))
        rec["share_capital"] = rec.get("share_capital") or sc
        rec["dividend_per10"] = dp
        if (sc or dp) and not rec["history_source"]:
            rec["history_source"] = (
                f"历年股本与每 10 股分红取自本行年报口径数据表 "
                f"data/tables/company_charts_{code}.json（share-capital / dividend-per10 两块，"
                f"逐年取自 A 股／H 股年报，A+H 同一年份优先用 A 股口径），"
                f"分红另与 bank_{code}_annual.json 的 dividend_per10 取并集"
                f"（重叠年份以年报口径为准，接口那份只补缺年）。")
    rec["holders_caliber"] = man.get("holders_caliber")
    rec["history_gaps"] = man.get("history_gaps")
    rec["dividend_unit"] = man.get("dividend_unit")
    # 分红序列两种形态（手工层数组 / annual 表字典）在这里合一
    rec["dividend_per10"] = _as_year_pairs(rec.get("dividend_per10"))
    # 年报口径环形图（银行取 company_charts）也落进 rec，合并表就自带 ring，请求时不必再读 json
    if not rec.get("ring") and industry == "bank":
        rec["ring"] = _ring_block_from_charts(code)
    if not rec.get("ring_alt"):
        rec["ring_alt"] = _ring_alt_from_charts(code, rec.get("ring_alt_meta"))
    rec["sources"] = _provenance(industry, code, rec, man, d)
    return rec


def _load_shareholder_table(industry, code):
    """读合并表 data/tables/<板块>_<code>_shareholder.json，没有就返回 None。"""
    path = os.path.join(TABLES_DIR, SHAREHOLDER_TABLE.format(industry=industry, code=code))
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_rec(industry, code, man):
    """合并表在就读表、不在就现拼（build_shareholder_tables.py 落地的正是 _stitch_rec 的结果，
    所以两条路给出的数据一致）。"""
    return _load_shareholder_table(industry, code) or _stitch_rec(industry, code, man)


def read_holders(code=None):
    """某公司的股东快照 + 它所属板块的成员名单。**板块由代码判定**（company_codes.json 的
    industry 字段，认不出时按各板块名单反查）—— 代码与板块本来就是一对一的，所以本接口
    不再收 industry 参数，页面只传 ?code=。code 省略时给 bank 板块的默认公司。
    code 给的是另一地的代码（H 股 01398 / 美股 BIDU）时按 company_codes.json 换成同一家公司
    在本板块名单里的代码（同一法人才换，中国联通 A 股与红筹不换，只说明原因）。
    纯 H 股公司（如中国海外发展 00688）接口不返回前十名股东，名单里保留但标 has_holders=false，
    页面把它画成不可点，避免看着像取数遗漏。"""
    if not code:
        code = industry_default_code(DEFAULT_HOLDER_INDUSTRY)
    industry = _industry_of_code(code)
    if not industry:
        return error(
            f"{code} 不在任何板块的名单里（已支持 {list(HOLDER_INDUSTRIES)}）；"
            f"代码与板块的对应表见 data/tables/company_codes.json", 404)
    spec = HOLDER_INDUSTRIES[industry]
    manual = _holders_manual()
    roster, tables = [], {}
    for c in spec["codes"]:
        man = manual.get(f"{industry}:{c}") or {}
        # 合并表在就读表、不在就现拼（同一份 _stitch_rec 逻辑，两条路数据一致）
        rec = _get_rec(industry, c, man)
        if rec is None:
            continue
        tables[c] = rec
        roster.append({"code": c, "name": rec.get("name") or c,
                       "tag": rec.get("tier") or rec.get("group") or man.get("tag") or "",
                       "has_holders": bool(rec.get("holders"))})
    if not roster:
        return error(f"尚无{spec['label']}数据文件", 404)
    code_note = None
    if code not in tables:
        # A 股／H 股／美股代码指向同一家公司时换成本板块名单里的那个代码；换不了的
        # （中国联通 A 股 600050 与红筹 00762 不是同一法人）给一份指引，页面照它提示该问哪个代码
        alt, why, ent0 = _resolve_company_code(code, set(tables))
        if not alt:
            red = _cross_industry_redirect(code, ent0, set(HOLDER_INDUSTRIES))
            return error(
                f"{spec['label']} {code} 尚无年度数据文件"
                + (f"：{why}" if why else (f"：{red['msg']}" if red else "")),
                404, {"redirect": red} if red else None)
        code, code_note = alt, why
    d = tables[code]
    ent = _company_codes()[0].get(code) or {}
    return success({
        "industry": industry,
        "label": spec["label"],
        "roster": roster,
        "company": {
            "code": code,
            "name": d.get("name") or code,
            "secucode": d.get("secucode"),
            "tag": d.get("tier") or d.get("group") or next(
                (r["tag"] for r in roster if r["code"] == code), ""),
            "source": d.get("source"),
            "holders_end_date": d.get("holders_end_date"),
            "holders": d.get("holders") or [],
            "holder_num": d.get("holder_num") or None,
            "holder_concentration": d.get("holder_concentration") or None,
            # 历年总股本 [[年, 股数, 变动原因]] 与历年每 10 股分红 [[年, 元]]：
            # shareholder.html 那套模板有这两张图，其余板块的数据在手工层补齐后自然也画得出来
            "share_capital": d.get("share_capital") or None,
            "dividend_per10": d.get("dividend_per10") or None,
            # 股本序列的口径断点 {at, text}：拆股／并股前后基数不可直接比较，图上画界线
            "share_capital_break": d.get("share_capital_break") or None,
            "history_source": d.get("history_source"),
            "holders_caliber": d.get("holders_caliber") or "接口口径的前十名股东快照",
            # 逐年抽取时记下的披露缺口，页面「口径与接口限制」原样列出
            "history_gaps": d.get("history_gaps") or None,
            # 分红图的单位：中国移动的股息以港元宣派，年报不给人民币每股金额，就照港元画
            "dividend_unit": d.get("dividend_unit") or "元",
            # 一致行动人：有派系表才画双层环，没有就只有单层（内外圈同一份数据没意义）
            "factions": _resolve_factions(d.get("holders") or [], d.get("factions"),
                                          d.get("faction_aliases")),
            # 环形图的标准数据块（年报口径）与附加口径：现在都已并进合并表（_stitch_rec 落地时
            # 银行取 company_charts 生成好），请求时直接读表，不再回头读 company_charts_<code>.json
            "ring": d.get("ring"),
            # 环形图的附加口径（渝农商行的 H 股年报两张）：图上给按钮切，切过去连口径说明一起换
            "ring_alt": d.get("ring_alt"),
            "ring_label": (d.get("ring_alt_meta") or {}).get("main_label"),
            "factions_source": d.get("factions_source"),
            # 手工层公司（百度按 20-F beneficial ownership、巴比按年报名册）口径与接口快照不同，
            # 页面把这句原样印出来，不让两套口径混着读
            "caliber_note": d.get("caliber_note"),
            # 环形图里「名册外那一块」的叫法：前十名口径叫「前十名之外」，20-F 口径不是名册前十名
            "residual_label": d.get("residual_label") or "其他股东（前十名之外）",
            # 股权结构只剩 dashboard/company/shareholder.html 一页（各板块靠 ?industry= 切换、
            # 只有顶部 header 不同），银行原先那套独立的年报口径股东页已并入本页 —— 不再有外链入口
            "detail_page": None,
            # 同一家公司的三地代码：页面把两地代码印在页头，?code= 给哪个都落到这一家
            "codes": {"a": ent.get("a_code"), "h": ent.get("h_code"), "us": ent.get("us_code"),
                      "same_entity": ent.get("same_entity", True),
                      # 行业字段：页面据此换 header 与配色（跨板块的代码也按它跳转）
                      "industry": ent.get("industry"),
                      "short": ent.get("short"), "full": ent.get("full"),
                      "note": ent.get("note")} if ent else None,
            # 传进来的 code 与最终取数的 code 不是同一个时，说明为什么（两地代码互换 / 不能互换）
            "code_note": code_note,
            # 每张图下那段解读（原先写死在银行年报口径股东页里的话），逐公司从自己的序列现算
            "narrative": _company_narrative(d, industry, code),
            # 合并表逐层的出处 {图/字段: {tier, label, from}}，供页面来源标签（SRC_TIER）用；
            # 没有合并表、退回现拼时也一并给出，两条路一致
            "sources": d.get("sources") or None,
        },
    })


@holders_bp.route("/holders")
def api_holders():
    """参数: code（任意一地的公司代码，省略取银行板块默认公司）—— 板块由代码判定，不收 industry
    股权结构页共用接口：返回该公司所属板块的成员名单 + 前十名股东（银行另带股东户数与集中度）"""
    return jsonify(read_holders(request.args.get("code")))


@holders_bp.route("/nav")
def api_nav():
    """参数: code（任意一地的公司代码，可省）、industry（认不出代码时的兜底，可省）
    股权结构页的导航判定：代码 → 所属板块 → 该载哪个 header 脚本、用哪一组链接"""
    return jsonify(read_nav(request.args.get("code"), request.args.get("industry")))
