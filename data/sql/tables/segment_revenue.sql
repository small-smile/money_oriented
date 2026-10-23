-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS segment_revenue
(
    company_code  CHAR(10)       NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year   SMALLINT       NOT NULL COMMENT '报告期(年度)',
    segment_code  VARCHAR(64)    NOT NULL COMMENT '分部编码(extract_telecom_segments.py 的 CANON) voice=语音业务、语音通话及月租费/sms=短彩信业务/wireless_data=无线上网业务/broadband=有线宽带业务/apps=应用及信息服务/other_service=其他、其他服务收入/products=销售产品收入及其他、出售商品及其他收入、销售通信产品、销售通信产品收入/total=合计/service_total=服务收入、小计/mobile=移动通信服务收入/fixed_home=固网及智慧家庭服务收入/dx=产业数字化服务收入/vas=增值服务/broadband_data=宽带及移动数据服务/internet_apps=数据及其他互联网应用收入/interconnect=网间结算收入/circuit=电路及网元服务、电路及网元租赁/legacy_voice=通话及月租费收入/legacy_vas=增值业务收入/legacy_broadband_internet=宽带、数据及互联网收入/legacy_circuit=电路及网元租赁收入/legacy_ict=信息与通信技术服务收入等',
    raw_item_name VARCHAR(128)   NULL COMMENT '年报原文科目名',
    is_subtotal   TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '1=小计或合计行(service_total=主营业务收入,total=营业收入),加总分部时排除；小计+其他业务收入=合计可自检/0=分部',
    revenue       DECIMAL(28, 4) NOT NULL COMMENT '收入(亿元；原文移动为百万元、电信与联通为元,已按合计量级归一)',
    source        VARCHAR(255)   NULL COMMENT '来源文件',
    PRIMARY KEY (company_code, fiscal_year, segment_code),
    CONSTRAINT fk_segment_revenue_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='分部收入（telecom_segment_manual.json，上交所 A 股年报「营业收入和营业成本」附注）：三家的分部科目完全不同，不可跨公司对同名 segment_code 横比；中国联通 2017 年起是真实的口径重分类，2015—2016 的旧科目集用 legacy_* 单独存';
