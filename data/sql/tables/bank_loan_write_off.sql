-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_loan_write_off
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)',
    write_offs                DECIMAL(28, 4) NULL COMMENT '本期核销(元)',
    recoveries                DECIMAL(28, 4) NULL COMMENT '收回已核销(元)',
    net_write_offs            DECIMAL(28, 4) NULL COMMENT '净核销(元,核销减收回)',
    amount_raw_unit           VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 bank_financials 贷款核销或贷款总额对账定出,金额列已换算为元',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_loan_write_off_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行贷款核销与收回（detail_manual 的 writeoff）：与 bank_financials 的 loan_write_offs(纯 H 股行年报摘录)来源不同,不拼接';
