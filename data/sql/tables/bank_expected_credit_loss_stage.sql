-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_expected_credit_loss_stage
(
    company_code     CHAR(10)       NOT NULL,
    fiscal_year      SMALLINT       NOT NULL COMMENT '报告期(年度)',
    statement_type   VARCHAR(32)    NOT NULL DEFAULT 'consolidated' COMMENT 'consolidated=本集团/parent=本行',
    asset_category   VARCHAR(64)    NOT NULL COMMENT 'loans_amortized_cost=以摊余成本计量的贷款/loans_fair_value_through_other_comprehensive_income=以公允价值计量且其变动计入其他综合收益的贷款/loans_total=贷款(年报未按计量方式拆分)/debt_investments=债权投资/other_debt_investments=其他债权投资/due_from_banks=存放同业/placements_with_banks=拆出资金/reverse_repurchase_assets=买入返售/off_balance_sheet_credit_commitments=表外信贷承诺及财务担保',
    measure          VARCHAR(32)    NOT NULL COMMENT 'gross_carrying_amount=账面余额/loss_allowance=损失准备',
    item_code        VARCHAR(64)    NOT NULL COMMENT 'opening_balance=期初余额/stage_transfers=阶段间转移(年报只给一行时)/transfer_to_stage_1、_2、_3=转至阶段一、二、三/net_provision=本期计提(转回)/newly_originated_or_purchased=新增源生或购入/derecognized_or_settled=终止确认或结清/remeasurement=重新计量/model_or_parameter_changes=模型或参数调整/write_offs=核销/transfers_out=转出/write_offs_and_transfers_out=核销及转出(合并披露时)/recoveries=收回已核销/net_write_offs=净核销(年报只给扣除收回后的净额时)/unwinding_of_discount=已减值贷款利息回拨/exchange_rate_and_other=汇率变动及其他/other_movements_1、_2…=上列以外的行(原文见 raw_item_name)/closing_balance=期末余额',
    stage            VARCHAR(64)    NOT NULL COMMENT 'stage_1=阶段一(未来12个月预期损失)/stage_2=阶段二(存续期,未发生信用减值)/stage_3=阶段三(存续期,已发生信用减值,不等于五级分类不良)/purchased_or_originated_credit_impaired=购入或源生已减值(年报单列时)/total=合计',
    item_name        VARCHAR(128)   NOT NULL COMMENT '标准化行项目名称',
    raw_item_name    VARCHAR(255)   NULL COMMENT '年报原始行项目名称',
    parent_item_code VARCHAR(64)    NULL COMMENT '汇总行编码(明细行与汇总行同时披露时填),核对期初+变动=期末只加本列为空的行',
    line_order       SMALLINT       NULL COMMENT '年报原表行序',
    value            DECIMAL(28, 4) NULL COMMENT '金额(元),减少记负,年报「—」记 0,stage=total 为年报合计原值,不反算',
    raw_unit         VARCHAR(32)    NULL COMMENT '年报原始单位(千元/百万元等),入库已换算为元',
    caliber_note     TEXT           NULL COMMENT '口径、重述、合并披露、H股回退和缺失说明',
    source_file      VARCHAR(255)   NULL COMMENT '具体源文件',
    source_section   VARCHAR(255)   NULL COMMENT '来源章节或附注表名',
    source_page      VARCHAR(32)    NULL COMMENT '来源页码',
    is_derived       TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否推算/近似值(图上须标记)',
    missing_reason   VARCHAR(255)   NULL COMMENT '缺失原因',
    PRIMARY KEY (company_code, fiscal_year, statement_type, asset_category, measure, item_code, stage),
    CONSTRAINT fk_bank_expected_credit_loss_stage_company
        FOREIGN KEY (company_code) REFERENCES company (company_code),
    KEY idx_bank_expected_credit_loss_stage_year (fiscal_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行预期信用损失三阶段明细(新金融工具准则/IFRS 9),未披露的项目不写行';
