-- data_anomaly  · 段 D. 解析异常记录（数据质量）
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS data_anomaly
( -- 载入时值超期望区间/非数值等异常的留痕，不入正表
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    company_code VARCHAR(12) NULL COMMENT '关联公司code；不加外键，异常源本身可能是非法code',
    source_file  VARCHAR(255) NULL COMMENT '来源文件，如 data/tables/bank_601916_annual.json',
    target_table VARCHAR(64) NULL COMMENT '本应写入的目标表名',
    field_name   VARCHAR(64) NULL COMMENT '字段/指标名，如 operating_revenue、metric_code',
    period VARCHAR (16) NULL COMMENT '年份或报告期，如 2024 / 2024-06-30',
    raw_value    VARCHAR(255) NULL COMMENT '清洗前的原始值（文本原样）',
    reason       VARCHAR(255) NOT NULL COMMENT '异常类型: not_in ',
    detected_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录写入时间',
    source       VARCHAR(255) NULL COMMENT '数据来源',
    PRIMARY KEY (id),
    KEY          idx_da_company (company_code),
    KEY          idx_da_target (target_table, field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 comment='解析/载入数据时的越界与异常留痕，供数据质量排查';
