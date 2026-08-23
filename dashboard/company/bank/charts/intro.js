/* 公司概览：消费投诉、员工人数与人均效能、岗位/学历/年龄结构、董事长与行长薪酬。
 * 由 charts-core.js 的 __section 注册，renderAll 拿到数据后调用；块内代码与拆分前一致。 */

__section(function (D, SELF, notes) {
/* ────── 1j4. 历年处理消费投诉数（件）与客户满意度（%） ────── */
(function () {
    if (!document.getElementById('chart-complaint')) return;   // 仅简介页
    const years3 = D['complaint'].years3;
    const complaints   = D['complaint'].complaints;
    const satisfaction = D['complaint'].satisfaction;

    initChart('chart-complaint')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 } },
        legend: { data: ['处理消费投诉数', '消费投诉处理客户满意度'], bottom: 2, textStyle: { fontSize: 18 } },
        grid: { left: 60, right: 60, top: 40, bottom: 56 },
        xAxis: { type: 'category', data: years3, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '投诉数(件)', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#c0392b', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '满意度(%)', min: 0, max: 100, nameTextStyle: { color: '#2980b9', fontSize: 18 },
              axisLabel: { color: '#2980b9', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '处理消费投诉数', type: 'bar', data: complaints, itemStyle: { color: '#c0392b' },
              barMaxWidth: 60,
              label: { show: true, position: 'top', fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '消费投诉处理客户满意度', type: 'line', yAxisIndex: 1, data: satisfaction, smooth: true, symbolSize: 6,
              lineStyle: { width: 3, color: '#2980b9' }, itemStyle: { color: '#2980b9' },
              endLabel: { show: true, fontSize: 18, color: '#2980b9', formatter: '{c}%' } }
        ]
    });
})();


});

__section(function (D, SELF, notes) {
/* ────── 1l. 员工人数与人均效能 ────── */
(function () {
    const years15 = D['staff'].years15;
    // 员工数：2011–2018 为本行口径「在岗员工」（H 股年报「員工及人力資源管理」）；2019–2025 为本集团口径「在岗员工」（A 股年报「员工和机构情况」，含子公司），2018→2019 口径切换处不连续
    const staff = D['staff'].staff;
    // 人均营业收入/人均归母净利润 = 营业收入/归母净利润(本行历年年度报告「合并利润表」披露值) ÷ 对应口径员工数
    const perOI = D['staff'].perOI;
    const perNP = D['staff'].perNP;

    initChart('chart-staff')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 18 },
                   formatter: p => {
                       const rows = p.map(s => s.seriesName + '：' + s.value +
                           (s.seriesName === '年末员工数' ? ' 人' : ' 万元/人'));
                       return p[0].axisValue + '<br>' + rows.join('<br>');
                   } },
        legend: { data: ['年末员工数', '人均营业收入', '人均归母净利润'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 72, right: 66, top: 46, bottom: 40 },
        xAxis: { type: 'category', data: years15, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: [
            { type: 'value', name: '员工数(人)', min: 0, nameTextStyle: { color: '#95a5a6', fontSize: 18 },
              axisLabel: { color: '#95a5a6', fontSize: 18 }, splitLine: { lineStyle: { color: '#eee' } } },
            { type: 'value', name: '万元/人', min: 0, nameTextStyle: { color: '#c0392b', fontSize: 18 },
              axisLabel: { color: '#555', fontSize: 18 }, splitLine: { show: false } }
        ],
        series: [
            { name: '年末员工数', type: 'bar', data: staff, itemStyle: { color: '#d5dbdb' },
              barWidth: '55%', z: 1 },
            { name: '人均营业收入', type: 'line', yAxisIndex: 1, data: perOI, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
              endLabel: { show: true, fontSize: 18, color: '#c0392b', formatter: '{c}' } },
            { name: '人均归母净利润', type: 'line', yAxisIndex: 1, data: perNP, smooth: true, symbolSize: 6, z: 3,
              lineStyle: { width: 3, color: '#e67e22' }, itemStyle: { color: '#e67e22' },
              endLabel: { show: true, fontSize: 18, color: '#e67e22', formatter: '{c}' } }
        ]
    });
})();

});

