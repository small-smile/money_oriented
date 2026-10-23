-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder_count
(
    company_code    CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    as_of_date      DATE         NOT NULL COMMENT '截止日',
    total_holders   BIGINT       NULL COMMENT '股东总户数(户)',
    a_share_holders BIGINT       NULL COMMENT 'A股股东户数(户)；纯A股公司与合计相同或留空',
    h_share_holders BIGINT       NULL COMMENT 'H股登记股东户数(户)；未披露留空,不插值',
    domestic_share_holders BIGINT NULL COMMENT '内资股(非境外上市股)股东户数(户)；纯 H 股行年报单列时才有,不并入合计',
    source          VARCHAR(255) NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, as_of_date),
    CONSTRAINT fk_shareholder_count_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股东户数逐期序列（annual JSON 与 holders_manual.json 的 holder_num、纯 H 股行的 holder_count、渝农商行 H 股户数 holder_count_hshare_2010_2018.json）：年末（12-31）那一期同时并入 financials 的户数列，本表另含季度末、披露日前月末等各期';
