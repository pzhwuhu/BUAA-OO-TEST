import random
import os
import json
import re

def remove_leading_zeros(text):
    return re.sub(r'\b0+(\d+)', r'\1', text)

def preTreatment(string):
    return remove_leading_zeros(string.replace('^','**').replace(" ", "").replace("\t",""))

##############################--全局变量的定义--##############################
config = json.load(open("config3.json", encoding='utf-8'))
isgenerateFun = False   # 是否正在产生自定义函数

# 存储已声明的自定义普通函数：键为函数名 ('g','h')，值为形参个数
ordinary_info = {}  
# 记录递推函数的形参个数（递推函数统一只允许一个全局的参数个数）
recursive_param_count = None

##############################--小函数--##############################
def generate_blank():
    if random.random() < float(config["blank_prob"]):
        return ' ' if random.random() < 0.8 else '\t'
    else:
        return ''

def generate_sign():
    if random.random() < float(config["sign_prob"]):
        return ''
    else:
        return '+' if random.random() > 0.5 else '-'
        
def generate_zero():
    if random.random() < float(config["zero_prob"]):
        return '0'
    else:
        return ''

def generate_exp():
    # 生成指数部分，如 "^+3"（指数一定为非负数）
    string = '^' + generate_blank()
    if random.random() > float(config["sign_prob"]):
        string += '+'
    string += generate_zero() + str(random.randint(0, 3))
    return string

##############################--新增：三角函数因子生成--##############################
def generate_trig(floor, allow_delta=True, allowed_calls=None):
    # 生成三角函数因子，形式： sin 或 cos 后跟括号内表达式，可选指数部分
    func = random.choice(['sin', 'cos'])
    s = func + generate_blank() + '(' + generate_blank() + generate_factor(floor - 1, allow_delta, allowed_calls) + generate_blank() + ')'
    if random.random() < float(config["exprFactor_exp"]):
        s += generate_blank() + generate_exp()
    return s

##############################--函数调用生成函数--##############################
def generate_ordinary_func_call(declared_ordinary, floor):
    # declared_ordinary：已声明普通函数列表（例如 ['g','h']）
    fname = random.choice(declared_ordinary)
    arity = ordinary_info[fname]
    args = []
    for i in range(arity):
        # 使用 generate_factor 且传入 allow_delta=False，确保不生成求导算子
        args.append(generate_factor(int(config["floor"])//2, allow_delta=False,
                                  allowed_calls={"ordinary": list(ordinary_info.keys()),
                                                 "recursive": []}))
    return fname + '(' + ','.join(args) + ')'

def generate_recursive_func_call(floor):
    global recursive_param_count
    # 随机生成一个 0 到 5 之间的序号
    num = random.randint(0, 5)
    args = []
    for i in range(recursive_param_count):
        # 使用 generate_factor 且传入 allow_delta=False
        args.append(generate_factor(int(config["floor"])//2, allow_delta=False,
                                  allowed_calls={"ordinary": list(ordinary_info.keys()),
                                                 "recursive": []}))
    return "f{" + str(num) + "}" + '(' + ','.join(args) + ')'

##############################--表达式、项、因子的生成（增加 allowed_calls 参数）--##############################
def generate_factor(floor, allow_delta=True, allowed_calls=None):
    if floor <= 0:
        return generate_constant() if random.random() < 0.5 else generate_power()
    control = int(config["floor"]) - floor + 1
    deltaProb = float(config["deltaFactor"]) / control if allow_delta else 0
    ordinaryCallProb = float(config.get("ordinaryFuncCallProb", 0.2)) if (allowed_calls and allowed_calls.get("ordinary") and len(allowed_calls["ordinary"]) > 0) else 0
    recursiveCallProb = float(config.get("recursiveFuncCallProb", 0.2)) if (allowed_calls and allowed_calls.get("recursive") and len(allowed_calls["recursive"]) > 0) else 0
    exprProb = float(config["exprFactor"]) / control
    totalFuncProb = ordinaryCallProb + recursiveCallProb
    r = random.random()
    if r < deltaProb:
         return generate_delta(floor - 1)
    r -= deltaProb
    if r < totalFuncProb:
         # 同时允许调用普通和递推函数，则按比例选择
         sub_r = random.random() * totalFuncProb
         if sub_r < ordinaryCallProb:
              return generate_ordinary_func_call(allowed_calls["ordinary"], floor)
         else:
              return generate_recursive_func_call(floor)
    r -= totalFuncProb
    if r < exprProb:
         return generate_exprF(floor - 1, allow_delta, allowed_calls)
    r -= exprProb
    choice = random.random()
    if choice < 0.33:
         return generate_constant()
    elif choice < 0.66:
         return generate_power()
    else:
         return generate_trig(floor, allow_delta, allowed_calls)

