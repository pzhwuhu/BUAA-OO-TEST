import sympy as sp
import subprocess
import random
import os

# 定义一个全局变量，用于判断是否需要添加括号
hasBrackets = False

# 生成一个随机索引
def rand_index():
    return str(random.choices(range(9), weights=[2, 1, 1, 1, 1, 1, 1, 1, 2])[0])

# 生成一个随机整数 
def rand_int():
    return str(random.choices(range(10), weights=[2, 1, 1, 1, 1, 1, 1, 1, 1, 2])[0])

# 生成一个随机带符号的整数
def rand_signed_int():
    sign = random.choice(['+', '-'])
    return sign + rand_int()

# 生成一个随机幂
def rand_power():
    base = rand_int()
    index = rand_index()
    return f"{base}*x^{index}"

# 生成一个随机表达式因子
def rand_expr_factor():
    global hasBrackets
    hasBrackets = True
    expr = rand_expr()
    hasBrackets = False
    if random.random() < 0.4: # 40%的概率不加指数
        return f'({expr})'
    return f'({expr})^{rand_index()}'

# 生成一个随机因子
def rand_factor():
    # 50%的概率生成表达式因子，50%的概率生成带符号整数
    if random.random() < 0.5 and not hasBrackets:
        return rand_expr_factor()
    elif random.random() < 0.5:
        return rand_signed_int()
    else:
        return rand_power()

# 生成一个随机项
def rand_term():
    if random.random() < 0.5:
        final_term = random.choice(['+ ', '- ']) + rand_factor()
    else:
        final_term = rand_factor()
    # 随机生成1~10个因子
    for _ in range(random.randint(1, 10)):
        final_term += " * " + rand_factor()
    return final_term

# 生成一个随机表达式
def rand_expr():
    if random.random() < 0.5:
        term = random.choice([' + ', ' - ']) + rand_term()
    else:
        term = rand_term()
    # 随机生成1~10项
    for _ in range(random.randint(1, 10)):
        op = random.choice(['+', '-'])
        term += f" {op} " + rand_term()
    return term

# 生成一个单独的表达式
def generate_single_expr():
    expr = rand_expr()
    # 设置表达式最短长度为30
    while len(expr) < 30:
        expr += ' + ' + rand_term()
    return expr

# 生成测试用例
def generate_test_cases(num_cases, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i in range(num_cases):
        expr = generate_single_expr()
        with open(os.path.join(output_dir, f'test{i}.txt'), 'w') as f:
            f.write(expr + '\n')

# 比较两个表达式是否相等
def compare_expr(expr_input, output_expr):
    # expr_input = expr_input.replace('^', '**')
    # output_expr = output_expr.replace('^', '**')
    try:
        expr1 = sp.sympify(expr_input)
        expr2 = sp.sympify(output_expr)
        return sp.simplify(expr1 - expr2) == 0
    except sp.SympifyError:
        return False

# 运行测试用例
def run_test_case(test_file):
    with open(test_file, 'r') as f:
        expr_input = f.read().strip()
    process = subprocess.Popen(
        ['java', '-jar', 'hw1.jar'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # 运行时间限制
        
    ) 
    print(f"Running test {test_file}...")
    stdout, stderr = process.communicate(input=expr_input.encode())
    output_expr = stdout.decode().strip()
    if process.returncode != 0:
        print(f"Error in hw1.jar for {test_file}: {stderr.decode()}")
        return False, expr_input, output_expr
    return compare_expr(expr_input, output_expr), expr_input, output_expr

# 主函数
def main():
    # 生成num_cases个测试用例
    num_cases = 100
    output_dir = 'tests'
    diff_file = 'diff.txt'
    generate_test_cases(num_cases, output_dir)
    accepted = 0
    # 逐个运行测试用例
    for i in range(num_cases):
        test_file = os.path.join(output_dir, f'test{i}.txt')
        is_eq, expr_input, output_expr = run_test_case(test_file)
        print(f"Test {i} Result: " + ("等值" if is_eq else "不等值"))
        if is_eq:
            accepted += 1
        else:
            print("find difference in test " + str(i) + "!")
            with open(diff_file, 'a') as f:
                f.write(f"Test {i}:\n")
                f.write(f"Input:  {expr_input}\n")
                f.write(f"Output: {output_expr}\n")
                f.write(f"Expected: {sp.simplify(expr_input)}\n\n")
    print("Accepted: {}/{}".format(accepted, num_cases))


if __name__ == '__main__':
    main()