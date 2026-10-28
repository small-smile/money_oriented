-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS company_annual_status
(
    company_code   CHAR(10)   NOT NULL,
    fiscal_year    SMALLINT   NOT NULL COMMENT '报告期(年度)',
    -- 重大风险（年报「重要提示」与「重要事项」）
    has_major_risk TINYINT(1) NULL COMMENT '是否存在重大风险:1=存在/0=不存在/NULL=年报未表态。「重要提示」点名需特别关注的重大风险,或「重要事项」写明有重大诉讼仲裁、资金占用、违规担保、立案调查或处罚、诚信问题、破产重整、承诺未履行、重大会计差错更正之一,记 1。只罗列信用、市场等常规风险的记 0,日常未决诉讼不算',
    risk_items     TEXT       NULL COMMENT '风险项,照年报原文列出(如 信用风险、市场风险、流动性风险),存在重大风险时写明是哪一项',
    source         TEXT       NULL COMMENT '出处:年报文件、章节、页码',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_company_annual_status_company
        FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='公司每年情况(年报里财务数据以外的信息,财务数据见 financials)';
