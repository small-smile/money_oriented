-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS social_financing_flow
(
    period_month                     CHAR(7)        NOT NULL COMMENT '月份 YYYY-MM',
    total                            DECIMAL(20, 4) NULL COMMENT '社会融资规模增量(亿元)',
    renminbi_loans                   DECIMAL(20, 4) NULL COMMENT '人民币贷款(亿元)',
    foreign_currency_loans           DECIMAL(20, 4) NULL COMMENT '外币贷款(折合人民币,亿元)',
    entrusted_loans                  DECIMAL(20, 4) NULL COMMENT '委托贷款(亿元)',
    trust_loans                      DECIMAL(20, 4) NULL COMMENT '信托贷款(亿元)',
    undiscounted_bankers_acceptances DECIMAL(20, 4) NULL COMMENT '未贴现银行承兑汇票(亿元)',
    corporate_bonds                  DECIMAL(20, 4) NULL COMMENT '企业债券(亿元)',
    government_bonds                 DECIMAL(20, 4) NULL COMMENT '政府债券(亿元)',
    domestic_equity_financing        DECIMAL(20, 4) NULL COMMENT '非金融企业境内股票融资(亿元)',
    asset_backed_securities          DECIMAL(20, 4) NULL COMMENT '存款类金融机构资产支持证券(亿元)',
    loan_write_offs                  DECIMAL(20, 4) NULL COMMENT '贷款核销(亿元)',
    source                           VARCHAR(255)   NULL COMMENT '数据来源',
    PRIMARY KEY (period_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='社会融资规模增量及分项（social_financing_pboc_flow.json，人民银行调查统计司增量统计表，按月，亿元人民币）：分项与原表科目一一对应，未披露的月份留空';
