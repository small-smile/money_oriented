-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_executive_pay
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)',
    chairman_name             VARCHAR(128)   NULL COMMENT '董事长姓名(当年在任者,空缺照原表写 —)',
    president_name            VARCHAR(128)   NULL COMMENT '行长姓名(同上)',
    chairman_pay              DECIMAL(28, 4) NULL COMMENT '董事长税前薪酬(元,原表万元)',
    president_pay             DECIMAL(28, 4) NULL COMMENT '行长税前薪酬(元,原表万元)',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_executive_pay_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行董事长与行长薪酬（detail_manual 的 chairman-pay,年报「董事、监事和高级管理人员」）：有姓名没披露薪酬的照写行';
