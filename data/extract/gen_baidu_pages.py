#!/usr/bin/env python3
"""把 data/tables/tech_09888_*.json 打包成 dashboard/company/baidu/data.js

百度详情页（dashboard/company/baidu/*.html）不走 backend_python.py 的 /api 接口，
而是 <script src="data.js"> 直接读全局对象——这样 file:// 打开也能画图，不用起服务、
也不受 fetch 跨域限制。银行页那套 /api/company_charts 是因为一份 HTML 要按 ?code=
渲染上百家银行，百度只有一家，没必要。

四份表原样打包，页面里不手抄任何数字（比例一律在 JS 里由股数算），
改数只需重跑本脚本。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "data" / "tables"
OUT = ROOT / "dashboard" / "company" / "baidu" / "data.js"

PARTS = {
    "annual": "tech_09888_annual.json",       # SEC XBRL 派生的年度财务序列
    "segments": "tech_09888_segments_manual.json",
    "holders": "tech_09888_holders_manual.json",
    "profile": "tech_09888_profile_manual.json",
}


def main() -> None:
    payload = {}
    for key, fname in PARTS.items():
        with open(TABLES / fname, encoding="utf-8") as f:
            payload[key] = json.load(f)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 本文件由 data/extract/gen_baidu_pages.py 生成，请勿手改。\n")
        f.write(" * 源表：" + "、".join(PARTS.values()) + " */\n")
        f.write("window.BAIDU = " + body + ";\n")

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
