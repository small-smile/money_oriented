#!/usr/bin/env python
"""把 data/tables 下的 JSON 成品表（原文存 MySQL json_file 表，经 backend/jsonstore.py 读）载入
data/sql/tables/*.sql 定义的 MySQL 表。

用法：
  # 只解析并打印各表将写入的行数，不写库（源 JSON 仍要从 json_file 表读，需 pymysql）：
  ./venv/bin/python data/extract/load_to_mysql.py --dry-run

  # 真实入库（需先 pip install pymysql；连接参数缺省同 jsonstore，读 .env 的 MYSQL_*；
  # --init 先按序执行 data/sql/tables/*.sql 建表；--reload 先清空本脚本写的表再全量重灌，可反复跑）：
  ./venv/bin/python data/extract/load_to_mysql.py --init --reload

财务表以 data/sql/tables 里现有的表为主：跨行业公共列（损益/资产负债/现金流/现金分红/审计意见/年末股东户数）进 financials 宽表，
银行专属列进 bank_financials，其余行业各自的专属列进 <行业>_financials（与 bank_financials 同构，同主键按需 JOIN）。
annual JSON 里每个字段都必须落到某一列；没登记映射的数值字段写进 data_anomaly（reason=unmapped_field），不静默丢弃。
JSON 沿用数据源字段名，落库时按 (SQL 列名, JSON 源字段名) 映射成标准英文财报列名。
company_code 是带交易所前缀的实体键（sh.601077 / sz.000001 / hk.01578，见 company.sql）；JSON 与文件名里的裸代码在这里换算。
本轮只收 JSON 派生表（oil/宏观 CSV 未纳入）。*_shareholder*.json 原始手工件较异构，股权数据统一从 annual 的 holders 与 holders_manual.json 取。
只写 data/sql/tables 里有建表语句的表；解析了但没有建表文件的表只在行数清单里标「跳过」，不写库。
"""
import os
import re
import sys
import glob
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from backend import jsonstore  # noqa: E402  JSON 成品表原文在 MySQL json_file 表，按原文件路径取
from industry_columns import (CEMENT_COLS, DEVELOPER_COLS, INSURER_COLS, INSURER_TEXT_COLS,  # noqa: E402
                              TECH_COLS, TELECOM_COLS, TELECOM_TEXT_COLS)

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
DIVIDEND_COLS = ("dividend_per_10_shares", "dividend_unit", "dividend_total")
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
CHANGE_STATUS = ("新进", "加仓", "减仓", "不变")   # 接口 HOLDER_STATE 的持股变动状态；其余取值是股份性质
LOADER = "load_to_mysql.py"                      # data_anomaly.source：本脚本写的行，--reload 时只清这些


