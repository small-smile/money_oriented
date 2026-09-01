"""生成 data/tables/holders_manual.json —— 股权结构页的一致行动人（分组）与手工股东块。

两类内容：
① 只补分组（telecom）：股东名册本身来自 <板块>_<code>_annual.json 的接口快照，
   这里只给「哪些股东归一组、依据是什么」；names 必须与接口名册里的名字逐字一致。
② 连股东名册一起给（food 巴比、tech 百度）：这两家没有 <板块>_<code>_annual.json，
   名册直接抄年报／20-F 原文（本地存档），比例按 股数 ÷ 总股本 重算到两位小数。

分组依据分两种，写在每组的 basis 里，页面会原样印出来，不让读者把「同类归并」
误当成年报披露的一致行动人：
  - 「年报披露」：年报/20-F 明确写出的关联关系、一致行动人、控股股东、WVR 受益人；
  - 「同类归并」：本项目按股东性质归的堆（ETF、保险资金、地方国资…），年报未认定其一致行动。
运营商三家的年报都写明「未知上述股东之间存在关联关系或一致行动」，所以除控股股东外
全部是同类归并 —— 这一点写进 caliber_note。

用法：venv/bin/python data/extract/build_holders_manual.py
"""
import json
import os
import re

TABLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tables")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
OUT = os.path.join(TABLES, "holders_manual.json")

# 名义持有人：只是代人登记的通道，集中度序列里另给一条「剔代理人」的口径
NOMINEE_RE = re.compile(r"香港中央结算|香港中央結算|代理人|HKSCC|nominee", re.I)
# 「本年度股本未变动」的各种写法，命中就把股本图那一年画成灰柱
NOCHANGE_RE = re.compile(r"未变动|未发生变化|未发生变动|不适用")

# ── 运营商：只补分组 ──────────────────────────────────────────────────────────
CM_SRC = ("中国移动《2025 年年度报告》（A 股 600941，上交所）第六节「股东和实际控制人情况」："
          "中国移动香港（BVI）有限公司为控股股东中国移动（香港）集团有限公司的全资子公司；"
          "「上述股东关联关系或一致行动的说明」原文为「公司未知上述股东是否存在关联关系或一致行动关系」，"
          "故除控股股东外均为本项目按股东性质做的同类归并。本地存档 data/raw/annual_600941_2025.pdf/.txt。")
CT_SRC = ("中国电信控股股东为中国电信集团有限公司（A 股 601728 招股说明书／各期年报「控股股东情况」）；"
          "广东省广晟控股集团有限公司与其「可交换公司债券质押专户」为同一法人的两个证券账户，按同一主体并组。"
          "其余分组为按股东性质的同类归并。注：601728 的 A 股年报未在本地存档，"
          "未逐字核对该年度「关联关系或一致行动的说明」，分组依据仅为股东名称本身与公开的控股关系。")
CU_SRC = ("中国联通《2025 年年度报告》（A 股 600050，上交所）第六节：「1.中国联合网络通信集团有限公司为本公司控股股东。"
          "2./3./4. 本公司未知前十名股东……之间是否存在《上海证券交易所股票上市规则》规定的关联关系"
          "或构成《上市公司收购管理办法》规定的一致行动人。」腾讯／阿里／百度三家为 2017 年混改引入的"
          "战略投资者（同期定增），按引入批次归为一组，年报未认定其一致行动。"
          "本地存档 data/raw/annual_600050_2025.pdf/.txt。")

TELECOM_NOTE = ("运营商三家的年报都写明「未知上述股东之间存在关联关系或一致行动」，"
                "因此外圈除**控股股东**一组外，其余都是本项目按股东性质做的**同类归并**，"
                "不是年报披露的一致行动人。")

