#!/usr/bin/env bash
# 一键启动：./start.sh [dev|prod]，Ctrl+C 全停
#   dev（默认）Flask :5000 + Vite :5173
#   prod       构建 dist，Flask :5000 + 免 root nginx :8080
set -euo pipefail
cd "$(dirname "$0")"

MODE=${1:-dev}
STATE=~/.local/share/nginx-money
NGINX=(/usr/local/nginx/sbin/nginx -e "$STATE/logs/error.log" -c "$PWD/deploy/nginx/standalone.conf")

cleanup() {
  trap - INT TERM EXIT
  [[ $MODE == prod ]] && "${NGINX[@]}" -s quit 2>/dev/null
  kill 0
}
trap cleanup INT TERM EXIT

venv/bin/python -m backend.app &
case $MODE in
  dev)  (cd frontend && npm run dev) & ;;
  prod) (cd frontend && npm run build)
        mkdir -p "$STATE"/{logs,temp/{client_body,proxy,fastcgi,uwsgi,scgi}}
        "${NGINX[@]}"
        echo "▶ http://127.0.0.1:8080/" ;;
  *)    echo "用法：$0 [dev|prod]" >&2; exit 1 ;;
esac
wait -n
