import os
import re
import json

from flask import Blueprint, Response, jsonify, request

from backend import jsonstore
from backend.shared import (
    TABLES_DIR, read_json, _resolve_company_code, _cross_industry_redirect, _company_entity,
    success, error,
)
from backend.cement_ops import CEMENT_PEERS, _merge_cement_ops
from backend.telecom_ops import TELECOM_PEERS, _merge_telecom

industry_bp = Blueprint("industry", __name__)

# 六家上市险企，数据由 data/extract/fetch_insurer_financials.py 生成：前五家为 A+H 上市、取 A 股年报口径，
# 中国太平（00966）仅在港交所上市，走港股 F10（金额已按年末汇率折人民币）
INSURER_PEERS = ["601318", "601628", "601601", "601336", "601319", "00966"]

# 六家头部央企开发商，数据由 data/extract/fetch_developer_financials.py 生成：
# 前三家 A 股上市（取 A 股年报口径），后三家仅在港交所上市，走港股 F10；
# 港股 F10 金额是年报本位币原值不折算，中海（00688）为港元口径，页面需单独标注
DEVELOPER_PEERS = ["600048", "001979", "000069", "00688", "01109", "00817"]


# ── 行业年度数据接口：保险/地产/水泥/通信共用一套读表逻辑 ─────────────────────
# 四个行业的成品表都是 data/tables/<行业>_<code>_annual.json，读法只差四件事：
# 成员清单、代码位数、同业对比要下发哪些字段（顺序即 JSON 里的字段顺序）、
# 有没有经营口径手工层要合并。差异写在下面的 INDUSTRIES 里，逻辑只有一份。
INDUSTRIES = {
    "insurer": {
        "label": "保险公司", "peers_label": "险企", "peers": INSURER_PEERS, "default": "601318",
        "code_re": r"[0-9]{5,6}", "script": "fetch_insurer_financials.py", "merge": None,
        "fields": ["name", "source", "unit_note", "caliber_note", "annual"],
    },
    "developer": {
        "label": "开发商", "peers_label": "开发商", "peers": DEVELOPER_PEERS, "default": "600048",
        "code_re": r"[0-9]{5,6}", "script": "fetch_developer_financials.py", "merge": None,
        "fields": ["name", "secucode", "group", "currency", "source", "unit_note",
                   "caliber_note", "annual", "dividend_per10"],
    },
    "cement": {
        "label": "水泥企业", "peers_label": "水泥企业", "peers": CEMENT_PEERS, "default": "600585",
        "code_re": r"[0-9]{5,6}", "script": "fetch_cement_financials.py",
        "merge": _merge_cement_ops,
        "fields": ["name", "secucode", "group", "currency", "source", "unit_note",
                   "caliber_note", "ops_meta", "annual", "dividend_per10"],
    },
    "telecom": {
        "label": "运营商", "peers_label": "运营商", "peers": TELECOM_PEERS, "default": "600941",
        "code_re": r"[0-9]{6}", "script": "fetch_telecom_financials.py",
        "merge": _merge_telecom,
        "fields": ["name", "secucode", "group", "h_code", "h_same_entity", "a_report_from",
                   "currency", "source", "unit_note", "caliber_note", "ops_meta", "segments",
                   "annual", "dividend_per10"],
    },
}

# 这两个字段缺失时给空 dict（前端直接 for-in 遍历），其余缺失给 None
_PEERS_DICT_FIELDS = ("annual", "dividend_per10")


def _read_industry_table(industry, code):
    """读 data/tables/<industry>_<code>_annual.json 并按行业规则合并手工层；文件不存在返回 None。"""
    spec = INDUSTRIES[industry]
    path = os.path.join(TABLES_DIR, f"{industry}_{code}_annual.json")
    d = read_json(path)
    if d is None:
        return None
    return spec["merge"](code, d) if spec["merge"] else d