# 逐年抽取件里记下来的披露缺口，页面「口径与接口限制」原样列出（每条都能回到年报原文）
HIST_GAPS = {
    "telecom:600941": [
        "**股息以港元宣派**：年报明确 A 股人民币金额要按股东周年大会前一周汇率折算，"
        "所以本页<b>没有分红图</b> —— 港元原值（2021–2025 全年每股 4.06 / 4.41 / 4.83 / 5.09 / 5.27 港元）"
        "在抽取件里，本项目不做汇率换算。",
        "**2021 年的前十名股东表只有 2 行**：当年 A 股尚未上市，香港《个人资料（私隐）条例》下"
        "H 股持股 5% 以下的股东不予披露，年报原表就是 2 行 —— 因此那一年的前三／前十名合计无从计算，图上断点。",
        "**2021 年的「股东总数」6,634 户是 H 股登记股东**（A 股 2022-01-05 才上市，当年 A 股户数为 0）；"
        "2022 年起才是 A+H 合计，2025 年末 162,272 户里 A 股 154,795 户。",
        "名册里「香港中央结算（代理人）有限公司」与「港股股东 A／B」的股东性质、报告期内增减、"
        "质押数量在年报里写的是「未知」或「-」，一律记为未披露（不是 0）。",
    ],
    "telecom:601728": [
        "**2021 年报没有「每 10 股派息数」那张表**，只有每股 0.170 元，本页那一年的分红值由"
        "每股 ×10 折算（纯单位换算，不涉及推算）。",
        "五年的股东总数都只有「普通股股东总数」一个口径，**未分 A 股／H 股登记户数**。",
        "2025 年报里「浙江省财务开发有限责任公司」已改称「浙江省财开集团有限公司」，按当年原文抄录，未回填统一。",
    ],
    "telecom:600050": [
        "**600050 只发 A 股**（H 股在联通红筹 0762.HK 名下），所以股东户数没有 A／H 拆分；"
        "2015–2020 年报另披露过「未合并融资融券信用账户」口径的户数，本页取的是合并口径。",
        "2016 年可供分配利润为负，**当年不分红**，图上记 0（原文依据在抽取件的 dividend.note 里）。",
        "2017 年总股本从 211.97 亿股跳到 302.34 亿股，是**混改定增**；2025 年降到 312.64 亿股为回购注销，"
        "两处台阶在图上用有色柱标出。",
    ],
    "food:605338": [
        "年报只披露「每 10 股派息数」，**未披露每股金额**，本页不做除算。",
        "2023 年总股本 2.5011 亿股是限制性股票授予导致的临时增加，2024 年三次回购注销后回到 2.48 亿股，"
        "2025 年 4 月再注销集中竞价回购的 843.33 万股 → 2.3957 亿股。",
        "2025 年报的前十名股东表<b>没有「合计」行</b>：本页 69.91% 是逐行比例相加；"
        "此前公司概览页写的 70.72% 与原文逐行相加不符，已改正。",
    ],
}

