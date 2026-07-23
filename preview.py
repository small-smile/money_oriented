import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# 设置中文字体（避免中文乱码，可根据系统自行调整）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# 生成 x 轴数据：从 -6 到 6，间距足够小以保证曲线平滑
x = np.linspace(-6, 6, 500)

# 计算不同参数下的概率密度函数值
pdf_std = norm.pdf(x, loc=0, scale=1)  # 标准正态分布 N(0,1)
pdf_wide = norm.pdf(x, loc=0, scale=2)  # N(0,2)，标准差更大，曲线更“矮胖”

# 绘图
plt.figure(figsize=(8, 5))
plt.plot(x, pdf_std, label='标准正态分布 N(0,1)', linewidth=2)
plt.plot(x, pdf_wide, label='正态分布 N(0,2)', linewidth=2, linestyle='--')

# 添加标注和样式
plt.title('正态分布概率密度曲线', fontsize=14)
plt.xlabel('数值', fontsize=12)
plt.ylabel('概率密度', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)

# 显示图形
plt.show()
