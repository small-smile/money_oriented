/* 银行详情页图表入口：拉数据 → 前置门控 → 依次跑各 charts/*.js 注册的分区。
 * 拆分后的文件清单与加载顺序见 charts/core.js 顶部说明；本文件必须最后加载，
 * 否则 renderAll 遍历 window.__BANK_SECTIONS 时分区还没注册完。 */

function renderAll(D) {
// 同业对比图里代表"本行"的那条线：换行后跟着换名字，其余同业名保持不变
const SELF = (D._bank && D._bank.shortName) || '渝农商行';

// 生成脚本按 DOM id 给出的分行说明文字（页面里的静态文案是渝农商行版本，换行后要覆盖）
const notes = D._notes || {};

/* .yns-only 里写死的是渝农商行的具体数字（标题、说明段、分红卡片）。换行后：
 *   · _notes 里有同 id 文案的 → 整段被覆盖成本行版本，留着显示；
 *   · 没有对应文案的 → 仍然是渝农商行的数字，隐藏掉。
 * .yns-h-only 是"H 股年报口径"专属块：渝农商 H 股年报只到 2018、A 股年报从 2019 起，两边没有
 * 重叠年份，所以能并排画 A/H 两套环形图；其余 A+H 行同一年两份年报都有，按 A 股优先只画 A 股，
 * 这块对它们恒定无意义，一律隐藏。 */
if (window.COMPANY_CODE !== '601077') {
    document.querySelectorAll('.yns-only').forEach(el => {
        if (!(el.id && notes[el.id])) el.style.display = 'none';
    });
    document.querySelectorAll('.yns-h-only').forEach(el => { el.style.display = 'none'; });
}


Object.keys(KEY_DOM).forEach(function (k) {
    if (!__emptyPayload(D[k])) return;
    // 集中度三张图还能靠港交所口径（holder-concentration-hist）单独画出来（纯 H 股行只有这一份），
    // A 股口径为空不等于整块没数据，别提前占位
    if (k === 'holder-concentration' && !__emptyPayload(D['holder-concentration-hist'])) {
        D[k] = EMPTY_D;
        return;
    }
    KEY_DOM[k].forEach(__stub);
    D[k] = EMPTY_D;
});

// 「历年股东持股集中度」是独立板块、三张图共用同一份数据：数据整份缺失时（如只有 H 股年报、
// F10 没有前十大历史的天津银行/江西银行）别留三块 400px 的"暂无数据"占位撑掉一屏，整块收起。
(function () {
    const sec = document.getElementById('sec-concentration');
    if (!sec) return;
    if (__emptyPayload(D['holder-concentration']) && __emptyPayload(D['holder-concentration-hist'])) {
        sec.style.display = 'none';
    }
})();

// 覆盖页面上的渝农商行静态文案（上面的 .yns-only 门控已经按 notes 决定了哪些块留着）
Object.keys(notes).forEach(function (id) {
    const el = document.getElementById(id);
    if (el) { el.innerHTML = notes[id]; el.style.display = ''; }
});


// 各分区（charts/perf.js / charts/asset.js …）注册进来的图表块，按注册顺序跑。
// 某一块抛异常仍会打断后面的块 —— 与拆分前单文件里的行为一致，便于第一时间发现数据问题。
(window.__BANK_SECTIONS || []).forEach(function (fn) { fn(D, SELF, notes); });
}


(function () {
    // 后端渲染时页面与接口同源，用相对路径（换端口/换机器都不用改代码）；
    // file:// 直接打开时没有同源可言，仍指向本机 5000 端口的开发服务。
    var BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';
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
