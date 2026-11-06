"""股权结构页的数据层：从 MySQL 拼回 holders_manual.json 与 <板块>_<code>_annual.json 里股权要用的那几块（形状照旧）。

两份原文件进库时已按 load_to_mysql.py 拆进 shareholder / shareholder_count / shareholder_concentration /
shareholder_faction / shareholder_meta / share_capital_year_end / financials 的分红列 / data_gap / data_note，
这里按来源文件（各表的 source 列）把同一份文件的那几块挑回来，所以手工层与接口层仍各是各的：
  · 名册、集中度只取该来源那一份的行，别的手工件补进库里的期次（港股年报重构的集中度）不混进来；
  · 户数取库里该公司的全部期次，格子已按年报原文改过（载入时年报原文盖接口值）；手工层那份另按 source 挑；
  · 手工层的分红取 dividend_source 记为该文件的年份，港元宣派的（中国移动）在港股序列 hk.<H 股代码>；
    annual 那份分红是库里整条序列（年报原文盖接口值，见 industry_db.read_annual_table）。"""
from backend import db, industry_db

MANUAL = "holders_manual.json"


def _bare(company_code):
    """sh.601398 → 601398（页面与 holders_manual.json 的键用的裸代码）。"""
    return company_code.split(".", 1)[1]


def _secucode(company_code):
    market, code = company_code.split(".", 1)
    return "%s.%s" % (code, market.upper())


def _roster(company_code, source):
    """某来源文件的那一期前十名股东 → (截止日, [原字段的股东记录])；没有返回 (None, None)。"""
    rows = db.query("SELECT * FROM shareholder WHERE company_code = %s AND source = %s"
                    " ORDER BY fiscal_year DESC, holder_rank, id", (company_code, source))
    if not rows:
        return None, None
    rows = [r for r in rows if r["fiscal_year"] == rows[0]["fiscal_year"]]
    out = []
    for r in rows:
        h = {"rank": r["holder_rank"], "name": r["holder_name"], "hold_num": db.number(r["hold_num"]),
             "ratio": db.number(r["ratio"]),
             # 增减原文是文字的照原文，原文本是数值的才给 chg_shares（页面按 '不变' 判 0）
             "change": r["raw_change"] if r["raw_change"] is not None else db.number(r["chg_shares"]),
             "state": r["raw_state"], "shares_type": r["raw_shares_type"],
             "total_shares": db.number(r["total_shares"])}
        if r["pledged_shares"] is not None:
            h["pledged"] = db.number(r["pledged_shares"])
        out.append(h)
    end = rows[0]["as_of_date"]
    return (end.isoformat() if end else None), out


def _holder_num(company_code, source=None):
    """[[截止日, 合计, A股, H股]]：给了 source 只取该来源文件的期次，不给取库里该公司全部期次；格子取库里的值。
    只披露了内资股户数的期次（哈尔滨银行）三格全空，这个形状放不下，不出行。"""
    sql = "SELECT * FROM shareholder_count WHERE company_code = %s" + (" AND source = %s" if source else "")
    return [[r["as_of_date"].isoformat(), db.number(r["total_holders"]), db.number(r["a_share_holders"]),
             db.number(r["h_share_holders"])]
            for r in db.query(sql + " ORDER BY as_of_date", (company_code, source) if source else (company_code,))
            if any(r[c] is not None for c in ("total_holders", "a_share_holders", "h_share_holders"))]


def _concentration(company_code, source):
    """[{date, top1, top3, top10, top1_name[, top1_ex, top3_ex, top1_ex_name][, top1_vote]}]：
    annual 文件每期都带剔代理人三项；手工层只有名册里有代理人的期次才带，三项都空的不带；表决权只有百度有。"""
    out = []
    for r in db.query("SELECT * FROM shareholder_concentration WHERE company_code = %s AND source = %s"
                      " ORDER BY as_of_date", (company_code, source)):
        c = {"date": r["as_of_date"].isoformat(), "top1": db.number(r["top1_holder_ratio"]),
             "top3": db.number(r["top3_holders_ratio"]), "top10": db.number(r["top10_holders_ratio"]),
             "top1_name": r["top1_holder_name"]}
        ex = {"top1_ex": db.number(r["top1_holder_ratio_excluding_nominees"]),
              "top3_ex": db.number(r["top3_holders_ratio_excluding_nominees"]),
              "top1_ex_name": r["top1_holder_name_excluding_nominees"]}
        if source != MANUAL or any(v is not None for v in ex.values()):
            c.update(ex)
        if r["top1_holder_voting_ratio"] is not None:
            c["top1_vote"] = db.number(r["top1_holder_voting_ratio"])
        out.append(c)
    return out