def read_industry_annual(industry, code):
    """单家公司历年数据（含该行业的经营口径手工层，如果有）。
    code 给的是另一地的代码（海螺水泥 H 股 00914 / 中国平安 H 股 02318）时，按 company_codes.json
    换成本行业名单里的那个代码并在 code_note 里说明；认得出但属别的行业的给 data.redirect
    （行业 + 该行业里的代码），页面照它跳到对应行业的页面，不是死在一个 404 上。"""
    spec = INDUSTRIES[industry]
    code_note = None
    if not re.fullmatch(spec["code_re"], code):
        # 代码形状不合本行业规则（中国移动 H 股 00941 是 5 位、运营商只收 6 位 A 股代码）时，
        # 先看它是不是本行业某家公司的另一地代码 —— 是就换过来，不是才算非法
        alt, why, _ = _resolve_company_code(code, set(spec["peers"]))
        if not alt or not re.fullmatch(spec["code_re"], alt):
            return error(f"非法{spec['label']}代码 {code}", 400)
        code, code_note = alt, why
    d = _read_industry_table(industry, code)
    if d is None:
        alt, why, ent = _resolve_company_code(code, set(spec["peers"]))
        if alt:
            code, code_note, d = alt, why, _read_industry_table(industry, alt)
        if d is None:
            red = _cross_industry_redirect(code, ent, set(INDUSTRIES))
            return error(
                f"{spec['label']} {code} 尚无年度数据文件"
                + (f"：{why}" if why else (f"：{red['msg']}" if red else "")),
                404, {"redirect": red} if red else None)
    ent = _company_entity(code) or {}
    out = dict(d)
    out["codes"] = {"a": ent.get("a_code"), "h": ent.get("h_code"), "us": ent.get("us_code"),
                    "same_entity": ent.get("same_entity", True),
                    "industry": ent.get("industry"), "short": ent.get("short"),
                    "full": ent.get("full"), "note": ent.get("note")} if ent else None
    out["code_note"] = code_note
    return success(out)


def read_industry_peers(industry):
    """同业对比用：code → 只带 spec['fields'] 声明的字段；缺数据文件的公司跳过。"""
    spec = INDUSTRIES[industry]
    peers = {}
    for code in spec["peers"]:
        d = _read_industry_table(industry, code)
        if d is None:
            continue
        peers[code] = {k: d.get(k, {} if k in _PEERS_DICT_FIELDS else None) for k in spec["fields"]}
    if not peers:
        return error(
            f"尚无{spec['peers_label']}年度数据文件，请先运行 data/extract/{spec['script']}",
            404)
    return success(peers)


# ── 路由：每个行业两条（单家 annual / 同业 peers），按 INDUSTRIES 循环注册 ──────
# 加一个行业只需在上面的 INDUSTRIES 里加一条（含 default 默认代码），不必再手写路由；
# 端点名沿用 api_<industry>_annual / api_<industry>_peers，URL 与默认代码都不变。
def _make_annual_view(industry, default):
    def view():
        return jsonify(read_industry_annual(industry, request.args.get("code", default)))
    view.__doc__ = f"参数: code（{INDUSTRIES[industry]['label']}代码），默认 {default}"
    return view


def _make_peers_view(industry):
    def view():
        return jsonify(read_industry_peers(industry))
    view.__doc__ = f"{INDUSTRIES[industry]['peers_label']}同业对比数据，一次返回"
    return view


for _ind, _spec in INDUSTRIES.items():
    industry_bp.add_url_rule(f"/{_ind}_annual", endpoint=f"api_{_ind}_annual",
                             view_func=_make_annual_view(_ind, _spec["default"]))
    industry_bp.add_url_rule(f"/{_ind}_peers", endpoint=f"api_{_ind}_peers",
                             view_func=_make_peers_view(_ind))


@industry_bp.route("/tables/<name>")
def api_table(name):
    """成品表原文（中国移动页原先直接 fetch('/data/tables/telecom_00941_*.json')，JSON 进库后改走这里）。
    按原文下发、不套 {code, data}，键序与原文件一致；只开放 tables/ 下的 *.json。"""
    text = jsonstore.read_text(os.path.join(TABLES_DIR, name)) \
        if re.fullmatch(r"[A-Za-z0-9_.\-]+\.json", name) else None
    if text is None:
        return jsonify(error(f"数据表 {name} 不存在", 404)), 404
    return Response(text, mimetype="application/json")
