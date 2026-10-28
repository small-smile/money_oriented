#!/usr/bin/env python
"""把 data/tables 下的 JSON 成品表（磁盘文件，经 backend/jsonstore.py 读）拆成
data/sql/tables/*.sql 定义的 MySQL 结构化表。MySQL 里不存 JSON 原文。

用法：
  # 只解析并打印各表将写入的行数，不连库：
  ./venv/bin/python data/extract/load_to_mysql.py --dry-run

  # 真实入库（需先 pip install pymysql；连接参数读环境变量 MYSQL_*，缺的从仓库根 .env 补；
  # --init 先按序执行 data/sql/tables/*.sql 建表；--reload 先清空本脚本写的表再全量重灌，可反复跑）：
  ./venv/bin/python data/extract/load_to_mysql.py --init --reload

财务表以 data/sql/tables 里现有的表为主：跨行业公共列（损益/资产负债/现金流/现金分红/审计意见/年末股东户数）进 financials 宽表，
银行专属列进 bank_financials，其余行业各自的专属列进 <行业>_financials（与 bank_financials 同构，同主键按需 JOIN）。
annual JSON 里每个字段都必须落到某一列；没登记映射的数值字段写进 data_anomaly（reason=unmapped_field），不静默丢弃。
JSON 沿用数据源字段名，落库时按 (SQL 列名, JSON 源字段名) 映射成标准英文财报列名。
company_code 是带交易所前缀的实体键（sh.601077 / sz.000001 / hk.01578，见 company.sql）；JSON 与文件名里的裸代码在这里换算。
只收 data/tables 下的源 JSON（oil/宏观 CSV 未纳入）。股权数据从 annual 的 holders 与 holders_manual.json 取，
银行股东手工件（shareholder_manual / ar_manual / 渝农商行精编件）的户数与分红按年报原文盖过接口值；
年报正文手工层 bank_<code>_detail_manual.json 进 bank_report_detail，经营口径表进 <行业>_operating，说明原文进 data_note。
银行详情页图表与每公司股东表是派生物，不入库也不落文件（后端从这些表拼回输入现算，见 backend/bank_charts_db.py、holders_db.py）；
渝农商行精编件里业绩/规模/息差等图表序列与环形图、公司简介/治理类文档（*_profile*.json、tech_09888_holders_manual.json）尚未拆表。
只写 data/sql/tables 里有建表语句的表；解析了但没有建表文件的表只在行数清单里标「跳过」，不写库。
"""
import os
import re
import sys
import glob
import argparse
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from backend import jsonstore  # noqa: E402  JSON 成品表读写统一走这里（磁盘文件）
from backend import db  # noqa: E402  MySQL 连接参数与后端同一份（环境变量 MYSQL_*，缺的从 .env 补）
from industry_columns import (CEMENT_COLS, DEVELOPER_COLS, INSURER_COLS, INSURER_TEXT_COLS,  # noqa: E402
                              TECH_COLS, TELECOM_COLS, TELECOM_TEXT_COLS,
                              CEMENT_OPERATING_COLS, CEMENT_OPERATING_TEXT_COLS,
                              TELECOM_OPERATING_COLS, TELECOM_OPERATING_TEXT_COLS, TELECOM_OPERATING_FLAG_COLS,
                              TECH_OPERATING_COLS, TECH_OPERATING_TEXT_COLS, TECH_OPERATING_FLAG_COLS)

TABLES = os.path.join(ROOT, "data", "tables")
SCHEMA_DIR = os.path.join(ROOT, "data", "sql", "tables")   # 每表一个 NN_<表>.sql，按文件名序建表

INDUSTRIES = ["bank", "insurer", "developer", "cement", "telecom", "tech", "food"]

# 跨行业公共列四表合一并入 financials 宽表（与 data/sql/tables/financials.sql 一致）；其余 annual 指标进 financial_metric 长表。
# 每项 (SQL 列名, JSON 源字段名)：成品表 JSON 沿用数据源(东方财富接口)字段名，落库时映射成标准英文财报列名，把厂商命名挡在数据层边界外。
REVENUE_COLS = [("operating_revenue", "operate_income"), ("operating_profit", "operate_profit"),
                ("profit_before_tax", "total_profit"), ("net_profit", "netprofit"),
                ("net_profit_attr_parent", "parent_netprofit"), ("net_margin", "net_margin"),
                ("roe_weighted", "roe_weighted"), ("eps", "eps")]
ASSET_COLS = [("total_assets", "total_assets"), ("total_liabilities", "total_liabilities"),
              ("total_equity", "total_equity"), ("equity_attr_parent", "parent_equity"),
              ("share_capital", "share_capital"), ("bps", "bps")]
CASHFLOW_COLS = [("net_cash_operating", "netcash_operate"), ("net_cash_investing", "netcash_invest"),
                 ("net_cash_financing", "netcash_finance"), ("operating_cf_per_share", "op_cf_per_share")]
# 审计信息（文本列，非数值）：审计意见取 annual 的 opinion_type；审计机构与关键审计事项 JSON 暂未提供，缺省 NULL，不臆造，
# 后续 annual JSON 补这些字段即自动入库。关键审计事项(key_audit_matters)与应对(audit_responses)多项按报告顺序编号，两字段编号一一对应。
AUDIT_COLS = [("auditor", "auditor"), ("audit_opinion", "opinion_type"),
              ("key_audit_matters", "key_audit_matters"), ("audit_responses", "audit_responses")]
FIN_NUM_COLS = (*REVENUE_COLS, *ASSET_COLS, *CASHFLOW_COLS)   # financials 表的数值列（损益+资产负债+现金流）
# 现金分红列：dividend_per_share / dividend_payout_ratio 是 STORED 生成列，不插入。
DIVIDEND_COLS = ("dividend_per_10_shares", "dividend_unit", "dividend_total", "dividend_source")
# 股东户数列：取 holder_num 里日期为 12-31 的行（年报「报告期末股东总数」），其余季度/披露日前月末的行不进 financials。
HOLDER_COUNT_COLS = ("total_holders", "a_share_holders", "h_share_holders")
# 银行专属列进 bank_financials（与 data/sql/tables/bank_financials.sql 一致）；只对 industry == "bank" 生效。
BANK_COLS = [("net_interest_income", "interest_ni"), ("net_fee_commission_income", "fee_ni"),
             ("net_interest_margin", "nim"), ("net_interest_spread", "nis"),
             ("general_admin_expenses", "manage_expense"), ("cost_income_ratio", "cost_income_ratio"),
             ("return_on_assets", "roa"), ("credit_impairment_loss", "credit_impairment"),
             ("asset_impairment_loss", "asset_impairment"),
             ("gross_loans", "gross_loans"), ("net_loans", "loan_advance"),
             ("loan_loss_allowance", "loan_loss_allowance"), ("customer_deposits", "total_deposits"),
             ("customer_deposits_balance_sheet", "accept_deposit"), ("loan_to_deposit_ratio", "ltd_ratio"),
             ("non_performing_loans", "npl_amount"), ("non_performing_loan_ratio", "npl_ratio"),
             ("non_performing_loan_formation", "npl_formation"),
             ("non_performing_loan_formation_rate", "npl_formation_rate"),
             ("overdue_loans", "overdue_loans"), ("net_charge_off", "net_charge_off"),
             ("provision_coverage_ratio", "provision_coverage"), ("loan_allowance_ratio", "loan_provision_ratio"),
             ("capital_adequacy_ratio", "car"), ("tier1_capital_ratio", "tier1"),
             ("core_tier1_capital_ratio", "cet1"), ("leverage_ratio", "leverage_ratio"),
             ("liquidity_coverage_ratio", "lcr"), ("net_stable_funding_ratio", "nsfr"),
             ("equity_asset_ratio", "equity_asset_ratio"),
             ("cash_and_central_bank_deposits", "cash_deposit_pbc"), ("due_from_banks", "deposit_interbank"),
             ("placements_with_banks", "lend_fund"), ("reverse_repurchase_assets", "buy_resale"),
             ("trading_financial_assets", "trade_finasset"), ("fvtpl_financial_assets", "fvtpl_finasset"),
             ("fvtoci_financial_assets", "fvtoci_finasset"),
             ("amortized_cost_financial_assets", "amortize_cost_finasset"),
             ("debt_investments", "creditor_invest"), ("other_debt_investments", "other_creditor_invest"),
             ("other_equity_investments", "other_equity_invest"),
             ("borrowings_from_central_bank", "loan_pbc"), ("due_to_banks", "iofi_deposit"),
             ("placements_from_banks", "borrow_fund"), ("repurchase_agreements", "sell_repo"),
             ("bonds_payable", "bond_payable"), ("employee_count", "staff_num"),
             ("operating_expenses", "operate_expense"), ("other_business_costs", "other_business_cost"),
             ("taxes_and_surcharges", "operate_tax"), ("income_tax_expense", "income_tax"),
             ("net_profit_attr_non_controlling_interests", "minority_interest"),
             ("equity_attr_non_controlling_interests", "minority_equity"),
             ("other_comprehensive_income", "oci"), ("total_shares", "total_share"),
             ("liquidity_ratio", "liquidity_ratio"), ("overdue_loans_over_90_days", "overdue_90plus"),
             ("loan_impairment_charge", "loan_impairment_charge"), ("loan_write_offs", "write_off"),
             ("loan_loss_allowance_transferred_out", "transfer_out"),
             ("recoveries_of_loans_written_off", "recovery"),
             ("loan_loss_allowance_amortized_cost", "loan_allowance_amortized")]
CONSUMED = {j for _, j in (*FIN_NUM_COLS, *AUDIT_COLS)}   # financials 已收的 JSON 源字段名（basic_eps 走 FIELD_ALIASES 回退到 eps）
# 公司/零售贷款结构列取自 bank_<code>_detail_manual.json 的 loantrend（按 years 对齐的数组，亿元）。
LOAN_STRUCTURE_COLS = [("corporate_loans", "corp"), ("retail_loans", "retail"),
                       ("corporate_non_performing_loans", "nplBalanceCorp"),
                       ("retail_non_performing_loans", "nplBalanceRetail")]
# 其余行业的专属列进 <行业>_financials（与 data/sql/tables/<行业>_financials.sql 一致），映射清单在 industry_columns.py；
# INDUSTRY_TEXT_COLS 是同表里的文本列（年报口径说明等），按原文存；INDUSTRY_FLAG_COLS 是 true/false 标记，存 1/0。
INDUSTRY_COLS = {"insurer": INSURER_COLS, "developer": DEVELOPER_COLS, "cement": CEMENT_COLS,
                 "telecom": TELECOM_COLS, "tech": TECH_COLS}