def generate_term(floor, allow_delta=True, allowed_calls=None):
    s = generate_sign() + generate_blank() + generate_factor(floor, allow_delta, allowed_calls)
    if isgenerateFun:
        factor_limit = int(config["myFun_factor_limit"]) / (int(config["myFun_floor"]) - floor + 1)
    else:
        factor_limit = int(config["factor_limit"]) / (int(config["floor"]) - floor + 1)
    for i in range(int(factor_limit) - 1):
         s += generate_blank() + '*' + generate_blank() + generate_factor(floor, allow_delta, allowed_calls)
    return s

def generate_expr(floor, allow_delta=True, allowed_calls=None):
    s = generate_blank() + generate_sign() + generate_blank() + generate_term(floor, allow_delta, allowed_calls) + generate_blank()
    if isgenerateFun:
        term_limit = int(config["myFun_term_limit"]) / (int(config["myFun_floor"]) - floor + 1)
    else:
        term_limit = int(config["term_limit"]) / (int(config["floor"]) - floor + 1)
    for i in range(int(term_limit) - 1):
         s += '+' if random.random() > 0.5 else '-'
         s += generate_blank() + generate_term(floor, allow_delta, allowed_calls) + generate_blank()
    return s

##############################--其它因子生成--##############################
def generate_delta(floor):
    s = 'dx' + generate_blank() + '(' + generate_blank()
    if floor <= 1:
        s += generate_constant() if random.random() < 0.5 else generate_power()
    else:
        # 在生成求导算子时依然允许求导（不限制 allow_delta ）
        s += generate_expr(floor - 1, allow_delta=True, allowed_calls={"ordinary": [], "recursive": []})
    s += generate_blank() + ')'
    return s

def generate_constant():
    constFactor_zero = float(config["constFactor_zero"])
    constFactor_big = float(config["constFactor_big"])
    p = random.random()
    if p < constFactor_zero:
        return generate_sign() + '0'
    elif p < constFactor_zero + constFactor_big:
        tmp = random.randint(-999999999, 999999999)
    else:
        tmp = random.randint(-20, 20)
    return (generate_sign().replace('-', '+') if tmp > 0 else '') + str(tmp)

def generate_power():
    return 'x' + generate_blank() + generate_exp()

def generate_exprF(floor, allow_delta=True, allowed_calls=None):
    s = '(' + generate_blank() + generate_expr(floor, allow_delta, allowed_calls) + generate_blank() + ')'
    if random.random() < float(config["exprFactor_exp"]):
        s += generate_blank() + generate_exp()
    return s

##############################--生成自定义普通函数定义（只允许 g 与 h）--##############################
def generate_ordinary_functions():
    global ordinary_info
    defs = []
    n = random.randint(0, 2)
    available = ["g", "h"]
    for i in range(n):
        fname = random.choice(available)
        available.remove(fname)
        param_count = random.choice([1, 2])
        if param_count == 1:
            params = [random.choice(["x", "y"])]
        else:
            params = ["x", "y"]
        # 定义时生成函数体使用 allow_delta=False，保证不生成求导算子
        allowed = {"ordinary": list(ordinary_info.keys()), "recursive": []}
        x_expr = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed)
        y_expr = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed).replace("x", "y")
        if param_count == 1:
            if params == ["x"]:
                expr = x_expr
            else:
                expr = y_expr
        else:
            sign = "+" if random.random() < 0.5 else "-"
            expr = f"{x_expr} {sign} {y_expr}"
        defs.append(f"{fname}({','.join(params)}) = {expr}")
        ordinary_info[fname] = param_count
    return defs

