"""
从 FRED (St. Louis Fed) 抓取 WTI / Brent 原油价格数据。

数据源: https://fred.stlouisfed.org/
    - DCOILWTICO   : WTI 现货 (Cushing, OK)     日频
    - MCOILWTICO   : WTI 现货                    月频 (月内交易日算术平均)
    - DCOILBRENTEU : Brent 现货 (Europe FOB)    日频
    - MCOILBRENTEU : Brent 现货                  月频

FRED 的 fredgraph.csv 端点开放下载，无需 API Key。
输出保存到 data/tables/，UTF-8 CSV，两列：date, price (USD/bbl)。
"""

from __future__ import annotations

import io
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# 项目根目录（extract/ 的上一级）
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "tables"

SERIES = {
    "wti_daily":    "DCOILWTICO",
    "wti_monthly":  "MCOILWTICO",
    "brent_daily":  "DCOILBRENTEU",
    "brent_monthly": "MCOILBRENTEU",
}

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def fetch_series(series_id: str, retries: int = 3, timeout: int = 60) -> pd.DataFrame:
    """下载单个 FRED 序列并返回 DataFrame[date, price]。失败时指数退避重试。"""
    url = FRED_CSV_URL.format(sid=series_id)
    # 注意: FRED 在收到 Accept-Encoding: gzip/deflate 时会挂起(实测),
    # 显式改为 identity。UA 用 curl 风格以避免可能的 WAF 拦截。
    headers = {
        "User-Agent": "curl/7.68.0",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }

    last_err: Exception | None = None
    raw = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            raw = resp.text
            break
        except (requests.RequestException, socket.timeout) as e:
            last_err = e
            wait = 2 ** attempt
            print(f"    [retry {attempt}/{retries}] {e}; sleep {wait}s", file=sys.stderr)
            time.sleep(wait)
    if raw is None:
        raise RuntimeError(f"failed after {retries} attempts: {last_err}")

    # FRED 现在返回的列名是 observation_date + series_id (旧格式是 DATE)
    df = pd.read_csv(io.StringIO(raw))
    date_col = df.columns[0]
    value_col = df.columns[1]

    df = df.rename(columns={date_col: "date", value_col: "price"})
    # FRED 用 "." 表示缺失
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["price"]).reset_index(drop=True)
    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    summary = []
    for name, sid in SERIES.items():
        print(f"[fetch] {name}  <-  FRED:{sid}")
        df = fetch_series(sid)
        out_path = OUT_DIR / f"{name}.csv"
        df.to_csv(out_path, index=False)
        summary.append({
            "file": out_path.name,
            "series": sid,
            "rows": len(df),
            "start": df["date"].min().date().isoformat(),
            "end":   df["date"].max().date().isoformat(),
        })
        print(f"    -> {out_path.relative_to(ROOT)}  "
              f"({len(df)} rows, {summary[-1]['start']} ~ {summary[-1]['end']})")

    # 写一份元数据说明
    meta_path = OUT_DIR / "fred_oil_meta.txt"
    with meta_path.open("w", encoding="utf-8") as f:
        f.write(f"# FRED oil price fetch\n")
        f.write(f"# fetched_at: {stamp}\n")
        f.write(f"# source: https://fred.stlouisfed.org/\n\n")
        for row in summary:
            f.write(f"{row['file']}\t{row['series']}\t"
                    f"rows={row['rows']}\t{row['start']}~{row['end']}\n")
    print(f"[meta] {meta_path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
