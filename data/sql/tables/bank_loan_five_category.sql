-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_loan_five_category
(
    company_code                CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                 SMALLINT       NOT NULL COMMENT '报告期(年度)；只给年报当年一期',
    normal_loans                DECIMAL(28, 4) NULL COMMENT '正常类贷款余额(元)',
    special_mention_loans       DECIMAL(28, 4) NULL COMMENT '关注类贷款余额(元)',
    substandard_loans           DECIMAL(28, 4) NULL COMMENT '次级类贷款余额(元)',
    doubtful_loans              DECIMAL(28, 4) NULL COMMENT '可疑类贷款余额(元)',
    loss_loans                  DECIMAL(28, 4) NULL COMMENT '损失类贷款余额(元)',
    normal_loans_share          DECIMAL(12, 4) NULL COMMENT '正常类占比%(原表只给占比时填,此时余额列为空)',
    special_mention_loans_share DECIMAL(12, 4) NULL COMMENT '关注类占比%',
    substandard_loans_share     DECIMAL(12, 4) NULL COMMENT '次级类占比%',
    doubtful_loans_share        DECIMAL(12, 4) NULL COMMENT '可疑类占比%',
    loss_loans_share            DECIMAL(12, 4) NULL COMMENT '损失类占比%',
    amount_raw_unit             VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 bank_financials 贷款总额对账定出,余额列已换算为元',
    columns_missing_in_source   VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：只给占比的行这里列出五个余额列,只给余额的列出五个占比列',
    source_file                 VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_loan_five_category_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行贷款五级分类（detail_manual 的 5tier）：年报当年末快照,五项合计约 100 的按占比入库,否则按余额';