def _dividends(company_code, source):
    """[[年, 每 10 股派息]]：该来源文件给出（或盖过接口值）的那几年，按年升序。"""
    rows = db.query("SELECT fiscal_year, dividend_per_10_shares FROM financials WHERE company_code = %s"
                    " AND dividend_source = %s AND dividend_per_10_shares IS NOT NULL ORDER BY fiscal_year",
                    (company_code, source))
    return [[str(r["fiscal_year"]), db.number(r["dividend_per_10_shares"])] for r in rows]


def share_prices(code):
    """[[年, 年末收盘价, 取价日, 币种, 行情来源]]：share_price_year_end 里该公司（裸代码）的逐年行，按年升序。"""
    rows = db.query("SELECT * FROM share_price_year_end WHERE SUBSTRING_INDEX(company_code, '.', -1) = %s"
                    " ORDER BY fiscal_year", (code,))
    return [[str(r["fiscal_year"]), db.number(r["close_price"]), r["trade_date"].isoformat(), r["currency"],
             r["source"]] for r in rows]


def exchange_rates():
    """{(年, 外币): 1 单位外币折人民币元}：exchange_rate_year_end 的年末中间价。"""
    return {(str(r["fiscal_year"]), r["currency"]): db.number(r["rmb_per_unit"])
            for r in db.query("SELECT fiscal_year, currency, rmb_per_unit FROM exchange_rate_year_end")}


def merge_bank_dividends(charts_block, annual_div):
    """银行历年每 10 股分红 [[年, 值]]：详情页载荷的 dividend-per10 块（逐年抄年报）∪ annual 表的
    dividend_per10（年→值，公司数据接口）。重叠年份以年报口径为准，接口那份只补缺年。"""
    dp = {}
    if isinstance(annual_div, dict):
        dp.update({str(y): v for y, v in annual_div.items() if v is not None})
    blk = charts_block or {}
    dp.update({str(y): v for y, v in zip(blk.get("years") or [], blk.get("per10") or []) if v is not None})
    return [[y, dp[y]] for y in sorted(dp)] or None


EXCHANGE_PRICE_SOURCES = ("上交所", "深交所", "港交所")   # share_price_year_end.source 的交易所前缀，其余是第三方行情


def dividend_yield(per10, unit, code):
    """股息率 [[年, 股息率%, 每股现金分红, 年末收盘价, 取价日, 行情来源, 股价币种, 折算汇率]]：
    当年每股现金分红（每 10 股 ÷ 10）÷ 当年末收盘价，按请求现算、不入库。股权页与银行详情页的多行对比共用这一份。
    分红与股价币种不同的（纯 H 股行人民币宣派、港元报价）先把股价按当年末人民币汇率中间价
    （exchange_rate_year_end，1 单位外币折人民币元）折成分红币种再除，折算汇率记在末列，同币种的记 None；
    那一年没有中间价就不出行。没有年末股价的年份（上市前、只有银行抓了行情）也不出行。"""
    prices = share_prices(code)
    if not (per10 and prices):
        return None
    rates = exchange_rates()

    def rmb(cur, y):          # 1 单位 cur 折人民币元；人民币本身为 1
        return 1 if cur == "元" else rates.get((y, cur))
    px = {r[0]: r for r in prices if r[1]}
    out = []
    for y, v in per10:
        if v is None or y not in px:
            continue
        p = px[y]
        if p[3] == unit:
            price, fx = p[1], None
        else:
            a, b = rmb(p[3], y), rmb(unit, y)
            if not (a and b):
                continue
            price, fx = p[1] * a / b, a / b
        out.append([y, round(v / 10 / price * 100, 4), round(v / 10, 6), p[1], p[2], p[4], p[3],
                    round(fx, 6) if fx else None])
    return out or None


def _notes(company_code, source):
    return {r["topic"]: r["note"] for r in db.query(
        "SELECT topic, note FROM data_note WHERE company_code = %s AND source_file = %s ORDER BY id",
        (company_code, source))}


def holder_table(industry, code):
    """<industry>_<code>_annual.json 里股权结构要用的那几块：年度序列（同 industry_db.read_annual_table）
    + 名册（holders / holders_end_date，该 annual 文件那一份）+ 集中度 holder_concentration（该文件那一份）
    + 户数 holder_num（库里该公司全部期次：各份年报原文手工件补的年份、纯 H 股行港股年报逐年户数都在里面）+ 银行 tier。
    没有 annual 文件（库里没有这份 financials_meta）返回 None。"""
    d = industry_db.read_annual_table(industry, code)
    if d is None:
        return None
    file = "%s_%s_annual.json" % (industry, code)
    meta = db.query("SELECT company_code FROM financials_meta WHERE source_file = %s", (file,))
    cc = meta[0]["company_code"]
    co = db.query("SELECT tier FROM company WHERE company_code = %s", (cc,))
    d["holders_end_date"], d["holders"] = _roster(cc, file)
    d["holder_num"] = _holder_num(cc)
    d["holder_concentration"] = _concentration(cc, file)
    if co and co[0]["tier"]:
        d["tier"] = co[0]["tier"]
    return d


