#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：向 bank_002142_detail_manual.json 插入 bondpay 与 _notes（宁波银行）。"""
import json, collections, io, os, re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bank_002142_detail_manual.json')

with io.open(P, encoding='utf-8') as f:
    d = json.load(f, object_pairs_hook=collections.OrderedDict)

years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
N = [None] * 8

bondpay = collections.OrderedDict()
bondpay["years"]     = years
bondpay["balNcd"]    = [1520.98, 1301.87, 885.03, 2963.57, 3213.58, 2434.96, 2842.46, 3427.10]
bondpay["balBond"]   = [563.39, 826.99, 989.40, 860.07, 1154.87, 1275.87, 1491.51, 1170.37]
bondpay["balTotal"]  = [2084.37, 2128.86, 1874.43, 3823.64, 4368.45, 3710.83, 4333.97, 4597.47]
bondpay["avgNcd"]    = list(N)
bondpay["avgBond"]   = list(N)
bondpay["avgTotal"]  = [1919.24, 1873.01, 1853.08, 2544.02, 3842.10, 3645.08, 3768.53, 4629.97]
bondpay["rateNcd"]   = list(N)
bondpay["rateBond"]  = list(N)
bondpay["rateTotal"] = [4.39, 3.71, 3.40, 3.10, 2.76, 2.60, 2.47, 2.04]
bondpay["bonds"] = [
    {"name": "12 次级债券", "issueDate": "2012-11-22", "tenor": "15年（第10年末可赎回）", "coupon": 5.75, "amount": 30.00, "maturity": "2027-11", "status": "已赎回"},
    {"name": "13 金融债券（品种一，5年期）", "issueDate": "2013-04-16", "tenor": "5年", "coupon": 4.70, "amount": 50.00, "maturity": "2018-04", "status": "已到期"},
    {"name": "13 金融债券（品种二，10年期）", "issueDate": "2013-04-16", "tenor": "10年", "coupon": 5.13, "amount": 30.00, "maturity": "2023-04", "status": "已到期"},
    {"name": "15 二级资本债券", "issueDate": "2015-05-26", "tenor": "10年（第5年末可赎回）", "coupon": 5.19, "amount": 70.00, "maturity": "2025-05", "status": "已赎回"},
    {"name": "15 金融债券（品种一）", "issueDate": "2015-07-03", "tenor": "3年", "coupon": 4.12, "amount": 5.00, "maturity": "2018-07", "status": "已到期"},
    {"name": "15 金融债券（品种二）", "issueDate": "2015-09-09", "tenor": "3年", "coupon": 3.98, "amount": 95.00, "maturity": "2018-09", "status": "已到期"},
    {"name": "宁行转债（A股可转债，票息逐年累进 0.2/0.4/0.8/1.2/1.6/2.0%）", "issueDate": "2017-12-05", "tenor": "6年", "coupon": 0.20, "amount": 100.00, "maturity": "2023-12", "status": "已赎回"},
    {"name": "17 二级资本债券", "issueDate": "2017-12-06", "tenor": "10年（第5年末可赎回）", "coupon": 4.80, "amount": 100.00, "maturity": "2027-12", "status": "已赎回"},
    {"name": "18 金融债券（第一期）", "issueDate": "2018-03-20", "tenor": "3年", "coupon": 5.15, "amount": 100.00, "maturity": "2021-03", "status": "已到期"},
    {"name": "18 金融债券（第二期）", "issueDate": "2018-05-21", "tenor": "3年", "coupon": 4.70, "amount": 80.00, "maturity": "2021-05", "status": "已到期"},
    {"name": "18 金融债券（第三期）", "issueDate": "2018-07-24", "tenor": "3年", "coupon": 4.30, "amount": 60.00, "maturity": "2021-07", "status": "已到期"},
    {"name": "18 绿色金融债券", "issueDate": "2018-10-24", "tenor": "3年", "coupon": 3.97, "amount": 30.00, "maturity": "2021-10", "status": "已到期"},
    {"name": "19 金融债券", "issueDate": "2019-01-14", "tenor": "3年", "coupon": 3.50, "amount": 60.00, "maturity": "2022-01", "status": "已到期"},
    {"name": "19 永赢金租金融债券", "issueDate": "2019-03-13", "tenor": "3年", "coupon": 3.80, "amount": 20.00, "maturity": "2022-03", "status": "已到期"},
    {"name": "19 二级资本债券", "issueDate": "2019-07-10", "tenor": "10年（第5年末可赎回）", "coupon": 4.40, "amount": 100.00, "maturity": "2029-07", "status": "已赎回"},
    {"name": "19 小微金融债券（品种一）", "issueDate": "2019-08-08", "tenor": "3年", "coupon": 3.46, "amount": 60.00, "maturity": "2022-08", "status": "已到期"},
    {"name": "19 小微金融债券（品种二）", "issueDate": "2019-10-14", "tenor": "3年", "coupon": 3.46, "amount": 60.00, "maturity": "2022-10", "status": "已到期"},
    {"name": "19 宁波银行小微债 03（品种三）", "issueDate": "2019-10-14", "tenor": "5年", "coupon": 3.80, "amount": 10.00, "maturity": "2024-10", "status": "已到期"},
    {"name": "20 永赢金租金融债券", "issueDate": "2020-02-25", "tenor": "3年", "coupon": 3.25, "amount": 10.00, "maturity": "2023-02", "status": "已到期"},
    {"name": "20 宁波银行小微债 01（品种一）", "issueDate": "2020-03-04", "tenor": "3年", "coupon": 2.92, "amount": 55.00, "maturity": "2023-03", "status": "已到期"},
    {"name": "20 宁波银行小微债 02（品种二）", "issueDate": "2020-03-04", "tenor": "5年", "coupon": 3.10, "amount": 15.00, "maturity": "2025-03", "status": "已到期"},
    {"name": "20 金融债券", "issueDate": "2020-04-09", "tenor": "3年", "coupon": 2.40, "amount": 50.00, "maturity": "2023-04", "status": "已到期"},
    {"name": "20 宁波银行二级资本债券", "issueDate": "2020-08-06", "tenor": "10年（第5年末可赎回）", "coupon": 4.10, "amount": 100.00, "maturity": "2030-08", "status": "已赎回"},
    {"name": "21 宁波银行 01（金融债券）", "issueDate": "2021-04-08", "tenor": "3年", "coupon": 3.48, "amount": 50.00, "maturity": "2024-04", "status": "已到期"},
    {"name": "21 宁波银行二级 01", "issueDate": "2021-06-03", "tenor": "10年（第5年末可赎回）", "coupon": 3.87, "amount": 60.00, "maturity": "2031-06", "status": "存续"},
    {"name": "21 宁波银行二级 02", "issueDate": "2021-07-08", "tenor": "10年（第5年末可赎回）", "coupon": 3.68, "amount": 35.00, "maturity": "2031-07", "status": "存续"},
    {"name": "22 宁波银行 01（金融债券）", "issueDate": "2022-02-16", "tenor": "3年", "coupon": 2.78, "amount": 100.00, "maturity": "2025-02", "status": "已到期"},
    {"name": "22 宁波银行 02（金融债券）", "issueDate": "2022-05-06", "tenor": "3年", "coupon": 2.84, "amount": 100.00, "maturity": "2025-05", "status": "已到期"},
    {"name": "22 宁波银行 03（金融债券）", "issueDate": "2022-06-09", "tenor": "3年", "coupon": 2.81, "amount": 100.00, "maturity": "2025-06", "status": "已到期"},
    {"name": "22 宁波银行二级资本债 01", "issueDate": "2022-08-02", "tenor": "10年（第5年末可赎回）", "coupon": 3.24, "amount": 220.00, "maturity": "2032-08", "status": "存续"},
    {"name": "22 宁波银行 04（金融债券）", "issueDate": "2022-11-03", "tenor": "3年", "coupon": 2.48, "amount": 100.00, "maturity": "2025-11", "status": "已到期"},
    {"name": "23 宁波银行 01（金融债券）", "issueDate": "2023-04-13", "tenor": "3年", "coupon": 2.83, "amount": 100.00, "maturity": "2026-04", "status": "存续"},
    {"name": "23 宁波银行 02（金融债券）", "issueDate": "2023-05-17", "tenor": "3年", "coupon": 2.78, "amount": 150.00, "maturity": "2026-05", "status": "存续"},
    {"name": "23 宁波银行永续债 01（其他权益工具，不计入余额）", "issueDate": "2023-07-06", "tenor": "无固定期限（每5年调整票面利率）", "coupon": 3.45, "amount": 100.00, "maturity": "无固定期限", "status": "存续"},
    {"name": "23 永赢金租债", "issueDate": "2023-12-15", "tenor": "3年", "coupon": 2.95, "amount": 15.00, "maturity": "2026-12", "status": "存续"},
    {"name": "24 永赢金租债 01", "issueDate": "2024-02-28", "tenor": "3年", "coupon": None, "amount": 30.00, "maturity": "2027-02", "status": "存续"},
    {"name": "24 永赢金租债 02", "issueDate": "2024-04-24", "tenor": "3年", "coupon": None, "amount": 30.00, "maturity": "2027-04", "status": "存续"},
    {"name": "24 宁波银行二级资本债 01", "issueDate": "2024-05-13", "tenor": "10年（第5年末可赎回）", "coupon": None, "amount": 140.00, "maturity": "2034-05", "status": "存续"},
    {"name": "24 永赢金租债 03", "issueDate": "2024-06-13", "tenor": "3年", "coupon": None, "amount": 15.00, "maturity": "2027-06", "status": "存续"},
    {"name": "24 宁波银行二级资本债 02", "issueDate": "2024-09-19", "tenor": "10年（第5年末可赎回）", "coupon": None, "amount": 100.00, "maturity": "2034-09", "status": "存续"},
    {"name": "24 永赢金租债 04", "issueDate": "2024-11-19", "tenor": "3年", "coupon": None, "amount": 30.00, "maturity": "2027-11", "status": "存续"},
    {"name": "宁惠 2024 年第一期个人消费贷款 ABS（优先级，宁银消费金融发起）", "issueDate": "2024-12-03", "tenor": None, "coupon": None, "amount": 18.76, "maturity": None, "status": "已到期"},
    {"name": "24 宁银消费金融债 01", "issueDate": "2024-12-04", "tenor": "3年", "coupon": None, "amount": 15.00, "maturity": "2027-12", "status": "存续"},
    {"name": "25 永赢金租债 01", "issueDate": "2025-02-20", "tenor": "3年", "coupon": None, "amount": 30.00, "maturity": "2028-02", "status": "存续"},
    {"name": "25 宁波银行二级资本债 01", "issueDate": "2025-03-25", "tenor": "10年（第5年末可赎回）", "coupon": None, "amount": 89.00, "maturity": "2035-03", "status": "存续"},
    {"name": "25 永赢金租债 02", "issueDate": "2025-04-23", "tenor": "3年", "coupon": None, "amount": 20.00, "maturity": "2028-04", "status": "存续"},
    {"name": "25 宁银消费金融债 01", "issueDate": "2025-04-25", "tenor": "1年", "coupon": None, "amount": 10.00, "maturity": "2026-04", "status": "存续"},
    {"name": "25 宁波银行科创债 01", "issueDate": "2025-07-05", "tenor": "5年", "coupon": None, "amount": 30.00, "maturity": "2030-07", "status": "存续"},
    {"name": "25 永赢金租债 03", "issueDate": "2025-07-09", "tenor": "3年", "coupon": None, "amount": 20.00, "maturity": "2028-07", "status": "存续"},
    {"name": "25 宁银消费金融债 02", "issueDate": "2025-07-10", "tenor": "1年", "coupon": None, "amount": 15.00, "maturity": "2026-07", "status": "存续"},
    {"name": "25 宁波银行永续债 01（其他权益工具，不计入余额）", "issueDate": "2025-09-12", "tenor": "无固定期限（每5年调整票面利率）", "coupon": 2.30, "amount": 100.00, "maturity": "无固定期限", "status": "存续"},
]

