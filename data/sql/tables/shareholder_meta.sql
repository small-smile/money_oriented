-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder_meta
(
    company_code    CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    holders_caliber VARCHAR(255) NULL COMMENT '前十名股东名册口径,如「年报口径（2025 年报「前十名股东持股情况表」）」',
    caliber_note    TEXT         NULL COMMENT '口径说明原文',
    source          TEXT         NULL COMMENT '名册来源原文',
    factions_source TEXT         NULL COMMENT '股东分组依据出处原文(见 shareholder_faction)',
    history_source  TEXT         NULL COMMENT '逐年序列出处原文(户数/集中度/年末股数)',
    PRIMARY KEY (company_code),
    CONSTRAINT fk_shareholder_meta_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股权数据的口径与出处（holders_manual.json 与银行 annual JSON 的 holders_note）';
