"""
Fetch 社会融资规模（TSF / Aggregate Financing to the Real Economy）月度数据。

来源: 人民银行调查统计司 - 统计数据 - 社会融资规模
    http://www.pbc.gov.cn/diaochatongjisi/116219/index.html
       └─ 20xx 年统计数据 → 社会融资规模 → 存量统计表.xlsx / 增量统计表.xlsx

每年一份 XLSX，各含当年 12 个月。分别缓存到 data/raw/pboc_tsf/YYYY_{stock,flow}.xlsx，
最终汇总到 data/tables/tsf_pboc_stock.json 与 tsf_pboc_flow.json。

用法:
    python data/extract/fetch_pboc_tsf.py         # 缺失年份才下载
    python data/extract/fetch_pboc_tsf.py --refresh  # 全部重新下载

注意:
    - PBoC 每年 XLSX 均为"当年 as-of 该年报送口径"，历年间口径不完全一致
      （2018 存款类金融机构 ABS 与贷款核销新增子项、2023 消金/理财/AIC 纳入统计等），
      表格内容/列数在不同年份会略有差异，脚本按"社会融资规模(总)+主要科目"取交集。
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("请先在 venv 中 `pip install openpyxl`")

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "pboc_tsf"
TABLES_DIR = ROOT / "data" / "tables"
BASE = "https://www.pbc.gov.cn"

# 主索引: 116319 下每一个「YYYY 年统计数据」子页 id
YEAR_INDEX = {
    2015: "/diaochatongjisi/116219/116319/2161324/index.html",
    2016: "/diaochatongjisi/116219/116319/3013637/index.html",
    2017: "/diaochatongjisi/116219/116319/3245697/index.html",
    2018: "/diaochatongjisi/116219/116319/3471721/index.html",
    2019: "/diaochatongjisi/116219/116319/3750274/index.html",
    2020: "/diaochatongjisi/116219/116319/3959050/index.html",
    2021: "/diaochatongjisi/116219/116319/4184109/index.html",
    2022: "/diaochatongjisi/116219/116319/4458449/index.html",
    2023: "/diaochatongjisi/116219/116319/4780803/index.html",
    2024: "/diaochatongjisi/116219/116319/5225358/index.html",
    2025: "/diaochatongjisi/116219/116319/5570903/index.html",
    2026: "/diaochatongjisi/116219/116319/2026ntjsj/index.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux) TSF-fetch/1.0",
    "Accept-Encoding": "identity",
    "Referer": "https://www.pbc.gov.cn/",
}


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def find_tsf_section_url(year_index_url: str) -> str | None:
    """在年度索引页里找到「社会融资规模」子栏目 URL。"""
    html = http_get(year_index_url).decode("utf-8", "ignore")
    m = re.search(r'href="([^"]+)"[^>]*>\s*社会融资规模', html)
    return BASE + m.group(1) if m else None


def find_attachment_pair(tsf_section_url: str) -> tuple[
    tuple[str | None, str | None], tuple[str | None, str | None]
]:
    """在「社会融资规模」子页定位存量/增量附件。

    2022 年起有 XLSX，2015-2021 只有 HTM。返回:
        ((stock_url, stock_ext), (flow_url, flow_ext))
    ext ∈ {"xlsx", "htm"}
    """
    html = http_get(tsf_section_url).decode("utf-8", "ignore")
    html_flat = re.sub(r"\s+", " ", html)

    def pick(kind: str) -> tuple[str | None, str | None]:
        # 每个附件项形如 "社会融资规模{kind}统计表 ... href=<htm> ... href=<xlsx> ... href=<pdf>"
        m = re.search(
            rf"社会融资规模{kind}统计表[\s\S]*?(?=社会融资规模|$)",
            html_flat,
        )
        if not m:
            return None, None
        seg = m.group(0)
        # 优先 xlsx；没有则退回 htm
        for ext in ("xlsx", "htm"):
            h = re.search(rf'href=[\'"]([^\'"]+\.{ext})[\'"]', seg)
            if h:
                href = h.group(1)
                url = href if href.startswith("http") else BASE + href
                return url, ext
        return None, None

    return pick("存量"), pick("增量")


def cache_attachment(year: int, kind: str, url: str, ext: str, refresh: bool = False) -> Path:
    """缓存附件到 data/raw/pboc_tsf/YYYY_{kind}.{ext}。"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dst = RAW_DIR / f"{year}_{kind}.{ext}"
    if dst.exists() and not refresh:
        return dst
    data = http_get(url)
    dst.write_bytes(data)
    print(f"    saved {dst.name} ({len(data):,} bytes)")
    return dst


