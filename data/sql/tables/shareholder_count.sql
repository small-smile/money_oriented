-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder_count
(
    company_code    CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    as_of_date      DATE         NOT NULL COMMENT '截止日',
    total_holders   BIGINT       NULL COMMENT '股东总户数(户)',
    a_share_holders BIGINT       NULL COMMENT 'A股股东户数(户)；纯A股公司与合计相同或留空',
    h_share_holders BIGINT       NULL COMMENT 'H股登记股东户数(户)；未披露留空,不插值',
    domestic_share_holders BIGINT NULL COMMENT '内资股(非境外上市股)股东户数(户)；纯 H 股行年报单列时才有,不并入合计',
    source          VARCHAR(255) NULL COMMENT '来源文件(最早给出本期的那份)',
    revised_by      VARCHAR(255) NULL COMMENT '年报原文手工件改过或补过本行格子时记该文件(如 bank_600016_shareholder_manual.json),没改过为空',
    PRIMARY KEY (company_code, as_of_date),
    CONSTRAINT fk_shareholder_count_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股东户数逐期序列（annual JSON 与 holders_manual.json 的 holder_num、纯 H 股行的 holder_count、渝农商行 H 股户数 holder_count_hshare_2010_2018.json；银行年报原文手工件 bank_<code>_shareholder_manual.json、ar_manual 的 holder_count_by_year、渝农商行精编件 company_charts_601077.json 的非空格子盖过接口值）：年末（12-31）那一期同时并入 financials 的户数列，本表另含季度末、披露日前月末等各期';
