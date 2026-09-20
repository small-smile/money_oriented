#!/usr/bin/env python3
"""校验 data/tables/telecom_00941_*.json 三份表，并打印字段覆盖与口径自检结果。

中国移动详情页（frontend/src/views/company/cmcc/*.vue）直接 fetch 这三份表，没有构建步骤，
所以「表对不对」是唯一需要把关的地方。本脚本做四件事：

1. JSON 能不能解析、年份键是否连续；
2. 每年 mixLayers 列出的各层相加，与 mixBase 差多少（差额即页面上那条灰斜线「未单列」，
   本来就允许有，但如果出现负数或异常大的差额，说明层选错了或口径混用了）；
3. 关键字段的覆盖区间与区间内缺口——「断点」是真没披露还是漏补数，看这一段就知道；
4. 运营指标的单位量级抽查（客户数是不是亿户、DOU 是不是 GB），防止折算漏乘。

用法：python3 data/extract/check_cmcc_tables.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "data" / "tables"
PARTS = {
    "annual": "telecom_00941_annual.json",
    "operating": "telecom_00941_operating.json",
    "profile": "telecom_00941_profile.json",
}


def load():
    out = {}
    for key, fname in PARTS.items():
        path = TABLES / fname
        with open(path, encoding="utf-8") as f:
            out[key] = json.load(f)
        print(f"  {fname:<38} {path.stat().st_size / 1024:6.1f} KB  解析通过")
    return out


def check_years(dic, label):
    ys = sorted(int(y) for y in dic)
    holes = [y for y in range(ys[0], ys[-1] + 1) if y not in ys]
    print(f"  {label}: {ys[0]}–{ys[-1]}  {len(ys)} 年" + (f"  缺年份 {holes}" if holes else "  年份连续"))


def check_mix(ann):
    print("\n—— 收入拆分自检（mixLayers 相加 vs mixBase）——")
    bad = 0
    for y in sorted(ann):
        r = ann[y]
        base = r.get("mixBase")
        layers = r.get("mixLayers") or []
        if base is None or not layers:
            print(f"  {y}  未定义 mixBase/mixLayers，页面会退到营运收入做分母")
            continue
        s = sum(r[f] for f in layers if r.get(f) is not None)
        diff = base - s
        pct = diff / base * 100
        flag = ""
        if diff < 0:
            flag = "  ← 负残余！层选重了或口径混用"
            bad += 1
        elif pct > 12:
            flag = "  ← 残余偏大，确认是否漏了一层"
        print(f"  {y}  mixBase {base:>9,}  层合计 {s:>9,}  未单列 {diff:>8,} ({pct:5.1f}%){flag}")
    print(f"  结论：{'全部通过' if bad == 0 else str(bad) + ' 年出现负残余，必须修'}")


def coverage(dic, fields, label):
    print(f"\n—— {label} 字段覆盖 ——")
    ys = sorted(dic)
    for fld in fields:
        got = [y for y in ys if dic[y].get(fld) is not None]
        if not got:
            print(f"  {fld:<22} 无任何年份披露")
            continue
        inner = [y for y in ys if got[0] < y < got[-1] and dic[y].get(fld) is None]
        gap = "，区间内缺 " + ",".join(inner) if inner else ""
        tail = "，" + str(int(got[-1]) + 1) + " 年起停止披露" if got[-1] != ys[-1] else ""
        print(f"  {fld:<22} {got[0]}–{got[-1]}  {len(got):2d} 年{gap}{tail}")


def check_units(ops):
    print("\n—— 运营指标量级抽查 ——")
    last = max(ops)
    r = ops[last]
    checks = [
        ("mobileSubs", r.get("mobileSubs"), 5, 15, "亿户"),
        ("dou", r.get("dou"), 1, 100, "GB/户/月"),
        ("arpu", r.get("arpu"), 20, 200, "元/户/月"),
        ("mou", r.get("mou"), 100, 600, "分钟/户/月"),
        ("iotConnections", r.get("iotConnections"), 1, 100, "亿"),
    ]
    for name, val, lo, hi, unit in checks:
        if val is None:
            print(f"  {last} {name:<16} 未披露")
        else:
            ok = lo <= val <= hi
            print(f"  {last} {name:<16} {val:>8} {unit}  {'量级正常' if ok else '← 量级异常，检查折算'}")


def main():
    print("读取数据表：")
    data = load()
    ann = data["annual"]["annual"]
    ops = data["operating"]["annual"]
    prof = data["profile"]

    print("\n—— 年份范围 ——")
    check_years(ann, "annual   ")
    check_years(ops, "operating")
    print(f"  profile: 里程碑 {len(prof['milestones'])} 条，"
          f"股权明细 {len(prof['shareholding']['breakdown'])} 项，"
          f"风险 {len(prof['risks'])} 条")

    check_mix(ann)
    coverage(ann, ["totalRevenue", "serviceRevenue", "otherRevenue", "voiceRevenue", "smsRevenue",
                   "dataRevenue", "broadbandRevenue", "appInfoRevenue", "vasRevenue",
                   "dataBusinessRevenue", "ebitda", "opProfit", "netProfit", "eps", "capex",
                   "ocf", "fcf", "opexTotal", "networkOpex", "dividendTotal", "payoutRatio",
                   "marketC", "digitalRevenue"], "annual")
    coverage(ops, ["mobileSubs", "netAddSubs", "subs3G", "subs4G", "subs5G", "subs5GPackage",
                   "mou", "dou", "arpu", "broadbandSubs", "homeBroadbandSubs", "gigabitSubs",
                   "homeArpu", "govEntSubs", "iotConnections", "base5G", "idcRacks", "employees",
                   "totalMinutes", "smsVolume", "totalDataTraffic"], "operating")
    check_units(ops)

    # 页面上会用到的几个「主线」结论，顺手算出来核对文案是否与数据一致
    print("\n—— 主线结论自检 ——")
    mou = {y: ops[y]["mou"] for y in ops if ops[y].get("mou") is not None}
    peak_mou = max(mou, key=lambda y: mou[y])
    print(f"  MOU 峰值 {peak_mou} 年 {mou[peak_mou]} 分钟 → {max(mou)} 年 {mou[max(mou)]} 分钟")
    dou = {y: ops[y]["dou"] for y in ops if ops[y].get("dou") is not None}
    print(f"  DOU {min(dou)} 年 {dou[min(dou)]} GB → {max(dou)} 年 {dou[max(dou)]} GB")
    voice = {y: ann[y]["voiceRevenue"] for y in ann if ann[y].get("voiceRevenue") is not None}
    pv = max(voice, key=lambda y: voice[y])
    print(f"  语音收入峰值 {pv} 年 {voice[pv]:,} 百万元 → {max(voice)} 年 {voice[max(voice)]:,} 百万元")
    dat = {y: ann[y]["dataRevenue"] for y in ann if ann[y].get("dataRevenue") is not None}
    pd_ = max(dat, key=lambda y: dat[y])
    print(f"  无线上网收入峰值 {pd_} 年 {dat[pd_]:,} 百万元 → {max(dat)} 年 {dat[max(dat)]:,} 百万元")
    cross = [y for y in sorted(ann) if ann[y].get("dataRevenue") is not None
             and ann[y].get("voiceRevenue") is not None and ann[y]["dataRevenue"] > ann[y]["voiceRevenue"]]
    if cross:
        print(f"  无线上网收入首次超过语音收入：{cross[0]} 年")


if __name__ == "__main__":
    main()