# ---------- HTM 解析（2015-2021 fallback）----------

def _flatten_htm(path: Path) -> str:
    """将 HTM 剥离标签后压成单行文本 (GBK 编码回退)。"""
    raw = path.read_bytes()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            t = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover
        t = raw.decode("utf-8", "ignore")
    t = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", "", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&#160;", " ")
    t = re.sub(r"\s+", " ", t)
    # 年份因换行被拆开：例如 "201 7.01" → "2017.01"
    t = re.sub(r"(20\d)\s+(\d[.\-]\d)", r"\1\2", t)
    return t


def parse_stock_htm(path: Path, year: int) -> list[dict]:
    """存量表 HTM: 「社会融资规模存量」总行提取月度 (存量, 同比) 对。

    - 2015 只发布季度数据 (Q1/Q2/Q3/Q4) → 4 条季末记录 (3/6/9/12 月)
    - 2016 起为月度 → 12 条
    - 各年 HTM 布局略有差异 (中英文/数字先后不一)，用「Chinese 标签之间的数字段」通吃
    """
    text = _flatten_htm(path)
    is_quarterly = (year == 2015)
    n_periods = 4 if is_quarterly else 12

    # 首个 "社会融资规模存量" 出现在标题「统计表」；实际数据行是第二次出现
    matches = [m.start() for m in re.finditer(r"社会融资规模存量", text)]
    if len(matches) < 2:
        return []
    start = matches[1]
    # 数据段结束于下一个中文标签「人民币贷款」
    m_next = re.search(r"人民币贷款", text[start + 4:])
    end = (start + 4 + m_next.start()) if m_next else start + 800
    seg = text[start:end]
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d+", seg)]
    nums = nums[: 2 * n_periods]
    if len(nums) < 2:
        return []

    quarterly_months = [3, 6, 9, 12]
    out = []
    for i in range(0, len(nums) - 1, 2):
        idx = i // 2
        mo = quarterly_months[idx] if is_quarterly else (idx + 1)
        out.append({
            "month": f"{year}-{mo:02d}",
            "stock_tnyuan": nums[i],
            "yoy_pct": nums[i + 1],
        })
    return out


# HTM 增量表按年份使用不同列结构 (口径演进):
#   2015-2017: 8 列 (无 政府债券/ABS/贷款核销)
#   2018:      9 列 (2018.09 政府专项债券纳入 → 政府债券)
#   2019+:    11 列 (2018.07 ABS 和 贷款核销 追加为独立列)
_FLOW_COLS_2015_2017 = [
    "total", "rmb_loans", "fx_loans", "entrusted_loans", "trust_loans",
    "undiscounted_ba", "corp_bonds", "equity",
]
_FLOW_COLS_2018 = [
    "total", "rmb_loans", "fx_loans", "entrusted_loans", "trust_loans",
    "undiscounted_ba", "corp_bonds", "gov_bonds", "equity",
]
_FLOW_COLS_2019P = [
    "total", "rmb_loans", "fx_loans", "entrusted_loans", "trust_loans",
    "undiscounted_ba", "corp_bonds", "gov_bonds", "equity", "abs", "loan_writeoff",
]

def _flow_cols_for(year: int) -> list[str]:
    if year <= 2017:
        return _FLOW_COLS_2015_2017
    if year == 2018:
        return _FLOW_COLS_2018
    return _FLOW_COLS_2019P


