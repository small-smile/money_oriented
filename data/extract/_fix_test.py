import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
p = os.path.join(ROOT, "test_backend.py")
s = open(p, encoding="utf-8").read()
if '"ring_label", "sources"' not in s:
    s = s.replace('"ring_alt", "ring_label"}', '"ring_alt", "ring_label", "sources"}')
    open(p, "w", encoding="utf-8").write(s)
    print("patched: added 'sources' to expected key set")
else:
    print("already patched")
