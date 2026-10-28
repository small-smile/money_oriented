from backend import industry_db

# 三大运营商（通信）
TELECOM_PEERS = ["600941", "601728", "600050"]


def _telecom_ops_manual():
    """经营口径手工层（逐份年报原文读出的移动/5G/宽带用户数、ARPU、年报口径资本开支、云与产业数字化收入，
    财务接口没有这些字段）：读 MySQL telecom_operating 与 data_note，形状同 telecom_ops_manual.json。"""
    return industry_db.telecom_ops_manual()


def _telecom_segment_manual():
    """收入构成层（年报「营业收入和营业成本」附注里的收入分解表，三家科目体系不同，不可横比同名科目）：
    读 MySQL segment_revenue 与 data_note，形状同 telecom_segment_manual.json。"""
    return industry_db.telecom_segment_manual()


def _telecom_segment_labels(comp):
    """canon 字段 → 年报中文科目名。items 与 canon 是同序生成的两份 dict，按位置对齐即可。
    年份从新到旧遍历，让当前科目体系（联通 2017 年起）排在旧科目（legacy_*）前面。"""
    labels, order = {}, []
    for year in sorted(comp.get("annual") or {}, reverse=True):
        rec = comp["annual"][year]
        for canon, label in zip(rec.get("canon") or {}, rec.get("items") or {}):
            if canon not in labels:
                labels[canon] = label
                order.append(canon)
    return labels, order


def _attach_telecom_segments(code, payload):
    """收入构成挂成顶层 segments 块，不摊进 annual：三家科目集不同、联通 2017 年前后换过一套，
    平铺进年份记录会得到一张到处是空洞的宽表，前端反而要再猜哪些字段属于哪家。"""
    seg = _telecom_segment_manual()
    if not seg:
        return payload
    comp = (seg.get("companies") or {}).get(code)
    if not comp:
        return payload
    labels, order = _telecom_segment_labels(comp)
    payload["segments"] = {
        "source": seg.get("source"),
        "unit_note": seg.get("unit_note"),
        "caliber_note": seg.get("caliber_note"),
        "unit": "亿元",
        "labels": labels,
        "order": order,
        "annual": {y: r.get("canon") or {} for y, r in (comp.get("annual") or {}).items()},
    }
    return payload


def _merge_telecom(code, payload):
    """通信行业的手工层合并入口：经营口径（ops_）+ 年报收入构成（segments）。"""
    return _attach_telecom_segments(code, _merge_telecom_ops(code, payload))


def _merge_telecom_ops(code, payload):
    """把经营手工层并进 annual 的每一年（ops_ 前缀已在手工表里带好），
    并把口径说明挂到顶层 ops_meta。annual 里原有的接口字段不动，
    缺该年份记录（如手工层覆盖到上市前）就补一条只有 ops_* 的年份。"""
    ops = _telecom_ops_manual()
    if not ops:
        return payload
    comp = (ops.get("companies") or {}).get(code)
    if not comp:
        return payload
    annual = payload.setdefault("annual", {})
    for year, rec in (comp.get("annual") or {}).items():
        row = annual.setdefault(year, {})
        for k, v in rec.items():
            row["ops_" + k if not k.startswith("ops_") else k] = v
    payload["ops_meta"] = {
        "source": ops.get("source"),
        "unit_note": ops.get("unit_note"),
        "caliber_note": ops.get("caliber_note"),
        "years": comp.get("years"),
        "report_source": comp.get("report_source"),
        "breaks": comp.get("breaks"),
    }
    return payload
