import pytest
import os
import tempfile

# 将项目根目录加入 sys.path，保证 import 正常
import sys
sys.path.insert(0, os.path.dirname(__file__))

import backend as bk


# ─────────────────────────────────────────────
# Helpers: 把临时数据文件写到 tmp_path 下，再把 backend.oil.TABLES_DIR 指过去
#
# 油价三个函数现在按绝对基准 TABLES_DIR 拼路径（不再依赖进程 CWD），所以测试用
# monkeypatch.setattr 把 backend.oil.TABLES_DIR 指向 tmp_path 下的临时表目录，
# 让被测函数用真的 open / os.path.exists 去命中临时文件 —— 既验证了路径拼接本身对不对，
# 又不必全局劫持 builtins.open（劫持会连函数内部别的 open 一起换掉，
# 且路径拼错也照样绿）。文件不存在的分支也交给真的 os.path.exists 判定。
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
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["2020", "2021", "2022"]
        assert result["data"]["prodData"] == [100, 200, 300]

    def test_file_not_exist(self, tmp_path, monkeypatch):
        """文件不存在时返回 500（切到空目录，让真的 os.path.exists 判定）"""
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["code"] == 500
        assert "不存在" in result["msg"]
        assert result["data"]["xAxis"] == []
        assert result["data"]["prodData"] == []

    def test_empty_file_only_header(self, tmp_path, monkeypatch):
        """只有表头，无数据行"""
        content = PRODUCTION_HEADER
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == []
        assert result["data"]["prodData"] == []

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\n\n2021\t200\n"
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]
        assert result["data"]["prodData"] == [100, 200]

    def test_line_with_too_few_columns_skipped(self, tmp_path, monkeypatch):
        """列数不足的行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\nonlyone\n2021\t200\n"
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]

    def test_invalid_int_raises_500(self, tmp_path, monkeypatch):
        """产量字段非整数时返回 500"""
        content = PRODUCTION_HEADER + "2020\tNOT_AN_INT\n"
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["code"] == 500
        assert result["data"]["xAxis"] == []

    def test_single_row(self, tmp_path, monkeypatch):
        """仅一条数据行"""
        content = PRODUCTION_HEADER + "1990\t999\n"
        write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["1990"]
        assert result["data"]["prodData"] == [999]


# ─────────────────────────────────────────────
# read_price
# ─────────────────────────────────────────────

class TestReadPrice:

    def _write(self, tmp_path, monkeypatch, content):
        write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

    def test_normal_multiple_rows(self, tmp_path, monkeypatch):
        """正常多行：蜡烛图数据正确构造"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n2021\t12.0\t11.0\n2022\t8.0\t7.5\n"
        self._write(tmp_path, monkeypatch, content)

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
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_price()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["2000"]
        assert result["data"]["candleData"] == [[50.0, 50.0, 50.0, 50.0]]

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n\n2021\t12.0\t11.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_price()
        assert len(result["data"]["xAxis"]) == 2

    def test_high_low_when_price_drops(self, tmp_path, monkeypatch):
        """价格下跌时 high=open, low=close"""
        content = PRICE_HEADER + "2020\t100.0\t90.0\n2021\t60.0\t55.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_price()
        _, close, low, high = result["data"]["candleData"][1]
        assert high == 100.0
        assert low == 60.0
        assert close == 60.0

    def test_high_low_when_price_rises(self, tmp_path, monkeypatch):
        """价格上涨时 high=close, low=open"""
        content = PRICE_HEADER + "2020\t50.0\t48.0\n2021\t80.0\t75.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_price()
        open_p, close, low, high = result["data"]["candleData"][1]
        assert open_p == 50.0
        assert close == 80.0
        assert low == 50.0
        assert high == 80.0

    def test_file_not_found_raises(self, tmp_path, monkeypatch):
        """文件不存在时抛出 FileNotFoundError（函数本身未容错）——
        切到没有数据表的空目录，让真的 open 抛出，而不是伪造一个异常。
        注：read_production 缺文件返回 500、read_price 直接抛，两者容错策略不一致，
        属未统一的后端技术债；此处如实记录现状，若后续统一为 500 需同步改本断言。"""
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))
        with pytest.raises(FileNotFoundError):
            bk.read_price()


