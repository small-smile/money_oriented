-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_loan_quality_by_segment
(
    company_code                        CHAR(10)      NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                         SMALLINT      NOT NULL COMMENT '报告期(年度)',
    corporate_non_performing_loan_ratio DECIMAL(12, 4) NULL COMMENT '公司贷款不良率%',
    retail_non_performing_loan_ratio    DECIMAL(12, 4) NULL COMMENT '零售(个人)贷款不良率%',
    columns_missing_in_source           VARCHAR(1024) NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file                         VARCHAR(255)  NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_loan_quality_by_segment_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行公司与零售贷款不良率（detail_manual 的 loantrend）：同一主题的公司/零售贷款余额与不良余额在 bank_financials,年份轴以本表为准,原表列了这一年但未披露的也写行';
