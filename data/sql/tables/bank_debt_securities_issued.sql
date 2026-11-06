-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_debt_securities_issued
(
    company_code                                      CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                                       SMALLINT       NOT NULL COMMENT '报告期(年度)',
    interbank_certificates_of_deposit                 DECIMAL(28, 4) NULL COMMENT '已发行同业存单期末余额(元)',
    bonds                                             DECIMAL(28, 4) NULL COMMENT '应付债券期末余额(元,金融债/二级资本债等,不含同业存单)',
    total                                             DECIMAL(28, 4) NULL COMMENT '已发行债务证券期末余额合计(元)；只整体披露的行只有这一列',
    interbank_certificates_of_deposit_average_balance DECIMAL(28, 4) NULL COMMENT '同业存单平均余额(元)',
    bonds_average_balance                             DECIMAL(28, 4) NULL COMMENT '应付债券平均余额(元)',
    total_average_balance                             DECIMAL(28, 4) NULL COMMENT '已发行债务证券平均余额合计(元)',
    interbank_certificates_of_deposit_cost_rate       DECIMAL(12, 4) NULL COMMENT '同业存单平均成本率%',
    bonds_cost_rate                                   DECIMAL(12, 4) NULL COMMENT '应付债券平均成本率%',
    total_cost_rate                                   DECIMAL(12, 4) NULL COMMENT '已发行债务证券平均成本率%',
    amount_raw_unit                                   VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 bank_financials 应付债券对账定出,金额列已换算为元',
    columns_missing_in_source                         VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file                                       VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_debt_securities_issued_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行已发行债务证券余额与成本率（detail_manual 的 bondpay,年报「应付债券」附注与利息支出表）：逐笔债券在 bank_bond_issue,原表列了这一年但未披露的也写行';
