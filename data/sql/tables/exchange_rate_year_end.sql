-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS exchange_rate_year_end
(
    fiscal_year   SMALLINT       NOT NULL COMMENT '年度',
    currency      VARCHAR(8)     NOT NULL COMMENT '外币：港元(与各表 currency/dividend_unit 同一写法)',
    rmb_per_unit  DECIMAL(16, 6) NOT NULL COMMENT '1 单位外币折人民币元(人民币汇率中间价,原文 HKD/CNY 报价)',
    rate_date     DATE           NOT NULL COMMENT '取值日：该年最后一个中间价发布日',
    source        VARCHAR(255)   NULL COMMENT '来源(中国外汇交易中心 中国货币网 人民币汇率中间价)',
    PRIMARY KEY (fiscal_year, currency)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='年末人民币汇率中间价（data/tables/exchange_rate_year_end.json,由 fetch_exchange_rate_year_end.py 抓取,接口 2006 年起有数）：港股价折人民币算股息率等用';
