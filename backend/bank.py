import json
import os
import re

from flask import Blueprint, jsonify, request

from backend import bank_charts_db, db
from backend.shared import (
    TABLES_DIR, read_json, _resolve_company_code, _cross_industry_redirect,
    success, error,
)

bank_bp = Blueprint("bank", __name__)


def read_bank_financials(stock_code):
    """读取银行财务数据（tab分隔txt文件）"""
    code_name = stock_code.replace('.', '_')
    FILE_MAP = {
        'sh_601288': 'abc_financials.txt',
    }
    filename = FILE_MAP.get(code_name, f'{code_name}_financials.txt')
    path = os.path.join(TABLES_DIR, filename)
    if not os.path.exists(path):
        return None
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            year, revenue, net_profit = parts[0], parts[1], parts[2]
            try:
                records.append({
                    'year': year,
                    'revenue': float(revenue) * 1e8,
                    'net_profit': float(net_profit) * 1e8
                })
            except (ValueError, TypeError):
                continue
    return records if records else None


@bank_bp.route("/bank_financials")
def api_bank_financials():
    """获取银行财务数据 - 参数: code (如 sh.601288，也接受 H 股代码 01288 这类另一地代码)"""
    stock_code = request.args.get('code', 'sh.601288')
    data = read_bank_financials(stock_code)
    if data is None:
        # 只带数字的代码（含 H 股）先按两地代码对应表换成 A 股代码，再按 sh./sz. 前缀重试
        num = re.sub(r"^[a-z]{2}\.", "", stock_code)
        alt = _resolve_company_code(num, set(BANK_ORDER))[0]
        for cand in ([f"sh.{alt}", f"sz.{alt}"] if alt else []):
            data = read_bank_financials(cand)
            if data is not None:
                break
    if data is None:
        return jsonify(error("财务数据文件不存在"))
    return jsonify(success(data))


# 渝农商行那份是手工精编件（42 个键，H 股时代的年报值、环形图配色与文案都是手工定的），不由 build() 现算，仍读文件
HAND_CHART_CODES = ("601077",)


def company_charts_doc(code, cache=None, skip=()):
    """某行详情页的整份图表载荷（同 company_charts_<code>.json 的形状）：库里拼回输入、gen_company_charts.build() 现算，
    见 backend/bank_charts_db.py（cache / skip 同 bank_charts_db.charts）；渝农商行读手工精编件。没有这家银行返回 None。"""
    if code in HAND_CHART_CODES:
        return read_json(os.path.join(TABLES_DIR, f"company_charts_{code}.json"))
    return bank_charts_db.charts(code, cache, skip)


def read_company_charts(code):
    """公司详情页全部图表数据（company_charts_doc）。
    给 H 股代码（03618 / 01398）时按 company_codes.json 换成同一家公司的 A 股代码 ——
    银行按 A 股代码取数（纯 H 股行按 H 股代码），两地代码都要能取到同一份。"""
    if not re.fullmatch(r"[0-9]{5,6}", code):
        return error(f"非法银行代码 {code}", 400)
    d = company_charts_doc(code)
    if d is None:
        alt, why, ent = _resolve_company_code(code, set(BANK_ORDER))
        alt_d = company_charts_doc(alt) if alt else None
        if alt_d is not None:
            return success(alt_d, why)
        red = _cross_industry_redirect(code, ent, {"bank"})
        return error(
            f"银行 {code} 尚无详情页图表数据"
            + (f"：{why}" if why else (f"：{red['msg']}" if red else "")),
            404, {"redirect": red} if red else None)
    return success(d)


@bank_bp.route("/company_charts")
def api_company_charts():
    """参数: code（银行 A 股 6 位代码或 H 股 5 位代码），默认渝农商行 601077"""
    return jsonify(read_company_charts(request.args.get("code", DEFAULT_BANK_CODE)))


def read_social_financing():
    """社会融资规模（TSF）宏观数据，独立于任一银行：MySQL social_financing_flow（增量）按月对齐
    social_financing_stock（存量与同比），拼成行业页社融页用的 months/stock/yoy/flow_total/分项结构。"""
    rows = db.query(
        "SELECT f.period_month, s.amount, s.year_on_year_growth, f.total, f.renminbi_loans, f.government_bonds,"
        " f.corporate_bonds, f.undiscounted_bankers_acceptances, f.trust_loans, f.entrusted_loans,"
        " f.domestic_equity_financing"
        " FROM social_financing_flow f LEFT JOIN social_financing_stock s ON s.period_month = f.period_month"
        " ORDER BY f.period_month")
    if not rows:
        return error("社融数据表为空（先跑 data/extract/load_to_mysql.py）", 404)
    cols = {"stock": "amount", "yoy": "year_on_year_growth", "flow_total": "total", "rmb_loans": "renminbi_loans",
            "gov_bonds": "government_bonds", "corp_bonds": "corporate_bonds",
            "und_ba": "undiscounted_bankers_acceptances", "trust_ln": "trust_loans", "entrust": "entrusted_loans",
            "equity": "domestic_equity_financing"}
    sf = {"months": [r["period_month"] for r in rows]}
    sf.update({k: [db.number(r[c]) for r in rows] for k, c in cols.items()})
    return success(sf)


