-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_financial_investment_by_measurement
(
    company_code                                         CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year                                          SMALLINT       NOT NULL COMMENT '报告期(年度)',
    amortized_cost                                       DECIMAL(28, 4) NULL COMMENT '以摊余成本计量的金融投资(元)',
    fair_value_through_other_comprehensive_income_debt   DECIMAL(28, 4) NULL COMMENT '以公允价值计量且其变动计入其他综合收益的金融投资——债务工具(元)',
    fair_value_through_other_comprehensive_income_equity DECIMAL(28, 4) NULL COMMENT '以公允价值计量且其变动计入其他综合收益的金融投资——权益工具(元)',
    fair_value_through_profit_or_loss                    DECIMAL(28, 4) NULL COMMENT '以公允价值计量且其变动计入当期损益的金融投资(元)',
    amount_raw_unit                                      VARCHAR(8)     NULL COMMENT '原表金额单位(亿元/百万元/千元/元),按 financials 总资产对账定出,金额列已换算为元',
    columns_missing_in_source                            VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file                                          VARCHAR(255)   NULL COMMENT '来源文件,如 bank_601288_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_financial_investment_by_measurement_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行金融投资按计量方式三分类（detail_manual 的 invest,新金融工具准则口径）';