MANUAL = {
    "telecom:600941": {
        "factions_source": CM_SRC,
        "caliber_note": TELECOM_NOTE,
        "factions": [
            {"title": "控股股东（中国移动集团）", "color": "#c0392b", "basis": "年报披露",
             "names": ["中国移动香港(BVI)有限公司"]},
            {"title": "央企产业资本（A 股 IPO 战略投资者）", "color": "#e67e22", "basis": "同类归并",
             "names": ["中国石油天然气集团有限公司", "国家能源集团资本控股有限公司",
                       "国新投资有限公司", "国网英大国际控股集团有限公司"]},
            {"title": "保险资金", "color": "#2980b9", "basis": "同类归并",
             "names": ["太平人寿保险有限公司-传统-普通保险产品-022L-CT001沪"]},
            {"title": "ETF", "color": "#16a085", "basis": "同类归并",
             "names": ["中国工商银行股份有限公司-华泰柏瑞沪深300交易型开放式指数证券投资基金"]},
            {"title": "未具名 H 股股东", "color": "#8e44ad", "basis": "披露缺口",
             "names": ["港股股东A", "港股股东B"]},
        ],
    },
    "telecom:601728": {
        "factions_source": CT_SRC,
        "caliber_note": TELECOM_NOTE,
        "factions": [
            {"title": "控股股东（中国电信集团）", "color": "#c0392b", "basis": "年报披露",
             "names": ["中国电信集团有限公司"]},
            {"title": "广东广晟系（同一法人两账户）", "color": "#e67e22", "basis": "同一主体",
             "names": ["广东省广晟控股集团有限公司",
                       "广东省广晟控股集团有限公司-2024年面向专业投资者非公开发行可交换公司债券(第一期)质押专户"]},
            {"title": "地方国资战略投资者", "color": "#6c3483", "basis": "同类归并",
             "names": ["浙江省财开集团有限公司", "江苏省国信集团有限公司",
                       "福建省投资开发集团有限责任公司"]},
            {"title": "保险资金及保险系长期投资试点基金", "color": "#2980b9", "basis": "同类归并",
             "names": ["中国人寿保险股份有限公司-传统-普通保险产品-005L-CT001沪",
                       "国丰兴华(北京)私募基金管理有限公司-鸿鹄志远(上海)私募投资基金有限公司"]},
            {"title": "央企产业资本", "color": "#27ae60", "basis": "同类归并",
             "names": ["国网英大国际控股集团有限公司"]},
        ],
    },
    "telecom:600050": {
        "factions_source": CU_SRC,
        "caliber_note": TELECOM_NOTE,
        "factions": [
            {"title": "控股股东（联通集团）", "color": "#c0392b", "basis": "年报披露",
             "names": ["中国联合网络通信集团有限公司"]},
            {"title": "混改战略投资者（互联网平台）", "color": "#e67e22", "basis": "同类归并",
             "names": ["深圳市腾讯信达有限合伙企业(有限合伙)", "杭州阿里创业投资有限公司",
                       "嘉兴小度投资管理有限公司-宁波梅山保税港区百度鹏寰投资合伙企业(有限合伙)"]},
            {"title": "国资运营平台", "color": "#6c3483", "basis": "同类归并",
             "names": ["中国国有企业结构调整基金股份有限公司", "国新产业资本管理有限公司"]},
            {"title": "保险资金", "color": "#2980b9", "basis": "同类归并",
             "names": ["中国人寿保险股份有限公司-传统-普通保险产品-005L-CT001沪"]},
            {"title": "ETF", "color": "#16a085", "basis": "同类归并",
             "names": ["中国工商银行-上证50交易型开放式指数证券投资基金",
                       "中国工商银行股份有限公司-华泰柏瑞沪深300交易型开放式指数证券投资基金"]},
        ],
    },
}

# ── 食品（巴比食品 605338）：名册整份抄年报 ────────────────────────────────────
# 总股本 239,566,662 股 = 期初 248,000,000 股 − 回购注销 8,433,338 股（年报「股份变动情况表」）
BABI_TOTAL = 239566662
BABI_SRC = ("中饮巴比食品股份有限公司《2025 年年度报告》（A 股 605338，上交所）第六节"
            "「股份变动及股东情况」——(二) 截至报告期末前十名股东持股情况表（不含通过转融通出借股份）。"
            "总股本 239,566,662 股取自同一份年报的股份变动情况表（期初 248,000,000 股 − 回购注销 8,433,338 股），"
            "与年报「截至 2026 年 4 月 8 日公司总股本 239,566,662 股」一致。"
            "本地存档 data/raw/annual_605338_2025.pdf/.txt。")
# (股东名称, 期末持股数, 报告期内增减, 股东性质)；增减 0 在年报里印的是 0，页面显示「不变」
BABI_ROWS = [
    ("刘会平", 101193300, 0, "境内自然人"),
    ("丁仕梅", 19027800, 0, "境内自然人"),
    ("天津会平投资管理合伙企业（有限合伙）", 13206242, -180900, "其他"),
    ("天津中饮投资管理合伙企业（有限合伙）", 9231029, -731200, "其他"),
    ("天津巴比投资管理合伙企业（有限合伙）", 8160729, -1102800, "其他"),
    ("潘和杰", 5550000, -565800, "境内自然人"),
    ("丁仕霞", 4555000, 0, "境内自然人"),
    ("基本养老保险基金一零零一组合", 3000000, -3084900, "其他"),
    ("中国平安保险（集团）股份有限公司企业年金计划－招商银行股份有限公司", 1986806, 1986806, "其他"),
    ("招商银行股份有限公司－易方达裕鑫债券型证券投资基金", 1574400, 1574400, "其他"),
]
BABI_FAC_SRC = ("同一份年报「上述股东关联关系或一致行动的说明」原文：「刘会平和丁仕梅为公司实际控制人。"
                "刘会平和丁仕梅系夫妻关系、丁仕霞和丁仕梅系姐妹关系。刘会平系天津巴比、天津会平、天津中饮"
                "的有限合伙人。除此之外公司未知上述股东之间存在任何关联关系或属于一致行动人。」"
                "第一组按这段原文归并；机构产品那组是本项目按股东性质做的同类归并。")

