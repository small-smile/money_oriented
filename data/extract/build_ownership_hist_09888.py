#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从本地存档的百度 20-F（2005—2025 共 21 份）抽取的历年股权结构数据，落地为
data/extract/out/ownership_hist_09888.json（不落盘，原文写进 MySQL json_file 表，
经 backend/jsonstore.py 按原文件路径存取）。

数据来源：data/raw/20f_09888_<year>.htm / .txt（.htm 的 <table> 结构按列取数，
.txt 用于章节/脚注语义通读与行号锚点）。未联网、未使用第三方接口、未做任何推算；
凡自算值单独标注 is_calculated=true。

抽取辅助脚本（同目录）：
  dump_20f_ownership_tables.py    把 .htm 的实益拥有权表 + 脚注表 dump 成网格
  dump_20f_ownership_sections.py  截取 .txt 的 Item 6.E 章节正文与行号
  digest_20f_ownership.py         压缩上面两者的输出便于人工语义核对
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend import jsonstore  # noqa: E402  JSON 原文在 MySQL json_file 表，按原文件路径取

OUTDIR = os.path.join(ROOT, "data", "extract", "out")
OUTFILE = os.path.join(OUTDIR, "ownership_hist_09888.json")

# 仅沿用本地范本 data/tables/tech_09888_holders_manual.json 已给出的中文名，
# 其余一律 null（20-F 原文为英文，不自行翻译）。
ZH = {
    "Robin Yanhong Li": "李彦宏",
    "Melissa Ma": "马东敏",
    "Yuanqing Yang": "杨元庆",
    "Jixun Foo": "符绩勋",
    "Sandy Ran Xu": "许冉",
    "Xiaodan Liu": "刘晓丹",
    "Haijian He": "何海建",
    "BlackRock, Inc.": "贝莱德",
}

DO = "directors_officers"
PS = "principal_shareholders"
TT = "total"


def row(group, name, role, total=None, pct=None, ca=None, cb=None, vp=None,
        fn=(), star=False, note=None, pct_text=None):
    r = {
        "name_en": name,
        "name_zh": ZH.get(name),
        "group": group,
        "role": role,
        "class_a": ca,
        "class_b": cb,
        "total_ordinary": total,
        "pct_of_total_ordinary": pct,
        "pct_of_voting_power": vp,
        "star": star,
        "footnote_refs": list(fn),
    }
    if pct_text:
        r["pct_of_total_ordinary_original"] = pct_text
    if note:
        r["note"] = note
    return r


def star_row(group, name, role, fn=(), cb=None, note=None):
    """原文以 * 表示不足 1%：数值字段全部 null，star=True。cb=0 表示 B 类列原文为 —。"""
    return row(group, name, role, fn=fn, cb=cb, star=True,
               note=note or "原文该行各数值列均为 *（少于 1%），未披露具体股数")


YEARS = {}

LEGEND_LT1_PLAIN = {"*": "Less than 1%."}
LEGEND_LT1_TOTAL = {"*": "Less than 1% of our total outstanding shares."}
LEGEND_LT1_AB = {"*": "Less than 1% of our total outstanding Class A ordinary shares and Class B ordinary shares."}
LEGEND_LT1_ORD = {"*": "Less than 1% of our total outstanding ordinary shares."}
VOTING_DAGGER = (
    "† For each person and group included in this column, percentage of voting power is calculated by "
    "dividing the voting power beneficially owned by such person or group by the voting power of all of our "
    "Class A ordinary shares and Class B ordinary shares as a single class. Each holder of Class A ordinary "
    "shares is entitled to one vote per share and each holder of our Class B ordinary shares is entitled to "
    "10 votes per share..."
)

ADS_1_1 = "1 ADS = 1 Class A ordinary share（原文：\u201cADSs, each representing one Class A ordinary share\u201d）"
ADS_10_1 = ("10 ADSs = 1 Class A ordinary share（原文：ADS 比例于 2010-05-12 由 \u201c1 ADS representing 1 Class A "
            "ordinary share\u201d 改为 \u201c10 ADSs representing 1 Class A ordinary share\u201d，效果等同 10 拆 1 的 ADS 拆股）")
ADS_1_8 = ("1 ADS = 8 Class A ordinary shares（原文：\u201ceach ADS representing 8 Class A ordinary shares\u201d；"
           "与 2021-03-01 生效的 1 拆 80 股份拆细 Share Subdivision 同步，20-F 全文追溯调整）")

COLS_SINGLE = ["Shares Beneficially Owned — Number", "Shares Beneficially Owned — %"]
COLS_DUAL = ["Class A Ordinary Shares", "Class B Ordinary Shares", "Total Ordinary Shares",
             "% of Total Ordinary Shares", "% of Aggregate Voting Power†"]

NOTE_SINGLE_COL = (
    "该年 20-F 的实益拥有权表只有一栏合计口径（Shares Beneficially Owned: Number / %），"
    "并未按 Class A / Class B 分列，因此各行 class_a / class_b 记 null；"
    "但公司自 2005 年美国 IPO 起即为双重股权结构——原文表述：\u201cholders of Class A ordinary shares are entitled to "
    "one vote per share, while holders of Class B ordinary shares are entitled to 10 votes per share\u201d，"
    "分类股数只出现在百分比分母脚注里（见 basis_original）。"
)
NOTE_DUAL_COL = (
    "该年表格按 Class A / Class B / Total 三列分列披露，并单列 % of Aggregate Voting Power†（A 类每股 1 票、"
    "B 类每股 10 票，两类作为单一类别一起投票）。"
)


def Y(fy, filing, as_of, as_of_original, total, ca, cb, basis_original, structure_note,
      ads_ratio, columns, legend, rows, key_footnotes, anchors, wvr=None, notes=None):
    d = {
        "filing": filing,
        "as_of": as_of,
        "as_of_original": as_of_original,
        "total_ordinary_shares": total,
        "class_a": ca,
        "class_b": cb,
        "basis_original": basis_original,
        "structure_note": structure_note,
        "ads_ratio": ads_ratio,
        "table_columns_original": columns,
        "legend": legend,
        "rows": rows,
        "wvr_beneficiaries": wvr,
        "key_footnotes": key_footnotes,
        "anchors": anchors,
    }
    if notes:
        d["notes"] = notes
    YEARS[str(fy)] = d


# <<<YEARS>>>
Y(2005,
  "Form 20-F for fiscal year ended December 31, 2005（Baidu.com, Inc.）",
  "2006-03-31", "March 31, 2006",
  33181182, None, None,
  "脚注(2)：\u201cPercentage of beneficial ownership of each listed person is based on 33,181,182 ordinary shares "
  "of the company outstanding as of March 31, 2006, and the number of ordinary shares underlying options held by "
  "such person as of that date.\u201d 该年脚注未给出 Class A / Class B 分类股数。",
  NOTE_SINGLE_COL + " 另据该年合并资产负债表：截至 2005-12-31 已发行流通 Class A 9,460,426 股、Class B 23,485,336 股"
  "（口径日期与本表 2006-03-31 不同，未用于本表分母）。",
  ADS_1_1, COLS_SINGLE,
  {"< 0.1": "原文该行百分比直接印为 \u201c< 0.1\u201d %，该年表格未使用 * 号图例"},
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 7276775, 21.9, fn=["(3)"]),
   row(DO, "Greg Penner", "Independent Director", 2223603, 6.7, fn=["(4)"]),
   row(DO, "Jerry Jianguo Liu", "Chief Technology Officer", 300500, 0.9, fn=["(5)"]),
   row(DO, "Shawn Wang", "Chief Financial Officer", 270366, 0.8, fn=["(6)"]),
   row(DO, "David Hongbo Zhu", "Chief Operating Officer", 302726, 0.9, fn=["(7)"]),
   row(DO, "Dong Liang", "Vice President of Marketing", 104850, 0.3, fn=["(8)"]),
   row(DO, "James Ding", "Independent Director", 15000, None, fn=["(9)"], pct_text="< 0.1",
       note="原文百分比为 \u201c< 0.1\u201d%，非 * 号，故 star=false 而 pct 记 null"),
   row(DO, "William Decker", "Independent Director", 20000, None, fn=["(10)"], pct_text="< 0.1",
       note="原文百分比为 \u201c< 0.1\u201d%，非 * 号，故 star=false 而 pct 记 null"),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 8 人）",
       10513820, 31.7, fn=["(11)"]),
   row(PS, "Draper Fisher Jurvetson ePlanet Ventures L.P.", "5% 以上主要股东（早期风险投资基金）",
       5167870, 15.6, fn=["(12)"]),
   row(PS, "Peninsula Capital Fund I, LLC", "5% 以上主要股东（Greg Penner 为唯一管理人）",
       2164603, 6.5, fn=["(13)"])],
  {"robin_li": {
      "footnote": "(3)",
      "components": [
          {"item": "本人直接持有", "class": "class_a", "shares": 33333, "desc": "33,333 Class A ordinary shares held by Mr. Li"},
          {"item": "60 日内可行使期权（原文未限定 60 日，为 assuming exercise of all outstanding options 口径）",
           "class": "class_a", "shares": 72050, "desc": "72,050 Class A ordinary shares issuable upon exercise of options held by Mr. Li"},
          {"item": "限制性股份", "class": "class_a", "shares": 4725, "desc": "4,725 restricted shares held by Mr. Li"},
          {"item": "Handsome Reward Limited 持有的 B 类", "class": "class_b", "shares": 5490000,
           "desc": "5,490,000 Class B ordinary shares held by Handsome Reward Limited, a company wholly owned and controlled by Mr. Li"},
          {"item": "配偶马东敏持有的 B 类（该年计入李彦宏行，但其声明放弃实益拥有权）",
           "class": "class_b", "shares": 1676667,
           "desc": "1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife. Mr. Li disclaims beneficial ownership of the shares held by his wife."}],
      "sum_check": {"sum": 7276775, "table_value": 7276775, "match": True, "is_calculated": True,
                    "note": "五项相加=表内 7,276,775，自算校验一致"},
      "esop_broker_ads": None,
      "irrevocable_proxy_shares": None},
   "institutions": [
       {"name_en": "Draper Fisher Jurvetson ePlanet Ventures L.P.", "footnote": "(12)",
        "detail": "含 Fund 持有的 5,078,223 股 B 类与 ePlanet GmbH 持有的 89,647 股 B 类；GP 为 Draper Fisher Jurvetson ePlanet Partners, Ltd.",
        "data_as_of": None, "source_filing": None},
       {"name_en": "Peninsula Capital Fund I, LLC", "footnote": "(13)",
        "detail": "2,164,603 股 B 类，Greg Penner 为唯一管理人并拥有全部投票与处置权，其声明除自身金钱利益外放弃实益拥有权",
        "data_as_of": None, "source_filing": None}]},
  {"htm_ownership_table_index": 176, "htm_footnote_tables": "177-191",
   "txt_section_line": 8373, "txt_basis_footnote_line": 8595,
   "section_title": "Item 6. DIRECTORS, SENIOR MANAGEMENT AND EMPLOYEES — E. Share Ownership"})

