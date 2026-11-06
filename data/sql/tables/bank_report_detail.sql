-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_report_detail
(
    company_code CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year  SMALLINT       NOT NULL COMMENT '报告期(年度)；只给一期的主题(员工构成)记年报当年',
    period_label VARCHAR(16)    NULL COMMENT '原表期次写法与年份不同时照存(如 2024 年末),其余为空',
    topic        VARCHAR(48)    NOT NULL COMMENT '主题(与 detail_manual 键的对应见表 COMMENT) net_interest_rate_item=生息资产与付息负债的平均利率及利息收支/corporate_loan_by_industry=公司贷款行业分布/corporate_loan_by_enterprise_size=境内公司贷款按国标企业规模/segment_revenue=分部营业收入(财务报表附注的经营分部)/business_line_result=业务条线经营业绩(业务回顾口径,招行为本公司,与 segment_revenue 不拼接)/fvtpl_investment_by_type=FVTPL 金融投资品种/repricing_gap=利率重定价缺口/maturity_gap=剩余到期日缺口/staff_by_role=员工专业构成/staff_by_education=员工学历构成/staff_by_age=员工年龄构成/staff_by_gender=员工性别构成/staff_by_region=员工区域分布/retail_wealth_management=零售财富管理(分项为产品类别)/overdue_loan_by_band=逾期贷款分档',
    item_name    VARCHAR(128)   NOT NULL DEFAULT '' COMMENT '分项：行业、期限档、科目、人员类别照年报原文；主题没有分项时为空串',
    item_order   SMALLINT       NULL COMMENT '分项在原表里的顺序(从 1 起,页面按它排类目)；按年份排的序列记该序列在图例里的位置',
    measure      VARCHAR(48)    NOT NULL COMMENT 'average_rate=平均收益率或成本率/balance=余额/share=占比/revenue=营业收入/gap=缺口(资产减负债)/assets=资产/liabilities=负债/headcount=人数/interest_income=利息收入/interest_expense=利息支出/profit_before_tax=税前利润/net_interest_income=净利息收入/non_interest_income=非利息净收入/fee_income=手续费及佣金收入/sales=代理销售额(保险为保费)/research_and_development_headcount=研发人员人数',
    value        DECIMAL(28, 4) NULL COMMENT '统一单位后的值,单位见 unit：金额为元,比率为 %,人数为人；原值单位判不出时留空',
    unit         VARCHAR(16)    NULL COMMENT '元/%/人',
    raw_value    DECIMAL(28, 6) NULL COMMENT 'detail_manual 原值(未换算)',
    raw_unit     VARCHAR(16)    NULL COMMENT '原值单位 亿元/百万元/万元/%/人：金额按同一行 annual 的同口径合计对账定量级,对不上留空并记 data_anomaly(reason=unknown_unit)',
    source_file  VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year, topic, item_name, measure),
    CONSTRAINT fk_bank_report_detail_company FOREIGN KEY (company_code) REFERENCES company (company_code),
    KEY idx_bank_report_detail_topic (topic, fiscal_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行年报正文明细中分项随银行变的主题（bank_<code>_detail_manual.json 逐年年报手工摘录）：一个数一行,原表数组里的空格子也写行(value 为空),年份轴与分项顺序靠它还原,整列为 null 的不写；指标固定的主题各有宽表(depterm=bank_deposit_structure/5tier=bank_loan_five_category/cf=bank_quarterly_operating_cash_flow/geo=bank_county_urban_share/migrate=bank_loan_migration_rate/loantrend=bank_loan_quality_by_segment/perloan-bal=bank_retail_loan_by_product/depcost=bank_deposit_cost/bondpay=bank_debt_securities_issued/loanmix-bal=bank_loan_average_yield/writeoff=bank_loan_write_off/complaint=bank_consumer_complaint/invest=bank_financial_investment_by_measurement/fvlevel=bank_fair_value_hierarchy/chairman-pay=bank_executive_pay),不在本表；各主题的口径说明与图上标注见 data_note,其 topic 记 detail_manual 的键(nim=net_interest_rate_item/loan-industry=corporate_loan_by_industry/seg-rev=segment_revenue/fvtpl-mix=fvtpl_investment_by_type/repricing=repricing_gap/maturity=maturity_gap/staff-role=staff_by_role/staff-edu=staff_by_education/staff-age=staff_by_age/overdue-band=overdue_loan_by_band)；判定可疑的值见 data_anomaly';