def parse_flow_htm(path: Path, year: int) -> list[dict]:
    """增量表 HTM: 每月一行 "YYYY.MM v1 v2 ... vN"，按年份口径映射列名。

    2019.htm 内含 3 张表 (调整历史绝对值 / 调整前绝对值 / 结构占比%)，
    这里只保留出现的**首个** 12 月序列 (Chart 1)。
    """
    text = _flatten_htm(path)
    cols = _flow_cols_for(year)
    n = len(cols)
    pat = re.compile(
        rf"{year}[.\-](\d{{1,2}})((?:\s+-?\d+\.?\d*){{{n}}})(?=\s+(?:{year}[.\-]\d|注|表|Chart|$))"
    )
    seen_months: set[int] = set()
    out = []
    for m in pat.finditer(text):
        mo = int(m.group(1))
        if mo < 1 or mo > 12 or mo in seen_months:
            continue
        seen_months.add(mo)
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", m.group(2))][:n]
        rec = {"month": f"{year}-{mo:02d}"}
        for k, v in zip(cols, nums):
            rec[k] = v
        out.append(rec)
        if len(seen_months) == 12:
            break
    return out


# ---------- 解析 XLSX ----------

def _clean(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v if v else None
    return v


def parse_stock(xlsx_path: Path, year: int) -> list[dict]:
    """存量表: 表头前若干行是标题/单位/月份表头，随后按项目行给出 存量/增速 交替列。"""
    wb = load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = [[_clean(c) for c in row] for row in ws.iter_rows(values_only=True)]

    # 找到「月份」表头行（形如 2015.1 / 2025.01）与「项目 Items」标签行
    header_row_idx = None
    for i, row in enumerate(rows):
        cells = [str(c) for c in row if c is not None]
        if any(re.match(rf"^{year}[.\-]0?\d+$", s) for s in cells):
            header_row_idx = i
            break
    if header_row_idx is None:
        return []

    # 月份列表 —— 存量表每个月两列（存量/增速）合并展示，取每个月的第一次出现位置
    month_col: dict[str, int] = {}
    for j, c in enumerate(rows[header_row_idx]):
        if c is None:
            continue
        m = re.match(rf"^{year}[.\-](\d{{1,2}})$", str(c))
        if m and str(c) not in month_col:
            month_col[str(c)] = j  # 该月存量列，其右邻列为增速

    # 定位「社会融资规模存量」总行（AFRE(stock) 前一行 / 中文标签行）
    total_row = None
    for i in range(header_row_idx + 1, len(rows)):
        first = rows[i][0]
        if first is None:
            continue
        s = str(first).strip()
        if s.startswith("社会融资规模") and "存量" in s:
            total_row = i
            break
    if total_row is None:
        return []

    out = []
    for label, col in month_col.items():
        m = re.match(rf"^{year}[.\-](\d{{1,2}})$", label)
        mo = int(m.group(1))
        stock = rows[total_row][col]
        growth = rows[total_row][col + 1] if col + 1 < len(rows[total_row]) else None
        if stock is None:
            continue
        out.append({
            "month": f"{year}-{mo:02d}",
            "stock_tnyuan": float(stock),       # 万亿元
            "yoy_pct": float(growth) if growth is not None else None,
        })
    return out


# 增量表列名到英文键的映射（各年份中文表头基本一致）
FLOW_COL_MAP = {
    "社会融资规模增量": "total",
    "人民币贷款": "rmb_loans",
    "外币贷款（折合人民币）": "fx_loans",
    "委托贷款": "entrusted_loans",
    "信托贷款": "trust_loans",
    "未贴现银行承兑汇票": "undiscounted_ba",
    "企业债券": "corp_bonds",
    "政府债券": "gov_bonds",
    "非金融企业境内股票融资": "equity",
    "存款类金融机构资产支持证券": "abs",
    "贷款核销": "loan_writeoff",
}


def parse_flow(xlsx_path: Path, year: int) -> list[dict]:
    """增量表: 每行一个月份（YYYY.MM），各列为科目当月新增。

    注意: openpyxl 会把 "2025.10" 数字化为 float 2025.1，与 2025.01 冲突。
    因此按 **行序** 分配月份 (第 N 个数据行 = 第 N 月)，比字面解析更稳。
    """
    wb = load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = [[_clean(c) for c in row] for row in ws.iter_rows(values_only=True)]

    # 找到中文表头行（其一格为"社会融资规模增量"）
    hdr_idx = None
    for i, row in enumerate(rows):
        if any(str(c) == "社会融资规模增量" for c in row if c is not None):
            hdr_idx = i
            break
    if hdr_idx is None:
        return []

    header = [str(c) if c is not None else "" for c in rows[hdr_idx]]
    # 列名 → 列下标
    col_of: dict[str, int] = {}
    for zh, key in FLOW_COL_MAP.items():
        for j, h in enumerate(header):
            if h == zh:
                col_of[key] = j
                break

    out: list[dict] = []
    ordinal = 0
    for row in rows[hdr_idx + 1 :]:
        if not row:
            continue
        first = row[0]
        if first is None:
            continue
        s = str(first).strip()
        # 只接受形如 "2025.01" / "2025.1" / "2025-01" 起始的数据行
        if not re.match(rf"^{year}[.\-]\d+$", s):
            continue
        ordinal += 1
        if ordinal > 12:
            break  # 只取当年 12 个月
        rec = {"month": f"{year}-{ordinal:02d}"}
        for key, j in col_of.items():
            v = row[j] if j < len(row) else None
            rec[key] = float(v) if isinstance(v, (int, float)) else None
        # 未披露的占位行 (2026 后半年) 跳过
        if rec.get("total") is None:
            continue
        out.append(rec)
    return out


# ---------- 主流程 ----------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="强制重新下载所有 XLSX")
    ap.add_argument(
        "--only",
        type=int,
        nargs="*",
        help="只处理这些年份（例如 --only 2025 2026）",
    )
    args = ap.parse_args()

    years = args.only or sorted(YEAR_INDEX.keys())
    all_stock: list[dict] = []
    all_flow: list[dict] = []

    for year in years:
        print(f"[{year}]")
        try:
            sect = find_tsf_section_url(BASE + YEAR_INDEX[year])
        except Exception as e:
            print(f"    !! index fetch failed: {e}")
            continue
        if not sect:
            print("    !! 未找到「社会融资规模」子栏目")
            continue
        try:
            (stock_url, stock_ext), (flow_url, flow_ext) = find_attachment_pair(sect)
        except Exception as e:
            print(f"    !! subsection parse failed: {e}")
            continue

        if stock_url:
            try:
                p = cache_attachment(year, "stock", stock_url, stock_ext, args.refresh)
                rows = parse_stock(p, year) if stock_ext == "xlsx" else parse_stock_htm(p, year)
                if not rows:
                    print("    !! stock rows empty")
                all_stock.extend(rows)
            except Exception as e:
                print(f"    !! stock failed: {e}")
        else:
            print("    (no stock attachment)")

        if flow_url:
            try:
                p = cache_attachment(year, "flow", flow_url, flow_ext, args.refresh)
                rows = parse_flow(p, year) if flow_ext == "xlsx" else parse_flow_htm(p, year)
                if not rows:
                    print("    !! flow rows empty")
                all_flow.extend(rows)
            except Exception as e:
                print(f"    !! flow failed: {e}")
        else:
            print("    (no flow attachment)")

    all_stock.sort(key=lambda r: r["month"])
    all_flow.sort(key=lambda r: r["month"])

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    (TABLES_DIR / "tsf_pboc_stock.json").write_text(
        json.dumps(
            {
                "source": "PBoC 调查统计司 · 社会融资规模存量统计表 (各年度 XLSX 聚合)",
                "unit": "万亿元人民币",
                "yoy_unit": "%",
                "data": all_stock,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (TABLES_DIR / "tsf_pboc_flow.json").write_text(
        json.dumps(
            {
                "source": "PBoC 调查统计司 · 社会融资规模增量统计表 (各年度 XLSX 聚合)",
                "unit": "亿元人民币",
                "columns": FLOW_COL_MAP,
                "data": all_flow,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ stock: {len(all_stock)} 月")
    print(f"→ flow:  {len(all_flow)} 月")


if __name__ == "__main__":
    main()
