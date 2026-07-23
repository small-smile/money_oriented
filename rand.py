import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)  # 可复现
steps = 1000  # 步数
walks = 1000  # 曲线条数

# 每步增量来自标准正态分布，尺寸 (步数, 曲线数)
increments = np.random.normal(loc=0, scale=1, size=(steps, walks))
positions = increments.cumsum(axis=0)  # 累积得到每条漫步的位置

plt.figure(figsize=(12, 6))
# 一次性绘制所有列，用极高的透明度和细线
plt.plot(range(steps), positions, alpha=0.03, linewidth=0.5, color='black')

plt.title(f'1D Random Walks ({walks} walks × {steps} steps)')
plt.xlabel('Step')
plt.ylabel('Value')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
