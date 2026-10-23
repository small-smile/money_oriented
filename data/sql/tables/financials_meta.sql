-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS financials_meta
(
    company_code CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    currency     VARCHAR(8)   NULL COMMENT '报表币种 CNY/HKD',
    unit_note    VARCHAR(255) NULL COMMENT '单位说明原文',
    caliber_note TEXT         NULL COMMENT '口径说明原文(重述、口径断点、汇率等)',
    dividend_note       TEXT     NULL COMMENT '分红口径说明原文(三家纯 H 股行)',
    exchange_rate_note  TEXT     NULL COMMENT '汇率折算说明原文(中国太平港币金额折人民币)',
    a_share_report_from SMALLINT NULL COMMENT 'A 股年报口径起始年(之前年份为上市前回填,见 telecom_financials.disclosure_source)',
    source       TEXT         NULL COMMENT '数据来源原文',
    source_file  VARCHAR(255) NULL COMMENT '来源文件,如 bank_601077_annual.json',
    fetched_at   DATETIME     NULL COMMENT '抓取时间(UTC)',
    PRIMARY KEY (company_code),
    CONSTRAINT fk_financials_meta_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='年度财务序列元信息（<行业>_<code>_annual.json 顶层字段与 _meta）：币种、单位与口径对 financials / bank_financials / <行业>_financials 中同一公司的全部年份生效';
