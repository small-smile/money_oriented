from sympy import symbols, diff, latex

# 定义符号变量 p
p = symbols('p')

# 表达式：p^8 * (1-p)^2
expr = p ** 8 * (1 - p) ** 2

# 对 p 求导
derivative = diff(expr, p)


print(derivative)