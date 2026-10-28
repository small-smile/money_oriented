# 本地数据检索索引 (data/)

**本地已抽取的年报是可信一手来源。取任何公司财务数据, 先查本地, 本地没有再去交易所/官网。**
`data/raw/annual_<code>_<year>.txt` 是交易所或公司官网年报 PDF 经 `pdftotext -layout`
抽出的原文, 与 `data/tables/*.json` 里由它汇总的数值同源, 不需要回交易所重新覆核;
只有本地确实缺该公司/该年份/该指标时才去外部抓取。

本文件由 `data/extract/gen_local_index.py` 生成, 回答「有没有、在哪、覆盖哪些年」。
**口径、单位、来源与历次陷阱记在 `data/tables/data_sources.txt`, 引用数值前读那份。**

## 怎么查

1. 看下面的公司清单确认代码与年份覆盖。
2. 要连续年度指标 -> `data/tables/<板块>_<code>_annual.json` 的 `annual["2025"]["nim"]` 这类路径。
3. 要年报里的明细表 (期限结构/五级分类/分部/员工/迁徙率等) -> `bank_<code>_detail_manual.json`,
   键名见文末清单, 每个键的口径写在同文件 `_notes` 里。
4. 表里没有的指标 -> 直接读 `data/raw/annual_<code>_<year>.txt`, 按章节语义通读, 不要 grep 单词。
5. A+H 两地都有年报时优先 A 股; 纯 H 股公司才用 H 股年报 (`_notes` 会注明)。


## 银行 (45 家) — `bank_<code>_*.json`

- **000001** 平安银行 [股份行]
  - 成品表: annual 1989-2025 (37); detail_manual 21 键
  - 年报文本: raw/annual_000001_<年>.txt 2018-2025 (8)
- **001227** 兰州银行 [城商行]
  - 成品表: annual 2000,2002,2007-2025 (21); detail_manual 21 键
  - 年报文本: raw/annual_001227_<年>.txt 2021-2022,2024-2025 (4)
- **002142** 宁波银行 [城商行]
  - 成品表: annual 2004-2025 (22); detail_manual 20 键
  - 年报文本: raw/annual_002142_<年>.txt 2018-2025 (8)
- **002807** 江阴银行 [农商行]
  - 成品表: annual 2005-2025 (21); detail_manual 20 键
  - 年报文本: raw/annual_002807_<年>.txt 2018-2025 (8)
- **002839** 张家港行 [农商行]
  - 成品表: annual 2006-2025 (20); detail_manual 20 键
  - 年报文本: raw/annual_002839_<年>.txt 2018-2025 (8)
- **002936** 郑州银行 [城商行]
  - 成品表: annual 2004-2025 (22); detail_manual 21 键
  - 年报文本: raw/annual_002936_<年>.txt 2018-2025 (8)
- **002948** 青岛银行 [城商行]
  - 成品表: annual 2003-2025 (23); detail_manual 20 键
  - 年报文本: raw/annual_002948_<年>.txt 2018-2025 (8)
- **002958** 青农商行 [农商行]
  - 成品表: annual 2011-2025 (15); detail_manual 21 键
  - 年报文本: raw/annual_002958_<年>.txt 2018-2025 (8)
- **002966** 苏州银行 [城商行]
  - 成品表: annual 2006-2007,2009-2025 (19); detail_manual 20 键
  - 年报文本: raw/annual_002966_<年>.txt 2020-2025 (6)
- **01578** 天津银行 [城商行]
  - 成品表: annual 2012-2025 (14); detail_manual 19 键; 年报覆盖层; 股东手工表
  - 年报文本: raw/annual_01578_<年>.txt 2016-2025 (10)
- **01916** 江西银行 [城商行]
  - 成品表: annual 2015-2025 (11); detail_manual 7 键; 年报覆盖层
  - 年报文本: raw/annual_01916_<年>.txt 2018-2025 (8)
- **06138** 哈尔滨银行 [城商行]
  - 成品表: annual 2009-2025 (17); detail_manual 19 键; 年报覆盖层
  - 年报文本: raw/annual_06138_<年>.txt 2013-2025 (13)
- **600000** 浦发银行 [股份行]
  - 成品表: annual 1996-2025 (30); detail_manual 20 键
  - 年报文本: raw/annual_600000_<年>.txt 2018-2025 (8)
- **600015** 华夏银行 [股份行]
  - 成品表: annual 2000-2025 (26); detail_manual 19 键
  - 年报文本: raw/annual_600015_<年>.txt 2018-2025 (8)
- **600016** 民生银行 [股份行]
  - 成品表: annual 1997-2025 (29); detail_manual 21 键; 股东手工表
  - 年报文本: raw/annual_600016_<年>.txt 2001-2025 (25)
