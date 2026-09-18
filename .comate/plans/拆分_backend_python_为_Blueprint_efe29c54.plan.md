
# 拆分 backend_python.py 为 Flask Blueprint

## 现状确认
1957 行、103 个函数、34 个路由，全部平铺在一个文件里。已用 Explore 子代理完整扫过全文件并画出调用图，关键约束：

- `test_backend_python.py` 用 `import backend_python as bk` 直接访问大量内部符号（`bk.INDUSTRIES`、`bk.HOLDER_INDUSTRIES`、`bk._company_codes`、`bk._resolve_factions`、`bk._holder_table`、`bk._bank_factions`、`bk.read_industry_annual`、`bk.read_nav` 等）。拆分后这些名字必须仍能通过 `import backend_python as bk` 访问到——用 **re-export**（`from x import *` 式的显式引入）解决，不改测试文件。
- 路径全部是相对路径字符串（`"data/tables/..."`），基于进程 CWD，不是 `__file__`；拆分后各模块保持同样写法，不引入 `__file__` 相对寻址的不一致。
- 有一层**跨三大组的公共代码**：`_company_entity`/`_company_codes`/`_resolve_company_code`/`_cross_industry_redirect`（公司代码解析），以及常量 `TABLES_DIR`/`DASHBOARD_DIR`/`BANK_ORDER`——bank、行业年度（保险/地产/水泥/通信）、股权结构三组路由都调用它们，必须放共享模块，不能复制。
- `INDUSTRIES` 字典（保险/地产/水泥/通信四行业共用调度器）本身也是共享层，不属于单一行业。

## 拆分方案：按域分 6 个 Blueprint + 1 个共享层

新建 `backend/` 目录：

- `backend/__init__.py`（空）
- `backend/shared.py` —— 公共基础设施：
  - `TABLES_DIR`、`DASHBOARD_DIR`、常量 `HOLDERS_MANUAL_FILE`/`COMPANY_CODES_FILE`
  - `_company_codes`、`_company_entity`、`_resolve_company_code`、`_cross_industry_redirect`、`_holders_manual`
  - 通用文件读取 helper：`_read_two_col_txt` 等（如果只被一个组用则留在该组，公用的才放这里）
- `backend/oil.py` —— 石油/宏观 Blueprint (`oil_bp`)：`read_production`~`read_gold_oil`/`read_population` 及对应 7 条路由（12-610 行内容）
- `backend/bank.py` —— 银行 Blueprint (`bank_bp`)：`read_bank_financials`、`read_company_charts`、`read_tsf`、`list_banks`、`render_bank_page`、`read_bank_npl_formation`，常量 `BANK_PAGES`/`BANK_ORDER`/`LISTING_DATES`/`DEFAULT_BANK_CODE`，路由：`/api/bank_financials`、`/api/company_charts`、`/api/tsf`、`/api/banks`、`/api/bank_npl_formation`、`/bank/<code>/...`
- `backend/industry.py` —— 行业年度公共调度 Blueprint (`industry_bp`)：`INDUSTRIES` 字典、`_read_industry_table`、`read_industry_annual`、`read_industry_peers`，及 8 条路由（insurer/developer/cement/telecom 的 annual+peers）。水泥/通信的手工层合并函数（`_merge_cement_ops`、`_merge_telecom` 等）各自放 `backend/cement_ops.py`、`backend/telecom_ops.py` 子模块，被 `industry.py` 里的 `INDUSTRIES["merge"]` 引用
- `backend/holders.py` —— 股权结构 Blueprint (`holders_bp`)：`HOLDER_INDUSTRIES`、`NAV_HEADERS`、`read_nav`、`industry_default_code`、`_industry_of_code`、`read_holders` 及其全部 `_narr_*`/`_ring_*`/`_bank_factions`/`_holder_table` 私有函数，路由 `/api/holders`、`/api/nav`
- `backend/pages.py` —— 静态页面/首页 Blueprint (`pages_bp`)：`home_page`、`dashboard_page`、`bank_page`（依赖 bank.py 的 `BANK_PAGES`/`render_bank_page`）

`backend_python.py` 精简为：
```python
from flask import Flask
from flask_cors import CORS
from backend.oil import oil_bp
from backend.bank import bank_bp
from backend.industry import industry_bp
from backend.holders import holders_bp
from backend.pages import pages_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(oil_bp)
app.register_blueprint(bank_bp)
app.register_blueprint(industry_bp)
app.register_blueprint(holders_bp)
app.register_blueprint(pages_bp)

# re-export：保持 `import backend_python as bk; bk.xxx` 可用（测试文件依赖这些名字）
from backend.shared import _company_codes, _company_entity, _resolve_company_code, _cross_industry_redirect, _holders_manual
from backend.bank import BANK_ORDER, ...
from backend.industry import INDUSTRIES, read_industry_annual, read_industry_peers
from backend.holders import HOLDER_INDUSTRIES, NAV_HEADERS, read_nav, read_holders, industry_default_code, _holder_table, _bank_factions, _resolve_factions, ...
from backend.oil import read_production, read_price, ...

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

## 执行步骤
1. 建目录结构，逐个模块搬迁代码（保持函数体逐字不动，只搬位置+调整 import）。
2. `backend_python.py` 汇总注册 Blueprint + re-export 所有 `test_backend_python.py` 用到的符号。
3. 跑 `python -m pytest test_backend_python.py -v`，必须全绿（当前测试数量与断言不变）。
4. 跑一次 `python backend_python.py` 简单起服务，curl 几个关键路由（`/api/holders?code=601077`、`/api/nav`、`/dashboard/`）确认行为不变，然后停掉。
5. 清理：确认没有遗留在旧 `backend_python.py` 里的重复定义。

## 验证标准
- `pytest test_backend_python.py` 全部通过（约 40+ 个断言，覆盖 industry/holders/nav 三大组）。
- 路由行为零变化——这是重构，不改任何返回值/状态码逻辑。
