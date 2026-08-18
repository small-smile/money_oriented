# 度阿发 (money_oriented)

石油行业与银行/个股的数据看板：本地抽数落盘成表，前端用 ECharts 画图。

## 目录

- `dashboard/` — 静态页面，直接用浏览器打开
  - `index.html` 入口；`industry/oil/*.html`、`industry/bank/*.html`、
    `industry/insurance/*.html` 行业页
  - `company/` 个股页，按行业分子目录：`company/bank/*.html`（银行，共用 `charts.js`）、
    `company/food/*.html`（食品）、`company/oil/*.html`（石油）；
    `company/page.css` 是各行业个股页共用的样式
  - `common/base.css` 各页共用样式；导航按分组分开：`common/site-header.js`（石油）、
    `common/bank-header.js`（`company/bank/`）
- `backend_python.py` — Flask 接口（只提供 `/api/...`，不托管静态文件）
- `data/extract/*.py` — 抽数脚本，从 `data/raw/` 的原始文件生成 `data/tables/`
- `data/tables/` — 入库的成品表；来源与口径记在 `data/tables/data_sources.txt`
- `data/raw/` — 原始下载文件，不入库（体积大，可用 `data/extract/` 重新拉取）

## 运行

```bash
./venv/bin/python backend_python.py   # 监听 5000
```

必须用 venv 里的 python，系统 python 没装 `flask_cors`。页面是独立打开的，跨域请求
`http://127.0.0.1:5000/api/...`，所以后端要先起来图才有数据。

`company/bank/*.html` 是同一份页面按银行代码渲染：地址栏 `?code=`（A 股 6 位 / H 股 5 位，
缺省 `601077` 渝农商行）决定向 `/api/company_charts?code=` 取哪家的图表数据，页面标题与
H1 由返回的 `_bank` 元信息拼出。目前只有 `data/tables/company_charts_601077.json`，
换别的代码后端会返回 404；页面里的文字说明、KPI 数字和 HTML 表格也还是渝农商行的。

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

## 开发约定

给 IDE 读的项目规则放在 `.comate/rules/`，一个 `.mdr` 一条规则，带 `globs` 指定生效范围：

- `echarts-no-datazoom.mdr` — 图表默认不加 `dataZoom`。年度序列一次画全；非 K 线图尤其
  不要用 `type:'inside'`（它会吃掉滚轮事件让页面无法滚动，`zoomOnMouseWheel:false` 也
  救不回来，只能整块删掉）。看局部用 `toolbox` 的框选缩放。K 线图是例外。

`.comate/` 下只有 `rules/` 入库（见 `.gitignore` 里的 `.comate/*` + `!.comate/rules/`），
`specs/` 等本地状态不跟着仓库走。规则内容只写在 `.mdr` 里，这里不复制，避免两份漂移。