NOTE_SRC = "出处：宁波银行A股年度报告（深交所披露）2018、2019、2020、2021、2022、2023、2024、2025 八份，宁波银行仅在深交所上市（002142），无H股年报，全部数据取自各年A股年报当年本期列，无缺失年份、未使用可比列。平均余额与平均付息率取自「管理层讨论与分析－利息支出／付息负债平均余额及平均付息率」表的「应付债券」行，该表历年仅披露应付债券合计一行、未按同业存单与非存单债券拆分，故avgTotal／rateTotal有全部8年数据，而avgNcd／avgBond／rateNcd／rateBond全部为null（8年均未披露，不估算、不倒算）。期末余额取自财务报表附注「应付债券」：2018年报附注五、29，2019年报五、26，2020年报五、24，2021年报五、24，2022、2023、2024、2025年报均为五、22（附注序号逐年漂移，已逐年核对）。该附注按「应付金融债券／次级债券／二级资本债券／可转换公司债券／资产支持证券／同业存单」分项列示并单列应计利息，故balNcd直接取同业存单余额，balTotal取资产负债表「应付债券」账面价值（含应计利息），balBond＝balTotal－balNcd为倒算值，等于金融债券＋次级债＋二级资本债＋可转债＋资产支持证券＋应计利息（同业存单以贴现方式发行、不含应计利息，应计利息全额归入balBond）；2018年报应计利息一栏披露为「不适用」，该年balTotal即各分项之和2,084.37亿元。口径：全部为合并（本集团）口径，包含子公司永赢金融租赁与宁银消费金融发行的金融债券及资产支持证券，未采用本行口径。单位：2018、2019年报以人民币千元列示，除以100,000换算为亿元；2020—2025年报以人民币百万元列示，除以100换算为亿元，均保留2位小数；利率／付息率保留2位小数。同业存单年报仅披露实际利率区间而非票面利率（2025年0.5%—3.37%、2024年1.65%—2.44%），区间值不能作为rateNcd，故未采用。bonds为八份年报附注逐笔披露的债券汇总去重后共51只（按发行日排序），涵盖次级债券、金融债券、二级资本债券、小微／绿色／科创专项金融债、子公司永赢金租与宁银消费金融的金融债券、A股可转债「宁行转债」，以及1单「宁惠2024年第一期个人消费贷款资产支持证券」优先级（计入应付债券，发行面值18.76亿元，2024年末余额14.85亿元、2025年末归零故status为已到期，期限／票面利率／到期日年报未披露记null）；不含同业存单（逐笔不披露，仅以balNcd体现）。另将2只永续债列入bonds并在name中标注「其他权益工具，不计入余额」——23宁波银行永续债01（2023-07-06、3.45%、100亿元）与25宁波银行永续债01（2025-09-12、2.30%、100亿元），取自附注「其他权益工具」（2025年报附注五、27.2），两者不计入balBond／balTotal；2015年48.5亿元4.60%与2018年100亿元5.30%优先股不属于债务证券，全部排除。amount为发行面值（亿元），status按2025年末状态判断；宁行转债coupon取第一年票面利率0.20%，逐年累进票息（0.2/0.4/0.8/1.2/1.6/2.0%）在name中标注，其2019年8月22日停止转股、转股率99.89%、剩余面值10,837,000元被赎回，故status为已赎回、maturity记原定到期2023-12。重要缺口：2024、2025年报取消了逐笔债券的票面利率披露（仅永续债披露票面利率），故2024—2025年发行的15只债券coupon全部为null；2018—2023年报附注脚注提供了此前各只债券的票面利率，已逐条采用。跨年披露冲突及取值：（1）22宁波银行02金融债券发行日，2022年报表格与脚注(16)均记2022/5/11，2023—2025年报记2022/5/6，取2022-05-06；（2）22宁波银行二级资本债01发行日，2022年报表格记2022/8/2、脚注(17)记2022年8月4日，取表格的2022-08-02；（3）23宁波银行01／02金融债券期限，2023、2024年报表格及2023年报脚注记3年，2025年报表格记5年，取3年（到期2026-04／2026-05）；（4）15二级资本债券发行日，2018年报记2015/5/27，2019—2021年报记2015/5/26，取2015-05-26。"
NOTE_HTML = "宁波银行已发行债务证券以<b>同业存单</b>为绝对主体：2025年末应付债券合计<b>4,597.47亿元</b>，其中同业存单3,427.10亿元（占<b>74.5%</b>），其余1,170.37亿元为金融债券、二级资本债券与资产支持证券；2018年末合计仅2,084.37亿元，八年扩张约1.2倍，中途在2020年一度回落至1,874.43亿元低点（同业存单压降至885.03亿元），2021年又急增至3,823.64亿元（同业存单2,963.57亿元），主动负债的摆动幅度很大。成本端单边下行：应付债券平均付息率从2018年的<b>4.39%</b>降至2025年的<b>2.04%</b>（<b>-235BP</b>），除市场利率下行外，还受益于5.19%、4.80%、4.40%、4.10%四只高息二级资本债券先后在第5年末行使赎回权退出，并由3.24%、3.87%、3.68%及2024—2025年新发的二级资本债券置换。结构上，逐笔披露的51只债券中，2019—2020年密集发行的小微／绿色专项金融债已陆续到期，100亿元<b>宁行转债</b>以99.89%的转股率于2019年转股完毕并赎回残值，子公司<b>永赢金融租赁</b>与<b>宁银消费金融</b>近年独立发债（2024—2025年合计10只、215亿元）成为新的增量来源，另有2只各100亿元永续债（3.45%、2.30%）以其他权益工具形式在应付债券之外补充资本；需注意2024、2025年报已不再披露逐笔票面利率，这两年新发15只债券的票面利率在本表中留空。"

