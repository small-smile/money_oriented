/* 银行详情页图表入口：拉数据 → 前置门控 → 依次跑各 charts/*.js 注册的分区。
 * 拆分后的文件清单与加载顺序见 charts/core.js 顶部说明；本文件必须最后加载，
 * 否则 renderAll 遍历 window.__BANK_SECTIONS 时分区还没注册完。 */

function renderAll(D) {
// 同业对比图里代表"本行"的那条线：换行后跟着换名字，其余同业名保持不变
const SELF = (D._bank && D._bank.shortName) || '渝农商行';

// 按 DOM id 下发的本行文案（年报摘录的说明段、KPI 卡、表格、含行名的标题），由后端从各行覆盖层拼出
const notes = D._notes || {};

/* .bank-specific 是「每家行各写各的」文案块：模板里只留带 id 的空壳，内容取自本行 _notes 里
 * 同 id 的那段；本行没给的整块隐藏。所有银行同一套规则，模板里不写任何一家的具体数字。 */
document.querySelectorAll('.bank-specific').forEach(el => {
    if (!(el.id && notes[el.id])) el.style.display = 'none';
});


Object.keys(KEY_DOM).forEach(function (k) {
    if (!__emptyPayload(D[k])) return;
    KEY_DOM[k].forEach(__stub);
    D[k] = EMPTY_D;
});

// 文案填进页面（.bank-specific 空壳，以及模板里带通用文字、需按本行改写的标题等）
Object.keys(notes).forEach(function (id) {
    const el = document.getElementById(id);
    if (el) { el.innerHTML = notes[id]; el.style.display = ''; }
});


// 各分区（charts/perf.js / charts/asset.js …）注册进来的图表块，按注册顺序跑。
// 某一块抛异常仍会打断后面的块 —— 与拆分前单文件里的行为一致，便于第一时间发现数据问题。
(window.__BANK_SECTIONS || []).forEach(function (fn) { fn(D, SELF, notes); });
}


(function () {
    // 页面与接口同源，一律用相对路径（nginx 转发、换端口/换机器都不用改代码）。
    var BASE = '';
    var API = BASE + '/api/company_charts?code=' + window.COMPANY_CODE;
    if (typeof axios !== 'undefined') {
        axios.get(API).then(function (res) {
            // 后端 404 / 无数据：整页图位换占位说明，不调 renderAll（拿 undefined 解构会整页崩）
            if (!res.data || res.data.code !== 200 || !res.data.data) { stubAll(); return; }
            window.__companyD = res.data.data;   // 缓存原始数据供股东页银行切换器复用
            window.__applyBankIdentity(res.data.data);
            renderAll(res.data.data);
        }).catch(function (e) { console.error('company_charts fetch error', e); stubAll(); });
    }
})();
