# 度阿发 (money_oriented)

石油行业与银行/个股的数据看板：本地抽数落盘成表，前端用 ECharts 画图。

## 目录

- `dashboard/` — 看板页面，由后端托管（银行详情页动态渲染，其余原样下发）
  - `index.html` 入口；`industry/oil/*.html`、`industry/bank/*.html`、
    `industry/insurance/*.html`、`industry/realestate/*.html` 行业页
  - `company/` 个股页，按行业分子目录：`company/bank/*.html`（银行，共用 `charts.js`）、
    `company/food/*.html`（食品）、`company/oil/*.html`（石油）；
    `company/page.css` 是各行业个股页共用的样式
  - `common/base.css` 各页共用样式；导航按分组分开：`common/site-header.js`（石油）、
    `common/bank-header.js`（`company/bank/`）
- `backend_python.py` — Flask：`/api/...` 接口 + 托管 `dashboard/`（银行详情页按
  bank code 动态渲染，`/api/banks` 下发可切换银行清单）
- `data/extract/*.py` — 抽数脚本，从 `data/raw/` 的原始文件生成 `data/tables/`
- `data/tables/` — 入库的成品表；来源与口径记在 `data/tables/data_sources.txt`
- `data/raw/` — 原始下载文件，不入库（体积大，可用 `data/extract/` 重新拉取）

## 运行

```bash
./venv/bin/python backend_python.py   # 监听 5000
```

必须用 venv 里的 python，系统 python 没装 `flask_cors`。起好后访问
`http://127.0.0.1:5000/`（会跳到 `/dashboard/index.html`）。直接 `file://` 打开 HTML 也仍
能用，此时页面跨域请求 `http://127.0.0.1:5000/api/...`，后端一样要先起来图才有数据。

`company/bank/*.html` 是同一份页面按银行代码渲染：`?code=`（A 股 6 位 / H 股 5 位，缺省
`601077` 渝农商行）决定向 `/api/company_charts?code=` 取哪家的图表数据，页面标题与 H1 由
返回的 `_bank` 元信息拼出。后端渲染时会把 code 注入 `window.COMPANY_CODE`、把可切换银行
清单注入 `window.__BANKS`（清单 = 实际存在的 `data/tables/company_charts_<code>.json`，
加一家行只需放数据文件），导航栏的银行下拉框直接用它，`file://` 下退回解析地址栏 + 前端
兜底名单。也可以走短地址 `/bank/<code>/<page>`，它 302 到
`/dashboard/company/bank/<page>?code=<code>`（保持 URL 深度，页内相对路径的 css/js 才不
会 404）；非法 code 退回默认行，不存在的页面 404。

目前 10 家行有数据文件（9 家 A+H 上市银行 + 天津银行 `01578` 这家纯 H 股城商行），但只有
`601077` 是手工精编（42 个数据键），其余由 `gen_company_charts.py` 批量生成（15~16 个键），
缺的图保留图位并贴「该行暂无此项数据」占位；
页面里的文字说明、KPI 数字和 HTML 表格也还是渝农商行的。

重新抽数：

```bash
./venv/bin/python data/extract/oil_consumption.py
```

保险行业的数据是接口直抓（不经 `data/raw/` 的年报 PDF）：

```bash
./venv/bin/python data/extract/fetch_insurer_financials.py            # 五家险企，走本地缓存
./venv/bin/python data/extract/fetch_insurer_financials.py --refresh  # 重新请求东财接口
```

生成 `data/tables/insurer_<code>_annual.json`（601318 平安 / 601628 国寿 / 601601 太保 /
601336 新华 / 601319 人保），后端 `/api/insurer_peers`（五家一次取回）与
`/api/insurer_annual?code=` 供 `industry/insurance/peers.html` 使用。取值为 A 股年报合并口径，
2023 年起的 IFRS17／IFRS9 断点、偿二代与二期的偿付能力口径断点见页面备注与
`data/tables/data_sources.txt`。

地产行业同样是接口直抓：

```bash
./venv/bin/python data/extract/fetch_developer_financials.py            # 六家央企开发商，走本地缓存
./venv/bin/python data/extract/fetch_developer_financials.py --refresh  # 重新请求东财接口
```

生成 `data/tables/developer_<code>_annual.json`（A 股：600048 保利发展 / 001979 招商蛇口 /
000069 华侨城A；纯港股：00688 中国海外发展 / 01109 华润置地 / 00817 中国金茂），后端
`/api/developer_peers`（六家一次取回）与 `/api/developer_annual?code=` 供
`industry/realestate/peers.html` 使用。三点要注意：三道红线（剔预收资产负债率／净负债率／
现金短债比）是按公开定义**自算**、不是年报披露值；港股 F10 返回的金额是年报本位币原值、
不折算（接口字段却一律标 HKD 不可信），但三家近年年报都以**人民币**编制（中海外自 FY2019、
华润置地自 FY2018、中国金茂自 FY2016），六家金额可直接比大小；港股三家的「已售未结」
（`presale`）接口取不到，逐年从 HKEXnews 年度业绩公告原文取数、硬编码在脚本的
`HK_PRESALE_THOUSANDS` 里。详见 `data/tables/data_sources.txt`。

## 开发约定

给 IDE 读的项目规则放在 `.comate/rules/`，一个 `.mdr` 一条规则，带 `globs` 指定生效范围：

- `echarts-no-datazoom.mdr` — 图表默认不加 `dataZoom`。年度序列一次画全；非 K 线图尤其
  不要用 `type:'inside'`（它会吃掉滚轮事件让页面无法滚动，`zoomOnMouseWheel:false` 也
  救不回来，只能整块删掉）。看局部用 `toolbox` 的框选缩放。K 线图是例外。

`.comate/` 下只有 `rules/` 入库（见 `.gitignore` 里的 `.comate/*` + `!.comate/rules/`），
`specs/` 等本地状态不跟着仓库走。规则内容只写在 `.mdr` 里，这里不复制，避免两份漂移。
