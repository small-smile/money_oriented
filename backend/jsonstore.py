"""data/ 下的 JSON（成品表 tables/、抓取缓存 raw/、抽数中间件 extract/）就是磁盘上的 *.json 文件，读写一律走这里。
MySQL 里不存 JSON 原文，只放 data/extract/load_to_mysql.py 从这些文件拆出来的结构化表（data/sql/tables/*.sql）。

路径照旧按原来的文件路径给：绝对路径（os.path.join(TABLES_DIR, ...) 拼出来的）
或相对 data/ 的路径（"tables/company_codes.json"）都行，内部统一换成相对 data/ 的 POSIX 路径（键）。
列目录、glob 只看 *.json。

命令行（仓库根目录下跑；按脚本路径跑，不用 -m，免得先导入整个 backend 包）：
  ./venv/bin/python backend/jsonstore.py ls [前缀]
  ./venv/bin/python backend/jsonstore.py get <路径>               # 原文打到 stdout（node 脚本经它读）
  ./venv/bin/python backend/jsonstore.py put <路径> < 原文        # stdin 原文校验后落盘（node 脚本经它写）
"""
import fnmatch
import json
import os
import sys

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 需换数据根目录时设环境变量 MONEY_DATA_DIR（与 backend/shared.py 同一口径）
DATA_DIR = os.path.abspath(os.environ.get("MONEY_DATA_DIR") or os.path.join(_BASE_DIR, "data"))
_SKIP_DIRS = ("node_modules", "__pycache__")


def key(path):
    """文件路径 → 键（相对 data/ 的 POSIX 路径）。绝对路径必须落在 data/ 之内。"""
    p = os.fspath(path)
    if os.path.isabs(p):
        rel = os.path.relpath(os.path.abspath(p), DATA_DIR)
        if rel == ".." or rel.startswith(".." + os.sep):
            raise ValueError(f"{p} 不在数据目录 {DATA_DIR} 之内")
        p = rel
    return os.path.normpath(p).replace(os.sep, "/")


def path_of(k):
    """键 → 文件的绝对路径（列目录、glob 返回这种形态，调用方照旧 basename/正则）。"""
    return os.path.join(DATA_DIR, *k.split("/"))


def read_text(path):
    """原文；不存在返回 None。"""
    try:
        with open(path_of(key(path)), encoding="utf-8", newline="") as f:
            return f.read()
    except FileNotFoundError:
        return None


def read(path, default=None):
    """解析好的对象；不存在返回 default。"""
    text = read_text(path)
    return default if text is None else json.loads(text)


def exists(path):
    return os.path.isfile(path_of(key(path)))


def write_text(path, text):
    """原文落盘（同名覆盖）。先校验一遍是合法 JSON，坏数据不落盘；写临时文件再改名，读的一方不会读到半截。"""
    json.loads(text)
    target = path_of(key(path))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, target)


def write(path, obj, **dumps_kw):
    """json.dumps(obj, **dumps_kw) 后落盘；dumps_kw 照搬原来写文件时的参数（indent/ensure_ascii…）。"""
    text = json.dumps(obj, **dumps_kw)
    write_text(path, text)
    return text


def delete(path):
    try:
        os.remove(path_of(key(path)))
    except FileNotFoundError:
        pass


def keys(prefix=""):
    """前缀下的全部 *.json 键（含子目录），按键排序。"""
    out = []
    for root, dirs, names in os.walk(DATA_DIR):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        rel = os.path.relpath(root, DATA_DIR)
        base = "" if rel == "." else rel.replace(os.sep, "/") + "/"
        out += [base + n for n in names if n.endswith(".json") and (base + n).startswith(prefix)]
    return sorted(out)


def listdir(directory):
    """代替 os.listdir：目录下（不含子目录）的 *.json 文件名，已排序。"""
    d = path_of(key(directory))
    if not os.path.isdir(d):
        return []
    return sorted(n for n in os.listdir(d) if n.endswith(".json") and os.path.isfile(os.path.join(d, n)))


def glob(pattern):
    """代替 glob.glob：只支持文件名部分带通配符（tables/bank_*_annual.json），返回绝对路径、已排序。"""
    d, name = os.path.split(os.fspath(pattern))
    return [os.path.join(d, n) if os.path.isabs(d) else path_of(key(os.path.join(d, n)))
            for n in listdir(d or ".") if fnmatch.fnmatchcase(n, name)]


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "ls":
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
