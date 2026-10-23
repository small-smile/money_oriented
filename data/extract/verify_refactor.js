/* Render-diff: run the data-driven dashboard/company/bank/charts.js in a stubbed sandbox,
 * invoke renderAll(D) with the API payload, capture every setOption, and compare to the
 * ground-truth original_options.json (captured from the pre-refactor charts.js).
 * Any per-chart difference is a regression.
 *
 * Usage: node verify_refactor.js [charts.js path] [bank code]
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { execFileSync } = require('child_process');

/* charts.js 已按主题拆成 dashboard/company/bank/charts/*.js（分区脚本注册进
 * window.__BANK_SECTIONS，charts.js 只剩 renderAll 与取数）。沙箱里没有 <script>，
 * 所以照页面里的顺序把分区文件拼在入口前面；老的单文件路径（如 /tmp 里的备份）照原样读。 */
const PART_ORDER = ['core', 'compare', 'perf', 'asset', 'debt', 'risk',
                    'shareholder', 'holders', 'intro', 'statement', 'switcher'];
function readCharts(entry) {
    const dir = path.join(path.dirname(entry), 'charts');
    if (!fs.existsSync(dir)) return fs.readFileSync(entry, 'utf8');
    return PART_ORDER.map(n => fs.readFileSync(path.join(dir, n + '.js'), 'utf8'))
        .concat(fs.readFileSync(entry, 'utf8')).join('\n;\n');
}

const ROOT = path.resolve(__dirname, '../..');
/* data/ 下的 JSON 原文已进 MySQL json_file 表，经 backend/jsonstore.py 的命令行读写（键为相对 data/ 的路径） */
function jsonstore(args, input) {
    return execFileSync(path.join(ROOT, 'venv/bin/python'), [path.join(ROOT, 'backend/jsonstore.py')].concat(args),
        { cwd: ROOT, input: input, encoding: 'utf8', maxBuffer: 64 << 20 });
}
const chartsPath = process.argv[2] || path.join(ROOT, 'dashboard/company/bank/charts.js');
const code = process.argv[3] || '601077';
const src = readCharts(chartsPath);
const D = JSON.parse(jsonstore(['get', `tables/company_charts_${code}.json`]));
const original = JSON.parse(jsonstore(['get', 'extract/original_options.json']));

const results = {};
let idSeq = 0;
function fakeEl(id) {
    return {
        __id: id != null ? id : ('__anon' + (idSeq++)),
        style: { setProperty() {}, removeProperty() {} },
        clientWidth: 800, clientHeight: 400, offsetWidth: 800, offsetHeight: 400,
        set innerHTML(v) {}, get innerHTML() { return ''; },
        closest() { return null; }, appendChild() {}, addEventListener() {}, removeEventListener() {},
        querySelector() { return null; }, querySelectorAll() { return []; },
        getAttribute() { return null; }, setAttribute() {},
    };
}
const instances = new Map();
function makeInstance(el) {
    const inst = {
        __id: el && el.__id,
        setOption(opt) { if (this.__id != null) results[this.__id] = opt; return this; },
        resize() {}, on() {}, off() {}, dispatchAction() {}, showLoading() {}, hideLoading() {}, clear() {},
        getWidth() { return 800; }, getHeight() { return 400; }, getZr() { return { on() {}, off() {} }; },
    };
    if (el && el.__id != null) instances.set(el.__id, inst);
    return inst;
}
const echarts = {
    init(el) { return makeInstance(el); },
    getInstanceByDom(el) { return el && instances.get(el.__id); },
    graphic: {
        LinearGradient: function (...a) { return { __gradient: a }; },
        RadialGradient: function (...a) { return { __gradient: a }; },
    },
};
const documentStub = {
    getElementById(id) { return fakeEl(id); },
    querySelector() { return null; }, querySelectorAll() { return []; },
    documentElement: { style: { setProperty() {} }, clientWidth: 800 },
    addEventListener() {}, createElement() { return fakeEl(null); }, body: fakeEl('body'),
};
const windowStub = {
    addEventListener() {}, removeEventListener() {}, requestAnimationFrame() { return 0; },
    setTimeout() { return 0; }, clearTimeout() {},
    getComputedStyle() { return { getPropertyValue() { return ''; } }; }, devicePixelRatio: 1,
};
const sandbox = {
    // charts.js 顶层要解析地址栏的 ?code=（window.COMPANY_CODE），沙箱里得给出 location/URLSearchParams
    location: { search: '?code=' + code },
    URLSearchParams,
    echarts, document: documentStub, window: windowStub, console,
    setTimeout: () => 0, clearTimeout: () => {}, requestAnimationFrame: () => 0,
    Math, JSON, Date, Array, Object, Number, String, Boolean, Set, Map, isNaN, parseFloat, parseInt,
    __D__: D,
};
sandbox.globalThis = sandbox; sandbox.self = sandbox;
vm.createContext(sandbox);
vm.runInContext(src, sandbox, { filename: path.basename(chartsPath) });
vm.runInContext('renderAll(__D__);', sandbox);

// compare
const oKeys = Object.keys(original).sort();
const rKeys = Object.keys(results).sort();
let ok = true;
if (oKeys.join(',') !== rKeys.join(',')) {
    ok = false;
    console.log('CHART ID SET MISMATCH');
    console.log('  only in original:', oKeys.filter(k => !rKeys.includes(k)).join(', ') || '(none)');
    console.log('  only in refactor:', rKeys.filter(k => !oKeys.includes(k)).join(', ') || '(none)');
}
for (const id of oKeys) {
    if (!(id in results)) continue;
    const a = JSON.stringify(original[id]);
    const b = JSON.stringify(results[id]);
    if (a !== b) {
        ok = false;
        console.log('DIFF in chart:', id);
        // show first divergence
        let i = 0; while (i < a.length && i < b.length && a[i] === b[i]) i++;
        console.log('  orig …', a.slice(Math.max(0, i - 40), i + 40));
        console.log('  refc …', b.slice(Math.max(0, i - 40), i + 40));
    }
}
console.log(ok ? `PASS — ${rKeys.length} charts identical` : 'FAIL — regressions above');
process.exit(ok ? 0 : 1);
