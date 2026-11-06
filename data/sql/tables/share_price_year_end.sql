-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS share_price_year_end
(
    company_code CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)；A+H 两地上市的只存 A 股价格,纯 H 股行存港股价格',
    fiscal_year  SMALLINT       NOT NULL COMMENT '年度',
    trade_date   DATE           NULL COMMENT '取价交易日：该股当年最后一个有成交的交易日,停牌跨年末时早于年末(如招商银行 2005-12-16)',
    close_price  DECIMAL(16, 4) NULL COMMENT '年末每股收盘价(不复权,当日实际成交价)',
    currency     VARCHAR(8)     NULL COMMENT '计价币种：元/港元',
    source       VARCHAR(255)   NULL COMMENT '行情来源：交易所(上交所/深交所/港交所)优先,交易所查不到的年份才用第三方(腾讯证券/Yahoo Finance)',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_share_price_year_end_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='年末每股价格（data/tables/share_price_year_end.json,由 fetch_share_price_year_end.py 抓取,目前只有银行）：年末股数见 share_capital_year_end';
