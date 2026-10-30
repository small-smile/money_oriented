# 度阿发 (industry_research)

行业财务数据看板：Vue 3 + ECharts 前端 + Flask 纯 JSON API。

两条硬约束：**可信**——只用经审计的一手数据（交易所披露、公司官网 IR），第三方接口仅作交叉核对，
出处与口径逐项记在 `data/tables/data_sources.txt`，缺口写清楚而不用别的数字顶上；
**可读**——每页只讲清一件事，不堆大而全的仪表盘。

## 目录

- `frontend/` — Vue 3 + Vite，唯一的页面来源
  - `src/views/` 页面：`Home.vue` 导航首页、`industry/*` 行业页、`company/*` 个股页
    （`bank/` `telecom/` `cmcc/` `baidu/` `food/` `oil/` + 全站共用的 `Shareholder.vue`）
  - `src/components/SiteHeader.vue` 按路由分组的导航；`src/assets/base.css` 全站样式；
    `src/router/index.js` 路由（`beforeEach` 剥掉旧链接的 `.html` 后缀）
  - `src/views/company/bank/legacy/` 银行页 3100+ 行原始图表脚本，逐字沿用
  - `public/data` → 仓库 `data/` 软链（只剩 txt/csv 等非 JSON 文件；cmcc 页的 JSON 走 `/api/tables/<表名>`）
- `app.py` + `backend/` — Flask 纯 JSON API，只有 `/api/...`，页面路径一律 404
- `data/extract/*.py` — 抽数脚本：`data/raw/`（原始文件，不入库）→ `data/tables/`（成品表，入库）；
  `data/` 下的 `*.json` 读写统一经 `backend/jsonstore.py`
- MySQL 只放结构化表，不存 JSON 原文：`data/sql/tables/*.sql` 一表一文件，
  由 `./venv/bin/python data/extract/load_to_mysql.py --init --reload` 从 `data/tables/*.json` 全量拆出，可反复跑
  （连接配置读 `.env` 的 `MYSQL_*`，`backend/db.py` 一份）。`/api` 一律读这些表、按载入映射还原原字段名
  （行业年度表 `backend/industry_db.py`、股权结构 `backend/holders_db.py`、银行详情页图表 `backend/bank_charts_db.py`）；
  只剩中国移动的 `/api/tables/telecom_00941_*.json` 还读文件（没拆表）。
  JSON 更新后重跑一次 load_to_mysql.py 才跟上。
  实体键带交易所前缀（`sh.601077` / `hk.01578`）；行业专属列的字段映射在 `data/extract/industry_columns.py`；
  没登记映射的字段、同义字段两边不一致，载入时记进 `data_anomaly`，不静默丢弃
- `data/local_index.md` — 本地数据索引（`gen_local_index.py` 生成）。取数先查它，本地没有才去交易所/官网抓

## 运行

```bash
./venv/bin/pip install -r requirements.txt   # 首次/换机
./venv/bin/python app.py                     # 后端，:5000
cd frontend && npm install && npm run dev    # 前端，:5173，/api 代理到 5000
cd frontend && npm run build                 # 产物 frontend/dist，给 nginx 发
```

- 后端必须用 venv 的 python，系统 python 没装 `flask_cors`。
- 后端与 `load_to_mysql.py` 都连本机 MySQL（`.env` 的 `MYSQL_*`），起后端前 MySQL 要在、表要先载入。
- 本机 `NODE_ENV=production` 会让 npm 跳过 devDependencies，靠仓库里的 `frontend/.npmrc`（`include=dev`）绕开。
- nginx 配置在 `deploy/nginx/`：发 `dist` 静态站、`/api/` 反代 Flask、`/data/` alias 到仓库 `data/`、
  SPA 深链 `try_files … /index.html`。`standalone.conf` 免 root（`127.0.0.1:8080`，
  `nginx -c $PWD/deploy/nginx/standalone.conf` 起、`-s quit` 停）；`industry_research.conf` 是系统 nginx
  （`/usr/local/nginx`）的 vhost，软链到 `conf/vhost/` 后 `sudo nginx -s reload`，即 `http://localhost/`。
  两份都只听 127.0.0.1——**服务没有鉴权，别暴露到局域网**。
- 测试：`./venv/bin/python -m pytest test_backend.py`

## 银行页

`/company/bank/:code`（A 股 6 位 / H 股 5 位，缺省 `601077` 渝农商行）是同一套页面按代码渲染：
向 `/api/company_charts?code=` 取数，标题与 H1 由返回的 `_bank` 元信息拼出；可切换清单 =
MySQL 里有年度财务序列的银行（`/api/banks`）。

图表载荷不落文件：后端把 `gen_company_charts.py` 的 `build()` 输入（annual、股东手工件、ar_manual、
`bank_<code>_detail_manual.json`）从 MySQL 拼回后请求时现算（`backend/bank_charts_db.py`），共 45 家
（42 家 A 股/A+H + 天津 `01578`、江西 `01916`、哈尔滨 `06138` 三家纯 H 股），渝农商行也一样；
各行 23~45 个数据键，缺的图保留图位贴占位。
页面模板不写任何一家的数字：各行的说明段、KPI 卡、年报摘录表按 DOM id 放在 detail_manual 的 `_notes`，
填进模板里 `.bank-specific` 的空壳，本行没给的整块隐藏。

## 抽数

```bash
./venv/bin/python data/extract/fetch_insurer_financials.py            # 走本地缓存
./venv/bin/python data/extract/fetch_insurer_financials.py --refresh  # 重新请求接口
./venv/bin/python data/extract/fetch_insurer_financials.py 00966      # 只重建一家
```

`fetch_{insurer,developer,cement,telecom,bank}_financials.py` 同套参数，生成
`data/tables/<行业>_<code>_annual.json`，供 `/api/<行业>_peers`、`/api/<行业>_annual?code=` 下发。
纯港股公司接口取不到的字段（中国太平 17 个保险专项字段、三家港股开发商的「已售未结」）
逐份年报读出后硬编码在脚本常量表里，每行带来源注释。

**口径断点、汇率折算、自算 vs 披露值、逐年交叉核验结果一律记在 `data/tables/data_sources.txt`，
本文件不复制，避免两份漂移。**

## 开发约定

项目规则放 `.comate/rules/`，一个 `.mdr` 一条，`globs` 指定生效范围（图表默认不加 dataZoom、
视图切换用胶囊控件、分部收入四桶映射、取数信息源优先级等）。规则内容只写在 `.mdr` 里。
`.comate/` 只有 `rules/` 入库（见 `.gitignore`）。
