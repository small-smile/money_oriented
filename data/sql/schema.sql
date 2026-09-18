-- money_oriented 结构化数据 → MySQL 8 schema（InnoDB / utf8mb4）
-- 由 data/tables 下各 JSON 成品表拆解而来。财务用「混合模型」：
--   financial_common 宽表存跨行业公共列（营收/利润/资产/权益/每股等），
--   financial_metric 长表 + metric 维度存行业特有或其余指标（银行 nim/car、险企 solvency/nbv…）。
-- 本轮只收 JSON 派生表；oil/宏观的 CSV/txt 成品表未纳入。
-- 本文件只定义结构，不含数据；加载见 data/extract/load_to_mysql.py。
SET NAMES utf8mb4;

-- ============================================================
-- A. 主体与来源
-- ============================================================
DROP TABLE IF EXISTS company;
CREATE TABLE company (                       -- company_codes.json entities[]
  code         VARCHAR(12)  NOT NULL COMMENT '实体唯一键:有A股用A股码,纯H股用H股码',
  short_name   VARCHAR(64)  NOT NULL,
  full_name    VARCHAR(128) NULL,
  industry     VARCHAR(24)  NOT NULL COMMENT 'bank/insurer/developer/cement/telecom/tech/food',
  a_code       VARCHAR(12)  NULL,
  h_code       VARCHAR(12)  NULL,
  us_code      VARCHAR(12)  NULL,
  tier         VARCHAR(32)  NULL COMMENT '国有大行/股份行/城商行/农商行等',
  same_entity  TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '0=两地非同一法人,不做代码互换',
  note         TEXT         NULL,
  PRIMARY KEY (code),
  KEY idx_company_industry (industry),
  KEY idx_company_a (a_code),
  KEY idx_company_h (h_code),
  KEY idx_company_us (us_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS company_source;
CREATE TABLE company_source (                -- entities[].sources[]（本地出处留痕）
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  company_code VARCHAR(12)  NOT NULL,
  source_line  VARCHAR(512) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_cs_company (company_code),
  CONSTRAINT fk_cs_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS data_gap;
CREATE TABLE data_gap (                      -- company_codes.gaps[] + 各表 history_gaps[]
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  company_code VARCHAR(12)  NULL COMMENT '全局缺口置空',
  item         VARCHAR(255) NOT NULL,
  why          TEXT         NULL,
  PRIMARY KEY (id),
  KEY idx_gap_company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- B. 财务时间序列（混合：公共宽表 + 指标长表）
-- ============================================================
DROP TABLE IF EXISTS metric;
CREATE TABLE metric (                        -- 长表指标字典：加载时按 annual 里出现的键补全
  metric_code  VARCHAR(64)  NOT NULL COMMENT '如 npl_ratio/car/nbv_rate',
  domain       VARCHAR(24)  NOT NULL DEFAULT 'common' COMMENT '所属行业口径',
  label        VARCHAR(128) NULL,
  unit         VARCHAR(32)  NULL,
  note         VARCHAR(255) NULL,
  PRIMARY KEY (metric_code, domain)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS financial_meta;
CREATE TABLE financial_meta (                -- <industry>_<code>_annual.json 顶层元信息(每公司一行)
  company_code VARCHAR(12)  NOT NULL,
  secucode     VARCHAR(16)  NULL,
  currency     VARCHAR(8)   NULL,
  group_name   VARCHAR(64)  NULL,
  source       VARCHAR(255) NULL,
  unit_note    VARCHAR(255) NULL,
  caliber_note TEXT         NULL,
  fetched_at   DATETIME     NULL,
  PRIMARY KEY (company_code),
  CONSTRAINT fk_fm_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS financial_common;
CREATE TABLE financial_common (              -- *_annual.json annual 里的跨行业公共列（每公司每年一行）
  company_code    VARCHAR(12)   NOT NULL,
  fiscal_year     SMALLINT      NOT NULL,
  operate_income  DECIMAL(28,4) NULL COMMENT '营业收入',
  operate_profit  DECIMAL(28,4) NULL,
  total_profit    DECIMAL(28,4) NULL,
  netprofit       DECIMAL(28,4) NULL COMMENT '净利润',
  parent_netprofit DECIMAL(28,4) NULL COMMENT '归母净利润',
  total_assets    DECIMAL(28,4) NULL,
  total_liabilities DECIMAL(28,4) NULL,
  total_equity    DECIMAL(28,4) NULL,
  parent_equity   DECIMAL(28,4) NULL,
  share_capital   DECIMAL(28,4) NULL COMMENT '总股本',
  eps             DECIMAL(16,6) NULL,
  bps             DECIMAL(16,6) NULL,
  roe_weighted    DECIMAL(12,4) NULL COMMENT '加权ROE%',
  net_margin      DECIMAL(12,4) NULL COMMENT '净利率%',
  op_cf_per_share DECIMAL(16,6) NULL,
  PRIMARY KEY (company_code, fiscal_year),
  CONSTRAINT fk_fc_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS financial_metric;
CREATE TABLE financial_metric (              -- 公共列之外的行业特有/其余指标（长表，只存非空值）
  company_code VARCHAR(12)   NOT NULL,
  fiscal_year  SMALLINT      NOT NULL,
  metric_code  VARCHAR(64)   NOT NULL,
  value        DECIMAL(28,6) NOT NULL,
  PRIMARY KEY (company_code, fiscal_year, metric_code),
  KEY idx_fm_metric (metric_code, fiscal_year),
  CONSTRAINT fk_fmet_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS dividend_per10;
CREATE TABLE dividend_per10 (                -- *_annual.json dividend_per10{年:值}
  company_code VARCHAR(12)   NOT NULL,
  fiscal_year  SMALLINT      NOT NULL,
  per10        DECIMAL(16,6) NOT NULL COMMENT '每10股派息',
  unit         VARCHAR(8)    NOT NULL DEFAULT '元' COMMENT '中国移动按港元',
  PRIMARY KEY (company_code, fiscal_year),
  CONSTRAINT fk_dp_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS segment_annual;
CREATE TABLE segment_annual (                -- telecom segments / bank seg-rev 等分部数据
  company_code VARCHAR(12)   NOT NULL,
  fiscal_year  SMALLINT      NOT NULL,
  segment      VARCHAR(64)   NOT NULL,
  metric_code  VARCHAR(64)   NOT NULL DEFAULT 'revenue',
  value        DECIMAL(28,6) NOT NULL,
  PRIMARY KEY (company_code, fiscal_year, segment, metric_code),
  CONSTRAINT fk_sa_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- C. 股权结构
-- ============================================================
DROP TABLE IF EXISTS shareholder_top10;
CREATE TABLE shareholder_top10 (             -- holders[] / holders_manual.json / *_shareholder.json
  id           BIGINT        NOT NULL AUTO_INCREMENT,
  company_code VARCHAR(12)   NOT NULL,
  as_of_date   DATE          NULL,
  `rank`       SMALLINT      NOT NULL,
  holder_name  VARCHAR(128)  NOT NULL,
  hold_num     BIGINT        NULL COMMENT '持股数',
  ratio        DECIMAL(10,4) NULL COMMENT '持股占比%',
  chg          VARCHAR(32)   NULL,
  state        VARCHAR(32)   NULL COMMENT '国有/外资/其他',
  shares_type  VARCHAR(16)   NULL COMMENT 'A/H/无限售流通等',
  total_shares BIGINT        NULL,
  pledged      BIGINT        NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_top10 (company_code, as_of_date, shares_type, `rank`),
  CONSTRAINT fk_sh_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS holder_faction;
CREATE TABLE holder_faction (                -- factions[]（一致行动人/派系）
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  company_code VARCHAR(12)  NOT NULL,
  title        VARCHAR(64)  NOT NULL,
  color        VARCHAR(16)  NULL,
  basis        VARCHAR(255) NULL COMMENT '归派系依据',
  PRIMARY KEY (id),
  KEY idx_hf_company (company_code),
  CONSTRAINT fk_hf_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS holder_faction_member;
CREATE TABLE holder_faction_member (         -- factions[].names[] + faction_aliases
  faction_id   BIGINT       NOT NULL,
  holder_name  VARCHAR(128) NOT NULL,
  alias_of     VARCHAR(128) NULL COMMENT '别名归并到的规范名',
  PRIMARY KEY (faction_id, holder_name),
  CONSTRAINT fk_hfm_faction FOREIGN KEY (faction_id) REFERENCES holder_faction(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS holder_count;
CREATE TABLE holder_count (                  -- holder_num[[date,count,...]]（逐期股东户数）
  company_code VARCHAR(12)   NOT NULL,
  as_of_date   DATE          NOT NULL,
  holder_num   BIGINT        NULL,
  avg_hold     DECIMAL(20,4) NULL,
  PRIMARY KEY (company_code, as_of_date),
  CONSTRAINT fk_hc_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS holder_concentration;
CREATE TABLE holder_concentration (          -- holder_concentration[{date,top1,top3,top10,...}]
  company_code VARCHAR(12)   NOT NULL,
  as_of_date   DATE          NOT NULL,
  top1         DECIMAL(10,4) NULL,
  top3         DECIMAL(10,4) NULL,
  top10        DECIMAL(10,4) NULL,
  top1_ex      DECIMAL(10,4) NULL COMMENT '剔除控股/国有后',
  top3_ex      DECIMAL(10,4) NULL,
  top1_name    VARCHAR(128)  NULL,
  top1_ex_name VARCHAR(128)  NULL,
  PRIMARY KEY (company_code, as_of_date),
  CONSTRAINT fk_hcc_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS share_capital_history;
CREATE TABLE share_capital_history (         -- share_capital[[year,shares,reason]]
  company_code  VARCHAR(12)  NOT NULL,
  fiscal_year   SMALLINT     NOT NULL,
  shares        BIGINT       NULL COMMENT '期末总股本',
  change_reason VARCHAR(255) NULL,
  PRIMARY KEY (company_code, fiscal_year),
  CONSTRAINT fk_sch_company FOREIGN KEY (company_code) REFERENCES company(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- D. 宏观（JSON 派生）
-- ============================================================
DROP TABLE IF EXISTS tsf_pboc;
CREATE TABLE tsf_pboc (                       -- tsf_pboc_stock.json / tsf_pboc_flow.json
  kind         ENUM('stock','flow') NOT NULL,
  period_month CHAR(7)       NOT NULL COMMENT 'YYYY-MM',
  series_key   VARCHAR(32)   NOT NULL COMMENT 'total/yoy/loan/bond 等分项',
  value        DECIMAL(20,4) NULL,
  PRIMARY KEY (kind, period_month, series_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
