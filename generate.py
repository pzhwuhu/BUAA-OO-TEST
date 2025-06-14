"""
负责生成评测机所需的动态数据，包括图书初始化信息以及后续各类交互指令：
1. 根据配置文件中设定的参数，随机生成图书信息，每种图书以 “类别号-序列号” 表示ISBN
   库存数量决定生成相应的具体副本BookId, 格式形如 "B-0001-01"。
2. 随机生成用户（学号）。
3. 随机生成基本交互操作指令，如查询、借书、预约等。命令中不含日期信息，
   日期将在“指令调度器”中统一添加（前缀 "[YYYY-mm-dd]"）。
4. 同时根据系统输出结果动态插入还书和取书等后续操作指令。
"""

from checker import Library, Person
import json
import random
from datetime import datetime, timedelta

# 从配置文件中读取相关参数
config = json.load(open('config.json', 'r'))
b_date = config['begin_date']
e_date = config['end_date']
max_num_of_days_with_command = int(config['max_num_of_days_with_command'])
command_num = int(config['basic_command_num'])
num_identifier = int(config['max_num_of_book_identifier'])
num_book = int(config['max_num_of_book_for_each_identifier'])
num_person = int(config['max_num_of_person'])
query_prob = float(config['query_prob'])
borrow_prob = float(config['borrow_prob'])
order_prob = float(config['order_prob'])
return_prob = float(config['return_prob'])
pick_1_prob = float(config['pick_1_prob'])
pick_2_prob = float(config['pick_2_prob'])

def split_list_randomly(lst, n):
    """
    将列表 lst 随机划分成 n 组
    """
    groups = [[] for _ in range(n)]
    random.shuffle(lst)
    for item in lst:
        random.choice(groups).append(item)
    return groups

def generate_books_specified(identifier) -> dict:
    """
    根据指定类别号生成随机图书信息（ISBN 和库存数量）
    参数 identifier 为图书的类别号，例如 "A"、"B"、"C"；
    返回一个字典，key 为形如 "A-0001" 的ISBN，value 为库存数量
    """
    global num_identifier, num_book
    identifiers_num = random.randint(1, num_identifier)
    # 随机选择一些序列号（四位数字）
    identifiers = random.sample(range(1, round(identifiers_num + 10)), identifiers_num)
    books = [f"{identifier}-{number:04d}" for number in identifiers]
    nums = random.choices(range(1, num_book), k=len(books))
    return dict(zip(books, nums))

