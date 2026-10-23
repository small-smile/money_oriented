-- bank_balance_sheet_item · 银行资产负债表逐项明细
-- 一公司、一年、一报表、一科目一行，兼容各银行科目名称、层级、单位和会计口径差异。
-- 现有 annual JSON 只有标准化字段；raw_*、层级、页码等字段为年报原文补录预留。
-- 金额统一入库为元；无法确认单位或口径时保留原值并写入 caliber_note，不擅自换算。
CREATE TABLE IF NOT EXISTS bank_balance_sheet_item
(
    company_code         CHAR(10)       NOT NULL,
    fiscal_year          SMALLINT       NOT NULL COMMENT '报告期(年度)',
    statement_type       VARCHAR(32)    NOT NULL DEFAULT 'consolidated' COMMENT '合并/母公司',
    section              VARCHAR(16)    NOT NULL COMMENT 'asset/liability/equity',
    item_code            VARCHAR(64)    NOT NULL COMMENT '标准化科目编码',
    item_name            VARCHAR(128)   NOT NULL COMMENT '标准化科目名称',
    raw_item_name        VARCHAR(255)   NULL COMMENT '年报原始项目名称',
    parent_item_code     VARCHAR(64)    NULL COMMENT '原始报表父项目编码',
    item_level           TINYINT        NULL COMMENT '原始报表层级',
    raw_value            DECIMAL(28, 4) NULL COMMENT '原始数值，未做单位换算',
    raw_unit             VARCHAR(32)    NULL COMMENT '原始单位',
    value                DECIMAL(28, 4) NULL COMMENT '统一值；金额为元',
    unit                 VARCHAR(32)    NULL COMMENT '统一单位',
    scope                VARCHAR(32)    NULL COMMENT '合并/母公司等口径',
    accounting_standard  VARCHAR(64)    NULL COMMENT '会计准则或分类口径',
    caliber_note         TEXT           NULL COMMENT '口径、重述、科目迁移和缺失说明',
    source_file          VARCHAR(255)   NULL COMMENT '具体源文件',
    source_section       VARCHAR(255)   NULL COMMENT '来源章节或报表名称',
    source_page          VARCHAR(32)    NULL COMMENT '来源页码',
    is_derived           TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否派生值',
    missing_reason       VARCHAR(255)   NULL COMMENT '缺失原因',
    PRIMARY KEY (company_code, fiscal_year, statement_type, item_code),
    CONSTRAINT fk_bank_balance_sheet_item_company
        FOREIGN KEY (company_code) REFERENCES company (company_code),
    KEY idx_bank_balance_sheet_item_year (fiscal_year),
    KEY idx_bank_balance_sheet_item_name (item_name),
    KEY idx_bank_balance_sheet_item_raw_name (raw_item_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
