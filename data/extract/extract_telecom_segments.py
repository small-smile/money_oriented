"""从本地已抽取的运营商 A 股年报原文里解析「营业收入和营业成本」附注的收入构成表。

三家的构成口径完全不同（也正是这张表的看点）：
    中国移动 600941：语音 / 短彩信 / 无线上网 / 有线宽带 / 应用及信息服务 / 其他 + 销售产品
    中国电信 601728：移动通信服务 / 固网及智慧家庭服务 / 产业数字化服务 / 其他 + 销售商品
    中国联通 600050：语音通话及月租费 / 增值服务 / 宽带及移动数据服务 / 数据及其他互联网应用
                     / 网间结算 / 电路及网元服务 / 其他 + 销售通信产品

每份年报同时给本年与上年两列，本脚本只取**本年列**（上年列是重述比较数，
按项目「同一指标只取一个来源」的做法不混用）。金额单位：移动年报为百万元、
电信与联通为元，脚本按量级归一成**亿元**。

输入：data/raw/annual_<code>_<year>.txt（由 fetch_telecom_reports.py 落盘）
输出：data/tables/telecom_segment_manual.json（经 backend/jsonstore.py 写）

用法：
    ./venv/bin/python data/extract/extract_telecom_segments.py            # 全部
    ./venv/bin/python data/extract/extract_telecom_segments.py 600941     # 只跑一家
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from backend import jsonstore  # noqa: E402  JSON 文件读写统一走 jsonstore

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "tables" / "telecom_segment_manual.json"

CODES = {
    "600941": "中国移动",
    "601728": "中国电信",
    "600050": "中国联通",
}

# 收入构成表的起始锚点（**不能**只用附注标题「营业收入和营业成本」定位：
# 该附注里营业收入与营业成本两张分解表并列，中国电信的成本分解表会先命中，
# 结果把折旧及摊销、人工成本当成收入科目）：
#   中国移动 / 中国联通：表头是「主营业务收入：」
#   中国电信：表头是「(a) 本集团营业收入分解如下：」
ANCHORS = ("本集团营业收入分解如下", "主营业务收入：")
# 一行 = 标签 + 1~2 个数字（可带千分位与小数），标签里不含数字开头
ROW_RE = re.compile(r"^\s*(?:其中：)?\s*([^\d\s][^\d]{1,28}?)\s{2,}"
                    r"(-?[\d,]+(?:\.\d+)?)\s*(?:\s(-?[\d,]+(?:\.\d+)?))?\s*$")
STOP_WORDS = ("本集团的收入主要", "收入确认", "本集团的绝大部分", "注：")
# 收入分解表里出现即视为跨到下一张表，立即停（防止把成本科目吃进来）
COST_WORDS = ("折旧及摊销", "人工成本", "运行维护", "营业成本")


def to_float(s: str) -> float:
    return float(s.replace(",", ""))


# 年报科目名 -> 归一键（同一家公司跨年偶有改名，页面按归一键取数）。
# 中国联通 2017 年起把「宽带、数据及互联网收入」拆成「宽带及移动数据服务」+
# 「数据及其他互联网应用收入」，并把「信息与通信技术服务收入等」并入后者，
# 这是一处**真实的口径重分类**，故 2015—2016 用 legacy_* 键单独存、不与 2017 年后混成一条。
CANON = {
    "600941": {
        "语音业务": "voice", "短彩信业务": "sms", "无线上网业务": "wireless_data",
        "有线宽带业务": "broadband", "应用及信息服务": "apps", "其他": "other_service",
        "销售产品收入及其他": "products", "合计": "total",
    },
    "601728": {
        "服务收入": "service_total", "移动通信服务收入": "mobile",
        "固网及智慧家庭服务收入": "fixed_home", "产业数字化服务收入": "dx",
        "其他服务收入": "other_service", "出售商品及其他收入": "products", "合计": "total",
    },
    "600050": {
        "语音通话及月租费": "voice", "增值服务": "vas",
        "宽带及移动数据服务": "broadband_data", "数据及其他互联网应用收入": "internet_apps",
        "网间结算收入": "interconnect", "电路及网元服务": "circuit",
        "电路及网元租赁": "circuit", "其他": "other_service",
        "销售通信产品": "products", "小计": "service_total", "合计": "total",
        # 2015—2016 的旧科目集
        "通话及月租费收入": "legacy_voice", "增值业务收入": "legacy_vas",
        "宽带、数据及互联网收入": "legacy_broadband_internet",
        "电路及网元租赁收入": "legacy_circuit",
        "信息与通信技术服务收入等": "legacy_ict",
        "销售通信产品收入": "products",
    },
}


def parse_note(path: Path) -> dict[str, float] | None:
    """返回 {科目: 本年金额（原始单位）}，含「小计/合计」行以便自检。"""
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    starts = [i for i, l in enumerate(lines) if any(a in l for a in ANCHORS)]
    for start in starts:
        rows: dict[str, float] = {}
        for line in lines[start:start + 45]:
            if any(w in line for w in COST_WORDS) and rows:
                break
            if any(w in line for w in STOP_WORDS) and rows:
                break
            m = ROW_RE.match(line)
            if not m:
                continue
            label = m.group(1).strip().replace(" ", "").replace("：", "")
            label = re.sub(r"\((?:[a-z]+|[ivx]+)\)$", "", label)   # 去掉 (i)/(ii)/(a) 之类脚注标号
            if not label or label in ("年度", "项目", "按商品或服务的种类", "主营业务收入"):
                continue
            rows[label] = to_float(m.group(2))
            if label == "合计":
                break
        # 一张有效的收入构成表至少有 4 个科目且带合计
        if len(rows) >= 4 and "合计" in rows:
            return rows
    return None


def normalize(code: str, rows: dict[str, float]) -> tuple[dict[str, float], str]:
    """按合计量级把金额归一成亿元。三家 2025 年营业收入都在 3,900—10,500 亿元区间，
    据此判断原始单位是百万元（移动）还是元（电信/联通）。"""
    total = rows.get("合计")
    if total is None:
        return {}, ""
    if total > 1e11:            # 元
        div, unit = 1e8, "元"
    elif total > 1e5:           # 百万元
        div, unit = 1e2, "百万元"
    else:                       # 亿元（少见）
        div, unit = 1.0, "亿元"
    return {k: round(v / div, 2) for k, v in rows.items()}, unit


def main() -> None:
    codes = sys.argv[1:] or list(CODES)
    out: dict = {
        "source": "上交所 A 股年度报告原文的「营业收入和营业成本」附注（data/raw/annual_<code>_<year>.txt），"
                  "由 data/extract/extract_telecom_segments.py 解析",
        "unit_note": "金额单位统一为亿元（原文移动为百万元、电信与联通为元，按合计量级归一）；"
                     "每年只取年报的本年列，不取上年比较列",
        "caliber_note": "三家的收入构成科目完全不同，不可跨公司对同名科目直接横比："
                        "移动按业务类型（语音/短彩信/无线上网/有线宽带/应用及信息服务）；"
                        "电信按服务板块（移动通信/固网及智慧家庭/产业数字化）；"
                        "联通按业务类型但切分更细（语音通话及月租费/增值服务/宽带及移动数据/"
                        "数据及其他互联网应用/网间结算/电路及网元服务）。"
                        "「小计」为主营业务收入，「合计」为营业收入（含销售终端等其他业务收入），"
                        "两者都保留以便自检：小计 + 其他业务收入 = 合计。",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "companies": {},
    }
    for code in codes:
        comp = {"name": CODES[code], "annual": {}}
        for path in sorted(RAW.glob(f"annual_{code}_*.txt")):
            year = path.stem.split("_")[-1]
            rows = parse_note(path)
            if not rows:
                print(f"[miss] {code} {year} 未找到收入构成附注")
                continue
            norm, unit = normalize(code, rows)
            if not norm:
                print(f"[miss] {code} {year} 附注缺合计行")
                continue
            canon = {}
            unknown = []
            for k, v in norm.items():
                key = CANON.get(code, {}).get(k)
                if key:
                    canon[key] = v
                else:
                    unknown.append(k)
            # 自检：各科目（不含小计/合计）加总应等于合计，差额 > 0.05 亿元就报出来
            parts = sum(v for k, v in canon.items()
                        if k not in ("total", "service_total"))
            diff = round(parts - canon.get("total", 0), 2)
            comp["annual"][year] = {
                "unit_src": unit, "items": norm, "canon": canon,
                "sum_check": diff,
            }
            flag = "" if abs(diff) <= 0.05 else f"  <== 加总差 {diff} 亿元"
            print(f"[ok] {code} {year} 单位 {unit} 合计 {norm['合计']} 亿元 "
                  f"科目 {len([k for k in norm if k not in ('小计', '合计')])} 项"
                  + (f" 未归一 {unknown}" if unknown else "") + flag)
        out["companies"][code] = comp
    jsonstore.write(OUT, out, ensure_ascii=False, indent=1)
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
