from random import choice, randint, random

# 常量定义
MAX_VALUE = 200
MAX_M_VALUE = 200
MAX_AGE = 200
MAX_NAME_LEN = 10

# 支持的指令列表（移除重复的 qsp）
instrs = ['ap', 'ar', 'mr', 'at', 'dt', 'att', 'dft', 'qv', 'qci', 'qts', 'qtav', 'qba',
          'coa', 'doa', 'ca', 'da', 'foa', 'qsp', 'qbc', 'qra', 'qtvs', 'qcs']

def generate(instr_num=10000, people_num=800, tag_num=500, account_num=200, article_num=1000):
    """主生成函数，根据指定概率选择数据生成模式"""
    mode_probabilities = {
        'stress_test_data': 0.1,                   
        'normal_data': 0.05,                        
        'extend_data': 0.05,                     
        'special_qtvs': 0.25,                        
        'structured_social_media_test': 0.25,      
        'special_qba_stress_test': 0.3         
    }
    
    k = random()
    cumulative_prob = 0.0
    for mode, prob in mode_probabilities.items():
        cumulative_prob += prob
        if k < cumulative_prob:
            if mode == 'stress_test_data':
                return stress_test_data(instr_num, people_num, tag_num, account_num, article_num)
            elif mode == 'normal_data':
                return normal_data(instr_num, people_num, tag_num, account_num, article_num)
            elif mode == 'extend_data':
                return extend_data(instr_num, people_num, tag_num, account_num, article_num)
            elif mode == 'special_qtvs':
                return special_qtvs(instr_num, people_num)
            elif mode == 'structured_social_media_test':
                return structured_social_media_test(instr_num, people_num, tag_num)
            elif mode == 'special_qba_stress_test':
                return special_qba_stress_test(instr_num, people_num, tag_num)

    return structured_social_media_test(instr_num, people_num, tag_num, account_num, article_num)

def random_name(prefix, id):
    """生成随机名称，如 Person_1, Account_1"""
    return f"{prefix}_{id}"

def ln_generator(n=90, sparse=True if random() < 0.5 else False):
    """生成 load_network 指令"""
    lines = [f"load_network {n}"]
    # 节点 ID
    lines.append(" ".join(str(i) for i in range(1, n + 1)))
    # 节点名称
    lines.append(" ".join(f"Person_{i}" for i in range(1, n + 1)))
    # 节点年龄
    lines.append(" ".join(str(randint(0, MAX_AGE)) for _ in range(1, n + 1)))
    # 关系矩阵（n-1 行）
    for i in range(1, n):
        row = []
        for j in range(1, i + 1):
            if sparse:
                value = randint(0, int(MAX_VALUE * 0.3)) if random() < 0.1 else 0
            else:
                value = 1 if random() < 0.5 else 0
            row.append(str(value))
        lines.append(" ".join(row))
    return '\n'.join(lines)

def locate_tag(person_id, people_num, tag_num):
    """为用户分配标签 ID"""
    tags_per_person = max(1, int(tag_num / people_num))
    return person_id * tags_per_person + randint(0, tags_per_person - 1)

def locate_tag_overlapped(person_id, people_num, tag_num):
    """为用户分配重叠标签 ID"""
    tags_per_person = max(1, int(tag_num / people_num / 2))
    return person_id * tags_per_person + randint(0, tags_per_person - 1)

def person_instr(id):
    """生成 add_person 指令"""
    return f"ap {id} {random_name('Person', id)} {randint(0, MAX_AGE)}"

def single_arg_instr(instr_name, id):
    """生成单参数指令"""
    return f"{instr_name} {id}"

def triplet_arg_instr(instr_name, id1, id2, value):
    """生成三参数指令"""
    return f"{instr_name} {id1} {id2} {value}"

def twin_arg_instr(instr_name, id1, id2):
    """生成双参数指令"""
    return f"{instr_name} {id1} {id2}"

