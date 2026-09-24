-- financials  · 段 B. 财务四表合一时间序列（*_annual.json annual 里的损益/资产负债/现金流/现金分红公共列 + 审计信息，每公司每年一行）
-- 由 income(损益) + asset(资产负债) + cashflow(现金流) + dividend(现金分红) 合并而来。
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS financials
(
    company_code           CHAR(10)      NOT NULL,
    fiscal_year            SMALLINT      NOT NULL COMMENT '报告期(年度)',
    -- 损益（原 income 表）
    operating_revenue      DECIMAL(28, 4) NULL COMMENT '营业收入',
    operating_profit       DECIMAL(28, 4) NULL COMMENT '营业利润',
    profit_before_tax      DECIMAL(28, 4) NULL COMMENT '利润总额(税前利润)',
    net_profit             DECIMAL(28, 4) NULL COMMENT '净利润',
    net_profit_attr_parent DECIMAL(28, 4) NULL COMMENT '归母净利润(归属母公司股东)',
    net_margin             DECIMAL(12, 4) NULL COMMENT '净利率%',
    roe_weighted           DECIMAL(12, 4) NULL COMMENT '加权ROE%',
    eps                    DECIMAL(16, 6) NULL COMMENT '每股收益',
    -- 资产负债（原 asset 表）
    total_assets           DECIMAL(28, 4) NULL COMMENT '总资产',
    total_liabilities      DECIMAL(28, 4) NULL COMMENT '总负债',
    total_equity           DECIMAL(28, 4) NULL COMMENT '股东权益合计',
    equity_attr_parent     DECIMAL(28, 4) NULL COMMENT '归母股东权益(归属母公司股东权益)',
    share_capital          DECIMAL(28, 4) NULL COMMENT '总股本',
    bps                    DECIMAL(16, 6) NULL COMMENT '每股净资产',
    -- 现金流（原 cashflow 表）
    net_cash_operating     DECIMAL(28, 4) NULL COMMENT '经营活动现金流量净额',
    net_cash_investing     DECIMAL(28, 4) NULL COMMENT '投资活动现金流量净额',
    net_cash_financing     DECIMAL(28, 4) NULL COMMENT '筹资活动现金流量净额',
    operating_cf_per_share DECIMAL(16, 6) NULL COMMENT '每股经营现金流',
    -- 现金分红（原 dividend 表）
    dividend_per_10_shares DECIMAL(16, 6) NULL COMMENT '每 10 股派息(含税)',
    dividend_per_share     DECIMAL(16, 6) GENERATED ALWAYS AS (dividend_per_10_shares / 10) STORED COMMENT '每股现金分红(=per10/10,单位换算,非反算)',
    dividend_unit          VARCHAR(8)   NULL COMMENT '每10股派息/每股 计价单位;中国移动等按港元',
    dividend_total         DECIMAL(20, 4) NULL COMMENT '当年现金分红总额(亿元/亿港元;年报「利润分配方案」原文,禁止反算, 元还是港元根据 dividend_unit)',
    dividend_payout_ratio  DECIMAL(12, 4) GENERATED ALWAYS AS (
        CASE WHEN dividend_unit = '元' AND eps > 0
             THEN dividend_per_share / eps * 100 END) STORED
        COMMENT '派息率/股利支付率%(每股现金分红÷每股收益;仅人民币宣派且EPS>0时计,港元宣派如中国移动两者不同币种故留空)',
    -- 审计信息
    auditor                VARCHAR(255) NULL COMMENT '审计机构(会计师事务所)',
    audit_opinion          VARCHAR(64)  NULL COMMENT '审计意见类型(标准无保留/保留/否定/无法表示意见等)',
    --股东信息
    total_holders    BIGINT   NULL COMMENT '股东总户数(户)',
    a_share_holders  BIGINT   NULL COMMENT 'A股股东户数(户);纯A股公司与合计相同或留空',
    h_share_holders  BIGINT   NULL COMMENT 'H股登记股东户数(户);H股年报未披露的年份留空,不插值',
    source                 VARCHAR(255) NULL COMMENT '数据来源',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_financials_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