@bank_bp.route("/social-financing")
def api_social_financing():
    return jsonify(read_social_financing())


# ── 银行清单与元信息 ─────────────────────────────────────────────────────
DEFAULT_BANK_CODE = "601077"
# 601077 排最前：它是手工精编（42 个数据键），其余由 gen_company_charts.py 批量生成
# （15~16 个键），缺的图由 charts.js 的 __stub() 贴占位说明。名单外的代码只影响排序。
# 顺序按机构类型分组：国有大行→股份行→城商行→农商行→纯 H 股。list_banks() 只用这个顺序排序，
# 前端 BankLayout.vue 的切换面板另按 tier 分列，两处顺序不必一致但代码集合要对齐。
BANK_ORDER = (
    DEFAULT_BANK_CODE,
    # 国有大行
    "601398", "601288", "601988", "601939", "601328", "601658",
    # 股份行
    "600036", "601166", "600000", "601998", "600016", "000001",
    "600015", "601818", "601916",
    # 城商行
    "601169", "601229", "600919", "002142", "601009", "601838",
    "600926", "601187", "002936", "002948", "601577", "002966",
    "601963", "601665", "601997", "600928", "001227",
    # 农商行（601077 已在最前）
    "601825", "601128", "002958", "600908", "002807", "601860",
    "002839", "601528", "603323",
    # 纯 H 股
    "01578", "01916", "06138",
)


# 上市日期：A+H 两地上市的分别给 A 股（上交所/深交所首日）与 H 股（港交所首日）；
# 仅 A 股的只有 "a"，纯 H 股（01578/01916/06138）只有 "h"。这里是唯一一份，
# 前端（BankLayout.vue / BankIntro.vue）用 /api/banks 下发的 aListDate/hListDate。
LISTING_DATES = {
    # 国有大行（均 A+H）
    "601398": {"a": "2006-10-27", "h": "2006-10-27"},
    "601288": {"a": "2010-07-15", "h": "2010-07-16"},
    "601988": {"a": "2006-07-05", "h": "2006-06-01"},
    "601939": {"a": "2007-09-25", "h": "2005-10-27"},
    "601328": {"a": "2007-05-15", "h": "2005-06-23"},
    "601658": {"a": "2019-12-10", "h": "2016-09-28"},
    # 股份行
    "600036": {"a": "2002-04-09", "h": "2006-09-22"},
    "601166": {"a": "2007-02-05"},
    "600000": {"a": "1999-11-10"},
    "601998": {"a": "2007-04-27", "h": "2007-04-27"},
    "600016": {"a": "2000-12-19", "h": "2009-11-26"},
    "000001": {"a": "1991-04-03"},
    "600015": {"a": "2003-09-12"},
    "601818": {"a": "2010-08-18", "h": "2013-12-20"},
    "601916": {"a": "2019-11-26", "h": "2016-03-30"},
    # 城商行
    "601169": {"a": "2007-09-19"},
    "601229": {"a": "2016-11-16"},
    "600919": {"a": "2016-08-02"},
    "002142": {"a": "2007-07-19"},
    "601009": {"a": "2007-07-19"},
    "601838": {"a": "2018-01-31"},
    "600926": {"a": "2016-10-27"},
    "601187": {"a": "2020-10-27"},
    "002936": {"a": "2018-09-19", "h": "2015-12-23"},
    "002948": {"a": "2019-01-16", "h": "2015-12-03"},
    "601577": {"a": "2018-09-26"},
    "002966": {"a": "2019-08-02"},
    "601963": {"a": "2021-02-05", "h": "2013-11-06"},
    "601665": {"a": "2021-06-18"},
    "601997": {"a": "2016-08-16"},
    "600928": {"a": "2019-03-01"},
    "001227": {"a": "2022-01-17"},
    # 农商行
    "601077": {"a": "2019-10-29", "h": "2010-12-16"},
    "601825": {"a": "2021-08-19"},
    "601128": {"a": "2016-09-30"},
    "002958": {"a": "2019-03-26"},
    "600908": {"a": "2016-09-23"},
    "002807": {"a": "2016-09-02"},
    "601860": {"a": "2019-01-03"},
    "002839": {"a": "2017-01-24"},
    "601528": {"a": "2021-06-25"},
    "603323": {"a": "2016-11-29"},
    # 纯 H 股（仅港交所）
    "01578": {"h": "2016-03-30"},
    "01916": {"h": "2018-06-26"},
    "06138": {"h": "2014-03-31"},
}


