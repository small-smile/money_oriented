"""
从 World Bank Open Data 抓取世界人口 (SP.POP.TOTL)。

数据源: https://data.worldbank.org/indicator/SP.POP.TOTL
    - indicator : SP.POP.TOTL  (Population, total)
    - country   : WLD          (World 聚合)
    - 覆盖范围  : 1960 起 (World Bank 世界聚合无更早数据)

World Bank v2 REST API 开放访问，无需 API Key。
输出保存到 data/tables/world_population.txt，UTF-8，两列: year, population_yi (单位: 亿)。
单位用「亿」以与图表 Y 轴一致，也保持 backend read_population 的解析格式不变。
"""

from __future__ import annotations

import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "tables"

INDICATOR = "SP.POP.TOTL"
COUNTRY = "WLD"
API_URL = (
    "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    "?format=json&per_page=1000"
)


def fetch_population(retries: int = 3, timeout: int = 60) -> list[tuple[str, float]]:
    """返回按年份升序的 [(year, population_yi), ...]。失败时指数退避重试。"""
    url = API_URL.format(country=COUNTRY, indicator=INDICATOR)
    headers = {"User-Agent": "curl/7.68.0", "Accept-Encoding": "identity"}

    last_err: Exception | None = None
    payload = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            break
        except (requests.RequestException, socket.timeout, ValueError) as e:
            last_err = e
            wait = 2 ** attempt
            print(f"    [retry {attempt}/{retries}] {e}; sleep {wait}s", file=sys.stderr)
            time.sleep(wait)
    if payload is None:
        raise RuntimeError(f"failed after {retries} attempts: {last_err}")

    # World Bank 返回 [metadata, data]
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"unexpected API payload: {str(payload)[:200]}")

    rows: list[tuple[str, float]] = []
    for item in payload[1]:
        year = item.get("date")
        val = item.get("value")
        if year is None or val is None:
            continue
        rows.append((year, float(val) / 1e8))  # 人数 -> 亿

    rows.sort(key=lambda r: int(r[0]))
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[fetch] world_population  <-  WorldBank:{INDICATOR} ({COUNTRY})")
    rows = fetch_population()
    if not rows:
        raise RuntimeError("no population rows returned")

    out_path = OUT_DIR / "world_population.txt"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("year\tpopulation_yi\n")
        for year, yi in rows:
            f.write(f"{year}\t{yi:.2f}\n")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"    -> {out_path.relative_to(ROOT)}  "
          f"({len(rows)} rows, {rows[0][0]}~{rows[-1][0]}) @ {stamp}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
