"""可复用的银行年报 PDF 下载器：按源优先级抓年报 PDF 到 data/raw/，再转 .txt。

下载后立即用 data/extract/pdf_to_text.py 的 convert() 生成同名 .txt（含「抽取健康度」
三道守卫：数字密度 / 合格页占比 / 每页字符数，任一不过不写 .txt）。

命名规则（与 data/raw/ 现有一致）：
    A 股银行     -> annual_<A股代码>_<year>.pdf/.txt   （如 annual_601169_2024.pdf）
    纯 H 股银行  -> annual_<H股代码>_<year>.pdf/.txt   （如 annual_01578_2020.pdf、annual_03618_2015.pdf）
其中 A 股代码 6 位（60xxxx/00xxxx/002xxx…），H 股代码 5 位补零（01916/03618…）。

下载源优先级（用户要求，按此顺序尝试，失败自动降级）：
    1. 港交所 HKEXnews  —— 仅用于「纯 H 股」银行（有 H 代码、无 A 股年报）。
       dual-listed 银行按项目规则「A/H 都有时优先取 A 股年报」，其数据以 A 股年报为准，
       因此**不**从港交所取（H 股 PDF 会与 A 股口径混用），改走 SSE/cninfo 拿 A 股年报。
    2. 上交所 SSE       —— SH 代码（60xxxx/6xxxxx）。列表可查，但静态 PDF 主机
       static.sse.com.cn 有阿里云 WAF 的 JS-cookie 挑战（acw_sc__v2），
       urllib/requests 拿不到会返回 7KB 的 HTML 挑战页，故下载多半失败、自动降级到 cninfo。
    3. 公司官网         —— 未做通用实现（各行 IR 页结构不一），留作人工兜底。
    4. 其他：巨潮资讯 cninfo（SH+SZ 全覆盖，静态主机 static.cninfo.com.cn 无 WAF，最稳）
       + 东方财富 dfcfw 兜底。

关键坑（实测 2026-08-20）：
    · HKEXnews prefix.do 解析器（code -> stockId）当前返回空，故用硬编码 stockId 表；
      titleSearchServlet.do 需 searchType=1 + 日期区间 + t*code=-2，年报标题为「YYYY ANNUAL REPORT」。
    · SSE 用 queryCompanyBulletin.do（不是用户给的 ...New.do，后者返回空），
      但下载被 WAF 挡，实际落地靠 cninfo。
    · BULLETIN_YEAR 是公告年（报告年+1），报告年份要从标题「YYYY年年度报告」解析。

用法：
    # 下载单行某年份区间（能下多少下多少）
    python data/extract/fetch_annual_reports.py 601398 --years 2018-2025
    # 多行
    python data/extract/fetch_annual_reports.py 601398 601988 601939 --years 2018-2025
    # 指定单一源（调试）：--source cninfo|sse|hkexnews|dfcfw
    python data/extract/fetch_annual_reports.py 000001 --years 2020-2024 --source cninfo
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdf_to_text  # noqa: E402  复用体检 + 落盘逻辑

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 纯 H 股发行人：HKEXnews 内部 stockId（prefix.do 解析器当前失效，硬编码）。
# 用 H 代码命名文件。dual-listed 银行不在此表——它们走 A 股源。
HKEX_STOCK_ID = {
    "03618": "56657",   # 重庆农村商业银行（渝农商行，另有 A 股 601077，此处仅示例/回归）
    "01916": "188671",  # 江西银行  —— HKEXnews stockId
    "01578": None,      # 天津银行  —— stockId 待补
    "06138": "104210",  # 哈尔滨银行 —— prefix.do 查得，2026-08-21 实测可列出 2013 年起全部年报
    "03698": "96181",   # 徽商银行 —— partial.do 查得，2026-11-10
    "00966": "2282",    # 中国太平（保险，纯 H 股）—— 2026-08-21 实测可列出 2007 年起全部年报
}

# dual-listed / 纯 A 股银行的交易所后缀（用于选 SSE 还是仅 cninfo）
# SH -> 可试 SSE；SZ -> 直接 cninfo


def is_hk_code(code: str) -> bool:
    """5 位（含前导 0）视为港股代码，如 01916/03618；6 位为 A 股。"""
    return len(code) == 5


def exchange_of(code: str) -> str:
    """A 股代码判交易所：6/9 开头为 SH，0 开头为 SZ。"""
    if code.startswith(("60", "68", "9")):
        return "SH"
    if code.startswith(("00", "30", "20")):
        return "SZ"
    return "SH"


# ── HTTP ────────────────────────────────────────────────────────────────────

def http(url: str, referer: str = "", retries: int = 3, timeout: int = 90,
         data: bytes | None = None, extra: dict | None = None) -> bytes:
    """GET/POST 原始字节，自动解 gzip，带 UA/Referer/重试。失败 raise。"""
    headers = {"User-Agent": UA, "Accept-Encoding": "gzip, identity"}
    if referer:
        headers["Referer"] = referer
    if extra:
        headers.update(extra)
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers,
                                         method="POST" if data else "GET")
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


def looks_like_pdf(body: bytes) -> bool:
    """真 PDF 以 %PDF 开头；WAF 挑战页是 HTML（<html/<script），据此判伪。"""
    head = body[:1024].lstrip()
    return head.startswith(b"%PDF")


# ── 各源：返回 {year(int): pdf_url} ───────────────────────────────────────────

def list_cninfo(code: str) -> dict[int, str]:
    """巨潮资讯：先查 orgId，再拉年报列表，返回 {报告年份: 完整 PDF URL}。SH+SZ 通用。"""
    ref = "http://www.cninfo.com.cn/"
    top = http("http://www.cninfo.com.cn/new/information/topSearch/query",
               referer=ref, data=urllib.parse.urlencode(
                   {"keyWord": code, "maxNum": "10"}).encode())
    hits = json.loads(top)
    org = next((h["orgId"] for h in hits if h.get("code") == code), None)
    if not org:
        return {}
    column = "sse" if exchange_of(code) == "SH" else "szse"
    plate = "sh" if column == "sse" else "sz"
    # 必须按 seDate 分窗扫，不能只查一次：hisAnnouncement/query 的 pageNum **完全无效**
    # （pageNum=2 返回与第 1 页一模一样的 30 条），且 pageSize 被服务端压到 30，
    # 于是「不带 seDate 查一次」只能回溯到 2011 年前后，早年年份被静默丢掉
    # （水泥五家 2010 年报就是这么「查不到」的，实测 2026-08-20）。
    # 公告日 = 报告年 + 1，故按公告日分窗；从新到旧扫，保证修订版仍先于原始版命中。
    anns: list[dict] = []
    for hi in range(2027, 2000, -3):
        body = http("http://www.cninfo.com.cn/new/hisAnnouncement/query", referer=ref,
                    data=urllib.parse.urlencode({
                        "stock": f"{code},{org}", "tabName": "fulltext",
                        "pageSize": "30", "pageNum": "1", "column": column,
                        "category": "category_ndbg_szsh", "plate": plate,
                        "seDate": f"{hi - 2}-01-01~{hi}-12-31",
                        "isHLtitle": "true"}).encode())
        anns.extend(json.loads(body).get("announcements") or [])
        time.sleep(0.3)
    out: dict[int, str] = {}
    for a in anns:
        title = a.get("announcementTitle") or ""
        # 排除摘要/英文/补充/取消/更正公告/H 股版（A 股年报为准，H 股版会混口径）
        if any(k in title for k in ("摘要", "英文", "补充", "取消", "H股", "H 股", "（H", "(H")):
            continue
        if title.startswith("关于"):     # 「关于2008年年度报告更正公告」不是年报正文
            continue
        # 标题写法不统一：新近「2025年度报告」、早年「2019年年度报告」、建行「2022年年报」，都要匹配
        m = re.search(r"(\d{4})\s*年(?:年度报告|度报告|年报)", title)
        if not m:
            continue
        yr = int(m.group(1))
        url = "http://static.cninfo.com.cn/" + a["adjunctUrl"]
        out.setdefault(yr, url)      # 列表按时间倒序，首条即最新修订版
    return out


def list_sse(code: str) -> dict[int, str]:
    """上交所：queryCompanyBulletin.do（非 ...New.do）。返回 {报告年份: 完整 PDF URL}。"""
    if exchange_of(code) != "SH":
        return {}
    ref = "http://www.sse.com.cn/"
    url = ("http://query.sse.com.cn/security/stock/queryCompanyBulletin.do"
           "?jsonCallBack=jsonpCallback&isPagination=true&productId=" + code +
           "&keyWord=&securityType=0101&reportType2=DQBG&reportType=YEARLY"
           "&pageHelp.pageSize=50&pageHelp.pageNo=1&pageHelp.beginPage=1"
           "&pageHelp.cacheSize=1&pageHelp.endPage=1")
    raw = http(url, referer=ref).decode("utf-8", "replace")
    m = re.search(r"jsonpCallback\((.*)\)\s*$", raw, re.S)
    doc = json.loads(m.group(1) if m else raw)
    out: dict[int, str] = {}
    for r in doc.get("pageHelp", {}).get("data") or []:
        title = r.get("TITLE") or ""
        if "摘要" in title or "补充" in title:
            continue
        mm = re.search(r"(\d{4})\s*年", title)
        if not mm:
            continue
        yr = int(mm.group(1))
        out.setdefault(yr, "http://static.sse.com.cn" + r["URL"])
    return out


def list_hkexnews(code: str) -> dict[int, str]:
    """港交所 HKEXnews：需内部 stockId（prefix.do 解析器当前失效，用 HKEX_STOCK_ID 表）。
    仅用于纯 H 股发行人（银行与中国太平 00966）。返回 {报告年份: 完整 PDF URL}。
    注意 searchType=1 的检索库只覆盖 2007-04 以后的披露，更早年份此处取不到。"""
    sid = HKEX_STOCK_ID.get(code)
    if not sid:
        return {}
    ref = "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en"
    out: dict[int, str] = {}
    # 中文版优先：纯 H 股各行的年报手工提取覆盖层都按中文原文（繁体）通读，取英文版会换一套
    # 科目名。标题写法不统一，「年報」与「年度報告」都要试（哈尔滨银行 06138 只有
    # 「2013年年度報告」这种写法，用「年報」检索只命中一条补充公告）。
    for lang, tag in (("zh", "年度報告"), ("zh", "年報"), ("en", "ANNUAL REPORT")):
        url = ("https://www1.hkexnews.hk/search/titleSearchServlet.do"
               "?sortDir=0&sortByOptions=DateTime&category=0&market=SEHK"
               f"&stockId={sid}&documentType=-1&fromDate=20000101&toDate=20301231"
               f"&title={urllib.parse.quote(tag)}&searchType=1&t1code=-2&t2Gcode=-2&t2code=-2"
               f"&rowRange=800&lang={lang}")
        try:
            raw = json.loads(http(url, referer=ref))
            rows = json.loads(raw.get("result") or "[]")
        except Exception as e:                          # noqa: BLE001
            print(f"      [hkexnews {lang}] {e}", file=sys.stderr)
            continue
        # 年份可前可后，中文版年份与「年報」之间无空格：
        # 「2024 ANNUAL REPORT」/「Annual Report 2024」/「2024年年報」
        pats = (re.compile(rf"^(\d{{4}})\s*年?\s*{tag}$", re.I),
                re.compile(rf"^{tag}\s*(\d{{4}})$", re.I))
        for r in rows:
            title = (r.get("TITLE") or "").strip()
            # 徽商 03698 写「二零二五年年度報告」（中文数字年份），先换成阿拉伯数字
            title = re.sub(r"[零〇一二三四五六七八九]{4}(?=年)",
                           lambda mm: "".join(str("零一二三四五六七八九".index(c) if c != "〇" else 0)
                                              for c in mm.group(0)), title)
            m = next((p.match(title) for p in pats if p.match(title)), None)
            if not m:
                continue
            yr = int(m.group(1))
            out.setdefault(yr, "https://www1.hkexnews.hk" + r["FILE_LINK"])
        if out:                                         # 命中一种写法即可，其余仅兜底
            break
    return out


def list_dfcfw(code: str) -> dict[int, str]:
    """东方财富公告镜像兜底：走 np-anotice-stock 列表接口找年报，返回 {报告年份: infoCode/URL}。"""
    market = "SH" if exchange_of(code) == "SH" else "SZ"
    api = ("https://np-anotice-stock.eastmoney.com/api/security/ann"
           f"?sr=-1&page_size=50&page_index=1&ann_type=A&client_source=web"
           f"&stock_list={code}&f_node=0&s_node=0")
    try:
        doc = json.loads(http(api, referer="https://data.eastmoney.com/"))
    except Exception:                                   # noqa: BLE001
        return {}
    out: dict[int, str] = {}
    for a in (doc.get("data") or {}).get("list") or []:
        title = a.get("title") or ""
        if "年度报告" not in title or "摘要" in title:
            continue
        m = re.search(r"(\d{4})\s*年", title)
        art = a.get("art_code")
        if not m or not art:
            continue
        yr = int(m.group(1))
        # dfcfw PDF 直链：pdf.dfcfw.com/pdf/H2_<art>_1.pdf
        out.setdefault(yr, f"https://pdf.dfcfw.com/pdf/H2_{art}_1.pdf")
    _ = market
    return out


# 源名 -> (列表函数, 下载所需 Referer)
SOURCES = {
    "hkexnews": (list_hkexnews, "https://www1.hkexnews.hk/"),
    "sse":      (list_sse,      "http://www.sse.com.cn/"),
    "cninfo":   (list_cninfo,   "http://www.cninfo.com.cn/"),
    "dfcfw":    (list_dfcfw,    "https://data.eastmoney.com/"),
}


def source_order(code: str, only: str | None) -> list[str]:
    """按代码类型与用户优先级排序尝试的源。"""
    if only:
        return [only]
    if is_hk_code(code):
        return ["hkexnews", "dfcfw"]            # 纯 H 股：港交所优先
    # A 股（含 dual-listed）：数据以 A 股年报为准，故不走港交所 H 股 PDF
    if exchange_of(code) == "SH":
        return ["sse", "cninfo", "dfcfw"]       # 上交所优先，WAF 挡了降级 cninfo
    return ["cninfo", "dfcfw"]                  # 深市：巨潮


def download(code: str, years: range, only: str | None = None) -> dict:
    """对单行按源优先级下载 years 内年报 PDF 到 data/raw/ 并转 txt。返回下载明细。"""
    RAW.mkdir(parents=True, exist_ok=True)
    log: dict = {"code": code, "downloaded": {}, "skipped": [], "failed": {}, "source_used": {}}
    want = set(years)
    # 已存在的跳过
    for y in list(want):
        pdf = RAW / f"annual_{code}_{y}.pdf"
        if pdf.exists() and pdf.stat().st_size > 10000:
            log["skipped"].append(y)
            want.discard(y)
    if not want:
        return log

    for src in source_order(code, only):
        if not want:
            break
        list_fn, ref = SOURCES[src]
        try:
            listing = list_fn(code)
        except Exception as e:                          # noqa: BLE001
            print(f"    [{src}] 列表失败: {e}", file=sys.stderr)
            continue
        avail = sorted(want & set(listing))
        if not avail:
            print(f"    [{src}] 无可下年份（列表覆盖 "
                  f"{min(listing) if listing else '-'}~{max(listing) if listing else '-'}）")
            continue
        print(f"    [{src}] 命中 {avail}")
        for y in avail:
            if y not in want:
                continue
            url = listing[y]
            pdf = RAW / f"annual_{code}_{y}.pdf"
            try:
                body = http(url, referer=ref)
                if not looks_like_pdf(body):
                    raise RuntimeError(f"非 PDF（{len(body)}B，疑 WAF 挑战/错误页）")
                pdf.write_bytes(body)
                pdf_to_text.convert(pdf)                 # 体检不过会 raise 且不写 txt
                log["downloaded"][y] = url
                log["source_used"][y] = src
                log["failed"].pop(y, None)               # 之前源失败但本源成功，清掉失败记录
                want.discard(y)
                print(f"      [ok] annual_{code}_{y}.pdf  <- {src}  ({len(body)//1024}KB)")
            except Exception as e:                       # noqa: BLE001
                if pdf.exists() and not (RAW / f"annual_{code}_{y}.txt").exists():
                    pdf.unlink(missing_ok=True)          # 删掉坏 PDF，允许下一个源重试
                log["failed"].setdefault(y, []).append(f"{src}: {e}")
                print(f"      [fail] {y} <- {src}: {e}", file=sys.stderr)
            time.sleep(1)

    for y in sorted(want):
        log["failed"].setdefault(y, []).append("所有源均未取到")
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("codes", nargs="+", help="银行代码（A 股 6 位 / 港股 5 位）")
    ap.add_argument("--years", default="2018-2025", help="年份区间，如 2018-2025 或 2020")
    ap.add_argument("--source", choices=list(SOURCES), help="只用指定源（调试）")
    args = ap.parse_args()

    if "-" in args.years:
        a, b = args.years.split("-")
        years = range(int(a), int(b) + 1)
    else:
        years = range(int(args.years), int(args.years) + 1)

    summary = []
    for code in args.codes:
        print(f"\n=== {code}  years {years.start}-{years.stop - 1} ===")
        summary.append(download(code, years, args.source))

    print("\n" + "=" * 60 + "\n汇总：")
    for s in summary:
        got = sorted(s["downloaded"])
        skip = sorted(s["skipped"])
        fail = sorted(s["failed"])
        srcs = {v for v in s["source_used"].values()}
        print(f"  {s['code']}: 新下 {got or '-'} (源 {srcs or '-'}) | "
              f"已存在 {skip or '-'} | 失败 {fail or '-'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                              # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)