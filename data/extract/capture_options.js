/* Runs the original dashboard/company/bank/charts.js inside a stubbed sandbox and
 * captures every echarts setOption(...) payload keyed by chart-container id.
 * Purpose: extract the real plotted data (as real JS values, no manual retyping)
 * and produce a ground-truth snapshot for later render-diff verification.
 *
 * Usage: node capture_options.js <path-to-charts.js> <out.json>
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const chartsPath = process.argv[2];
const outPath = process.argv[3];
const src = fs.readFileSync(chartsPath, 'utf8');

const results = {};          // id -> last setOption payload
let idSeq = 0;

function fakeEl(id) {
    return {
        __id: id != null ? id : ('__anon' + (idSeq++)),
        style: { setProperty() {}, removeProperty() {} },
        clientWidth: 800,
        clientHeight: 400,
        offsetWidth: 800,
        offsetHeight: 400,
        set innerHTML(v) { /* no-op */ },
        get innerHTML() { return ''; },
        closest() { return null; },
        appendChild() {},
        addEventListener() {},
        removeEventListener() {},
        querySelector() { return null; },
        querySelectorAll() { return []; },
        getAttribute() { return null; },
        setAttribute() {},
    };
}

const instances = new Map();   // el.__id -> instance
function makeInstance(el) {
    const inst = {
        __id: el && el.__id,
        setOption(opt) { if (this.__id != null) results[this.__id] = opt; return this; },
        resize() {}, on() {}, off() {}, dispatchAction() {},
        showLoading() {}, hideLoading() {}, clear() {},
        getWidth() { return 800; }, getHeight() { return 400; },
        getZr() { return { on() {}, off() {} }; },
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
    getElementById(id) { return fakeEl(id); },      // every id "exists" -> all charts render
    querySelector() { return null; },
    querySelectorAll() { return []; },
    documentElement: { style: { setProperty() {} }, clientWidth: 800 },
    addEventListener() {},
    createElement() { return fakeEl(null); },
    body: fakeEl('body'),
};

const windowStub = {
    addEventListener() {}, removeEventListener() {},
    requestAnimationFrame(fn) { return 0; },
    setTimeout() { return 0; }, clearTimeout() {},
    getComputedStyle() { return { getPropertyValue() { return ''; } }; },
    devicePixelRatio: 1,
};

const sandbox = {
    echarts,
    document: documentStub,
    window: windowStub,
    console,
    setTimeout: () => 0,
    clearTimeout: () => {},
    requestAnimationFrame: () => 0,
    Math, JSON, Date, Array, Object, Number, String, Boolean, Set, Map, isNaN, parseFloat, parseInt,
};
sandbox.globalThis = sandbox;
sandbox.self = sandbox;

vm.createContext(sandbox);
vm.runInContext(src, sandbox, { filename: path.basename(chartsPath) });

fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
const ids = Object.keys(results).sort();
console.log('captured charts:', ids.length);
console.log(ids.join('\n'));
