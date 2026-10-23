-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder_faction
(
    company_code  CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    faction_title VARCHAR(64)  NOT NULL COMMENT '分组名称',
    holder_name   VARCHAR(128) NOT NULL COMMENT '组内股东名称(与前十名股东表逐字一致)',
    color         VARCHAR(16)  NULL COMMENT '页面着色',
    basis         VARCHAR(32)  NULL COMMENT '分组依据 年报披露=年报或20-F 明确的关联关系、一致行动人、控股股东/同类归并=本项目按股东性质归的堆,年报未认定一致行动/同一主体=同一法人的多个证券账户/20-F 披露',
    source        VARCHAR(255) NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, faction_title, holder_name),
    CONSTRAINT fk_shareholder_faction_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股东分组（holders_manual.json factions[]，一组一成员一行）：「同类归并」不是一致行动人，不写进 shareholder.concert_party';
