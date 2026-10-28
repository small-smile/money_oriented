-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS shareholder_concentration
(
    company_code                          CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    as_of_date                            DATE           NOT NULL COMMENT '截止日',
    top1_holder_ratio                     DECIMAL(10, 4) NULL COMMENT '第一大股东持股%',
    top3_holders_ratio                    DECIMAL(10, 4) NULL COMMENT '前三大股东合计持股%',
    top10_holders_ratio                   DECIMAL(10, 4) NULL COMMENT '前十大股东合计持股%',
    top1_holder_ratio_excluding_nominees  DECIMAL(10, 4) NULL COMMENT '剔除名义持有人后第一大股东持股%(香港中央结算(代理人)、HKSCC 等整行剔除后重排再算,名册无代理人时为空,算法见 build_holders_manual.py 的 _conc_row)',
    top3_holders_ratio_excluding_nominees DECIMAL(10, 4) NULL COMMENT '剔除名义持有人后前三大合计持股%',
    top1_holder_name                      VARCHAR(128)   NULL COMMENT '第一大股东名称',
    top1_holder_name_excluding_nominees   VARCHAR(128)   NULL COMMENT '剔除名义持有人后第一大股东名称',
    top1_holder_voting_ratio              DECIMAL(10, 4) NULL COMMENT '第一大股东表决权%(不同投票权架构另行披露,如百度 20-F 里李彦宏的投票权占比),其余公司为空',
    is_reconstructed                      TINYINT(1)     NULL COMMENT 'H 股年报口径序列才有：1=年报只单列内资股前十大,按 SFO 具名 H 股实益持有人合并重构(recon)/0=年报直接披露合并前十大(disc)；A 股接口与手工层算出的为空',
    source                                VARCHAR(255)   NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, as_of_date),
    CONSTRAINT fk_shareholder_concentration_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股权集中度（holders_manual.json 与银行 annual JSON 的 holder_concentration，由逐期前十名股东表算出；纯 H 股行 ar_manual 的 concentrationHist 与渝农商行精编件的重构序列只补接口没有的期）';
