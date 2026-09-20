"""
抓取保险类上市公司的年报口径财务数据（东方财富 F10 数据接口，取值来自各期年度报告）。

数据源（datacenter-web.eastmoney.com/api/data/v1/get，reportName 为报表模板）：
    - RPT_F10_FINANCE_IINCOME       保险业利润表（年报期）
    - RPT_F10_FINANCE_IBALANCE      保险业资产负债表（年报期）
    - RPT_F10_FINANCE_ICASHFLOW     保险业现金流量表（年报期）
    - RPT_F10_FINANCE_MAINFINADATA  主要指标（含保险专项：已赚保费、综合/净投资收益率、
                                    偿付能力充足率、寿险退保率、新业务价值及其利润率等）
    - RPT_F10_EH_HOLDERS            前十名股东（含报告期内增减）
    - RPT_SHAREBONUS_DET            历年分红实施明细（每 10 股派现等）

纯 H 股险企（中国太平 00966.HK，无 A 股上市）走港股 F10（datacenter.eastmoney.com/securities/api/data/v1/get）：
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标（年报 + 中期混排，需自行筛 12-31 行）
      币种陷阱：行内 CURRENCY="HKD"、IS_CNY_CODE=0，但金额已按当年年末汇率折成人民币 ——
      2025 年隐含 0.90322（年报 270.59 亿港元 → 接口 244.40 亿元）、2024 年 0.92600
      （84.32 → 78.08；总资产 17,343.42 → 16,060.7），与年末 CNY/HKD 中间价吻合，
      因此可与五家 A 股险企的人民币金额同图比较；但同比字段 *_YOY 是按港元原值算的（2025 年
      +220.93% 对应港元口径），与折算后金额自算的同比不等，不要引用。
      不提供净/总投资收益率、偿付能力充足率、新业务价值、退保率与投资资产明细科目。
      RPT_HKF10_FN_INCOME / _BALANCE 为 STD_ITEM_CODE 长表（每个科目一行）需 pivot，科目与 A 股模板
      不对应，暂未采用；_CASHFLOW 与保险专版（_INCOME_INSU/_BALANCE_INSU）接口不存在（code 9501）。
      DPS_HKD 是快照字段（2000—2024 年逐行同为 1.58），不可当逐年股息序列。
      已核验（2026-08-19，对照 2025 年度业绩公告与 2025 中期公告原文）：2025 年保险服务收入
      1,122.67 亿港元、股东应占溢利 270.59 亿港元、EPS 7.251 港元、平均净资产 ROE 27.30%，
      2024 年股东应占溢利 84.32 亿港元、总资产 17,343.42 亿港元、普通股股东应占权益 711.09 亿港元，
      折算后与接口 earned_premium / parent_netprofit / eps / roe_weighted / total_assets / bps 一致。

口径断点（画图/解读时必须标注，详见 data/tables/data_sources.txt）：
    - 2023 年起执行 IFRS17 新保险合同准则 + IFRS9 新金融工具准则：退保金、赔付支出、
      提取保险责任准备金、手续费及佣金支出、分保相关科目在 2022 年止；
      「保险合同负债」未进入本模板的资产负债表字段，2023 年起负债只能看 TOTAL_LIABILITIES。
    - 2022 年是接口的新旧准则混排年（中国人寿晚一年，自 2024-01-01 起执行新准则，其混排年为 2023 年）：
      合计项与每股指标已被后一年年报的
      重述可比数覆盖（operate_income / earned_premium / parent_netprofit / total_assets /
      eps / roe_weighted），而同一行的明细科目仍是当年旧准则原披露值
      （surrender_value 退保金、compensate_expense 赔付支出、fee_commission_expense
      手续费及佣金支出、policy_bonus_expense 保单红利、insurance_contract_reserve 保险合同准备金），
      main_earned_premium（MAINFINADATA 的已赚保费）与 bps 也停留在原披露值
      —— 同一年度内两种口径并存，"收入-支出=营业利润"只在重述侧成立。
      已用中国平安核实：2022 年报原披露营业收入 1,110,568 百万元、已赚保费 742,418、
      归母净利润 83,774、EPS 4.80、加权 ROE 10.1%、每股净资产 46.97；
      接口的 operate_income 880,355 / earned_premium 525,981 / parent_netprofit 111,008 /
      eps 6.36 / roe_weighted 13.2 出自《基于新保险合同准则编制的 2022 年财务信息》
      (2023-07-19) 的重述数，而 main_earned_premium 742,418、bps 46.97、退保金 54,102、
      赔付支出 282,122、手续费及佣金支出 70,354 与 2022 年报原文一致。
      同期 extract_insurance_reserve=78,000,000 也不是年报的「提取保险责任准备金」262,301 百万元，
      而是紧邻一行的「提取保费准备金」(78) 百万元，不可当准备金提取额使用。
      国寿的 2023 混排行同理：bps 16.28、total_roi 2.68、extract_insurance_reserve 407,211 百万元
      是旧准则原披露值（2021 447,296 → 2022 461,204 → 2023 407,211 连续，属真实披露而非错行，故保留），
      而金额与 eps/roe_weighted 已是 2024 年报重述数。
    - 2018 年起金融资产三分类：可供出售/持有至到期被债权投资、其他债权投资、其他权益投资替代。
    - 偿付能力充足率 2016 年切换偿二代、2022 年切换偿二代二期，前后不可直接比较。
    - 中国平安合并平安银行，资产负债表出现吸收存款/发放贷款，总资产与 ROA 不宜与纯保险公司直接对比；
      invest_asset_total 同理为集团合并数（含银行/信托/证券/理财资产），与四家纯保险集团不可比。

接口取值缺陷与修补（均对照年报原文，代码见 ZERO_AS_MISSING / BAD_VALUES / ANNUAL_OVERRIDES / patch_annual）：
    - 当年未披露的比率字段接口填 0（平安 solvency_ar 2003—2007、国寿 net_roi 2003—2010、
      太保 net_roi 2004—2008、人保 2007 全套比率等），直接入图会画出真实的 0 线，统一改判缺失。
      派生的 roi_spread 因此也不再出现 −15.2 这类假值。
    - MAINFINADATA.TOTAL_SHARE 是当前总股本快照逐年重复填充，不是各年年末股数；
      按年算每股指标要用资产负债表的 share_capital。
    - 国寿 2005 行 netprofit ≠ 利润总额 − 所得税（差 58 百万元）：2005 年 CAS 利润表版式为
      「利润总额 − 所得税 − 少数股东收益 = 净利润」，接口把归母数填进 NETPROFIT 又漏抓少数股东收益，
      已按 2006 年 A 股年报的 2005 比较列补正 netprofit / minority_interest / main_liability。
    - 中国太平（港股 F10）金额取自后一年年报重列列、比率取自当年原披露值，2008 等 9 个年度两者矛盾，
      debt_ratio / equity_multiplier 一律按金额重算，原披露值记入输出的 vintage_note。
    - 中国人保 2025 年报 PDF（data/raw/annual_601319_2025.pdf）的数字被 suwell 转换器矢量化成
      Form XObject 轮廓，文本层无任何数字，任何抽取器都拿不到；核验请用重建的
      data/raw/annual_601319_2025.ocr.txt，不要再重下 PDF（东财与 picc.com 副本字节相同，H 股版同样坏）。

已核验（2026-08-18，对照 data/raw/annual_<code>_2025.txt，按章节语义通读而非 grep）：
    五家 2025 年度的营业收入/保险服务收入/归母净利润/总资产/股东权益合计/综合偿付能力充足率/
    净与总投资收益率/新业务价值/新业务价值率/加权 ROE/EPS/BPS/员工数/总股本/退保率共 84 项，
    与 A 股年报原文逐项一致，无数值偏差；中国人保 nbv_rate 为空经确认系年报确未披露价值率。
    新华 2008—2010 偿付能力充足率 27.74 / 36.19 / 34.99（新华人寿本级、偿一代）已用 2011 年
    招股说明书（data/raw/prospectus_601336_2011.pdf 第 1-1-325 页）核验，2010 年另由 2011 年年报
    附注 73(2)(d) 双源确认；三年均低于 100% 监管线，2011-03-30 保监会批复的 140 亿元增资后
    当年末回升至 155.95%。2005—2007 年公司未披露偿付能力，留空。

输出：
    data/raw/em_<reportName>_<code>.json       原始响应（缓存；--refresh 重新拉取）
    data/tables/insurer_<code>_annual.json     整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_insurer_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_insurer_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_insurer_financials.py 601318     # 只处理指定代码
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from _common import (
    API, API_HK, HEADERS, OUT_DIR, RAW_DIR, ROOT, annual_rows, cached, pick, request_json,
)


# 代码 -> (交易所后缀, 简称)；A+H 两地上市公司统一取 A 股年报口径
INSURERS = {
    "601318": ("SH", "中国平安"),
    "601628": ("SH", "中国人寿"),
    "601601": ("SH", "中国太保"),
    "601336": ("SH", "新华保险"),
    "601319": ("SH", "中国人保"),
}

# 纯 H 股上市险企：无 A 股年报，只能走港股 F10（RPT_HKF10_*）；年报以港元编制，
# 但接口返回的金额已按各年年末汇率折成人民币（见 HK_MAIN_FIELDS 上方的币种陷阱说明）
INSURERS_HK = {
    "00966": ("HK", "中国太平"),
}

STATEMENTS = {
    "income": "RPT_F10_FINANCE_IINCOME",
    "balance": "RPT_F10_FINANCE_IBALANCE",
    "cashflow": "RPT_F10_FINANCE_ICASHFLOW",
    "main": "RPT_F10_FINANCE_MAINFINADATA",
}

# 从各报表里取用的字段（键 = 输出字段名，值 = 接口字段名）
INCOME_FIELDS = {
    "operate_income": "OPERATE_INCOME",
    "earned_premium": "EARNED_PREMIUM",              # 已赚保费 / 保险服务收入（2023 起）
    "reinsure_income": "REINSURE_INCOME",            # 分保费收入
    "bank_interest_ni": "BANK_INTEREST_NI",          # 银行业务利息净收入（平安）
    "uninsurance_cni": "UNINSURANCE_CNI",            # 非保险业务手续费及佣金净收入
    "invest_income": "INVEST_INCOME",
    "invest_joint_income": "INVEST_JOINT_INCOME",    # 对联营合营企业投资收益
    "fairvalue_change": "FAIRVALUE_CHANGE",
    "exchange_income": "EXCHANGE_INCOME",
    "other_business_income": "OTHER_BUSINESS_INCOME",
    "operate_expense": "OPERATE_EXPENSE",
    "surrender_value": "SURRENDER_VALUE",            # 退保金（2022 年止）
    "compensate_expense": "COMPENSATE_EXPENSE",      # 赔付支出（2022 年止）
    "extract_insurance_reserve": "EXTRACT_INSURANCE_RESERVE",  # 提取保险责任准备金（2022 年止）
    "policy_bonus_expense": "POLICY_BONUS_EXPENSE",  # 保单红利支出
    "reinsure_expense": "REINSURE_EXPENSE",          # 分保费用
    "fee_commission_expense": "FEE_COMMISSION_EXPENSE",  # 手续费及佣金支出（2022 年止）
    "manage_expense": "BUSINESS_MANAGE_EXPENSE",
    "interest_expense": "INTEREST_EXPENSE",
    "other_business_cost": "OTHER_BUSINESS_COST",
    "credit_impairment": "CREDIT_IMPAIRMENT_LOSS",
    "asset_impairment": "ASSET_IMPAIRMENT_LOSS",
    "operate_tax": "OPERATE_TAX_ADD",
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "TOTAL_PROFIT",
    "income_tax": "INCOME_TAX",
    "netprofit": "NETPROFIT",
    "parent_netprofit": "PARENT_NETPROFIT",
    "deduct_parent_netprofit": "DEDUCT_PARENT_NETPROFIT",
    "minority_interest": "MINORITY_INTEREST",
    "basic_eps": "BASIC_EPS",
    "other_compre_income": "OTHER_COMPRE_INCOME",
    "total_compre_income": "TOTAL_COMPRE_INCOME",
    "opinion_type": "OPINION_TYPE",
}

BALANCE_FIELDS = {
    "total_assets": "TOTAL_ASSETS",
    "monetaryfunds": "MONETARYFUNDS",
    "time_deposit": "TIME_DEPOSIT",
    "buy_resale": "BUY_RESALE_FINASSET",
    # 金融资产：2018 年起为三分类，之前为可供出售 / 持有至到期 / 交易性
    "trade_finasset": "TRADE_FINASSET_NOTFVTPL",
    "creditor_invest": "CREDITOR_INVEST",
    "other_creditor_invest": "OTHER_CREDITOR_INVEST",
    "other_equity_invest": "OTHER_EQUITY_INVEST",
    "fvtpl_finasset": "FVTPL_FINASSET",
    "fvtoci_finasset": "FVTOCI_FINASSET",
    "amortize_cost_finasset": "AMORTIZE_COST_FINASSET",
    "available_sale_finasset": "AVAILABLE_SALE_FINASSET",
    "hold_maturity_invest": "HOLD_MATURITY_INVEST",
    "creditor_plan_invest": "CREDITOR_PLAN_INVEST",  # 债权计划投资
    "long_equity_invest": "LONG_EQUITY_INVEST",
    "invest_realestate": "INVEST_REALESTATE",
    "insured_pledge_loan": "INSURED_PLEDGE_LOAN",    # 保户质押贷款
    "premium_rece": "PREMIUM_RECE",                  # 应收保费（2022 年止）
    "reinsure_rece": "REINSURE_RECE",
    "ind_acc_asset": "IND_ACC_ASSET",                # 独立账户资产
    "fixed_asset": "FIXED_ASSET",
    "defer_tax_asset": "DEFER_TAX_ASSET",
    "accept_deposit": "ACCEPT_DEPOSIT",              # 吸收存款（平安合并平安银行）
    "loan_advance": "LOAN_ADVANCE",                  # 发放贷款（同上）
    "total_liabilities": "TOTAL_LIABILITIES",
    "insurance_contract_reserve": "INSURANCE_CONTRACT_RESERVE",  # 保险合同准备金（2022 年止）
    "uc_reserve": "UC_RESERVE",                      # 未到期责任准备金
    "ud_reserve": "UD_RESERVE",                      # 未决赔款准备金
    "ld_reserve": "LD_RESERVE",                      # 寿险责任准备金
    "hd_reserve": "HD_RESERVE",                      # 长期健康险责任准备金
    "insured_deposit_invest": "INSURED_DEPOSIT_INVEST",  # 保户储金及投资款
    "sell_repo": "SELL_REPO_FINASSET",
    "bond_payable": "BOND_PAYABLE",
    "subbond_payable": "SUBBOND_PAYABLE",
    "ind_acc_liab": "IND_ACC_LIAB",
    "total_equity": "TOTAL_EQUITY",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "minority_equity": "MINORITY_EQUITY",
    "share_capital": "SHARE_CAPITAL",
    "general_risk_reserve": "GENERAL_RISK_RESERVE",
    "unassign_profit": "UNASSIGN_RPOFIT",
    "balance_oci": "OTHER_COMPRE_INCOME",            # 资产负债表其他综合收益（累计额）
}

CASHFLOW_FIELDS = {
    "receive_premium_cash": "RECEIVE_ORIGIC_PREMIUM",  # 收到原保险合同保费现金
    "pay_compensate_cash": "PAY_ORIGIC_COMPENSATE",    # 支付原保险合同赔付款项
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
}

MAIN_FIELDS = {
    "main_earned_premium": "EARNED_PREMIUM",     # 主要指标口径的已赚保费（元）
    "total_roi": "TOTAL_ROI",                    # 总（综合）投资收益率 %
    "net_roi": "NET_ROI",                        # 净投资收益率 %
    "solvency_ar": "SOLVENCY_AR",                # 偿付能力充足率 %
    "surrender_rate_life": "SURRENDER_RATE_LIFE",  # 寿险退保率 %
    "nbv_life": "NBV_LIFE",                      # 寿险新业务价值（元）
    "nbv_rate": "NBV_RATE",                      # 新业务价值率 %
    "roe_weighted": "ROEJQ",                     # 加权平均 ROE %
    "roa": "ZZCJLL",                             # 总资产净利率 %
    "net_margin": "XSJLL",                       # 销售净利率 %
    "debt_ratio": "ZCFZL",                       # 资产负债率 %
    "equity_multiplier": "QYCS",                 # 权益乘数
    "bps": "BPS",                                # 每股净资产
    "eps": "EPSJB",                              # 基本每股收益
    "op_cf_per_share": "MGJYXJJE",               # 每股经营现金流
    "total_revenue": "TOTALOPERATEREVE",         # 营业总收入（元）
    "main_parent_netprofit": "PARENTNETPROFIT",  # 归母净利润（元）
    "main_total_assets": "TOTAL_ASSETS_PK",      # 总资产（元）
    "main_total_equity": "TOTAL_EQUITY_PK",      # 股东权益（元）
    "main_liability": "LIABILITY",               # 总负债（元）
    "staff_num": "STAFF_NUM",                    # 员工人数
    "total_share": "TOTAL_SHARE",                # 总股本
}

# 港股 F10 主要指标（RPT_HKF10_FN_MAININDICATOR）-> 与 A 股输出字段名对齐，便于同一张图共用 key。
# 币种陷阱：行内 CURRENCY 写 "HKD"、IS_CNY_CODE 写 0，但金额其实已按当年年末汇率折成人民币
# （2025 年隐含 0.90322、2024 年 0.92600，与年末 CNY/HKD 中间价一致，已用年报原文反推核验），
# 所以可以直接与五家 A 股险企的人民币金额同图比较；而 *_YOY 同比字段是按港元原值算的，不要用。
# 港股 F10 的利润表/资产负债表（RPT_HKF10_FN_INCOME/BALANCE）是 STD_ITEM_CODE 长表，
# 需逐项 pivot 且科目名与 A 股模板不对应，暂不取；现金流量表与保险专版报表接口不存在（code 9501）。
HK_MAIN_FIELDS = {
    "operate_income": "OPERATE_INCOME",
    "earned_premium": "PREMIUM_INCOME",      # 2023 起为 IFRS17 保险服务收入，此前为接口保费收入口径
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "PRETAX_PROFIT",
    "parent_netprofit": "HOLDER_PROFIT",     # 股东应占溢利
    "total_assets": "TOTAL_ASSETS",
    "total_liabilities": "TOTAL_LIABILITIES",
    "roe_weighted": "ROE_AVG",               # 港股 F10 为平均净资产 ROE，非 A 股「加权平均」算法
    "roa": "ROA",
    "net_margin": "NET_PROFIT_RATIO",
    "debt_ratio": "DEBT_ASSET_RATIO",
    "equity_multiplier": "EQUITY_MULTIPLIER",
    "eps": "BASIC_EPS",
    "bps": "BPS",                            # 对得上「普通股股东应占权益 ÷ 已发行股数」
    "op_cf_per_share": "PER_NETCASH_OPERATE",
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "total_share": "ISSUED_COMMON_SHARES",
}
# 未采用：TOTAL_PARENT_EQUITY（2024 年折回港元为 870.7 亿，与年报「普通股股东应占权益」711.09 亿、
# 「总权益」1,223 亿都对不上，口径不明）；DPS_HKD（快照值，2000—2024 年逐行同为 1.58）。


# ── 接口缺陷修补（全部经年报原文核验，见 data/tables/data_sources.txt） ──

# 接口对「当年未披露」的比率字段填 0 而不是 null，直接入图会画出一条真实的 0 线
# （平安 solvency_ar 2003—2007、国寿 net_roi 2003—2010、太保 net_roi 2004—2008、
#  人保 2007 全套比率等，均系公司当年尚未上市/未披露该指标）。统一按缺失处理。
ZERO_AS_MISSING = {
    "total_roi", "net_roi", "solvency_ar", "surrender_rate_life",
    "nbv_life", "nbv_rate", "roe_weighted", "basic_eps", "eps", "op_cf_per_share",
}

# 接口取值错行/残留，年报原文无对应数，置空而非沿用（否则每次重抓又会写回）：
#   平安 2022 年 extract_insurance_reserve=78,000,000 取的是紧邻一行的「提取保费准备金」(78) 百万元，
#          年报「提取保险责任准备金」实为 262,301 百万元；2023 年 230,000,000 是同一模板的残留值，
#          该年已执行 IFRS17，年报不再有此科目。
#   注：国寿 2023 年 extract_insurance_reserve=407,211 百万元是旧准则真实披露值
#      （2021 447,296 → 2022 461,204 → 2023 407,211 连续），属混排年而非错行，保留。
#   人保 2007 年 net_roi=15.2：净投资收益率（不含公允价值变动）不可能到 15%，
#          当年 invest_income 66.8 亿元 ÷ 总资产 1,471.4 亿元 ≈ 4.5%；人保集团 2012-12 才在港交所上市，
#          2007 年不存在可核验的年报，且该行前后 2009—2014 年 net_roi 全为空，是无源孤点。
#          按招行 2017 年孤点的处理办法置空（宁缺勿错），序列从 2015 年起连续可比。
BAD_VALUES: dict[tuple[str, str], tuple[str, ...]] = {
    ("601318", "2022"): ("extract_insurance_reserve",),
    ("601318", "2023"): ("extract_insurance_reserve",),
    ("601319", "2007"): ("net_roi",),
}

# 单年份字段级修正，(代码, 年份) -> {字段: (值, 依据)}
ANNUAL_OVERRIDES: dict[tuple[str, str], dict[str, tuple[float, str]]] = {
    # 2005 年 CAS 利润表版式为「利润总额 − 所得税 − 少数股东收益 = 净利润」，那一版的「净利润」
    # 已是归母数，接口把它填进 NETPROFIT 又漏抓 MINORITY_INTEREST，导致
    # netprofit ≠ total_profit − income_tax（差 58 百万元 = 1.06%）。
    # 依据：2006 年 A 股年报「2006 年度利润表」2005 年比较列（利润总额 5,760 / 所得税 246 /
    # 少数股东收益 58 / 净利润 5,456），H 股 2005 年报 HKFRS 表少数股东损益 59 亦同量级。
    ("601628", "2005"): {
        "netprofit": (5_514_000_000, "2006 年 A 股年报 2005 比较列：5,760 − 246"),
        "minority_interest": (58_000_000, "2006 年 A 股年报 2005 比较列「减：少数股东收益」"),
        "main_liability": (458_432_000_000, "2006 年 A 股年报 2005 比较列「负债合计」"),
    },
}


def patch_annual(code: str, annual: dict[str, dict]) -> None:
    """把接口的 0 填充、错行值、缺失值就地修补成可入图的口径。"""
    for year, rec in annual.items():
        for field in ZERO_AS_MISSING:
            if rec.get(field) == 0:
                rec[field] = None
        for field in BAD_VALUES.get((code, year), ()):
            rec[field] = None
        for field, (value, _src) in ANNUAL_OVERRIDES.get((code, year), {}).items():
            rec[field] = value


# ── 中国太平（00966.HK）年报手工表 ──
#
# 港股 F10 主要指标不含投资收益率、偿付能力、新业务价值、投资资产、员工数与逐年股息，
# 这些只在年报原文里披露，因此按 fetch_developer_financials.HK_PRESALE_THOUSANDS 的办法
# 硬编码一张年报手工表。来源：港交所 HKEXnews 中文年报（data/raw/annual_00966_<年>.pdf），
# 2007—2025 连续 19 份逐份语义通读披露章节后录入。2000—2006 年报在 HKEXnews
# searchType=1 检索库里取不到（该库覆盖自 2007-04 起），那 7 年这些字段仍为空。
#
# 单位：ta/inv/nbv/equity_parent/equity_total 为年报原披露港币百万元（as reported，非重列数），
#   dps 为港元/股（当年宣派全年股息 = 中期 + 末期），比率字段为 %。
#   金额一律乘 HKD_CNY_YEAR_END[年] 折成人民币，与五家 A 股险企同图可比。
#   ta 不入库，只用来反推隐含汇率（F10 人民币总资产 ÷ 年报港币总资产）做交叉校验。
# 偿付能力：太平是控股集团，境内子公司分别披露，集团层面没有单一指标——
#   sol_l/sol_p/sol_o = 太平人寿/太平财险/太平养老「综合偿付能力充足率」，
#   sol_*_core 为对应「核心偿付能力充足率」（2022 年偿二代二期起才逐年披露）。
#   2015 年及以前为偿一代，2016—2021 偿二代一期，2022 年起二期，三段不可比。
#   注意别把 CIRe（太平再保险）按香港监管口径披露的偿付能力充足率（2007 年 147.1%、
#   2008 年 630.6% 等）当成境内子公司的原保监会口径数。
# 新业务价值：nbv 为太平人寿（集团持股 75.1%）单体一年新业务价值，非集团合计。
#   2007—2008 扣「资本成本及费用超支」，2009 年起仅扣资本成本，故 2009 年是口径断点；
#   2016 年报同时给出偿二代 9,115 与偿一代 7,126，取偿二代（2016 年亦为断点）；
#   2023 年起取「经济假设调整后」数（2023 年调整前 9,396、2024 年调整前 14,272）。
# 退保率：太平只披露退保金额、±10% 敏感性与 13/25 个月继续率，从不披露退保率，
#   surrender_rate_life 19 年全空，这个缺口无法从年报补上。
HK_REPORT_FIELDS = ("ta", "inv", "net_roi", "total_roi", "compre_roi",
                    "sol_l", "sol_p", "sol_o", "sol_l_core", "sol_p_core", "sol_o_core",
                    "nbv", "nbv_rate", "equity_parent", "equity_total", "staff", "dps")

HK_REPORT_00966: dict[str, tuple] = {
    # 时名「中保国际控股」，太平财险为联营企业未纳入合并；集团层面未披露投资收益率
    "2007": (55_617.55, 50_844.71, None, None, None,
             215, None, None, None, None, None,
             603, None, 5_685.63, 8_095.68, 9_925, 0.10),
    # 只有寿险分部收益率 5.3%，无集团口径
    "2008": (80_815.39, 72_561.28, None, None, None,
             218, 173, None, None, None, None,
             865, None, 4_596.62, 7_239.25, 24_048, 0.0),
    # 本年更名「中国太平保险控股」；NBV 改为仅扣资本成本口径
    "2009": (111_531.03, 95_757.89, None, None, None,
             222, 192, None, None, None, None,
             1_353, None, 10_296.71, 15_337.83, 33_002, 0.0),
    "2010": (154_483.67, 133_664.17, None, None, None,
             270, 154, None, None, None, None,
             1_827, None, 12_712.39, 18_481.87, 33_663, 0.0),
    "2011": (191_372.35, 171_263.51, None, None, None,
             178, 152, None, None, None, None,
             2_244, None, 11_434.70, 16_874.05, 31_661, 0.0),
    "2012": (242_938.51, 219_786.78, 4.9, 3.4, None,
             164, 163, None, None, None, None,
             2_304, None, 13_836.77, 20_992.42, 37_187, 0.0),
    # 年报里的「偿付能力充足率 191.9%」属太平澳门财险，不是太平养老，未采
    "2013": (315_016.18, 280_860.00, None, 5.1, None,
             166, 166, None, None, None, None,
             3_148, None, 19_847.24, 23_850.84, 40_827, 0.0),
    "2014": (443_548.99, 357_261.30, None, 5.8, None,
             275, 174, 297, None, None, None,
             4_326, None, 35_992.98, 51_338.52, 43_933, 0.0),
    "2015": (488_031.35, 372_667.46, None, 7.97, None,
             226, 178, 254, None, None, None,
             6_017, 28.0, 55_020.66, 71_798.63, 53_682, 0.0),
    # 偿一代→偿二代切换年；NBV 取偿二代 9,115（偿一代口径 7,126）
    "2016": (505_405.76, 425_179.64, None, 5.01, None,
             251, 206, 324, None, None, None,
             9_115, 33.5, 51_462.12, 67_002.66, 60_270, 0.10),
    "2017": (666_473.69, 539_929.69, None, 4.48, None,
             246, 216, 336, None, None, None,
             13_638, 35.5, 61_733.27, 81_720.70, 77_472, 0.10),
    # 2019 年报把长期股权投资重分类，把本年投资资产由 595,925.20 重列为 608,295.45，此处留原披露数
    "2018": (752_101.33, 595_925.20, None, 3.85, None,
             224, 225, 299, None, None, None,
             13_237, 36.0, 61_022.69, 80_395.78, 75_341, 0.10),
    "2019": (919_420.18, 760_253.92, 4.72, 4.77, None,
             227, 271, 221, None, None, None,
             10_511, 28.4, 76_307.60, 94_056.96, 65_957, 0.30),
    "2020": (1_169_007.97, 979_709.65, 4.21, 5.44, None,
             213, 239, 234, None, None, None,
             8_784, 24.6, 90_647.45, 116_613.06, 65_900, 0.40),
    "2021": (1_378_641.97, 1_180_654.69, 4.07, 5.39, None,
             208, 216, 256, None, None, None,
             9_104, 24.1, 88_066.83, 113_455.96, 68_446, 0.46),
    # 偿二代二期首年，太平人寿实际资本由 214,315 降至 166,142（人民币百万元），年报无文字说明
    "2022": (1_409_365.57, 1_218_217.92, 4.02, 3.31, None,
             194, 186, 224, None, None, None,
             7_458, 18.7, 75_505.99, 98_686.18, 68_386, 0.26),
    # IFRS17+IFRS9 首年；本年报无集中偿付能力章节，核心充足率取 2024 年报比较列
    "2023": (1_509_497.49, 1_349_531.70, 3.56, 2.66, 5.01,
             284, 216, 229, 148, 138, 152,
             7_512, 15.9, 78_988.11, 132_595.65, 65_378, 0.30),
    "2024": (1_734_342.01, 1_562_099.00, 3.46, 4.57, 10.32,
             298, 239, 245, 186, 172, 186,
             9_103, 20.7, 71_080.41, 122_407.45, 62_266, 0.35),
    # 综合投资收益率 1.73% 全由 FVOCI 债券公允价值变动 −431.56 亿港元压低（剔除后 4.29%）
    "2025": (1_986_586.64, 1_743_052.49, 3.21, 4.04, 1.73,
             230, 236, 215, 143, 170, 160,
             9_589, 21.3, 95_154.88, 164_792.95, 57_951, 1.23),
}

HK_REPORT_TABLES: dict[str, dict[str, tuple]] = {"00966": HK_REPORT_00966}

# 港元→人民币折算率：中国外汇交易中心受权公布的「当年最后一个交易日」人民币对港元中间价。
# 用官方中间价（而非 F10 隐含汇率）作折算基准的理由：F10 的人民币金额取自后一年年报的
# 重列比较列，年报手工表存的是原披露数，两者不同版本，相除得到的隐含汇率会被重列幅度污染。
# 用官方中间价折出来的 nbv_life 能逐年复现年报正文自己披露的人民币新业务价值
# （2018 115.99 / 2019 94.16 / 2020 73.93 / 2021 74.44 / 2022 66.62 / 2023 68.07 /
#  2024 84.29 / 2025 86.61 亿元），隐含汇率则复现不了（2022 会低 6.2%）。
# 逢年末休市的年份取实际最后交易日：2007-12-28、2011-12-30、2016-12-30、
# 2017-12-29、2018-12-28、2022-12-30、2023-12-29。
HKD_CNY_YEAR_END = {
    "2007": 0.93638, "2008": 0.88189, "2009": 0.88048, "2010": 0.85093,
    "2011": 0.81070, "2012": 0.81085, "2013": 0.78623, "2014": 0.78887,
    "2015": 0.83778, "2016": 0.89451, "2017": 0.83591, "2018": 0.87620,
    "2019": 0.89578, "2020": 0.84164, "2021": 0.81760, "2022": 0.89327,
    "2023": 0.90622, "2024": 0.92604, "2025": 0.90322,
}
# 隐含汇率与官方中间价的偏离阈值（绝对值），超过就写进 fx_check 提示该年 F10 金额被重列过
FX_IMPLIED_TOL = 0.005

# 手工表里的比率字段直接落库的字段名（左：输出字段，右：HK_REPORT_FIELDS 里的名）
HK_REPORT_RATIOS = {
    "net_roi": "net_roi", "total_roi": "total_roi", "compre_roi": "compre_roi",
    "nbv_rate": "nbv_rate",
    "solvency_ar_life": "sol_l", "solvency_ar_pc": "sol_p", "solvency_ar_pension": "sol_o",
    "solvency_core_life": "sol_l_core", "solvency_core_pc": "sol_p_core",
    "solvency_core_pension": "sol_o_core",
}
# 手工表里的港币金额字段（左：输出字段，右：源字段），逐年乘隐含汇率折人民币
HK_REPORT_AMOUNTS = {
    "invest_asset_total": "inv", "nbv_life": "nbv",
    "parent_equity": "equity_parent", "total_equity": "equity_total",
}


def patch_annual_hk_report(code: str, annual: dict[str, dict]) -> tuple[dict, dict, dict]:
    """把年报手工表并入港股 F10 年度记录，港币金额按当年官方年末中间价折人民币。

    返回 (逐年隐含汇率, 每 10 股股息（人民币元）, 隐含汇率偏离说明)。
    """
    table = HK_REPORT_TABLES.get(code) or {}
    fx_implied: dict[str, float] = {}
    dividend_per10: dict[str, float] = {}
    fx_check: dict[str, str] = {}
    for year, values in table.items():
        rec = annual.get(year)
        if rec is None:
            continue
        r = dict(zip(HK_REPORT_FIELDS, values))
        fx = HKD_CNY_YEAR_END.get(year)
        ta_cny = rec.get("total_assets")
        if ta_cny and r.get("ta"):
            implied = round(ta_cny / 1e6 / r["ta"], 5)
            fx_implied[year] = implied
            if fx and abs(implied - fx) > FX_IMPLIED_TOL:
                fx_check[year] = (f"隐含汇率 {implied} 与官方年末中间价 {fx} 差 "
                                  f"{round((implied - fx) * 100, 2)} 分——该年 F10 人民币金额取自"
                                  f"后一年年报的重列比较列，与手工表的原披露港币总资产不是同一版本；"
                                  f"折算一律以官方中间价为准")
        for out_key, src in HK_REPORT_RATIOS.items():
            rec[out_key] = r[src]
        for out_key, src in HK_REPORT_AMOUNTS.items():
            v = r[src]
            rec[out_key] = round(v * 1e6 * fx) if (v is not None and fx) else None
        rec["staff_num"] = r["staff"]
        # 控股集团层面没有单一偿付能力充足率，留空，不与 A 股同名序列混画
        rec["solvency_ar"] = None
        # 年报只披露退保金额、敏感性与继续率，从不披露退保率
        rec["surrender_rate_life"] = None
        if fx and r["dps"] is not None:
            dividend_per10[year] = round(r["dps"] * 10 * fx, 4)
    return fx_implied, dividend_per10, fx_check


def build_insurer(code: str, refresh: bool) -> dict:
    suffix, name = INSURERS[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}")

    payloads = {key: cached(rn, code, filt, refresh) for key, rn in STATEMENTS.items()}
    rows = {key: annual_rows(p) for key, p in payloads.items()}

    years = sorted(set().union(*[set(r) for r in rows.values()]))
    annual: dict[str, dict] = {}
    for y in years:
        rec: dict = {}
        for key, fields in (("income", INCOME_FIELDS), ("balance", BALANCE_FIELDS),
                            ("cashflow", CASHFLOW_FIELDS), ("main", MAIN_FIELDS)):
            row = rows[key].get(y)
            if row:
                rec.update(pick(row, fields))
        annual[y] = rec

    patch_annual(code, annual)

    # ── 派生指标 ──
    prev_assets: float | None = None
    for y in years:
        rec = annual[y]
        # 综合与净投资收益率之差：正值多来自浮盈/已实现价差，负值多为公允价值损失
        tr, nr = rec.get("total_roi"), rec.get("net_roi")
        rec["roi_spread"] = round(tr - nr, 4) if tr is not None and nr is not None else None

        # 投资资产合计：按当年披露存在的分类科目相加，避免新旧准则重复计入
        legacy = [rec.get(k) for k in ("available_sale_finasset", "hold_maturity_invest")]
        new_cls = [rec.get(k) for k in ("creditor_invest", "other_creditor_invest",
                                        "other_equity_invest")]
        parts = [rec.get("trade_finasset"), rec.get("fvtpl_finasset"),
                 rec.get("fvtoci_finasset"), rec.get("amortize_cost_finasset"),
                 rec.get("time_deposit"), rec.get("long_equity_invest"),
                 rec.get("invest_realestate")]
        parts += new_cls if any(v for v in new_cls) else legacy
        vals = [v for v in parts if v]
        rec["invest_asset_total"] = sum(vals) if vals else None

        # 归母 ROA（期初期末总资产均值），平安含银行业务不宜与纯保险公司横比
        pnp, ta = rec.get("parent_netprofit"), rec.get("total_assets")
        if pnp is not None and ta and prev_assets:
            rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4)
        else:
            rec["roa_avg"] = None
        prev_assets = ta

        # 权益资产比：股东权益合计 ÷ 总资产（= 1 − 资产负债率 = 1/权益乘数），衡量财务杠杆。
        # total_equity 含少数股东权益（非归母口径）；平安含平安银行，分母被银行资产抬高。
        te = rec.get("total_equity")
        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None

    # 历年分红：按利润分配方案归属的报告年度（REPORT_DATE 年份）累加每 10 股派现（含税），
    # 同一年度可能有中期 + 末期两条记录，按年度合计。
    bonus_payload = cached("RPT_SHAREBONUS_DET", code, filt, refresh,
                           sort_col="PLAN_NOTICE_DATE", page_size=100)
    bonus_rows = (bonus_payload.get("result") or {}).get("data") or []
    dividend_per10: dict[str, float] = {}
    for r in bonus_rows:
        if r.get("ASSIGN_PROGRESS") != "实施分配":
            continue
        amt = r.get("PRETAX_BONUS_RMB")
        rd = (r.get("REPORT_DATE") or "")[:4]
        if amt is None or not rd:
            continue
        dividend_per10[rd] = round(dividend_per10.get(rd, 0.0) + amt, 4)

    holders_payload = cached("RPT_F10_EH_HOLDERS", code, filt, refresh,
                             sort_col="END_DATE", page_size=200)
    holder_rows = (holders_payload.get("result") or {}).get("data") or []
    # 取最近一个年报期（12-31）的前十大股东，与页面「年报口径」一致
    year_ends = [d for d in ((r.get("END_DATE") or "")[:10] for r in holder_rows) if d.endswith("-12-31")]
    latest_end = max(year_ends) if year_ends else None
    holders = [
        {
            "rank": r.get("HOLDER_RANK"),
            "name": r.get("HOLDER_NAME"),
            "hold_num": r.get("HOLD_NUM"),
            "ratio": r.get("HOLD_NUM_RATIO"),
            "change": r.get("HOLD_NUM_CHANGE"),
            "state": r.get("HOLDER_STATE_NEW") or r.get("HOLDER_STATE"),
            "shares_type": r.get("SHARES_TYPE"),
            "total_shares": r.get("TOTAL_SHARES_NUM"),
        }
        for r in holder_rows if (r.get("END_DATE") or "")[:10] == latest_end
    ]
    holders.sort(key=lambda h: h["rank"] or 99)

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富公司数据接口（各期 A 股年报合并数）。2025 年度已逐项对照五家 A 股年报"
                   "原文核验：营业收入/保险服务收入/归母净利润/总资产/股东权益/偿付能力/投资收益率/"
                   "新业务价值/ROE/EPS/BPS/员工数/总股本/退保率全部一致；2022 年（中国人寿为 2023 年）"
                   "接口为新旧准则混排行，不可直接同比，详见 data/tables/data_sources.txt。"
                   "接口取值缺陷已就地修补（见本脚本 ZERO_AS_MISSING / BAD_VALUES / ANNUAL_OVERRIDES）："
                   "未披露比率的 0 填充改判缺失、平安 2022/2023 提取保险责任准备金错行值置空、"
                   "国寿 2005 净利润/少数股东收益/负债合计按 2006 年 A 股年报比较列补正；"
                   "新华 2008—2010 偿付能力已用 2011 年招股说明书（data/raw/prospectus_601336_2011.pdf）"
                   "与 2011 年年报核验，2005—2007 年公司未披露、留空"),
        "unit_note": "金额字段单位为元；比率字段单位为 %",
        "caliber_note": ("2023 年起执行 IFRS17 + IFRS9：退保金/赔付支出/提取保险责任准备金/"
                         "手续费及佣金支出/保险合同准备金等科目在 2022 年止；"
                         "偿付能力充足率 2016 年切偿二代、2022 年切偿二代二期，前后不可比。"
                         "2022 年是混排年：营业收入/保险服务收入/归母净利润/总资产/EPS/加权 ROE "
                         "已是后一年年报的新准则重述值，而同一行的退保金/赔付支出/"
                         "手续费及佣金支出/保险合同准备金以及 main_earned_premium（已赚保费）/BPS "
                         "仍是旧准则原披露值。中国人寿自 2024-01-01 起才执行新准则，其混排年是 2023 年"
                         "（2023 行的金额与 EPS/ROE 为 2024 年报重述数，而 bps 16.28、total_roi 2.68、"
                         "extract_insurance_reserve 407,211 百万元仍是旧准则原披露值），画准则断点须单独标 2024。"
                         "字段名沿用接口命名，earned_premium 在 2022 年起"
                         "实为「保险服务收入」；total_equity 含少数股东权益（中国人保归母仅占 74%），"
                         "solvency_ar 主体不一（平安/太保/人保为集团，新华为寿险本级），"
                         "nbv_rate 口径不一（平安按标准保费、国寿仅个险渠道、人保不披露）。"
                         "total_share 取自 MAINFINADATA.TOTAL_SHARE，是当前总股本快照被逐年重复填充，"
                         "不是各年年末股数；要按年算每股指标请用资产负债表的 share_capital，"
                         "或直接用接口已给的 eps/bps/op_cf_per_share。"
                         "invest_asset_total 是本脚本按资产科目自加的「可投资资产」，"
                         "与年报管理口径的「投资资产」不等；中国平安为集团合并数（含平安银行/信托/"
                         "证券/理财的资产），与四家纯保险集团不可比，图上须单独标注。"
                         "未披露年份的比率字段接口填 0，本脚本已统一改判为缺失（null），不画 0 线。"),
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
        "dividend_per10": dividend_per10,
    }


def build_insurer_hk(code: str, refresh: bool) -> dict:
    """纯 H 股险企（中国太平 00966.HK）：走港股 F10 主要指标，金额已折人民币。"""
    suffix, name = INSURERS_HK[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}（港股 F10，金额已按年末汇率折人民币）")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"em_RPT_HKF10_FN_MAININDICATOR_{code}.json"
    if raw_path.exists() and not refresh:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        print("    [http] RPT_HKF10_FN_MAININDICATOR")
        payload = request_json("RPT_HKF10_FN_MAININDICATOR", filt, page_size=200, api=API_HK)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    # 接口把中期与年报混在一起返回（DATE_TYPE_CODE 作为查询参数无效），只保留 12-31 行
    rows = annual_rows(payload)
    annual = {y: pick(row, HK_MAIN_FIELDS) for y, row in rows.items()}

    # 权益资产比：港股 F10 未采集股东权益，用（总资产 − 总负债）÷ 总资产 反推全口径权益占比，
    # 与五家 A 股「total_equity ÷ total_assets」同义（total_equity = 总资产 − 总负债）。
    for rec in annual.values():
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        rec["equity_asset_ratio"] = round((ta - tl) / ta * 100, 4) if ta and tl else None

    # 版本混排修补：接口的金额字段取自后一年年报的重列比较列，而比率字段取自当年年报的原披露值，
    # 遇到重大追溯重列的年份两者就互相矛盾（2008 年 debt_ratio 91.04% 是原披露
    # 73,576,142/80,815,389，而同一行的 total_assets/total_liabilities 已是 2009 年报重列的
    # 88,017,055/75,866,531 → 86.20%，且与本函数自算的 equity_asset_ratio 13.80% 无法自洽）。
    # 重列原因：财政部 2009 年《保险合同相关会计处理的规定》分拆混合合同 + 同一控制下收购民安控股
    # 追溯合并，已对照 2008/2009 两份 H 股年报（data/raw/annual_00966_2008.pdf、_2009.pdf）核验。
    # 处理：负债率与权益乘数一律按存量金额（= equity_asset_ratio 的同一口径）重算，不做阈值判断——
    # 否则阈值以下的年份（如 2013 年差 0.42pp）会留下 debt_ratio + equity_asset_ratio ≠ 100 的自相矛盾，
    # 整条序列变成两种口径混排。原披露值与差额记入 vintage_note 备查（仅列差 > 0.05pp 的年份）。
    # 注意：equity_asset_ratio 是本函数用同一对金额自算的，因此它与重算后的 debt_ratio 相加恒为 100，
    # 这只是自洽，不构成对重列金额的独立验证；独立验证只有 2008 年做过（两份年报原文）。
    # roe_weighted/roa/net_margin/op_cf_per_share 仍是原披露口径（缺重列净利润与权益，无法重算）。
    vintage_mixed: dict[str, str] = {}
    for y, rec in annual.items():
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        if not ta or not tl:
            continue
        recalc = round(tl / ta * 100, 4)
        old, old_em = rec.get("debt_ratio"), rec.get("equity_multiplier")
        rec["debt_ratio"] = recalc
        rec["equity_multiplier"] = round(ta / (ta - tl), 6)
        if old is None or abs(old - recalc) <= 0.05:
            continue
        vintage_mixed[y] = (
            f"金额与 eps 为后一年年报重列数，接口比率为当年年报原披露数；"
            f"debt_ratio 已按重列金额重算 {recalc}%（原披露 {old}%，差 {round(old - recalc, 4)}pp）、"
            f"equity_multiplier 重算 {rec['equity_multiplier']}（原披露 {old_em}）；"
            f"roe_weighted/roa/net_margin/op_cf_per_share 仍为原披露口径，不可与本行金额互推"
        )

    # 年报手工表：补 F10 缺失的投资收益率/偿付能力/新业务价值/投资资产/员工数/股息（2007—2025）
    fx_implied, dividend_per10, fx_check = patch_annual_hk_report(code, annual)

    # 交叉验证：年报原披露「总权益」× 官方年末中间价 应等于 F10 的（总资产 − 总负债）。
    # 对不上的年份恰好是接口按后一年年报重列的年份（手工表存的是原披露数），
    # 与 fx_check 标出的年份互相印证。
    equity_check: dict[str, str] = {}
    for y, rec in annual.items():
        te, ta, ear = rec.get("total_equity"), rec.get("total_assets"), rec.get("equity_asset_ratio")
        if not (te and ta and ear):
            continue
        share = round(te / ta * 100, 4)
        diff = round(share - ear, 4)
        if abs(diff) > 0.05:
            equity_check[y] = (f"年报原披露总权益折人民币后占 F10 总资产 {share}%，与 F10（总资产−总负债）"
                               f"自算的 {ear}% 差 {diff}pp——该年 F10 金额为后一年年报的重列比较列")

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富港股公司数据接口（主要指标） RPT_HKF10_FN_MAININDICATOR（各期年报数），"
                   "投资收益率、偿付能力充足率、寿险新业务价值、投资资产、员工数与逐年股息"
                   "取自港交所 HKEXnews 中文年报原文（data/raw/annual_00966_2007~2025.pdf，"
                   "见 HK_REPORT_00966 手工表）。"
                   "中国太平仅在港交所上市（00966.HK），无 A 股年报，因此不适用「A/H 都有时优先取 A 股」"
                   "的取数规则；年报本身以港元编制，接口返回的金额已按各年年末汇率折成人民币"
                   "（行内 CURRENCY 写 HKD、IS_CNY_CODE 写 0 是误标，2025 年隐含 0.90322、2024 年 0.92600，"
                   "已用 2025 年报业绩公告原文反推核验）"),
        "unit_note": "金额字段单位为人民币元（接口按当年年末汇率由港元折算）；比率字段单位为 %",
        "caliber_note": ("金额已折成人民币，可与五家 A 股险企同图直接比大小；但每年用各自年末汇率折算，"
                         "太平自身的同比含汇率漂移，利润按期末价而非平均价折算。"
                         "2023 年起同步执行 IFRS17 + IFRS9，接口 2022 年行已是重述可比数："
                         "营业收入 2021 年 2,582.5→2022 年 1,081.0 亿元、保险服务收入 2,146.6→972.8 亿元，"
                         "落差是换口径不是业务下滑。"
                         "港股 F10 主要指标本身不提供保险专项指标，net_roi/total_roi/compre_roi、"
                         "solvency_ar_life/_pc/_pension（及 _core）、nbv_life/nbv_rate、invest_asset_total、"
                         "parent_equity/total_equity、staff_num、dividend_per10 均来自年报手工表 HK_REPORT_00966，"
                         "口径断点见该表注释；2000—2006 年这些字段为空（HKEXnews 检索库覆盖自 2007-04 起）。"
                         "太平是控股集团，偿付能力按太平人寿/太平财险/太平养老分别披露，集团层面无单一指标，"
                         "故 solvency_ar 留空，不与 A 股同名序列混画；"
                         "nbv_life 是太平人寿（持股 75.1%）单体数，不是集团合计，与 A 股五家的集团/寿险口径不完全同层。"
                         "surrender_rate_life 19 份年报全无披露（只有退保金额、±10% 敏感性与 13/25 个月继续率），"
                         "是披露缺口而非取数遗漏。"
                         "roe_weighted 取接口 ROE_AVG（平均净资产口径），与 A 股「加权平均 ROE」算法不完全一致。"
                         "接口 *_YOY 同比字段是按港元原值算的（2025 年 +220.93% 为港元口径），与折算后金额"
                         "自算的同比不等，故未采集；DPS_HKD 字段为快照值（2000—2024 年各行同为 1.58），"
                         "不能当逐年股息序列用，dividend_per10 改由年报宣派股息 × 10 × 当年隐含汇率算得。"
                         "total_share 是当前已发行股数快照（各年同为 3,594,018,538 股），bps 亦按该股数"
                         "反算（= 母公司权益 ÷ 当前股数），与年报披露的当年每股净资产不等，只可看趋势；"
                         "eps 是按当年加权股数算的，可与年报对上。"
                         "vintage_note 列出的年份存在「金额=重列 / 比率=原披露」混排，见该字段说明。"),
        "annual": annual,
        "vintage_note": vintage_mixed,
        "fx_rate_used": HKD_CNY_YEAR_END,
        "fx_implied": fx_implied,
        "fx_note": ("年报手工表的港币金额按 fx_rate_used（中国外汇交易中心受权公布的当年最后一个交易日"
                    "人民币对港元中间价）折成人民币。校验：折出来的 nbv_life 逐年复现年报正文自己披露的"
                    "人民币新业务价值（2018 115.99 / 2019 94.16 / 2020 73.93 / 2021 74.44 / 2022 66.62 / "
                    "2023 68.07 / 2024 84.29 / 2025 86.61 亿元）。"
                    "fx_implied = F10 人民币总资产 ÷ 年报港币总资产，仅作交叉校验：19 年里 13 年与官方"
                    "中间价一致，不一致的年份（F10 金额取自后一年年报的重列比较列）见 fx_check，"
                    "折算不采用隐含汇率。"),
        "fx_check": fx_check,
        "equity_check": equity_check,
        "holders_end_date": None,
        "holders": [],
        "dividend_per10": dividend_per10,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="股票代码，默认全部")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重新拉取")
    args = ap.parse_args()

    codes = args.codes or list(INSURERS) + list(INSURERS_HK)
    unknown = [c for c in codes if c not in INSURERS and c not in INSURERS_HK]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(INSURERS) + list(INSURERS_HK)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build_insurer_hk(code, args.refresh) if code in INSURERS_HK \
            else build_insurer(code, args.refresh)
        out = OUT_DIR / f"insurer_{code}_annual.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        yrs = sorted(data["annual"])
        print(f"    -> {out.relative_to(ROOT)}  ({len(yrs)} 年，{yrs[0]}~{yrs[-1]}，"
              f"股东 {len(data['holders'])} 名 @ {data['holders_end_date']})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


