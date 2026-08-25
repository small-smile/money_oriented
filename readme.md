# 度阿发 (money_oriented)

石油行业与银行/个股的数据看板：本地抽数落盘成表，前端用 ECharts 画图。

## 目录

- `dashboard/` — 看板页面，由后端托管（银行详情页动态渲染，其余原样下发）
  - `index.html` 入口；`subject/oil/*.html`、`industry/bank/*.html`、
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
- `data/local_index.md` — 本地数据检索索引：哪家公司、哪些年、有哪些成品表和年报文本，
  由 `data/extract/gen_local_index.py` 扫描 `data/raw/` 与 `data/tables/` 生成。
  取数先查它——本地已抽取的年报就是可信一手来源，本地没有才去交易所/官网抓

## 运行

```bash
./venv/bin/python backend_python.py   # 监听 5000
```

必须用 venv 里的 python，系统 python 没装 `flask_cors`。起好后访问后端根路径（本机直连是
5000 端口，线上走 nginx 转发的域名，会跳到 `/dashboard/index.html`）。页面里的接口地址一律
写成相对路径 `/api/...`，跟页面同源，换端口/换机器都不用改代码；因此不能再用 `file://`
直接打开 HTML——那样相对路径无处可指，图会取不到数据。

`company/bank/*.html` 是同一份页面按银行代码渲染：`?code=`（A 股 6 位 / H 股 5 位，缺省
`601077` 渝农商行）决定向 `/api/company_charts?code=` 取哪家的图表数据，页面标题与 H1 由
返回的 `_bank` 元信息拼出。后端渲染时会把 code 注入 `window.COMPANY_CODE`、把可切换银行
清单注入 `window.__BANKS`（清单 = 实际存在的 `data/tables/company_charts_<code>.json`，
加一家行只需放数据文件），导航栏的银行下拉框直接用它，`file://` 下退回解析地址栏 + 前端
兜底名单。也可以走短地址 `/bank/<code>/<page>`，它 302 到
`/dashboard/company/bank/<page>?code=<code>`（保持 URL 深度，页内相对路径的 css/js 才不
会 404）；非法 code 退回默认行，不存在的页面 404。

目前 44 家行有数据文件（41 家 A 股或 A+H 上市银行 + 天津银行 `01578`、江西银行 `01916`、
哈尔滨银行 `06138` 这三家纯 H 股城商行），但只有
`601077` 是手工精编（42 个数据键），其余由 `gen_company_charts.py` 批量生成（基础 15~16 个键，
另有 `bank_<code>_detail_manual.json` 手工覆盖层可把某家行补到 33~39 个键），
缺的图保留图位并贴「该行暂无此项数据」占位；
页面里的文字说明、KPI 数字和 HTML 表格也还是渝农商行的。

重新抽数：

```bash
./venv/bin/python data/extract/oil_consumption.py
```

保险行业的 A 股五家是接口直抓，港股中国太平的保险专项指标另有一份年报手工表：

```bash
./venv/bin/python data/extract/fetch_insurer_financials.py            # 六家险企，走本地缓存
./venv/bin/python data/extract/fetch_insurer_financials.py --refresh  # 重新请求东财接口
./venv/bin/python data/extract/fetch_insurer_financials.py 00966      # 只重建中国太平
```

生成 `data/tables/insurer_<code>_annual.json`（601318 平安 / 601628 国寿 / 601601 太保 /
601336 新华 / 601319 人保 / 00966.HK 中国太平），后端 `/api/insurer_peers`（六家一次取回）与
`/api/insurer_annual?code=` 供 `industry/insurance/peers.html` 使用。A 股五家取值为 A 股年报合并口径，
2023 年起的 IFRS17／IFRS9 断点、偿二代与二期的偿付能力口径断点见页面备注与
`data/tables/data_sources.txt`。

中国太平只在港交所上市，港股 F10 主要指标不含任何保险专项指标，因此投资收益率、分子公司偿付能力、
寿险新业务价值、投资资产、母公司与总权益、员工数、每股股息共 17 个字段来自港交所 HKEXnews 的
2007—2025 年 19 份中文年报原文，硬编码在 `fetch_insurer_financials.py` 的 `HK_REPORT_00966` 常量表里
（每行带来源与口径注释）。年报以港元编制，逐年隐含汇率 = F10 人民币总资产 ÷ 年报港元总资产，
写入 JSON 的 `fx_implied`；用年报总权益反算权益资产比与 F10 自算值比对，19 年中 12 年四位小数一致，
另 7 年的差额全部落在已知重述年份上，差额见 `equity_check`。2000—2006 年取不到（HKEXnews 检索库自 2007-04 起），
寿险退保率年报从不披露，是 11 张图里唯一没有太平序列的一张。

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
