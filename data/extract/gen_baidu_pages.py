#!/usr/bin/env python3
"""把 data/tables/tech_09888_*.json 打包成 frontend/src/views/company/baidu/data.js

百度只有一家公司，没必要像银行页那样按 ?code= 走 /api 接口：四份表原样打包成一个
`window.BAIDU` 全局对象 + 模块导出，Vue 各页与 charts.js 直接 import，
页面里不手抄任何数字（比例一律在 JS 里由股数算），改数只需重跑本脚本。
源表原文存 MySQL json_file 表（经 backend/jsonstore.py 按原文件路径读），data.js 照旧写盘。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend import jsonstore  # noqa: E402  JSON 表原文在 MySQL json_file 表，按原文件路径取

TABLES = ROOT / "data" / "tables"
OUT = ROOT / "frontend" / "src" / "views" / "company" / "baidu" / "data.js"

PARTS = {
    "annual": "tech_09888_annual.json",       # SEC XBRL 派生的年度财务序列
    "segments": "tech_09888_segments_manual.json",
    "holders": "tech_09888_holders_manual.json",
    "profile": "tech_09888_profile_manual.json",
}


def main() -> None:
    payload = {}
    for key, fname in PARTS.items():
        payload[key] = jsonstore.read(TABLES / fname)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 本文件由 data/extract/gen_baidu_pages.py 生成，请勿手改。\n")
        f.write(" * 源表：" + "、".join(PARTS.values()) + " */\n")
        f.write("window.BAIDU = " + body + ";\n")
        f.write("\n/* 供 Vue 各页与 charts.js import：window.BAIDU 已在上方逐字设置，"
                "此处仅追加模块导出，数据本体一字未改。 */\n")
        f.write("export default window.BAIDU;\n")
        f.write("export const BAIDU = window.BAIDU;\n")

    print(f"写出 {OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1024:.1f} KB")
    ann = payload["annual"]["annual"]
    print(f"  annual   {min(ann)}–{max(ann)}  {len(ann)} 年 × {len(ann[max(ann)])} 字段")
    seg = payload["segments"]["annual"]
    print(f"  segments {min(seg)}–{max(seg)}  {len(seg)} 年")
    print(f"  holders  as_of {payload['holders']['_meta']['as_of']}"
          f"  总股本 {payload['holders']['share_capital']['outstanding_as_of_2026_01_31']['total']:,}")
    print(f"  profile  里程碑 {len(payload['profile']['milestones'])} 条"
          f"  风险 {len(payload['profile']['risks'])} 条")


if __name__ == "__main__":
    main()
