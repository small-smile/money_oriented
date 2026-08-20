"""把年报 PDF 转成 data/raw/<name>.txt，并在写盘前做「抽取健康度」体检。

背景：2026-08-19 发现中国人保 2025 年报（data/raw/annual_601319_2025.pdf）由 suwell pdf creator 生成，
全部阿拉伯数字被转成 Form XObject 矢量轮廓（页面内容流只有 m/l/c/re + 填充，没有 BT/Tj/TJ 文本算子），
pdftotext 抽出来的 txt 中文完好、数字全丢，字数看着正常，但**一个财务数字都没有**。
当时是逐项核对时才发现的，纯手工 pdftotext 没有任何信号提示这件事。

因此本脚本在 pdftotext 之后加三道守卫，任一不过就 raise 且**不写 .txt**（避免坏文件混进 data/raw/ 被当作可信原文）：
    1. 全局数字密度 digits/非空白字符 >= 2%  —— 实测 data/raw/ 下 113 份正常年报为 10.19%~29.80%，该坏文件 0.100%
    2. 至少 50% 的页（按 \\f 分页）数字密度 >= 1%   —— 防「只有目录页有数字、正文全丢」这类局部损坏
    3. 平均每页字符数 >= 500                        —— 防扫描版 / 纯图片 PDF（抽出来近乎空白）

数字密度的分母是非空白字符（含中文），年报正文表格密集，正常值远高于 2%；
2% 是把已知坏样本（0.100%）与已知好样本下界（10.19%，港股英文版年报）之间留两个数量级余量后取的下界。
注意口径：若分母改用含空白的全部字符，同一批文件的数值约为此处的一半（601318 2025 为 9.66% vs 本脚本 20.01%），
引用历史记录的数字时先确认分母。

矢量化数字这种 PDF 无论怎么重下都救不回来（东财镜像与官网副本字节相同，H 股版同样坏），
只能另做字形几何识别，产物按 <name>.ocr.txt 命名，不走本脚本。

用法：
    python data/extract/pdf_to_text.py data/raw/annual_601318_2025.pdf      # 转单个文件
    python data/extract/pdf_to_text.py data/raw/annual_601318_2025.pdf -f   # 体检不过也强行写盘
    python data/extract/pdf_to_text.py --audit                              # 体检 data/raw/ 下已有的全部 txt，不转换
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw"

MIN_DIGIT_RATIO = 0.02      # 全局数字密度下界
MIN_PAGE_RATIO = 0.01       # 单页数字密度下界
MIN_GOOD_PAGE_SHARE = 0.5   # 达到单页下界的页数占比
MIN_CHARS_PER_PAGE = 500    # 平均每页字符数下界


def digit_ratio(text: str) -> float:
    """数字密度 = 阿拉伯数字数 / 非空白字符数。空文本返回 0。"""
    chars = sum(1 for c in text if not c.isspace())
    if not chars:
        return 0.0
    return sum(1 for c in text if c.isdigit()) / chars


def health_check(text: str) -> tuple[bool, dict, list[str]]:
    """返回 (是否通过, 指标字典, 未通过项的说明列表)。"""
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()                      # pdftotext 末页后会多一个 \f
    n_pages = len(pages) or 1
    chars = sum(1 for c in text if not c.isspace())
    good_pages = sum(1 for p in pages if digit_ratio(p) >= MIN_PAGE_RATIO)

    stats = {
        "pages": n_pages,
        "chars": chars,
        "digit_ratio": digit_ratio(text),
        "good_page_share": good_pages / n_pages,
        "chars_per_page": chars / n_pages,
    }

    problems = []
    if stats["digit_ratio"] < MIN_DIGIT_RATIO:
        problems.append(
            f"全局数字密度 {stats['digit_ratio']:.3%} < {MIN_DIGIT_RATIO:.0%}"
            "（数字可能被矢量化或字体编码不可映射，中文正常也不能用）"
        )
    if stats["good_page_share"] < MIN_GOOD_PAGE_SHARE:
        problems.append(
            f"数字密度 >= {MIN_PAGE_RATIO:.0%} 的页仅占 {stats['good_page_share']:.1%}"
            f" < {MIN_GOOD_PAGE_SHARE:.0%}（局部损坏，表格页可能整段丢数字）"
        )
    if stats["chars_per_page"] < MIN_CHARS_PER_PAGE:
        problems.append(
            f"平均每页 {stats['chars_per_page']:.0f} 字符 < {MIN_CHARS_PER_PAGE}"
            "（疑似扫描版/图片型 PDF，无文本层）"
        )
    return not problems, stats, problems


def fmt(stats: dict) -> str:
    return (
        f"{stats['pages']} 页, 数字密度 {stats['digit_ratio']:.3%}, "
        f"合格页占比 {stats['good_page_share']:.1%}, 每页 {stats['chars_per_page']:.0f} 字符"
    )


def convert(pdf: Path, force: bool = False) -> Path:
    """pdftotext -layout 转同名 .txt，体检不过则 raise 且不写盘。"""
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    out = pdf.with_suffix(".txt")
    # 先输出到 stdout，体检通过后再落盘，避免坏文件留在 data/raw/
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True,
        check=True,
    )
    text = proc.stdout.decode("utf-8", errors="replace")

    ok, stats, problems = health_check(text)
    if not ok and not force:
        raise RuntimeError(
            f"{pdf.name} 文本抽取体检不通过（{fmt(stats)}）：\n  - "
            + "\n  - ".join(problems)
            + f"\n未写入 {out.name}。若确认要保留原样对照，加 -f 强制写盘；"
            "若是数字矢量化那类损坏，重下无用，须另做字形识别并存为 <name>.ocr.txt。"
        )
    out.write_text(text, encoding="utf-8")
    flag = "（体检未过，-f 强制写盘）" if not ok else ""
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"[ok] {shown}  {fmt(stats)} {flag}")
    return out


def audit() -> int:
    """体检 data/raw/ 下已有的全部 annual_*/prospectus_* txt，作为回归基线。返回不合格文件数。"""
    files = sorted(
        p for p in RAW.glob("*.txt")
        if p.name.startswith(("annual_", "prospectus_"))
    )
    bad = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        ok, stats, problems = health_check(text)
        mark = "ok  " if ok else "BAD "
        print(f"{mark}{p.name:<40} {fmt(stats)}")
        if not ok:
            bad.append((p.name, problems))
    print(f"\n共 {len(files)} 份, 不合格 {len(bad)} 份")
    for name, problems in bad:
        print(f"  {name}: " + "; ".join(problems))
    return len(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", nargs="*", help="待转换的 PDF 路径")
    ap.add_argument("-f", "--force", action="store_true", help="体检不过也写盘")
    ap.add_argument("--audit", action="store_true", help="只体检 data/raw/ 下已有 txt")
    args = ap.parse_args()

    if args.audit:
        audit()
        return 0
    if not args.pdf:
        ap.error("请给出 PDF 路径, 或用 --audit 体检已有 txt")

    failed = 0
    for name in args.pdf:
        try:
            convert(Path(name), force=args.force)
        except Exception as exc:      # noqa: BLE001 —— 逐个文件报错但不中断批量转换
            failed += 1
            print(f"[fail] {name}\n{exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
