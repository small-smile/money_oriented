-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_quarterly_operating_cash_flow
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)；只给年报当年一期',
    first_quarter             DECIMAL(28, 4) NULL COMMENT '第一季度经营活动现金流量净额(元)',
    second_quarter            DECIMAL(28, 4) NULL COMMENT '第二季度经营活动现金流量净额(元)',
    third_quarter             DECIMAL(28, 4) NULL COMMENT '第三季度经营活动现金流量净额(元)',
    fourth_quarter            DECIMAL(28, 4) NULL COMMENT '第四季度经营活动现金流量净额(元)',
    amount_raw_unit           VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按全年经营活动现金流量净额对账定出,金额列已换算为元',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_quarterly_operating_cash_flow_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行分季度经营活动现金流（detail_manual 的 cf）：年报「分季度主要财务指标」,首季等于全年而四季之和对不上的记 data_anomaly';
