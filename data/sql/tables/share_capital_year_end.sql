-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS share_capital_year_end
(
    company_code   CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year    SMALLINT     NOT NULL COMMENT '报告期(年度)',
    total_shares   BIGINT       NULL COMMENT '年末股份总数(股)；是股数不是 financials.share_capital 的股本金额(元),中国移动等无面值公司两者不等',
    change_summary TEXT         NULL COMMENT '当年股本变动摘要原文(未变动/IPO/回购注销…)',
    change_type    VARCHAR(8)   NULL COMMENT '当年资本运作类型(股权页按它给点上色)：ipo=IPO/上市发行,pp=非公开定向增发,seo=增发/超额配股权行使；只有精编过成因的年份才有',
    share_split_factor DECIMAL(10, 4) NULL COMMENT '拆股折算系数：拆细前各年股数 × 本系数 = 拆细后口径(百度 2021 年 1 拆 80,2005–2019 年记 80)；没有拆并股的为空,断点说明见 data_note 的 share_capital_break',
    source         VARCHAR(255) NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_share_capital_year_end_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='年末股份总数（holders_manual.json 的 share_capital 与 bank_<code>_ar_manual.json 的 share_capital_events（目前只有渝农商行），年报「股份变动情况」逐年抄录）：变动事件本身（日期、股数、价格）见 share_capital_change';
