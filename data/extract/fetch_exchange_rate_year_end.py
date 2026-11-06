"""年末人民币汇率中间价 → data/tables/exchange_rate_year_end.json，供 exchange_rate_year_end 表。

来源：中国外汇交易中心（中国货币网 chinamoney.com.cn）「人民币汇率中间价」历史查询接口 CcprHisNew，
受权公布的官方中间价，接口 2006 年起有数。每年查 12 月整月，取最后一个发布日。
原始响应缓存在 data/raw/fx_cfets_<币种>.json，没有 --refresh 就只读缓存、不联网。

    ./venv/bin/python data/extract/fetch_exchange_rate_year_end.py [--refresh]
"""
import argparse
import datetime
import json
import sys
import time
import urllib.request

from _common import OUT_DIR, RAW_DIR, jsonstore

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
FIRST_YEAR = 2006                               # 接口最早有数的年份
LAST_YEAR = datetime.date.today().year - 1      # 只取已结束的年度
OUT = OUT_DIR / "exchange_rate_year_end.json"
SOURCE = "中国外汇交易中心 人民币汇率中间价"
# 币种（与各表 currency 同一写法）-> 接口报价代码；报价都是「1 单位外币 = X 元」
PAIRS = {"港元": "HKD/CNY"}


def http(url, retries=3, timeout=60):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.chinamoney.com.cn/"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:                      # noqa: BLE001 - 统一重试
            last = e
            print("    [retry %d/%d] %s" % (attempt, retries, e), file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("%s 失败: %s" % (url, last))


def december(pair, year):
    """某年 12 月的逐日中间价 [{date, values:[报价]}]（12 月最多 23 个发布日，一页够）。"""
    d = http("https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew?startDate=%d-12-01&endDate=%d-12-31"
             "&currency=%s&pageNum=1&pageSize=50" % (year, year, pair))
    return d.get("records") or []


def main():
    ap = argparse.ArgumentParser(description="年末人民币汇率中间价 → data/tables/exchange_rate_year_end.json")
    ap.add_argument("--refresh", action="store_true", help="重新联网抓取，覆盖 data/raw/fx_cfets_*.json 缓存")
    refresh = ap.parse_args().refresh

    rows = []
    for currency, pair in PAIRS.items():
        path = RAW_DIR / ("fx_cfets_%s.json" % pair.split("/")[0].lower())
        raw = {} if refresh or not jsonstore.exists(path) else jsonstore.read(path)
        missing = [y for y in range(FIRST_YEAR, LAST_YEAR + 1) if str(y) not in raw]
        if missing:
            print("    [http] %s %d—%d" % (pair, missing[0], missing[-1]))
            raw.update({str(y): december(pair, y) for y in missing})
            jsonstore.write(path, raw, ensure_ascii=False)
        for y in sorted(raw, key=int):
            recs = [r for r in raw[y] if r.get("values") and r["values"][0]]
            if not recs:
                print("  %s %s 年 12 月无中间价" % (currency, y))
                continue
            last = max(recs, key=lambda r: r["date"])
            rows.append({"year": int(y), "currency": currency, "rmb_per_unit": float(last["values"][0]),
                         "rate_date": last["date"], "source": SOURCE})
        got = [r for r in rows if r["currency"] == currency]
        print("  %s %d—%d %d 年" % (currency, got[0]["year"], got[-1]["year"], len(got)))

    jsonstore.write(OUT, {
        "_meta": {"generated_by": "data/extract/fetch_exchange_rate_year_end.py",
                  "fetched_at": datetime.date.today().isoformat(),
                  "caliber": "每年最后一个发布日的人民币汇率中间价, 1 单位外币折人民币元",
                  "columns": "year 年度 / currency 外币 / rmb_per_unit 折人民币元 / rate_date 取值日 / source 来源"},
        "rows": rows}, ensure_ascii=False, indent=1)
    print("写入 %s：%d 行" % (OUT.relative_to(OUT_DIR.parent.parent), len(rows)))


if __name__ == "__main__":
    main()
