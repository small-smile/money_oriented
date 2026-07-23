# kelly_distribution.py
"""
模拟并绘制 100 轮下注后最终资金的概率分布图。
对比三种下注比例：full Kelly, 0.5*Kelly, 0.25*Kelly
"""

import numpy as np
import matplotlib.pyplot as plt


def kelly_fraction(b: float, p: float) -> float:
    q = 1.0 - p
    f_star = (b * p - q) / b
    return max(0.0, min(1.0, f_star))


def simulate_final_wealths(W0, f, b, p, n_rounds, n_sims, seed=None):
    if seed is not None:
        np.random.seed(seed)
    # 随机胜负矩阵
    r = np.random.rand(n_sims, n_rounds) < p
    mult_win = 1.0 + b * f
    mult_loss = 1.0 - f
    wealth = np.full(n_sims, W0, dtype=float)
    for j in range(n_rounds):
        win_mask = r[:, j]
        wealth[win_mask] *= mult_win
        wealth[~win_mask] *= mult_loss
    return wealth


def main():
    # 参数（可修改）
    b = 1.0  # 净赔率（下注 1，赢时净赚 b）
    p = 0.6  # 赢的概率
    W0 = 100.0  # 初始资金
    n_rounds = 100
    n_sims = 200000
    seed = 42

    f_star = kelly_fraction(b, p)
    fractions = {
        f"1.5Kelly ({f_star:.3f})": 1.5 * f_star,
        f"Kelly ({f_star:.3f})": f_star,
        f"0.5*Kelly ({0.5 * f_star:.3f})": 0.5 * f_star,
        f"0.25*Kelly ({0.25 * f_star:.3f})": 0.25 * f_star,
    }

    results = {}
    for name, f in fractions.items():
        w = simulate_final_wealths(W0=W0, f=f, b=b, p=p, n_rounds=n_rounds, n_sims=n_sims, seed=seed)
        results[name] = w
        # 打印一些统计量
        print(
            f"{name}: mean={w.mean():.2f}, median={np.median(w):.2f}, 5%={np.percentile(w, 5):.2f}, 95%={np.percentile(w, 95):.2f}")

    # 绘图：左侧线性 x 轴（可能被长尾主导），右侧对数 x 轴（更清晰）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    bins_linear = 100
    for name, w in results.items():
        ax1.hist(w, bins=bins_linear, alpha=0.6, label=name, histtype='stepfilled')
    ax1.set_xlabel("Final wealth after {} rounds".format(n_rounds))
    ax1.set_ylabel("Frequency")
    ax1.set_title("Linear scale (x)")
    ax1.legend()

    # 对数 x 轴：用对数间隔的 bins，更均匀展示长尾
    # 取所有样本的最小/最大（>0）
    all_vals = np.concatenate(list(results.values()))
    vmin = max(all_vals.min(), 1e-8)
    vmax = all_vals.max()
    # 避免 vmax==vmin 的情况
    if vmax <= vmin:
        vmax = vmin * 10.0
    bins_log = np.logspace(np.log10(vmin), np.log10(vmax), 100)
    for name, w in results.items():
        ax2.hist(w, bins=bins_log, alpha=0.6, label=name, histtype='stepfilled')
    ax2.set_xscale('log')
    ax2.set_xlabel("Final wealth (log scale) after {} rounds".format(n_rounds))
    ax2.set_ylabel("Frequency")
    ax2.set_title("Log-x scale (shows long tail)")
    ax2.legend()

    plt.tight_layout()
    plt.show()

    # 可选：保存图片
    fig.savefig("kelly_final_wealth_distribution.png", dpi=200)
    print("Saved figure to kelly_final_wealth_distribution.png")


if __name__ == "__main__":
    main()
