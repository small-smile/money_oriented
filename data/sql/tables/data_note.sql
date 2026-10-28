-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS data_note
(
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    company_code CHAR(10)     NULL COMMENT '关联公司code；整份文件通用的说明留空,不加外键',
    source_file  VARCHAR(255) NOT NULL COMMENT '来源文件,如 bank_600036_detail_manual.json',
    topic        VARCHAR(64)  NOT NULL COMMENT '说明所属的键(原文件里的键名,如 loan-industry、unit_rule、units)',
    note         TEXT         NOT NULL COMMENT '说明原文；嵌套的对象逐项写成「键：值」,多段换行连接',
    PRIMARY KEY (id),
    KEY idx_data_note_company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='手工层 JSON 里的口径、单位、出处说明原文（detail_manual 的 _notes、经营口径表与百度分部表的 _meta、股东手工表的说明等）：结构化表的数怎么来的看这里';