def li_fn(footnote, comps, table_value, excludes=None, voting=None, proxy=None):
    """李彦宏持股构成脚注的统一结构；sum_check 为自算校验值。"""
    s = sum(c["shares"] for c in comps if c.get("shares") and c.get("counted", True))
    d = {"footnote": footnote, "components": comps,
         "sum_check": {"sum": s, "table_value": table_value, "match": s == table_value,
                       "is_calculated": True, "note": "各项相加与表内数字比对，自算校验"}}
    if excludes is not None:
        d["excludes"] = excludes
    d["voting_power_stated_in_footnote"] = voting
    d["irrevocable_proxy_shares"] = proxy
    return d


def C(item, cls, shares, desc, counted=True):
    return {"item": item, "class": cls, "shares": shares, "desc": desc, "counted": counted}


Y(2006,
  "Form 20-F for fiscal year ended December 31, 2006（Baidu.com, Inc.）",
  "2007-03-31", "March 31, 2007",
  33828412, 22960385, 10868027,
  "脚注(2)：\u201cPercentage of beneficial ownership ... is based on 33,828,412 ordinary shares (consisting of "
  "22,960,385 Class A ordinary shares and 10,868,027 Class B ordinary shares) of the company outstanding as of "
  "March 31, 2007 ...\u201d",
  NOTE_SINGLE_COL, ADS_1_1, COLS_SINGLE, LEGEND_LT1_PLAIN,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 7294275, 21.5, fn=["(3)"]),
   row(DO, "Greg Penner", "Independent Director", 1717845, 5.1, fn=["(4)"]),
   row(DO, "Shawn Wang", "Chief Financial Officer", 164807, None, fn=["(5)"], star=True,
       note="原文股数为 164,807，百分比为 *（少于 1%）"),
   row(DO, "David Hongbo Zhu", "Chief Operating Officer", 114918, None, fn=["(6)"], star=True,
       note="原文股数为 114,918，百分比为 *"),
   row(DO, "William Chang", "Chief Scientist", 55970, None, fn=["(7)"], star=True,
       note="原文股数为 55,970，百分比为 *；表内姓名印为 William Chang（董事名单里为 William I. Chang）"),
   row(DO, "James Ding", "Independent Director", 15000, None, fn=["(8)"], star=True),
   row(DO, "William Decker", "Independent Director", 20000, None, fn=["(9)"], star=True),
   row(DO, "Asad Jamal", "Director", 263208, None, fn=["(10)"], star=True),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 8 人）",
       9646023, 28.2, fn=["(11)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 16.3, fn=["(12)"]),
   row(PS, "FMR Corp.", "5% 以上主要股东（机构投资者）", 2104361, 6.2, fn=["(13)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 35893, "35,893 Class A ordinary shares held by Mr. Li"),
      C("可行使期权", "class_a", 87050, "87,050 Class A ordinary shares issuable upon exercise of options held by Mr. Li"),
      C("限制性股份", "class_a", 4665, "4,665 restricted shares held by Mr. Li"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "5,490,000 Class B ordinary shares held by Handsome Reward Limited, a company wholly owned and controlled by Mr. Li"),
      C("配偶马东敏持有的 B 类（该年计入其行，但声明放弃实益拥有权）", "class_b", 1676667,
        "1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife; Mr. Li disclaims beneficial ownership")],
      7294275),
   "institutions": [
       {"name_en": "FMR Corp.", "footnote": "(13)",
        "detail": "1,755,536 股 A 类（以 ADS 形式，FMR Corp. 持有）+ 348,825 股 A 类（Fidelity International Limited 持有）",
        "data_as_of": None,
        "source_filing": "Amendment No. 3 to the Schedule 13G of FMR Corp. filed on February 14, 2007"}]},
  {"htm_ownership_table_index": 189, "htm_footnote_tables": "190-203",
   "txt_section_line": 8127, "txt_intro_line": 8130, "txt_basis_footnote_line": 8299,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2007,
  "Form 20-F for fiscal year ended December 31, 2007（Baidu.com, Inc.）",
  "2008-03-31", "March 31, 2008",
  34195183, 25300772, 8894411,
  "脚注(2)：\u201c... based on 34,195,183 ordinary shares (consisting of 25,300,772 Class A ordinary shares and "
  "8,894,411 Class B ordinary shares) of the company outstanding as of March 31, 2008 ...\u201d",
  NOTE_SINGLE_COL, ADS_1_1, COLS_SINGLE, LEGEND_LT1_PLAIN,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5617608, 16.4, fn=["(3)"]),
   row(DO, "Jennifer Li", "Chief Financial Officer", 10500, None, fn=["(4)"], star=True),
   row(DO, "Peng Ye", "Chief Operating Officer", 10500, None, fn=["(5)"], star=True),
   row(DO, "William Chang", "Chief Scientist", 33370, None, fn=["(6)"], star=True),
   row(DO, "William Decker", "Independent Director", 800, None, fn=["(7)"], star=True),
   row(DO, "James Ding", "Independent Director", 650, None, fn=["(8)"], star=True),
   row(DO, "Nobuyuki Idei", "Independent Director", 15000, None, fn=["(9)"], star=True),
   row(DO, "Greg Penner", "Independent Director", 1133853, 3.3, fn=["(10)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 8 人）",
       6822281, 19.9, fn=["(11)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 16.1, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A ordinary shares held by Mr. Li"),
      C("可行使期权", "class_a", 87050, "(ii) 87,050 Class A ordinary shares issuable upon exercise of options held by Mr. Li"),
      C("限制性股份", "class_a", 2893, "(iii) 2,893 restricted shares held by Mr. Li"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "(iv) 5,490,000 Class B ordinary shares held by Handsome Reward Limited, a company wholly-owned and controlled by Mr. Li")],
      5617608,
      excludes=[{"item": "配偶马东敏持有的 B 类（自该年起不再计入）", "class": "class_b", "shares": 1676667,
                 "desc": "Excludes 1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife, of which Mr. Li disclaims beneficial ownership"}]),
   "institutions": []},
  {"htm_ownership_table_index": 81, "htm_footnote_tables": "82-83",
   "txt_section_line": 10695, "txt_basis_footnote_line": 10920,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2008,
  "Form 20-F for fiscal year ended December 31, 2008（Baidu, Inc.）",
  "2009-03-31", "March 31, 2009",
  34552169, 25678183, 8873986,
  "脚注(2)：\u201c... based on 34,552,169 ordinary shares (consisting of 25,678,183 Class A ordinary shares and "
  "8,873,986 Class B ordinary shares) of the company outstanding as of March 31, 2009 ...\u201d（并计入该人 60 日内"
  "可归属的期权/限制性股份）",
  NOTE_SINGLE_COL, ADS_1_1, COLS_SINGLE, LEGEND_LT1_TOTAL,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5591224, 16.2, fn=["(3)"]),
   star_row(DO, "Jennifer Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "Peng Ye", "Chief Operating Officer", fn=["(5)"]),
   star_row(DO, "Yinan Li", "Chief Technology Officer", fn=["(6)"]),
   star_row(DO, "William Chang", "Chief Scientist", fn=["(7)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(8)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(9)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(10)"]),
   row(DO, "Greg Penner", "Independent Director", 1183637, 3.4, fn=["(11)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 9 人）",
       6805932, 19.7, fn=["(12)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.9, fn=["(13)"]),
   row(PS, "Morgan Stanley", "5% 以上主要股东（机构投资者）", 1765818, 5.1, fn=["(14)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A ordinary shares held by Mr. Li"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 34000,
        "(ii) 34,000 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("60 日内可行使期权", "class_a", 26666, "(iii) 26,666 Class A ordinary shares issuable upon exercise of options"),
      C("限制性股份", "class_a", 2893, "(iv) 2,893 restricted shares held by Mr. Li"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "(v) 5,490,000 Class B ordinary shares held by Handsome Reward Limited")],
      5591224,
      excludes=[{"item": "配偶马东敏持有的 B 类", "class": "class_b", "shares": 1676667,
                 "desc": "Excludes 1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Morgan Stanley", "footnote": "(14)",
        "detail": "1,765,818 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "two Schedule 13G/As filed by Morgan Stanley on February 17, 2009"}]},
  {"htm_ownership_table_index": 68, "htm_footnote_tables": "69-70",
   "txt_intro_line": 22186, "txt_basis_footnote_line": 22688,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2009,
  "Form 20-F for fiscal year ended December 31, 2009（Baidu, Inc.）",
  "2009-12-31", "December 31, 2009",
  34753292, 26298960, 8454332,
  "脚注(2)：\u201c... based on 34,753,292 ordinary shares (consisting of 26,298,960 Class A ordinary shares and "
  "8,454,332 Class B ordinary shares) of our company outstanding as of December 31, 2009 ...\u201d",
  NOTE_SINGLE_COL, ADS_1_1, COLS_SINGLE, LEGEND_LT1_TOTAL,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5601527, 16.1, fn=["(3)"]),
   star_row(DO, "Jennifer Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "William Chang", "Chief Scientist", fn=["(5)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(6)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(7)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(8)"]),
   row(DO, "Greg Penner", "Independent Director", 878333, 2.5, fn=["(9)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 7 人）",
       6503163, 18.7, fn=["(10)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.8, fn=["(11)"]),
   row(PS, "Marsico Capital Management, LLC", "5% 以上主要股东（机构投资者）", 2435495, 7.0, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A ordinary shares held by Mr. Li"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 35249,
        "(ii) 35,249 Class A Ordinary Shares in the form of ADSs held in the brokerage account of the administrator of our employee stock option program"),
      C("可行使期权", "class_a", 38613, "(iii) 38,613 Class A ordinary shares issuable upon exercise of options held by Mr. Li"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "(iv) 5,490,000 Class B ordinary shares held by Handsome Reward Limited")],
      5601527,
      excludes=[{"item": "配偶马东敏持有的 B 类", "class": "class_b", "shares": 1676667,
                 "desc": "Excludes 1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Marsico Capital Management, LLC", "footnote": "(12)",
        "detail": "2,435,495 股 A 类（以 ADS 形式）；百分比按 2009-12-31 总股本计算",
        "data_as_of": None,
        "source_filing": "Schedule 13G filed by Marsico Capital Management, LLC on February 10, 2010"}]},
  {"htm_ownership_table_index": 94, "htm_footnote_tables": "95-96",
   "txt_intro_line": 21613, "txt_basis_footnote_line": 22072,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2010,
  "Form 20-F for fiscal year ended December 31, 2010（Baidu, Inc.）",
  "2010-12-31", "December 31, 2010",
  34849672, 27045340, 7804332,
  "脚注(2)：\u201c... based on 34,849,672 ordinary shares (consisting of 27,045,340 Class A ordinary shares and "
  "7,804,332 Class B ordinary shares) of our company outstanding as of December 31, 2010 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_TOTAL,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5602679, 16.1, fn=["(3)"]),
   star_row(DO, "Jennifer Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "William Chang", "Chief Scientist", fn=["(5)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(6)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(7)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(8)"]),
   row(DO, "Greg Penner", "Independent Director", 350970, 1.0, fn=["(9)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 7 人）",
       5974881, 17.1, fn=["(10)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.8, fn=["(11)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2621936, 7.5, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A ordinary shares held by Mr. Li"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 35249,
        "(ii) 35,249 Class A Ordinary Shares in the form of ADSs held in the brokerage account of the administrator of our employee stock option program"),
      C("60 日内可行使期权", "class_a", 39000,
        "(iii) 39,000 Class A ordinary shares issuable upon exercise of options within 60 days after December 31, 2010"),
      C("60 日内可归属限制性股份", "class_a", 765,
        "(iv) 765 Class A Ordinary Shares issuable upon vesting of restricted shares within 60 days after December 31, 2010"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "(v) 5,490,000 Class B ordinary shares held by Handsome Reward Limited")],
      5602679,
      excludes=[{"item": "配偶马东敏持有的 B 类", "class": "class_b", "shares": 1676667,
                 "desc": "Excludes 1,676,667 Class B ordinary shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(12)",
        "detail": "2,621,936 股 A 类（以 ADS 形式）；百分比按 2010-12-31 总股本计算",
        "data_as_of": None,
        "source_filing": "Schedule 13G filed by Baillie Gifford & Co (Scottish partnership) on January 25, 2011"}]},
  {"htm_ownership_table_index": 97, "htm_footnote_tables": "98-99",
   "txt_intro_line": 24648, "txt_basis_footnote_line": 25079,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2011,
  "Form 20-F for fiscal year ended December 31, 2011（Baidu, Inc.）",
  "2011-12-31", "December 31, 2011",
  34914117, 27111117, 7803000,
  "脚注(2)：\u201c... based on 34,914,117 ordinary shares (consisting of 27,111,117 Class A ordinary shares and "
  "7,803,000 Class B ordinary shares) of our company outstanding as of December 31, 2011 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5580928, 16.0, fn=["(3)"]),
   star_row(DO, "Jennifer Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "William I. Chang", "Chief Scientist", fn=["(5)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(6)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(7)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(8)"]),
   star_row(DO, "Greg Penner", "Independent Director", fn=["(9)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 7 人）",
       5908278, 16.9, fn=["(10)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.7, fn=["(11)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2618149, 7.5, fn=["(12)"]),
   row(PS, "T. Rowe Price Associates, Inc.", "5% 以上主要股东（机构投资者）", 2423182, 6.9, fn=["(13)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 35249,
        "(ii) 35,249 Class A Ordinary Shares in the form of ADSs held in the brokerage account of the administrator of the issuer's employee stock option program"),
      C("已归属限制性 A 类股", "class_a", 1353, "(iii) 1,353 restricted Class A Ordinary Shares that have vested as of December 31, 2011"),
      C("60 日内可行使期权", "class_a", 16151, "(iv) 16,151 Class A Ordinary Shares issuable upon exercise of options within 60 days"),
      C("60 日内可归属限制性股份", "class_a", 510, "(v) 510 Class A Ordinary Shares issuable upon vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000,
        "(vi) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited, a British Virgin Islands company wholly owned and controlled by Mr. Li")],
      5580928,
      excludes=[{"item": "配偶马东敏持有的 B 类", "class": "class_b", "shares": 1676667,
                 "desc": "excludes 1,676,667 Class B Ordinary Shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(12)",
        "detail": "2,618,149 股 A 类（以 ADS 形式）；百分比按 2011-12-31 总股本计算", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 17, 2012"},
       {"name_en": "T. Rowe Price Associates, Inc.", "footnote": "(13)",
        "detail": "2,423,182 股 A 类（以 ADS 形式）；百分比按 2011-12-31 总股本计算", "data_as_of": None,
        "source_filing": "Schedule 13G filed on February 14, 2012"}]},
  {"htm_ownership_table_index": 180, "htm_footnote_tables": "181-194",
   "txt_section_line": 11183, "txt_intro_line": 11186, "txt_basis_footnote_line": 11400,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2012,
  "Form 20-F for fiscal year ended December 31, 2012（Baidu, Inc.）",
  "2012-12-31", "December 31, 2012",
  34965710, 27202710, 7763000,
  "脚注(2)：\u201c... based on 34,965,710 ordinary shares (consisting of 27,202,710 Class A ordinary shares and "
  "7,763,000 Class B ordinary shares) of our company outstanding as of December 31, 2012 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5581324, 16.0, fn=["(3)"]),
   star_row(DO, "Jennifer Xinzhe Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(5)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(6)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(7)"]),
   star_row(DO, "Greg Penner", "Independent Director", fn=["(8)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 6 人）",
       5889609, 16.8, fn=["(9)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.7, fn=["(10)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2824785, 8.1, fn=["(11)"]),
   row(PS, "T. Rowe Price Associates, Inc.", "5% 以上主要股东（机构投资者）", 1892572, 5.4, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 35249, "(ii) 35,249 Class A Ordinary Shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 2209, "(iii) 2,209 restricted Class A Ordinary Shares that have vested as of December 31, 2012"),
      C("60 日内可行使期权", "class_a", 15841, "(iv) 15,841 Class A Ordinary Shares issuable upon exercise of options within 60 days"),
      C("60 日内可归属限制性股份", "class_a", 360, "(v) 360 Class A Ordinary Shares issuable upon vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(vi) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5581324,
      excludes=[{"item": "配偶马东敏持有的 B 类", "class": "class_b", "shares": 1676667,
                 "desc": "excludes 1,676,667 Class B Ordinary Shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(11)",
        "detail": "2,824,785 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on February 7, 2013"},
       {"name_en": "T. Rowe Price Associates, Inc.", "footnote": "(12)",
        "detail": "1,892,572 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on February 11, 2013"}]},
  {"htm_ownership_table_index": 184, "htm_footnote_tables": "185-197",
   "txt_section_line": 11456, "txt_intro_line": 11458, "txt_basis_footnote_line": 11662,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2013,
  "Form 20-F for fiscal year ended December 31, 2013（Baidu, Inc.）",
  "2014-02-28", "February 28, 2014",
  35036446, 27518525, 7517921,
  "脚注(2)：\u201c... based on 35,036,446 ordinary shares (consisting of 27,518,525 Class A ordinary shares and "
  "7,517,921 Class B ordinary shares) of our company outstanding as of February 28, 2014 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5569715, 15.9, fn=["(3)"]),
   star_row(DO, "Jennifer Xinzhe Li", "Chief Financial Officer", fn=["(4)"]),
   star_row(DO, "William Decker", "Independent Director", fn=["(5)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(6)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(7)"]),
   star_row(DO, "Greg Penner", "Independent Director", fn=["(8)"]),
   row(DO, "Dejian Liu", "Director", 0, 0.0, fn=["(9)"],
       note="原文股数与百分比两栏均为 —，按规则记 0（不是 *）"),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 7 人）",
       5848829, 16.7, fn=["(10)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.7, fn=["(11)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2563477, 7.3, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 20460, "(ii) 20,460 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 2244, "(iii) 2,244 restricted Class A Ordinary Shares that have vested as of February 28, 2014"),
      C("60 日内可行使期权", "class_a", 19346, "(iv) 19,346 Class A Ordinary Shares issuable upon exercise of options within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5569715,
      excludes=[{"item": "配偶马东敏持有的 B 类（数量由 1,676,667 降至 1,576,667）", "class": "class_b", "shares": 1576667,
                 "desc": "excludes 1,576,667 Class B Ordinary Shares held by Melissa Ma, Mr. Li's wife"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(12)",
        "detail": "2,563,477 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 17, 2014"}]},
  {"htm_ownership_table_index": 206, "htm_footnote_tables": "207-219",
   "txt_section_line": 11672, "txt_intro_line": 11675, "txt_basis_footnote_line": 11877,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2014,
  "Form 20-F for fiscal year ended December 31, 2014（Baidu, Inc.）",
  "2015-02-28", "February 28, 2015",
  35119651, 27626730, 7492921,
  "脚注(2)：\u201c... based on 35,119,651 ordinary shares (consisting of 27,626,730 Class A ordinary shares and "
  "7,492,921 Class B ordinary shares) of our company outstanding as of February 28, 2015 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5570815, 15.9, fn=["(3)"]),
   star_row(DO, "Jennifer Xinzhe Li", "Chief Financial Officer"),
   star_row(DO, "Ya-Qin Zhang", "President"),
   star_row(DO, "Jing Wang", "Senior Vice President"),
   star_row(DO, "Hailong Xiang", "Senior Vice President"),
   star_row(DO, "Mingyuan Li", "Vice President"),
   star_row(DO, "William Decker", "Independent Director", fn=["(4)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(5)"]),
   star_row(DO, "Nobuyuki Idei", "Independent Director", fn=["(6)"]),
   star_row(DO, "Greg Penner", "Independent Director", fn=["(7)"]),
   row(DO, "Dejian Liu", "Director", 0, 0.0, fn=["(8)"], note="原文两栏均为 —，记 0"),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 11 人）",
       5838897, 16.6, fn=["(9)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.6, fn=["(10)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2256661, 6.4, fn=["(11)"]),
   row(PS, "T. Rowe Price Associates, Inc.", "5% 以上主要股东（机构投资者）", 1953701, 5.6, fn=["(12)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 20460, "(ii) 20,460 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 2466, "(iii) 2,466 restricted Class A Ordinary Shares that have vested as of February 28, 2015"),
      C("60 日内可行使期权", "class_a", 20224, "(iv) 20,224 Class A Ordinary Shares issuable upon exercise of options within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5570815,
      excludes=[{"item": "配偶马东敏持有的 A 类/B 类/ADS", "class": "mixed", "shares": None,
                 "desc": "excludes 25,000 Class A Ordinary Shares, 1,576,667 Class B Ordinary Shares and 35,000 Class A Ordinary Shares in the form of ADSs in her brokerage account, held by Melissa Ma"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(11)",
        "detail": "2,256,661 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 21, 2015"},
       {"name_en": "T. Rowe Price Associates, Inc.", "footnote": "(12)",
        "detail": "1,953,701 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on February 13, 2015"}]},
  {"htm_ownership_table_index": 232, "htm_footnote_tables": "233-246",
   "txt_section_line": 12028, "txt_intro_line": 12030, "txt_basis_footnote_line": 12301,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2015,
  "Form 20-F for fiscal year ended December 31, 2015（Baidu, Inc.）",
  "2016-02-29", "February 29, 2016",
  34625025, 27132104, 7492921,
  "脚注(2)：\u201c... based on 34,625,025 ordinary shares (consisting of 27,132,104 Class A ordinary shares and "
  "7,492,921 Class B ordinary shares) of our company outstanding as of February 29, 2016 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5590294, 16.1, fn=["(3)"]),
   star_row(DO, "Jennifer Xinzhe Li", "Chief Financial Officer"),
   star_row(DO, "Ya-Qin Zhang", "President"),
   star_row(DO, "Jing Wang", "Senior Vice President"),
   star_row(DO, "Hailong Xiang", "Senior Vice President"),
   star_row(DO, "Mingyuan Li", "Vice President"),
   star_row(DO, "William Decker", "Independent Director", fn=["(4)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(5)"]),
   star_row(DO, "Greg Penner", "Independent Director", fn=["(6)"]),
   star_row(DO, "Brent Callinicos", "Independent Director"),
   star_row(DO, "Yuanqing Yang", "Independent Director", fn=["(7)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 11 人）",
       5795101, 16.7, fn=["(8)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.9, fn=["(9)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2486003, 7.2, fn=["(10)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 20460, "(ii) 20,460 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 3781, "(iii) 3,781 restricted Class A Ordinary Shares that had vested as of February 29, 2016"),
      C("60 日内可行使期权及可归属限制性股份", "class_a", 38388,
        "(iv) 38,388 Class A Ordinary Shares issuable upon exercise of options and vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5590294,
      excludes=[{"item": "配偶马东敏持有的 A 类/B 类/ADS", "class": "mixed", "shares": None,
                 "desc": "excludes 25,000 Class A Ordinary Shares, 1,576,667 Class B Ordinary Shares and 17,000 Class A Ordinary Shares in the form of ADSs in her brokerage account, held by Melissa Ma"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(10)",
        "detail": "2,486,003 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 28, 2016"}]},
  {"htm_ownership_table_index": 208, "htm_footnote_tables": "209-220",
   "txt_section_line": 12667, "txt_intro_line": 12669, "txt_basis_footnote_line": 12930,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2016,
  "Form 20-F for fiscal year ended December 31, 2016（Baidu, Inc.）",
  "2017-02-28", "February 28, 2017",
  34748746, 27372492, 7376254,
  "脚注(2)：\u201c... based on 34,748,746 ordinary shares (consisting of 27,372,492 Class A ordinary shares and "
  "7,376,254 Class B ordinary shares) of our company outstanding as of February 28, 2017 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5607622, 16.1, fn=["(3)"]),
   star_row(DO, "Qi Lu", "Vice Chairman, Group President and Chief Operating Officer"),
   star_row(DO, "Jennifer Xinzhe Li", "Chief Financial Officer"),
   star_row(DO, "Ya-Qin Zhang", "President"),
   star_row(DO, "Hailong Xiang", "Senior Vice President"),
   star_row(DO, "James Ding", "Independent Director", fn=["(4)"]),
   star_row(DO, "Brent Callinicos", "Independent Director"),
   star_row(DO, "Yuanqing Yang", "Independent Director", fn=["(5)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 8 人）",
       5636595, 16.2, fn=["(6)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.8, fn=["(7)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2467540, 7.1, fn=["(8)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 21481, "(ii) 21,481 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 5097, "(iii) 5,097 restricted Class A Ordinary Shares that had vested as of February 28, 2017"),
      C("60 日内可行使期权及可归属限制性股份", "class_a", 53379,
        "(iv) 53,379 Class A Ordinary Shares issuable upon exercise of options and vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5607622,
      excludes=[{"item": "配偶马东敏持有的 B 类与 ADS", "class": "mixed", "shares": None,
                 "desc": "excludes 1,510,000 Class B Ordinary Shares and 49,600 Class A Ordinary Shares in the form of ADSs owned by Melissa Ma"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(8)",
        "detail": "2,467,540 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 13, 2017"}]},
  {"htm_ownership_table_index": 229, "htm_footnote_tables": "230-239",
   "txt_section_line": 12991, "txt_intro_line": 12993, "txt_basis_footnote_line": 13218,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2017,
  "Form 20-F for fiscal year ended December 31, 2017（Baidu, Inc.）",
  "2018-01-31", "January 31, 2018",
  34816248, 27614994, 7201254,
  "脚注(2)：\u201c... based on 34,816,248 ordinary shares (consisting of 27,614,994 Class A ordinary shares and "
  "7,201,254 Class B ordinary shares) of our company outstanding as of January 31, 2018 ...\u201d（该年起口径日期"
  "改为次年 1 月 31 日）",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman and Chief Executive Officer", 5615344, 16.1, fn=["(3)"]),
   star_row(DO, "Qi Lu", "Vice Chairman, Group President and Chief Operating Officer"),
   row(DO, "Herman Yu", "Chief Financial Officer", 0, 0.0,
       note="原文股数与百分比两栏均为 —，按规则记 0"),
   star_row(DO, "Lee Liu", "Senior Vice President"),
   star_row(DO, "Ya-Qin Zhang", "President, New Business"),
   star_row(DO, "Hailong Xiang", "Senior Vice President", fn=["(4)"]),
   star_row(DO, "James Ding", "Independent Director", fn=["(5)"]),
   star_row(DO, "Brent Callinicos", "Independent Director", fn=["(6)"]),
   star_row(DO, "Yuanqing Yang", "Independent Director", fn=["(7)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 9 人）",
       5671083, 16.3, fn=["(8)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.8, fn=["(9)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       2281972, 6.6, fn=["(10)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 21481, "(ii) 21,481 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 5980, "(iii) 5,980 restricted Class A Ordinary Shares that had vested as of January 31, 2018"),
      C("60 日内可行使期权及可归属限制性股份", "class_a", 60218,
        "(iv) 60,218 Class A Ordinary Shares issuable upon exercise of options and vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5615344,
      excludes=[{"item": "配偶马东敏持有的 B 类及其 60 日内可取得的 A 类", "class": "mixed", "shares": None,
                 "desc": "excludes 1,510,000 Class B Ordinary Shares owned by Melissa Ma, who also had the right to acquire 555 Class A Ordinary Shares upon vesting of RSUs within 60 days after January 31, 2018"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(10)",
        "detail": "2,281,972 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 10, 2018"}]},
  {"htm_ownership_table_index": 218, "htm_footnote_tables": "219-230",
   "txt_section_line": 12819, "txt_intro_line": 12821, "txt_basis_footnote_line": 13057,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2018,
  "Form 20-F for fiscal year ended December 31, 2018（Baidu, Inc.）",
  "2019-01-31", "January 31, 2019",
  34936512, 27735258, 7201254,
  "脚注(2)：\u201c... based on 34,936,512 ordinary shares (consisting of 27,735,258 Class A ordinary shares and "
  "7,201,254 Class B ordinary shares) of our company outstanding as of January 31, 2019 ...\u201d",
  NOTE_SINGLE_COL, ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       5654180, 16.1, fn=["(3)"]),
   star_row(DO, "Herman Yu", "Chief Financial Officer"),
   star_row(DO, "Ya-Qin Zhang", "President, New Business"),
   star_row(DO, "Hailong Xiang", "Senior Vice President", fn=["(4)"]),
   star_row(DO, "Lee Liu", "Senior Vice President"),
   star_row(DO, "Haifeng Wang", "Senior Vice President"),
   star_row(DO, "Qi Lu", "Vice Chairman of the Board of Directors"),
   star_row(DO, "James Ding", "Independent Director", fn=["(5)"]),
   star_row(DO, "Brent Callinicos", "Independent Director", fn=["(6)"]),
   star_row(DO, "Yuanqing Yang", "Independent Director", fn=["(7)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 10 人）",
       5704475, 16.3, fn=["(8)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.6, fn=["(9)"]),
   row(PS, "Baillie Gifford & Co (Scottish partnership)", "5% 以上主要股东（机构投资者）",
       1811319, 5.2, fn=["(10)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 21481, "(ii) 21,481 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 24193, "(iii) 24,193 restricted Class A Ordinary Shares that had vested as of January 31, 2019"),
      C("60 日内可行使期权及可归属限制性股份", "class_a", 80841,
        "(iv) 80,841 Class A Ordinary Shares issuable upon exercise of options and vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5654180,
      excludes=[{"item": "配偶马东敏持有的 B 类、ADS 及 60 日内可取得的 A 类", "class": "mixed", "shares": None,
                 "desc": "excludes 1,510,000 Class B Ordinary Shares owned by Melissa Ma, who also had 2,917 ADSs in the ESOP administrator's brokerage account and the right to acquire 870 Class A Ordinary Shares upon vesting of RSUs within 60 days after January 31, 2019"}]),
   "institutions": [
       {"name_en": "Baillie Gifford & Co (Scottish partnership)", "footnote": "(10)",
        "detail": "1,811,319 股 A 类（以 ADS 形式）", "data_as_of": None,
        "source_filing": "Schedule 13G filed on January 9, 2019"}]},
  {"htm_ownership_table_index": 224, "htm_footnote_tables": "225-236",
   "txt_section_line": 11414, "txt_intro_line": 11416, "txt_basis_footnote_line": 11662,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2019,
  "Form 20-F for fiscal year ended December 31, 2019（Baidu, Inc.）",
  "2020-01-31", "January 31, 2020",
  34584829, 27383575, 7201254,
  "脚注(2)：\u201c... based on 34,584,829 ordinary shares (consisting of 27,383,575 Class A ordinary shares and "
  "7,201,254 Class B ordinary shares) of our company outstanding as of January 31, 2020 ...\u201d",
  NOTE_SINGLE_COL + " 该年是最后一份未按 A/B 分列的 20-F；李彦宏投票权% 首次在脚注(3) 末句以文字披露（55.4%）。",
  ADS_10_1, COLS_SINGLE, LEGEND_LT1_AB,
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       5692798, 16.4, vp=55.4, fn=["(3)"],
       note="投票权 55.4% 不是表格列，而是脚注(3) 末句原文：\u201cThe voting power of the shares beneficially owned by "
            "Mr. Li represented 55.4% of the total outstanding voting power of our company as of January 31, 2020.\u201d"),
   star_row(DO, "Herman Yu", "Chief Financial Officer"),
   star_row(DO, "Dou Shen", "Executive Vice President"),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer"),
   star_row(DO, "Shanshan Cui", "Senior Vice President"),
   star_row(DO, "James Ding", "Independent Director", fn=["(4)"]),
   star_row(DO, "Brent Callinicos", "Independent Director", fn=["(5)"]),
   star_row(DO, "Yuanqing Yang", "Independent Director", fn=["(6)"]),
   star_row(DO, "Jixun Foo", "Independent Director", fn=["(7)"]),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 9 人）",
       5713741, 16.5, fn=["(8)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       5490000, 15.8, fn=["(9)"])],
  {"robin_li": li_fn("(3)", [
      C("本人在册直接持有", "class_a", 37665, "(i) 37,665 Class A Ordinary Shares directly held by Mr. Li on record"),
      C("ESOP 管理人经纪账户内以 ADS 形式持有", "class_a", 21897, "(ii) 21,897 Class A ordinary shares in the form of ADSs"),
      C("已归属限制性 A 类股", "class_a", 44668, "(iii) 44,668 restricted Class A Ordinary Shares that had vested as of January 31, 2020"),
      C("60 日内可行使期权及可归属限制性股份", "class_a", 98568,
        "(iv) 98,568 Class A Ordinary Shares issuable upon exercise of options and vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 持有的 B 类", "class_b", 5490000, "(v) 5,490,000 Class B Ordinary Shares held by Handsome Reward Limited")],
      5692798,
      excludes=[{"item": "配偶马东敏持有的 B 类、ADS 及 60 日内可取得的 A 类", "class": "mixed", "shares": None,
                 "desc": "excludes 1,510,000 Class B Ordinary Shares owned by Melissa Ma, who also had 8,722 ADSs in the ESOP administrator's brokerage account and the right to acquire 1,523 Class A Ordinary Shares upon vesting of RSUs within 60 days after January 31, 2020"}],
      voting="脚注(3) 原文：李彦宏实益拥有股份的投票权占公司全部流通投票权的 55.4%（截至 2020-01-31）"),
   "institutions": []},
  {"htm_ownership_table_index": 236, "htm_footnote_tables": "237-247",
   "txt_section_line": 18276, "txt_intro_line": 18287, "txt_basis_footnote_line": 18660,
   "section_title": "Item 6. — E. Share Ownership"})

Y(2020,
  "Form 20-F for fiscal year ended December 31, 2020（Baidu, Inc.，2021-03 报送，已追溯反映 1 拆 80 股份拆细）",
  "2021-03-03", "March 3, 2021",
  2685023744, 2125123424, 559900320,
  "正文：\u201cThe calculations in the table below are based on 2,685,023,744 ordinary shares, consisting of "
  "2,125,123,424 Class A ordinary shares and 559,900,320 Class B ordinary shares issued and outstanding as of "
  "March 3, 2021. For purpose of this table, each ADS representing eight Class A ordinary share ...\u201d",
  NOTE_DUAL_COL + " 这是首份按 Class A / Class B 分列并单列投票权% 的 20-F；股数为 1 拆 80 拆细后口径，"
  "与 2019 及以前年度的股数不可直接比较。该年 20-F 尚无港交所 WVR 受益人表（港股上市为 2021-03-23）。",
  ADS_1_8, COLS_DUAL,
  dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       457491280, 17.0, ca=18291280, cb=439200000, vp=57.0, fn=["(1)"]),
   star_row(DO, "Herman Yu", "Chief Financial Officer", cb=0),
   star_row(DO, "Dou Shen", "Executive Vice President", cb=0),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer", cb=0),
   star_row(DO, "Shanshan Cui", "Senior Vice President", cb=0),
   star_row(DO, "Victor Zhixiang Liang", "Senior Vice President", cb=0),
   star_row(DO, "James Ding", "Independent Director", cb=0),
   star_row(DO, "Brent Callinicos", "Independent Director", cb=0),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 10 人）",
       459409280, 17.1, ca=20209280, cb=439200000, vp=57.1),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       451889200, 16.8, ca=12689200, cb=439200000, vp=57.0, fn=["(2)"])],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 2232000,
        "(ii) 2,232,000 Class A ordinary shares in the form of ADSs held by Mr. Li in the brokerage account of the administrator of our employee stock option program"),
      C("本人 60 日内可行使期权", "class_a", 342320, "(iii) 342,320 Class A ordinary shares issuable to Mr. Li upon exercise of options within 60 days after March 3, 2021"),
      C("本人 60 日内可归属限制性股份", "class_a", 14560, "(iv) 14,560 Class A ordinary shares issuable to Mr. Li upon vesting of restricted shares within 60 days"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(v) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 5772720,
        "(vi) 5,772,720 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 6916480,
        "(vii) 6,916,480 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days after March 3, 2021")],
      457491280,
      excludes=[{"item": "配偶马东敏持有的 B 类与 ADS", "class": "mixed", "shares": 116600000,
                 "desc": "excludes 116,600,000 Class B ordinary shares owned by Ms. Melissa Ma, who also owned 50,000 ADSs, an additional 25,645 ADSs in the ESOP administrator's brokerage account and the right to acquire 575 ADSs within 60 days after March 3, 2021"}],
      voting="脚注(1) 末句：李彦宏实益拥有股份的投票权占公司全部流通投票权的 57.0%（截至 2021-03-03），与表内 57.0% 一致"),
   "institutions": []},
  {"htm_ownership_table_index": 298, "htm_footnote_tables": "299-303",
   "txt_section_line": 19070, "txt_intro_line": 19079, "txt_basis_line": 19112,
   "section_title": "Item 6. — E. Share Ownership"})

def w(name, ca, cb, pct, footnote=None):
    return {"name_en": name, "name_zh": ZH.get(name), "class_a": ca, "class_b": cb,
            "pct_of_voting_rights": pct, "footnote": footnote}


WVR_BASIS_FN = "On the basis that Class A ordinary shares entitle the shareholder to one vote per share and Class B ordinary shares entitle the shareholder to 10 votes per share."

Y(2021,
  "Form 20-F for fiscal year ended December 31, 2021（Baidu, Inc.，A 类普通股 2021-03-23 于港交所主板上市）",
  "2022-01-31", "January 31, 2022",
  2764404104, 2205103784, 559300320,
  "正文：\u201cThe calculations in the table below are based on 2,764,404,104 ordinary shares, consisting of "
  "2,205,103,784 Class A ordinary shares and 559,300,320 Class B ordinary shares issued and outstanding as of "
  "January 31, 2022.\u201d",
  NOTE_DUAL_COL + " 该年起 20-F 同时载有港交所《上市规则》第 19C 章要求的「加权投票权受益人（WVR beneficiaries）」表，"
  "口径与 SEC beneficial ownership 表不同（含非董事高管的马东敏等，不含机构投资者，只列投票权%）。",
  ADS_1_8, COLS_DUAL, dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       456864568, 16.5, ca=17664568, cb=439200000, vp=56.5, fn=["(1)"]),
   star_row(DO, "James Ding", "Independent Director", cb=0),
   star_row(DO, "Brent Callinicos", "Independent Director", cb=0),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   star_row(DO, "Rong Luo", "Chief Financial Officer", cb=0),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer", cb=0),
   star_row(DO, "Dou Shen", "Executive Vice President", cb=0),
   star_row(DO, "Herman Yu", "Chief Strategy Officer", cb=0),
   star_row(DO, "Victor Zhixiang Liang", "Senior Vice President", cb=0),
   star_row(DO, "Shanshan Cui", "Senior Vice President", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 11 人）",
       459725968, 16.6, ca=20525968, cb=439200000, vp=56.5),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       451582368, 16.3, ca=12382368, cb=439200000, vp=56.4, fn=["(2)"])],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 2269000, "(ii) 2,269,000 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(iii) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 5772720, "(iv) 5,772,720 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 6411008, "(v) 6,411,008 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days after January 31, 2022"),
      C("Handsome Reward Limited 60 日内可归属限制性股份", "class_a", 198640, "(vi) 198,640 Class A Ordinary Shares issuable to Handsome Reward Limited upon vesting of restricted shares within 60 days")],
      456864568,
      excludes=[{"item": "配偶马东敏持有的 B 类与 ADS", "class": "mixed", "shares": 116000000,
                 "desc": "excludes 116,000,000 Class B ordinary shares owned by Ms. Melissa Ma, who owned 27,333 ADSs in the ESOP administrator's brokerage account and the right to acquire 9,677 ADSs within 60 days after January 31, 2022"}],
      voting="脚注(1) 末句：李彦宏实益拥有股份的投票权占公司全部流通投票权的 56.5%（截至 2022-01-31）"),
   "institutions": [],
   "wvr_footnotes": [
       {"footnote": "(1)", "text": "Shimoda Holdings, LLC (\u201cShimoda\u201d) holds 500,000 ADSs and 4,000,000 Class B ordinary shares of our company. Shimoda is affiliated with an early stage investor of our company that invested in our company before its US IPO in 2005."},
       {"footnote": "(2)", "text": "Integrity Partners V, LLC (\u201cIntegrity\u201d) holds 100,320 Class B ordinary shares of our company and was not a record shareholder of any Class A ordinary shares as at January 31, 2022."},
       {"footnote": "(3)", "text": WVR_BASIS_FN}]},
  {"htm_ownership_table_index": 336, "htm_footnote_tables": "337-341",
   "htm_wvr_table_index": 344, "txt_section_line": 25208, "txt_intro_line": 25216,
   "txt_basis_line": 25249, "txt_wvr_line": 25891,
   "section_title": "Item 6. — E. Share Ownership / Weighted Voting Rights Structure"},
  wvr={"as_of": "2022-01-31", "as_of_original": "As at January 31, 2022",
       "columns_original": ["Number of Class A Ordinary Shares", "Number of Class B Ordinary Shares",
                            "Approximate percentage of voting rights(3)"],
       "rows": [w("Robin Yanhong Li", 17664568, 439200000, 56.5),
                w("Melissa Ma", 296080, 116000000, 14.9),
                w("Shimoda Holdings, LLC", 4000000, 4000000, 0.6, "(1)"),
                w("Integrity Partners V, LLC", 0, 100320, 0.0, "(2)"),
                w("Total", 18460648, 559300320, 72.0, "(3)")]})

Y(2022,
  "Form 20-F for fiscal year ended December 31, 2022（Baidu, Inc.）",
  "2023-01-31", "January 31, 2023",
  2796777776, 2255397456, 541380320,
  "正文：\u201cThe calculations in the table below are based on 2,796,777,776 ordinary shares, consisting of "
  "2,255,397,456 Class A ordinary shares and 541,380,320 Class B ordinary shares issued and outstanding as of "
  "January 31, 2023.\u201d",
  NOTE_DUAL_COL + " 该年首次出现「员工不可撤销投票代理」安排：8,037,128 股 A 类的投票权授予李彦宏，"
  "原文明确该等股份不计入其实益拥有股数（只影响投票权%）。",
  ADS_1_8, COLS_DUAL, dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       458158800, 16.3, ca=18958800, cb=439200000, vp=57.6, fn=["(1)", "(2)"]),
   star_row(DO, "James Ding", "Independent Director", cb=0),
   star_row(DO, "Brent Callinicos", "Independent Director", cb=0),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   star_row(DO, "Rong Luo", "Chief Financial Officer", cb=0),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer", cb=0),
   star_row(DO, "Dou Shen", "Executive Vice President", cb=0),
   star_row(DO, "Victor Zhixiang Liang", "Senior Vice President", cb=0),
   star_row(DO, "Shanshan Cui", "Senior Vice President", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 10 人）",
       462450800, 16.5, ca=23250800, cb=439200000, vp=57.6),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       451602016, 16.1, ca=12402016, cb=439200000, vp=57.4, fn=["(3)"]),
   row(PS, "BlackRock, Inc.", "5% 以上主要股东（机构投资者，ADS 实益持有人）",
       150331434, 5.4, ca=150331434, cb=0, vp=1.7, fn=["(4)"])],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 2725904, "(ii) 2,725,904 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("本人 60 日内可归属限制性股份", "class_a", 817680, "(iii) 817,680 Class A Ordinary Shares issuable to Mr. Li upon vesting of restricted shares within 60 days after January 31, 2023"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(iv) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 5971360, "(v) 5,971,360 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 6068640, "(vi) 6,068,640 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days"),
      C("Handsome Reward Limited 60 日内可归属限制性股份", "class_a", 362016, "(vii) 362,016 Class A Ordinary Shares issuable to Handsome Reward Limited upon vesting of restricted shares within 60 days")],
      458158800,
      excludes=[{"item": "配偶马东敏持有的 B 类与 ADS", "class": "mixed", "shares": 98080000,
                 "desc": "excludes 98,080,000 Class B ordinary shares, 36,015 ADSs in the ESOP administrator's brokerage account and the right to acquire 6,525 ADSs within 60 days after January 31, 2023, all owned by Ms. Melissa Ma"}],
      voting="脚注(2)：部分雇员近期就其持有的合计 8,037,128 股 A 类普通股向李彦宏授予投票代理，因此李彦宏所持投票权占"
             "公司全部流通投票权的 57.6%（截至 2023-01-31）；原文明确该等代理股份未计入表中其他列的实益拥有股数",
      proxy=8037128),
   "institutions": [
       {"name_en": "BlackRock, Inc.", "footnote": "(4)",
        "detail": "150,331,434 股 A 类（拥有唯一处置权）；投票权按其拥有唯一投票权的 133,259,677 股 A 类计算；"
                  "百分比按公司 2023-01-31 总股本并假设持股自 2022-12-31 未变计算",
        "data_as_of": "2022-12-31",
        "source_filing": "Schedule 13G filed by BlackRock, Inc. on February 1, 2023"}],
   "wvr_footnotes": [
       {"footnote": "(1)", "text": "To our knowledge, Shimoda Holdings, LLC holds 500,000 ADSs and 4,000,000 Class B ordinary shares of our company."},
       {"footnote": "(2)", "text": "To our knowledge, Integrity Partners V, LLC holds 100,320 Class B ordinary shares of our company and was not a record shareholder of any Class A ordinary shares as at January 31, 2023."},
       {"footnote": "(3)", "text": WVR_BASIS_FN}]},
  {"htm_ownership_table_index": 340, "htm_footnote_tables": "341-347",
   "htm_wvr_table_index": 350, "txt_section_line": 17077, "txt_intro_line": 17080,
   "txt_basis_line": 17100, "txt_wvr_line": 17661,
   "section_title": "Item 6. — E. Share Ownership / Weighted Voting Rights Structure"},
  wvr={"as_of": "2023-01-31", "as_of_original": "As at January 31, 2023",
       "columns_original": ["Number of Class A Ordinary Shares", "Number of Class B Ordinary Shares",
                            "Approximate percentage of voting rights(3)"],
       "rows": [w("Robin Yanhong Li", 18958800, 439200000, 57.6),
                w("Melissa Ma", 340320, 98080000, 12.8),
                w("Shimoda Holdings, LLC", 4000000, 4000000, 0.6, "(1)"),
                w("Integrity Partners V, LLC", 0, 100320, 0.0, "(2)"),
                w("Total", 23299120, 541380320, 71.0, "(3)")]})

Y(2023,
  "Form 20-F for fiscal year ended December 31, 2023（Baidu, Inc.）",
  "2024-01-31", "January 31, 2024",
  2805219752, 2280439432, 524780320,
  "正文：\u201cThe calculations in the table below are based on 2,805,219,752 ordinary shares, consisting of "
  "2,280,439,432 Class A ordinary shares and 524,780,320 Class B ordinary shares issued and outstanding as of "
  "January 31, 2024.\u201d",
  NOTE_DUAL_COL + " 该年起员工不可撤销投票代理股份（53,418,112 股 A 类）被直接计入李彦宏与董事高管合计行的"
  "实益拥有股数（与 FY2022 的处理不同），故其 A 类股数从 18,958,800 跳升至 72,882,496。",
  ADS_1_8, COLS_DUAL, dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       512082496, 18.2, ca=72882496, cb=439200000, vp=59.3, fn=["(1)"]),
   star_row(DO, "James Ding", "Independent Director", cb=0),
   star_row(DO, "Brent Callinicos", "Independent Director", cb=0),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   star_row(DO, "Sandy Ran Xu", "Independent Director", cb=0),
   star_row(DO, "Rong Luo", "Chief Financial Officer", cb=0),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer", cb=0),
   star_row(DO, "Dou Shen", "Executive Vice President", cb=0),
   star_row(DO, "Victor Zhixiang Liang", "Senior Vice President", cb=0),
   star_row(DO, "Shanshan Cui", "Senior Vice President", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 11 人）",
       517587112, 18.5, ca=78387112, cb=439200000, vp=59.3, fn=["(2)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       451964032, 16.1, ca=12764032, cb=439200000, vp=58.5, fn=["(3)"]),
   row(PS, "BlackRock, Inc.", "5% 以上主要股东（机构投资者，ADS 实益持有人）",
       128640168, 4.6, ca=128640168, cb=0, vp=1.5, fn=["(4)"],
       note="虽列于 Principal Shareholders，但按 2024-01-31 分母其占比已低于 5%（4.6%），系沿用 2023-12-31 的 13G/A 数据")],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 3146232, "(ii) 3,146,232 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("本人 60 日内可归属限制性股份", "class_a", 540920, "(iii) 540,920 Class A Ordinary Shares issuable to Mr. Li upon vesting of restricted shares within 60 days after January 31, 2024"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(iv) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 6333376, "(v) 6,333,376 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 6068640, "(vi) 6,068,640 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days"),
      C("Handsome Reward Limited 60 日内可归属限制性股份", "class_a", 362016, "(vii) 362,016 Class A Ordinary Shares issuable to Handsome Reward Limited upon vesting of restricted shares within 60 days"),
      C("员工授予李彦宏不可撤销投票代理的 A 类（以 ADS 形式持有）", "class_a", 53418112,
        "(viii) 53,418,112 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies as of January 31, 2024")],
      512082496,
      excludes=[{"item": "配偶马东敏持有的 A 类、B 类与 ADS", "class": "mixed", "shares": None,
                 "desc": "excludes 3,732,240 Class A ordinary shares, 85,480,000 Class B ordinary shares and 41,860 ADSs in the ESOP administrator's brokerage account, all owned by Ms. Melissa Ma"}],
      voting="WVR 表脚注(1)：因该等投票代理，李彦宏所持投票权占公司全部流通投票权的 59.3%（截至 2024-01-31）",
      proxy=53418112),
   "group_footnote": {"footnote": "(2)",
                      "text": "Includes 53,418,112 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Robin Yanhong Li irrevocable voting proxies as of January 31, 2024.",
                      "included_proxy_shares": 53418112},
   "institutions": [
       {"name_en": "BlackRock, Inc.", "footnote": "(4)",
        "detail": "128,640,168 股 A 类（唯一处置权）；投票权按其拥有唯一投票权的 116,610,874 股 A 类计算；"
                  "百分比按公司 2024-01-31 总股本并假设持股自 2023-12-31 未变计算",
        "data_as_of": "2023-12-31",
        "source_filing": "Schedule 13G/A filed by BlackRock, Inc. on February 1, 2024"}],
   "wvr_footnotes": [
       {"footnote": "(1)", "text": "Includes 53,418,112 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies ... As a result, the voting power held by Mr. Robin Yanhong Li represented 59.3% of the total outstanding voting power as of January 31, 2024."},
       {"footnote": "(2)", "text": "To our knowledge, Integrity Partners V, LLC holds 100,320 Class B ordinary shares and was not a record shareholder of any Class A ordinary shares as at January 31, 2024."},
       {"footnote": "(3)", "text": WVR_BASIS_FN}]},
  {"htm_ownership_table_index": 326, "htm_footnote_tables": "327-333",
   "htm_wvr_table_index": 336, "txt_section_line": 17166, "txt_intro_line": 17169,
   "txt_basis_line": 17189, "txt_wvr_line": 17770,
   "section_title": "Item 6. — E. Share Ownership / Weighted Voting Rights Structure"},
  wvr={"as_of": "2024-01-31", "as_of_original": "As at January 31, 2024",
       "columns_original": ["Number of Class A Ordinary Shares", "Number of Class B Ordinary Shares",
                            "Approximate percentage of voting rights(3)"],
       "rows": [w("Robin Yanhong Li", 72882496, 439200000, 59.3, "(1)"),
                w("Melissa Ma", 4067120, 85480000, 11.4),
                w("Integrity Partners V, LLC", 0, 100320, 0.0, "(2)"),
                w("Total", 76949616, 524780320, 70.7, "(3)")],
       "note": "该年起 Shimoda Holdings, LLC 不再出现在 WVR 受益人表中（其 4,000,000 股 B 类已不在表内）"})

Y(2024,
  "Form 20-F for fiscal year ended December 31, 2024（Baidu, Inc.）",
  "2025-01-31", "January 31, 2025",
  2750167168, 2225826848, 524340320,
  "正文：\u201cThe calculations in the table below are based on 2,750,167,168 ordinary shares, consisting of "
  "2,225,826,848 Class A ordinary shares and 524,340,320 Class B ordinary shares issued and outstanding as of "
  "January 31, 2025.\u201d",
  NOTE_DUAL_COL, ADS_1_8, COLS_DUAL, dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       526140856, 19.1, ca=86940856, cb=439200000, vp=59.9, fn=["(1)"]),
   star_row(DO, "James Ding", "Independent Director", cb=0),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   star_row(DO, "Sandy Ran Xu", "Independent Director", cb=0),
   star_row(DO, "Xiaodan Liu", "Independent Director", cb=0),
   star_row(DO, "Rong Luo", "Executive Vice President", cb=0),
   star_row(DO, "Haifeng Wang", "Chief Technology Officer", cb=0),
   star_row(DO, "Dou Shen", "Executive Vice President", cb=0),
   star_row(DO, "Victor Zhixiang Liang", "Senior Vice President", cb=0),
   star_row(DO, "Shanshan Cui", "Senior Vice President", cb=0),
   star_row(DO, "Junjie He", "Interim Chief Financial Officer", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 12 人）",
       532550288, 19.3, ca=93350288, cb=439200000, vp=60.0, fn=["(2)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       452474944, 16.4, ca=13274944, cb=439200000, vp=58.9, fn=["(3)"]),
   row(PS, "BlackRock, Inc.", "5% 以上主要股东（机构投资者，ADS 实益持有人）",
       128640168, 4.7, ca=128640168, cb=0, vp=1.6, fn=["(4)"],
       note="沿用 2023-12-31 的 13G/A 数据，按 2025-01-31 分母占比 4.7%")],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 3421504, "(ii) 3,421,504 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("本人 60 日内可归属限制性股份", "class_a", 211480, "(iii) 211,480 Class A Ordinary Shares issuable to Mr. Li upon vesting of restricted shares within 60 days after January 31, 2025"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(iv) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 7037488, "(v) 7,037,488 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 5875440, "(vi) 5,875,440 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days"),
      C("Handsome Reward Limited 60 日内可归属限制性股份", "class_a", 362016, "(vii) 362,016 Class A Ordinary Shares issuable to Handsome Reward Limited upon vesting of restricted shares within 60 days"),
      C("员工授予李彦宏不可撤销投票代理的 A 类（以 ADS 形式持有）", "class_a", 67019728,
        "(viii) 67,019,728 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies as of January 31, 2025")],
      526140856,
      excludes=[{"item": "配偶马东敏持有的 A 类、B 类与 ADS", "class": "mixed", "shares": None,
                 "desc": "excludes 3,732,240 Class A ordinary shares, 85,040,000 Class B ordinary shares and 44,262 ADSs in the ESOP administrator's brokerage account, all owned by Ms. Melissa Ma"}],
      voting="WVR 表脚注(1)：因该等投票代理，李彦宏所持投票权占公司全部流通投票权的 59.9%（截至 2025-01-31）",
      proxy=67019728),
   "group_footnote": {"footnote": "(2)",
                      "text": "Includes 67,019,728 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Robin Yanhong Li irrevocable voting proxies as of January 31, 2025.",
                      "included_proxy_shares": 67019728},
   "institutions": [
       {"name_en": "BlackRock, Inc.", "footnote": "(4)",
        "detail": "128,640,168 股 A 类（唯一处置权）；投票权按 116,610,874 股 A 类（唯一投票权）计算；"
                  "百分比按公司 2025-01-31 总股本并假设持股自 2023-12-31 未变计算",
        "data_as_of": "2023-12-31",
        "source_filing": "Schedule 13G/A filed by BlackRock, Inc. on February 1, 2024"}],
   "wvr_footnotes": [
       {"footnote": "(1)", "text": "Includes 67,019,728 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies ... As a result, the voting power held by Mr. Robin Yanhong Li represented 59.9% of the total outstanding voting power as of January 31, 2025."},
       {"footnote": "(2)", "text": "To our knowledge, Integrity Partners V, LLC holds 100,320 Class B ordinary shares and was not a record shareholder of any Class A ordinary shares as at January 31, 2025."},
       {"footnote": "(3)", "text": WVR_BASIS_FN}]},
  {"htm_ownership_table_index": 337, "htm_footnote_tables": "338-344",
   "htm_wvr_table_index": 347, "txt_section_line": 17771, "txt_intro_line": 17774,
   "txt_basis_line": 17794, "txt_wvr_line": 18402,
   "section_title": "Item 6. — E. Share Ownership / Weighted Voting Rights Structure"},
  wvr={"as_of": "2025-01-31", "as_of_original": "As at January 31, 2025",
       "columns_original": ["Number of Class A Ordinary Shares", "Number of Class B Ordinary Shares",
                            "Approximate percentage of voting rights(3)"],
       "rows": [w("Robin Yanhong Li", 86940856, 439200000, 59.9, "(1)"),
                w("Melissa Ma", 4086336, 85040000, 11.4),
                w("Integrity Partners V, LLC", 0, 100320, 0.0, "(2)"),
                w("Total", 91027192, 524340320, 71.4, "(3)")]})

Y(2025,
  "Form 20-F for fiscal year ended December 31, 2025（Baidu, Inc.，2026-03-17 报送）",
  "2026-01-31", "January 31, 2026",
  2722021272, 2198000952, 524020320,
  "正文：\u201cThe calculations in the table below are based on 2,722,021,272 ordinary shares, consisting of "
  "2,198,000,952 Class A ordinary shares and 524,020,320 Class B ordinary shares issued and outstanding as of "
  "January 31, 2026.\u201d",
  NOTE_DUAL_COL, ADS_1_8, COLS_DUAL, dict(LEGEND_LT1_ORD, **{"†": VOTING_DAGGER}),
  [row(DO, "Robin Yanhong Li", "Chairman of the Board of Directors and Chief Executive Officer",
       507314224, 18.6, ca=68114224, cb=439200000, vp=59.9, fn=["(1)"]),
   star_row(DO, "Yuanqing Yang", "Independent Director", cb=0),
   star_row(DO, "Jixun Foo", "Independent Director", cb=0),
   star_row(DO, "Sandy Ran Xu", "Independent Director", cb=0),
   star_row(DO, "Xiaodan Liu", "Independent Director", cb=0),
   star_row(DO, "Haijian He", "Chief Financial Officer", cb=0),
   row(TT, "All Directors and Executive Officers as a Group", "全体董事及高管合计（表内 6 人）",
       507347040, 18.6, ca=68147040, cb=439200000, vp=59.9, fn=["(2)"]),
   row(PS, "Handsome Reward Limited", "5% 以上主要股东（李彦宏全资拥有及控制的 BVI 公司）",
       449219376, 16.5, ca=10019376, cb=439200000, vp=59.2, fn=["(3)"]),
   row(PS, "BlackRock, Inc.", "5% 以上主要股东（机构投资者，ADS 实益持有人）",
       128640168, 4.7, ca=128640168, cb=0, vp=1.6, fn=["(4)"],
       note="沿用 2023-12-31 的 13G/A 数据，按 2026-01-31 分母占比 4.7%")],
  {"robin_li": li_fn("(1)", [
      C("本人在册直接持有", "class_a", 3013200, "(i) 3,013,200 Class A Ordinary Shares directly held by Mr. Robin Yanhong Li on record"),
      C("本人经 ESOP 管理人经纪账户以 ADS 形式持有", "class_a", 3530768, "(ii) 3,530,768 Class A ordinary shares in the form of ADSs held by Mr. Li"),
      C("Handsome Reward Limited 在册持有的 B 类", "class_b", 439200000, "(iii) 439,200,000 Class B ordinary shares held on record by Handsome Reward Limited"),
      C("Handsome Reward Limited 经 ESOP 账户以 ADS 形式持有的 A 类", "class_a", 8252408, "(iv) 8,252,408 Class A ordinary shares in the form of ADSs held by Handsome Reward Limited"),
      C("Handsome Reward Limited 60 日内可行使期权", "class_a", 1404960, "(v) 1,404,960 Class A ordinary shares issuable to Handsome Reward Limited upon exercise of options within 60 days after January 31, 2026"),
      C("Handsome Reward Limited 60 日内可归属限制性股份", "class_a", 362008, "(vi) 362,008 Class A Ordinary Shares issuable to Handsome Reward Limited upon vesting of restricted shares within 60 days"),
      C("员工授予李彦宏不可撤销投票代理的 A 类（以 ADS 形式持有）", "class_a", 51550880,
        "(vii) 51,550,880 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies as of January 31, 2026")],
      507314224,
      excludes=[{"item": "配偶马东敏持有的 A 类与 B 类", "class": "mixed", "shares": None,
                 "desc": "This excludes 3,465,992 Class A ordinary shares, including in the form of ADSs, and 84,720,000 Class B ordinary shares, all owned by Ms. Melissa Ma; Mr. Li disclaims beneficial ownership of all of such shares"}],
      voting="WVR 表脚注(1)：李彦宏所持投票权占公司全部流通投票权的 59.9%（截至 2026-01-31），与 SEC 表 59.9% 一致",
      proxy=51550880),
   "group_footnote": {"footnote": "(2)",
                      "text": "Includes 51,550,880 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Robin Yanhong Li irrevocable voting proxies as of January 31, 2026.",
                      "included_proxy_shares": 51550880},
   "institutions": [
       {"name_en": "BlackRock, Inc.", "footnote": "(4)",
        "detail": "128,640,168 股 A 类（唯一处置权）；投票权按 116,610,874 股 A 类（唯一投票权）计算；"
                  "百分比按公司 2026-01-31 总股本并假设持股自 2023-12-31 未变计算",
        "data_as_of": "2023-12-31",
        "source_filing": "Schedule 13G/A filed by BlackRock, Inc. on February 1, 2024"}],
   "wvr_footnotes": [
       {"footnote": "(1)", "text": "Includes 51,550,880 Class A ordinary shares in the form of ADSs held by certain employees who have granted Mr. Li irrevocable voting proxies as of January 31, 2026."},
       {"footnote": "(2)", "text": "To our knowledge, Integrity Partners V, LLC holds 100,320 Class B ordinary shares and was not a record shareholder of any Class A ordinary shares as at January 31, 2026."},
       {"footnote": "(3)", "text": WVR_BASIS_FN}]},
  {"htm_ownership_table_index": 328, "htm_footnote_tables": "329-335",
   "htm_wvr_table_index": 338, "txt_section_line": 16372, "txt_intro_line": 16375,
   "txt_basis_line": 16395, "txt_wvr_line": 16847,
   "section_title": "Item 6. — E. Share Ownership / Weighted Voting Rights Structure"},
  wvr={"as_of": "2026-01-31", "as_of_original": "As at January 31, 2026",
       "columns_original": ["Number of Class A Ordinary Shares", "Number of Class B Ordinary Shares",
                            "Approximate percentage of voting rights(3)"],
       "rows": [w("Robin Yanhong Li", 68114224, 439200000, 59.9, "(1)"),
                w("Melissa Ma", 3465992, 84720000, 11.4),
                w("Integrity Partners V, LLC", 0, 100320, 0.0, "(2)"),
                w("Total", 71580216, 524020320, 71.4, "(3)")]})

# <<<TAIL>>>
META = {
    "company_zh": "百度集团",
    "company_en": "Baidu, Inc.",
    "codes": {"hkex": "9888", "nasdaq": "BIDU"},
    "source": "各财年 Form 20-F（SEC）Item 6.E Share Ownership / Item 7.A Major Shareholders，"
              "本地存档 data/raw/20f_09888_<年>.htm/.txt",
    "caliber": "SEC beneficial ownership 口径：含 60 日内可行使期权与通过不可撤销投票代理取得的股份，"
               "披露门槛为任一类别 5%；与 A 股「前十名股东」口径不同",
    "extracted_at": "2026-09-01",
    "method": "从 .htm 的表格结构按列取数，语义通读章节，未做任何推算；自算值单独标注",
    "coverage": "FY2005—FY2025 共 21 个财年，全部来自本地已存档 20-F 原文；未联网、未使用第三方接口",
    "unit": "股数=普通股股（不是 ADS）；百分比=%（原文精度）",
    "share_count_comparability": "股数跨年不可直接比较：ADS 比例 2010-05-12 由 1:1 改为 10 ADS : 1 股；"
                                 "2021-03-01 生效 1 拆 80 股份拆细（Share Subdivision）并同步改为 1 ADS = 8 股 A 类。"
                                 "FY2019 及以前的表格股数为拆细前口径，FY2020 起为拆细后口径，本文件一律照录原文，未做换算。",
    "dual_class_note": "百度自 2005 年美国 IPO 起即为 A/B 双重股权（A 类每股 1 票、B 类每股 10 票，两类作为单一类别"
                       "一起投票，B 类可随时 1:1 转为 A 类）。但 FY2005—FY2019 的实益拥有权表只列一栏合计"
                       "（Shares Beneficially Owned: Number / %），未按类别分列，故该 15 个年度各行 class_a / class_b 记 null；"
                       "FY2020 起改为 Class A / Class B / Total + 投票权% 五列。",
    "name_zh_policy": "20-F 原文为英文，无中文名。name_zh 仅沿用本地范本 data/tables/tech_09888_holders_manual.json "
                      "已给出的中文名（李彦宏、马东敏、杨元庆、符绩勋、许冉、刘晓丹、何海建、贝莱德），其余一律 null，未自行翻译。",
    "cross_check": "FY2025 与 data/tables/tech_09888_holders_manual.json 逐格核对一致："
                   "李彦宏 18.6% / 59.9%、Handsome Reward 16.5%、BlackRock 4.7%、总股本 2,722,021,272。",
    "helper_scripts": ["data/extract/dump_20f_ownership_tables.py",
                       "data/extract/dump_20f_ownership_sections.py",
                       "data/extract/digest_20f_ownership.py",
                       "data/extract/build_ownership_hist_09888.py"],
}


def li_row(y):
    for r in YEARS[y]["rows"]:
        if r["name_en"] == "Robin Yanhong Li":
            return r
    return None


def build_derived():
    eco, vote = {}, {}
    for y in sorted(YEARS):
        r = li_row(y)
        eco[y] = r["pct_of_total_ordinary"]
        vote[y] = r["pct_of_voting_power"]
    return {
        "li_economic_pct_by_year": eco,
        "li_voting_pct_by_year": vote,
        "note": "这两条序列只是把各年 rows 里李彦宏那一行的原文百分比抽出来排成序列，没有任何推算",
        "li_voting_pct_source_note": "FY2005—FY2018 原文未披露李彦宏投票权%（表内无该列、脚注亦未提及）→ null；"
                                     "FY2019 的 55.4% 来自脚注(3) 文字披露；FY2020 起为表内 % of Aggregate Voting Power† 列。",
        "li_economic_pct_caliber_break": "FY2023 起员工不可撤销投票代理股份被计入李彦宏实益拥有股数，"
                                         "经济权益% 因此跳升（FY2022 16.3% → FY2023 18.2%），并非增持；"
                                         "FY2005/FY2006 的 21.9%/21.5% 含当年计入的配偶马东敏 1,676,667 股 B 类，"
                                         "FY2007 起该部分改为 excludes，口径亦有断点。",
    }


def build_gaps():
    g = []
    for y in sorted(YEARS):
        d = YEARS[y]
        if d["class_a"] is None:
            g.append({"year": y, "field": "total_ordinary_shares.class_a / class_b",
                      "reason": "原文脚注(2) 只给出合计 33,181,182 股 ordinary shares，未拆分 Class A / Class B"})
        if all(r["class_a"] is None for r in d["rows"]):
            g.append({"year": y, "field": "rows[].class_a / rows[].class_b",
                      "reason": "该年表格只有 \u201cShares Beneficially Owned: Number / %\u201d 一栏合计口径，原文未按类别分列"})
        if all(r["pct_of_voting_power"] is None for r in d["rows"]):
            g.append({"year": y, "field": "rows[].pct_of_voting_power",
                      "reason": "该年表格未设投票权% 列，原文亦未在脚注中披露任何人的投票权%"})
        stars = [r["name_en"] for r in d["rows"] if r["star"] and r["total_ordinary"] is None]
        if stars:
            g.append({"year": y, "field": "rows[].class_a/total_ordinary/pct_of_total_ordinary（%s 等 %d 人）"
                                          % (stars[0], len(stars)),
                      "reason": "原文以 * 表示「少于 1%」（Less than 1%），未披露具体股数与百分比"})
        if d["wvr_beneficiaries"] is None:
            g.append({"year": y, "field": "wvr_beneficiaries",
                      "reason": "该年 20-F 无「加权投票权受益人 / WVR beneficiaries」表；"
                                "港交所 WVR 披露自 FY2021 20-F 起才出现（A 类普通股 2021-03-23 于港交所上市）"})
    return g


EXTRA_GAPS = [
    {"year": "2005", "field": "rows[James Ding / William Decker].pct_of_total_ordinary",
     "reason": "原文百分比直接印为 \u201c< 0.1\u201d%，非具体数值也非 * 号，故 pct 记 null 并在 "
               "pct_of_total_ordinary_original 保留原文写法"},
    {"year": "2005", "field": "legend[*]",
     "reason": "该年表格未使用 * 号图例（其余年度均有 \u201cLess than 1%\u201d 图例）"},
    {"year": "2006-2010", "field": "rows[].pct_of_total_ordinary（部分董事高管）",
     "reason": "原文给出具体股数但百分比印为 *（少于 1%），故股数照录、pct 记 null 且 star=true"},
    {"year": "2005-2019", "field": "rows[].pct_of_voting_power",
     "reason": "FY2019 仅在李彦宏脚注(3) 以文字披露 55.4%；FY2005—FY2018 原文完全未披露投票权%"},
    {"year": "2005-2020", "field": "wvr_beneficiaries",
     "reason": "港交所 WVR 受益人表自 FY2021 20-F 起披露；FY2020 20-F（2021 年 3 月报送）仍无该表"},
    {"year": "2021-2025", "field": "wvr_beneficiaries[].pct_of_total_ordinary",
     "reason": "WVR 受益人表按港交所口径只列 A/B 类股数与投票权%，原文未给经济权益%"},
    {"year": "2021-2022", "field": "key_footnotes.group_footnote",
     "reason": "FY2021 20-F 的董事高管合计行无脚注；FY2022 的投票代理股份（8,037,128 股）按原文明确不计入实益拥有股数，"
               "故合计行亦无 included_proxy_shares"},
    {"year": "2005-2019", "field": "key_footnotes.institutions[].data_as_of",
     "reason": "早年机构行脚注只给 Schedule 13G 的提交日与百分比分母日期，未单独说明持仓数据日（FY2022 起才出现"
               "\u201cas of December 31, 20XX\u201d 的持仓数据日）"},
]


def main():
    out = {
        "_meta": META,
        "years": {y: YEARS[y] for y in sorted(YEARS)},
        "derived": build_derived(),
        "gaps": build_gaps() + EXTRA_GAPS,
    }
    jsonstore.write(OUTFILE, out, ensure_ascii=False, indent=1)
    # 本地自检：李彦宏脚注各项相加与表内数字是否一致
    bad = []
    for y in sorted(YEARS):
        sc = YEARS[y]["key_footnotes"]["robin_li"]["sum_check"]
        if not sc["match"]:
            bad.append((y, sc["sum"], sc["table_value"]))
    print("written:", OUTFILE)
    print("years:", len(out["years"]), "rows/year:",
          {y: len(YEARS[y]["rows"]) for y in sorted(YEARS)})
    print("li_sum_check mismatches:", bad if bad else "none")
    print("gaps:", len(out["gaps"]))


if __name__ == "__main__":
    main()

