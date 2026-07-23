import pytest
import os
import tempfile

# 将项目根目录加入 sys.path，保证 import 正常
import sys
sys.path.insert(0, os.path.dirname(__file__))

import backend_python as bk


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
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

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
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == []
        assert result["data"]["prodData"] == []

    def test_blank_lines_skipped(self, tmp_path, monkeypatch):
        """空行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\n\n2021\t200\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]
        assert result["data"]["prodData"] == [100, 200]

    def test_line_with_too_few_columns_skipped(self, tmp_path, monkeypatch):
        """列数不足的行被跳过"""
        content = PRODUCTION_HEADER + "2020\t100\nonlyone\n2021\t200\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["data"]["xAxis"] == ["2020", "2021"]

    def test_invalid_int_raises_500(self, tmp_path, monkeypatch):
        """产量字段非整数时返回 500"""
        content = PRODUCTION_HEADER + "2020\tNOT_AN_INT\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 500
        assert result["data"]["xAxis"] == []

    def test_single_row(self, tmp_path, monkeypatch):
        """仅一条数据行"""
        content = PRODUCTION_HEADER + "1990\t999\n"
        fpath = write_tmp_file(tmp_path, "data/tables/oil.production.txt", content)
        monkeypatch.setattr(bk.os.path, "exists", lambda p: True)
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

        result = bk.read_production()
        assert result["code"] == 200
        assert result["data"]["xAxis"] == ["1990"]
        assert result["data"]["prodData"] == [999]


# ─────────────────────────────────────────────
# read_price
# ─────────────────────────────────────────────

class TestReadPrice:

    def _patch(self, monkeypatch, fpath):
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

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
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: open(fpath, *a, **kw))

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
