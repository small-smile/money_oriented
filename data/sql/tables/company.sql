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
    us_code     VARCHAR(12)  NULL COMMENT '美股代码',
    tier        VARCHAR(32)  NULL COMMENT '银行类型 国有大行/股份行/城商行/农商行',
    group_name  VARCHAR(64)  NULL COMMENT '所属集团/控股股东(annual JSON 的 group)',
    note        TEXT         NULL COMMENT '代码对应说明(company_codes.json note)',
    source      TEXT         NULL COMMENT '代码对应出处(company_codes.json sources[],一行一条)',
    PRIMARY KEY (company_code),
    KEY         idx_company_industry (industry),
    KEY         idx_company_a (a_code),
    KEY         idx_company_h (h_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='主体与来源（company_codes.json entities[]）';
