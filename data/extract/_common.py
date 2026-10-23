"""五个 fetch_*_financials.py 共用的东财接口层：常量、带重试的请求、原始响应缓存、年报期聚合。

各行业脚本只保留自己的口径差异（成员名单、字段映射、派生指标），取数管道走这里一份。
直接 `python data/extract/fetch_xxx_financials.py` 运行时，脚本所在目录就在 sys.path 上，
`from _common import ...` 即可。
data/ 下的 *.json（raw/ 缓存、tables/ 成品表）已不落盘，原文存 MySQL json_file 表，
按原文件路径经 backend/jsonstore.py 读写；这里把仓库根加进 sys.path 并导出 jsonstore 给各脚本用。
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend import jsonstore  # noqa: E402  JSON 原文在 MySQL json_file 表，按原文件路径取

RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "tables"

API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
API_HK = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept-Encoding": "identity",
}


def request_page(report_name: str, filt: str, sort_col: str = "REPORT_DATE",
                 page_size: int = 200, page: int = 1, retries: int = 3,
                 timeout: int = 60, api: str = API) -> dict:
    """请求一页，失败按 2^n 秒退避重试。"""
    url = "%s?reportName=%s&columns=ALL&filter=%s&sortColumns=%s&sortTypes=-1&pageSize=%d&pageNumber=%d" % (
        api, report_name, urllib.parse.quote(filt), sort_col, page_size, page)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if not payload.get("success", True) and payload.get("result") is None:
                raise RuntimeError(payload.get("message") or "empty result")
            return payload
        except Exception as e:                      # noqa: BLE001 - 统一重试
            last_err = e
            wait = 2 ** attempt
            print(f"    [retry {attempt}/{retries}] {e}; sleep {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"{report_name} failed after {retries} attempts: {last_err}")


def request_json(report_name: str, filt: str, sort_col: str = "REPORT_DATE",
                 page_size: int = 200, retries: int = 3, timeout: int = 60,
                 api: str = API, full: bool = False) -> dict:
    """取结果。full=True 时若 count 超出首页行数就按 pageSize=count 整包重取。

    为什么不翻页（银行脚本一直用 full=True）：排序键只有 END_DATE，同一报告期内
    多行次序不稳定，跨页边界会重复几行、漏掉几行（601077 的 RPT_F10_EH_HOLDERS
    count=315，只取首页 200 行会把 2008—2021Q1 共 11 期静默吞掉）。
    """
    payload = request_page(report_name, filt, sort_col, page_size, 1, retries, timeout, api)
    if full:
        result = payload.get("result") or {}
        count = result.get("count") or 0
        if count > len(result.get("data") or []):
            payload = request_page(report_name, filt, sort_col, count, 1, retries, timeout, api)
    return payload


def cached(report_name: str, code: str, filt: str, refresh: bool, **kw) -> dict:
    """缓存存 MySQL json_file 表，键照旧是 data/raw/em_<报表>_<代码>.json；没有 --refresh 就只读缓存、不联网。"""
    path = RAW_DIR / f"em_{report_name}_{code}.json"
    if jsonstore.exists(path) and not refresh:
        return jsonstore.read(path)
    print(f"    [http] {report_name}")
    payload = request_json(report_name, filt, **kw)
    jsonstore.write(path, payload, ensure_ascii=False)
    return payload


def annual_rows(payload: dict) -> dict[str, dict]:
    """按年份聚合年报期（REPORT_DATE 为 12-31）的行。"""
    out: dict[str, dict] = {}
    for row in (payload.get("result") or {}).get("data") or []:
        rd = (row.get("REPORT_DATE") or "")[:10]
        if not rd.endswith("-12-31"):
            continue
        out.setdefault(rd[:4], row)     # 接口按日期降序，首条为最新修订版
    return out


def pick(row: dict, mapping: dict[str, str]) -> dict:
    return {k: row.get(v) for k, v in mapping.items()}


def ssum(rec: dict, keys: tuple[str, ...]) -> float | None:
    """按 keys 求和；全为空则返回 None（区分「科目本年未披露」与「真的是 0」）。"""
    vals = [rec.get(k) for k in keys]
    got = [v for v in vals if v is not None]
    return sum(got) if got else None


def fetch_holders(code: str, filt: str, refresh: bool) -> tuple[str | None, list[dict]]:
    """前十名股东名册：取最新的年末报告期那一组，按名次排好。"""
    payload = cached("RPT_F10_EH_HOLDERS", code, filt, refresh,
                     sort_col="END_DATE", page_size=200)
    rows = (payload.get("result") or {}).get("data") or []
    year_ends = [d for d in ((r.get("END_DATE") or "")[:10] for r in rows) if d.endswith("-12-31")]
    latest = max(year_ends) if year_ends else None
    holders = [
        {
            "rank": r.get("HOLDER_RANK"),
            "name": r.get("HOLDER_NAME"),
            "hold_num": r.get("HOLD_NUM"),
            "ratio": r.get("HOLD_NUM_RATIO"),
            "change": r.get("HOLD_NUM_CHANGE"),
            "state": r.get("HOLDER_STATE_NEW") or r.get("HOLDER_STATE"),
            "shares_type": r.get("SHARES_TYPE"),
            "total_shares": r.get("TOTAL_SHARES_NUM"),
        }
        for r in rows if (r.get("END_DATE") or "")[:10] == latest
    ]
    holders.sort(key=lambda h: h["rank"] or 99)
    return latest, holders


def fetch_dividend(code: str, filt: str, refresh: bool) -> dict[str, float]:
    """逐年现金分红总额（税前，元）：只认「实施分配」的方案，同年多次分红累加。"""
    payload = cached("RPT_SHAREBONUS_DET", code, filt, refresh,
                     sort_col="PLAN_NOTICE_DATE", page_size=100)
    out: dict[str, float] = {}
    for r in (payload.get("result") or {}).get("data") or []:
        if r.get("ASSIGN_PROGRESS") != "实施分配":
            continue
        amt = r.get("PRETAX_BONUS_RMB")
        rd = (r.get("REPORT_DATE") or "")[:4]
        if amt is None or not rd:
            continue
        out[rd] = round(out.get(rd, 0.0) + amt, 4)
    return out