__section(function (D, SELF, notes) {

/* ────── intro.html · 员工岗位结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-role')) return;
    // 数据来源：2025 年报「第四章 五、（一）员工情况」PDF 第 119 页；本行口径合计 13,853 人
    const roles = D['staff-role'].roles;
    initChart('chart-staff-role')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: roles,
            color: ['#6c3483', '#af7ac5', '#c0392b', '#e67e22']
        }]
    });
})();

/* ────── intro.html · 员工学历结构（饼图） ────── */
(function () {
    if (!document.getElementById('chart-staff-edu')) return;
    const edu = D['staff-edu'].edu;
    initChart('chart-staff-edu')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'item', textStyle: { fontSize: 18 },
            formatter: p => `${p.marker}${p.name}<br><b>${p.value.toLocaleString()} 人</b>（${p.percent}%）` },
        legend: { top: 8, textStyle: { fontSize: 18 } },
        series: [{
            type: 'pie', radius: ['38%', '68%'], center: ['50%', '58%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 },
            label: { fontSize: 17, color: '#333',
                formatter: p => `${p.name}\n${p.value.toLocaleString()}（${p.percent}%）` },
            labelLine: { length: 12, length2: 10 },
            data: edu,
            color: ['#6c3483', '#95a5a6', '#af7ac5']
        }]
    });
})();

/* ────── intro.html · 历年董事长 / 行长薪酬披露（2010-2025，税前，万元） ──────
 * 2010-2018: H股03618年报「董事、监事及高级管理层人员」章节；2019-2025: A股601077年报「公司治理报告」章节。
 * 董事长换人：2022年4月刘建忠→谢文辉；2024年10月谢文辉离任后行长隋军代行董事长职务
 * （年报"董事长及行长"章节原文："谢文辉先生于2024年10月离任后，董事会推举隋军先生代行董事长职务"，
 * 2025年"隋军...并经董事会推举短暂代行董事长职务"），2024/2025两年董事长栏均取隋军的行长薪酬数
 * （年报薪酬表职务栏对代行期间未单列"代行董事长"报酬，隋军实际以行长身份领取同一份薪酬）；
 * 2026-01-08刘小军任职资格获监管核准，但2025年度隋军仍是全年代行董事长的实际人选，故2025年
 * 董事长栏仍用隋军59.75万元，刘小军42.07万元(候任身份取得)在图中不作为该年"董事长"代表数值。
 * 行长换人：2013年12月谭远胜退休→谢文辉（任职资格待核准，2013年谢文辉当年确实未在任何身份下
 * 领取报酬，年报本身未披露任何数字，非因职务代行而留空，故该点保留空缺并在note注明原因）；
 * 2014-2023年3月为谢文辉；2023年4月起为隋军。
 * 注意：2010-2021年董事长(刘建忠)与行长(谢文辉/谭远胜)始终是两个不同的人，2014年报"董事长及行长"
 * 一节原文强调"角色相互分立"；"一人兼两职"发生在2022年(谢文辉升任董事长兼行长)及2024-2025年
 * (隋军以行长身份代行董事长职务)——这几年两条线数值相同，图上用虚线叠画并标注"一人兼两职/代行"。
 * 各年数值均为年报"税前薪酬合计"列，历年年报均注明非最终考核数。 */
