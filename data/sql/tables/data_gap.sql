-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS data_gap
(
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    company_code CHAR(10)     NULL COMMENT '关联公司code；跨公司的缺口留空,不加外键',
    description  TEXT         NOT NULL COMMENT '缺口/冲突内容(原文)',
    reason       TEXT         NULL COMMENT '原因与已查范围(原文；history_gaps 只有一段话,并在 description 里)',
    source_file  VARCHAR(255) NULL COMMENT '来源文件,如 company_codes.json',
    PRIMARY KEY (id),
    KEY idx_data_gap_company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='已知数据缺口与出处冲突（company_codes.json gaps、holders_manual.json history_gaps、annual JSON 的 _meta.gaps、渝农商行 H 股户数未披露的年份）：人工核查时记下的，原文照存；载入时机器发现的异常见 data_anomaly';
