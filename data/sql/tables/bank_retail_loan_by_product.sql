-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_retail_loan_by_product
(
    company_code                                   CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                                    SMALLINT       NOT NULL COMMENT '报告期(年度)',
    residential_mortgage_loans                     DECIMAL(28, 4) NULL COMMENT '个人住房贷款余额(元)',
    personal_business_loans                        DECIMAL(28, 4) NULL COMMENT '个人经营贷款余额(元)',
    credit_card_loans                              DECIMAL(28, 4) NULL COMMENT '信用卡贷款余额(元)',
    personal_consumer_loans                        DECIMAL(28, 4) NULL COMMENT '个人消费贷款余额(元)',
    other_retail_loans                             DECIMAL(28, 4) NULL COMMENT '其他零售贷款余额(元)',
    residential_mortgage_non_performing_loan_ratio DECIMAL(12, 4) NULL COMMENT '个人住房贷款不良率%',
    personal_business_non_performing_loan_ratio    DECIMAL(12, 4) NULL COMMENT '个人经营贷款不良率%',
    other_retail_non_performing_loan_ratio         DECIMAL(12, 4) NULL COMMENT '其他零售贷款不良率%(含消费贷与信用卡,与 other_retail_loans 口径不同)',
    amount_raw_unit                                VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 bank_financials 贷款总额对账定出,余额列已换算为元',
    columns_missing_in_source                      VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file                                    VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_retail_loan_by_product_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行零售贷款分品种（detail_manual 的 perloan-bal）：原表列了这一年但未披露的也写行';
