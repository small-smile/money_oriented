-- shareholder  · 段 C. 股权结构
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder
( -- 某一期 top 股东明细表；A+H 的数据源从 A 出
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    company_code  CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year   SMALLINT     NOT NULL COMMENT '报告期(年度)',
    holder_name   VARCHAR(128) NOT NULL COMMENT '股东名称',
    holder_short  VARCHAR(64) NULL COMMENT '股东名称(短)',
    concert_party VARCHAR(128) NULL COMMENT '一致行动人',
    concert_short VARCHAR(64) NULL COMMENT '一致行动人(短)',
    is_state      TINYINT(1)    NULL COMMENT '是否国资',
    is_foreign    TINYINT(1)    NULL COMMENT '是否外资',
    is_natural    TINYINT(1)    NULL COMMENT '是否自然人',
    is_listed     TINYINT(1)    NULL COMMENT '是否上市',
    hold_num      BIGINT NULL COMMENT '期末持股数(股)',
    ratio         DECIMAL(10, 4) NULL COMMENT '期末持股比例%',
    shares_type   VARCHAR(16) NULL COMMENT '股份类别 A/H/非上市股',
    chg_shares    BIGINT NULL COMMENT '报告期内股本变动(股)',
    chg_ratio     DECIMAL(10, 4) NULL COMMENT '报告期内股本变动(比例)',
    is_additional TINYINT(1) NULL COMMENT '是否补充股东：不在A股前十名名册、据H股≥5%主要股东权益披露补入(如Peaktrade)，1=是 ，　或者5%以上股东、控股股东、实际控制人等权益披露中的实际披露　',
    source        VARCHAR(255) NULL COMMENT '数据来源',
    PRIMARY KEY (id),
    UNIQUE KEY uk_shareholder (company_code, fiscal_year, holder_name),
    CONSTRAINT fk_shareholder_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 comment='某一期的股权结构  优先使用 A 股的top 10 股东数据 ,  ';
