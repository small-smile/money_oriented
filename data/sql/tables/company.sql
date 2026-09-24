-- company  · 段 A. 主体与来源
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS company
( -- company_codes.json entities[]
    company_code CHAR(10)    NOT NULL COMMENT '实体唯一键:有A股用A股码 sh.601919 ,纯H股用H股码 hk.01919 补充前缀做区分',
    short_name  VARCHAR(64) NOT NULL comment '公司简称',
    full_name   VARCHAR(128) NULL comment '公司全称',
    industry    VARCHAR(24) NOT NULL COMMENT 'bank/insurer/developer/cement/telecom/tech/food',
    a_code      VARCHAR(12) NULL COMMENT 'A股代码',
    h_code      VARCHAR(12) NULL comment 'H股代码',
    same_entity TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '0=两地非同一法人,不做代码互换',
    PRIMARY KEY (company_code),
    KEY         idx_company_industry (industry),
    KEY         idx_company_a (a_code),
    KEY         idx_company_h (h_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
