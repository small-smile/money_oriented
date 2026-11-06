-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_fair_value_hierarchy
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)',
    period_label              VARCHAR(16)    NULL COMMENT '原表期次写法与年份不同时照存(如 2024 年末),其余为空',
    level_1                   DECIMAL(28, 4) NULL COMMENT '第一层次公允价值计量的金融资产(元)',
    level_2                   DECIMAL(28, 4) NULL COMMENT '第二层次(元)',
    level_3                   DECIMAL(28, 4) NULL COMMENT '第三层次(元)',
    total                     DECIMAL(28, 4) NULL COMMENT '合计(元,年报原值,不由三个层次相加)',
    amount_raw_unit           VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 financials 总资产对账定出,金额列已换算为元',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_fair_value_hierarchy_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行以公允价值计量的金融资产按层级（detail_manual 的 fvlevel）：年末持续以公允价值计量的部分';
