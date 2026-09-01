import pytest
import os
import tempfile

# 将项目根目录加入 sys.path，保证 import 正常
import sys
sys.path.insert(0, os.path.dirname(__file__))

import backend_python as bk

# monkeypatch 会把 builtins.open 换成下面的 lambda，lambda 体里若再写 open 就是调它自己
# （无限递归 RecursionError），所以先把真的 open 存下来给替身用。
_real_open = open


# ─────────────────────────────────────────────
# Helpers: 写临时数据文件，并 monkeypatch 路径
# ─────────────────────────────────────────────

PRODUCTION_HEADER = "year\tproduction\n"
PRICE_HEADER = "year\traw\tadj\n"


def write_tmp_file(tmp_path, filename, content):
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


# ─────────────────────────────────────────────
# read_production
# ─────────────────────────────────────────────

class TestReadProduction:

    def test_normal(self, tmp_path, monkeypatch):
        """正常多行数据"""
        content = PRODUCTION_HEADER + "2020\t100\n2021\t200\n2022\t300\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["2020", "2021", "2022"]
        assert result["data"]["prodData"] == [100, 200, 300]

    def test_file_not_exist(self, monkeypatch):
        """文件不存在时返回 500"""
        monkeypatch.setattr(bk.os.path, "exists", lambda p: False)

        result = bk.read_production()
        assert result["code"] == 500
        assert "不存在" in result["msg"]
        assert result["data"]["xAxis"] == []
        assert result["data"]["prodData"] == []

    def test_empty_file_only_header(self, tmp_path, monkeypatch):
        """只有表头，无数据行"""
        content = PRODUCTION_HEADER
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == []
        assert result["data"]["prodData"] == []

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\n\n2021\t200\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]
        assert result["data"]["prodData"] == [100, 200]

    def test_line_with_too_few_columns_skipped(self, tmp_path, monkeypatch):
        """列数不足的行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\nonlyone\n2021\t200\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]

    def test_invalid_int_raises_500(self, tmp_path, monkeypatch):
        """产量字段非整数时返回 500"""
        content = PRODUCTION_HEADER + "2020\tNOT_AN_INT\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 500
        assert result["data"]["xAxis"] == []

    def test_single_row(self, tmp_path, monkeypatch):
        """仅一条数据行"""
        content = PRODUCTION_HEADER + "1990\t999\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["1990"]
        assert result["data"]["prodData"] == [999]


# ─────────────────────────────────────────────
# read_price
# ─────────────────────────────────────────────

class TestReadPrice:

    def _patch(self, monkeypatch, fpath):
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

    def test_normal_multiple_rows(self, tmp_path, monkeypatch):
        """正常多行：蜡烛图数据正确构造"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n2021\t12.0\t11.0\n2022\t8.0\t7.5\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_price()
        assert result["code"] == 200
        xAxis = result["data"]["xAxis"]
        candle = result["data"]["candleData"]

        assert xAxis == ["2020", "2021", "2022"]
        # 第一行：open=close=10.0，high=low=10.0
        assert candle[0] == [10.0, 10.0, 10.0, 10.0]
        # 第二行：open=10.0(上期), close=12.0
        assert candle[1] == [10.0, 12.0, 10.0, 12.0]
        # 第三行：open=12.0(上期), close=8.0
        assert candle[2] == [12.0, 8.0, 8.0, 12.0]

    def test_single_row(self, tmp_path, monkeypatch):
        """仅一行：open=close，high=low"""
        content = PRICE_HEADER + "2000\t50.0\t48.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_price()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["2000"]
        assert result["data"]["candleData"] == [[50.0, 50.0, 50.0, 50.0]]

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n\n2021\t12.0\t11.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_price()
        assert len(result["data"]["xAxis"]) == 2

    def test_high_low_when_price_drops(self, tmp_path, monkeypatch):
        """价格下跌时 high=open, low=close"""
        content = PRICE_HEADER + "2020\t100.0\t90.0\n2021\t60.0\t55.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_price()
        _, close, low, high = result["data"]["candleData"][1]
        assert high == 100.0
        assert low == 60.0
        assert close == 60.0

    def test_high_low_when_price_rises(self, tmp_path, monkeypatch):
        """价格上涨时 high=close, low=open"""
        content = PRICE_HEADER + "2020\t50.0\t48.0\n2021\t80.0\t75.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_price()
        open_p, close, low, high = result["data"]["candleData"][1]
        assert open_p == 50.0
        assert close == 80.0
        assert low == 50.0
        assert high == 80.0

    def test_file_not_found_raises(self, monkeypatch):
        """文件不存在时抛出 FileNotFoundError（函数本身未容错）"""
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: (_ for _ in ()).throw(FileNotFoundError("no file")))
        with pytest.raises(FileNotFoundError):
            bk.read_price()


