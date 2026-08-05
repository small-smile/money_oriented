"""
从 EI Statistical Review 抽取世界总发电量 (World electricity generation)：

    Electricity Generation - TWh  →  data/tables/electricity_generation.txt

只取 "Total World" 行，年份 1985-2024（源表电力序列从 1985 起）。
输出两列 tab 分隔: year, twh，与 world_population.txt 同风格，
便于后端 read_electricity 直接按行解析。

注意：源表表头行里，年度列之后还有 3 个统计列（同比增速 / 近十年均速 / 份额），
它们的表头被错误写成 "2024"，所以按"4 位年份 + 严格递增"去重，只保留真正的年度列。

用法：
    python data/extract/electricity.py
"""
import openpyxl

XLSX_PATH = "data/raw/EI-Stats-Review-ALL-data.xlsx"
OUT_PATH = "data/tables/electricity_generation.txt"
SHEET = "Electricity Generation - TWh"
ROW_LABEL = "Total World"


def main():
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb[SHEET]
    rows = list(ws.iter_rows(values_only=True))

    # 表头在第 3 行 (index 2)：col0='Terawatt-hours', 其后为年份
    hdr = rows[2]
    year_cols = []
    last_year = None
    for i, cell in enumerate(hdr):
        s = str(cell).strip() if cell is not None else ""
        if len(s) == 4 and s.isdigit():
            y = int(s)
            # 只保留严格递增的年份列，丢掉尾部被误标为 "2024" 的统计列
            if last_year is None or y > last_year:
                year_cols.append((i, y))
                last_year = y

    world = next(r for r in rows if r[0] and str(r[0]).strip() == ROW_LABEL)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("year\ttwh\n")
        for ci, y in year_cols:
            v = world[ci]
            if v is None:
                continue
            f.write(f"{y}\t{float(v):.1f}\n")

    print(f"[extract] {ROW_LABEL} electricity -> {OUT_PATH} "
          f"({year_cols[0][1]}~{year_cols[-1][1]}, {len(year_cols)} years)")


if __name__ == "__main__":
    main()
