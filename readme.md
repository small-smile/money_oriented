# money_oriented

石油行业与银行/个股的数据看板：本地抽数落盘成表，前端用 ECharts 画图。

## 目录

- `dashboard/` — 静态页面，直接用浏览器打开
  - `index.html` 入口；`industry/oil/*.html` 行业页；`company/*.html` 个股页
  - `common/base.css`、`common/site-header.js` 是各页共用的样式与导航
- `backend_python.py` — Flask 接口（只提供 `/api/...`，不托管静态文件）
- `data/extract/*.py` — 抽数脚本，从 `data/raw/` 的原始文件生成 `data/tables/`
- `data/tables/` — 入库的成品表；来源与口径记在 `data/tables/data_sources.txt`
- `data/raw/` — 原始下载文件，不入库（体积大，可用 `data/extract/` 重新拉取）

## 运行

```bash
./venv/bin/python backend_python.py   # 监听 5000
```

必须用 venv 里的 python，系统 python 没装 `flask_cors`。页面是独立打开的，跨域请求
`http://127.0.0.1:5000/api/...`，所以后端要先起来图才有数据。有些页面的数据直接内联在
HTML 里（如 `company/` 下的几页），不依赖后端。

重新抽数：

```bash
./venv/bin/python data/extract/oil_consumption.py
```

## 开发约定

给 IDE 读的项目规则放在 `.comate/rules/`，一个 `.mdr` 一条规则，带 `globs` 指定生效范围：

- `echarts-no-datazoom.mdr` — 图表默认不加 `dataZoom`。年度序列一次画全；非 K 线图尤其
  不要用 `type:'inside'`（它会吃掉滚轮事件让页面无法滚动，`zoomOnMouseWheel:false` 也
  救不回来，只能整块删掉）。看局部用 `toolbox` 的框选缩放。K 线图是例外。

`.comate/` 下只有 `rules/` 入库（见 `.gitignore` 里的 `.comate/*` + `!.comate/rules/`），
`specs/` 等本地状态不跟着仓库走。规则内容只写在 `.mdr` 里，这里不复制，避免两份漂移。
