"""银行年末每股收盘价（不复权）→ data/tables/share_price_year_end.json，供 share_price_year_end 表。

按信息源优先级先取交易所行情，交易所查不到的年份才退第三方，并逐行记 source：
- 上交所：yunhq 日 K，上市以来全量。
- 深交所：月 K（getHistoryData cycleType=34，每月一根，日期是当月最后成交日），只回最近约 200 根（目前到 2010 年）；
  月 K 被截断的，更早的年份用「股票行情」日报表（report 1815_stock，最早到 2004-12）；再早的交易所不提供。
- 港交所：hkexwidget 日线，只回溯 10 年（2016-11 起）。
- 第三方：平安银行 1991—2003 用腾讯证券日 K（不复权）；哈尔滨银行 2014—2015 用 Yahoo Finance 日线 Close（未做分红复权）。

取每年该股最后一个有成交的交易日；A+H 两地上市的只取 A 股（H 股另成序列，见表 COMMENT）；只取已结束的年度。
原始响应缓存在 data/raw/price_<来源>_<代码>.json，没有 --refresh 就只读缓存、不联网。

    ./venv/bin/python data/extract/fetch_share_price_year_end.py [--refresh]
"""
import argparse
import datetime
import json
import re
import sys
import time
import urllib.request

from _common import OUT_DIR, RAW_DIR, jsonstore

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
LAST_YEAR = datetime.date.today().year - 1      # 只取已结束的年度
OUT = OUT_DIR / "share_price_year_end.json"
SZSE_MONTHLY_CAP = 200                          # 深交所月 K 只回最近约 200 根，够数即视为被截断
SZSE_REPORT_FROM = 2004                         # 深交所日报表最早到 2004-12
HKEX_QUOTE_PAGE = "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=%d&sc_lang=en"

SRC_SSE = "上交所行情(yunhq 日K)"
SRC_SZSE_MONTHLY = "深交所行情(月K)"
SRC_SZSE_REPORT = "深交所股票行情日报表"
SRC_HKEX = "港交所行情(hkexwidget 日线)"
SRC_TENCENT = "腾讯证券日K(不复权)"
SRC_YAHOO = "Yahoo Finance 日线 Close(未做分红复权)"
# 交易所查不到的年份：代码 -> (来源, 年份)
THIRD_PARTY = {"000001": (SRC_TENCENT, range(1991, SZSE_REPORT_FROM)),
               "06138": (SRC_YAHOO, range(2014, 2016))}


