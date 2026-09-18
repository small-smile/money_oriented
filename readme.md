# 度阿发 (money_oriented)

数据看板 前端用 ECharts 图表库

## 项目定位

行业分析平台，对标百度内部竞品观察室类工具在「可视化功能弱、数据可信度低」上的短板，
致力于把数据的**高可信**与**高可读**做实：

- **可信**：数据优先采用上市公司财报等经审计的一手数据（交易所披露、公司官网 IR），
  第三方接口/研报仅作交叉核对或缺口补充，且逐项在页面或 `data/tables/data_sources.txt`
  中注明出处与口径；缺失、断点、口径变化不遮掩，写清楚而不是拿别的数字顶上。
- **可读**：拒绝数字堆砌、拒绝多图表/多层次的数据展示——每页聚焦讲清一件事，
  不用大而全的仪表盘和一堆并列小图去逼用户自己找结论。

## 目录

- `frontend/` — Vue 3 + Vite 前端（前后端分离后唯一的页面来源，取代原 `dashboard/`）
  - `src/views/` 页面：`Home.vue` 导航首页；`industry/*`（bank/insurance/realestate/
    cement/telecom 行业页）、`company/*`（个股页，按行业分子目录：`bank/`、`telecom/`、
    `cmcc/`、`baidu/`、`food/`、`oil/`，以及全站共用的 `Shareholder.vue` 股权结构页）
  - `src/components/SiteHeader.vue` 按路由分组的导航；`src/assets/base.css` 各页共用样式
    （逐字沿用原 `dashboard/common/base.css`）；`src/router/index.js` 路由（`beforeEach`
    会剥掉旧 URL 的 `.html` 后缀兼容老链接）
  - 银行页共用 3100+ 行原始图表脚本，逐字放在 `src/views/company/bank/legacy/`
  - `public/data` 软链到仓库 `data/`，dev 下 cmcc 页可直接 `fetch('/data/tables/*.json')`
  - `dist/` 是 `npm run build` 产物，线上由 nginx 直接发
- `app.py` — Flask **纯 JSON API**（只有 `/api/...`，不再托管任何页面）；`/api/banks`
  下发可切换银行清单，`/api/nav?code=` 按代码反查所属板块的导航
- `data/extract/*.py` — 抽数脚本，从 `data/raw/` 的原始文件生成 `data/tables/`
- `data/tables/` — 入库的成品表；来源与口径记在 `data/tables/data_sources.txt`
- `data/raw/` — 原始下载文件，不入库（体积大，可用 `data/extract/` 重新拉取）
- `data/local_index.md` — 本地数据检索索引：哪家公司、哪些年、有哪些成品表和年报文本，
  由 `data/extract/gen_local_index.py` 扫描 `data/raw/` 与 `data/tables/` 生成。
  取数先查它——本地已抽取的年报就是可信一手来源，本地没有才去交易所/官网抓

## 运行

前后端分离，分两块起。

后端（纯 JSON API，监听 5000）：

```bash
./venv/bin/python app.py
```

必须用 venv 里的 python，系统 python 没装 `flask_cors`。后端只提供 `/api/...`，根路径与
任何页面路径都返回 404——页面全部由前端负责。

前端开发（Vite dev server，热更新）：

```bash
cd frontend && npm install && npm run dev   # 监听 5173，/api 代理到 127.0.0.1:5000
```

本机 `NODE_ENV=production` 会让 npm 跳过 devDependencies，仓库里放了 `frontend/.npmrc`
（`include=dev`）绕开它。dev server 通过 vite 代理把 `/api` 打到后端，页面和接口同源。

前端构建 + nginx（测试/线上，URL 不带端口、页面和接口同源）：

```bash
cd frontend && npm run build      # 产物在 frontend/dist
```

nginx 配置在 `deploy/nginx/`：直接发 `frontend/dist` 静态站，只把 `/api/` 反代给 Flask，
`/data/` alias 到仓库 `data/`（cmcc 页取数用），SPA 深链用 `try_files ... /index.html` 兜底。
`standalone.conf` 是免 root 的独立实例（`127.0.0.1:8080`），
`nginx -c $PWD/deploy/nginx/standalone.conf` 起、`-s quit` 停；
`money_oriented.conf` 是给系统 nginx（`/usr/local/nginx`）的 vhost，软链到 `conf/vhost/`
后 `sudo nginx -s reload` 即可用 `http://localhost/` 访问（需 root）。
两份都只监听 127.0.0.1——服务没有鉴权，别暴露到局域网。

`company/bank/*` 是同一套页面按银行代码渲染：路由 `/company/bank/:code`（A 股 6 位 / H 股
5 位，缺省 `601077` 渝农商行）决定向 `/api/company_charts?code=` 取哪家的图表数据，页面标题
与 H1 由返回的 `_bank` 元信息拼出。前端把 code 与可切换银行清单（清单 = 实际存在的
`data/tables/company_charts_<code>.json`，加一家行只需放数据文件）喂给复用的原始图表脚本，
导航栏的银行下拉框直接用它。旧的 `.html` 链接和 `/bank/<code>/<page>` 短地址由前端路由兼容
（`beforeEach` 剥 `.html`）。

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
`/api/insurer_annual?code=` 供 `/industry/insurance/peers` 页使用。A 股五家取值为 A 股年报合并口径，
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
`/industry/realestate/peers` 页使用。三点要注意：三道红线（剔预收资产负债率／净负债率／
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