def generate_basic_date() -> list:
    """
    根据配置文件的起始日期和结束日期，生成含有命令的日期列表
    随机选取一部分天数，返回格式为 "YYYY-MM-DD" 的字符串列表（递增排序）
    """
    global command_num, b_date, e_date, max_num_of_days_with_command
    begin_date = datetime.strptime(b_date, "%Y-%m-%d")
    end_date = datetime.strptime(e_date, "%Y-%m-%d")
    delta = end_date - begin_date
    num_of_days_with_command = random.randint(max_num_of_days_with_command // 2, max_num_of_days_with_command)
    random_days = random.sample(range(delta.days), num_of_days_with_command)
    dates_with_commands = [str((begin_date + timedelta(days=day)).date()) for day in random_days]
    return sorted(dates_with_commands)

class data_generator:
    def __init__(self, library):
        """
        构造函数：初始化数据生成器
        1. 生成图书信息并调用 library.add_book 初始化图书库存；
        2. 生成用户；
        3. 生成每日基本操作指令；
        4. 初始化调度参数，用于依日期调度 OPEN、CLOSE 以及其他命令。
        """
        self.index = 0  # 当前处理某一日命令的下标
        self.library = library
        self.commands = []   # 存放所有生成的命令（包含日期前缀）
        self.init_command_list = []  # 初始化图书信息的命令列表（用于评测机判断初始库存）
        self.date2commands = {}  # key: 日期字符串，value: 当天生成的命令列表（不含日期前缀）
        # 生成初始数据：（1）图书；（2）用户；（3）基本命令
        self.generate_books()
        self.generate_persons()
        self.generate_basic_commands()
        # 调度标志
        self.open_flag = True
        self.close_flag = False
        self.end_flag = False
        self.date = list(self.date2commands.keys())[0]

    def generate_books(self):
        """
        生成图书初始化命令：
        1. 随机确定生成几类图书（A、B、C）；
        2. 对每个类别生成若干 ISBN 及其库存数量；
        3. 同时调用 Library.add_book 初始化库存，并将命令记录到 init_command_list 中。
        """
        # 内部定义加权采样函数，用于按权重选择图书类别（降低A类书籍概率，提高C类书籍概率）
        def weighted_sample(options, weights, k):
            result = []
            while len(result) < k:
                candidate = random.choices(options, weights=weights)[0]
                if candidate not in result:
                    result.append(candidate)
            return result

        prob = random.random()
        if prob < 0.5:
            type_num = 3
        elif prob < 0.75:
            type_num = 2
        else:
            type_num = 1
        # 概率：A类较低、C类较高
        types = weighted_sample(['A', 'B', 'C'], [2, 3, 5], type_num)
        self.commands.append(f"{type_num}\n")
        temp_commands = []
        for t in types:
            books = generate_books_specified(t)
            for isbn, num in books.items():
                # 每条初始化命令格式："<ISBN> <库存数量>"
                temp_commands.append(f"{isbn} {num}\n")
                self.library.add_book(isbn, num)
        # 打乱命令顺序
        random.shuffle(temp_commands)
        self.commands.extend(temp_commands)
        # 第一行数字表示有多少条初始化图书命令，后面为具体命令
        self.init_command_list = [str(len(temp_commands)) + "\n"] + temp_commands

    def generate_persons(self):
        """
        随机生成用户（学号），格式为 8 位数字，
        并将其存入 Library.persons 中。
        """
        global num_person
        temp_ids = random.sample(range(1, 99999999), random.randint(num_person // 2, num_person))
        ids = [f"{temp_id:08d}" for temp_id in temp_ids]
        for id in ids:
            self.library.persons[id] = Person(id)

    def generate_basic_commands(self):
        """
        生成除图书初始化外的其他基本交互指令：
        命令类型包括查询、借书和预约（预约后后续会生成取书指令）。
        随机生成一定数量的命令，再将这些命令按日期均匀分配至各天。
        每条命令格式为："<personId> <操作> <ISBN>"
        """
        global command_num, query_prob, borrow_prob, order_prob
        dates = generate_basic_date()  # 获取生成命令的日期列表
        t_command_num = random.randint(max(command_num // 2, 1), command_num)
        tmp_commands = []
        for i in range(t_command_num):
            prob = random.random()
            if prob < query_prob:
                tmp_commands.append(self.generate_query())
            elif prob < query_prob + borrow_prob:
                tmp_commands.append(self.generate_borrow())
            else:
                tmp_commands.append(self.generate_order())
        # 将所有命令随机划分成与日期数量相同的组
        tmp_commands = split_list_randomly(tmp_commands, len(dates))
        for date in dates:
            self.date2commands[date] = tmp_commands.pop(0)

    def generate_query(self) -> str:
        """
        生成查询命令：
        格式为 "<personId> queried <BookId>\n"
        其中 BookId 为形如 "A-0001-01" 的字符串
        """
        person_id = random.choice(list(self.library.persons.keys()))
        # 随机选择一个 BookId
        # 书架：key 为 ISBN，值为存有该ISBN下所有可用 BookId 的列表
        book_id = random.choice(random.choice(list(self.library.bs.values())))
        return f"{person_id} queried {book_id}\n"

    def generate_borrow(self) -> str:
        """
        生成借书命令：
        格式为 "<personId> borrowed <ISBN>\n"
        """
        person_id = random.choice(list(self.library.persons.keys()))
        isbn = random.choice(list(self.library.bs.keys()))
        return f"{person_id} borrowed {isbn}\n"

    def generate_order(self) -> str:
        """
        生成预约命令：
        格式为 "<personId> ordered <ISBN>\n"
        """
        person_id = random.choice(list(self.library.persons.keys()))
        isbn = random.choice(list(self.library.bs.keys()))
        return f"{person_id} ordered {isbn}\n"

    def generate_pick(self, person_id, book_id):
        """
        生成取书命令：
        格式为 "<personId> picked <BookId>\n"
        """
        return f"{person_id} picked {book_id}\n"

    def generate_return(self, person_id, book_id):
        """
        生成还书命令：
        格式为 "<personId> returned <BookId>\n"
        """
        return f"{person_id} returned {book_id}\n"

    def add_command(self, output=""):
        """
        根据评测机的输出结果动态插入后续命令：
        若输出为借书或取书成功，则可能会在未来日期插入还书命令；
        若预约成功，则可能在未来日期插入取书命令。
        输出字符串格式参考 Checker 模块规定。
        """
        global e_date, pick_1_prob, pick_2_prob, return_prob
        if 'accept' in output:
            # 从输出中获取日期、学号、以及最终分配的 BookId（一般位于字符串最后）
            date_str = output.split(" ")[0].strip("\n")
            book_id = output.split(" ")[-1].strip("\n")
            person_id = output.split(" ")[2].strip("\n")
            date = datetime.strptime(date_str, "[%Y-%m-%d]")
            date_str = str(date.date())
            end_date = datetime.strptime(e_date, "%Y-%m-%d")
            # 对于借书或取书成功的命令，按一定概率生成还书命令
            if ('borrowed' in output or "picked" in output) and 'accept' in output:
                if random.random() < return_prob:
                    delta = end_date - date
                    next_date_str = str((date + timedelta(days=random.randint(0, delta.days))).date())
                    command = self.generate_return(person_id, book_id)
                    if next_date_str == date_str:
                        insert_place = random.randint(self.index, len(self.date2commands[date_str]))
                        self.date2commands[date_str].insert(insert_place, command)
                    elif next_date_str in self.date2commands:
                        insert_place = random.randint(0, len(self.date2commands[next_date_str]))
                        self.date2commands[next_date_str].insert(insert_place, command)
                    else:
                        self.date2commands[next_date_str] = [command]
                        self.date2commands = dict(sorted(self.date2commands.items()))
            # 对于预约成功的命令，按一定概率生成1~2条取书命令
            if 'ordered' in output and 'accept' in output:
                prob = random.random()
                if prob < pick_2_prob:  # 生成两条取书命令
                    command = self.generate_pick(person_id, book_id)
                    for i in range(2):
                        next_date_str = str((date + timedelta(days=random.randint(0, min(12, (end_date - date).days)))).date())
                        if next_date_str == date_str:
                            insert_place = random.randint(self.index, len(self.date2commands[date_str]))
                            self.date2commands[date_str].insert(insert_place, command)
                        elif next_date_str in self.date2commands:
                            insert_place = random.randint(0, len(self.date2commands[next_date_str]))
                            self.date2commands[next_date_str].insert(insert_place, command)
                        else:
                            self.date2commands[next_date_str] = [command]
                            self.date2commands = dict(sorted(self.date2commands.items()))
                elif prob < pick_1_prob + pick_2_prob:  # 生成一条取书命令
                    command = self.generate_pick(person_id, book_id)
                    next_date_str = str((date + timedelta(days=random.randint(0, min(12, (end_date - date).days)))).date())
                    if next_date_str == date_str:
                        insert_place = random.randint(self.index, len(self.date2commands[date_str]))
                        self.date2commands[date_str].insert(insert_place, command)
                    elif next_date_str in self.date2commands:
                        insert_place = random.randint(0, len(self.date2commands[next_date_str]))
                        self.date2commands[next_date_str].insert(insert_place, command)
                    else:
                        self.date2commands[next_date_str] = [command]
                        self.date2commands = dict(sorted(self.date2commands.items()))

    def get_next_command(self) -> str:
        """
        按日期顺序及命令在当天的顺序分批输出下一条命令：
        ① 每日第一条命令输出为 OPEN 指令；
        ② 当当日命令全部输出后输出 CLOSE 指令；
        ③ 当所有日期命令发完后，返回空字符串，表示数据生成完毕。
        """
        # 若本日命令已经输出完毕，则置关闭标志
        if self.index == len(self.date2commands[self.date]):
            self.close_flag = True
        # 如果所有命令均已输出，返回空字符串
        if self.end_flag:
            return ""
        # 若处于 CLOSE 阶段，则输出 CLOSE 指令，并切换到下一天或结束
        if self.close_flag:
            self.close_flag = False
            command = f"[{self.date}] CLOSE\n"
            # 获取当前日期在所有日期中的下标
            i = list(self.date2commands.keys()).index(self.date)
            if i + 1 == len(self.date2commands):
                self.end_flag = True
            else:
                self.date = list(self.date2commands.keys())[i + 1]
                self.index = 0
                self.open_flag = True
        # 若为 OPEN 状态，则输出 OPEN 指令
        elif self.open_flag:
            self.open_flag = False
            command = f"[{self.date}] OPEN\n"
            if not self.date2commands[self.date]:
                self.close_flag = True
        # 其它情况输出当前日期对应的命令（已带换行符，无需额外添加）
        else:
            command = f"[{self.date}] {self.date2commands[self.date][self.index]}"
            self.index += 1
        self.commands.append(command)
        return command

if __name__ == '__main__':
    library = Library()
    generator = data_generator(library)
    # 输出初始化图书信息命令（评测机根据该信息初始化图书库存）
    for command in generator.init_command_list:
        print(command, end="")
    # 循环输出后续动态命令，并允许用户输入系统输出结果反馈，动态插入还书/取书命令
    while True:
        input_command = generator.get_next_command()
        if input_command == "":
            print("数据生成完毕")
            break
        print(input_command, end="")
        output_command = input("输出结果为:")
        generator.add_command(output_command)