def zero_arg_instr(instr_name):
    """生成无参数指令"""
    return f"{instr_name}"

def official_account_instr(instr_name, person_id, account_id):
    """生成公众号相关指令"""
    if instr_name == "coa":
        return f"coa {person_id} {account_id} {random_name('Account', account_id)}"
    return f"{instr_name} {person_id} {account_id}"

def article_instr(instr_name, person_id, account_id, article_id):
    """生成文章相关指令"""
    if instr_name == "ca":
        return f"ca {person_id} {account_id} {article_id} {random_name('Article', article_id)}"
    return f"{instr_name} {person_id} {account_id} {article_id}"

def normal_data(instr_num, people_num, tag_num, account_num, article_num):
    """生成常规测试数据"""
    instrlist = []
    created_accounts = set()
    created_articles = set()
    # 添加用户
    for i in range(1, randint(int(people_num * 0.7), people_num)):
        instrlist.append(person_instr(i))
    # 添加标签
    for i in range(1, randint(int(tag_num * 0.7), tag_num)):
        person_id = int((i + (tag_num / people_num) - 1) / (tag_num / people_num))
        instrlist.append(twin_arg_instr("at", person_id, i))
    # 添加公众号
    for i in range(1, randint(int(account_num * 0.7), account_num)):
        person_id = randint(1, people_num)
        instrlist.append(official_account_instr("coa", person_id, i))
        created_accounts.add(i)
    # 随机生成剩余指令
    remaining = instr_num - len(instrlist)
    for _ in range(remaining):
        instr = choice(instrs)
        if instr == "ap":
            instrlist.append(person_instr(randint(1, people_num)))
        elif instr == "ar":
            instrlist.append(triplet_arg_instr("ar", randint(1, people_num), randint(1, people_num), randint(1, MAX_VALUE)))
        elif instr == "mr":
            instrlist.append(triplet_arg_instr("mr", randint(1, people_num), randint(1, people_num), randint(-MAX_M_VALUE, int(MAX_M_VALUE * 0.3))))
        elif instr in ["qv", "qci", "qsp"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, people_num)))
        elif instr in ["qts", "qcs"]:
            instrlist.append(zero_arg_instr(instr))
        elif instr in ["at", "dt"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr in ["att", "dft"]:
            person_id = randint(1, people_num)
            instrlist.append(triplet_arg_instr(instr, randint(1, people_num), person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr in ["qtvs", "qtav"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr == "qba":
            instrlist.append(single_arg_instr("qba", randint(1, people_num)))
        elif instr == "coa":
            account_id = randint(1, account_num)
            instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
            created_accounts.add(account_id)
        elif instr == "doa" and created_accounts:
            account_id = choice(list(created_accounts))
            instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
            created_accounts.discard(account_id)
        elif instr == "ca":
            account_id = choice(list(created_accounts)) if created_accounts else randint(1, account_num)
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif instr == "da" and created_articles:
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif instr == "foa" and created_accounts:
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif instr == "qbc" and created_accounts:
            instrlist.append(single_arg_instr("qbc", choice(list(created_accounts))))
        elif instr == "qra":
            instrlist.append(single_arg_instr("qra", randint(1, people_num)))
    return '\n'.join(instrlist)

def extend_data(instr_num, people_num, tag_num, account_num, article_num):
    """生成扩展测试数据（标签重叠）"""
    instrlist = []
    created_accounts = set()
    created_articles = set()
    # 添加用户
    for i in range(1, randint(int(people_num * 0.7), people_num)):
        instrlist.append(person_instr(i))
    # 添加重叠标签
    for i in range(5, randint(int(tag_num * 0.7), tag_num)):
        person_id1 = int((i / (tag_num / people_num)) - 1)
        person_id2 = int(i / (tag_num / people_num))
        instrlist.append(twin_arg_instr("at", person_id1, i))
        instrlist.append(twin_arg_instr("at", person_id2, i))
    # 添加公众号
    for i in range(1, randint(int(account_num * 0.7), account_num)):
        person_id = randint(1, people_num)
        instrlist.append(official_account_instr("coa", person_id, i))
        created_accounts.add(i)
    # 随机生成剩余指令
    remaining = instr_num - len(instrlist)
    for _ in range(remaining):
        instr = choice(instrs)
        if instr == "ap":
            instrlist.append(person_instr(randint(1, people_num)))
        elif instr == "ar":
            instrlist.append(triplet_arg_instr("ar", randint(1, people_num), randint(1, people_num), randint(1, MAX_VALUE)))
        elif instr == "mr":
            instrlist.append(triplet_arg_instr("mr", randint(1, people_num), randint(1, people_num), randint(-MAX_M_VALUE, int(MAX_M_VALUE * 0.3))))
        elif instr in ["qv", "qci", "qsp"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, people_num)))
        elif instr in ["qts", "qcs"]:
            instrlist.append(zero_arg_instr(instr))
        elif instr in ["at", "dt"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag_overlapped(person_id, people_num, tag_num)))
        elif instr in ["att", "dft"]:
            person_id = randint(1, people_num)
            instrlist.append(triplet_arg_instr(instr, randint(1, people_num), person_id, locate_tag_overlapped(person_id, people_num, tag_num)))
        elif instr in ["qtvs", "qtav"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag_overlapped(person_id, people_num, tag_num)))
        elif instr == "qba":
            instrlist.append(single_arg_instr("qba", randint(1, people_num)))
        elif instr == "coa":
            account_id = randint(1, account_num)
            instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
            created_accounts.add(account_id)
        elif instr == "doa" and created_accounts:
            account_id = choice(list(created_accounts))
            instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
            created_accounts.discard(account_id)
        elif instr == "ca":
            account_id = choice(list(created_accounts)) if created_accounts else randint(1, account_num)
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif instr == "da" and created_articles:
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif instr == "foa" and created_accounts:
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif instr == "qbc" and created_accounts:
            instrlist.append(single_arg_instr("qbc", choice(list(created_accounts))))
        elif instr == "qra":
            instrlist.append(single_arg_instr("qra", randint(1, people_num)))
    return '\n'.join(instrlist)