- **600036** 招商银行 [股份行]
  - 成品表: annual 1999-2025 (27); detail_manual 20 键; 股东手工表
  - 年报文本: raw/annual_600036_<年>.txt 2002-2025 (24)
- **600908** 无锡银行 [农商行]
  - 成品表: annual 2006-2007,2009,2011-2025 (18); detail_manual 21 键
  - 年报文本: raw/annual_600908_<年>.txt 2018-2025 (8)
- **600919** 江苏银行 [城商行]
  - 成品表: annual 2005-2025 (21); detail_manual 19 键
  - 年报文本: raw/annual_600919_<年>.txt 2018-2025 (8)
- **600926** 杭州银行 [城商行]
  - 成品表: annual 2001-2025 (25); detail_manual 21 键
  - 年报文本: raw/annual_600926_<年>.txt 2018-2025 (8)
- **600928** 西安银行 [城商行]
  - 成品表: annual 2006-2025 (20); detail_manual 20 键
  - 年报文本: raw/annual_600928_<年>.txt 2018-2025 (8)
- **601009** 南京银行 [城商行]
  - 成品表: annual 2002-2025 (24); detail_manual 21 键
  - 年报文本: raw/annual_601009_<年>.txt 2018-2025 (8)
- **601077** 渝农商行 [农商行]
  - 成品表: annual 2005-2025 (21); 详情页图表
  - 年报文本: raw/annual_601077_<年>.txt 2019-2025 (7)
- **601128** 常熟银行 [农商行]
  - 成品表: annual 2001-2025 (25); detail_manual 20 键
  - 年报文本: raw/annual_601128_<年>.txt 2018-2022,2024-2025 (7)
- **601166** 兴业银行 [股份行]
  - 成品表: annual 2003-2025 (23); detail_manual 21 键
  - 年报文本: raw/annual_601166_<年>.txt 2018-2025 (8)
- **601169** 北京银行 [城商行]
  - 成品表: annual 2004-2025 (22); detail_manual 21 键
  - 年报文本: raw/annual_601169_<年>.txt 2018-2025 (8)
- **601187** 厦门银行 [城商行]
  - 成品表: annual 1999-2004,2006-2025 (26); detail_manual 21 键
  - 年报文本: raw/annual_601187_<年>.txt 2020-2025 (6)
- **601229** 上海银行 [城商行]
  - 成品表: annual 1996-2025 (30); detail_manual 20 键
  - 年报文本: raw/annual_601229_<年>.txt 2018-2025 (8)
- **601288** 农业银行 [国有大行]
  - 成品表: annual 2002-2025 (24); detail_manual 23 键; 股东手工表
  - 年报文本: raw/annual_601288_<年>.txt 2010-2025 (16)
- **601328** 交通银行 [国有大行]
  - 成品表: annual 2001-2025 (25); detail_manual 21 键
  - 年报文本: raw/annual_601328_<年>.txt 2018-2025 (8)
- **601398** 工商银行 [国有大行]
  - 成品表: annual 2003-2025 (23); detail_manual 21 键
  - 年报文本: raw/annual_601398_<年>.txt 2018-2025 (8)
- **601528** 瑞丰银行 [农商行]
  - 成品表: annual 2010-2025 (16); detail_manual 21 键
  - 年报文本: raw/annual_601528_<年>.txt 2021-2023,2025 (4)
- **601577** 长沙银行 [城商行]
  - 成品表: annual 2001-2006,2008-2025 (24); detail_manual 21 键
  - 年报文本: raw/annual_601577_<年>.txt 2018-2025 (8)
- **601658** 邮储银行 [国有大行]
  - 成品表: annual 2010-2025 (16); detail_manual 19 键
  - 年报文本: raw/annual_601658_<年>.txt 2019-2025 (7)
- **601665** 齐鲁银行 [城商行]
  - 成品表: annual 2004-2025 (22); detail_manual 20 键
  - 年报文本: raw/annual_601665_<年>.txt 2021-2025 (5)
- **601818** 光大银行 [股份行]
  - 成品表: annual 2005-2025 (21); detail_manual 20 键
  - 年报文本: raw/annual_601818_<年>.txt 2018-2025 (8)
- **601825** 沪农商行 [农商行]
  - 成品表: annual 2005-2025 (21); detail_manual 21 键
  - 年报文本: raw/annual_601825_<年>.txt 2021-2025 (5)
- **601838** 成都银行 [城商行]
  - 成品表: annual 2002-2004,2006-2025 (23); detail_manual 21 键
  - 年报文本: raw/annual_601838_<年>.txt 2018-2025 (8)
- **601860** 紫金银行 [农商行]
  - 成品表: annual 2010-2025 (16); detail_manual 20 键
  - 年报文本: raw/annual_601860_<年>.txt 2018,2021,2024-2025 (4)
