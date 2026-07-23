"""
A股银行股15年数据分析 - 分开展示图表
"""

import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

# 设置matplotlib
plt.rcParams['axes.unicode_minus'] = False

# 银行股列表（拼音，避免乱码）
BANK_STOCKS = {
    'sh.601398': 'GS_YH', 'sh.601939': 'JS_YH', 'sh.601288': 'NY_YH',
    'sh.601988': 'ZG_YH', 'sh.601328': 'JT_YH','sh.601658': 'YC_YH',
    # 'sh.600036': 'ZS_YH', 'sh.600016': 'MS_YH', 'sh.600000': 'PF_YH',
    # 'sh.601166': 'XY_YH', 'sh.601998': 'ZX_YH', 'sh.601818': 'GD_YH',
    # 'sh.600015': 'HX_YH', 'sh.601169': 'BJ_YH', 'sh.601229': 'SH_YH',
    # 'sh.600926': 'HZ_YH', 'sh.601009': 'NJ_YH', 'sz.002142': 'NB_YH',
    # 'sh.601077': 'YNS_YH', 'sz.002966': 'SZ_YH'
}

# 中英文映射
NAME_CN = {
    'GS_YH': '工商银行', 'JS_YH': '建设银行', 'NY_YH': '农业银行',
    'ZG_YH': '中国银行', 'JT_YH': '交通银行', 'YC_YH': '邮储银行',
    'ZS_YH': '招商银行', 'MS_YH': '民生银行', 'PF_YH': '浦发银行',
    'XY_YH': '兴业银行', 'ZX_YH': '中信银行', 'GD_YH': '光大银行',
    'HX_YH': '华夏银行', 'BJ_YH': '北京银行', 'SH_YH': '上海银行',
    'HZ_YH': '杭州银行', 'NJ_YH': '南京银行', 'NB_YH': '宁波银行',
    'YNS_YH': '渝农商行', 'SZ_YH': '苏州银行'
}