# ─────────────────────────────────────────────
# read_adj_price
# ─────────────────────────────────────────────

class TestReadAdjPrice:

    def _patch(self, monkeypatch, fpath):
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(fpath, *a, **kw))

    def test_uses_adj_column(self, tmp_path, monkeypatch):
        """使用 adj 列（第三列）而非 raw 列"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n2021\t12.0\t11.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_adj_price()
        assert result["code"] == 200
        # 第一行：open=close=9.0（adj）
        assert result["data"]["candleData"][0] == [9.0, 9.0, 9.0, 9.0]
        # 第二行：open=9.0(上期adj), close=11.0
        assert result["data"]["candleData"][1] == [9.0, 11.0, 9.0, 11.0]

    def test_xaxis_populated(self, tmp_path, monkeypatch):
        """xAxis 正确填充"""
        content = PRICE_HEADER + "2019\t5.0\t4.5\n2020\t6.0\t5.5\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_adj_price()
        assert result["data"]["xAxis"] == ["2019", "2020"]

    def test_single_row(self, tmp_path, monkeypatch):
        """单行：open=close=adj"""
        content = PRICE_HEADER + "2000\t50.0\t48.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_adj_price()
        assert result["data"]["candleData"] == [[48.0, 48.0, 48.0, 48.0]]

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n\n2021\t12.0\t11.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_adj_price()
        assert len(result["data"]["xAxis"]) == 2

    def test_price_drop_high_low(self, tmp_path, monkeypatch):
        """价格下跌：high=open(上期adj), low=close(本期adj)"""
        content = PRICE_HEADER + "2020\t100.0\t90.0\n2021\t60.0\t50.0\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        self._patch(monkeypatch, fpath)

        result = bk.read_adj_price()
        _, close, low, high = result["data"]["candleData"][1]
        assert high == 90.0
        assert low == 50.0

    def test_file_not_found_raises(self, monkeypatch):
        """文件不存在时抛出 FileNotFoundError"""
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: (_ for _ in ()).throw(FileNotFoundError("no file")))
        with pytest.raises(FileNotFoundError):
            bk.read_adj_price()


# ─────────────────────────────────────────────
# read_industry_annual / read_industry_peers
# 保险/地产/水泥/通信四个行业共用的读表逻辑，用本地 data/tables 的真实成品表跑
# ─────────────────────────────────────────────

class TestIndustryTables:

    @pytest.mark.parametrize("industry", sorted(bk.INDUSTRIES))
    def test_illegal_code_400(self, industry):
        """代码位数不合规直接 400，不去碰文件系统"""
        r = bk.read_industry_annual(industry, "abc")
        assert r["code"] == 400 and r["data"] == {}

    @pytest.mark.parametrize("industry", sorted(bk.INDUSTRIES))
    def test_unknown_code_404(self, industry):
        """代码合规但没有数据文件时 404"""
        r = bk.read_industry_annual(industry, "999999")
        assert r["code"] == 404 and "尚无年度数据文件" in r["msg"]

    @pytest.mark.parametrize("industry", sorted(bk.INDUSTRIES))
    def test_peers_only_declared_fields(self, industry):
        """同业对比只下发 spec['fields'] 声明的字段，且每家都带 annual"""
        r = bk.read_industry_peers(industry)
        assert r["code"] == 200, r.get("msg")
        fields = set(bk.INDUSTRIES[industry]["fields"])
        for code, d in r["data"].items():
            assert set(d) == fields, f"{industry} {code} 字段与声明不一致"
            assert isinstance(d["annual"], dict) and d["annual"]

    @pytest.mark.parametrize("industry", ["cement", "telecom"])
    def test_ops_manual_layer_merged(self, industry):
        """带经营手工层的行业：annual 里应出现 ops_* 字段，且顶层有 ops_meta"""
        r = bk.read_industry_peers(industry)
        merged = [c for c, d in r["data"].items()
                  if d.get("ops_meta") and any(k.startswith("ops_")
                                               for rec in d["annual"].values() for k in rec)]
        assert merged, f"{industry} 没有任何一家并进了 ops_* 手工层"

    def test_telecom_segment_layer(self):
        """通信板块的收入构成层：三家都要有 segments，且合计与利润表营业收入对得上
        （单位从元归一到亿元，容差 0.05 亿）"""
        data = bk.read_industry_peers("telecom")["data"]
        for code, d in data.items():
            seg = d["segments"]
            assert seg and seg["annual"], f"{code} 缺收入构成层"
            assert set(seg["labels"]) >= set(seg["order"]), f"{code} order 里有没有中文名的科目"
            for year, canon in seg["annual"].items():
                rev = d["annual"][year]["revenue"]
                assert abs(canon["total"] - rev / 1e8) < 0.05, f"{code} {year} 合计与营业收入不符"


class TestHolders:
    """股权结构共用接口：各板块同一份 payload 形状"""

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_payload_shape(self, industry):
        r = bk.read_holders(industry)
        assert r["code"] == 200, r.get("msg")
        d = r["data"]
        assert d["industry"] == industry and d["label"] and d["roster"]
        c = d["company"]
        assert set(c) == {"code", "name", "secucode", "tag", "source", "holders_end_date",
                          "holders", "holder_num", "holder_concentration", "detail_page",
                          "factions", "factions_source", "caliber_note", "residual_label", "ring",
                          "share_capital", "dividend_per10", "history_source", "holders_caliber",
                          "history_gaps", "dividend_unit", "share_capital_break"}
        # 默认公司必须是有股东数据的那一家，比例分母（total_shares）也要在
        assert c["holders"] and c["holders"][0]["total_shares"]
        assert all(r0["code"] in [x["code"] for x in d["roster"]] for r0 in [c])

    def test_manual_only_industries(self):
        """百度与巴比没有 annual 表，股东块整份来自 holders_manual.json，照样能出 payload"""
        for industry, code, total in (("tech", "09888", 2722021272), ("food", "605338", 239566662)):
            c = bk.read_holders(industry)["data"]["company"]
            assert c["code"] == code and c["holders"], industry
            assert c["holders"][0]["total_shares"] == total
            assert c["caliber_note"], "手工层公司必须写清口径，不能与接口快照混着读"
            # 比例是按 股数 ÷ 总股本 重算的，逐行都要能对上
            for h in c["holders"]:
                assert abs(h["hold_num"] / total * 100 - h["ratio"]) < 0.006, (industry, h["name"])

    def test_factions_resolved_against_roster(self):
        """分组里点名的股东必须真在名册里 —— 对不上的成员由后端剔除，不许留下悬空名字"""
        for industry in sorted(bk.HOLDER_INDUSTRIES):
            for r in bk.read_holders(industry)["data"]["roster"]:
                c = bk.read_holders(industry, r["code"])["data"]["company"]
                names = {h["name"] for h in c["holders"]}
                for g in c["factions"] or []:
                    assert g["names"], f"{industry} {r['code']} 空分组不该下发"
                    assert set(g["names"]) <= names, f"{industry} {r['code']} {g['title']}"

    def test_bank_faction_members_all_resolve(self):
        """银行派系表（年报口径页那份）的每个成员都要落到接口名册上：
        用年报简称的 5 家（601077/601288/600036/600016/01578）靠手工层 faction_aliases 接，
        名册换期后别名失效会在这里暴露 —— 只有「其他流通股东」是环形图残余块，名册里本来没有。"""
        for r in bk.read_holders("bank")["data"]["roster"]:
            d = bk._holder_table("bank", r["code"])
            fac = bk._bank_factions(r["code"])
            if not d or not fac:
                continue
            man = bk._holders_manual().get("bank:" + r["code"]) or {}
            want = sum(1 for f in fac for n in (f.get("names") or []) if n != "其他流通股东")
            got = bk._resolve_factions(d.get("holders") or [], fac, man.get("faction_aliases")) or []
            assert sum(len(f["names"]) for f in got) == want, r["code"]

    def test_ring_block_sums_to_100(self):
        """银行的环形图数据块是年报口径（含「其他流通股东」），一圈铺满 100%"""
        for code in ("601398", "601077", "600036"):
            ring = bk.read_holders("bank", code)["data"]["company"]["ring"]
            assert ring and ring["caliber"] == "占总股本"
            assert abs(sum(x["value"] for x in ring["holderData"]) - 100) < 0.05, code
            names = {x["name"] for x in ring["holderData"]}
            for g in ring["factions"]:
                assert set(g["names"]) <= names, f"{code} {g['title']} 引用了 holderData 里没有的名字"

    def test_history_layers_are_monotone_and_consistent(self):
        """照 bank/shareholder.html 那套模板补的历年序列：股本/户数/集中度/分红四层的内部一致性。
        集中度必须满足 top1 ≤ top3 ≤ top10（同一年的前 N 名累计），否则就是排序或加总错了。"""
        cases = [("telecom", "600941"), ("telecom", "601728"), ("telecom", "600050"),
                 ("food", "605338")]
        for industry, code in cases:
            c = bk.read_holders(industry, code)["data"]["company"]
            cap = c["share_capital"]
            assert cap and len(cap) >= 5, f"{code} 缺历年股本"
            assert [r[0] for r in cap] == sorted(r[0] for r in cap), f"{code} 股本年份未升序"
            assert all(r[1] > 0 for r in cap), code
            hn = c["holder_num"]
            assert hn and len({r[0] for r in hn}) == len(hn), f"{code} 户数日期有重复"
            for r in c["holder_concentration"]:
                t1, t3, t10 = r.get("top1"), r.get("top3"), r.get("top10")
                assert t1 is not None, (code, r["date"])
                if t3 is not None:
                    assert t1 <= t3 + 1e-9, (code, r["date"], t1, t3)
                    if t10 is not None:
                        assert t3 <= t10 + 1e-9, (code, r["date"], t3, t10)
                if r.get("top1_ex") is not None:
                    assert r["top1_ex"] <= t1 + 1e-9, (code, r["date"])
            assert all(v >= 0 for _, v in (c["dividend_per10"] or [])), code
            # 港元宣派的公司必须把单位标出来，不能混进「元」的序列里
            assert c["dividend_unit"] in ("元", "港元"), (code, c["dividend_unit"])
            assert c["history_source"], f"{code} 历年序列必须留来源"

    def test_pure_h_marked_not_dropped(self):
        """纯 H 股公司接口不返回股东，名单里要保留并标 has_holders=false（不是取数遗漏）"""
        roster = bk.read_holders("developer")["data"]["roster"]
        assert [r["code"] for r in roster if not r["has_holders"]], "开发商板块应有纯 H 股缺股东数据的公司"

    def test_bank_extra_layers_and_link(self):
        """银行表另带股东户数与集中度两层，并给出年报口径股东页入口"""
        c = bk.read_holders("bank", "601077")["data"]["company"]
        assert c["holder_num"] and c["holder_concentration"]
        assert c["detail_page"] == "/bank/601077/shareholder.html"

    def test_unknown_industry_and_code(self):
        assert bk.read_holders("foo")["code"] == 400
        assert bk.read_holders("bank", "999999")["code"] == 404

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_source_no_f10_branding(self, industry):
        """项目规则：对外文本不写「F10」品牌字样（接口报表名 RPT_HKF10_* 除外）"""
        for r in bk.read_holders(industry)["data"]["roster"]:
            src = (bk.read_holders(industry, r["code"])["data"]["company"]["source"] or "")
            assert "F10 " not in src.replace("RPT_HKF10_FN_MAININDICATOR", ""), f"{industry} {r['code']}"

