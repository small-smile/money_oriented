# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs

# 1. 生成一些模拟数据（二维点）
X, _ = make_blobs(n_samples=300, centers=4, cluster_std=0.6, random_state=42)

# 2. 定义 k-means 模型，指定簇数 k=4
kmeans = KMeans(n_clusters=4, random_state=42)
kmeans.fit(X)

# 3. 获取聚类结果
y_kmeans = kmeans.predict(X)

# 4. 可视化
plt.scatter(X[:, 0], X[:, 1], c=y_kmeans, s=30, cmap='viridis')  # 数据点
centers = kmeans.cluster_centers_  # 聚类中心
plt.scatter(centers[:, 0], centers[:, 1], c='red', s=200, marker='X')  # 用红色X标记中心
plt.title("K-means Clustering (k=4)")
plt.show()
