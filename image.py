import cv2
import numpy as np

img = cv2.imread('/home/zhu/Documents/beauty.jpg')

# 乘以常数（亮度增强）
brighter = cv2.convertScaleAbs(img, alpha=1.1, beta=0)  # alpha = k
# 或手动操作：
darker = np.clip(img * 0.7, 0, 255).astype(np.uint8)
brighter_two = cv2.convertScaleAbs(img, alpha=1.15, beta=0)  # alpha = k

cv2.imshow('darker', darker)
cv2.imshow('origin', img)
cv2.imshow('brighter', brighter)
cv2.imshow('brighter_15', brighter_two)
cv2.waitKey(0)
cv2.destroyAllWindows()
