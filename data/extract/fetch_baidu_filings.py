#!/usr/bin/env python3
"""百度（09888.HK / BIDU）法定披露抓取 —— 港交所年报 + SEC 20-F + XBRL companyfacts。

信息源优先级（company-report-source-priority）：百度无 A 股，港交所 HKEXnews 是
中文法定披露首选；美股为原上市地，20-F 覆盖 FY2005 起的全部历史，港股年报只有
FY2020 起，所以两边都取，长序列以 20-F / XBRL 为准，中文口径与股权结构以港股年报为准。

产物（PDF/htm/txt 落 data/raw/，只把汇总打到 stdout）：
    annual_09888_<年>.pdf / .txt        港交所中文年度報告（pdftotext -layout）
    20f_09888_<财年>.htm / .txt          SEC 20-F 正文（HTML 去标签）
    sec_companyfacts_09888.json          SEC XBRL 全量事实（结构化长序列，经 backend/jsonstore.py 读写）

用法：
    ./venv/bin/python data/extract/fetch_baidu_filings.py              # 全量（已存在则跳过）
    ./venv/bin/python data/extract/fetch_baidu_filings.py --only hkex  # 只跑港交所
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdf_to_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend import jsonstore  # noqa: E402  JSON 文件读写统一走 jsonstore

RAW = ROOT / "data" / "raw"
CODE = "09888"
HKEX_STOCK_ID = "1000086901"       # activestock_sehk_e.json 里 BIDU-SW 的内部 id
SEC_CIK = "0001329099"

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")
# SEC 要求 User-Agent 带「名称 + 邮箱」，否则 403；www.sec.gov/Archives 偶发 403，
# 靠 http() 的重试兜过去，不要额外写 Host 头（覆盖 Host 会被边缘节点判为异常请求）
SEC_UA = "industry-research zhu@example.com"
SEC_HDR = {"User-Agent": SEC_UA, "Accept": "text/html,application/xhtml+xml,application/json"}


def http(url: str, headers: dict | None = None, retries: int = 3, timeout: int = 120) -> bytes:
    h = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}
    h.update(headers or {})
    last = None
    for i in range(retries):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout).read()
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            return body
        except Exception as e:                                    # noqa: BLE001
            last = e
            time.sleep(2 + 3 * i)
    raise RuntimeError(f"{url} -> {last}")


# ── 港交所年报 ────────────────────────────────────────────────────────────────
def list_hkex(lang: str = "zh") -> dict[int, str]:
    """{财年: PDF 绝对 URL}，标题形如「2025 年度報告」/「ANNUAL REPORT 2025」。"""
    url = ("https://www1.hkexnews.hk/search/titleSearchServlet.do"
           f"?sortDir=0&sortByOptions=DateTime&category=0&market=SEHK&lang={lang}"
           f"&stockId={HKEX_STOCK_ID}&documentType=-1&fromDate=20200101&toDate=20301231"
           "&title=&searchType=1&t1code=40000&t2Gcode=-2&t2code=40100&rowRange=100")
    d = json.loads(http(url, {"Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh"}))
    rows = json.loads(d["result"]) if isinstance(d.get("result"), str) else (d.get("result") or [])
    out: dict[int, str] = {}
    for r in rows:
        m = re.search(r"(19|20)\d{2}", r.get("TITLE", ""))
        if not m or not r.get("FILE_LINK"):
            continue
        out.setdefault(int(m.group(0)), "https://www1.hkexnews.hk" + r["FILE_LINK"])
    return out


def run_hkex() -> None:
    urls = list_hkex("zh")
    print(f"[hkex] 命中年度報告 {len(urls)} 份: {sorted(urls)}")
    for year in sorted(urls):
        pdf = RAW / f"annual_{CODE}_{year}.pdf"
        txt = pdf.with_suffix(".txt")
        if txt.exists():
            print(f"  {year} 已有 txt，跳过")
            continue
        if not pdf.exists():
            body = http(urls[year], {"Referer": "https://www1.hkexnews.hk/"})
            if body[:4] != b"%PDF":
                print(f"  {year} 下载物不是 PDF（{len(body)}B），跳过", file=sys.stderr)
                continue
            pdf.write_bytes(body)
        try:
            pdf_to_text.convert(pdf)
            print(f"  {year} OK {pdf.stat().st_size // 1024}KB -> {txt.stat().st_size // 1024}KB txt")
        except Exception as e:                                    # noqa: BLE001
            print(f"  {year} 转文本失败: {e}", file=sys.stderr)


# ── SEC 20-F ─────────────────────────────────────────────────────────────────
class Strip(HTMLParser):
    """去标签取正文；<td> 之间补两个空格，保住表格列的可读性。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.buf: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("td", "th"):
            self.buf.append("  ")
        elif tag in ("tr", "p", "div", "br", "table"):
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in ("tr", "p", "div", "table"):
            self.buf.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def text(self) -> str:
        t = "".join(self.buf)
        t = re.sub(r"[ \t\u00a0]+", " ", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def list_20f() -> list[tuple[int, str]]:
    """[(财年, 正文 htm URL)]；财年 = 提交年 - 1。"""
    d = json.loads(http(f"https://data.sec.gov/submissions/CIK{SEC_CIK}.json", SEC_HDR))
    r = d["filings"]["recent"]
    out = []
    for i, form in enumerate(r["form"]):
        if form != "20-F":
            continue
        acc = r["accessionNumber"][i].replace("-", "")
        doc = r["primaryDocument"][i]
        fy = int(r["filingDate"][i][:4]) - 1
        out.append((fy, f"https://www.sec.gov/Archives/edgar/data/{int(SEC_CIK)}/{acc}/{doc}"))
    return sorted(out)


def run_sec() -> None:
    facts = RAW / f"sec_companyfacts_{CODE}.json"
    text = jsonstore.read_text(facts)
    if text is None:
        text = http(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{SEC_CIK}.json", SEC_HDR).decode("utf-8")
        jsonstore.write_text(facts, text)
    print(f"[sec] companyfacts {len(text.encode('utf-8')) // 1024}KB")

    items = list_20f()
    print(f"[sec] 20-F {len(items)} 份: FY{items[0][0]}–FY{items[-1][0]}")
    for fy, url in items:
        htm = RAW / f"20f_{CODE}_{fy}.htm"
        txt = htm.with_suffix(".txt")
        if txt.exists():
            print(f"  FY{fy} 已有 txt，跳过")
            continue
        if not htm.exists():
            htm.write_bytes(http(url, SEC_HDR, retries=5))
            time.sleep(0.4)                                        # SEC 限速 10 req/s，宽松点
        p = Strip()
        p.feed(htm.read_text("utf-8", errors="ignore"))
        body = p.text()
        if len(body) < 200_000:
            print(f"  FY{fy} 正文仅 {len(body)}B，疑似只抓到封面/索引", file=sys.stderr)
        txt.write_text(body, "utf-8")
        print(f"  FY{fy} OK {htm.stat().st_size // 1024}KB -> {len(body) // 1024}KB txt")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", choices=["hkex", "sec"], help="只跑一个源")
    a = ap.parse_args()
    if a.only in (None, "hkex"):
        run_hkex()
    if a.only in (None, "sec"):
        run_sec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
