/* 一次性抽取：把 shareholder-switch.js 里内置的 4 家对比银行（农业/招商/民生/天津）
 * 股东页数据，从 JS 字面量导出为 data/tables/company_charts_<code>.json，
 * 供 /api/company_charts?code=<code> 动态下发（与渝农商行 601077 走同一端点）。
 *
 * 与 transform_charts.js 一致的思路：对源文件做文本切片 + 沙箱 eval，
 * 不手工重录数值，避免抄写误差。属迁移用的 codemod：
 * 迁移后 company_charts_<code>.json 即为对比行数据的权威来源，
 * shareholder-switch.js 不再内置 BANKS。
 *
 * 用法：node data/extract/gen_bank_shareholder_data.js
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '../..');
const SRC = path.join(ROOT, 'dashboard/company/bank/shareholder-switch.js');
const OUTDIR = path.join(ROOT, 'data/tables');
const CODES = ['601288', '600036', '600016', '01578'];

const src = fs.readFileSync(SRC, 'utf8');

// 切出 `var BANKS = {};` 到 buildHolders 注释之间的赋值区（含 4 家 BANKS[...] = {...}）
const START = 'var BANKS = {};';
const END = '// ── 由 top10';
const si = src.indexOf(START);
const ei = src.indexOf(END);
if (si < 0 || ei < 0 || ei <= si) {
    throw new Error('未定位到 BANKS 数据块，源文件结构可能已变化');
}
const block = src.slice(si, ei);

// years() 辅助函数在数据块上方定义，沙箱里补一份供 dividend.years9 求值
const prelude =
    'function years(from, to){var a=[];for(var y=from;y<=to;y++)a.push(""+y);return a;}\n';

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(prelude + block, sandbox);
const BANKS = sandbox.BANKS;

CODES.forEach(function (code) {
    const b = BANKS[code];
    if (!b) throw new Error('BANKS 中缺少银行 ' + code);
    const out = path.join(OUTDIR, 'company_charts_' + code + '.json');
    fs.writeFileSync(out, JSON.stringify(b, null, 2) + '\n', 'utf8');
    console.log('wrote', path.relative(ROOT, out));
});