INDUSTRY_TEXT_COLS = {"insurer": INSURER_TEXT_COLS, "telecom": TELECOM_TEXT_COLS}
INDUSTRY_FLAG_COLS = {"telecom": [("revenue_fields_mismatch", "rev_field_mismatch")]}
# 个别文件里同名字段含义不同：中国移动港股年报序列的 depreciation 是营运支出里的折旧及摊销（百万元），
# A 股三家的 depreciation 是现金流量表补充资料的资产减值准备（元，见 TELECOM_COLS）。
FILE_COLUMN_OVERRIDES = {"telecom_00941_annual.json": {"depreciation": ("depreciation_and_amortization", "depreciation", 1e6)}}
# 与已映射字段同义的源字段：{源字段: (同义的 JSON 字段, 倍数)}。同义字段为空才补，两边都有且不等记 data_anomaly。
FIELD_ALIASES = {
    "*": {"main_total_assets": ("total_assets", 1), "main_liability": ("total_liabilities", 1),   # 东财「主要指标」接口给的同一科目
          "main_total_equity": ("total_equity", 1), "main_parent_netprofit": ("parent_netprofit", 1),
          "total_revenue": ("total_operate_income", 1), "basic_eps": ("eps", 1)},
    "telecom": {"revenue": ("operate_income", 1), "totalRevenue": ("operate_income", 1e6),     # 中国移动港股年报序列为百万元
                "netProfit": ("parent_netprofit", 1e6), "ocf": ("netcash_operate", 1e6)},
    "tech": {"revenue": ("operate_income", 1e6), "netIncome": ("parent_netprofit", 1e6),     # 百度 20-F，百万元
             "netIncomeIncNci": ("netprofit", 1e6), "assets": ("total_assets", 1e6),
             "liabilities": ("total_liabilities", 1e6), "equity": ("parent_equity", 1e6),
             "equityIncNci": ("total_equity", 1e6), "opCashFlow": ("netcash_operate", 1e6)},
}
PER_SHARE_DIVIDEND_FIELDS = {"dividendTotal": "港元"}   # 每股股息 → financials 每 10 股派息（只做 ×10 的单位换算）
# 挂在文件顶层、按年份组织的字段，先并进当年那行再映射（hk_crosscheck 是 {年:{字段:值}}，其余是 {年:值}）
YEAR_LEVEL_KEYS = ("fx_rate_used", "fx_implied", "fx_check", "equity_check", "vintage_note", "hk_crosscheck")

# annual JSON 中可稳定识别的资产负债表项目。现有 JSON 没有逐项原文名称，
# 因此 raw_item_name、层级和页码留空，待补录年报原文时填写。
BANK_BALANCE_SHEET_COLS = [
    ("asset", "total_assets", "资产合计", "total_assets"),
    ("asset", "cash_deposit_pbc", "现金及存放中央银行款项", "cash_and_central_bank_deposits"),
    ("asset", "deposit_interbank", "存放同业和其他金融机构款项", "due_from_banks"),
    ("asset", "lend_fund", "拆出资金", "placements_with_banks"),
    ("asset", "buy_resale", "买入返售金融资产", "reverse_repurchase_assets"),
    ("asset", "loan_advance", "发放贷款和垫款", "net_loans"),
    ("asset", "trade_finasset", "交易性金融资产", "trading_financial_assets"),
    ("asset", "fvtpl_finasset", "以公允价值计量且其变动计入当期损益的金融资产", "fvtpl_financial_assets"),
    ("asset", "creditor_invest", "债权投资", "debt_investments"),
    ("asset", "amortize_cost_finasset", "以摊余成本计量的金融资产", "amortized_cost_financial_assets"),
    ("asset", "other_creditor_invest", "其他债权投资", "other_debt_investments"),
    ("asset", "fvtoci_finasset", "以公允价值计量且其变动计入其他综合收益的金融资产", "fvtoci_financial_assets"),
    ("asset", "other_equity_invest", "其他权益工具投资", "other_equity_investments"),
    ("liability", "total_liabilities", "负债合计", "total_liabilities"),
    ("liability", "accept_deposit", "吸收存款", "customer_deposits_balance_sheet"),
    ("liability", "loan_pbc", "向中央银行借款", "borrowings_from_central_bank"),
    ("liability", "iofi_deposit", "同业和其他金融机构存放款项", "due_to_banks"),
    ("liability", "borrow_fund", "拆入资金", "placements_from_banks"),
    ("liability", "sell_repo", "卖出回购金融资产款", "repurchase_agreements"),
    ("liability", "bond_payable", "应付债券", "bonds_payable"),
    ("equity", "total_equity", "股东权益合计", "total_equity"),
    ("equity", "parent_equity", "归属于母公司股东权益", "equity_attr_parent"),
    ("equity", "minority_equity", "少数股东权益", "minority_equity"),
    ("equity", "share_capital", "股本", "share_capital"),
]

YEAR = re.compile(r"^(19|20)\d{2}$")


