import numpy as np
import pandas as pd
from itertools import product

INIT_CASH = 10000.0
TARGET = 15000.0
MAX_DAYS = 1000
DAILY_DIVIDEND_PER_SHARE = 6.0 / 250
DAILY_CASH_RATE = 2.0 / 100 / 250
PRICE_MIN = 60.0
PRICE_MAX = 200.0
PRICE_START = 100.0
PRICE_STEP = .5

np.random.seed(42)


def simulate(init_ratio, add_ratio):
    cash = INIT_CASH
    shares = 0.0
    price = PRICE_START
    last_buy_price = price
    if price <= PRICE_START and shares == 0:
        invest = cash * init_ratio
        shares = invest / price
        cash -= invest
        last_buy_price = price

    for day in range(1, MAX_DAYS + 1):
        cash += cash * DAILY_CASH_RATE
        cash += shares * DAILY_DIVIDEND_PER_SHARE

        change = np.random.choice([-PRICE_STEP, PRICE_STEP])
        price += change
        price = np.clip(price, PRICE_MIN, PRICE_MAX)

        if shares > 0 and price >= PRICE_MAX:
            cash += shares * price
            shares = 0.0
            last_buy_price = price
        elif shares == 0 and price <= PRICE_START:
            invest = cash * init_ratio
            if invest > 0:
                shares = invest / price
                cash -= invest
                last_buy_price = price
        elif shares > 0 and price < PRICE_START and (last_buy_price - price) >= PRICE_STEP:
            add_cash = cash * add_ratio
            if add_cash > 0:
                if add_cash > cash:
                    add_cash = cash
                add_shares = add_cash / price
                shares += add_shares
                cash -= add_cash
                last_buy_price = price

        total_asset = cash + shares * price
        if total_asset >= TARGET:
            return day
    return MAX_DAYS + 1


def monte_carlo(params, n_sim=50):
    days_list = [simulate(params[0], params[1]) for _ in range(n_sim)]
    days_arr = np.array(days_list)
    success = days_arr <= MAX_DAYS
    if np.any(success):
        mean_days = np.mean(days_arr[success])
    else:
        mean_days = np.inf
    success_rate = np.mean(success)
    return mean_days, success_rate


init_ratios = np.arange(0.1, 1.0, 0.1)
add_ratios = np.arange(0.1, 1.0, 0.1)
results = []

print("Parameter search (50 simulations per combo)...")
for ir, ar in product(init_ratios, add_ratios):
    mean_days, success_rate = monte_carlo((ir, ar), n_sim=50)
    results.append({
        'init_ratio': ir,
        'add_ratio': ar,
        'mean_days': mean_days,
        'success_rate': success_rate
    })
    print(f"init={ir:.1f}, add={ar:.1f} -> mean_days={mean_days:.1f}, success={success_rate:.0%}")

df = pd.DataFrame(results)
df_valid = df[df['success_rate'] > 0.5]
if len(df_valid) > 0:
    best = df_valid.loc[df_valid['mean_days'].idxmin()]
    print("\n===== Best parameters =====")
    print(f"Initial investment ratio: {best['init_ratio']:.1f}")
    print(f"Add ratio: {best['add_ratio']:.1f}")
    print(f"Average days to target: {best['mean_days']:.1f}")
    print(f"Success rate: {best['success_rate']:.0%}")
else:
    print("No parameter group with success rate > 50% found.")

# ----- 等高线图（英文） -----
try:
    import matplotlib.pyplot as plt

    pivot = df.pivot(index='init_ratio', columns='add_ratio', values='mean_days')
    X = pivot.columns.values
    Y = pivot.index.values
    Z = pivot.values

    plt.figure(figsize=(8, 6))
    contour = plt.contourf(X, Y, Z, levels=20, cmap='viridis_r')
    plt.colorbar(contour, label='Mean days to reach 15000 (lower is better)')
    plt.xlabel('Add ratio')
    plt.ylabel('Initial investment ratio')
    plt.title('Contour plot of time to target')
    plt.tight_layout()
    plt.show()
except ImportError:
    print("matplotlib not installed, skip plotting.")
