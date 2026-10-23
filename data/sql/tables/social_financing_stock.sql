-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS social_financing_stock
(
    period_month        CHAR(7)        NOT NULL COMMENT '月份 YYYY-MM',
    amount              DECIMAL(20, 4) NULL COMMENT '社会融资规模存量(万亿元人民币)',
    year_on_year_growth DECIMAL(12, 4) NULL COMMENT '同比增速%',
    source              VARCHAR(255)   NULL COMMENT '数据来源',
    PRIMARY KEY (period_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='社会融资规模存量（social_financing_pboc_stock.json，人民银行调查统计司存量统计表，按月）';
