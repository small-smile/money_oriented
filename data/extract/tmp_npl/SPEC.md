# 任务：从年报原文抽取「公司贷款 / 零售(个人)贷款 不良贷款余额」

仓库根：/home/zhu/Desktop/real_home/code/python/money_oriented

## 每家银行要做的事
1. 读 `data/tables/bank_<code>_detail_manual.json` 的 `loantrend`（years / corp / retail / nplCorp / nplRetail，余额单位亿元，不良率 %）
   和 `_notes.loantrend`（若有），弄清 corp、retail 的口径（公司贷款是否含票据贴现、零售是否含信用卡等）。
2. 对 loantrend.years 的每一年，从 `data/raw/annual_<code>_<year>.txt`（年报 pdftotext 原文）里取：
   - 公司贷款不良贷款余额（与 loantrend.corp 同口径）
   - 个人/零售贷款不良贷款余额（与 loantrend.retail 同口径）
   一般在「管理层讨论与分析 — 贷款质量分析 / 按产品类型划分的贷款及不良贷款分布」表，或「按行业划分的贷款和不良贷款分布」表的公司贷款小计 / 个人贷款行。
3. 必须**按章节语义通读**，不要只 grep 关键词；同义写法很多（企业贷款、对公贷款、公司类贷款、法人贷款；个人贷款、零售贷款、个人类贷款）。
4. 某年报本地缺失时，用下一年年报的「上年末」比较列；两份年报都披露同一年时，优先当年年报，若下一年年报重述了，采用重述值并在 note 里说明。
5. A+H 两地都有年报时优先 A 股年报；纯 H 股用 H 股年报。

## 硬规则
- **禁止反算**：不许用 余额×不良率 或 合计−个人 之类推算不良余额。年报没直接披露就填 null，并在 gaps 里写明原因。
- 口径必须与 loantrend.corp / retail 一致：例如 corp 不含票据贴现，就取「公司贷款」行而不是「公司贷款+票据贴现」；
  若年报只披露含贴现的合计，而 corp 不含贴现（或反过来），取能对上的那行；实在对不上就填 null 并在 gaps 写明。
- 自检：用抽到的 不良余额 ÷ loantrend 余额 与 loantrend.nplCorp / nplRetail 比，偏差 > 0.05 个百分点要复核；仍不一致的在 note 里说明。
- 单位统一换算成**亿元**，保留 2 位小数（原文百万元 ÷100，千元 ÷100000，万元 ÷10000）。

## 输出
每家银行写一个文件 `data/extract/tmp_npl/<code>.json`：
```json
{
  "code": "601398",
  "years": ["2020", "..."],
  "nplBalanceCorp": [123.45, null, ...],
  "nplBalanceRetail": [67.89, ...],
  "note": "一段中文口径说明：取自哪份年报哪张表、原始单位、公司口径是否含贴现、个人是否含信用卡、哪几年用了下一年年报比较列/重述值、自检结果",
  "gaps": ["2019: 年报未单列个人贷款不良余额，只给不良率", "..."]
}
```
years 必须与 loantrend.years 完全一致、数组等长。
不要改动 data/tables 下任何文件。最终回复只给每家一行汇总（代码、非空年数/总年数、自检是否通过、缺口一句话），不要回传原文。