def _industry_columns(industry):
    """<行业>_financials 的数值列：映射清单 + 文件覆盖里出现的列，按出现先后去重（一列可由多个源字段供数）。"""
    cols = list(INDUSTRY_COLS[industry]) + [t for f, ov in FILE_COLUMN_OVERRIDES.items()
                                           if f.startswith(industry + "_") for t in ov.values()]
    return list(dict.fromkeys(t[0] for t in cols))


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
                        "revenue", "source"),
    "shareholder": ("company_code", "fiscal_year", "holder_rank", "holder_name", "holder_nature",
                    "hold_num", "ratio", "shares_type", "pledged_shares", "chg_shares", "change_status",
                    "source"),
    "shareholder_meta": ("company_code", "holders_caliber", "caliber_note", "source", "factions_source",
                         "history_source"),
    "shareholder_count": ("company_code", "as_of_date", *HOLDER_COUNT_COLS, "domestic_share_holders", "source"),
    "shareholder_concentration": ("company_code", "as_of_date", "top1_holder_ratio", "top3_holders_ratio",
                                  "top10_holders_ratio", "top1_holder_ratio_excluding_nominees",
                                  "top3_holders_ratio_excluding_nominees", "top1_holder_name",
                                  "top1_holder_name_excluding_nominees", "source"),
    "shareholder_faction": ("company_code", "faction_title", "holder_name", "color", "basis", "source"),
    "share_capital_year_end": ("company_code", "fiscal_year", "total_shares", "change_summary", "source"),
    "social_financing_stock": ("period_month", "amount", "year_on_year_growth", "source"),
    "social_financing_flow": ("period_month", *[c for c, _ in SOCIAL_FINANCING_FLOW_COLS], "source"),
    "data_gap": ("company_code", "description", "reason", "source_file"),
    "data_anomaly": ("company_code", "source_file", "target_table", "field_name", "period", "raw_value",
                     "reason", "source"),
}
# 插入顺序：company 先建（外键父表）；--reload 按逆序清
INSERT_ORDER = ["company", "financials_meta", "financials", "bank_financials",
                *["%s_financials" % i for i in INDUSTRY_COLS], "bank_balance_sheet_item", "segment_revenue",
                "shareholder", "shareholder_meta", "shareholder_count", "shareholder_concentration",
                "shareholder_faction", "share_capital_year_end", "social_financing_stock",
                "social_financing_flow", "data_gap", "data_anomaly"]


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

    def add_dividend(self, code, year, per10, unit, total, override=False):
        """override=True 用于年报原文手工件：盖过东财接口值（接口把港元宣派折成了人民币）。"""
        if override or (code, year) not in self.dividends:
            self.dividends[(code, year)] = (per10, unit, total)

    def add_holder_count(self, code, date, counts, source, override=False):
        """counts = [合计, A股, H股, 内资股]。override=True（holders_manual 年报原文）整格盖过接口值；否则只补空着的格。"""
        cell = self.holder_counts.get((code, date))
        if cell is None or override:
            self.holder_counts[(code, date)] = [*counts, source]
        else:
            cell[:4] = [old if old is not None else new for old, new in zip(cell[:4], counts)]

    def add_concentration(self, code, r, source, override=False):
        """集中度一期一行：holder_concentration[{date,top1,top3,top10,top1_ex,top3_ex,top1_name,top1_ex_name}]。"""
        if override or (code, r["date"]) not in self.concentrations:
            self.concentrations[(code, r["date"])] = (code, r["date"], *[_num(r.get(k)) for k in (
                "top1", "top3", "top10", "top1_ex", "top3_ex")], _txt(r.get("top1_name")),
                _txt(r.get("top1_ex_name")), source)

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
    """{年: (公司余额, 零售余额, 公司不良, 零售不良)}，亿元换算为元；无 detail_manual 返回空。"""
    path = os.path.join(TABLES, "bank_%s_detail_manual.json" % code)
    d = jsonstore.read(path)
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
    """同义源字段并到已映射的那个字段上：那边为空才补（按倍数换成元），两边都有且不等记 data_anomaly。"""
    for alias, (canon, scale) in aliases.items():
        v = _num(row.get(alias))
        if v is None:
            continue
        cur = _num(row.get(canon))
        if cur is None:
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
                if any(v is not None for v in (*rv, *av, *cf, *au)):   # 分红 3 列、股东户数 3 列先留空，最后并入
                    L.add("financials", (code, yr, *rv, *av, *cf, None, None, None, *au, None, None, None, src))
                for f, unit in PER_SHARE_DIVIDEND_FIELDS.items():
                    if _num(row.get(f)) is not None:
                        L.add_dividend(code, yr, round(_num(row.get(f)) * 10, 6), unit, None)
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
                    L.add_dividend(code, int(year), v, "元", _num(dtot.get(year)))
            L.set_shareholders(_shareholder_rows(code, d.get("holders_end_date"), d.get("holders"), file))
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
    """接口的股份类别（流通A股 / 限售流通A股,流通H股 …）→ A / H / A,H；认不出的返回 None。"""
    s = _txt(raw) or ""
    return ",".join(c for c in ("A", "H") if c + "股" in s) or None


def _shareholder_rows(code, end_date, holders, source):
    """前十名股东 → shareholder 行。只收 12-31 的年末名册，fiscal_year 取截止日所在年；
    其余日期（如 20-F 的披露日）不入，免得错标成某个年报期。
    接口的 state 是持股变动状态（新进/加仓/减仓/不变），个别公司在这一栏写股份性质（国有法人股…），那种进 holder_nature；
    holders_manual 的 shares_type 写的是股东性质（国有法人/境内自然人…），也进 holder_nature，股份类别留空。
    change 是数字才进 chg_shares，「不变」记 0，「新进」不算股数。"""
    year = _year_end(end_date)
    rows = []
    for h in (holders or []) if year else []:
        name = _txt(h.get("name"))
        if not name:
            continue
        change, state, shares_type = _txt(h.get("change")), _txt(h.get("state")), _txt(h.get("shares_type"))
        share_class = _share_class(shares_type)
        status = state if state in CHANGE_STATUS else (change if change in CHANGE_STATUS else None)
        nature = (state if state and state not in CHANGE_STATUS else None) or (None if share_class else shares_type)
        rows.append((code, year, h.get("rank"), name, nature, _num(h.get("hold_num")), _num(h.get("ratio")),
                     share_class, _num(h.get("pledged")), 0 if change == "不变" else _num(change), status,
                     source))
    return rows