def _num(v):
    """把 12,345 / 3.4% / '' / '-' 之类清成 float 或 None。"""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).replace(",", "").replace("%", "").strip()
    if s in ("", "-", "—", "N/A", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _txt(v):
    if v is None:
        return None
    if isinstance(v, list):                   # mixLayers 之类的键名清单
        v = ",".join(str(x) for x in v)
    s = str(v).strip()
    return s or None


def _entity_code(code):
    """JSON 与文件名里的裸代码 → 库里的实体键（见 company.sql）：6 位 A 股按交易所加 sh./sz./bj.，5 位港股加 hk.。
    认不出交易所的直接报错，不猜。"""
    c = _txt(code)
    if c is None or "." in c:
        return c
    if len(c) == 5 and c.isdigit():
        return "hk." + c
    exchange = {"6": "sh", "0": "sz", "3": "sz", "4": "bj", "8": "bj"}.get(c[:1])
    if len(c) == 6 and c.isdigit() and exchange:
        return "%s.%s" % (exchange, c)
    raise ValueError("认不出交易所的代码：%r" % c)


# 社融增量分项：(SQL 列名, JSON 源字段名)，源字段与原表科目的对应见 social_financing_pboc_flow.json 的 columns。
SOCIAL_FINANCING_FLOW_COLS = [
    ("total", "total"), ("renminbi_loans", "rmb_loans"), ("foreign_currency_loans", "fx_loans"),
    ("entrusted_loans", "entrusted_loans"), ("trust_loans", "trust_loans"),
    ("undiscounted_bankers_acceptances", "undiscounted_ba"), ("corporate_bonds", "corp_bonds"),
    ("government_bonds", "gov_bonds"), ("domestic_equity_financing", "equity"),
    ("asset_backed_securities", "abs"), ("loan_write_offs", "loan_writeoff")]
CHANGE_STATUS = ("新进", "加仓", "减仓", "不变")   # 接口 HOLDER_STATE 的持股变动状态；其余取值是股份类别或股份性质
# 股东/股份性质原文 → (is_state, is_foreign, is_natural)。国资指国有（国有法人、国有法人股）；
# 一般法人股是股份分类里与国有法人股相对的社会法人股；内资法人股、境外法人说明不了是否国有，is_state 留空。
HOLDER_NATURE_FLAGS = {
    "国有法人": (1, 0, 0), "国有法人股": (1, 0, 0), "非境外上市股（国有法人）": (1, 0, 0),
    "一般法人股": (0, 0, 0), "内资法人股": (None, 0, 0),
    "境内自然人": (0, 0, 1), "境外法人": (None, 1, 0),
}
HOLDER_NATURE_UNKNOWN = ("其他", "未知")   # 年报原文就写「其他/未知」，三个标志都留空，不算缺对照
LOADER = "load_to_mysql.py"                      # data_anomaly.source：本脚本写的行，--reload 时只清这些


def _industry_columns(industry):
    """<行业>_financials 的数值列：映射清单 + 文件覆盖里出现的列，按出现先后去重（一列可由多个源字段供数）。"""
    cols = list(INDUSTRY_COLS[industry]) + [t for f, ov in FILE_COLUMN_OVERRIDES.items()
                                           if f.startswith(industry + "_") for t in ov.values()]
    return list(dict.fromkeys(t[0] for t in cols))


# 经营口径表 → (数值列, 文本列, 标记列)，映射清单在 industry_columns.py
OPERATING_TABLES = {
    "cement_operating": (CEMENT_OPERATING_COLS, CEMENT_OPERATING_TEXT_COLS, []),
    "telecom_operating": (TELECOM_OPERATING_COLS, TELECOM_OPERATING_TEXT_COLS, TELECOM_OPERATING_FLAG_COLS),
    "tech_operating": (TECH_OPERATING_COLS, TECH_OPERATING_TEXT_COLS, TECH_OPERATING_FLAG_COLS),
}
HOLDER_COUNT_FIELDS = (*HOLDER_COUNT_COLS, "domestic_share_holders")   # Loader.holder_counts 每格的四个户数


def _operating_columns(table):
    """<行业>_operating 的列（除主键）：数值列按出现先后去重，再接文本列、标记列；没有 source 映射的补一列来源文件。"""
    num, text, flag = OPERATING_TABLES[table]
    cols = list(dict.fromkeys(t[0] for t in num)) + [c for c, _ in (*text, *flag)]
    return cols if "source" in cols else cols + ["source"]


# 每张表的插入列（顺序即 add() 时元组的顺序）；带 AUTO_INCREMENT id 的表这里不列 id。
COLUMNS = {
    "company": ("company_code", "short_name", "full_name", "industry", "a_code", "h_code",
                "same_entity", "us_code", "tier", "group_name", "note", "source"),
    "financials_meta": ("company_code", "currency", "unit_note", "caliber_note", "dividend_note",
                        "exchange_rate_note", "a_share_report_from", "source", "source_file", "fetched_at"),
    "financials": ("company_code", "fiscal_year",
                   *[c for c, _ in FIN_NUM_COLS], *DIVIDEND_COLS, *[c for c, _ in AUDIT_COLS],
                   *HOLDER_COUNT_COLS, "source"),
    "bank_financials": ("company_code", "fiscal_year", *[c for c, _ in BANK_COLS],
                        *[c for c, _ in LOAN_STRUCTURE_COLS], "source"),
    **{"%s_financials" % i: ("company_code", "fiscal_year", *_industry_columns(i),
                             *[c for c, _ in INDUSTRY_TEXT_COLS.get(i, [])],
                             *[c for c, _ in INDUSTRY_FLAG_COLS.get(i, [])], "source")
       for i in INDUSTRY_COLS},
    "bank_balance_sheet_item": (
        "company_code", "fiscal_year", "statement_type", "section",
        "item_code", "item_name", "raw_item_name", "parent_item_code",
        "item_level", "raw_value", "raw_unit", "value", "unit", "scope",
        "accounting_standard", "caliber_note", "source_file", "source_section",
        "source_page", "is_derived", "missing_reason"),
    "segment_revenue": ("company_code", "fiscal_year", "segment_code", "raw_item_name", "is_subtotal",
                        "revenue", "line_order", "source"),
    "bank_report_detail": ("company_code", "fiscal_year", "period_label", "topic", "item_name", "item_order", "measure",
                           "value", "unit", "raw_value", "raw_unit", "source_file"),
    "bank_bond_issue": ("company_code", "bond_order", "bond_name", "issue_date", "tenor", "coupon_rate",
                        "issue_amount", "maturity", "status", "source_file"),
    **{t: ("company_code", "fiscal_year", *_operating_columns(t)) for t in OPERATING_TABLES},
    "shareholder": ("company_code", "fiscal_year", "as_of_date", "holder_rank", "holder_name", "holder_short",
                    "holder_category", "is_state", "is_foreign", "is_natural", "holder_nature", "hold_num", "ratio",
                    "total_shares", "shares_type", "raw_shares_type", "pledged_shares", "chg_shares", "raw_change",
                    "change_status", "raw_state", "source"),
    "shareholder_meta": ("company_code", "holders_caliber", "caliber_note", "source", "factions_source",
                         "history_source"),
    "shareholder_count": ("company_code", "as_of_date", *HOLDER_COUNT_COLS, "domestic_share_holders", "source",
                          "revised_by"),
    "shareholder_concentration": ("company_code", "as_of_date", "top1_holder_ratio", "top3_holders_ratio",
                                  "top10_holders_ratio", "top1_holder_ratio_excluding_nominees",
                                  "top3_holders_ratio_excluding_nominees", "top1_holder_name",
                                  "top1_holder_name_excluding_nominees", "top1_holder_voting_ratio", "is_reconstructed",
                                  "source"),
    "shareholder_faction": ("company_code", "faction_title", "faction_order", "holder_name", "member_order", "color",
                            "basis", "source"),
    "share_capital_year_end": ("company_code", "fiscal_year", "total_shares", "change_summary", "share_split_factor",
                               "source"),
    "social_financing_stock": ("period_month", "amount", "year_on_year_growth", "source"),
    "social_financing_flow": ("period_month", *[c for c, _ in SOCIAL_FINANCING_FLOW_COLS], "source"),
    "data_note": ("company_code", "source_file", "topic", "note"),
    "data_gap": ("company_code", "description", "reason", "source_file"),
    "data_anomaly": ("company_code", "source_file", "target_table", "field_name", "period", "raw_value",
                     "reason", "source"),
}
# 插入顺序：company 先建（外键父表）；--reload 按逆序清
INSERT_ORDER = ["company", "financials_meta", "financials", "bank_financials",
                *["%s_financials" % i for i in INDUSTRY_COLS], "bank_balance_sheet_item", "segment_revenue",
                "bank_report_detail", "bank_bond_issue", *OPERATING_TABLES,
                "shareholder", "shareholder_meta", "shareholder_count", "shareholder_concentration",
                "shareholder_faction", "share_capital_year_end", "social_financing_stock",
                "social_financing_flow", "data_note", "data_gap", "data_anomaly"]


class Loader:
    def __init__(self):
        self.rows = {t: [] for t in COLUMNS}
        self.companies = {}       # 实体键 -> company 行（list，载完再转 tuple）
        self.dividends = {}       # (code, year) -> (per10, unit, total)；最后并入 financials 行
        self.holder_counts = {}   # (code, 截止日) -> [合计, A股, H股, 内资股, 来源文件]；全部期进 shareholder_count，12-31 再并入 financials
        self.shareholders = {}    # (code, year) -> [shareholder 行]；一期只取一个来源
        self.concentrations = {}  # (code, 截止日) -> shareholder_concentration 行
        self.holder_meta = {}     # code -> [名册口径, 口径说明, 名册来源, 分组出处, 序列出处]

    def add(self, table, row):
        self.rows[table].append(row)

    def add_dividend(self, code, year, per10, unit, total, source, override=False):
        """override=True 用于年报原文手工件：盖过东财接口值（接口把港元宣派折成了人民币）。source 记进 dividend_source。"""
        if override or (code, year) not in self.dividends:
            self.dividends[(code, year)] = (per10, unit, total, source)

    def add_holder_count(self, code, date, counts, source, override=False):
        """counts = [合计, A股, H股, 内资股]。override=True（holders_manual 年报原文）整格盖过接口值；否则只补空着的格。"""
        cell = self.holder_counts.get((code, date))
        if cell is None or override:
            self.holder_counts[(code, date)] = [*counts, source, None]
        else:
            cell[:4] = [old if old is not None else new for old, new in zip(cell[:4], counts)]

    def merge_holder_count(self, code, date, counts, source):
        """银行年报原文手工件：非空格子盖过已有值，两边都有且不等记 data_anomaly；空格子保留已有值。
        改的是别的文件先给出的期次时，revised_by 记本文件（source 仍是先给出的那份）。"""
        if all(c is None for c in counts):
            return
        cell = self.holder_counts.get((code, date))
        if cell is None:
            cell = self.holder_counts[(code, date)] = [None, None, None, None, source, None]
        elif cell[4] != source:
            cell[5] = source
        for i, new in enumerate(counts):
            if new is None:
                continue
            if cell[i] is not None and not _same(cell[i], new):
                self.add("data_anomaly", (code, source, "shareholder_count", HOLDER_COUNT_FIELDS[i], date,
                                          "%s（原值 %s）" % (new, cell[i]), "conflicting_duplicate", LOADER))
            cell[i] = new

    def merge_dividend(self, code, year, per10, source):
        """每 10 股派息的年报原文值盖过已有值，单位与分红总额沿用已有的；两边不等记 data_anomaly。"""
        per10_old, unit, total = (self.dividends.get((code, year)) or (None, None, None))[:3]
        if per10_old is not None and not _same(per10_old, per10):
            self.add("data_anomaly", (code, source, "financials", "dividend_per_10_shares", str(year),
                                      "%s（原值 %s）" % (per10, per10_old), "conflicting_duplicate", LOADER))
        self.dividends[(code, year)] = (per10, unit or "元", total, source)

    def add_concentration(self, code, r, source, override=False):
        """集中度一期一行：holder_concentration[{date,top1,top3,top10,top1_ex,top3_ex,top1_name,top1_ex_name}]；
        H 股年报口径的 concentrationHist 另带 recon（recon/disc）。"""
        if override or (code, r["date"]) not in self.concentrations:
            self.concentrations[(code, r["date"])] = (code, r["date"], *[_num(r.get(k)) for k in (
                "top1", "top3", "top10", "top1_ex", "top3_ex")], _txt(r.get("top1_name")),
                _txt(r.get("top1_ex_name")), _num(r.get("top1_vote")),
                {"recon": 1, "disc": 0}.get(r.get("recon")), source)

    def set_holder_meta(self, code, values):
        """后载入的非空值盖过先前的（holders_manual 在 annual 之后载入）。"""
        cur = self.holder_meta.setdefault(code, [None] * 5)
        cur[:] = [new if new is not None else old for old, new in zip(cur, values)]

    def set_shareholders(self, rows, override=False):
        """前十名股东按期整份取一个来源：override=True（holders_manual 年报原文）整期替换接口那份，不逐行拼。"""
        if rows and (override or rows[0][:2] not in self.shareholders):
            self.shareholders[rows[0][:2]] = rows

    def finish(self):
        """收尾：公司行转 tuple；股东名册/户数/集中度/口径落行；分红与年末户数并进 financials。"""
        self.rows["company"] = [tuple(c) for c in self.companies.values()]
        self.rows["shareholder"] = [r for rows in self.shareholders.values() for r in rows]
        self.rows["shareholder_count"] = [(code, date, *v) for (code, date), v in sorted(self.holder_counts.items())]
        self.rows["shareholder_concentration"] = [r for _, r in sorted(self.concentrations.items())]
        self.rows["shareholder_meta"] = [(code, *v) for code, v in self.holder_meta.items() if any(v)]
        year_end = {(code, _year_end(date)): tuple(v[:3]) for (code, date), v in self.holder_counts.items()
                    if _year_end(date)}
        cols = COLUMNS["financials"]
        rows = {(r[0], r[1]): list(r) for r in self.rows["financials"]}
        for extra, names in ((self.dividends, DIVIDEND_COLS), (year_end, HOLDER_COUNT_COLS)):
            lo = cols.index(names[0])
            for (code, yr), vals in extra.items():
                row = rows.setdefault((code, yr), [code, yr] + [None] * (len(cols) - 2))
                row[lo:lo + len(names)] = vals
        self.rows["financials"] = [tuple(r) for r in rows.values()]

    def ensure_company(self, raw_code, industry="", name=None):
        """annual 等文件里出现、company_codes.json 没登记的裸代码补一行（如中国移动港股年报序列 00941），返回实体键。"""
        code = _entity_code(raw_code)
        if code and code not in self.companies:
            twin = next((c[0] for c in self.companies.values() if raw_code in (c[4], c[5])), None)
            note = "company_codes.json 未登记此代码" + (
                "；%s 已挂在 %s 名下，本行只承载按该代码披露的那条序列，两条序列不拼接" % (raw_code, twin) if twin else "")
            self.companies[code] = [code, name or raw_code, None, industry,
                                    raw_code if len(raw_code) == 6 else None,
                                    raw_code if len(raw_code) == 5 else None, 1, None, None, None, note, None]
        return code

    def set_company(self, e):     # 权威公司行来自 company_codes.json
        code = _entity_code(e["key"])
        self.companies[code] = [
            code, e.get("short") or e["key"], e.get("full"), e.get("industry") or "",
            e.get("a_code"), e.get("h_code"), 1 if e.get("same_entity", True) else 0,
            e.get("us_code"), e.get("tier"), None, _txt(e.get("note")),
            "\n".join(str(s) for s in e.get("sources") or []) or None]

    def set_group(self, code, group):
        if group:
            self.companies[code][COLUMNS["company"].index("group_name")] = group

    def counts(self):
        c = {t: len(r) for t, r in self.rows.items()}
        c["company"] = len(self.companies)
        return c


def _load_json(name):
    return jsonstore.read(os.path.join(TABLES, name))


def load_company(L):
    d = _load_json("company_codes.json")
    for e in d.get("entities", []) or []:
        L.set_company(e)
    for g in d.get("gaps", []) or []:
        L.add("data_gap", (None, _txt(g.get("item")) or "", _txt(g.get("why")), "company_codes.json"))


def _cols_values(row, cols):
    return [_num(row.get(j)) for _, j in cols]               # JSON 源字段名；eps 缺时由 basic_eps 回退见 FIELD_ALIASES


def _loan_structure(code):
    """{年: (公司余额, 零售余额, 公司不良, 零售不良)}，亿元换算为元；取 detail_manual（渝农商行取手工精编件），没有返回空。"""
    d, _ = _detail_doc(code)
    if d is None:
        return {}
    lt = d.get("loantrend") or {}
    out = {}
    for i, year in enumerate(lt.get("years") or []):
        vals = []
        for _, j in LOAN_STRUCTURE_COLS:
            v = _num(((lt.get(j) or [])[i:i + 1] or [None])[0])
            vals.append(None if v is None else round(v * 1e8, 2))
        if any(v is not None for v in vals):
            out[int(year)] = tuple(vals)
    return out


def _load_bank_balance_sheet(L, code, year, row, source_file, source, caliber_note, unit_note):
    """把 annual 中已有的标准化资产负债科目落成逐项表；缺失值不写行。"""
    amount_unit = "元" if "元" in (unit_note or "") else None
    for section, json_key, item_name, item_code in BANK_BALANCE_SHEET_COLS:
        value = _num(row.get(json_key))
        if value is None:
            continue
        L.add("bank_balance_sheet_item", (
            code, year, "consolidated", section, item_code, item_name,
            None, None, None, value, amount_unit, value, amount_unit,
            "合并", None, _txt(caliber_note), source_file, "资产负债表",
            None, 0, None))


def _same(a, b):
    return abs(a - b) <= max(1e-6, 1e-9 * max(abs(a), abs(b)))


def _apply_aliases(L, aliases, row, code, yr, file, table):
    """同义源字段并到已映射的那个字段上：那边为空才补（按倍数换成元），两边都有且不等记 data_anomaly。
    每股收益恰为 0 而当年归母净利润不为 0 的是接口拿 0 占位（如 601229、601825 的 2010 年 basic_eps），不拿来补，记 caliber_mismatch。"""
    for alias, (canon, scale) in aliases.items():
        v = _num(row.get(alias))
        if v is None:
            continue
        cur = _num(row.get(canon))
        if cur is None:
            if canon == "eps" and v == 0 and _num(row.get("parent_netprofit")):
                L.add("data_anomaly", (code, file, table, alias, str(yr),
                                       "0（归母净利润 %s，按接口占位处理，不补 eps）" % _num(row.get("parent_netprofit")),
                                       "caliber_mismatch", LOADER))
                continue
            row[canon] = v * scale
        elif not _same(cur, v * scale):
            L.add("data_anomaly", (code, file, table, alias, str(yr), "%s（%s 已有 %s）" % (v * scale, canon, cur),
                                   "conflicting_duplicate", LOADER))


def _industry_values(L, cols, row, code, yr, file, table):
    """(列, 源字段[, 倍数]) → {列: 值}；一列多个源字段时取非空的那个，都有且不等记 data_anomaly。"""
    vals = {}
    for t in cols:
        v = _num(row.get(t[1]))
        if v is None:
            continue
        v = v * t[2] if len(t) > 2 else v
        if t[0] in vals and not _same(vals[t[0]], v):
            L.add("data_anomaly", (code, file, table, t[1], str(yr), "%s（%s 已有 %s）" % (v, t[0], vals[t[0]]),
                                   "conflicting_duplicate", LOADER))
        else:
            vals.setdefault(t[0], v)
    return vals


def _meta_text(meta, *keys):
    """_meta 里的说明拼成一段：dict 逐项写成「键：值」，多段换行连接。"""
    parts = []
    for k in keys:
        v = meta.get(k)
        if isinstance(v, dict):
            parts += ["%s：%s" % (kk, vv) for kk, vv in v.items()]
        elif _txt(v):
            parts.append(_txt(v))
    return "\n".join(parts) or None


def load_annual(L):
    for industry in INDUSTRIES:
        for path in jsonstore.glob(os.path.join(TABLES, "%s_*_annual.json" % industry)):
            d = jsonstore.read(path)
            meta = d.get("_meta") or {}           # 中国移动港股年报序列、百度的文件只有 _meta 没有顶层元信息
            file = os.path.basename(path)
            raw_code = _txt(d.get("code")) or re.search(r"_(\w+)_annual", file).group(1)
            code = L.ensure_company(raw_code, industry, _txt(d.get("name")) or _txt(meta.get("company")))
            L.set_group(code, _txt(d.get("group")))
            src = _txt(d.get("source")) or _meta_text(meta, "sourcePrimary", "sourcePriority", "source", "generated_by")
            L.add("financials_meta", (
                code, _txt(d.get("currency")), _txt(d.get("unit_note")) or _txt(meta.get("unit")),
                _txt(d.get("caliber_note")) or _meta_text(meta, "coverage", "rules", "definitions", "note"),
                _txt(d.get("dividend_note")), _txt(d.get("fx_note")), d.get("a_report_from"),
                src, file, _utc_time(d.get("fetched_at")) or _txt(meta.get("extractedAt"))))
            for k, v in (meta.get("gaps") or {}).items():
                L.add("data_gap", (code, "%s：%s" % (k, v), None, file))
            loans = _loan_structure(raw_code) if industry == "bank" else {}
            no_loans = (None,) * len(LOAN_STRUCTURE_COLS)
            table = "%s_financials" % industry
            overrides = FILE_COLUMN_OVERRIDES.get(file, {})
            num_cols = [overrides.get(t[1], t) for t in (BANK_COLS if industry == "bank" else INDUSTRY_COLS.get(industry, []))]
            text_cols = INDUSTRY_TEXT_COLS.get(industry, [])
            flag_cols = INDUSTRY_FLAG_COLS.get(industry, [])
            aliases = {**FIELD_ALIASES["*"], **FIELD_ALIASES.get(industry, {})}
            consumed = (CONSUMED | {t[1] for t in (*num_cols, *text_cols, *flag_cols)} | set(aliases)
                        | set(PER_SHARE_DIVIDEND_FIELDS) | set(YEAR_LEVEL_KEYS))
            years = dict(d.get("annual") or {})
            for key in YEAR_LEVEL_KEYS:           # 顶层按年份挂的字段并进当年那行
                for y, v in (d.get(key) or {}).items():
                    row = years.setdefault(y, {})
                    if key == "hk_crosscheck":
                        row.update(v or {})
                        consumed |= set(v or {})
                    else:
                        row[key] = v
            for year, row in years.items():
                if not (YEAR.match(str(year)) and isinstance(row, dict)):
                    continue
                yr = int(year)
                _apply_aliases(L, aliases, row, code, yr, file, table)
                rv = _cols_values(row, REVENUE_COLS)
                av = _cols_values(row, ASSET_COLS)
                cf = _cols_values(row, CASHFLOW_COLS)
                au = [_txt(row.get(j)) for _, j in AUDIT_COLS]   # 审计机构/审计意见：文本，缺则 NULL
                if any(v is not None for v in (*rv, *av, *cf, *au)):   # 分红 4 列、股东户数 3 列先留空，最后并入
                    L.add("financials", (code, yr, *rv, *av, *cf, *[None] * len(DIVIDEND_COLS), *au, None, None, None, src))
                for f, unit in PER_SHARE_DIVIDEND_FIELDS.items():
                    if _num(row.get(f)) is not None:
                        L.add_dividend(code, yr, round(_num(row.get(f)) * 10, 6), unit, None, file)
                if industry == "bank":
                    bv = [*_cols_values(row, BANK_COLS), *loans.pop(yr, no_loans)]
                    if any(v is not None for v in bv):
                        L.add("bank_financials", (code, yr, *bv, src))
                    _load_bank_balance_sheet(
                        L, code, yr, row, file, src,
                        d.get("caliber_note"), d.get("unit_note"))
                elif num_cols:
                    vals = _industry_values(L, num_cols, row, code, yr, file, table)
                    vals.update({c: _txt(row.get(j)) for c, j in text_cols})
                    vals.update({c: {True: 1, False: 0}.get(row.get(j)) for c, j in flag_cols})
                    if any(v is not None for v in vals.values()):
                        L.add(table, (code, yr, *[vals.get(c) for c in COLUMNS[table][2:-1]], src))
                for k, v in row.items():   # 没登记映射的字段留痕，不静默丢
                    if k not in consumed and _txt(v) is not None:
                        L.add("data_anomaly", (code, file, table, k, str(yr), _txt(v)[:255], "unmapped_field", LOADER))
            dtot = d.get("dividend_total") if isinstance(d.get("dividend_total"), dict) else {}   # {年:亿元}，年报原文，禁反算
            for year, val in (d.get("dividend_per10") or {}).items():
                v = _num(val)
                if YEAR.match(str(year)) and v is not None:
                    L.add_dividend(code, int(year), v, "元", _num(dtot.get(year)), file)
            L.set_shareholders(_shareholder_rows(L, code, d.get("holders_end_date"), d.get("holders"), file))
            _load_holder_count(L, code, d.get("holder_num"), file)
            hc = d.get("holder_count")            # 纯 H 股行：名册那一期的户数，有的只给合计，有的拆内资股/H股
            if isinstance(hc, dict) and _txt(d.get("holders_end_date")):
                L.add_holder_count(code, d["holders_end_date"], [_num(hc.get("total")), None, _num(hc.get("hshare")),
                                                                 _num(hc.get("domestic"))], file)
            for r in d.get("holder_concentration") or []:
                if isinstance(r, dict) and _txt(r.get("date")):
                    L.add_concentration(code, r, file)
            L.set_holder_meta(code, [None, _txt(d.get("holders_note")), None, None, None])


def _load_holder_count(L, code, rows, source, override=False):
    """holder_num = [[日期, 合计, A股, H股], ...]；缺列记 NULL。全部期进 shareholder_count，12-31 那行另并入 financials。"""
    for r in rows or []:
        if isinstance(r, list) and r and _txt(r[0]):
            L.add_holder_count(code, _txt(r[0]), [_num(r[i]) if len(r) > i else None for i in (1, 2, 3)] + [None],
                               source, override)


def _year_end(date):
    """'2024-12-31' → 2024；不是 12-31 的日期返回 None。"""
    s = _txt(date) or ""
    return int(s[:4]) if YEAR.match(s[:4]) and s[4:] == "-12-31" else None


def _utc_time(v):
    """'2026-08-19 09:05 UTC' → '2026-08-19 09:05'：fetched_at 列是 DATETIME，时区记在列注释里。"""
    s = _txt(v)
    return re.sub(r"\s*UTC$", "", s) if s else None


def _share_class(raw):
    """接口的股份类别（流通A股 / 限售流通A股,流通H股 / H 股 …）→ A / H / A,H；认不出的返回 None。"""
    s = (_txt(raw) or "").replace(" ", "")
    return ",".join(c for c in ("A", "H") if c + "股" in s) or None


def _roster_year(end_date):
    """名册截止日 → 报告期：12-31 取当年；次年 1–4 月的披露日（20-F 的 beneficial ownership 日）记上一年度；
    其余日期（季报、半年报）返回 None，不入，免得错标成某个年报期。"""
    s = _txt(end_date) or ""
    if _year_end(s):
        return _year_end(s)
    m = re.fullmatch(r"((?:19|20)\d{2})-(0[1-4])-\d{2}", s)
    return int(m.group(1)) - 1 if m else None


def _raw_text(v):
    """原文照存（不去空白、空串保留）；数字转成文本，None 仍是 None。"""
    return None if v is None or isinstance(v, bool) else str(v)


def _shareholder_rows(L, code, end_date, holders, source):
    """前十名股东 → shareholder 行。年报名册（12-31）与 20-F 披露日名册才收，fiscal_year 见 _roster_year。
    接口的 state 是持股变动状态（新进/加仓/减仓/不变）；个别公司在这一栏写股份类别（H 股）或股份性质（国有法人股…），
    前者进 shares_type，后者进 holder_nature。holders_manual 的 shares_type 写的是股东性质（国有法人/境内自然人…），也进 holder_nature；
    20-F 那种股份类别长句不是性质，只留在 raw_shares_type。
    is_state/is_foreign/is_natural 按 holder_nature 查 HOLDER_NATURE_FLAGS，对照表里没有的性质三个标志都留空并记 data_anomaly。
    change 是数字才进 chg_shares，「不变」记 0，「新进」不算股数；change 是文字时原文另进 raw_change（页面按原文判「不变」）。"""
    year = _roster_year(end_date)
    rows = []
    for h in (holders or []) if year else []:
        name = _txt(h.get("name"))
        if not name:
            continue
        change, state, shares_type = _txt(h.get("change")), _txt(h.get("state")), _txt(h.get("shares_type"))
        status = state if state in CHANGE_STATUS else (change if change in CHANGE_STATUS else None)
        other = state if state and state not in CHANGE_STATUS else None
        share_class = _share_class(shares_type) or _share_class(other)
        nature = (None if _share_class(other) else other) or (None if _share_class(shares_type) else shares_type)
        if nature and (len(nature) > 32 or re.search(r"[AB] ?类", nature)):   # 20-F 的股份类别说明（「B 类 … + A 类 …」），不是股东性质
            nature = None
        flags = HOLDER_NATURE_FLAGS.get(nature, (None, None, None))
        if nature and nature not in HOLDER_NATURE_FLAGS and nature not in HOLDER_NATURE_UNKNOWN:
            L.add("data_anomaly", (code, source, "shareholder", "holder_nature", str(year), nature,
                                   "unmapped_value", LOADER))
        raw_change = h.get("change") if isinstance(h.get("change"), str) else None
        rows.append((code, year, _txt(end_date), h.get("rank"), name, None, None, *flags, nature,
                     _num(h.get("hold_num")), _num(h.get("ratio")), _num(h.get("total_shares")), share_class,
                     _raw_text(h.get("shares_type")), _num(h.get("pledged")), 0 if change == "不变" else _num(change),
                     raw_change, status, _raw_text(h.get("state")), source))
    return rows


def load_holders_manual(L):
    """holders_manual.json：年报原文手工件，名册/户数/分红按期盖过接口值；分组、集中度、年末股数、口径与缺口另各进一张表。
    faction_aliases（年报简称 → 接口名册全称）记进名册那一行的 holder_short；环形图的叫法、板块标签、股本断点说明进 data_note。"""
    file = "holders_manual.json"
    d = _load_json(file)
    roster_cols = COLUMNS["shareholder"]
    name_at, short_at = roster_cols.index("holder_name"), roster_cols.index("holder_short")
    for key, e in d.items():
        if ":" not in key or not isinstance(e, dict):
            continue
        industry, raw_code = key.split(":", 1)
        code = L.ensure_company(raw_code, industry, _txt(e.get("name")))
        L.set_shareholders(_shareholder_rows(L, code, e.get("holders_end_date"), e.get("holders"), file), override=True)
        L.set_holder_meta(code, [_txt(e.get(k)) for k in ("holders_caliber", "caliber_note", "source",
                                                          "factions_source", "history_source")])
        aliases = {str(full): str(alias) for alias, full in (e.get("faction_aliases") or {}).items()}
        if aliases:
            found = set()
            for k, rows in L.shareholders.items():
                if k[0] == code:
                    L.shareholders[k] = [r[:short_at] + (aliases.get(r[name_at], r[short_at]),) + r[short_at + 1:]
                                         for r in rows]
                    found |= {r[name_at] for r in rows}
            for full, alias in aliases.items():
                if full not in found:
                    L.add("data_anomaly", (code, file, "shareholder", "holder_short", None,
                                           "%s → %s（名册里没有这个全称）" % (alias, full), "unmapped_value", LOADER))
        for i, fac in enumerate(e.get("factions") or [], 1):
            for j, name in enumerate(fac.get("names") or [], 1):
                L.add("shareholder_faction", (code, _txt(fac.get("title")) or "", i, str(name), j,
                                              _txt(fac.get("color")), _txt(fac.get("basis")), file))
        _load_holder_count(L, code, e.get("holder_num"), file, override=True)
        for r in e.get("holder_concentration") or []:
            if isinstance(r, dict) and _txt(r.get("date")):
                L.add_concentration(code, r, file, override=True)
        brk = e.get("share_capital_break") or {}
        at, factor = _txt(brk.get("at")), _num(brk.get("factor"))
        for r in e.get("share_capital") or []:
            if isinstance(r, list) and r and YEAR.match(str(r[0])):
                split = factor if factor and at and YEAR.match(at) and int(r[0]) < int(at) else None
                L.add("share_capital_year_end", (code, int(r[0]), _num(r[1]) if len(r) > 1 else None,
                                                 _raw_text(r[2]) if len(r) > 2 else None, split, file))
        for g in e.get("history_gaps") or []:
            L.add("data_gap", (code, str(g), None, file))
        ring_alt = e.get("ring_alt_meta") or {}
        _add_notes(L, code, file, {
            "tag": e.get("tag"), "residual_label": e.get("residual_label"), "dividend_unit": e.get("dividend_unit"),
            "share_capital_break": brk.get("text"),
            **{"ring_alt_meta." + k: v for k, v in ring_alt.items() if not isinstance(v, dict)},
            **{"ring_alt_meta.%s.%s" % (k, kk): vv for k, v in ring_alt.items() if isinstance(v, dict)
               for kk, vv in v.items()}})
        unit = _txt(e.get("dividend_unit")) or "元"
        h_entity = "hk." + L.companies[code][5] if L.companies[code][5] else None
        dtot = e.get("dividend_total") or {}   # {年:亿元} 或 [[年,亿元]]，年报原文，禁反算
        if isinstance(dtot, list):
            dtot = {str(x[0]): x[1] for x in dtot if isinstance(x, list) and len(x) >= 2}
        for r in e.get("dividend_per10") or []:
            if isinstance(r, list) and len(r) >= 2 and YEAR.match(str(r[0])) and _num(r[1]) is not None:
                y, v = int(r[0]), _num(r[1])
                if unit != "元" and not code.startswith("hk."):
                    # A 股序列只收人民币口径：中国移动年报按港元宣派，港元值归港股序列 hk.00941（telecom_00941_annual.json），
                    # A 股这行保留接口的人民币值；港股序列已有的年份两边不等才记 data_anomaly
                    old = L.dividends.get((h_entity, y)) if h_entity in L.companies else None
                    if h_entity not in L.companies:
                        L.add("data_anomaly", (code, file, "financials", "dividend_per_10_shares", str(y),
                                               "%s %s（A 股序列保留人民币口径）" % (v, unit), "caliber_mismatch", LOADER))
                    elif old and old[0] is not None and not _same(old[0], v):
                        L.add("data_anomaly", (h_entity, file, "financials", "dividend_per_10_shares", str(y),
                                               "%s %s（原值 %s）" % (v, unit, old[0]), "conflicting_duplicate", LOADER))
                    else:
                        L.add_dividend(h_entity, y, v, unit, (old or (None, None, None))[2], file, override=True)
                    continue
                tv = _num(dtot.get(str(r[0]))) if isinstance(dtot, dict) else None
                L.add_dividend(code, y, v, unit, tv, file, override=True)


def load_hshare_holder_count(L):
    """holder_count_hshare_2010_2018.json：渝农商行 H 股（03618）逐年港股年报核过的 H 股登记股东户数，
    只补该期 H 股那一格（接口/手工件已有值的不覆盖）；未披露的年份把原文说明记进 data_gap。"""
    file = "holder_count_hshare_2010_2018.json"
    d = _load_json(file) or {}
    code = next((c[0] for c in L.companies.values() if c[5] == "03618"), None)
    for r in d.get("data") or []:
        date, n = _txt(r.get("year_end")), _num(r.get("h_shareholders"))
        if n is None:
            L.add("data_gap", (code, _txt(r.get("note")) or "%s H 股登记股东户数未披露" % date, None, file))
            continue
        L.add_holder_count(code, date, [None, None, n, None], file)


def load_telecom_segments(L):
    """telecom_segment_manual.json：companies[code].annual[year].canon = {规范键:亿元}。
    原文科目名按 extract_telecom_segments.py 的 CANON 反查 items；小计/合计也存，is_subtotal=1。"""
    from extract_telecom_segments import CANON   # 归一键只在抽取脚本里定义一处
    file = "telecom_segment_manual.json"
    d = _load_json(file)
    if d is None:
        return
    _add_notes(L, None, file, {k: d.get(k) for k in ("source", "unit_note", "caliber_note")})
    for raw_code, c in (d.get("companies") or {}).items():
        code = L.ensure_company(raw_code, "telecom", _txt(c.get("name")))
        for year, blk in (c.get("annual") or {}).items():
            if not (YEAR.match(str(year)) and isinstance((blk or {}).get("canon"), dict)):
                continue
            for order, (seg, v) in enumerate(blk["canon"].items(), 1):
                labels = [k for k in (blk.get("items") or {}) if CANON.get(raw_code, {}).get(k) == seg]
                if _num(v) is not None:
                    L.add("segment_revenue", (code, int(year), seg, "、".join(labels) or None,
                                              1 if seg in ("total", "service_total") else 0, _num(v), order, file))


def load_social_financing(L):
    """社融存量/增量两份月度表：[{month, <分项>:值}]，按列名映射成宽表一月一行。"""
    stock_file, flow_file = "social_financing_pboc_stock.json", "social_financing_pboc_flow.json"
    stock = _load_json(stock_file) or {}
    for r in stock.get("data") or []:
        if _txt(r.get("month")):
            L.add("social_financing_stock", (r["month"][:7], _num(r.get("stock_tnyuan")), _num(r.get("yoy_pct")),
                                             _txt(stock.get("source"))))
    flow = _load_json(flow_file) or {}
    for r in flow.get("data") or []:
        if _txt(r.get("month")):
            L.add("social_financing_flow", (r["month"][:7], *[_num(r.get(j)) for _, j in SOCIAL_FINANCING_FLOW_COLS],
                                            _txt(flow.get("source"))))


# ── 银行年报正文明细：bank_<code>_detail_manual.json → bank_report_detail / bank_bond_issue / data_note ──
# 渝农商行没有 detail_manual，同一批键手工精编在 company_charts_601077.json（gen_company_charts.py 不生成它）。
HAND_CHART_FILES = {"601077": "company_charts_601077.json"}
AMOUNT_UNITS = (("亿元", 1e8), ("百万元", 1e6), ("千元", 1e3), ("元", 1))   # 相邻两档差 100 倍以上
FIXED_UNITS = {"%": ("%", 1), "人": ("人", 1), "笔": ("笔", 1), "万元": ("元", 1e4)}   # 原值单位 → (统一单位, 倍数)
# 分项 × 两期：(topic, 分项键, {值键: (年, measure)}, 单位类)；年为 None 的取年报当年
DETAIL_PAIR = {
    "nim": ("net_interest_rate_item", "items", {"rate25": (2025, "average_rate"), "rate24": (2024, "average_rate")}, "%"),
    "loan-industry": ("corporate_loan_by_industry", "inds",
                      {"bal25": (2025, "balance"), "bal24": (2024, "balance")}, "amount"),
    "seg-rev": ("segment_revenue", "segs", {"rev25": (2025, "revenue"), "rev24": (2024, "revenue")}, "amount"),
    "fvtpl-mix": ("fvtpl_investment_by_type", "cats", {"y2025": (2025, "balance"), "y2024": (2024, "balance")}, "amount"),
    "repricing": ("repricing_gap", "buckets", {"g2025": (2025, "gap"), "g2024": (2024, "gap")}, "amount"),
    "maturity": ("maturity_gap", "buckets", {"asset2025": (2025, "assets"), "debt2025": (2025, "liabilities")}, "amount"),
    "geo": ("county_urban_share", "cats", {"county": (None, "county_share"), "urban": (None, "urban_share")}, "%"),
}
# 只给年报当年一期、分项固定（顺序与页面图例一致）：(topic, 分项名, measure, 单位类)
DETAIL_SINGLE = {
    "depterm": ("deposit_structure", ["定期存款", "活期存款", "保证金及其他"], "balance", "amount"),
    "5tier": ("loan_five_category", ["正常", "关注", "次级", "可疑", "损失"], "balance", "amount_or_share"),
    "cf": ("quarterly_operating_cash_flow", ["Q1", "Q2", "Q3", "Q4"], "net_cash_operating", "amount"),
    "staff-role": ("staff_by_role", "roles", "headcount", "people_or_share"),
    "staff-edu": ("staff_by_education", "edu", "headcount", "people_or_share"),
    "staff-age": ("staff_by_age", "buckets", "headcount", "people_or_share"),
}
# 逐年序列：(topic, {序列键: (分项名, measure, 单位类[, 年份键])})，年份键缺省 years
DETAIL_SERIES = {
    "migrate": ("loan_migration_rate", {"ynshbNormal": ("", "normal_migration_rate", "%", "normalYears"),
                                        "guanzhu": ("", "special_mention_migration_rate", "%"),
                                        "ciji": ("", "substandard_migration_rate", "%"),
                                        "keyi": ("", "doubtful_migration_rate", "%")}),
    "loantrend": ("loan_trend", {"nplCorp": ("", "corporate_npl_ratio", "%"), "nplRetail": ("", "retail_npl_ratio", "%")}),
    "perloan-bal": ("retail_loan_by_product", {
        "balMortgage": ("个人住房贷款", "balance", "amount"), "balBusiness": ("个人经营贷款", "balance", "amount"),
        "balCard": ("信用卡", "balance", "amount"), "balConsume": ("个人消费贷款", "balance", "amount"),
        "balOthers": ("其他", "balance", "amount"), "nplMortgage": ("个人住房贷款", "npl_ratio", "%"),
        "nplBusiness": ("个人经营贷款", "npl_ratio", "%"), "nplOthers": ("其他(含消费/信用卡)", "npl_ratio", "%")}),
    "depcost": ("deposit_cost", {"cost": ("", "customer_deposit_cost_rate", "%"),
                                 "demand": ("", "demand_deposit_share", "%")}),
    "bondpay": ("bonds_payable", {
        "balNcd": ("同业存单", "balance", "amount"), "balBond": ("债券", "balance", "amount"),
        "balTotal": ("合计", "balance", "amount"), "avgNcd": ("同业存单", "average_balance", "amount"),
        "avgBond": ("债券", "average_balance", "amount"), "avgTotal": ("合计", "average_balance", "amount"),
        "rateNcd": ("同业存单", "cost_rate", "%"), "rateBond": ("债券", "cost_rate", "%"),
        "rateTotal": ("合计", "cost_rate", "%")}),
    "loanmix-bal": ("loan_average_yield", {
        "balCorp": ("公司贷款", "average_balance", "amount"), "balRetail": ("零售贷款", "average_balance", "amount"),
        "balBill": ("票据贴现", "average_balance", "amount"), "balTotal": ("合计", "average_balance", "amount"),
        "yldCorp": ("公司贷款", "average_yield", "%"), "yldRetail": ("零售贷款", "average_yield", "%"),
        "yldBill": ("票据贴现", "average_yield", "%"), "yldTotal": ("合计", "average_yield", "%")}),
    "writeoff": ("loan_write_off", {"writeOff": ("", "write_offs", "amount"), "recovery": ("", "recoveries", "amount"),
                                    "netWO": ("", "net_write_offs", "amount")}),
    "complaint": ("consumer_complaint", {"complaints": ("", "complaints", "笔"),
                                         "satisfaction": ("", "satisfaction_rate", "%")}),
    "invest": ("financial_investment_by_measurement", {
        "ac": ("以摊余成本计量", "balance", "amount"),
        "fvociDebt": ("以公允价值计量且其变动计入其他综合收益(债务工具)", "balance", "amount"),
        "fvociEq": ("以公允价值计量且其变动计入其他综合收益(权益工具)", "balance", "amount"),
        "fvtpl": ("以公允价值计量且其变动计入当期损益", "balance", "amount")}),
    "overdue-band": ("overdue_loan_by_band", {
        "b90": ("逾期1至90天", "balance", "amount"), "b91y": ("逾期91天至1年", "balance", "amount"),
        "b1_5": ("逾期1至5年", "balance", "amount"), "b5up": ("逾期5年以上", "balance", "amount"),
        "b1up": ("逾期1年及以上(未细分)", "balance", "amount")}),
    "fvlevel": ("fair_value_hierarchy", {"l1": ("第一层次", "balance", "amount"), "l2": ("第二层次", "balance", "amount"),
                                         "l3": ("第三层次", "balance", "amount"), "tot": ("合计", "balance", "amount")}),
}
# 各键里不进 bank_report_detail 的子键：年份/分项轴、页面标注（marks 进 data_note）、
# loantrend 的四项余额（已在 bank_financials）、seg-rev.std（gen 按四桶归并的派生值）、
# migrate.abcNormal（农业银行的对标序列，不是本行数据）、bondpay.bonds（进 bank_bond_issue）、
# overdue-band.names（本行档名，替换缺省分项名）
DETAIL_SKIP_KEYS = {"years", "normalYears", "items", "inds", "segs", "cats", "buckets", "roles", "edu", "vals",
                    "marks", "names", "std", "abcNormal", "bonds", "corp", "retail", "nplBalanceCorp",
                    "nplBalanceRetail", "chairmanNames", "presidentNames", "chairmanPay", "presidentPay"}
# 金额量级对账：(参照列, 下限, 上限)，依次试，参照有值就用；合计 × 倍数 ÷ 参照落进区间的那一档即原值单位。
# 区间都不足 100 倍宽，至多命中一档。取 topic 里哪些行求和见 _unit_probe。
DETAIL_UNIT_CHECKS = {
    "deposit_structure": [("customer_deposits_balance_sheet", 0.5, 2), ("customer_deposits", 0.5, 2)],
    "loan_five_category": [("gross_loans", 0.5, 2)],
    "corporate_loan_by_industry": [("gross_loans", 0.05, 2)],
    "segment_revenue": [("operating_revenue", 0.5, 2)],
    "quarterly_operating_cash_flow": [("net_cash_operating", 0.5, 2)],
    "fvtpl_investment_by_type": [("trading_financial_assets", 0.3, 3), ("fvtpl_financial_assets", 0.3, 3),
                                 ("total_assets", 0.005, 0.3)],
    "fair_value_hierarchy": [("total_assets", 0.01, 0.8)],
    "repricing_gap": [("total_assets", 0.05, 3)],
    "maturity_gap": [("total_assets", 0.5, 2)],
    "retail_loan_by_product": [("gross_loans", 0.05, 1.5)],
    "bonds_payable": [("bonds_payable", 0.5, 2), ("total_assets", 0.003, 0.25)],
    "loan_average_yield": [("gross_loans", 0.6, 1.5)],
    "loan_write_off": [("loan_write_offs", 0.5, 2), ("gross_loans", 0.0005, 0.04)],
    "financial_investment_by_measurement": [("total_assets", 0.05, 0.8)],
    "overdue_loan_by_band": [("overdue_loans", 0.5, 2), ("gross_loans", 0.002, 0.15)],
}


def _note_text(v):
    """说明原文：字符串照存；对象逐项写成「键：值」；列表逐条换行。"""
    if isinstance(v, dict):
        return "\n".join("%s：%s" % (k, t) for k, t in ((k, _note_text(x)) for k, x in v.items()) if t) or None
    if isinstance(v, list):
        return "\n".join(t for t in (_note_text(x) for x in v) if t) or None
    return _txt(v)


def _add_notes(L, code, file, notes):
    """{键: 说明} 逐键写进 data_note，空的不写。"""
    for k, v in (notes or {}).items():
        text = _note_text(v)
        if text:
            L.add("data_note", (code, file, str(k), text))


def _bank_refs(L):
    """(实体键, 年) → financials / bank_financials 已载入的同口径总量（元），给 detail_manual 的金额对账定量级。"""
    refs = collections.defaultdict(dict)
    for t in ("financials", "bank_financials"):
        cols = COLUMNS[t]
        for r in L.rows[t]:
            refs[(r[0], r[1])].update({c: v for c, v in zip(cols[2:], r[2:]) if isinstance(v, (int, float))})
    return refs


def _detail_doc(code):
    """银行年报正文手工层 (文档, 文件名)：bank_<code>_detail_manual.json；渝农商行取手工精编的 company_charts_601077.json。"""
    name = "bank_%s_detail_manual.json" % code
    d = _load_json(name)
    if d is None and code in HAND_CHART_FILES:
        name = HAND_CHART_FILES[code]
        d = _load_json(name)
    return d, name


# 对账取哪些行求和（依次试，前一种取不到行再用后一种）；没列的主题取全部金额行
UNIT_PROBE_ROWS = {
    "fair_value_hierarchy": [lambda i, m: i == "合计", lambda i, m: True],            # 没有合计行就三个层次相加
    "bonds_payable": [lambda i, m: i == "合计" and m == "balance", lambda i, m: m == "balance"],
    "loan_average_yield": [lambda i, m: i == "合计"],
    "maturity_gap": [lambda i, m: m == "assets"],
    "loan_write_off": [lambda i, m: m == "write_offs"],
    "retail_loan_by_product": [lambda i, m: m == "balance"],
}


def _unit_probe(topic, rows, year):
    """对账用的合计：该年金额类的行按 UNIT_PROBE_ROWS 求和，缺口取绝对值之和。"""
    amt = [(i, m, v) for t, y, i, m, v, k, *_ in rows if t == topic and y == year and k == "amount" and v is not None]
    for only in UNIT_PROBE_ROWS.get(topic, [lambda i, m: True]):     # 依次试，取到行就用
        vals = [v for i, m, v in amt if only(i, m)]
        if vals:
            return sum(abs(v) for v in vals) if topic == "repricing_gap" else sum(vals)
    return None


def _detail_unit(topic, rows, refs, code):
    """金额原值单位：从最近一年往前找有参照的年份，按 DETAIL_UNIT_CHECKS 对账；对不上返回 (None, 对账记录)。"""
    tried = []
    for year in sorted({r[1] for r in rows if r[0] == topic and r[5] == "amount"}, reverse=True):
        probe = _unit_probe(topic, rows, year)
        if not probe:
            continue
        for col, lo, hi in DETAIL_UNIT_CHECKS.get(topic, []):
            ref = refs.get((code, year), {}).get(col)
            if not ref:
                continue
            hits = [u for u, f in AMOUNT_UNITS if lo <= abs(probe) * f / abs(ref) <= hi]
            if len(hits) == 1:
                return hits[0], None
            tried.append("%d 年合计 %s，%s %s" % (year, probe, col, ref))
    return None, "；".join(tried[:3]) or "没有可对账的参照值"


def _cash_flow_caliber(rows, refs, code, year):
    """分季度经营现金流的首项若就等于全年经营活动现金流量净额（四项之和却不等），返回该首项的单位，否则 None。"""
    q = [v for t, y, i, m, v, k, *_ in rows if t == "quarterly_operating_cash_flow" and y == year and v is not None]
    ref = refs.get((code, year), {}).get("net_cash_operating")
    if len(q) != 4 or not ref:
        return None
    for u, f in AMOUNT_UNITS:
        if abs(q[0] * f / ref - 1) <= 0.01 < abs(sum(q) * f / ref - 1):
            return u
    return None


def _bank_detail_codes():
    names = (re.fullmatch(r"bank_(\w+)_detail_manual\.json", n) for n in jsonstore.listdir(TABLES))
    return sorted({m.group(1) for m in names if m} | set(HAND_CHART_FILES))


def _detail_rows(d, report_year):
    """detail_manual 各键摊成 (topic, 年, 分项, measure, 原值, 单位类, 分项顺序, 期次写法)；另返回 bonds、页面标注与没登记的子键。
    数组里的空格子也出一行（原值为空），年份轴与分项顺序靠这些行还原；整列为 null 的不出行。
    年份写成「2024 年末」这类的取前四位作年份，原写法记进期次写法。"""
    rows, bonds, marks, unknown = [], [], {}, []

    def put(topic, year, item, measure, value, kind, order=None):
        m = re.fullmatch(r"((?:19|20)\d{2})(.*)", str(year).strip()) if year is not None else None
        if m:
            rows.append((topic, int(m.group(1)), (_txt(item) or "")[:128], measure, _num(value), kind, order,
                         str(year) if m.group(2).strip() else None))

    for key, sec in d.items():
        if not isinstance(sec, dict) or key.startswith("_"):
            continue
        consumed = set(DETAIL_SKIP_KEYS)
        if key in DETAIL_PAIR:
            topic, items_key, value_keys, kind = DETAIL_PAIR[key]
            for vk, (year, measure) in value_keys.items():
                consumed.add(vk)
                for i, (item, v) in enumerate(zip(sec.get(items_key) or [], sec.get(vk) or []), 1):
                    put(topic, year or report_year, item, measure, v, kind, i)
        elif key in DETAIL_SINGLE:
            topic, items, measure, kind = DETAIL_SINGLE[key]
            if isinstance(items, list):                        # 固定分项，值在 vals
                pairs = zip(items, sec.get("vals") or [])
            elif items == "buckets":                           # staff-age：buckets + vals
                pairs = zip(sec.get("buckets") or [], sec.get("vals") or [])
            else:                                              # staff-role / staff-edu：[{name, value}]
                pairs = [(x.get("name"), x.get("value")) for x in sec.get(items) or [] if isinstance(x, dict)]
            for i, (item, v) in enumerate(pairs, 1):
                put(topic, report_year, item, measure, v, kind, i)
        elif key in DETAIL_SERIES:
            topic, series = DETAIL_SERIES[key]
            names = sec.get("names") or {}
            for i, (sk, spec) in enumerate(series.items(), 1):   # 序列在键里的位置即图例顺序，记进分项顺序
                consumed.add(sk)
                for y, v in zip(sec.get(spec[3] if len(spec) > 3 else "years") or [], sec.get(sk) or []):
                    put(topic, y, names.get(sk) or spec[0], spec[1], v, spec[2], i)
        elif key == "chairman-pay":                            # 在任者姓名作分项，空缺（—）与没披露薪酬的照写（value 为空）
            for y, cn, cp, pn, pp in zip(*(sec.get(k) or [] for k in (
                    "years", "chairmanNames", "chairmanPay", "presidentNames", "presidentPay"))):
                for name, pay, measure in ((cn, cp, "chairman_pay"), (pn, pp, "president_pay")):
                    put("executive_pay", y, name, measure, pay, "万元")
        else:
            unknown.append(key)
            continue
        bonds += [b for b in sec.get("bonds") or [] if isinstance(b, dict)]
        for i, m in enumerate(sec.get("marks") or [], 1):      # 图上标注逐条逐字段进 data_note：<键>.marks.<序号>.<字段>
            if isinstance(m, dict):
                marks.update({"%s.marks.%d.%s" % (key, i, k): v for k, v in m.items()})
        unknown += ["%s.%s" % (key, k) for k in sec if k not in consumed]
    return rows, bonds, marks, unknown


def load_bank_detail(L):
    """银行年报正文手工层 → bank_report_detail（一个数一行）、bondpay.bonds → bank_bond_issue、_notes → data_note。
    金额原值单位按主题与 annual 同口径总量对账定量级（DETAIL_UNIT_CHECKS），统一成元；对不上只留原值并记 data_anomaly。
    数组里的空格子也写行、分项记顺序，后端据此原样拼回（backend/bank_charts_db.detail）。
    渝农商行的 company_charts_601077.json 只取与 detail_manual 同名的键，其余键是手工精编的图表值，尚未拆表。"""
    refs = _bank_refs(L)
    for raw_code in _bank_detail_codes():
        d, file = _detail_doc(raw_code)
        if not d:
            continue
        code = _entity_code(raw_code)
        years = [y for c, y in refs if c == code]
        report_year = max(years) if years else None      # 只给一期的键记年报当年
        rows, bonds, marks, unknown = _detail_rows(d, report_year)
        if file != HAND_CHART_FILES.get(raw_code):
            for k in unknown:
                L.add("data_anomaly", (code, file, "bank_report_detail", k, None, None, "unmapped_field", LOADER))
        resolved = []                                    # 五级分类、员工构成：合计约 100 的是占比
        for topic, year, item, measure, v, kind, order, label in rows:
            if kind in ("amount_or_share", "people_or_share"):
                total = sum(r[4] for r in rows if r[0] == topic and r[1] == year and r[4] is not None)
                staff = refs.get((code, year), {}).get("employee_count")
                if 95 <= total <= 105 and (kind == "amount_or_share" or not staff or staff > 1000):
                    measure, kind = "share", "%"
                else:
                    kind = "amount" if kind == "amount_or_share" else "人"
            resolved.append((topic, year, item, measure, v, kind, order, label))
        units = {}
        for topic in sorted({r[0] for r in resolved if r[5] == "amount"}):
            unit, why = _detail_unit(topic, resolved, refs, code)
            if topic == "quarterly_operating_cash_flow":
                alt = _cash_flow_caliber(resolved, refs, code, report_year)
                if alt:
                    unit = alt
                    L.add("data_anomaly", (code, file, "bank_report_detail", "cf", str(report_year),
                                           "首项等于全年经营活动现金流量净额，四项之和与全年对不上，不像单季口径",
                                           "caliber_mismatch", LOADER))
            if unit is None:
                L.add("data_anomaly", (code, file, "bank_report_detail", topic, None, why[:255], "unknown_unit", LOADER))
            units[topic] = unit
        for topic, year, item, measure, v, kind, order, label in resolved:
            if kind == "amount":
                raw_unit = units.get(topic)
                unit, factor = ("元", dict(AMOUNT_UNITS)[raw_unit]) if raw_unit else (None, None)
            else:
                raw_unit = kind
                unit, factor = FIXED_UNITS[kind]
            value = None if v is None or factor is None else round(v * factor, 4)
            L.add("bank_report_detail", (code, year, label, topic, item, order, measure, value, unit, v, raw_unit, file))
        for i, b in enumerate(bonds, 1):
            if _txt(b.get("name")):
                L.add("bank_bond_issue", (code, i, _txt(b["name"]), _txt(b.get("issueDate")), _txt(b.get("tenor")),
                                          _num(b.get("coupon")), _num(b.get("amount")), _txt(b.get("maturity")),
                                          _txt(b.get("status")), file))
        _add_notes(L, code, file, {**(d.get("_notes") or {}), "_source": d.get("_source"), **marks})


def load_bank_hand_layers(L):
    """银行年报原文手工件里的股东户数、集中度、年末股数、分红：bank_<code>_shareholder_manual.json、
    纯 H 股行 bank_<code>_ar_manual.json 里 annual 没并进去的逐年户数与集中度重构序列、渝农商行手工精编的 company_charts_601077.json。
    户数与分红是非空格子盖过接口值，两边不一致记 data_anomaly；集中度与股数只补接口没有的期。
    shareholder_manual 的前十名（与 annual 同一份名册）只把简称与类别记到名册那一行，页面文案进 data_note。"""
    for name in jsonstore.listdir(TABLES):
        m = re.fullmatch(r"bank_(\w+)_ar_manual\.json", name)
        if not m:
            continue
        code, d = _entity_code(m.group(1)), _load_json(name) or {}
        note = _txt(d.get("holder_count_note")) or ""
        domestic = "内资股" in note or "內資股" in note        # 哈尔滨银行只披露过内资股股东数
        for y, n in (d.get("holder_count_by_year") or {}).items():
            if YEAR.match(str(y)) and _num(n) is not None:
                L.merge_holder_count(code, "%s-12-31" % y,
                                     [None, None, None, _num(n)] if domestic else [_num(n), None, None, None], name)
        for r in d.get("concentrationHist") or []:     # [截止日, 第一大, 前三大, 前十大, recon/disc]
            if isinstance(r, list) and len(r) >= 4 and _txt(r[0]):
                L.add_concentration(code, {"date": r[0], "top1": r[1], "top3": r[2], "top10": r[3],
                                           "recon": r[4] if len(r) > 4 else None}, name)
        _add_notes(L, code, name, {**(d.get("notes") or {}), **{k: d.get(k) for k in (
            "reports", "concentrationHistNote", "holder_count_note")}})
    for name in jsonstore.listdir(TABLES):
        m = re.fullmatch(r"bank_(\w+)_shareholder_manual\.json", name)
        if not m:
            continue
        code, d = _entity_code(m.group(1)), _load_json(name) or {}
        for r in d.get("holderCount") or []:            # [年, A股户数, H股户数]
            if not (isinstance(r, list) and r and YEAR.match(str(r[0]))):
                continue
            date, a, h = "%s-12-31" % r[0], *[_num(r[i]) if len(r) > i else None for i in (1, 2)]
            cell = L.holder_counts.get((code, date)) or [None] * 4
            if a is None and h is not None and cell[2] is None and cell[0] is not None and _same(cell[0], h):
                # 纯 H 股行：这里记成 H 股户数的数，ar_manual / annual 记为未拆分的股东总数，不再填进 H 股一格
                L.add("data_anomaly", (code, name, "shareholder_count", "h_share_holders", date,
                                       "%s（ar_manual/annual 记为股东总数 %s）" % (h, cell[0]), "caliber_mismatch", LOADER))
                continue
            L.merge_holder_count(code, date, [None, a, h, None], name)
        _merge_dividends(L, code, d.get("dividend"), name)
        _add_notes(L, code, name, {k: d.get(k) for k in ("holderNote", "holdersNote", "dividendNote", "meta",
                                                          "holdersSub", "dividendSub", "holderUnit", "top10Sum")})
        _label_roster(L, code, d.get("top10"), name)
    for raw_code, name in HAND_CHART_FILES.items():
        code, d = _entity_code(raw_code), _load_json(name) or {}
        for r in (d.get("holder-count") or {}).get("raw") or []:     # [截止日, 合计, A股, H股]
            if isinstance(r, list) and r and _txt(r[0]):
                L.merge_holder_count(code, _txt(r[0]), [_num(r[i]) if len(r) > i else None for i in (1, 2, 3)] + [None],
                                     name)
        for r in (d.get("holder-concentration-hist") or {}).get("raw") or []:   # 同 ar_manual 的 concentrationHist
            if isinstance(r, list) and len(r) >= 4 and _txt(r[0]):
                L.add_concentration(code, {"date": r[0], "top1": r[1], "top3": r[2], "top10": r[3],
                                           "recon": r[4] if len(r) > 4 else None}, name)
        _add_notes(L, code, name, {"holder-concentration-hist": (d.get("holder-concentration-hist") or {}).get("note")})
        hc = d.get("holder-concentration") or {}
        tops = hc.get("top1Names") or []
        for i, r in enumerate(hc.get("raw") or []):    # [报告期, 第一大, 前三大, 前十大, 其他流通股东]
            if isinstance(r, list) and len(r) >= 4 and _txt(r[0]):
                L.add_concentration(code, {"date": r[0], "top1": r[1], "top3": r[2], "top10": r[3],
                                           "top1_name": tops[i] if i < len(tops) else None}, name)
        _merge_dividends(L, code, d.get("dividend-per10"), name)
        sc = d.get("share-capital") or {}
        for y, s in zip(sc.get("years") or [], sc.get("shares") or []):   # 亿股
            if YEAR.match(str(y)) and _num(s) is not None:
                ev = (sc.get("events") or {}).get(str(y)) or {}
                L.add("share_capital_year_end", (code, int(y), round(_num(s) * 1e8),
                                                 _txt("；".join(map(str, ev.get("items") or []))), None, name))


TOP10_CATEGORIES = ("soe", "hk", "ssf", "ins", "corp", "other")   # 银行股东手工件 top10 的类别键（见 shareholder.holder_category）


def _label_roster(L, code, top10, source):
    """银行股东手工件的 top10（[简称, 占比, 增减, 类别文字, 类别键]）与 annual 那份名册是同一批股东、同一顺序：
    按名次对上后把简称记进 holder_short、类别键记进 holder_category；占比对不上或类别认不出的记 data_anomaly，不硬配。"""
    keys = sorted(k for k in L.shareholders if k[0] == code)
    if not top10 or not keys:
        return
    cols = COLUMNS["shareholder"]
    rank, name, short, ratio = (cols.index(c) for c in ("holder_rank", "holder_name", "holder_short", "ratio"))
    rows = sorted(L.shareholders[keys[-1]], key=lambda r: r[rank] or 99)
    labels = {}
    for i, t in enumerate(top10):
        r = rows[i] if i < len(rows) else None
        ok = (r is not None and isinstance(t, list) and len(t) >= 5 and t[4] in TOP10_CATEGORIES
              and r[ratio] is not None and _num(t[1]) is not None and abs(r[ratio] - _num(t[1])) <= 0.011)
        if not ok:
            L.add("data_anomaly", (code, source, "shareholder", "holder_short", str(keys[-1][1]),
                                   "top10 第 %d 行 %s 对不上名册（%s）" % (i + 1, t, r and (r[name], r[ratio])),
                                   "unmapped_value", LOADER))
            continue
        if r[short] and r[short] != t[0]:
            L.add("data_anomaly", (code, source, "shareholder", "holder_short", str(keys[-1][1]),
                                   "%s（已有简称 %s）" % (t[0], r[short]), "conflicting_duplicate", LOADER))
        labels[r[name]] = (str(t[0]), t[4])
    L.shareholders[keys[-1]] = [r[:short] + labels[r[name]] + r[short + 2:] if r[name] in labels else r
                                for r in L.shareholders[keys[-1]]]


def _merge_dividends(L, code, block, source):
    """{years, per10}：每 10 股派息（元）按年并进分红。"""
    block = block or {}
    for y, v in zip(block.get("years") or [], block.get("per10") or []):
        if YEAR.match(str(y)) and _num(v) is not None:
            L.merge_dividend(code, int(y), _num(v), source)


def _add_operating(L, table, code, year, row, file, defaults=None):
    """经营口径表一行：数值列按映射缩放（一列多个源字段取非空的那个）、文本照存、标记存 1/0，没登记映射的字段记 data_anomaly。"""
    num, text, flag = OPERATING_TABLES[table]
    vals = _industry_values(L, num, row, code, year, file, table)
    vals.update({c: _txt(row.get(j)) for c, j in text if _txt(row.get(j)) is not None})
    vals.update({c: 1 if row[j] else 0 for c, j in flag if isinstance(row.get(j), bool)})
    for k, v in row.items():
        if k not in {t[1] for t in (*num, *text, *flag)} and _txt(v) is not None:
            L.add("data_anomaly", (code, file, table, k, str(year), _txt(v)[:255], "unmapped_field", LOADER))
    if not any(v is not None for v in vals.values()):
        return
    vals = {**(defaults or {}), **{c: round(v, 6) if isinstance(v, float) else v
                                   for c, v in vals.items() if v is not None}}
    if "source" not in {c for c, _ in text}:          # telecom 的 source 是年报出处原文，其余表记来源文件
        vals["source"] = file
    L.add(table, (code, year, *[vals.get(c) for c in COLUMNS[table][2:]]))


def load_operating(L):
    """经营口径手工层（年报正文人工摘录）→ <行业>_operating；各文件的口径、单位、出处说明进 data_note。"""
    for file, table, industry, company_notes in (
            ("cement_ops_manual.json", "cement_operating", "cement",
             ("currency", "years", "sales_key", "rev_caliber", "unit_rule", "breaks")),
            ("telecom_ops_manual.json", "telecom_operating", "telecom", ("years", "report_source", "breaks"))):
        d = _load_json(file) or {}
        _add_notes(L, None, file, {k: d.get(k) for k in ("source", "unit_note", "caliber_note")})
        for raw_code, c in (d.get("companies") or {}).items():
            code = L.ensure_company(raw_code, industry, _txt(c.get("name")))
            _add_notes(L, code, file, {k: c.get(k) for k in company_notes})
            for year, row in (c.get("annual") or {}).items():
                if YEAR.match(str(year)) and isinstance(row, dict):
                    _add_operating(L, table, code, int(year), row, file)
    for file, table, industry in (("telecom_00941_operating.json", "telecom_operating", "telecom"),
                                  ("tech_09888_segments_manual.json", "tech_operating", "tech")):
        d = _load_json(file) or {}
        code = L.ensure_company(re.search(r"_(\d{5,6})_", file).group(1), industry)
        _add_notes(L, code, file, d.get("_meta"))
        for year, row in (d.get("annual") or {}).items():
            if YEAR.match(str(year)) and isinstance(row, dict):
                _add_operating(L, table, code, int(year), row, file)



# 有自然主键/唯一键的表，入库前按键去重（多来源可能给出同一行），保留首次出现。
KEY_COLS = {
    "financials_meta": ("company_code",),
    "financials": ("company_code", "fiscal_year"),
    "bank_financials": ("company_code", "fiscal_year"),
    **{"%s_financials" % i: ("company_code", "fiscal_year") for i in INDUSTRY_COLS},
    "bank_balance_sheet_item": ("company_code", "fiscal_year", "statement_type", "item_code"),
    "segment_revenue": ("company_code", "fiscal_year", "segment_code"),
    "bank_report_detail": ("company_code", "fiscal_year", "topic", "item_name", "measure"),
    "bank_bond_issue": ("company_code", "bond_order"),
    **{t: ("company_code", "fiscal_year") for t in OPERATING_TABLES},
    "shareholder": ("company_code", "fiscal_year", "holder_name"),
    "shareholder_meta": ("company_code",),
    "shareholder_count": ("company_code", "as_of_date"),
    "shareholder_concentration": ("company_code", "as_of_date"),
    "shareholder_faction": ("company_code", "faction_title", "holder_name"),
    "share_capital_year_end": ("company_code", "fiscal_year"),
    "social_financing_stock": ("period_month",),
    "social_financing_flow": ("period_month",),
}


def dedupe(L):
    for t, keys in KEY_COLS.items():
        idx = [COLUMNS[t].index(k) for k in keys]
        seen, out = set(), []
        for row in L.rows[t]:
            kk = tuple(row[i] for i in idx)
            if kk not in seen:
                seen.add(kk)
                out.append(row)
        L.rows[t] = out


def _schema_tables():
    """data/sql/tables/*.sql 里建了的表名；只往这些表写。"""
    names = set()
    for path in glob.glob(os.path.join(SCHEMA_DIR, "*.sql")):
        with open(path, encoding="utf-8") as f:
            names.update(re.findall(r"CREATE TABLE(?: IF NOT EXISTS)?\s+`?(\w+)", f.read(), re.I))
    return names


def _run_schema(cur):
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for path in sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.sql"))):   # 建表时 FK 检查已关，文件名序即可
        with open(path, encoding="utf-8") as f:
            # 只按行尾的 ';' 切语句：COMMENT '…;…' 里的半角分号在行中间，不能当语句结束
            for stmt in re.split(r";[ \t]*$", f.read(), flags=re.M):
                code_lines = [ln for ln in stmt.splitlines()
                              if ln.strip() and not ln.strip().startswith("--")]
                if code_lines:
                    cur.execute(stmt)
    cur.execute("SET FOREIGN_KEY_CHECKS=1")


def main():
    cfg = db.config()
    ap = argparse.ArgumentParser(description="载入 data/tables JSON → MySQL 结构化表（见文件头用法）")
    ap.add_argument("--dry-run", action="store_true", help="只解析并打印各表行数，不连库")
    ap.add_argument("--host", default=cfg["host"])
    ap.add_argument("--port", type=int, default=cfg["port"])
    ap.add_argument("--user", default=cfg["user"])
    ap.add_argument("--password", default=cfg["password"])
    ap.add_argument("--db", default=cfg["database"])
    ap.add_argument("--init", action="store_true", help="入库前先按序执行 data/sql/tables/*.sql 建表")
    ap.add_argument("--reload", action="store_true",
                    help="同一事务里先清空本脚本要写的表再插入（全量重灌）")
    a = ap.parse_args()

    L = Loader()
    load_company(L)
    load_annual(L)
    load_holders_manual(L)
    load_hshare_holder_count(L)
    load_social_financing(L)
    load_telecom_segments(L)
    load_bank_detail(L)             # 要用 annual 已载入的总量对账，放在 annual 之后
    load_bank_hand_layers(L)        # 户数与分红要在 finish() 并进 financials 之前
    load_operating(L)
    L.finish()
    dedupe(L)

    schema = _schema_tables()
    tables = [t for t in INSERT_ORDER if t in schema]
    counts = L.counts()
    for t in INSERT_ORDER:
        print("  %-26s %8d%s" % (t, counts.get(t, 0), "" if t in tables else "  跳过（data/sql/tables 无建表文件）"))
    print("  %-26s %8d" % ("(合计)", sum(counts[t] for t in INSERT_ORDER)))
    unmapped = sorted({(r[2], r[3]) for r in L.rows["data_anomaly"] if r[6] == "unmapped_field"})
    if unmapped:
        print("  未登记映射的字段（已写进 data_anomaly）:", ", ".join("%s.%s" % t for t in unmapped))

    if a.dry_run:
        print("dry-run：未连接数据库、未写入。")
        return

    import pymysql
    conn = pymysql.connect(host=a.host, port=a.port, user=a.user,
                           password=a.password, database=a.db, charset="utf8mb4")
    try:
        cur = conn.cursor()
        if a.init:
            _run_schema(cur)
        if a.reload:                         # 子表先删，company 最后；data_anomaly 只清本脚本写的行
            for t in tables[::-1]:
                cur.execute("DELETE FROM `%s`" % t + (" WHERE source = %s" if t == "data_anomaly" else ""),
                            (LOADER,) if t == "data_anomaly" else None)
        for t in tables:
            rows = L.rows[t]
            if not rows:
                continue
            cols = ",".join("`%s`" % c for c in COLUMNS[t])
            ph = ",".join(["%s"] * len(COLUMNS[t]))
            cur.executemany("INSERT INTO `%s` (%s) VALUES (%s)" % (t, cols, ph), rows)
        conn.commit()
        print("入库完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