MANUAL["food:605338"] = {
    "name": "巴比食品",
    "secucode": "605338.SH",
    "tag": "中式面点连锁",
    "source": BABI_SRC,
    "factions_source": BABI_FAC_SRC,
    "caliber_note": ("本页股东数据不来自任何第三方接口，**整份抄自 2025 年年报的前十名股东持股情况表**；"
                     "比例按 期末持股数 ÷ 总股本 239,566,662 股重算到两位小数，与年报印的一位小数一致。"),
    "residual_label": "其他股东（前十名之外）",
    "holders_end_date": "2025-12-31",
    "holder_num": [["2025-12-31", 12120, None, None]],
    "holders": [
        {"rank": i + 1, "name": n, "hold_num": v, "ratio": round(v / BABI_TOTAL * 100, 2),
         "change": ("不变" if c == 0 else str(c)), "state": ("不变" if c == 0 else ""),
         "shares_type": t, "total_shares": BABI_TOTAL}
        for i, (n, v, c, t) in enumerate(BABI_ROWS)
    ],
    "factions": [
        {"title": "刘会平·丁仕梅实控人及关联方", "color": "#c0392b", "basis": "年报披露",
         "names": ["刘会平", "丁仕梅", "天津会平投资管理合伙企业（有限合伙）",
                   "天津中饮投资管理合伙企业（有限合伙）", "天津巴比投资管理合伙企业（有限合伙）",
                   "丁仕霞"]},
        {"title": "机构产品（养老金／年金／债基）", "color": "#2980b9", "basis": "同类归并",
         "names": ["基本养老保险基金一零零一组合",
                   "中国平安保险（集团）股份有限公司企业年金计划－招商银行股份有限公司",
                   "招商银行股份有限公司－易方达裕鑫债券型证券投资基金"]},
    ],
}

# ── 科技（百度 09888）：名册整份来自 20-F 的 beneficial ownership 口径 ─────────
# 口径与 A 股「前十名股东」完全不同：算的是实益拥有权（含 60 日内可行使期权、
# 含通过不可撤销投票代理取得的股份），披露门槛是 5%，不是名册前十名。
BIDU_TOTAL = 2722021272
BIDU_SRC = ("百度集团 Form 20-F for fiscal year 2025（SEC，2026-03-17 报送）Item 6.E. Share Ownership "
            "的 beneficial ownership 表与 Item 6.E. 加权投票权（WVR）受益人表，口径日 2026-01-31，"
            "分母为已发行流通普通股 2,722,021,272 股（A 类 2,198,000,952 + B 类 524,020,320）。"
            "李彦宏那 507,314,224 股按脚注 (1) 的七项组成拆成三行（BVI 公司／员工投票代理／本人直接持有），"
            "拆分后合计与表列数一致。本地存档 data/raw/20f_09888_2025.htm/.txt，"
            "结构化底稿 data/tables/tech_09888_holders_manual.json。")
