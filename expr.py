import random


# 用这个全局标志来消除嵌套括号的影响
hasBrackets = False

# 生成指数（0~8）可修改概率分布，可以想想怎么调整概率分布会更难，我的选择是，两头多，中间少
def rand_index():
    return str(random.choices(range(9), weights=[2, 1, 1, 1, 1, 1, 1, 1, 2])[0])

# 生成随机整数，可以包含前导零，这个也得加一定的概率分布，不然数据太过随机，我这里也是两头多，中间少
def rand_int():
    return str(random.choices(range(10), weights=[2, 1, 1, 1, 1, 1, 1, 1, 1, 2])[0])

# 生成带符号整数
def rand_signed_int():
    sign = random.choice(['+', '-'])
    return sign + rand_int()

# 生成幂函数
def rand_power():
    base = rand_int()
    index = rand_index()
    return base +'*'+ 'x' +'^' + index

# 生成表达式因子
def rand_expr_factor():
    global hasBrackets
    hasBrackets = True
    expr = rand_expr()
    hasBrackets = False  # 这里能够消除嵌套括号，想想为啥
    if random.random() < 0.4:
        return '(' + expr + ')'
    return '(' + expr + ')^' + rand_index()

# 生成常数因子或变量因子
def rand_const_or_var():
    if random.random() < 0.5:
        return rand_signed_int()
    else:
        return rand_power()

# 生成因子，这里的...的取值可以调整数据的难度
def rand_factor():
    if random.random() < 0.5 and not hasBrackets:  # 消括号操作
        return rand_expr_factor()
    elif random.random() < 0.5:
        return rand_signed_int()
    else:
        return rand_power()

# 生成项
def rand_term():
    final_term = rand_factor()
    for _ in range(random.randint(1, 3)):
        final_term = final_term + " * " + rand_factor()
    return final_term

# 定义函数，生成表达式
def rand_expr():
    term = rand_term()
    for _ in range(random.randint(1, 3)):
        op = random.choice(['+', '-'])
        term = term + " " + op + " " + rand_term()
    return term

# 生成表达式
def generate_expr(num, output_file):
    with open(output_file, 'w') as f:
        for _ in range(num):
            expr = rand_expr()
            # 确保表达式长度足够长
            while len(expr) < 30:  # 填上你想要的最短数据长度
                expr += ' + ' + rand_term()
            f.write(expr + '\n')

# 调用函数生成表达式
generate_expr(10, 'D:/py_vsc/expr.txt')