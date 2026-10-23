-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS negative_matter
(
    company_code   CHAR(10)       NOT NULL,
    fiscal_year    SMALLINT       NOT NULL COMMENT '报告期(年度)',
    item_code      VARCHAR(64)    NOT NULL COMMENT 'major_litigation_arbitration=重大诉讼、仲裁/penalty_or_investigation=公司及董监高被立案调查或受处罚/related_party_fund_occupation=控股股东及其他关联方非经营性占用资金/illegal_guarantee=违规对外担保/integrity_breach=诚信问题(未履行法院生效判决、大额债务到期未清偿)/bankruptcy_reorganization=破产重整/commitment_breach=承诺未履行/accounting_error_correction=重大会计差错更正(追溯重述)',
    has_matter     TINYINT(1)     NULL COMMENT '1=年报披露存在/0=年报明确写无/NULL=年报未提及(原因写 missing_reason),按年报对「重大」的表态记,日常未决诉讼另记 case_count 与 amount',
    case_count     INT            NULL COMMENT '案件数(件),年报给出时填',
    amount         DECIMAL(28, 4) NULL COMMENT '涉及金额(元),如未决诉讼标的,年报原值换算为元',
    raw_unit       VARCHAR(32)    NULL COMMENT '年报原始单位(万元/亿元等)',
    summary        TEXT           NULL COMMENT '年报原文摘录,照抄不改写,多起案件逐案写在这里',
    caliber_note   TEXT           NULL COMMENT '口径说明(本集团/本行、被告或第三人等范围、H股回退)',
    source_file    VARCHAR(255)   NULL COMMENT '具体源文件',
    source_section VARCHAR(255)   NULL COMMENT '来源章节,如 第六章 重要事项-四、重大诉讼及仲裁事项',
    source_page    VARCHAR(32)    NULL COMMENT '来源页码',
    is_derived     TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否推算值(如多案金额加总,图上须标记)',
    missing_reason VARCHAR(255)   NULL COMMENT '缺失原因',
    PRIMARY KEY (company_code, fiscal_year, item_code),
    CONSTRAINT fk_negative_matter_company
        FOREIGN KEY (company_code) REFERENCES company (company_code),
    KEY idx_negative_matter_year (fiscal_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='年报负面事项清单(A股年报「重要事项」章),年报未提及的事项也写行(has_matter 留空),审计意见见 financials.audit_opinion 不重复收';