BIDU_ROWS = [
    ("Handsome Reward Limited（李彦宏全资 BVI 公司）", 449219376,
     "B 类 439,200,000 + A 类 10,019,376（含 ESOP 账户 ADS、60 日内期权与限制性股份）"),
    ("员工不可撤销投票代理股份（表决权归李彦宏）", 51550880,
     "A 类·ADS 形式 · 李彦宏只有表决权、无经济利益"),
    ("李彦宏本人直接及 ESOP 经纪账户持有", 6543968, "A 类 3,013,200 + ADS 形式 3,530,768"),
    ("贝莱德（BlackRock, Inc.）", 128640168,
     "A 类 · 数据日 2023-12-31 的 13G/A，三份 20-F 沿用未更新"),
    ("马东敏（Melissa Ma，李彦宏配偶）", 88185992,
     "A 类 3,465,992 + B 类 84,720,000 · 仅见于 WVR 受益人表"),
    ("Integrity Partners V, LLC", 100320, "B 类 · 2005 年美股 IPO 前早期投资人关联实体"),
]

MANUAL["tech:09888"] = {
    "name": "百度集团",
    "secucode": "09888.HK",
    "tag": "WVR 不同投票权架构",
    "source": BIDU_SRC,
    "factions_source": ("20-F 脚注 (1) 把 Handsome Reward Limited、员工投票代理股份与本人直接持股"
                        "一并计入李彦宏的实益拥有权，WVR 受益人表同样把这三项列在李彦宏名下，"
                        "故合为一组；马东敏虽为李彦宏配偶且同为 WVR 受益人，但 20-F 明确写李彦宏"
                        "「disclaims beneficial ownership」其全部股份，故单独一组、不并入李彦宏系。"),
    "caliber_note": ("**这一页的百度是 20-F 的 beneficial ownership 口径，不是 A 股「前十名股东」口径**："
                     "只披露董事高管与已知持股 5% 以上者，含 60 日内可行使的期权与通过不可撤销投票代理"
                     "取得的股份，因此「持股」里混着表决权而非全部是经济权益；绝大多数机构经 ADS 与 HKSCC"
                     "间接持有、不进在册名册，20-F 里除贝莱德外无任何机构股东。"
                     "贝莱德那行的股数数据日是 2023-12-31，三份 20-F 沿用未更新，只换了分母。"),
    "residual_label": "其他股东（20-F 未列示，主要为 ADS／港股通公众持股）",
    "holders_caliber": "20-F beneficial ownership 口径（FY2025 Item 6.E，口径日 2026-01-31）",
    "holders_end_date": "2026-01-31",
    "holders": [
        {"rank": i + 1, "name": n, "hold_num": v, "ratio": round(v / BIDU_TOTAL * 100, 2),
         "change": None, "state": "", "shares_type": t, "total_shares": BIDU_TOTAL}
        for i, (n, v, t) in enumerate(BIDU_ROWS)
    ],
    "factions": [
        {"title": "李彦宏系（WVR 受益人）", "color": "#c0392b", "basis": "20-F 披露",
         "names": ["Handsome Reward Limited（李彦宏全资 BVI 公司）",
                   "员工不可撤销投票代理股份（表决权归李彦宏）",
                   "李彦宏本人直接及 ESOP 经纪账户持有"]},
    ],
}

# ── 历年序列：照 bank/shareholder.html 那套模板补的三层 ─────────────────────────
# 数据来自 data/extract/out/holders_hist_<code>.json（逐年年报「股份变动及股东情况」章节的
# 原文抽取件），这里只做重排与加总，不新增任何数字：
#   share_capital        [[年, 期末股份总数, 变动原因摘要]]      → 历年总股本变动图
#   holder_num           [[年末日期, 股东总数, A 股, H 股]]      → 与银行同结构，直接喂现有那张图
#   holder_concentration [{date, top1, top3, top10, …_ex}]      → 同上；_ex = 剔除港股代理人后重排
#   dividend_per10       [[年, 每 10 股派现]]                    → 历年分红图
HIST_CODES = {"telecom:600941": "600941", "telecom:601728": "601728",
              "telecom:600050": "600050", "food:605338": "605338"}


def _first_sentence(s, limit=90):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if not s:
        return ""
    if NOCHANGE_RE.search(s) and len(s) < 24:
        return "未变动"
    cut = re.split(r"[；;。]", s)[0]
    return (cut[:limit] + "…") if len(cut) > limit else cut


