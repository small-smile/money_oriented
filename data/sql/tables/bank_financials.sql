-- bank_financials  · 段 B. 银行业专属年度指标（bank_*_annual.json annual 里 financials 公共列以外的银行字段，每行每年一行）
-- 公司/零售贷款余额与不良余额 4 列来自 bank_*_detail_manual.json 的 loantrend（亿元，入库换算为元）。
-- 与 financials 同主键 (company_code, fiscal_year)，按需 JOIN；公共列（营收/净利/总资产等）只放 financials，不在此重复。
-- 单位：金额为元；比率为 %；loan_to_deposit_ratio 例外为小数（与 JSON 源一致，不换算）。
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_financials
(
    company_code                     CHAR(10)       NOT NULL,
    fiscal_year                      SMALLINT       NOT NULL COMMENT '报告期(年度)',
    -- 收入结构与盈利能力
    net_interest_income              DECIMAL(28, 4) NULL COMMENT '利息净收入',
    net_fee_commission_income        DECIMAL(28, 4) NULL COMMENT '手续费及佣金净收入',
    net_interest_margin              DECIMAL(12, 4) NULL COMMENT '净息差%',
    net_interest_spread              DECIMAL(12, 4) NULL COMMENT '净利差%',
    general_admin_expenses           DECIMAL(28, 4) NULL COMMENT '业务及管理费',
    cost_income_ratio                DECIMAL(12, 4) NULL COMMENT '成本收入比%',
    return_on_assets                 DECIMAL(12, 4) NULL COMMENT '总资产收益率ROA%',
    credit_impairment_loss           DECIMAL(28, 4) NULL COMMENT '信用减值损失',
    asset_impairment_loss            DECIMAL(28, 4) NULL COMMENT '资产减值损失(旧准则口径)',
    -- 贷款与存款
    gross_loans                      DECIMAL(28, 4) NULL COMMENT '发放贷款和垫款总额(减值准备前)',
    net_loans                        DECIMAL(28, 4) NULL COMMENT '发放贷款和垫款(资产负债表净额)',
    loan_loss_allowance              DECIMAL(28, 4) NULL COMMENT '贷款损失准备',
    customer_deposits                DECIMAL(28, 4) NULL COMMENT '客户存款总额(本金口径)',
    customer_deposits_balance_sheet  DECIMAL(28, 4) NULL COMMENT '吸收存款(资产负债表列报,可含应计利息)',
    loan_to_deposit_ratio            DECIMAL(12, 6) NULL COMMENT '存贷比(小数,非%)',
    corporate_loans                  DECIMAL(28, 4) NULL COMMENT '公司贷款期末余额(是否含票据贴现按各行 detail_manual 的 _notes.loantrend)',
    retail_loans                     DECIMAL(28, 4) NULL COMMENT '零售(个人)贷款期末余额',
    -- 资产质量
    non_performing_loans             DECIMAL(28, 4) NULL COMMENT '不良贷款余额',
    non_performing_loan_ratio        DECIMAL(12, 4) NULL COMMENT '不良贷款率%',
    corporate_non_performing_loans   DECIMAL(28, 4) NULL COMMENT '公司贷款不良余额(与 corporate_loans 同口径;年报未单列则 NULL,不反算)',
    retail_non_performing_loans      DECIMAL(28, 4) NULL COMMENT '零售(个人)贷款不良余额(同上)',
    non_performing_loan_formation    DECIMAL(28, 4) NULL COMMENT '不良贷款生成额',
    non_performing_loan_formation_rate DECIMAL(12, 4) NULL COMMENT '不良贷款生成率%',
    overdue_loans                    DECIMAL(28, 4) NULL COMMENT '逾期贷款',
    net_charge_off                   DECIMAL(28, 4) NULL COMMENT '核销及转出净额',
    provision_coverage_ratio         DECIMAL(12, 4) NULL COMMENT '拨备覆盖率%',
    loan_allowance_ratio             DECIMAL(12, 4) NULL COMMENT '拨贷比%',
    -- 资本与流动性
    capital_adequacy_ratio           DECIMAL(12, 4) NULL COMMENT '资本充足率%',
    tier1_capital_ratio              DECIMAL(12, 4) NULL COMMENT '一级资本充足率%',
    core_tier1_capital_ratio         DECIMAL(12, 4) NULL COMMENT '核心一级资本充足率%',
    leverage_ratio                   DECIMAL(12, 4) NULL COMMENT '杠杆率%',
    liquidity_coverage_ratio         DECIMAL(12, 4) NULL COMMENT '流动性覆盖率%',
    net_stable_funding_ratio         DECIMAL(12, 4) NULL COMMENT '净稳定资金比例%',
    equity_asset_ratio               DECIMAL(12, 4) NULL COMMENT '权益资产比%',
    -- 银行特有资产负债科目
    cash_and_central_bank_deposits   DECIMAL(28, 4) NULL COMMENT '现金及存放中央银行款项',
    due_from_banks                   DECIMAL(28, 4) NULL COMMENT '存放同业和其他金融机构款项',
    placements_with_banks            DECIMAL(28, 4) NULL COMMENT '拆出资金',
    reverse_repurchase_assets        DECIMAL(28, 4) NULL COMMENT '买入返售金融资产',
    trading_financial_assets         DECIMAL(28, 4) NULL COMMENT '交易性金融资产',
    fvtpl_financial_assets           DECIMAL(28, 4) NULL COMMENT '以公允价值计量且其变动计入当期损益的金融资产',
    fvtoci_financial_assets          DECIMAL(28, 4) NULL COMMENT '以公允价值计量且其变动计入其他综合收益的金融资产',
    amortized_cost_financial_assets  DECIMAL(28, 4) NULL COMMENT '以摊余成本计量的金融资产',
    debt_investments                 DECIMAL(28, 4) NULL COMMENT '债权投资',
    other_debt_investments           DECIMAL(28, 4) NULL COMMENT '其他债权投资',
    other_equity_investments         DECIMAL(28, 4) NULL COMMENT '其他权益工具投资',
    borrowings_from_central_bank     DECIMAL(28, 4) NULL COMMENT '向中央银行借款',
    due_to_banks                     DECIMAL(28, 4) NULL COMMENT '同业和其他金融机构存放款项',
    placements_from_banks            DECIMAL(28, 4) NULL COMMENT '拆入资金',
    repurchase_agreements            DECIMAL(28, 4) NULL COMMENT '卖出回购金融资产款',
    bonds_payable                    DECIMAL(28, 4) NULL COMMENT '应付债券(应计利息并入;永续债不入)',
    -- 规模
    employee_count                   INT            NULL COMMENT '员工人数(人)',
    source                           VARCHAR(255)   NULL COMMENT '数据来源',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_financials_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