def list_banks():
    """可切换银行清单：MySQL company 表里有年度财务序列的银行；简称、全称、类型取 company，
    reportYear 取 financials 最近一年，上市日期取 LISTING_DATES。"""
    rows = db.query(
        "SELECT c.a_code, c.h_code, c.short_name, c.full_name, c.tier, MAX(f.fiscal_year) AS report_year"
        " FROM company c JOIN financials f ON f.company_code = c.company_code WHERE c.industry = 'bank'"
        " GROUP BY c.company_code, c.a_code, c.h_code, c.short_name, c.full_name, c.tier")
    found = {}
    for r in rows:
        code = r["a_code"] or r["h_code"]          # 页面与 company_charts 文件名用的裸代码：A 股代码，纯 H 股用 H 股代码
        ld = LISTING_DATES.get(code, {})
        found[code] = {
            "code": code,
            "name": r["short_name"] or code,
            "fullName": r["full_name"] or "",
            "reportYear": str(r["report_year"]) if r["report_year"] else "",
            "tier": r["tier"] or "",
            "aListDate": ld.get("a", ""),
            "hListDate": ld.get("h", ""),
        }
    ordered = [found.pop(c) for c in BANK_ORDER if c in found]
    return ordered + [found[c] for c in sorted(found)]


@bank_bp.route("/banks")
def api_banks():
    """导航栏银行下拉框的数据源；MySQL 里有该行年度财务序列才列出"""
    return jsonify(success(list_banks()))


def read_bank_npl_formation():
    """全部已有数据行的风控横向对比序列，一次返回，供行业页 npl-formation.html 使用。
    每家的详情页图表载荷（company_charts_doc）取三条可跨行横比的序列：
      · 不良生成率 formation —— scale-dep.formation（配 scale-dep.years，2018 起可比）
      · 净息差 nim / 净利差 nis —— nim-trend.nim / nim-trend.nis（配 nim-trend.years）
    连同 _bank 元信息按 BANK_ORDER 排序（国有→股份→城商→农商→纯 H）返回。
    各行 years 取自同一提取管线本应一致，仍逐行随数据带出，前端按并集对齐、容忍缺口。
    只要三条序列里任一条有值即纳入（个别行可能只披露息差或只倒推出不良生成）。"""
    banks = []
    seen = set()
    annual_cache = {}                 # 各行图表都要拼对标行的年度序列，整次请求共用一份

    def _has(v):
        return isinstance(v, list) and any(x is not None for x in v)

    def _push(code):
        if code in seen:
            return
        try:
            d = company_charts_doc(code, annual_cache, ("manual", "ar_manual", "detail", "social_financing"))
        except (ValueError, KeyError, TypeError, FileNotFoundError):
            d = None                  # 半截/缺层的数据不该让整页 500，这一行不进对比图
        if d is None:
            return
        sd = d.get("scale-dep") or {}
        nt = d.get("nim-trend") or {}
        fm = sd.get("formation")
        nim = nt.get("nim")
        nis = nt.get("nis")
        if not (_has(fm) or _has(nim) or _has(nis)):
            return                    # 三条全无值的行不进对比图
        b = d.get("_bank") or {}
        seen.add(code)
        banks.append({
            "code": code,
            "name": b.get("shortName") or code,
            "tier": b.get("tier") or "",
            "years": sd.get("years") or [],
            "formation": fm if isinstance(fm, list) else [],
            "nimYears": nt.get("years") or [],
            "nim": nim if isinstance(nim, list) else [],
            "nis": nis if isinstance(nis, list) else [],
        })

    for code in BANK_ORDER:
        _push(code)
    for r in db.query("SELECT source_file FROM financials_meta WHERE source_file LIKE 'bank\\_%%\\_annual.json'"
                      " ORDER BY source_file"):          # BANK_ORDER 之外、库里有年度序列的行兜底
        m = re.fullmatch(r"bank_([0-9]{5,6})_annual\.json", r["source_file"])
        if m:
            _push(m.group(1))
    if not banks:
        return error("尚无银行年度数据（先跑 data/extract/load_to_mysql.py）", 404, [])
    return success(banks)


@bank_bp.route("/bank_npl_formation")
def api_bank_npl_formation():
    """全部上市银行历年不良生成率 + 净息差/净利差，一次返回，供跨行对比页使用"""
    return jsonify(read_bank_npl_formation())