def _chg_field(row):
    """报告期内增减 → 接口那套 change 字段的写法（数字字符串／「不变」／「新进」）。
    子代理抽取件里 change 是原文串（可能写 -、(953,351)、新进），change_shares 是它解析出的股数。"""
    raw = str(row.get("change") if row.get("change") is not None else "").strip()
    n = row.get("change_shares")
    if n is None and re.fullmatch(r"[-+(]?[\d,]+\)?", raw or "x"):
        n = int(re.sub(r"[^\d-]", "", raw.replace("(", "-"))) if raw not in ("-", "") else 0
    if "新进" in raw:
        return "新进"
    if n is None:
        return None if raw in ("", "-", "—") else raw
    return "不变" if n == 0 else str(int(n))


def _conc_row(year, rows):
    """某一年的集中度：pct 是年报口径的占总股本比例，直接排序加总；
    剔代理人那套把名义持有人整行去掉后重排，只有名册里确有代理人时才给。"""
    pcts = sorted([float(r["pct"]) for r in rows if r.get("pct") is not None], reverse=True)
    named = [r for r in rows if not NOMINEE_RE.search(r.get("name") or "")]
    ex = sorted([float(r["pct"]) for r in named if r.get("pct") is not None], reverse=True)
    top = lambda a, n: round(sum(a[:n]), 2) if len(a) >= n else None
    first = max(rows, key=lambda r: float(r.get("pct") or 0)) if rows else {}
    first_ex = max(named, key=lambda r: float(r.get("pct") or 0)) if named else {}
    out = {"date": f"{year}-12-31", "top1": top(pcts, 1), "top3": top(pcts, 3),
           "top10": top(pcts, 10), "top1_name": first.get("name")}
    if len(named) < len(rows):
        out.update({"top1_ex": top(ex, 1), "top3_ex": top(ex, 3),
                    "top1_ex_name": first_ex.get("name")})
    return out


def attach_history(key, code):
    """把抽取件折成上面四层塞进 MANUAL[key]；抽取件还没生成就跳过（页面自然少那几张图）。
    最新一年的前十名股东表同时覆盖 holders —— 名册也用年报原文那份，跟标准模板同口径。"""
    path = os.path.join(OUT_DIR, f"holders_hist_{code}.json")
    if not os.path.exists(path):
        print(f"  [skip] {key}: 缺 {os.path.relpath(path, os.path.dirname(TABLES))}")
        return
    with open(path, "r", encoding="utf-8") as f:
        hist = json.load(f)
    years = hist.get("years") or {}
    ent = MANUAL.setdefault(key, {})
    cap, hnum, conc, div = [], [], [], []
    unit = "元"
    for y in sorted(years):
        r = years[y] or {}
        if r.get("total_shares"):
            cap.append([y, int(r["total_shares"]), _first_sentence(r.get("share_change_note"))])
        if r.get("holder_num_total"):
            hnum.append([f"{y}-12-31", int(r["holder_num_total"]),
                         r.get("holder_num_a"), r.get("holder_num_h")])
        rows = [x for x in (r.get("top_holders") or []) if x.get("pct") is not None]
        if rows:
            conc.append(_conc_row(y, rows))
        d = r.get("dividend") or {}
        v = d.get("per_10_shares")
        if v is None and d.get("per_share") is not None:
            v = round(float(d["per_share"]) * 10, 4)   # 只做 ×10 的单位换算，不推算金额
        if v is None and d.get("per_share_hkd") is not None:
            # 中国移动的股息以港元宣派、人民币金额待汇率折算 —— 那就画港元，**不做汇率换算**
            v = round(float(d["per_share_hkd"]) * 10, 4)
            unit = "港元"
        if v is not None:
            div.append([y, float(v)])
    last = sorted(years)[-1] if years else None
    rows = (years.get(last) or {}).get("top_holders") or []
    total = (years.get(last) or {}).get("total_shares")
    if rows and total:
        holders = [{"rank": i + 1, "name": x["name"], "hold_num": x.get("shares"),
                    "ratio": (round(x["shares"] / total * 100, 2) if x.get("shares")
                              else x.get("pct")),
                    "change": _chg_field(x), "state": ("新进" if "新进" in str(x.get("change") or "")
                                                       else ""),
                    "shares_type": x.get("nature") or "", "total_shares": int(total),
                    "pledged": x.get("pledged")}
                   for i, x in enumerate(rows)]
        # 手工写过 holders 的公司（巴比）拿抽取件交叉核对：两次独立转录必须对上
        for old, new in zip(ent.get("holders") or [], holders):
            assert old["hold_num"] == new["hold_num"], (key, old["name"], old["hold_num"],
                                                        new["hold_num"])
        ent["holders"] = holders
        ent["holders_end_date"] = f"{last}-12-31"
        # 名册换成年报原文那份后，页面上的「主体口径」也要跟着改口 —— 再写「接口快照」就是错的
        ent.setdefault("source", (hist.get("_meta") or {}).get("source"))
        ent["holders_caliber"] = f"年报口径（{last} 年报「前十名股东持股情况表」）"
    ent["share_capital"] = cap or None
    ent["holder_num"] = hnum or None
    ent["holder_concentration"] = conc or None
    ent["dividend_per10"] = div or None
    ent["dividend_unit"] = unit if div else None
    ent["history_gaps"] = HIST_GAPS.get(key) or None
    ent["history_source"] = (hist.get("_meta") or {}).get("source", "") + \
        "　逐年抽取件：data/extract/out/holders_hist_%s.json（抽取方式见其 _meta.method，" \
        "缺口见其 gaps）。集中度序列由各年前十名股东表的占总股本比例排序加总，" \
        "「剔代理人」口径为去掉名义持有人整行后重排。" % code
    print(f"  [hist] {key}: 股本 {len(cap)} 年 / 户数 {len(hnum)} 期 / 集中度 {len(conc)} 年 / "
          f"分红 {len(div)} 年 / 名册 {len(ent.get('holders') or [])} 行（{last}）")


