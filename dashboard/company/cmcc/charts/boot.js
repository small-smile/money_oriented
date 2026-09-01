/* 中国移动详情页数据引导 —— 供 dashboard/company/cmcc/*.html 使用
 *
 * 做法与百度页不同：百度页把三份表打包进 data.js（要跑一次 Python），
 * 本页直接 fetch data/tables/telecom_00941_*.json，改数只需改表、刷新页面即可，
 * 不需要任何构建步骤。代价是必须通过本地服务打开（file:// 下 fetch 会被浏览器拦），
 * 与银行页走 /api/company_charts 一样都依赖本地服务，这在本项目里是常态。
 *
 * 用法：页面 <head> 里写
 *     <script src="charts/boot.js" data-page="index"></script>
 * data-page 决定拉完数据后加载哪个 charts/*.js。
 */
(function () {
    var self = document.currentScript
        || Array.prototype.find.call(document.scripts, function (s) {
            return /charts\/boot\.js/.test(s.getAttribute('src') || '');
        });
    var PAGE = self ? self.getAttribute('data-page') : null;
    /* 本脚本在 dashboard/company/cmcc/charts/ 下，数据表在仓库根的 data/tables/ */
    var TABLES = '../../../data/tables/';
    var PARTS = {
        annual: 'telecom_00941_annual.json',
        operating: 'telecom_00941_operating.json',
        profile: 'telecom_00941_profile.json'
    };

    function fail(msg) {
        var box = document.createElement('div');
        box.style.cssText = 'max-width:900px;margin:80px auto;padding:20px 24px;'
            + 'background:#fff5f5;border-left:4px solid #c0392b;border-radius:8px;'
            + 'font:18px/1.8 -apple-system,"Microsoft YaHei",sans-serif;color:#7b241c';
        box.innerHTML = '<b>数据未能加载：</b>' + msg
            + '<br>本页通过 fetch 读取 <code>data/tables/telecom_00941_*.json</code>，'
            + '需要用本地服务打开（例如在仓库根执行 <code>python3 -m http.server</code> 后访问 '
            + '<code>/dashboard/company/cmcc/</code>），直接用 file:// 打开会被浏览器拦截。';
        document.body.insertBefore(box, document.body.firstChild);
    }

    function loadScript(src) {
        return new Promise(function (res, rej) {
            var s = document.createElement('script');
            s.src = src;
            s.onload = res;
            s.onerror = function () { rej(new Error('加载 ' + src + ' 失败')); };
            document.body.appendChild(s);
        });
    }

    function boot() {
        var keys = Object.keys(PARTS);
        Promise.all(keys.map(function (k) {
            return fetch(TABLES + PARTS[k]).then(function (r) {
                if (!r.ok) throw new Error(PARTS[k] + ' HTTP ' + r.status);
                return r.json();
            });
        })).then(function (arr) {
            var payload = {};
            keys.forEach(function (k, i) { payload[k] = arr[i]; });
            window.CMCC = payload;
            return loadScript('charts/common.js').then(function () {
                return PAGE ? loadScript('charts/' + PAGE + '.js') : null;
            });
        }).catch(function (e) {
            fail(e && e.message ? e.message : String(e));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