def holders_manual():
    """holders_manual.json 同形状：{"<板块>:<代码>": {名册、户数、集中度、股本、分红、分组、口径说明…}}，只给有值的键。"""
    codes = [r["company_code"] for r in db.query(
        "SELECT company_code FROM shareholder WHERE source = %s OR holder_short IS NOT NULL"
        " UNION SELECT company_code FROM shareholder_faction WHERE source = %s"
        " UNION SELECT company_code FROM data_note WHERE source_file = %s AND company_code IS NOT NULL"
        " UNION SELECT company_code FROM data_gap WHERE source_file = %s"
        " UNION SELECT company_code FROM share_capital_year_end WHERE source = %s",
        (MANUAL, MANUAL, MANUAL, MANUAL, MANUAL))]
    out = {}
    for cc in sorted(set(codes)):
        co = db.query("SELECT * FROM company WHERE company_code = %s", (cc,))[0]
        e = {}
        end, holders = _roster(cc, MANUAL)
        notes = _notes(cc, MANUAL)
        if holders:
            # 名册整份来自手工层的公司（通信三家、百度、巴比），口径说明也是手工层的；只补分组别名的银行不带这几项
            e.update({"name": co["short_name"], "secucode": _secucode(cc), "holders_end_date": end, "holders": holders})
            meta = db.query("SELECT * FROM shareholder_meta WHERE company_code = %s", (cc,))
            for k in ("holders_caliber", "caliber_note", "source", "factions_source", "history_source"):
                if meta and meta[0][k]:
                    e[k] = meta[0][k]
        e["holder_num"] = _holder_num(cc, MANUAL)
        e["holder_concentration"] = _concentration(cc, MANUAL)
        sc = db.query("SELECT * FROM share_capital_year_end WHERE company_code = %s AND source = %s"
                      " ORDER BY fiscal_year", (cc, MANUAL))
        e["share_capital"] = [[str(r["fiscal_year"]), db.number(r["total_shares"]), r["change_summary"]] for r in sc]
        split = [r for r in sc if r["share_split_factor"] is not None]
        if split:
            after = [r["fiscal_year"] for r in sc if r["fiscal_year"] > split[-1]["fiscal_year"]]
            e["share_capital_break"] = {"at": str(after[0]) if after else None,
                                        "factor": db.number(split[-1]["share_split_factor"]),
                                        "text": notes.get("share_capital_break")}
        unit = notes.get("dividend_unit")
        if unit:
            e["dividend_unit"] = unit
            # 以外币宣派的（中国移动按港元）A 股行库里存的是人民币，外币口径在港股序列 hk.<H 股代码>
            src = "hk." + co["h_code"] if unit != "元" and co["h_code"] else cc
            e["dividend_per10"] = _dividends(src, MANUAL)
        factions = {}
        for r in db.query("SELECT * FROM shareholder_faction WHERE company_code = %s AND source = %s"
                          " ORDER BY faction_order, member_order", (cc, MANUAL)):
            f = factions.setdefault(r["faction_title"], {"title": r["faction_title"], "color": r["color"],
                                                         "basis": r["basis"], "names": []})
            f["names"].append(r["holder_name"])
        e["factions"] = list(factions.values())
        e["faction_aliases"] = {r["holder_short"]: r["holder_name"] for r in db.query(
            "SELECT holder_short, holder_name FROM shareholder WHERE company_code = %s AND holder_short IS NOT NULL"
            " ORDER BY id", (cc,))}
        e["history_gaps"] = [r["description"] for r in db.query(
            "SELECT description FROM data_gap WHERE company_code = %s AND source_file = %s ORDER BY id", (cc, MANUAL))]
        for k in ("tag", "residual_label"):
            if notes.get(k):
                e[k] = notes[k]
        ring_alt = {}
        for topic, note in notes.items():
            if topic.startswith("ring_alt_meta."):
                parts = topic.split(".", 2)
                if len(parts) == 2:
                    ring_alt[parts[1]] = note
                else:
                    ring_alt.setdefault(parts[1], {})[parts[2]] = note
        if ring_alt:
            e["ring_alt_meta"] = ring_alt
        out["%s:%s" % (co["industry"], _bare(cc))] = {k: v for k, v in e.items() if v not in (None, [], {})}
    return out