# ─────────────────────────────────────────────
# read_adj_price
# ─────────────────────────────────────────────

class TestReadAdjPrice:

    def _write(self, tmp_path, monkeypatch, content):
        write_tmp_file(tmp_path, "data/tables/oil.price.txt", content)
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))

    def test_uses_adj_column(self, tmp_path, monkeypatch):
        """使用 adj 列（第三列）而非 raw 列"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n2021\t12.0\t11.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_adj_price()
        assert result["code"] == 200
        # 第一行：open=close=9.0（adj）
        assert result["data"]["candleData"][0] == [9.0, 9.0, 9.0, 9.0]
        # 第二行：open=9.0(上期adj), close=11.0
        assert result["data"]["candleData"][1] == [9.0, 11.0, 9.0, 11.0]

    def test_xaxis_populated(self, tmp_path, monkeypatch):
        """xAxis 正确填充"""
        content = PRICE_HEADER + "2019\t5.0\t4.5\n2020\t6.0\t5.5\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_adj_price()
        assert result["data"]["xAxis"] == ["2019", "2020"]

    def test_single_row(self, tmp_path, monkeypatch):
        """单行：open=close=adj"""
        content = PRICE_HEADER + "2000\t50.0\t48.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_adj_price()
        assert result["data"]["candleData"] == [[48.0, 48.0, 48.0, 48.0]]

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRICE_HEADER + "2020\t10.0\t9.0\n\n2021\t12.0\t11.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_adj_price()
        assert len(result["data"]["xAxis"]) == 2

    def test_price_drop_high_low(self, tmp_path, monkeypatch):
        """价格下跌：high=open(上期adj), low=close(本期adj)"""
        content = PRICE_HEADER + "2020\t100.0\t90.0\n2021\t60.0\t50.0\n"
        self._write(tmp_path, monkeypatch, content)

        result = bk.read_adj_price()
        _, close, low, high = result["data"]["candleData"][1]
        assert high == 90.0
        assert low == 50.0

    def test_file_not_found_raises(self, tmp_path, monkeypatch):
        """文件不存在时抛出 FileNotFoundError（切到空目录让真的 open 抛出）"""
        monkeypatch.setattr(bk.oil, "TABLES_DIR", str(tmp_path / "data" / "tables"))
        with pytest.raises(FileNotFoundError):
            bk.read_adj_price()


# ─────────────────────────────────────────────
# read_industry_annual / read_industry_peers
# 保险/地产/水泥/通信四个行业共用的读表逻辑，用本地 data/tables 的真实成品表跑
#
# 下面三类（TestIndustryTables / TestHolders / TestNav）不造临时文件，
# 直接读真实成品表 —— 属集成测试，依赖 data/tables 的当前内容，且必须
# 从项目根目录运行。全部打 @pytest.mark.integration，可用
#   pytest -m "not integration"   只跑上面油价那几组纯单元测试。
# ─────────────────────────────────────────────

class TestIndustryTables:
    pytestmark = pytest.mark.integration

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
    pytestmark = pytest.mark.integration

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_payload_shape(self, industry):
        r = bk.read_holders(bk.industry_default_code(industry))
        assert r["code"] == 200, r.get("msg")
        d = r["data"]
        assert d["industry"] == industry and d["label"] and d["roster"]
        c = d["company"]
        assert set(c) == {"code", "name", "secucode", "tag", "source", "holders_end_date",
                          "holders", "holder_num", "holder_concentration", "detail_page",
                          "factions", "factions_source", "caliber_note", "residual_label", "ring",
                          "share_capital", "dividend_per10", "history_source", "holders_caliber",
                          "history_gaps", "dividend_unit", "share_capital_break",
                          # 两地代码对应表 + 每张图下那段现算的解读 + 环形图的附加口径
                          "codes", "code_note", "narrative", "ring_alt", "ring_label", "sources"}
        # 默认公司必须是有股东数据的那一家，比例分母（total_shares）也要在
        assert c["holders"] and c["holders"][0]["total_shares"]
        assert all(r0["code"] in [x["code"] for x in d["roster"]] for r0 in [c])

    def test_manual_only_industries(self):
        """百度与巴比没有 annual 表，股东块整份来自 holders_manual.json，照样能出 payload"""
        # (板块, 代码, 年报口径总股本)：total 抄自 holders_manual.json 里那家的 total_shares，
        # 即比例分母，年报更新时同步这里
        for industry, code, total in (("tech", "09888", 2722021272), ("food", "605338", 239566662)):
            c = bk.read_holders(bk.industry_default_code(industry))["data"]["company"]
            assert c["code"] == code and c["holders"], industry
            assert c["holders"][0]["total_shares"] == total
            assert c["caliber_note"], "手工层公司必须写清口径，不能与接口快照混着读"
            # 比例是按 股数 ÷ 总股本 重算的，逐行都要能对上
            for h in c["holders"]:
                assert abs(h["hold_num"] / total * 100 - h["ratio"]) < 0.006, (industry, h["name"])

    def test_factions_resolved_against_roster(self):
        """分组里点名的股东必须真在名册里 —— 对不上的成员由后端剔除，不许留下悬空名字"""
        for industry in sorted(bk.HOLDER_INDUSTRIES):
            for r in bk.read_holders(bk.industry_default_code(industry))["data"]["roster"]:
                c = bk.read_holders(r["code"])["data"]["company"]
                names = {h["name"] for h in c["holders"]}
                for g in c["factions"] or []:
                    assert g["names"], f"{industry} {r['code']} 空分组不该下发"
                    assert set(g["names"]) <= names, f"{industry} {r['code']} {g['title']}"

    def test_bank_faction_members_all_resolve(self):
        """银行派系表（年报口径页那份）的每个成员都要落到接口名册上：
        用年报简称的 5 家（601077/601288/600036/600016/01578）靠手工层 faction_aliases 接，
        名册换期后别名失效会在这里暴露 —— 只有「其他流通股东」是环形图残余块，名册里本来没有。"""
        for r in bk.read_holders(bk.industry_default_code("bank"))["data"]["roster"]:
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
        # 三家有年报口径环形块的样本：工行 / 渝农商行 / 招行
        for code in ("601398", "601077", "600036"):
            ring = bk.read_holders(code)["data"]["company"]["ring"]
            assert ring and ring["caliber"] == "占总股本"
            assert abs(sum(x["value"] for x in ring["holderData"]) - 100) < 0.05, code
            names = {x["name"] for x in ring["holderData"]}
            for g in ring["factions"]:
                assert set(g["names"]) <= names, f"{code} {g['title']} 引用了 holderData 里没有的名字"

    def test_history_layers_are_monotone_and_consistent(self):
        """照 shareholder.html 那套模板补的历年序列：股本/户数/集中度/分红四层的内部一致性。
        集中度必须满足 top1 ≤ top3 ≤ top10（同一年的前 N 名累计），否则就是排序或加总错了。"""
        cases = [("telecom", "600941"), ("telecom", "601728"), ("telecom", "600050"),
                 ("food", "605338")]
        for industry, code in cases:
            c = bk.read_holders(code)["data"]["company"]
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
        roster = bk.read_holders(bk.industry_default_code("developer"))["data"]["roster"]
        assert [r["code"] for r in roster if not r["has_holders"]], "开发商板块应有纯 H 股缺股东数据的公司"

    def test_bank_extra_layers_and_link(self):
        """银行四层历史序列都要在：户数与集中度来自 bank 表，股本与分红来自 company_charts
        （银行原先独立的年报口径股东页已并入唯一一份股权结构页，所以不再给外链入口）"""
        c = bk.read_holders("601077")["data"]["company"]
        assert c["holder_num"] and c["holder_concentration"]
        assert c["detail_page"] is None
        cap, div = c["share_capital"], c["dividend_per10"]
        # 每行 [年, 股数, 变动原因, 类型]：类型只有精编过成因的年份才有（其余为 None），
        # 页面据它按银行那套调色板给点上色，缺这一层的公司退回「动过／未动过」两色
        assert cap and len(cap) > 5 and all(len(r) == 4 for r in cap)
        assert {r[3] for r in cap} >= {"ipo", "pp", "seo"}, "渝农商行的资本运作类型不该丢"
        # 股本单位是股（渝农商行 113.57 亿股），不是数据表里那个「亿股」
        assert cap[-1][1] > 1e9, cap[-1]
        assert div and all(len(r) == 2 and r[1] is not None for r in div)
        # company_charts 里 share-capital / dividend-per10 是各行标配，有股东数据的行都该有这两层
        for r in bk.read_holders(bk.industry_default_code("bank"))["data"]["roster"]:
            if not r["has_holders"]:
                continue
            cc = bk.read_holders(r["code"])["data"]["company"]
            assert cc["share_capital"] and cc["dividend_per10"], r["code"]

    def test_unknown_code(self):
        """接口只认代码（板块由代码判定），认不出的代码给 404 并指到对应表"""
        assert bk.industry_default_code("foo") is None
        r = bk.read_holders("999999")
        assert r["code"] == 404 and "company_codes.json" in r["msg"]

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_source_no_f10_branding(self, industry):
        """项目规则：对外文本不写「F10」品牌字样（接口报表名 RPT_HKF10_* 除外）"""
        for r in bk.read_holders(bk.industry_default_code(industry))["data"]["roster"]:
            src = (bk.read_holders(r["code"])["data"]["company"]["source"] or "")
            assert "F10 " not in src.replace("RPT_HKF10_FN_MAININDICATOR", ""), f"{industry} {r['code']}"

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_dividend_series_is_array(self, industry):
        """分红序列一律是 [[年, 值]]：annual 表里那份是「年→值」的字典，前端只吃数组
        （原先字典直下发，险企/开发商/水泥三个板块的分红图 length 为 undefined，静默不画）"""
        for r in bk.read_holders(bk.industry_default_code(industry))["data"]["roster"]:
            div = bk.read_holders(r["code"])["data"]["company"]["dividend_per10"]
            if div is None:
                continue
            assert isinstance(div, list), (industry, r["code"])
            assert all(isinstance(x, list) and len(x) == 2 for x in div), (industry, r["code"])
            assert [x[0] for x in div] == sorted(x[0] for x in div), (industry, r["code"])

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_narrative_is_per_company(self, industry):
        """每张图下那段解读必须是本公司自己的数（原先银行那套话写死在 HTML 里，只对渝农商行成立）：
        每段都要带本公司名字，且有那一层数据才有那一段 —— 反过来说，没有的层不许凭空出现解读。"""
        for r in bk.read_holders(bk.industry_default_code(industry))["data"]["roster"]:
            c = bk.read_holders(r["code"])["data"]["company"]
            nar = c["narrative"] or {}
            if not c["holders"]:
                continue
            assert nar, (industry, r["code"])
            for k, v in nar.items():
                assert c["name"] in v["text"], (industry, r["code"], k)
                assert "**" in v["text"], f"{r['code']} {k} 没有一个加粗的关键数字"
                assert "F10" not in v["text"] + (v.get("detail") or ""), (r["code"], k)
            assert ("divper10" in nar) == bool(c["dividend_per10"]), (industry, r["code"])
            assert ("sharecap" in nar) == bool(c["share_capital"]
                                               and len(c["share_capital"]) > 1), r["code"]
            assert ("holdernum" in nar) == bool(c["holder_num"]
                                                and len(c["holder_num"]) > 1), r["code"]

    def test_narrative_numbers_match_series(self):
        """解读里的数字是从序列现算的，不是抄来的：抽三家核对每 10 股派现与股本两端"""
        for industry, code in (("bank", "601398"), ("telecom", "600941"), ("food", "605338")):
            c = bk.read_holders(code)["data"]["company"]
            nar = c["narrative"]
            ly, lp = c["dividend_per10"][-1]
            assert f"{ly} 年度每 10 股派现 {lp:,.4f}" in nar["divper10"]["text"], code
            cap = c["share_capital"]
            assert f"{cap[0][0]}–{cap[-1][0]} 年" in nar["sharecap"]["text"], code
            assert f"{cap[-1][1] / 1e8:,.2f} 亿股" in nar["sharecap"]["text"], code

    def test_dividend_ratio_only_when_base_is_trustworthy(self):
        """分红率的分母必须可信：中国移动 annual 表里的「股本」科目是 468 亿元、总股本只有 216 亿股
        （科目含发行溢价，不等于股数），这种情况只给每 10 股金额，不许拿错一个量级的数算分红率；
        港元宣派的公司也不与人民币利润相除。"""
        c = bk.read_holders("600941")["data"]["company"]
        t = c["narrative"]["divper10"]["text"]
        assert "不算分红率" in t and "分红率（占归母净利润）" not in t
        # 现金分红总额按本页股本序列（年报股数）算：52.70/10 × 216.45 亿股 ≈ 1,141 亿港元
        assert "1,141 亿港元" in t, t

    def test_code_map_resolves_both_markets(self):
        """A 股／H 股／美股代码指向同一家公司时可互换；不是同一法人的不许换"""
        c = bk.read_holders("01398")["data"]["company"]
        assert c["code"] == "601398" and c["codes"]["h"] == "01398"
        assert "同一家公司" in (c["code_note"] or "")
        c = bk.read_holders("BIDU")["data"]["company"]
        assert c["code"] == "09888" and c["codes"]["us"] == "BIDU"
        # 中国联通 A 股 600050 与红筹 00762 不是同一法人：接口拒绝互换并说明原因
        r = bk.read_holders("00762")
        assert r["code"] == 404 and "不是同一法人" in r["msg"]
        # 别的板块的代码不必再指定板块：600585 直接落到水泥板块的海螺水泥
        d = bk.read_holders("600585")["data"]
        assert d["industry"] == "cement" and d["company"]["code"] == "600585"

    def test_code_decides_industry(self):
        """板块由代码判定：任意一地的代码都直接落到那家公司所在的板块，不用再传 industry，
        也不再需要「跳转指引」那一步；换不了代码的（联通红筹）仍给 404 + 原因 + 该问哪个代码。"""
        d = bk.read_holders("00914")["data"]          # 海螺水泥的 H 股代码
        assert d["industry"] == "cement"
        assert d["company"]["code"] == "600585" and d["company"]["codes"]["industry"] == "cement"
        assert len(d["roster"]) == len(bk.HOLDER_INDUSTRIES["cement"]["codes"])
        # 联通红筹不是同一法人：msg 先说清两者不是一家，并指到 telecom/600050
        r = bk.read_holders("00762")
        assert r["code"] == 404 and "不是同一法人" in r["msg"]
        assert r["data"]["redirect"]["code"] == "600050"

    def test_code_map_on_other_endpoints(self):
        """两地代码对应表接到所有吃 ?code= 的接口上：行业年度表、银行 company_charts 都要能换"""
        for industry, h, a in (("cement", "00914", "600585"), ("insurer", "02318", "601318"),
                               ("telecom", "00941", "600941")):
            d = bk.read_industry_annual(industry, h)
            assert d["code"] == 200, (industry, h, d.get("msg"))
            assert d["data"]["code"] == a and "同一家公司" in d["data"]["code_note"]
            assert d["data"]["codes"]["industry"] == industry
        for h, a in (("03618", "601077"), ("01398", "601398")):
            r = bk.read_company_charts(h)
            assert r["code"] == 200 and r["data"]["_bank"]["aCode"] == a, h
        # 本接口不服务的板块只给说明、不给可跳的板块（industry=None），也不许静默返回别家数据
        r = bk.read_company_charts("00914")
        assert r["code"] == 404 and r["data"]["redirect"]["industry"] is None

    def test_code_map_no_collision(self):
        entities, index = bk._company_codes()
        assert len(entities) > 60
        for e in entities.values():
            assert e["key"] in (e.get("a_code"), e.get("h_code"), e.get("us_code")), e["key"]
        for code, es in index.items():
            assert len(es) == 1, (code, [x["key"] for x in es])

    def test_ring_alt_calibers(self):
        """环形图的附加口径（渝农商行两张 H 股年报环）：每圈自成 100%，且必须带口径说明 ——
        分母是总股本还是 H 股股本、取哪一年年报，说不清的图不下发"""
        c = bk.read_holders("601077")["data"]["company"]
        alt = c["ring_alt"]
        assert alt and len(alt) == 2 and c["ring_label"]
        for a in alt:
            assert a["note"] and a["label"] and a["caliber"]
            assert abs(sum(x["value"] for x in a["holderData"]) - 100) < 0.05, a["key"]
            names = {x["name"] for x in a["holderData"]}
            for g in a["factions"]:
                assert set(g["names"]) <= names, (a["key"], g["title"])
        # 附加口径是逐公司的数据层给的，没有那两块的行不许凭空出现
        assert bk.read_holders("601398")["data"]["company"]["ring_alt"] is None


class TestNav:
    """股权结构页的导航判定：代码 → 板块 + 该板块的默认公司代码"""
    pytestmark = pytest.mark.integration

    @pytest.mark.parametrize("industry", sorted(bk.HOLDER_INDUSTRIES))
    def test_every_industry_has_a_nav(self, industry):
        """每个板块都判得出自己，且带上板块中文名"""
        d = bk.read_nav(None, industry)["data"]
        assert d["industry"] == industry and d["label"]

    def test_code_decides_industry(self):
        """板块按代码判定：A 股／H 股／美股代码都认得，industry 参数对不上时以代码为准"""
        for code, ind in (("601077", "bank"), ("01398", "bank"), ("600941", "telecom"),
                          ("00941", "telecom"), ("BIDU", "tech"), ("605338", "food"),
                          ("600585", "cement"), ("601318", "insurer")):
            assert bk.read_nav(code)["data"]["industry"] == ind, code
        r = bk.read_nav("600585", "bank")["data"]
        assert r["industry"] == "cement" and r["note"]

    def test_unknown_falls_back(self):
        """认不出的代码退回 industry 参数、两个都没有落到银行 —— 都要把原因写在 note 里"""
        assert bk.read_nav("999999", "telecom")["data"]["industry"] == "telecom"
        assert bk.read_nav("999999", "telecom")["data"]["note"]
        # code 都没给时落到银行板块，并把该板块的默认公司代码给页面（页面照它去 /api/holders）
        assert bk.read_nav()["data"] == {"industry": "bank", "label": "银行", "note": None,
                                         "code": "601077"}
        # 只给老链接那种 ?industry=：也换成该板块的默认公司代码
        assert bk.read_nav(None, "cement")["data"]["code"] == "600585"
        # 给了认得出的代码就原样带回去（另一地的代码由 /api/holders 再换成同一家公司的本板块代码）
        assert bk.read_nav("00914")["data"]["code"] == "00914"