def load_holders_manual(L):
    """holders_manual.json：年报原文手工件，名册/户数/分红按期盖过接口值；分组、集中度、年末股数、口径与缺口另各进一张表。"""
    file = "holders_manual.json"
    d = _load_json(file)
    for key, e in d.items():
        if ":" not in key or not isinstance(e, dict):
            continue
        industry, raw_code = key.split(":", 1)
        code = L.ensure_company(raw_code, industry, _txt(e.get("name")))
        L.set_shareholders(_shareholder_rows(code, e.get("holders_end_date"), e.get("holders"), file), override=True)
        L.set_holder_meta(code, [_txt(e.get(k)) for k in ("holders_caliber", "caliber_note", "source",
                                                          "factions_source", "history_source")])
        for fac in e.get("factions") or []:
            for name in fac.get("names") or []:
                L.add("shareholder_faction", (code, _txt(fac.get("title")) or "", str(name),
                                              _txt(fac.get("color")), _txt(fac.get("basis")), file))
        _load_holder_count(L, code, e.get("holder_num"), file, override=True)
        for r in e.get("holder_concentration") or []:
            if isinstance(r, dict) and _txt(r.get("date")):
                L.add_concentration(code, r, file, override=True)
        for r in e.get("share_capital") or []:
            if isinstance(r, list) and r and YEAR.match(str(r[0])):
                L.add("share_capital_year_end", (code, int(r[0]), _num(r[1]) if len(r) > 1 else None,
                                                 _txt(r[2]) if len(r) > 2 else None, file))
        for g in e.get("history_gaps") or []:
            L.add("data_gap", (code, str(g), None, file))
        unit = _txt(e.get("dividend_unit")) or "元"
        dtot = e.get("dividend_total") or {}   # {年:亿元} 或 [[年,亿元]]，年报原文，禁反算
        if isinstance(dtot, list):
            dtot = {str(x[0]): x[1] for x in dtot if isinstance(x, list) and len(x) >= 2}
        for r in e.get("dividend_per10") or []:
            if isinstance(r, list) and len(r) >= 2 and YEAR.match(str(r[0])) and _num(r[1]) is not None:
                tv = _num(dtot.get(str(r[0]))) if isinstance(dtot, dict) else None
                L.add_dividend(code, int(r[0]), _num(r[1]), unit, tv, override=True)


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
    for raw_code, c in (d.get("companies") or {}).items():
        code = L.ensure_company(raw_code, "telecom", _txt(c.get("name")))
        for year, blk in (c.get("annual") or {}).items():
            if not (YEAR.match(str(year)) and isinstance((blk or {}).get("canon"), dict)):
                continue
            for seg, v in blk["canon"].items():
                labels = [k for k in (blk.get("items") or {}) if CANON.get(raw_code, {}).get(k) == seg]
                if _num(v) is not None:
                    L.add("segment_revenue", (code, int(year), seg, "、".join(labels) or None,
                                              1 if seg in ("total", "service_total") else 0, _num(v), file))


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


# 有自然主键/唯一键的表，入库前按键去重（多来源可能给出同一行），保留首次出现。
KEY_COLS = {
    "financials_meta": ("company_code",),
    "financials": ("company_code", "fiscal_year"),
    "bank_financials": ("company_code", "fiscal_year"),
    **{"%s_financials" % i: ("company_code", "fiscal_year") for i in INDUSTRY_COLS},
    "bank_balance_sheet_item": ("company_code", "fiscal_year", "statement_type", "item_code"),
    "segment_revenue": ("company_code", "fiscal_year", "segment_code"),
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
    db = jsonstore._config()      # 连接配置与 json_file 同一份：环境变量 MYSQL_*，缺的从仓库根 .env 补
    ap = argparse.ArgumentParser(description="载入 data/tables JSON（json_file 表）→ MySQL（见文件头用法）")
    ap.add_argument("--dry-run", action="store_true", help="只解析并打印各表行数，不写库")
    ap.add_argument("--host", default=db["host"])
    ap.add_argument("--port", type=int, default=db["port"])
    ap.add_argument("--user", default=db["user"])
    ap.add_argument("--password", default=db["password"])
    ap.add_argument("--db", default=db["database"])
    ap.add_argument("--init", action="store_true", help="入库前先按序执行 data/sql/tables/*.sql 建表")
    ap.add_argument("--reload", action="store_true",
                    help="同一事务里先清空本脚本要写的表再插入（全量重灌；json_file 不动）")
    a = ap.parse_args()

    L = Loader()
    load_company(L)
    load_annual(L)
    load_holders_manual(L)
    load_hshare_holder_count(L)
    load_social_financing(L)
    load_telecom_segments(L)
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
        print("dry-run：只读了 json_file，未写入。")
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
