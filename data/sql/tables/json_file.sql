-- json_file  · 段 E. JSON 文件原文（原 data/ 下的 *.json：tables/ 成品表、raw/ 抓取缓存、extract/ 抽数中间件）
-- 一份文件一行，content 存原文（不用 JSON 列类型：那会重排键序、去掉缩进，页面依赖原文键序）。
-- 读写统一走 backend/jsonstore.py；path 沿用原文件相对 data/ 的路径，大小写敏感。
-- 单份最大约 2.2MB（raw/sec_companyfacts_09888.json），服务端 max_allowed_packet 须大于它。
-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS json_file
(
    path       VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '相对 data/ 的原文件路径，如 tables/company_codes.json',
    content    LONGTEXT     NOT NULL COMMENT 'JSON 原文',
    updated_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后写入时间',
    PRIMARY KEY (path),
    CONSTRAINT chk_json_file_valid CHECK (JSON_VALID(content))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='data/ 下 JSON 文件原文，替代磁盘上的 *.json';
