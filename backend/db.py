"""MySQL 结构化表的只读连接。表结构见 data/sql/tables/*.sql，数据由 data/extract/load_to_mysql.py
从 data/tables/*.json 拆出（JSON 改了要重跑一次）。连接参数读环境变量 MYSQL_HOST / MYSQL_PORT /
MYSQL_USER / MYSQL_PWD / MYSQL_DB，缺的从仓库根 .env 补。"""
import os
import threading

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_local = threading.local()      # 每线程一条连接：Flask 多线程处理请求，pymysql 连接不能跨线程共用


def config():
    env = {}
    path = os.path.join(_BASE_DIR, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")

    def get(k, default):
        return os.environ.get(k) or env.get(k) or default

    return {"host": get("MYSQL_HOST", "127.0.0.1"), "port": int(get("MYSQL_PORT", "3306")),
            "user": get("MYSQL_USER", "root"), "password": get("MYSQL_PWD", ""),
            "database": get("MYSQL_DB", "money")}


def query(sql, args=None):
    """执行只读查询，返回 [dict]（列名 → 值）；DECIMAL 列是 Decimal，由调用方按需转换。"""
    import pymysql
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = pymysql.connect(charset="utf8mb4", autocommit=True, **config())
        _local.conn = conn
    else:
        conn.ping(reconnect=True)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def number(v):
    """DECIMAL → JSON 数：整数值给 int、否则给 float，NULL 给 None（与成品表 JSON 的写法一致）。"""
    if v is None:
        return None
    f = float(v)
    return int(f) if f.is_integer() else f