def attach_tech_history(key="tech:09888", code="09888"):
    """百度的历年序列来自 20-F 抽取件（口径与 A 股完全不同，单独一段）：
      share_capital        各年 20-F 用作分母的已发行流通普通股总数
      holder_concentration 各年实益拥有权表里排前的几行累计（top1 = 李彦宏），另给一条投票权%
    没有股东户数（开曼公司 + ADS，不存在 A 股那种登记户数），也没有分红（百度从未派息）。"""
    path = os.path.join(OUT_DIR, f"ownership_hist_{code}.json")
    if not os.path.exists(path):
        print(f"  [skip] {key}: 缺 {os.path.relpath(path, os.path.dirname(TABLES))}")
        return
    with open(path, "r", encoding="utf-8") as f:
        hist = json.load(f)
    years, cap, conc = hist.get("years") or {}, [], []
    for y in sorted(years):
        r = years[y] or {}
        if r.get("total_ordinary_shares"):
            # 20-F 没有 A 股那种「股份变动情况表」，变动原因一律留空（图上就都是灰柱）
            cap.append([y, int(r["total_ordinary_shares"]), ""])
        rows = [x for x in (r.get("rows") or [])
                if x.get("group") != "total" and x.get("pct_of_total_ordinary") is not None]
        if not rows:
            continue
        first = max(rows, key=lambda x: float(x["pct_of_total_ordinary"]))
        # 只给第一大股东那一条：20-F 的表里 Handsome Reward 的 16.5% 是李彦宏 18.6% 的**一部分**
        # （同一批 B 类股既算在他名下、又单列他全资的 BVI 公司），逐行相加会重复计一遍，
        # 所以这里不做前三／前十名累计 —— 宁可只画一条线，也不给一个加错的数。
        row = {"date": f"{y}-12-31", "top1": round(float(first["pct_of_total_ordinary"]), 2),
               "top3": None, "top10": None,
               "top1_name": first.get("name_zh") or first.get("name_en")}
        if first.get("pct_of_voting_power") is not None:
            row["top1_vote"] = float(first["pct_of_voting_power"])
        conc.append(row)
    ent = MANUAL.setdefault(key, {})
    ent["share_capital"] = cap or None
    # 股本序列跨着一次股份拆细：2005–2019 是拆细前基数（约 3,500 万股），
    # FY2020 起的 20-F 按 1 拆 80 后的基数追溯列示（约 27 亿股）—— 原文两段差 80 倍，
    # 同轴画会把前 15 年压成看不见的贴地条，所以给前段一个折算倍数，让页面按拆细后口径统一画
    ent["share_capital_break"] = {
        "at": "2020",
        "factor": 80,
        "text": "2021-03 股东批准并实施 **1 拆 80 股份拆细**（同步把 ADS 比例改为 1 ADS = 8 股 A 类），"
                "FY2020 起的 20-F 按拆细后基数列示。原文里 2005–2019 各年是拆细前基数（约 3,500 万股），"
                "与右侧差 80 倍无法同轴比较，**本图把断点左侧各年 × 80 折算到拆细后口径**"
                "（浅色柱，tooltip 同时给出年报原文股数）—— 拆股不改变经济份额，折算后才看得出"
                "百度这二十年股本几乎没有摊薄。ADS 比例另在 2010-05-12 由 1 ADS = 1 股改为 10 ADS = 1 股。",
    }
    ent["holder_concentration"] = conc or None
    ent["history_gaps"] = [
        "**百度不派股息**（20-F 各年均无分红方案），所以没有分红图；也没有 A 股那种「股东户数」——"
        "开曼公司 + ADS 结构下不存在境内登记户数这一口径。",
        "**历年集中度只有第一大股东那一条**：20-F 只披露董事高管与已知持股 5% 以上者，"
        "而且表里 Handsome Reward Limited 的 16.5% 是李彦宏 18.6% 的一部分（同一批 B 类股"
        "既算在他名下、又单列他全资的 BVI 公司），逐行相加会重复计一遍，因此不给前三／前十名累计。",
        "**FY2023 起口径变了**：员工不可撤销投票代理的股份开始计入李彦宏的实益拥有股数，"
        "所以 16.3%（FY2022）→ 18.2%（FY2023）**是口径变化，不是增持**；"
        "FY2005/2006 的 21.9%／21.5% 则含当年计入的配偶马东敏 B 类股（FY2007 起改为剔除）。",
        "**投票权%那条线 FY2018 及以前没有**：原文表格无该列、脚注也未提；"
        "A 类 1 票 / B 类 10 票的双重股权自 2005 年 IPO 起就存在，只是 FY2019 及以前的表不分列 A/B 股数。",
    ]
    ent["history_source"] = (hist.get("_meta") or {}).get("source", "") + \
        "　逐年抽取件：data/extract/out/ownership_hist_09888.json（21 份 20-F，" \
        "从 .htm 表格按列取数，抽取方式见其 _meta.method，缺口见其 gaps）。"
    print(f"  [hist] {key}: 股本 {len(cap)} 年 / 集中度 {len(conc)} 年（无户数、无分红）")


