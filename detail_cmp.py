import sympy as sp


# 读取表达式
# # 简化表达式
expr1 = sp.sympify(input("请输入第一个表达式: "))
expr1 = sp.simplify(expr1)
print('expr1 simplified!')
print(expr1)
expr2 = sp.sympify(input("请输入第二个表达式: "))
expr2 = sp.simplify(expr2)
print('expr2 simplified!')

print(expr2)

# 比较表达式是否等值
if sp.simplify(expr1 - expr2) == 0:
    print("两个表达式等值")
else:
    print("两个表达式不等值")
    print(expr1)
    print(expr2)
    
    