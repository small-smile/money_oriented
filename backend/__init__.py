# backend 包的公开 API：把各子模块的公开/私有函数与常量在包顶层重新导出，
# 让 `import backend as bk` 能一次拿到全部符号（测试即依赖这个扁平命名空间）。
# 拆分只挪动了实现位置，这里保持对外符号不变。
import os          # noqa: F401  (test_backend.py monkeypatches bk.os.path.exists)
import json        # noqa: F401
import re          # noqa: F401

from backend.shared import (          # noqa: F401
    success, error,
    TABLES_DIR, HOLDERS_MANUAL_FILE, COMPANY_CODES_FILE,
    _holders_manual, _company_codes, _company_entity,
    _resolve_company_code, _cross_industry_redirect,
)
from backend.oil import (             # noqa: F401
    read_production, _read_oil_candles, read_price, read_adj_price,
    _read_region_csv, read_production_region, read_consumption_region,
    read_consumption_product, _read_two_col_txt, read_consumption_growth,
    _read_reserves_csv, read_petrochina_reserves, read_cnooc_reserves,
    _read_company_production_csv, _read_oil_years_usd,
    read_gold_ratio, read_gold_oil, read_population,
)
from backend.bank import (            # noqa: F401
    read_bank_financials, read_company_charts, read_tsf,
    list_banks, read_bank_npl_formation,
    DEFAULT_BANK_CODE, BANK_ORDER, LISTING_DATES,
)
from backend.cement_ops import (      # noqa: F401
    CEMENT_PEERS, _cement_ops_manual, _cement_unit, _cement_ops_year, _merge_cement_ops,
)
from backend.telecom_ops import (     # noqa: F401
    TELECOM_PEERS, _telecom_ops_manual, _telecom_segment_manual,
    _telecom_segment_labels, _attach_telecom_segments, _merge_telecom, _merge_telecom_ops,
)
from backend.industry import (        # noqa: F401
    INSURER_PEERS, DEVELOPER_PEERS, INDUSTRIES, _PEERS_DICT_FIELDS,
    _read_industry_table, read_industry_annual, read_industry_peers,
)
from backend.holders import (         # noqa: F401
    HOLDER_INDUSTRIES, DEFAULT_HOLDER_INDUSTRY,
    _industry_of_code, industry_default_code, read_nav,
    _company_charts_block, _company_charts_holders, _bank_history_from_charts,
    _bank_factions, _holder_table, _norm_holder_name, _resolve_factions,
    _ring_block_from_charts, _ring_alt_from_charts, _RING_ALT_KEYS,
    YI, _n, _narr_dividend, _narr_share_capital, _narr_holder_num,
    _narr_concentration, _narr_holders, _company_narrative, _as_year_pairs,
    read_holders,
)
