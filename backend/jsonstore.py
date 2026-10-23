"""data/ 下的 JSON（成品表 tables/、抓取缓存 raw/、抽数中间件 extract/）统一存在 MySQL 的 json_file 表，
一份文件一行、原文照存（键序、缩进都不动），磁盘上不再留 *.json。表结构见 data/sql/tables/json_file.sql。

读写一律走这里。路径照旧按原来的文件路径给：绝对路径（os.path.join(TABLES_DIR, ...) 拼出来的）
或相对 data/ 的路径（"tables/company_codes.json"）都行，库里的键统一是相对 data/ 的 POSIX 路径，
调用方不用改路径拼法，只把 open/json.load/os.listdir 换成这里的同名动作。

连接配置读环境变量 MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PWD / MYSQL_DB，缺的从仓库根 .env 补。

命令行（仓库根目录下跑；按脚本路径跑，不用 -m，免得先导入整个 backend 包）：
  ./venv/bin/python backend/jsonstore.py import [文件或目录...]   # 磁盘上的 *.json 写进库，缺省整个 data/
  ./venv/bin/python backend/jsonstore.py export <目标目录> [前缀]  # 从库里导回文件（恢复/对照用）
  ./venv/bin/python backend/jsonstore.py ls [前缀]
  ./venv/bin/python backend/jsonstore.py get <路径>               # 原文打到 stdout（node 脚本经它读）
  ./venv/bin/python backend/jsonstore.py put <路径> < 原文        # stdin 原文写进库（node 脚本经它写）
"""
import fnmatch
import json
import os
import sys
import threading

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 需换数据根目录时设环境变量 MONEY_DATA_DIR（与 backend/shared.py 同一口径）
DATA_DIR = os.path.abspath(os.environ.get("MONEY_DATA_DIR") or os.path.join(_BASE_DIR, "data"))
TABLE = "json_file"

_local = threading.local()      # 每线程一条连接：Flask 多线程处理请求，pymysql 连接不能跨线程共用


def _config():
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


def _cursor():
    conn = getattr(_local, "conn", None)
    if conn is None:
        import pymysql
        conn = pymysql.connect(charset="utf8mb4", autocommit=True, **_config())
        _local.conn = conn
    else:
        conn.ping(reconnect=True)
    return conn.cursor()


def key(path):
    """文件路径 → 库里的键（相对 data/ 的 POSIX 路径）。绝对路径必须落在 data/ 之内。"""
    p = os.fspath(path)
    if os.path.isabs(p):
        rel = os.path.relpath(os.path.abspath(p), DATA_DIR)
        if rel == ".." or rel.startswith(".." + os.sep):
            raise ValueError(f"{p} 不在数据目录 {DATA_DIR} 之内")
        p = rel
    return os.path.normpath(p).replace(os.sep, "/")


def path_of(k):
    """库里的键 → 原文件的绝对路径（列目录、glob 返回这种形态，调用方照旧 basename/正则）。"""
    return os.path.join(DATA_DIR, *k.split("/"))


def _like_prefix(prefix):
    return prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def read_text(path):
    """原文；不存在返回 None。"""
    with _cursor() as cur:
        cur.execute(f"SELECT content FROM {TABLE} WHERE path=%s", (key(path),))
        row = cur.fetchone()
    return row[0] if row else None


def read(path, default=None):
    """解析好的对象；不存在返回 default。"""
    text = read_text(path)
    return default if text is None else json.loads(text)


def exists(path):
    with _cursor() as cur:
        cur.execute(f"SELECT 1 FROM {TABLE} WHERE path=%s", (key(path),))
        return cur.fetchone() is not None


def write_text(path, text):
    """原文写进库（同键覆盖）。先在本地校验一遍是合法 JSON，坏数据不进库。"""
    json.loads(text)
    with _cursor() as cur:
        cur.execute(f"INSERT INTO {TABLE} (path, content) VALUES (%s, %s) AS new "
                    f"ON DUPLICATE KEY UPDATE content = new.content", (key(path), text))


def write(path, obj, **dumps_kw):
    """json.dumps(obj, **dumps_kw) 后写进库；dumps_kw 照搬原来写文件时的参数（indent/ensure_ascii…）。"""
    text = json.dumps(obj, **dumps_kw)
    write_text(path, text)
    return text


def delete(path):
    with _cursor() as cur:
        cur.execute(f"DELETE FROM {TABLE} WHERE path=%s", (key(path),))


def keys(prefix=""):
    """前缀下的全部键（含子目录），按键排序。"""
    with _cursor() as cur:
        cur.execute(f"SELECT path FROM {TABLE} WHERE path LIKE %s ORDER BY path",
                    (_like_prefix(prefix),))
        return [r[0] for r in cur.fetchall()]


def listdir(directory):
    """代替 os.listdir：目录下（不含子目录）的文件名，已排序。"""
    d = key(directory).rstrip("/")
    prefix = "" if d == "." else d + "/"
    return [k[len(prefix):] for k in keys(prefix) if "/" not in k[len(prefix):]]


def glob(pattern):
    """代替 glob.glob：只支持文件名部分带通配符（tables/bank_*_annual.json），返回绝对路径、已排序。"""
    d, name = os.path.split(os.fspath(pattern))
    return [os.path.join(d, n) if os.path.isabs(d) else path_of(key(os.path.join(d, n)))
            for n in listdir(d or ".") if fnmatch.fnmatchcase(n, name)]


def _import(targets):
    files = []
    for t in targets:
        t = os.path.abspath(t)
        if os.path.isdir(t):
            for root, dirs, names in os.walk(t):
                dirs[:] = sorted(x for x in dirs if x not in ("node_modules", "__pycache__"))
                files += [os.path.join(root, n) for n in sorted(names) if n.endswith(".json")]
        elif t.endswith(".json"):
            files.append(t)
    for p in files:
        with open(p, encoding="utf-8") as f:
            write_text(p, f.read())
    print(f"写入 {len(files)} 份 JSON → {TABLE}")


def _export(target, prefix=""):
    ks = keys(prefix)
    for k in ks:
        out = os.path.join(target, *k.split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(read_text(k))
    print(f"导出 {len(ks)} 份 JSON → {target}")


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "import":
        _import(args or [DATA_DIR])
    elif cmd == "export" and args:
        _export(args[0], args[1] if len(args) > 1 else "")
    elif cmd == "ls":
        print("\n".join(keys(args[0] if args else "")))
    elif cmd == "get" and args:
        text = read_text(args[0])
        if text is None:
            sys.exit(f"{args[0]} 不存在")
        sys.stdout.buffer.write(text.encode("utf-8"))
    elif cmd == "put" and args:
        write_text(args[0], sys.stdin.buffer.read().decode("utf-8"))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
