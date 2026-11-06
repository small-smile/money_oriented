-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS bank_consumer_complaint
(
    company_code              CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year               SMALLINT       NOT NULL COMMENT '报告期(年度)',
    complaints                INT            NULL COMMENT '处理消费投诉(笔)',
    satisfaction_rate         DECIMAL(12, 4) NULL COMMENT '消费投诉处理客户满意度%',
    columns_missing_in_source VARCHAR(1024)  NULL COMMENT '这一年原表没有的指标格(逗号分隔)：这些列为空是原表没这一格,其余列为空是原表列了但未披露',
    source_file               VARCHAR(255)   NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    PRIMARY KEY (company_code, fiscal_year),
    CONSTRAINT fk_bank_consumer_complaint_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='银行消费投诉（detail_manual 的 complaint,年报「消费者权益保护」）：原表列了这一年但未披露的也写行';