- **601916** 浙商银行 [股份行]
  - 成品表: annual 2002-2025 (24); detail_manual 19 键
  - 年报文本: raw/annual_601916_<年>.txt 2019-2025 (7)
- **601939** 建设银行 [国有大行]
  - 成品表: annual 2000-2025 (26); detail_manual 21 键
  - 年报文本: raw/annual_601939_<年>.txt 2018-2025 (8)
- **601963** 重庆银行 [城商行]
  - 成品表: annual 1999-2025 (27); detail_manual 21 键; 股东手工表
  - 年报文本: raw/annual_601963_<年>.txt 2020-2025 (6)
- **601988** 中国银行 [国有大行]
  - 成品表: annual 2003-2025 (23); detail_manual 21 键
  - 年报文本: raw/annual_601988_<年>.txt 2018-2025 (8)
- **601997** 贵阳银行 [城商行]
  - 成品表: annual 2006-2025 (20); detail_manual 21 键
  - 年报文本: raw/annual_601997_<年>.txt 2018-2025 (8)
- **601998** 中信银行 [股份行]
  - 成品表: annual 2002-2025 (24); detail_manual 21 键
  - 年报文本: raw/annual_601998_<年>.txt 2018-2025 (8)
- **603323** 苏农银行 [农商行]
  - 成品表: annual 2004-2009,2011-2025 (21); detail_manual 20 键
  - 年报文本: raw/annual_603323_<年>.txt 2018-2025 (8)

## 保险 (6 家) — `insurer_<code>_*.json`

- **00966** 中国太平
  - 成品表: annual 2000-2025 (26)
  - 年报文本: raw/annual_00966_<年>.txt 2007-2025 (19); 英文版 2008 (1)
- **601318** 中国平安
  - 成品表: annual 2003-2025 (23)
  - 年报文本: raw/annual_601318_<年>.txt 2022,2025 (2)
- **601319** 中国人保
  - 成品表: annual 2007,2009-2011,2014-2025 (16)
  - 年报文本: raw/annual_601319_<年>.txt 2025 (1); OCR 2025 (1)
- **601336** 新华保险
  - 成品表: annual 2005-2025 (21)
  - 年报文本: raw/annual_601336_<年>.txt 2011,2025 (2)
- **601601** 中国太保
  - 成品表: annual 2004-2025 (22)
  - 年报文本: raw/annual_601601_<年>.txt 2025 (1)
- **601628** 中国人寿
  - 成品表: annual 2003-2025 (23)
  - 年报文本: raw/annual_601628_<年>.txt 2005,2025 (2)

## 水泥 (8 家) — `cement_<code>_*.json`

- **000401** 冀东水泥 [金隅集团]
  - 成品表: annual 1993-2025 (33)
  - 年报文本: raw/annual_000401_<年>.txt 2010-2025 (16)
- **000877** 天山股份 [中国建材集团]
  - 成品表: annual 1995-2025 (31)
  - 年报文本: raw/annual_000877_<年>.txt 2010-2025 (16)
- **002233** 塔牌集团 [民营（广东梅州）]
  - 成品表: annual 2005-2025 (21)
  - 年报文本: raw/annual_002233_<年>.txt 2010-2025 (16)
- **00743** 亚洲水泥（中国） [台湾远东 / 亚泥系]
  - 成品表: annual 2005-2025 (21)
  - 年报文本: raw/annual_00743_<年>.txt 2010-2025 (16)
- **01313** 华润建材科技 [华润集团]
  - 成品表: annual 2000-2025 (26)
  - 年报文本: raw/annual_01313_<年>.txt 2010-2025 (16)
- **03323** 中国建材 [中国建材集团]
  - 成品表: annual 2002-2025 (24)
  - 年报文本: raw/annual_03323_<年>.txt 2015-2025 (11)
- **600585** 海螺水泥 [安徽海螺集团]
  - 成品表: annual 1999-2025 (27)
  - 年报文本: raw/annual_600585_<年>.txt 2010-2025 (16)
- **600801** 华新水泥 [华新集团 / Holcim 参股]
  - 成品表: annual 1993-2025 (33)
  - 年报文本: raw/annual_600801_<年>.txt 2010-2025 (16)

- 板块手工层 `cement_ops_manual.json`: 冀东水泥 2010-2025 (16); 天山股份 2010-2025 (16); 塔牌集团 2010-2025 (16); 亚洲水泥（中国） 2010-2025 (16); 华润建材科技 2010-2025 (16); 中国建材 2015-2025 (11); 海螺水泥 2010-2025 (16); 华新水泥 2010-2025 (16)

## 房地产 (6 家) — `developer_<code>_*.json`

- **000069** 华侨城A [华侨城集团]
  - 成品表: annual 1994-2025 (32)
- **001979** 招商蛇口 [招商局集团]
  - 成品表: annual 2013-2025 (13)
