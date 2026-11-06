-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_loan_migration_rate
(
    company_code                   CHAR(10)      NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                    SMALLINT      NOT NULL COMMENT '报告期(年度)',
    normal_migration_rate          DECIMAL(12, 4) NULL COMMENT '正常类贷款迁徙率%',
    special_mention_migration_rate DECIMAL(12, 4) NULL COMMENT '关注类贷款迁徙率%',
    substandard_migration_rate     DECIMAL(12, 4) NULL COMMENT '次级类贷款迁徙率%',
    doubtful_migration_rate        DECIMAL(12, 4) NULL COMMENT '可疑类贷款迁徙率%',
    columns_missing_in_source      VARCHAR(1024) NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格(如正常类序列比其他三类起得早),其余列为空是原表列了但未披露',
    source_file                    VARCHAR(255)  NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_loan_migration_rate_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行贷款迁徙率（detail_manual 的 migrate,监管口径）：原表列了这一年但未披露的,四列全空也写行';
