import os
import json


# ── 统一接口响应 ──────────────────────────────────────────────────────────
# 所有 read_* 一律经这两个方法出参，形状固定为 {"code", "data"(, "msg")}，
# 路由层只管 jsonify(read_x())。
def success(data, msg=None):
    """成功响应：{"code": 200, "data": ...}；个别接口带一句说明才加 msg。"""
    resp = {"code": 200, "data": data}
    if msg is not None:
        resp["msg"] = msg
    return resp


def error(msg, code=500, data=None):
    """错误响应：{"code": code, "msg": ..., "data": ...}。
    data 默认空 dict；要保留 typed 空壳（油价产量的空 xAxis）或空 list 时显式传。"""
    return {"code": code, "msg": msg, "data": {} if data is None else data}


# ── 通用路径常量 ──────────────────────────────────────────────────────────
# 基准目录取自本文件的绝对位置，与进程启动时的工作目录（CWD）无关 —— gunicorn/systemd/
# docker 等不在仓库根启动的场景也能定位到数据；需换数据根目录时设环境变量 MONEY_DATA_DIR。
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.abspath(os.environ.get("MONEY_DATA_DIR") or os.path.join(_BASE_DIR, "data"))
TABLES_DIR = os.path.join(DATA_DIR, "tables")

# 两种用法都在这里：① 只补 factions（telecom 这类 annual 表已有接口股东快照的板块）；
# ② 连 holders 一起给（tech/food 这类没有 annual 表的公司，股东块直接抄年报／20-F 原文）。
HOLDERS_MANUAL_FILE = os.path.join(TABLES_DIR, "holders_manual.json")

# 代码 ↔ 公司的对应表：一家公司在 A 股 / 港交所 / 美股各有一个代码，页面与外链给哪个都要能落到
# 同一家公司上（?code=601398 与 ?code=01398 都是工商银行）。表由 data/extract/build_company_codes.py
# 生成，每条都带本地出处，不靠常识补代码。
COMPANY_CODES_FILE = os.path.join(TABLES_DIR, "company_codes.json")


def _holders_manual():
    if not os.path.exists(HOLDERS_MANUAL_FILE):
        return {}
    with open(HOLDERS_MANUAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _company_codes():
    """返回 (entities, index)：entities 按实体唯一键索引，index 是「任意代码 → 实体」的反查表。
    same_entity=false 的两地主体（中国联通 A 股 600050 与红筹 00762 不是同一法人）照样进 index，
    但标着 same_entity=false —— 解析时按这个标记拒绝互换，只把原因说清楚，不静默换成另一家。"""
    if not os.path.exists(COMPANY_CODES_FILE):
        return {}, {}
    with open(COMPANY_CODES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    entities = {e["key"]: e for e in raw.get("entities") or []}
    index = {}
    for e in entities.values():
        for c in (e.get("a_code"), e.get("h_code"), e.get("us_code")):
            if c:
                index.setdefault(c, []).append(e)
    return entities, index


def _company_entity(code):
    """任意一地的代码 → 对应实体（找不到给 None）。撞号在生成时就断言过，这里只会有一条。"""
    es = _company_codes()[1].get(code) or []
    return es[0] if es else None


def _resolve_company_code(code, known):
    """把任意一地的代码解析成 known（某个板块已有数据的代码集合）里的那个代码。
    返回 (代码 or None, 说明, 实体)：
      · 本来就在 known 里 → (code, None, 实体)
      · 同一法人的另一地代码 → (换后的代码, 「H 股 01398 即 A 股 601398」, 实体)
      · 两地不是同一法人（中国联通 A 股 600050 vs 红筹 00762）→ (None, 原因, 实体)
      · 这家公司不在 known 里（属别的板块）→ (None, None, 实体) —— 由调用方决定是报错还是给跳转
      · 表里根本没这个代码 → (None, None, None)"""
    e = _company_entity(code)
    if e is None:
        return None, None, None
    if code in known:
        return code, None, e
    if e["key"] not in known:
        return None, None, e
    if not e.get("same_entity", True):
        return None, (f"{code} 与 {e['key']}（{e.get('short') or ''}）不是同一法人，"
                      f"不做代码互换：{e.get('note') or ''}"), e
    return e["key"], (f"{code} 与 {e['key']} 是同一家公司（{e.get('short') or ''}）的两地代码，"
                      f"已按 {e['key']} 取数"), e


def _cross_industry_redirect(code, e, want=None):
    """代码认得出、但不属于当前板块时给一份跳转指引（板块 + 该板块里的代码 + 公司名）。
    want 为调用方支持的板块集合，不在其中的（本接口不服务的板块）不给跳转、只给说明。"""
    if not e:
        return None
    msg = (f"{code} 是{e.get('short') or e['key']}的代码，属 {e.get('industry')} 板块"
           f"（该板块里的代码是 {e['key']}）")
    if want is not None and e.get("industry") not in want:
        return {"industry": None, "code": e["key"],
                "name": e.get("short") or e.get("full") or e["key"],
                "msg": msg + "，本接口不服务该板块"}
    return {"industry": e.get("industry"), "code": e["key"],
            "name": e.get("short") or e.get("full") or e["key"], "msg": msg}