def http(url, referer, retries=3, timeout=60):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001 - 统一重试
            last = e
            print("    [retry %d/%d] %s" % (attempt, retries, e), file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("%s 失败: %s" % (url, last))


def cached(name, fetch, refresh):
    path = RAW_DIR / ("price_%s.json" % name)
    if jsonstore.exists(path) and not refresh:
        return jsonstore.read(path)
    print("    [http] %s" % name)
    data = fetch()
    jsonstore.write(path, data, ensure_ascii=False)
    return data


def year_last(bars):
    """[(YYYY-MM-DD, close)] 升序 → {年: (日期, 收盘)}，每年取最后一根。"""
    out = {}
    for d, c in sorted(bars):
        if int(d[:4]) <= LAST_YEAR:
            out[int(d[:4])] = (d, float(c))
    return out


def sse(code, refresh):
    d = cached("sse_" + code, lambda: json.loads(http(
        "http://yunhq.sse.com.cn:32041/v1/sh1/dayk/%s?begin=0&end=-1&period=day" % code,
        "http://www.sse.com.cn/")), refresh)
    # kline: [YYYYMMDD, 开, 高, 低, 收, 成交量, 成交额]
    return {y: v + (SRC_SSE,) for y, v in year_last(
        ("%s-%s-%s" % (str(k[0])[:4], str(k[0])[4:6], str(k[0])[6:]), k[4]) for k in d["kline"] if k[5]).items()}


def szse_report(code, year):
    """深交所「股票行情」日报表只按单日查（给日期区间也只回 txtBeginDate 那天），
    所以从 12-31 往前逐日查，查到 12 月里最后一个有成交的交易日为止；12 月整月无成交的年份留空。"""
    day = datetime.date(year, 12, 31)
    while day.month == 12:
        t = json.loads(http(
            "http://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1815_stock&TABKEY=tab1"
            "&txtBeginDate=%s&txtEndDate=%s&txtDMorJC=%s" % (day, day, code), "http://www.szse.cn/"))[0]
        rows = [r for r in t["data"] if float(r["cjgs"].replace(",", "") or 0) > 0]
        if rows:
            return rows
        day -= datetime.timedelta(days=1)
    return []


def szse(code, refresh):
    m = cached("szse_month_" + code, lambda: json.loads(http(
        "http://www.szse.cn/api/market/ssjjhq/getHistoryData?cycleType=34&marketId=1&code=%s" % code,
        "http://www.szse.cn/")), refresh)
    # picupdata: [当月最后成交日, 开, 收, 低, 高, 涨跌, 涨幅%, 成交量, 成交额]
    bars = m["data"]["picupdata"]
    got = {y: v + (SRC_SZSE_MONTHLY,) for y, v in year_last((r[0], r[2]) for r in bars if r[7]).items()}
    if len(bars) < SZSE_MONTHLY_CAP:
        return got                                      # 月 K 没被截断＝上市就在窗口内，不用查日报表
    first_year = int(bars[0][0][:4])                    # 首根所在年的年末已由月 K 覆盖
    rep = cached("szse_report_" + code, lambda: {
        str(y): szse_report(code, y) for y in range(SZSE_REPORT_FROM, first_year)}, refresh)
    for rs in rep.values():
        # jyrq 交易日、ss 今收、cjgs 成交股数(万股,带千分位)
        bars = [(r["jyrq"], r["ss"]) for r in rs if float(r["cjgs"].replace(",", "") or 0) > 0]
        for y, v in year_last(bars).items():
            got.setdefault(y, v + (SRC_SZSE_REPORT,))
    return got


def hkex(code, refresh):
    def fetch():
        html = http(HKEX_QUOTE_PAGE % int(code), "https://www.hkex.com.hk/")
        token = re.search(r'return\s+"([A-Za-z0-9%+/=]{20,})"', html).group(1)
        t = http("https://www1.hkex.com.hk/hkexwidget/data/getchartdata2?hchart=1&span=6&int=8"
                 "&ric=%d.HK&token=%s&qid=1&callback=cb" % (int(code), token), "https://www.hkex.com.hk/")
        return json.loads(t[t.index("(") + 1:t.rindex(")")])
    d = cached("hkex_" + code, fetch, refresh)
    # span=6 日线、int=8 近 10 年；datalist: [香港时间零点的 UTC 毫秒, 开, 高, 低, 收, 成交量, 成交额]
    hkt = lambda ms: (datetime.datetime.utcfromtimestamp(ms / 1000) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
    return {y: v + (SRC_HKEX,) for y, v in year_last(
        (hkt(r[0]), r[4]) for r in d["data"]["datalist"] if r[4] is not None and r[5]).items()}


def tencent(code, years):
    bars = []
    for a in range(years.start, years.stop, 6):         # 接口单次最多 2000 根，6 年一段
        b = min(a + 5, years.stop - 1)
        u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz%s,day,%d-01-01,%d-12-31,2000," % (code, a, b)
        # day: [日期, 开, 收, 高, 低, 成交量]，不带 qfq/hfq 即不复权
        bars += [[r[0], r[2]] for r in json.loads(http(u, "https://gu.qq.com/"))["data"]["sz" + code]["day"]
                 if float(r[5]) > 0]
    return bars


def yahoo(code, years):
    import yfinance as yf
    h = yf.Ticker("%d.HK" % int(code)).history(start="%d-01-01" % years.start, end="%d-01-10" % years.stop,
                                               auto_adjust=False)
    return [[d.strftime("%Y-%m-%d"), round(float(c), 4)] for d, c, v in zip(h.index, h["Close"], h["Volume"]) if v > 0]


def main():
    ap = argparse.ArgumentParser(description="银行年末每股收盘价 → data/tables/share_price_year_end.json")
    ap.add_argument("--refresh", action="store_true", help="重新联网抓取，覆盖 data/raw/price_*.json 缓存")
    refresh = ap.parse_args().refresh

    banks = [e for e in jsonstore.read(OUT_DIR / "company_codes.json")["entities"] if e["industry"] == "bank"]
    rows = []
    for e in banks:
        code = e["a_code"] or e["h_code"]
        currency = "元" if e["a_code"] else "港元"
        got = (sse if code.startswith("6") else szse if e["a_code"] else hkex)(code, refresh)
        if code in THIRD_PARTY:
            src, years = THIRD_PARTY[code]
            fetch = tencent if src == SRC_TENCENT else yahoo
            bars = cached("%s_%s" % (fetch.__name__, code), lambda: fetch(code, years), refresh)
            for y, v in year_last(bars).items():
                if y in years:
                    got.setdefault(y, v + (src,))
        for y in sorted(got):
            d, c, src = got[y]
            rows.append({"code": e["key"], "year": y, "trade_date": d, "close": c, "currency": currency, "source": src})
        print("  %-8s %-6s %s—%s %3d 年  %s" % (e["key"], e["short"], min(got), max(got), len(got),
                                               " / ".join(sorted({v[2] for v in got.values()}))))

    jsonstore.write(OUT, {
        "_meta": {"generated_by": "data/extract/fetch_share_price_year_end.py",
                  "fetched_at": datetime.date.today().isoformat(),
                  "caliber": "每年该股最后一个有成交的交易日收盘价,不复权,A+H 两地上市只取 A 股",
                  "columns": "code 裸代码 / year 年度 / trade_date 取价日 / close 收盘价 / currency 币种 / source 来源"},
        "rows": rows}, ensure_ascii=False, indent=1)
    print("写入 %s：%d 家 %d 行" % (OUT.relative_to(OUT_DIR.parent.parent), len(banks), len(rows)))


if __name__ == "__main__":
    main()
