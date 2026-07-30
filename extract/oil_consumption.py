"""
从 EI Statistical Review 里抽取 Oil Consumption - barrels sheet，
按 (年份, 国家, 洲, 消费量千桶/日) 展平输出到 data/tables/consumption_region.csv

用法：
    python extract/oil_consumption.py

结构与 production_region.csv 完全一致，便于后端复用聚合逻辑。
"""
import os
import pandas as pd

XLSX_PATH = "data/raw/EI-Stats-Review-ALL-data.xlsx"
OUT_PATH = "data/tables/consumption_region.csv"
SHEET = "Oil Consumption - barrels"

# 每个洲汇总行的文字标签 → 洲名（会被跳过写入，仅用作"分洲游标"切换）
TOTAL_TO_REGION = {
    "Total North America":        "North America",
    "Total S. & Cent. America":   "S. & Cent. America",
    "Total Europe ":              "Europe",   # 注意尾部空格与源文件一致
    "Total Europe":               "Europe",
    "Total CIS":                  "CIS",
    "Total Middle East":          "Middle East",
    "Total Africa":               "Africa",
    "Total Asia Pacific":         "Asia Pacific",
}

# 明确要跳过的非"国家"行（Total、注释、聚合口径等）
SKIP_ROWS = {
    "Total World", "of which: OECD", "Non-OECD",
    "European Union #", "European Union",
}


def main() -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name=SHEET, header=None)

    # 第 3 行（index=2）是年份表头。注意源表右侧还挂了 "2024 增长率" / "2014-24 平均"
    # / "2024 份额" 等辅助列，也叫 2024 —— 只取第一次出现，避免重复入表。
    year_row = df.iloc[2, 1:].tolist()
    years = []
    year_cols = []
    seen = set()
    for i, y in enumerate(year_row, start=1):
        if pd.notna(y):
            try:
                yi = int(y)
                if 1900 < yi < 2100 and yi not in seen:
                    seen.add(yi)
                    years.append(yi)
                    year_cols.append(i)
            except (TypeError, ValueError):
                continue

    # 按顺序缓冲当前"待归属洲"的国家行；一旦遇到 Total 行，回填所有 buffered 行的洲
    pending = []   # [(row_idx, country_name)]
    rows = []
    for i in range(4, len(df)):
        name_raw = df.iloc[i, 0]
        if not isinstance(name_raw, str):
            continue
        name = name_raw.strip()
        if not name:
            continue

        # 洲总计行：把缓冲区里的国家写入该洲
        if name in TOTAL_TO_REGION:
            region = TOTAL_TO_REGION[name]
            for row_idx, country in pending:
                for y, col in zip(years, year_cols):
                    v = df.iloc[row_idx, col]
                    if pd.isna(v):
                        continue
                    try:
                        v_num = round(float(v), 4)
                    except (TypeError, ValueError):
                        continue
                    rows.append((y, country, region, v_num))
            pending = []
            continue

        if name.startswith("Total "):
            # 未预期的 Total 前缀行：清空缓冲丢弃
            pending = []
            continue
        if name in SKIP_ROWS:
            pending = []
            continue

        low = name.lower()
        if low.startswith(("*", "n/a", "notes:", "annual")):
            continue
        if low.startswith("ussr includes") or low.startswith("of which:") or low.startswith("non-oecd"):
            continue
        if name.startswith("#"):
            continue

        # 视为国家行，加入缓冲区
        pending.append((i, name))

    out_df = pd.DataFrame(rows, columns=["年份", "国家", "洲", "消费量(千桶/日)"])
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print(f"wrote {len(out_df)} rows to {OUT_PATH}")
    print(out_df.head())
    print("countries:", out_df["国家"].nunique())
    print("years:", out_df["年份"].min(), "-", out_df["年份"].max())


if __name__ == "__main__":
    main()