- **00688** 中国海外发展 [中国建筑集团]
  - 成品表: annual 2000-2025 (26)
- **00817** 中国金茂 [中国中化]
  - 成品表: annual 2004-2025 (22)
- **01109** 华润置地 [华润集团]
  - 成品表: annual 1999-2025 (27)
- **600048** 保利发展 [保利集团]
  - 成品表: annual 2003-2025 (23)

## 通信 (4 家) — `telecom_<code>_*.json`

- **00941** ?
  - 成品表: annual 2001-2025 (25)
- **600050** 中国联通 [中国联通集团（经联通 BVI 持股）]
  - 成品表: annual 1999-2025 (27)
  - 年报文本: raw/annual_600050_<年>.txt 2015-2025 (11)
- **600941** 中国移动 [中国移动通信集团]
  - 成品表: annual 1999-2001,2007-2011,2018-2025 (16)
  - 年报文本: raw/annual_600941_<年>.txt 2021-2025 (5)
- **601728** 中国电信 [中国电信集团]
  - 成品表: annual 2002-2025 (24)
  - 年报文本: raw/annual_601728_<年>.txt 2021-2025 (5)

- 板块手工层 `telecom_ops_manual.json`: 中国联通 2015-2025 (11); 中国移动 2021-2025 (5); 中国电信 2021-2025 (5)
- 板块手工层 `telecom_segment_manual.json`: 中国联通 2015-2025 (11); 中国移动 2021-2025 (5); 中国电信 2021-2025 (5)

## 只有年报文本、没有成品表的代码

没有对应的 `*_annual.json`, 需要时直接读文本 (可能是同一家公司的另一上市地, 也可能是尚未入库的公司):

- **03618**: raw/annual_03618_<年>.txt 2010-2018,2025 (10); 英文版 2010-2013 (4)
- **09888**: raw/annual_09888_<年>.txt 2020-2025 (6)
- **605338**: raw/annual_605338_<年>.txt 2020-2025 (6)

## `<板块>_<code>_annual.json` 可查字段

顶层: `code / secucode / name / tier|group / fetched_at / source / unit_note / annual /
holders / holder_num / holder_concentration / dividend_per10`。金额单位元, 比率单位 %。
`annual` 以年份字符串为键, 每年一个 dict, 字段:

`accept_deposit` / `amortize_cost_finasset` / `asset_impairment` / `basic_eps` / `bond_payable` / `borrow_fund` / `bps` / `buy_resale` / `car` / `cash_deposit_pbc` / `cet1` / `cost_income_ratio` / `credit_impairment` / `creditor_invest` / `deposit_interbank` / `eps` / `equity_asset_ratio` / `fee_ni` / `fvtoci_finasset` / `fvtpl_finasset` / `gross_loans` / `income_tax` / `interest_ni` / `iofi_deposit` / `lcr` / `lend_fund` / `leverage_ratio` / `liquidity_ratio` / `loan_advance` / `loan_allowance_amortized` / `loan_impairment_charge` / `loan_loss_allowance` / `loan_pbc` / `loan_provision_ratio` / `ltd_ratio` / `manage_expense` / `minority_equity` / `minority_interest` / `net_charge_off` / `netcash_finance` / `netcash_invest` / `netcash_operate` / `netprofit` / `nim` / `nis` / `npl_amount` / `npl_formation` / `npl_formation_rate` / `npl_ratio` / `nsfr` / `oci` / `op_cf_per_share` / `operate_expense` / `operate_income` / `operate_profit` / `operate_tax` / `opinion_type` / `other_business_cost` / `other_creditor_invest` / `other_equity_invest` / `overdue_90plus` / `overdue_loans` / `parent_equity` / `parent_netprofit` / `provision_coverage` / `recovery` / `roa` / `roe_weighted` / `sell_repo` / `share_capital` / `staff_num` / `tier1` / `total_assets` / `total_deposits` / `total_equity` / `total_liabilities` / `total_profit` / `total_share` / `trade_finasset` / `transfer_out` / `write_off`

注意 `share_capital` / `total_share` 在多数行是最新值向历年回填, 不能用来看历年股本变动。

## `bank_<code>_detail_manual.json` 键

`5tier` / `bondpay` / `cf` / `chairman-pay` / `complaint` / `depcost` / `depterm` / `fvlevel` / `fvtpl-mix` / `geo` / `invest` / `loan-industry` / `loanmix-bal` / `loantrend` / `maturity` / `migrate` / `nim` / `overdue-band` / `perloan-bal` / `repricing` / `seg-rev` / `staff-age` / `staff-edu` / `staff-role` / `writeoff`

各键的年份范围、期末/日均口径、单位都写在同文件的 `_notes` 里, 读值前先读 `_notes`。


---
共 65 个代码、573 份年报文本 (445 MB)。新增公司或年份后重跑 `python3 data/extract/gen_local_index.py`。
