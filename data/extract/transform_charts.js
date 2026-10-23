/* Codemod: turn dashboard/company/bank/charts.js data-literals into reads from an
 * injected D payload (served by /api/company_charts), keeping ALL presentation,
 * derivations and layout untouched.
 *   - named data consts  ->  const NAME = D['block'].NAME;
 *   - 4 inline datasets (depterm / 5tier / cf / geo) -> exact-string swaps
 *   - all IIFEs wrapped in  function renderAll(D){...}
 *   - axios bootstrap appended
 * Output: charts.refactored.js (original left intact until render-diff passes).
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '../..');
/* data/ 下的 JSON 原文已进 MySQL json_file 表，经 backend/jsonstore.py 的命令行读写（键为相对 data/ 的路径） */
function jsonstore(args, input) {
    return execFileSync(path.join(ROOT, 'venv/bin/python'), [path.join(ROOT, 'backend/jsonstore.py')].concat(args),
        { cwd: ROOT, input: input, encoding: 'utf8', maxBuffer: 64 << 20 });
}
const SRC = path.join(ROOT, 'dashboard/company/bank/charts.js');
const OUT = path.join(ROOT, 'dashboard/company/bank/charts.refactored.js');
const D = JSON.parse(jsonstore(['get', 'tables/company_charts_601077.json']));

let src = fs.readFileSync(SRC, 'utf8');

/* ---- Step A: 4 inline datasets (no named const) — exact-string swaps ---- */
const inline = [
    ['value: 7640.86,', "value: D['depterm'].vals[0],"],
    ['value: 2601.74,', "value: D['depterm'].vals[1],"],
    ['value: 44.68,',   "value: D['depterm'].vals[2],"],
    ['value: 777351.2,', "value: D['5tier'].vals[0],"],
    ['value: 11346.4,',  "value: D['5tier'].vals[1],"],
    ['value: 3759.4,',   "value: D['5tier'].vals[2],"],
    ['value: 2888.4,',   "value: D['5tier'].vals[3],"],
    ['value: 1941.6,',   "value: D['5tier'].vals[4],"],
    ['data: [22569.6, -19134.4, 15532.8, -18595.7],', "data: D['cf'].vals,"],
    ["data: ['存款', '贷款', '资产'],", "data: D['geo'].cats,"],
    ['data: [73.30, 50.78, 52.60],', "data: D['geo'].county,"],
    ['data: [26.70, 49.22, 47.40],', "data: D['geo'].urban,"],
];
for (const [find, repl] of inline) {
    const n = src.split(find).length - 1;
    if (n !== 1) throw new Error(`inline swap expected 1 occurrence, got ${n}: ${find}`);
    src = src.replace(find, repl);
}

/* ---- helpers ---- */
// scan RHS of a `const NAME = <literal>;` and return index of the terminating ;
function rhsEnd(text, i) {
    let depth = 0, s = null;
    for (; i < text.length; i++) {
        const c = text[i];
        if (s) {                                   // inside string
            if (c === '\\') { i++; continue; }
            if (c === s) s = null;
            continue;
        }
        if (c === '/' && text[i + 1] === '/') {     // line comment
            i = text.indexOf('\n', i); if (i < 0) return -1; continue;
        }
        if (c === '/' && text[i + 1] === '*') {     // block comment
            i = text.indexOf('*/', i + 2); if (i < 0) return -1; i++; continue;
        }
        if (c === '"' || c === "'" || c === '`') { s = c; continue; }
        if (c === '(' || c === '[' || c === '{') depth++;
        else if (c === ')' || c === ']' || c === '}') depth--;
        else if (c === ';' && depth === 0) return i;
    }
    return -1;
}

/* ---- Step B: named data consts, scoped per IIFE chunk ---- */
// boundaries: every IIFE `(function` at column 0. Preamble (initChart) stays out.
const starts = [];
const re = /^\(function/gm;
let m;
while ((m = re.exec(src))) starts.push(m.index);
if (!starts.length) throw new Error('no IIFE found');

const preamble = src.slice(0, starts[0]);
let body = '';
const seen = {};
const notFound = [];

for (let k = 0; k < starts.length; k++) {
    let chunk = src.slice(starts[k], k + 1 < starts.length ? starts[k + 1] : src.length);

    const idm = chunk.match(/chart-([a-z0-9-]+)/);
    let key = null;
    if (idm) {
        const base = idm[1];
        if (seen[base]) { key = base + '_' + seen[base]; seen[base]++; }
        else { seen[base] = 1; key = base; }
    }

    if (key && D[key]) {
        const edits = [];
        for (const name of Object.keys(D[key])) {
            const cre = new RegExp('\\n {4}const ' + name + '\\b');
            const cm = cre.exec(chunk);
            if (!cm) { notFound.push(`${key}.${name}`); continue; }
            const eq = chunk.indexOf('=', cm.index);
            const end = rhsEnd(chunk, eq + 1);
            if (eq < 0 || end < 0) throw new Error(`RHS scan failed: ${key}.${name}`);
            edits.push({ start: eq + 1, end, name });
        }
        // apply last->first so offsets stay valid
        edits.sort((a, b) => b.start - a.start);
        for (const e of edits) {
            chunk = chunk.slice(0, e.start) + ` D['${key}'].${e.name}` + chunk.slice(e.end);
        }
    }
    body += chunk;
}

if (notFound.length) console.log('NOTE consts not found in chunk (expected for 5tier/cf vals):', notFound.join(', '));

/* ---- Step C + D: wrap body in renderAll(D) and append axios bootstrap ---- */
const bootstrap = `
(function () {
    var API = 'http://127.0.0.1:5000/api/company_charts';
    if (typeof axios !== 'undefined') {
        axios.get(API).then(function (res) {
            if (!res.data || res.data.code !== 200) throw new Error('company_charts load failed');
            renderAll(res.data.data);
        }).catch(function (e) { console.error('company_charts fetch error', e); });
    }
})();
`;

const out = preamble + 'function renderAll(D) {\n' + body + '\n}\n' + bootstrap;
fs.writeFileSync(OUT, out);
console.log('wrote', OUT, out.length, 'bytes; IIFEs=', starts.length);