def all_random(instr_num, people_num, tag_num, account_num, article_num):
    """生成完全随机测试数据"""
    instrlist = []
    created_accounts = set()
    created_articles = set()
    for _ in range(instr_num):
        instr = choice(instrs)
        if instr == "ap":
            instrlist.append(person_instr(randint(1, people_num)))
        elif instr == "ar":
            instrlist.append(triplet_arg_instr("ar", randint(1, people_num), randint(1, people_num), randint(1, MAX_VALUE)))
        elif instr == "mr":
            instrlist.append(triplet_arg_instr("mr", randint(1, people_num), randint(1, people_num), randint(-MAX_M_VALUE, int(MAX_M_VALUE * 0.3))))
        elif instr in ["qv", "qci", "qsp"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, people_num)))
        elif instr in ["qts", "qcs"]:
            instrlist.append(zero_arg_instr(instr))
        elif instr in ["at", "dt"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, tag_num)))
        elif instr in ["att", "dft"]:
            instrlist.append(triplet_arg_instr(instr, randint(1, people_num), randint(1, people_num), randint(1, tag_num)))
        elif instr in ["qtvs", "qtav"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, tag_num)))
        elif instr == "qba":
            instrlist.append(single_arg_instr("qba", randint(1, people_num)))
        elif instr == "coa":
            account_id = randint(1, account_num)
            instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
            created_accounts.add(account_id)
        elif instr == "doa" and created_accounts:
            account_id = choice(list(created_accounts))
            instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
            created_accounts.discard(account_id)
        elif instr == "ca":
            account_id = choice(list(created_accounts)) if created_accounts else randint(1, account_num)
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif instr == "da" and created_articles:
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif instr == "foa" and created_accounts:
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif instr == "qbc" and created_accounts:
            instrlist.append(single_arg_instr("qbc", choice(list(created_accounts))))
        elif instr == "qra":
            instrlist.append(single_arg_instr("qra", randint(1, people_num)))
    return '\n'.join(instrlist)

