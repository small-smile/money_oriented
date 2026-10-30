-- 约定：本表由 load_to_mysql.py --init 一次性建表（init 只跑一次）；用 CREATE ... IF NOT EXISTS，勿加回 DROP TABLE（会清空真实库数据）。
CREATE TABLE IF NOT EXISTS share_capital_structure
(
    company_code CHAR(10)     NOT NULL COMMENT '公司code(→company.company_code)',
    fiscal_year  SMALLINT     NOT NULL COMMENT '报告期(年度),取年末(12-31)时点',
    share_class  VARCHAR(32)  NOT NULL COMMENT '股份类别：a_share=A股(人民币普通股)/h_share=H股或港股(年报「境外上市的外资股」,含中国移动这类境外注册公司的香港股份)/domestic_share=内资股(境内注册、未在境内上市的普通股,纯H股行及渝农商行2019年A股上市前)/class_a_ordinary_share=A类普通股(百度,每股1票)/class_b_ordinary_share=B类普通股(百度,每股10票)/domestic_preference_share=境内优先股(每股面值100元)/offshore_preference_share=境外优先股(美元等外币计价)',
    shares       BIGINT       NULL COMMENT '年末股数(股)：普通股取年报「股份变动情况表」期末数,限售股按持股性质另列的(国有法人持股、其他内资持股等)并入所属类别,优先股取「优先股相关情况」里期末存续各期的发行数量之和,年内赎回的不计',
    source       VARCHAR(255) NULL COMMENT '出处:年报文件、章节、页码',
    PRIMARY KEY (company_code, fiscal_year, share_class),
    CONSTRAINT fk_share_capital_structure_company FOREIGN KEY (company_code) REFERENCES company (company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT ='股本结构（年末各类股份股数,含优先股,年报「股份变动情况表」与「优先股相关情况」逐年抄录,A+H 两地年报都有时取 A 股年报）：年报没有的类别不写行。优先股不计入普通股股份总数,普通股各行(share_class 不以 _preference_share 结尾)之和应等于 share_capital_year_end.total_shares';
