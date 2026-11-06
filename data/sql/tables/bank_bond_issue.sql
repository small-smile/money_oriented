-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_bond_issue
(
    company_code CHAR(10)      NOT NULL COMMENT '公司code(→company.company_code)',
    bond_order   SMALLINT      NOT NULL COMMENT 'detail_manual 里 bondpay.bonds 的顺序(从 1 起)；同名债券多期按此区分',
    bond_name    VARCHAR(128)  NOT NULL COMMENT '债券名称(年报原文)',
    issue_date   VARCHAR(16)   NULL COMMENT '发行日(原文 YYYY-MM-DD 或 YYYY-MM)',
    tenor        VARCHAR(64)   NULL COMMENT '期限(原文,如 10年(第5年可赎回))',
    coupon_rate  DECIMAL(10, 4) NULL COMMENT '票面利率%',
    issue_amount DECIMAL(28, 4) NULL COMMENT '发行规模(亿元,原值)',
    maturity     VARCHAR(16)   NULL COMMENT '到期(原文 YYYY-MM)',
    status       VARCHAR(32)   NULL COMMENT '状态(原文,如 存续/已赎回/已到期)',
    source_file  VARCHAR(255)  NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, bond_order),
    CONSTRAINT fk_bank_bond_issue_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行已发行债券清单（detail_manual 的 bondpay.bonds）：含永续债(不计入应付债券余额),余额与成本率在 bank_debt_securities_issued';
