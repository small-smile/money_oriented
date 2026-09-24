-- share_capital_change  · 段 C. 股本变动（年报「股份变动情况」/ 发行、配股、送转、转股、回购注销公告，每次变动每类股份一行）
-- 年末总股本只放 financials.share_capital；本表记录变动事件本身，按 change_date 累加应能对上各年末总股本。
-- 单位：股数为股；价格按 currency 计价。A+H 同一事件两类股份都变动时拆两行。
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS share_capital_change
(
    id             BIGINT        NOT NULL AUTO_INCREMENT,
    company_code   CHAR(10)      NOT NULL COMMENT '公司code(→company.company_code)',
    change_date    DATE          NOT NULL COMMENT '股本变动日(新股上市日/登记日/注销日)',
    fiscal_year    SMALLINT      GENERATED ALWAYS AS (YEAR(change_date)) STORED COMMENT '变动所属报告期(年度,=变动日所在年)',
    share_class    VARCHAR(16)   NOT NULL COMMENT '股份类别 A/H/非上市股',
    change_reason  VARCHAR(32)   NOT NULL COMMENT 'initial_public_offering/private_placement/rights_issue/bonus_share/capital_reserve_conversion/convertible_bond_conversion/share_buyback_cancellation/other',
    change_shares  BIGINT        NOT NULL COMMENT '本次变动股数(股,减少为负)',
    shares_after   BIGINT        NULL COMMENT '变动后该类股份总数(股)',
    shares_before  BIGINT        GENERATED ALWAYS AS (shares_after - change_shares) STORED COMMENT '变动前该类股份总数(股,=变动后-变动数)',
    issue_price    DECIMAL(16, 6) NULL COMMENT '发行/配股/转股/回购价格(送转为空)',
    currency       VARCHAR(8)    NULL COMMENT '价格计价单位 元/港元',
    description    VARCHAR(255)  NULL COMMENT '原文摘要(如「每10股配售1.5股」)',
    source         VARCHAR(255)  NULL COMMENT '数据来源',
    PRIMARY KEY (id),
    UNIQUE KEY uk_share_capital_change (company_code, change_date, share_class, change_reason),
    KEY idx_share_capital_change_year (company_code, fiscal_year),
    CONSTRAINT fk_share_capital_change_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股本变动事件表；A+H 两类股份分行记录';