def stress_test_data(instr_num=10000, people_num=800, tag_num=100, account_num=100, article_num=5000):
    """生成压力测试数据"""
    special_instr = ['mr', 'qts', 'att', 'dft', 'qtvs', 'qtav', 'qcs', 'qsp', 'qbc', 'qra']
    instrlist = [ln_generator(people_num)]
    created_accounts = set()
    created_articles = set()
    # 添加标签
    for i in range(1, randint(int(tag_num * 0.7), tag_num)):
        person_id = int((i + (tag_num / people_num) - 1) / (tag_num / people_num))
        instrlist.append(twin_arg_instr("at", person_id, i))
    # 添加公众号
    for i in range(1, randint(int(account_num * 0.7), account_num)):
        person_id = randint(1, people_num)
        instrlist.append(official_account_instr("coa", person_id, i))
        created_accounts.add(i)
    # 随机生成剩余指令
    remaining = instr_num - len(instrlist)
    for _ in range(remaining):
        instr = choice(special_instr)
        if instr == "ap":
            instrlist.append(person_instr(randint(1, people_num)))
        elif instr == "ar":
            instrlist.append(triplet_arg_instr("ar", randint(1, people_num), randint(1, people_num), randint(1, MAX_VALUE)))
        elif instr == "mr":
            instrlist.append(triplet_arg_instr("mr", randint(1, people_num), randint(1, people_num), randint(-MAX_M_VALUE, int(MAX_M_VALUE * 0.3))))
        elif instr in ["qv", "qci", "qsp"]:
            instrlist.append(twin_arg_instr(instr, randint(1, people_num), randint(1, people_num)))
        elif instr in ["qts", "qcs"]:
            instrlist.append(zero_arg_instr(instr))
        elif instr in ["at", "dt"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr in ["att", "dft"]:
            person_id = randint(1, people_num)
            instrlist.append(triplet_arg_instr(instr, randint(1, people_num), person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr in ["qtvs", "qtav"]:
            person_id = randint(1, people_num)
            instrlist.append(twin_arg_instr(instr, person_id, locate_tag(person_id, people_num, tag_num)))
        elif instr == "qba":
            instrlist.append(single_arg_instr("qba", randint(1, people_num)))
        elif instr == "coa":
            account_id = randint(1, account_num)
            instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
            created_accounts.add(account_id)
        elif instr == "doa" and created_accounts:
            account_id = choice(list(created_accounts))
            instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
            created_accounts.discard(account_id)
        elif instr == "ca":
            account_id = choice(list(created_accounts)) if created_accounts else randint(1, account_num)
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif instr == "da" and created_articles:
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif instr == "foa" and created_accounts:
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif instr == "qbc" and created_accounts:
            instrlist.append(single_arg_instr("qbc", choice(list(created_accounts))))
        elif instr == "qra":
            instrlist.append(single_arg_instr("qra", randint(1, people_num)))
    return '\n'.join(instrlist)

def structured_social_media_test(instr_num=10000, people_num=800, tag_num=100, account_num=100, article_num=5000):
    """生成有逻辑、梯度的公众号测试数据"""
    instrlist = []
    created_accounts = set()
    created_articles = set()
    active_users = set()

    # 阶段 1: 初始化社交网络
    # 创建用户
    for i in range(1, people_num + 1):
        instrlist.append(f"ap {i} Person_{i} {randint(1, 100)}")
    for i in range(1, people_num + 1):
        for j in range(1, int(i / 2)):
            if random() < 0.5:  # 增加关系密度
                instrlist.append(triplet_arg_instr("ar", i, j, randint(1, MAX_VALUE)))
                active_users.add(i)
                active_users.add(j)

    # 阶段 2: 创建公众号（初期，20% 指令）
    init_instr = int(instr_num * 0.2)
    for i in range(1, randint(int(account_num * 0.7), account_num)):
        person_id = choice(list(active_users)) if active_users else randint(1, people_num)
        instrlist.append(official_account_instr("coa", person_id, i))
        created_accounts.add(i)
    # 添加少量文章和关注
    for _ in range(init_instr - len(instrlist)):
        if random() < 0.5 and created_accounts:
            account_id = choice(list(created_accounts))
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif created_accounts:
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))

    # 阶段 3: 中期测试（50% 指令，增加操作频率）
    mid_instr = int(instr_num * 0.5)
    for _ in range(mid_instr):
        r = random()
        if r < 0.3 and created_accounts:  # 贡献大量文章
            account_id = choice(list(created_accounts))
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        elif r < 0.5 and created_articles:  # 删除部分文章
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif r < 0.7 and created_accounts:  # 增加关注
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif r < 0.85 and created_accounts:  # 删除公众号
            account_id = choice(list(created_accounts))
            instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
            created_accounts.discard(account_id)
        else:  # 重新创建公众号
            account_id = randint(1, account_num)
            instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
            created_accounts.add(account_id)

    # 阶段 4: 后期测试（30% 指令，高频操作）
    remaining = instr_num - len(instrlist)
    for _ in range(remaining):
        r = random()
        if r < 0.4 and created_accounts:  # 高频关注
            instrlist.append(twin_arg_instr("foa", randint(1, people_num), choice(list(created_accounts))))
        elif r < 0.7 and created_articles:  # 高频文章删除
            account_id, article_id = choice(list(created_articles))
            instrlist.append(article_instr("da", randint(1, people_num), account_id, article_id))
            created_articles.discard((account_id, article_id))
        elif r < 0.9 and created_accounts:  # 文章贡献
            account_id = choice(list(created_accounts))
            article_id = randint(1, article_num)
            instrlist.append(article_instr("ca", randint(1, people_num), account_id, article_id))
            created_articles.add((account_id, article_id))
        else:  # 混合操作
            account_id = randint(1, account_num)
            if account_id in created_accounts:
                instrlist.append(official_account_instr("doa", randint(1, people_num), account_id))
                created_accounts.discard(account_id)
            else:
                instrlist.append(official_account_instr("coa", randint(1, people_num), account_id))
                created_accounts.add(account_id)

    return '\n'.join(instrlist)

def special_qtvs(instr_num=10000, people_num=800):
    """改进版 qtvs 压力测试数据生成器（四阶段测试）"""
    instrlist = []
    
    # 创建用户
    for i in range(1, people_num + 1):
        instrlist.append(f"ap {i} Person_{i} {randint(1, 100)}")
    
    # 初始化星型关系网络（用户1为中心）
    for i in range(2, people_num):
        instrlist.append(f"ar 1 {i} {randint(1, MAX_VALUE)}")
    
    # 为所有用户添加相同标签（tag_id=1）
    instrlist.append("at 1 1")  # 用户1添加标签1
    for i in range(1, people_num):
        instrlist.append(f"att {i} 1 1")  # 全部加入1号的1号标签
    
    phase1_size = instr_num // 3  # 合并阶段1和阶段2的总量
    for _ in range(phase1_size):
        # 随机选择操作类型
        op_choice = random()
        if op_choice < 0.4:  # 30%*70%=21%概率修改现有关系
            p1, p2 = 1, randint(1, people_num)
            instrlist.append(f"mr {p1} {p2} {randint(-MAX_VALUE, MAX_VALUE)}")
        elif op_choice < 0.75:  # 70%*70%=49%概率新增关系
            p1, p2 = sorted([randint(2, people_num), randint(2, people_num)])
            if p1 != p2:
                instrlist.append(f"ar {p1} {p2} {randint(1, MAX_VALUE)}")
        else:  # 25%概率执行qtvs查询
            instrlist.append("qtvs 1 1")
    
    # 合并后的阶段3：混合操作（ar/mr/dft）和qtvs查询
    phase2_size = instr_num // 3  # 剩余指令
    for _ in range(phase2_size):
        op_choice = random()
        if op_choice < 0.4:  # 50%*70%=35%概率修改关系
            p1, p2 = randint(1, 10), randint(1, people_num)
            instrlist.append(f"mr {p1} {p2} {randint(int(-MAX_VALUE / 2), MAX_VALUE)}")
        elif op_choice < 0.5:  # 30%*70%=21%概率新增关系
            p1, p2 = sorted([randint(1, people_num), randint(1, people_num)])
            if p1 != p2:
                instrlist.append(f"ar {p1} {p2} {randint(1, MAX_VALUE)}")
        elif op_choice < 0.8:  # 20%*70%=14%概率删除标签
            target = randint(1, people_num)
            instrlist.append(f"dft {target} 1 1")
        else:  # 30%概率执行qtvs查询
            instrlist.append("qtvs 1 1")
    
    phase3_size = instr_num - len(instrlist)
    for _ in range(phase3_size):
        instrlist.append("qtvs 1 1")
        
    return '\n'.join(instrlist[:instr_num])


def special_qba_stress_test(instr_num=10000, people_num=800, max_relation_value=200):
    """高频qba压力测试生成器(动态关系网络+密集查询）"""
    instrlist = []
    
    # 创建核心用户群（集中在前20%的ID）
    core_users = int(people_num * 0.1)
    for i in range(1, core_users + 1):
        instrlist.append(f"ap {i} CoreUser_{i} {randint(1, 100)}")
    
    # 建立核心用户间的强关系网络
    for i in range(1, core_users + 1):
        for j in range(i + 1, min(i + 3, core_users + 1)):  # 每个用户连接后续2人
            instrlist.append(f"ar {i} {j} {randint(max_relation_value//2, max_relation_value)}")
    
    # === 阶段2：动态操作与qba混合测试 ===
    remaining_instructions = instr_num - len(instrlist)
    for _ in range(remaining_instructions):
        op_type = random()
        
        # 40%概率执行qba查询（侧重核心用户）
        if op_type < 0.4:
            target = randint(1, core_users) if random() < 0.8 else randint(1, people_num)
            instrlist.append(f"qba {target}")
        
        # 30%概率修改关系（mr）
        elif op_type < 0.7:
            p1 = randint(1, core_users)  # 涉及核心用户
            p2 = randint(1, people_num)
            delta = randint(-max_relation_value//2, max_relation_value//2)
            instrlist.append(f"mr {p1} {p2} {delta}")
        
        # 30%概率新增用户或关系（ap/ar）
        else:
            if random() < 0.5 and len(instrlist) < instr_num * 0.9:  # 限制后期新增用户
                new_id = randint(core_users + 1, people_num)
                instrlist.append(f"ap {new_id} NewUser_{new_id} {randint(1, 100)}")
                instrlist.append(f"ar {new_id} {randint(1, core_users)} {randint(max_relation_value//2, max_relation_value)}")
            else:
                p1 = randint(1, people_num)
                p2 = randint(1, people_num)
                if p1 != p2:
                    instrlist.append(f"ar {p1} {p2} {randint(1, max_relation_value)}")
    
    # 确保最后一条指令是qba验证
    if not instrlist[-1].startswith("qba"):
        instrlist.append(f"qba {randint(1, core_users)}")
    
    return '\n'.join(instrlist[:instr_num])

if __name__ == "__main__":
    print(generate())