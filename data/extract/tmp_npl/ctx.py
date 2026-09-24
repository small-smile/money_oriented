import re, sys
# usage: ctx.py file regex [before] [after] [maxhits]
f, pat = sys.argv[1], sys.argv[2]
b = int(sys.argv[3]) if len(sys.argv) > 3 else 5
a = int(sys.argv[4]) if len(sys.argv) > 4 else 30
m = int(sys.argv[5]) if len(sys.argv) > 5 else 3
lines = open(f, encoding='utf-8', errors='ignore').read().split('\n')
hits = 0
for i, l in enumerate(lines):
    if re.search(pat, l):
        print(f'===== line {i}')
        for j in range(max(0, i - b), min(len(lines), i + a)):
            s = lines[j].rstrip()
            if s.strip():
                print(f'{j}: {s}')
        hits += 1
        if hits >= m:
            break
