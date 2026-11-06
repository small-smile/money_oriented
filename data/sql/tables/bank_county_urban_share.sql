-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_county_urban_share
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)；只给年报当年一期',
    deposits_county_share     DECIMAL(12, 4) NULL COMMENT '存款县域占比%',
    deposits_urban_share      DECIMAL(12, 4) NULL COMMENT '存款主城占比%',
    loans_county_share        DECIMAL(12, 4) NULL COMMENT '贷款县域占比%',
    loans_urban_share         DECIMAL(12, 4) NULL COMMENT '贷款主城占比%',
    assets_county_share       DECIMAL(12, 4) NULL COMMENT '资产县域占比%',
    assets_urban_share        DECIMAL(12, 4) NULL COMMENT '资产主城占比%',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_601077_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_county_urban_share_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行县域与主城业务占比（detail_manual 的 geo）：只有披露县域口径的行有';