##############################--生成自定义递推函数定义（只允许 f）--##############################
def generate_recursive_functions():
    global recursive_param_count
    defs = []
    m = random.randint(0, 1)
    if m == 0:
        return defs, m
    # 递推函数统一形参个数为 1～2（且一致）
    param_count = random.choice([1, 2])
    if param_count == 1:
        params = [random.choice(["x", "y"])]
    else:
        params = ["x", "y"]
    recursive_param_count = param_count
    # f{0}：允许调用已声明的普通函数（递推部分为空），且不生成求导算子
    allowed0 = {"ordinary": list(ordinary_info.keys()), "recursive": []}
    expr0_x = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed0)
    expr0_y = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed0).replace("x", "y")
    if param_count == 1:
        expr0 = expr0_x if params == ["x"] else expr0_y
    else:
        sign = "+" if random.random() < 0.5 else "-"
        expr0 = f"{expr0_x} {sign} {expr0_y}"
    line0 = f"f{{0}}({','.join(params)}) = {expr0}"
    # f{1}：允许调用 f{{0}} 及普通函数，不生成求导算子
    allowed1 = {"ordinary": list(ordinary_info.keys()), "recursive": []}
    expr1_x = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed1)
    expr1_y = generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls=allowed1).replace("x", "y")
    if param_count == 1:
        expr1 = expr1_x if params == ["x"] else expr1_y
    else:
        sign = "+" if random.random() < 0.5 else "-"
        expr1 = f"{expr1_x} {sign} {expr1_y}"
    line1 = f"f{{1}}({','.join(params)}) = {expr1}"
    # f{n}：固定格式，右侧必须包含 f{{n-1}} 与 f{{n-2}} 各一次，生成参数使用 generate_factor
    allowedn = {"ordinary": list(ordinary_info.keys()), "recursive": []}
    args1 = []
    args2 = []
    for i in range(param_count):
        arg = generate_factor(int(config["floor"])//2, allow_delta=False, allowed_calls=allowedn)
        if params[i] == "y":
            arg = arg.replace("x", "y")
        args1.append(arg)
    for i in range(param_count):
        arg = generate_factor(int(config["floor"])//2, allow_delta=False, allowed_calls=allowedn)
        # 根据参数类型替换：如果对应形参是 "y"，则将生成的因子中的 "x" 替换为 "y"
        if params[i] == "y":
            arg = arg.replace("x", "y")
        args2.append(arg)
    args1 = ",".join(args1)
    args2 = ",".join(args2)
    extra = ""
    if random.random() < 0.6:
         extra = " + " + generate_expr(int(config["floor"])//2, allow_delta=False, allowed_calls={"ordinary": list(ordinary_info.keys()), "recursive": []}).replace("x", params[0])
    exprn = f"{generate_constant()}*f{{n-1}}({args1})" + (" - " if random.random() < 0.5 else " + ") + f"{generate_constant()}*f{{n-2}}({args2})" + extra
    line_n = f"f{{n}}({','.join(params)}) = {exprn}"
    group = [line0, line1, line_n]
    random.shuffle(group)
    return group, m

##############################--主函数：按照新格式输出数据--##############################
if __name__ == "__main__":
    config = json.load(open("config3.json", encoding='utf-8'))
    ordinary_defs = generate_ordinary_functions()
    recursive_defs, m = generate_recursive_functions()
    # 修改：如果有递推函数定义，则允许递推调用，令 allowed_calls["recursive"] 为非空
    if m != 0:
        allowed_recursive = [0, 1]  # 任何非空列表即可
    else:
        allowed_recursive = []
    allowed_all = {"ordinary": list(ordinary_info.keys()), "recursive": allowed_recursive}
    final_expr = generate_expr(int(config["floor"]), allow_delta=True, allowed_calls=allowed_all)
    output_lines = []
    output_lines.append(str(len(ordinary_defs)))
    output_lines.extend(ordinary_defs)
    output_lines.append(str(m))
    output_lines.extend(recursive_defs)
    output_lines.append(final_expr)
    print("\n".join(output_lines))