if __name__ == "__main__":
    for _key, _code in HIST_CODES.items():
        attach_history(_key, _code)
    attach_tech_history()
    MANUAL["_meta"] = {
        "generated_by": "data/extract/build_holders_manual.py",
        "consumed_by": "backend_python.py::read_holders → /api/holders → dashboard/company/shareholder.html",
        "note": ("按 \"<板块>:<代码>\" 索引。factions 只做分组，不改任何数字；"
                 "food/tech 两家没有 annual 表，holders 整份在这里，口径见各自 caliber_note。"
                 "basis 字段区分「年报披露／20-F 披露」与「同类归并」，页面会原样印出。"
                 "share_capital / holder_num / holder_concentration / dividend_per10 四层"
                 "照 dashboard/company/bank/shareholder.html 那套标准模板补，"
                 "来自 data/extract/out/holders_hist_<代码>.json 的年报原文抽取件，只重排与加总。"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(MANUAL, f, ensure_ascii=False, indent=1)
    print("written", OUT)
    for k, v in MANUAL.items():
        if k == "_meta":
            continue
        hs = v.get("holders") or []
        print(f"  {k:16s} factions={len(v.get('factions') or [])} holders={len(hs)}"
              + (f" 合计={sum(h['ratio'] for h in hs):.2f}%" if hs else ""))