out = collections.OrderedDict()
for k, v in d.items():
    if k == '_notes':
        continue
    out[k] = v
    if k == 'depcost':
        out['bondpay'] = bondpay
if 'bondpay' not in out:
    out['bondpay'] = bondpay
notes = d.get('_notes') or collections.OrderedDict()
notes['bondpay'] = NOTE_SRC
notes['note-bondpay'] = NOTE_HTML
out['_notes'] = notes

txt = json.dumps(out, ensure_ascii=False, indent=2)


def collapse(text):
    """把纯数值/字符串数组压成一行。"""
    return re.sub(r'\[\s*\n\s*([^\[\]\{\}]*?)\s*\n\s*\]',
                  lambda m: '[' + ' '.join(x.strip() for x in m.group(1).split('\n')) + ']',
                  text)


# 仅对新插入的 bondpay 区块做压行，其余键保持原文件的展开格式（保证 diff 只有插入）
i = txt.index('\n  "bondpay": {')
j = txt.index('\n  },', i) + len('\n  },')
head, blk, tail = txt[:i], txt[i:j], txt[j:]
prev = None
while prev != blk:
    prev = blk
    blk = collapse(blk)
# bonds 内每只债券压成一行
blk = re.sub(r'\{\s*\n\s*("name".*?)\n\s*\}',
             lambda m: '{' + ' '.join(x.strip() for x in m.group(1).split('\n')) + '}',
             blk, flags=re.S)
txt = head + blk + tail

with io.open(P, 'w', encoding='utf-8') as f:
    f.write(txt + '\n')

with io.open(P, encoding='utf-8') as f:
    chk = json.load(f)
b = chk['bondpay']
assert list(b['years']) == years
for k in ('balNcd', 'balBond', 'balTotal', 'avgNcd', 'avgBond', 'avgTotal',
          'rateNcd', 'rateBond', 'rateTotal'):
    assert len(b[k]) == len(years), k
print('ok', list(chk.keys()))
print('bonds', len(b['bonds']))
