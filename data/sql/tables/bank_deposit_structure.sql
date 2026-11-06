-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_deposit_structure
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)；只给年报当年一期',
    time_deposits             DECIMAL(28, 4) NULL COMMENT '定期存款(元)',
    demand_deposits           DECIMAL(28, 4) NULL COMMENT '活期存款(元)',
    margin_and_other_deposits DECIMAL(28, 4) NULL COMMENT '保证金及其他存款(元)',
    amount_raw_unit           VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 bank_financials 吸收存款对账定出,金额列已换算为元',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_deposit_structure_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行客户存款期限结构（detail_manual 的 depterm）：年报当年末快照';