(function () {
    if (!document.getElementById('chart-chairman-pay')) return;
    const years = D['chairman-pay'].years;
    const chairmanNames = D['chairman-pay'].chairmanNames;
    const chairmanPay   = D['chairman-pay'].chairmanPay;
    // 2013 谢文辉当年刚获聘行长、任职资格未获监管核准，年报本身未披露其任何报酬数（非代行职务留空，是确无数据）
    const presidentNames = D['chairman-pay'].presidentNames;
    const presidentPay   = D['chairman-pay'].presidentPay;
    // 一人兼两职/代行区间：用虚线线型标注两条线数值相同的年份。索引由数据 dashedIdx 提供
    // （编辑口径，需语义读年报判定同一人兼任，不能靠数值相等推断，故随数据下发）；缺省则无虚线。
    const dashedIdx = new Set(D['chairman-pay'].dashedIdx || []);
    // 换任/代行标注线：由数据 marks 提供 [{xAxis, name}]，缺省则不画标注线（各行专属）
    const payMarks = D['chairman-pay'].marks || [];

    initChart('chart-chairman-pay')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', textStyle: { fontSize: 18 },
            formatter: p => `<b>${p[0].axisValue} 年</b><br>` + p.map(x => {
                const idx = x.dataIndex;
                const who = x.seriesIndex === 0 ? chairmanNames[idx] : presidentNames[idx];
                const note = dashedIdx.has(idx) ? '（一人兼两职/代行）' : '';
                return x.value == null ? '' : `${x.marker}${x.seriesName}（${who}）${note}：${x.value} 万元`;
            }).filter(Boolean).join('<br>') },
        legend: { data: ['董事长', '行长'], top: 4, textStyle: { fontSize: 18 } },
        grid: { left: 68, right: 30, top: 52, bottom: 40 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 18, color: '#555' } },
        yAxis: { type: 'value', name: '万元', min: 0, nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' }, splitLine: { lineStyle: { color: '#eee' } } },
        series: [
            {
                name: '董事长', type: 'line', data: chairmanPay, smooth: true, symbolSize: 8,
                lineStyle: {
                    width: 2.5, color: '#c9a24a',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#c9a24a' },
                markLine: {
                    symbol: 'none', silent: true,
                    lineStyle: { color: '#999', type: 'dashed', width: 1 },
                    label: { fontSize: 16, color: '#888', formatter: p => p.name },
                    data: payMarks
                },
                label: { show: true, position: 'top', fontSize: 15, color: '#8a6d1f', formatter: '{c}' }
            },
            {
                name: '行长', type: 'line', data: presidentPay, smooth: true, symbolSize: 8,
                connectNulls: true,   // 仅2013年谢文辉当年确无薪酬数据(非代行留空), 跨越该点连线并在note说明
                lineStyle: {
                    width: 2.5, color: '#2980b9',
                    type: p => dashedIdx.has(p.dataIndex) || dashedIdx.has(p.dataIndex - 1) ? 'dashed' : 'solid'
                },
                itemStyle: { color: '#2980b9' },
                label: { show: true, position: 'bottom', fontSize: 15, color: '#1f618d',
                         formatter: p => p.value == null ? '' : p.value }
            }
        ]
    });
})();

/* ────── intro.html · 员工年龄结构（横向堆叠条） ────── */
(function () {
    if (!document.getElementById('chart-staff-age')) return;
    const buckets = D['staff-age'].buckets;
    const vals    = D['staff-age'].vals;
    const total   = vals.reduce((s, v) => s + v, 0);
    initChart('chart-staff-age')?.setOption({
        backgroundColor: '#fff',
        textStyle: { fontSize: 18 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            textStyle: { fontSize: 18 },
            formatter: p => {
                const x = p[0];
                const pct = (x.value / total * 100).toFixed(1);
                return `<b>${x.axisValue}</b><br>${x.marker}人数：${x.value.toLocaleString()} 人（${pct}%）`;
            } },
        grid: { left: 100, right: 60, top: 20, bottom: 40 },
        xAxis: { type: 'value', name: '人数', nameTextStyle: { fontSize: 18 },
                 axisLabel: { fontSize: 18, color: '#555' },
                 splitLine: { lineStyle: { color: '#eee' } } },
        yAxis: { type: 'category', data: buckets, inverse: true,
                 axisLabel: { fontSize: 18, color: '#333' } },
        series: [{
            type: 'bar', data: vals,
            itemStyle: { color: '#6c3483' },
            barWidth: 26,
            label: { show: true, position: 'right', fontSize: 17, color: '#333',
                formatter: p => `${p.value.toLocaleString()}（${(p.value / total * 100).toFixed(1)}%）` }
        }]
    });
})();
});
