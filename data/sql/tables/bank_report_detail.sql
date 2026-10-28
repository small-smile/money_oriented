-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_report_detail
(
    company_code CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year  SMALLINT       NOT NULL COMMENT '报告期(年度)；只给一期的主题(存款期限、五级分类、分季度现金流、员工构成、县域占比)记年报当年',
    period_label VARCHAR(16)    NULL COMMENT '原表期次写法与年份不同时照存(如 2024 年末),其余为空',
    topic        VARCHAR(48)    NOT NULL COMMENT '主题(括号内为 detail_manual 的键) net_interest_rate_item=生息资产收益率与付息负债成本率(nim)/deposit_structure=客户存款期限结构(depterm)/loan_five_category=贷款五级分类(5tier)/corporate_loan_by_industry=公司贷款行业分布(loan-industry)/segment_revenue=分部营业收入(seg-rev)/quarterly_operating_cash_flow=分季度经营活动现金流(cf)/fvtpl_investment_by_type=FVTPL 金融投资品种(fvtpl-mix)/fair_value_hierarchy=公允价值层级(fvlevel)/repricing_gap=利率重定价缺口(repricing)/maturity_gap=剩余到期日缺口(maturity)/staff_by_role=员工专业构成(staff-role)/staff_by_education=员工学历构成(staff-edu)/staff_by_age=员工年龄构成(staff-age)/loan_migration_rate=贷款迁徙率(migrate)/loan_trend=公司与零售贷款不良率(loantrend)/retail_loan_by_product=零售贷款分品种(perloan-bal)/deposit_cost=存款成本(depcost)/bonds_payable=已发行债务证券(bondpay)/loan_average_yield=贷款日均余额与收益率(loanmix-bal)/loan_write_off=核销与收回(writeoff)/executive_pay=董事长与行长薪酬(chairman-pay)/consumer_complaint=消费投诉(complaint)/financial_investment_by_measurement=金融投资三分类(invest)/overdue_loan_by_band=逾期贷款分档(overdue-band)/county_urban_share=县域与主城占比(geo)',
    item_name    VARCHAR(128)   NOT NULL DEFAULT '' COMMENT '分项：行业、期限档、科目、人员类别照年报原文,固定分项用中文名(如 定期存款、正常、Q1)；executive_pay 为在任者姓名(空缺照原表写 —)；主题没有分项时为空串',
    item_order   SMALLINT       NULL COMMENT '分项在原表里的顺序(从 1 起,页面按它排类目)；按年份排的序列记该序列在图例里的位置,董事长与行长薪酬为空',
    measure      VARCHAR(48)    NOT NULL COMMENT 'average_rate=平均收益率或成本率/balance=余额/share=占比/revenue=营业收入/net_cash_operating=经营活动现金流量净额/gap=缺口(资产减负债)/assets=资产/liabilities=负债/headcount=人数/normal_migration_rate=正常类迁徙率/special_mention_migration_rate=关注类迁徙率/substandard_migration_rate=次级类迁徙率/doubtful_migration_rate=可疑类迁徙率/corporate_npl_ratio=公司贷款不良率/retail_npl_ratio=零售贷款不良率/npl_ratio=不良率/customer_deposit_cost_rate=客户存款平均成本率/demand_deposit_share=活期存款占比(日均)/average_balance=日均余额/cost_rate=平均成本率/average_yield=平均收益率/write_offs=核销/recoveries=收回已核销/net_write_offs=净核销(核销减收回)/chairman_pay=董事长薪酬(税前)/president_pay=行长薪酬(税前)/complaints=投诉笔数/satisfaction_rate=投诉处理满意度/county_share=县域占比/urban_share=主城占比',
    value        DECIMAL(28, 4) NULL COMMENT '统一单位后的值,单位见 unit：金额为元,比率为 %,人数为人,笔数为笔；原值单位判不出时留空',
    unit         VARCHAR(16)    NULL COMMENT '元/%/人/笔',
    raw_value    DECIMAL(28, 6) NULL COMMENT 'detail_manual 原值(未换算)',
    raw_unit     VARCHAR(16)    NULL COMMENT '原值单位 亿元/百万元/万元/%/人/笔：金额按同一行 annual 的同口径合计对账定量级,对不上留空并记 data_anomaly(reason=unknown_unit)',
    source_file  VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json(渝农商行为手工精编的 company_charts_601077.json)',
    PRIMARY KEY (company_code, fiscal_year, topic, item_name, measure),
    CONSTRAINT fk_bank_report_detail_company FOREIGN KEY (company_code) REFERENCES company (company_code),
    KEY idx_bank_report_detail_topic (topic, fiscal_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行年报正文明细（bank_<code>_detail_manual.json 逐年年报手工摘录）：一个数一行,原表数组里的空格子也写行(value 为空),年份轴与分项顺序靠它还原,整列为 null 的不写；公司/零售贷款余额与不良余额已在 bank_financials,这里不重复；各主题的口径说明与图上标注见 data_note,判定可疑的值见 data_anomaly';
