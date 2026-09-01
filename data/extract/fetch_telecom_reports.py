"""下载三大运营商的 A 股年报 PDF（上交所原文）并转 txt。

按项目信息源优先级：**上交所优先**。static.sse.com.cn 的阿里云 WAF（acw_sc__v2）
挑战用纯 Python 求解，不需要浏览器（解法见 reference_sse_waf_bypass）：
    1. unsbox(arg1)：按固定位置表重排挑战页里的 40 位 hex
    2. hexXor(重排结果, "3000176000856006061501533003690027800375")
    3. 带 Cookie: acw_sc__v2=<结果> 重新请求同一 URL，即返回真 PDF

公告列表：query.sse.com.cn/security/stock/queryCompanyBulletin.do
（referer 必须是 http://www.sse.com.cn/，响应是 jsonpCallback(...) 包裹）

落盘命名与 data/raw/ 现有一致：annual_<A股代码>_<year>.pdf / .txt
年份取标题里的「YYYY年年度报告」，摘要（年报摘要）跳过。

用法：
    python data/extract/fetch_telecom_reports.py                      # 三家全部可得年份
    python data/extract/fetch_telecom_reports.py 600941 --years 2021-2025
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdf_to_text  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

CODES = ["600941", "601728", "600050"]

LIST_URL = (
    "http://query.sse.com.cn/security/stock/queryCompanyBulletin.do"
    "?jsonCallBack=jsonpCallback1&isPagination=true&productId={code}"
    "&securityType=0101%2C120100%2C020100%2C020200%2C120200"
    "&beginDate={begin}&endDate={end}"
    "&pageHelp.pageSize=100&pageHelp.pageNo={page}&pageHelp.beginPage={page}"
    "&pageHelp.cacheSize=1&pageHelp.endPage={page}"
)

# 年报标题的三种写法都要认：
#   「中国移动：2025年年度报告」「…2020年度报告全文」「中国联通2015年度报告（印刷版）」
# 必须排除同样含「年度报告」四字的伴生公告：摘要、独立董事关于年度报告的独立意见、
# 审计报告、内部控制评价报告、半年度/季度报告。
# **不能**加 reportType=YEARLY 过滤：中国移动 2023 年年度报告在上交所被归到
# BULLETIN_TYPE=「其它」，带过滤就查不到。
TITLE_RE = re.compile(r"(\d{4})\s*年年?度报告(?:全文)?(?:（印刷版）)?\s*$")
TITLE_SKIP = ("摘要", "半年", "季度", "更正", "补充", "意见", "审计", "内部控制",
              "英文", "社会责任", "可持续")

# WAF 挑战里的固定位置表与 key（硬编码在混淆 JS 常量里）
UNSBOX_POS = [15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27, 22, 23, 25, 13, 6, 11,
              39, 18, 20, 8, 14, 21, 32, 26, 2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36]
XOR_KEY = "3000176000856006061501533003690027800375"


def http(url: str, referer: str = "", cookie: str = "", retries: int = 3,
         timeout: int = 120) -> bytes:
    """GET 原始字节。static.sse.com.cn 的 WAF 挑战页**即使请求 identity 也回 gzip**，
    所以这里一律声明支持 gzip 并按响应头解压（不解压会导致挑战页里的 arg1 抠不出来）。"""
    headers = {"User-Agent": UA, "Accept-Encoding": "gzip, identity"}
    if referer:
        headers["Referer"] = referer
    if cookie:
        headers["Cookie"] = cookie
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
            return body
        except Exception as e:      # noqa: BLE001
            last = e
            wait = 2 ** attempt
            print(f"      [retry {attempt}/{retries}] {e}; sleep {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"http failed after {retries}: {last}")


def solve_acw(arg1: str) -> str:
    """acw_sc__v2 = hexXor(unsbox(arg1), KEY)"""
    box = [""] * 40
    for i, pos in enumerate(UNSBOX_POS):
        box[i] = arg1[pos - 1]
    reordered = "".join(box)
    out = []
    for i in range(0, len(reordered), 2):
        v = int(reordered[i:i + 2], 16) ^ int(XOR_KEY[i:i + 2], 16)
        out.append(f"{v:02x}")
    return "".join(out)


def download_pdf(url: str) -> bytes:
    """先直连，遇 WAF 挑战页则求解 acw_sc__v2 后重试。"""
    body = http(url, referer="http://www.sse.com.cn/")
    if body[:1024].lstrip().startswith(b"%PDF"):
        return body
    m = re.search(rb"var arg1\s*=\s*'([0-9A-Fa-f]{40})'", body)
    if not m:
        raise RuntimeError(f"非 PDF 且未找到 WAF 挑战（{len(body)} 字节）")
    cookie = "acw_sc__v2=" + solve_acw(m.group(1).decode())
    print(f"      [waf] 已求解 acw_sc__v2，重试")
    body = http(url, referer="http://www.sse.com.cn/", cookie=cookie)
    if not body[:1024].lstrip().startswith(b"%PDF"):
        raise RuntimeError("WAF 求解后仍非 PDF")
    return body


def list_annual_reports(code: str) -> dict[int, str]:
    """返回 {报告年份: PDF 绝对 URL}，只要正文年报、不要摘要与伴生公告。
    列表接口单页最多 100 条且不能按年报过滤（见 TITLE_RE 注释），三家运营商公告密集，
    故**按公告年逐年 + 逐页**翻到底（联通 2022 年报就落在某年的第 2 页）。"""
    out: dict[int, str] = {}
    for pub_year in range(2000, 2027):
        for page in range(1, 8):
            url = LIST_URL.format(code=code, begin=f"{pub_year}-01-01",
                                  end=f"{pub_year}-12-31", page=page)
            raw = http(url, referer="http://www.sse.com.cn/").decode("utf-8", "replace")
            payload = json.loads(raw[raw.index("(") + 1: raw.rindex(")")])
            rows = payload.get("pageHelp", {}).get("data", []) or []
            for row in rows:
                title = (row.get("TITLE") or "").strip()
                if any(w in title for w in TITLE_SKIP):
                    continue
                m = TITLE_RE.search(title)
                if not m:
                    continue
                u = row.get("URL") or ""
                if not u.endswith(".pdf"):
                    continue
                # 同一年可能有多版（印刷版、全文），列表按日期降序，保留首个（最新）
                out.setdefault(int(m.group(1)), "https://static.sse.com.cn" + u)
            time.sleep(0.3)
            if len(rows) < 100:
                break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="A 股代码，默认三大运营商")
    ap.add_argument("--years", default="", help="如 2021-2025，默认全部可得年份")
    args = ap.parse_args()

    years = None
    if args.years:
        a, _, b = args.years.partition("-")
        years = set(range(int(a), int(b or a) + 1))

    RAW.mkdir(parents=True, exist_ok=True)
    fails: list[str] = []
    for code in (args.codes or CODES):
        print(f"[list] {code}")
        try:
            reports = list_annual_reports(code)
        except Exception as e:      # noqa: BLE001
            print(f"  [error] 列表失败：{e}", file=sys.stderr)
            fails.append(f"{code} list")
            continue
        got = sorted(y for y in reports if years is None or y in years)
        print(f"  可得年报年份：{got}")
        for year in got:
            pdf = RAW / f"annual_{code}_{year}.pdf"
            txt = pdf.with_suffix(".txt")
            if txt.exists():
                print(f"  [skip] {txt.name} 已存在")
                continue
            try:
                if not pdf.exists():
                    print(f"  [get] {year} {reports[year]}")
                    pdf.write_bytes(download_pdf(reports[year]))
                out = pdf_to_text.convert(pdf)
                print(f"  [ok] {out.name}")
            except Exception as e:  # noqa: BLE001
                print(f"  [error] {code} {year}: {e}", file=sys.stderr)
                fails.append(f"{code} {year}")
    if fails:
        print(f"[done] 失败 {len(fails)} 项：{fails}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