# ==================== 获取数据 ====================
def get_bank_data(code, name, start='2011-01-01', end='2026-04-08'):
    """获取单个银行数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code, "date,close",
            start_date=start, end_date=end,
            frequency="d", adjustflag="3"
        )

        if rs is None:
            return None

        data = []
        while rs.next():
            data.append(rs.get_row_data())

        if not data:
            return None

        df = pd.DataFrame(data, columns=['date', 'close'])
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df = df.dropna()

        if len(df) < 100:
            return None

        df.set_index('date', inplace=True)
        df['return'] = df['close'].pct_change() * 100
        return df['return']

    except Exception as e:
        return None


# ==================== 图表1：各银行累计超额收益折线图 ====================
def plot_excess_return_line(deviation):
    """绘制累计超额收益折线图"""
    plt.figure(figsize=(14, 8))

    for bank in deviation.columns:
        cumsum = deviation[bank].dropna().cumsum()
        plt.plot(cumsum.index, cumsum, label=bank, linewidth=1.2, alpha=0.7)

    plt.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Excess Return (%)', fontsize=12)
    plt.title('Bank Stocks - Cumulative Excess Return (2011-2026)', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=8, ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_01_excess_return_line.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表1已保存: chart_01_excess_return_line.png")


# ==================== 图表2：波动率排名柱状图 ====================
def plot_volatility_bar(volatility):
    """绘制波动率排名柱状图"""
    plt.figure(figsize=(12, 8))

    vol_sorted = volatility.sort_values()

    # 颜色：低波动绿色，中波动黄色，高波动红色
    colors = []
    for i in range(len(vol_sorted)):
        if i < len(vol_sorted) // 3:
            colors.append('#2ecc71')  # 绿
        elif i < 2 * len(vol_sorted) // 3:
            colors.append('#f39c12')  # 黄
        else:
            colors.append('#e74c3c')  # 红

    plt.barh(range(len(vol_sorted)), vol_sorted.values, color=colors, alpha=0.8)
    plt.yticks(range(len(vol_sorted)), vol_sorted.index, fontsize=9)
    plt.xlabel('Annualized Volatility (%)', fontsize=12)
    plt.title('Bank Stocks - Volatility Ranking (Green=Low, Red=High)', fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_02_volatility_bar.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表2已保存: chart_02_volatility_bar.png")


# ==================== 图表3：板块偏离度范围图 ====================
def plot_deviation_range(deviation):
    """绘制板块内部分化范围图"""
    plt.figure(figsize=(14, 7))

    max_dev = deviation.max(axis=1)
    min_dev = deviation.min(axis=1)
    mean_dev = deviation.mean(axis=1)

    plt.fill_between(deviation.index, min_dev, max_dev, alpha=0.3, color='gray', label='All Banks Range')
    plt.plot(deviation.index, mean_dev, 'r-', linewidth=2, label='Average Deviation')
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)

    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Deviation from Sector Avg (%)', fontsize=12)
    plt.title('Bank Sector - Deviation Range (Max vs Min)', fontsize=14, fontweight='bold')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_03_deviation_range.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表3已保存: chart_03_deviation_range.png")


# ==================== 图表4：波动率 vs 累计收益散点图 ====================
def plot_volatility_vs_return(volatility, cum_returns):
    """绘制波动率与累计收益散点图"""
    plt.figure(figsize=(12, 8))

    # 绘制散点
    plt.scatter(volatility, cum_returns, s=120, alpha=0.7, c='steelblue', edgecolors='black', linewidth=1.5)

    # 添加标签
    for bank in volatility.index:
        plt.annotate(bank, (volatility[bank], cum_returns[bank]), fontsize=9, alpha=0.8)

    # 添加中位线
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(x=volatility.median(), color='gray', linestyle='--', alpha=0.5)

    plt.xlabel('Annualized Volatility (%)', fontsize=12)
    plt.ylabel('Cumulative Excess Return (%)', fontsize=12)
    plt.title('Bank Stocks - Volatility vs Cumulative Excess Return', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_04_volatility_vs_return.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表4已保存: chart_04_volatility_vs_return.png")


# ==================== 图表5：重点银行对比折线图 ====================
def plot_key_banks_line(deviation):
    """绘制重点银行对比折线图（只选几家代表性银行）"""
    plt.figure(figsize=(14, 8))

    # 选择代表性银行
    key_banks = ['GS_YH', 'ZS_YH', 'NB_YH', 'NY_YH']
    key_banks = [b for b in key_banks if b in deviation.columns]

    for bank in key_banks:
        cumsum = deviation[bank].dropna().cumsum()
        plt.plot(cumsum.index, cumsum, label=NAME_CN.get(bank, bank), linewidth=2)

    plt.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Excess Return (%)', fontsize=12)
    plt.title('Key Banks - Cumulative Excess Return Comparison', fontsize=14, fontweight='bold')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_05_key_banks_line.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表5已保存: chart_05_key_banks_line.png")


# ==================== 图表6：波动率分布直方图 ====================
def plot_volatility_histogram(volatility):
    """绘制波动率分布直方图"""
    plt.figure(figsize=(10, 6))

    plt.hist(volatility, bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    plt.axvline(x=volatility.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {volatility.mean():.1f}%')
    plt.axvline(x=volatility.median(), color='green', linestyle='--', linewidth=2,
                label=f'Median: {volatility.median():.1f}%')

    plt.xlabel('Annualized Volatility (%)', fontsize=12)
    plt.ylabel('Number of Banks', fontsize=12)
    plt.title('Bank Stocks - Volatility Distribution', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('chart_06_volatility_histogram.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ 图表6已保存: chart_06_volatility_histogram.png")


# ==================== 打印结果 ====================
def print_results(volatility, cum_returns, deviation):
    """打印分析结果"""
    print("\n" + "=" * 70)
    print("银行股15年分析结果 (2011-2026)")
    print("=" * 70)
    print(f"分析期间: {deviation.index[0].strftime('%Y-%m-%d')} 至 {deviation.index[-1].strftime('%Y-%m-%d')}")
    print(f"交易日数: {len(deviation)}")
    print(f"银行数量: {len(deviation.columns)}")

    # 波动率排名
    print("\n" + "-" * 50)
    print("年化波动率排名（由低到高）")
    print("-" * 50)
    vol_sorted = volatility.sort_values()
    for i, (bank, vol) in enumerate(vol_sorted.items(), 1):
        cn_name = NAME_CN.get(bank, bank)
        bar = "█" * int(vol / 2)
        print(f"{i:2}. {cn_name:8} : {vol:6.2f}% {bar}")

    # 累计超额收益排名
    print("\n" + "-" * 50)
    print("累计超额收益排名（跑赢板块最多的银行）")
    print("-" * 50)
    cum_sorted = cum_returns.sort_values(ascending=False)
    for i, (bank, ret) in enumerate(cum_sorted.items(), 1):
        cn_name = NAME_CN.get(bank, bank)
        sign = "+" if ret > 0 else ""
        print(f"{i:2}. {cn_name:8} : {sign}{ret:6.2f}%")

    # 统计摘要
    print("\n" + "-" * 50)
    print("统计摘要")
    print("-" * 50)
    print(f"最低波动率 : {volatility.min():.2f}% ({NAME_CN.get(volatility.idxmin(), volatility.idxmin())})")
    print(f"最高波动率 : {volatility.max():.2f}% ({NAME_CN.get(volatility.idxmax(), volatility.idxmax())})")
    print(f"平均波动率 : {volatility.mean():.2f}%")
    print(f"\n累计超额收益最高 : {cum_returns.max():.2f}% ({NAME_CN.get(cum_returns.idxmax(), cum_returns.idxmax())})")
    print(f"累计超额收益最低 : {cum_returns.min():.2f}% ({NAME_CN.get(cum_returns.idxmin(), cum_returns.idxmin())})")


# ==================== 主程序 ====================
def main():
    print("=" * 70)
    print("A股银行股15年分析")
    print("数据源: baostock")
    print("时间: 2011-01-01 至 2026-04-08")
    print("=" * 70)

    # 登录
    print("\n[1] 登录 baostock...")
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    print("登录成功")

    # 获取数据
    print("\n[2] 获取银行股数据...")
    print("-" * 50)

    all_returns = pd.DataFrame()
    failed = []

    for i, (code, name) in enumerate(BANK_STOCKS.items(), 1):
        print(f"[{i}/{len(BANK_STOCKS)}] {name}...")
        ret = get_bank_data(code, name)
        if ret is not None:
            all_returns[name] = ret
        else:
            failed.append(name)
        time.sleep(0.3)

    bs.logout()
    print("-" * 50)
    print(f"成功: {len(all_returns.columns)}只, 失败: {len(failed)}只")

    if all_returns.empty:
        print("错误: 未获取到数据")
        return

    # 计算指标
    print("\n[3] 计算超额收益...")
    all_returns['板块均值'] = all_returns.mean(axis=1)
    deviation = all_returns.drop('板块均值', axis=1).subtract(all_returns['板块均值'], axis=0)

    print("[4] 计算波动率...")
    volatility = deviation.std() * np.sqrt(252)
    cum_returns = deviation.sum()

    # 打印结果
    print_results(volatility, cum_returns, deviation)

    # 生成图表（分开显示）
    print("\n[5] 生成图表...")
    print("-" * 50)

    plot_excess_return_line(deviation)  # 图表1：累计超额收益折线图
    plot_volatility_bar(volatility)  # 图表2：波动率排名柱状图
    plot_deviation_range(deviation)  # 图表3：板块偏离度范围图
    plot_volatility_vs_return(volatility, cum_returns)  # 图表4：波动率vs收益散点图
    plot_key_banks_line(deviation)  # 图表5：重点银行对比图
    plot_volatility_histogram(volatility)  # 图表6：波动率分布直方图

    print("\n" + "=" * 70)
    print("分析完成！共生成6张图表")
    print("=" * 70)


if __name__ == "__main__":
    main()
