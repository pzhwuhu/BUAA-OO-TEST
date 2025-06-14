from datetime import date,timedelta
import re
import json

class Person:
    def __init__(self,id):
        self.id=id
        self.books=set() # {bookId:str}
        self.typeB=False
    def add_book(self,bookId):
        if 'B' in bookId:
            self.typeB=True
        self.books.add(bookId)
    def del_book(self,bookId):
        if 'B' in bookId:
            self.typeB=False
        self.books.remove(bookId)
    def has_book(self,bookId)->bool:
        return bookId in self.books
    def has_book(self, isbn) -> bool:
        # 判断用户是否持有该 ISBN 的任一本副本
        for b in self.books:
            if b.startswith(isbn): # 如果用户持有以该 ISBN 开头的副本，则返回 True
                return True
        return False
    def has_B_book(self)->bool:
        return self.typeB

    def get_books(self)->set:
        return self.books

class Library:
    def __init__(self):
        # 书架：key 为 ISBN，值为存有该ISBN下所有可用 BookId 的列表
        self.bs = {}  
        # 借还处：key 为 ISBN，值为存有该ISBN下所有 BookId 的列表
        self.bro = {}  
        # 预约处：每项记录为 (appoint_date:date, personId, ISBN, BookId, valid:bool)
        self.ao = []  
        # 预约记录：列表记录 (personId, ISBN)
        self.aoLog = []   
        self.datetime = date(2025, 1, 1)
        self.persons = {}  # key: personId, value: Person
        # 书籍轨迹记录： key 为具体 BookId，值为轨迹记录列表，每项为 (操作日期, 起点, 终点)
        self.book_tracks = {}  

    def add_book(self, isbn: str, count: int = 1):
        # 为每个 ISBN 生成 count 个副本，初始均在书架上
        copies = []
        for i in range(1, count + 1):
            book_id = f"{isbn}-{i:02d}"  # 格式为两位副本号
            copies.append(book_id)
            # 初始化该副本的轨迹记录
            self.book_tracks[book_id] = []
        self.bs[isbn] = copies
        self.bro[isbn] = []  # 初始借还处为空

    def update(self, isclose: bool, dt: date):
        """
        开馆/闭馆更新：更新当前时间；闭馆时对预约记录进行检查（超过保留期限置为无效）
        """
        if isclose:
            # 闭馆时，对所有预约记录检查：若预约已保留≥4天，则置为无效
            for i in range(len(self.ao)):
                appoint_date, pid, isbn, bookId, valid = self.ao[i]
                if (self.datetime - appoint_date).days >= 4:
                    self.ao[i] = (appoint_date, pid, isbn, bookId, False)
        else:
            self.datetime = dt
            # 开馆时，对预约处若超过5天保留的预约置为无效
            for i in range(len(self.ao)):
                appoint_date, pid, isbn, bookId, valid = self.ao[i]
                if (self.datetime - appoint_date).days >= 5:
                    self.ao[i] = (appoint_date, pid, isbn, bookId, False)

    def open_check(self) -> str:
        """
        开馆整理后调用：
        检查借还处应为空，预约处不应保留逾期图书
        """
        for isbn in self.bro.keys():
            if len(self.bro[isbn]) != 0:
                return '开馆整理后借还处不应有书 ' + str(self.bro[isbn])
        for record in self.ao:
            appoint_date = record[0]
            if (self.datetime - appoint_date).days >= 5:
                return '开馆整理后预约处不应有逾期的书 ' + str(record) + ' ' + str(self.datetime)
        return ''

    def borrow(self, personId: str, bookId: str) -> tuple:
        """
        借书：
        1. 若书架中该ISBN没有可借副本或为 A 类，则 reject。
        2. 若用户已持有该ISBN（或对 B 类已有持有），则 reject。
        3. 否则从书架中取出一个具体副本借出，并更新轨迹 (bs -> user)。
        """
        parts = bookId.split('-')
        isbn = '-'.join(parts[:2])
        if personId not in self.persons:
            self.persons[personId] = Person(personId)
        if isbn not in self.bs or len(self.bs[isbn]) == 0 or bookId.startswith('A'):
            return 'reject', '书架上没有该ISBN ' + isbn + ' 的副本或不允许借阅 ' + bookId
        if self.persons[personId].has_book(isbn) or (bookId.startswith('B') and self.persons[personId].has_B_book()):
            # 此处不允许重复借阅
            return 'reject', personId + '已持有ISBN' + isbn
        # 正常借书
        if bookId not in self.bs[isbn]:
            book_id = self.bs[isbn].pop(0)  # 从书架中取出一个副本, 此时出错！
            return 'reject', '书架上没有该ISBN ' + isbn + ' 的副本 ' + bookId
        else:
            book_id = bookId
            self.bs[isbn].remove(bookId)
        self.persons[personId].add_book(book_id)
        # 更新历史轨迹：书架 -> user
        self.book_tracks[book_id].append((self.datetime, "bs", "user"))
        return 'accept', book_id

    def return_book(self, personId: str, bookId: str) -> tuple:
        """
        还书：
        用户归还书籍，将该副本移至借还处，并记录轨迹 (user -> bro)
        """
        if personId not in self.persons:
            return 'reject', '查无此人' + personId
        if bookId not in self.persons[personId].books:
            return 'reject', '用户没有持有该书籍 ' + bookId
        parts = bookId.split('-')
        isbn = '-'.join(parts[:2])  # 获取ISBN
        self.bro[isbn].append(bookId)
        self.persons[personId].del_book(bookId)
        self.book_tracks[bookId].append((self.datetime, "user", "bro"))
        return 'accept', ''

    def order(self, personId: str, isbn: str) -> tuple:
        """
        预约：
        条件与借书类似，但不消耗书架资源，实际预约时在整理中会由书架转移到预约处。
        """
        if personId not in self.persons:
            self.persons[personId] = Person(personId)
        if isbn.startswith('A') or (isbn.startswith('B') and self.persons[personId].has_B_book()):
            return 'reject', personId + ' 已有B类书籍或该ISBN书籍为A类书籍 ' + isbn
        if self.persons[personId].has_book(isbn):  # 判断用户是否已经借过该书籍
            return 'reject', personId + ' 已借过该书籍 ' + isbn
        # 判断用户是否已经预定过书籍且还未取书
        for record in self.aoLog:
            if record[0] == personId:
                return 'reject', personId + ' 已预约书籍 ' + record[1]
        for record in self.ao:
            if record[1] == personId and record[4]:
                return 'reject', personId + ' 在预约处有未取书籍' + record[3]
        self.aoLog.append((personId, isbn))
        return 'accept', isbn

    def pick(self, personId: str, isbn: str) -> tuple:
        """
        取书：
        用户从预约处取书，按条件取走对应具体副本，并更新轨迹 (ao -> user)。
        """
        if personId not in self.persons:
            self.persons[personId] = Person(personId)
        if self.persons[personId].has_book(isbn) or (isbn.startswith('B') and self.persons[personId].has_B_book()):
            return 'reject', personId + ' 已有B类书籍或该ISBN书籍为A类书籍 ' + isbn
        # 查找预约处中有效的对应记录
        for i in range(len(self.ao)):
            appoint_date, pid, i_isbn, book_id, valid = self.ao[i]
            if pid == personId and i_isbn == isbn and valid:
                self.ao.pop(i)
                self.persons[personId].add_book(book_id)
                self.book_tracks[book_id].append((self.datetime, "ao", "user"))
                return 'accept', book_id
        return 'reject', personId + ' 在预约处没有该书籍 ' + isbn

    def query(self, input_str: str, output_str: list[str]) -> str:
        """
        查询：根据输入的查询字符串，输出查询结果。
        """
        # 从输入中提取日期与具体的 BookId（注意：允许副本号可选，但查询时应提供完整信息）
        tmp = re.match(r'\[(\d{4}-\d{2}-\d{2})\]\s+\S+\s+queried\s+([ABC]-\d{4}(?:-\d{2})?)', input_str)
        if not tmp:
            return "输入查询格式错误"
        bookId = tmp.group(2)
        result = []
        # 获取该 BookId 的历史转运记录，只有记录中至少包含（日期, 起点, 终点）的才计为一次转运
        if bookId not in self.book_tracks:
            cnt = 0
            traces = []
        else:
            traces = [record for record in self.book_tracks[bookId] if len(record) >= 3]
            cnt = len(traces)
        header = f"[{self.datetime.strftime('%Y-%m-%d')}] {bookId} moving trace: {cnt}\n"
        result.append(header)
        details = []
        for idx, record in enumerate(traces, start=1):
            details.append(f"{idx} [{record[0].strftime('%Y-%m-%d')}] from {record[1]} to {record[2]}\n")
        result.extend(details)
        # 与传入的 expected 输出进行比较
        if len(output_str) != len(result):
            return '查询结果错误，应为: \n' + '\n'.join(result) + '\n实际为: \n' + '\n'.join(output_str)
        for i in range(len(output_str)):
            if output_str[i] != result[i]:
                return '查询结果错误，应为: \n' + '\n'.join(result) + '\n实际为: \n' + '\n'.join(output_str)
        return ''

    def action(self, input_str: str, output_str: str) -> str:
        # 检查时间：从输入与输出中各提取日期进行比较
        tmp_match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\].*', input_str)
        if tmp_match is None:
            return '输入日期格式错误' + input_str
        time1 = date(int(tmp_match.group(1)), int(tmp_match.group(2)), int(tmp_match.group(3)))
        tmp_match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\].*', output_str)
        if tmp_match is None:
            return '输出日期格式错误' + output_str
        time2 = date(int(tmp_match.group(1)), int(tmp_match.group(2)), int(tmp_match.group(3)))
        if time1 != time2:
            return '时间错误' + str(time1) + ' 和 ' + str(time2)
        # 从输入提取操作信息：允许查询时最后的 BookId 包含可选的副本号
        tmp_match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\]\s+(\w+)\s+(\w+)\s+([ABC]-\d{4}(?:-\d{2})?)', input_str)
        if tmp_match is None:
            return '输入操作格式错误' + input_str
        personId = tmp_match.group(4)
        isbn = tmp_match.group(6)
        command = tmp_match.group(5)
        # 输出格式：[YYYY-mm-dd] [accept/reject] <personId> <操作> <ISBN>
        tmp_match = re.match(
            r'\[\d{4}-\d{2}-\d{2}\]\s+\[(\w+)\]\s+(\w+)\s+(\w+)\s+([ABC]-\d{4}(?:-\d{2})?)',
            output_str)
        if tmp_match is None:
            return '操作输出格式错误' + output_str
        output_status = tmp_match.group(1)  # "accept" 或 "reject"
        out_person = tmp_match.group(2)
        op = tmp_match.group(3)
        out_id = tmp_match.group(4)  # 完整BookId或ISBN
        if personId != out_person:
            return '查询学号错误' + out_person
        if isbn != out_id and not out_id.startswith(isbn):
            return '借阅书籍id错误' + out_id
        if op == 'borrowed':
            result, book_id = self.borrow(personId, out_id)
            if result == 'reject':
                # 失败时输出中的最后一个参数为借书失败的原因
                if output_status != result or out_id != isbn:
                    return 'borrowed错误, 应为 ' + result + ': ' + book_id
            else:
                # 成功借书后输出的最后一个参数应为借到的完整副本号
                if output_status != result or out_id != book_id:
                    return 'borrowed错误, 应为 ' + result + ': ' + book_id
        elif op == 'ordered':
            result, errorInfo = self.order(personId, isbn)
            # 预约操作输出时最后一个参数为 ISBN
            if result != output_status or out_id != isbn:
                return 'ordered错误, '+ errorInfo + ' 实际为 ' + output_status + ' ' + isbn + ', 应为 '+  result
        elif op == 'returned':
            # 用户还书时输入中提供的是完整的副本号
            result, errorInfo = self.return_book(personId, out_id)
            if result != output_status:
                return 'returned错误, 应为 ' + result + ': ' + errorInfo
        elif op == 'picked':
            result, errorInfo = self.pick(personId, isbn)
            if result == 'reject':
                if output_status != result or out_id != isbn:
                    return 'picked错误, 应为 ' + result  + ': '+ errorInfo
            else:
                picked_book = None
                for b in self.persons[personId].books:
                    if b.startswith(isbn + '-'):
                        picked_book = b
                        break
                if output_status != result or out_id != picked_book:
                    return 'picked错误, 应为 ' + result + ': ' + errorInfo
        return ''

    def orgnize(self, isOpenOrgnize: bool, command: str) -> str:
        """
        整理操作时，模拟图书在不同位置间转运，并更新各处存储与书籍轨迹。
        支持格式：
          "[YYYY-mm-dd] move <ISBN> from <起点> to <终点>"
          "[YYYY-mm-dd] move <ISBN> from <起点> to <终点> for <personId>"
        注意：操作时具体的书籍副本由系统自动分配。
        """
        ffrom = ''; to = ''; book_id = ''; personId = ''
        tmp_match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\].*', command)
        cmd_date = date(int(tmp_match.group(1)), int(tmp_match.group(2)), int(tmp_match.group(3)))
        if cmd_date != self.datetime:
            return '时间错误' + '，应为 ' + self.datetime.strftime('%Y-%m-%d')
        try:
            if 'for' in command: # 终点为预约处，为指定用户移动书籍
                # [2025-01-09] move B-0003-02 from bs to ao for 80455487
                tmp_match = re.match(r'\[\d{4}-\d{2}-\d{2}\]\s+move\s+([ABC]-\d{4}-\d{2})\s+from\s+(\w+)\s+to\s+(\w+)\s+for\s+(\w+)', command)
                book_id = tmp_match.group(1)
                ffrom = tmp_match.group(2)
                to = tmp_match.group(3)
                personId = tmp_match.group(4)
            else:
                tmp_match = re.match(r'\[\d{4}-\d{2}-\d{2}\]\s+move\s+([ABC]-\d{4}-\d{2})\s+from\s+(\w+)\s+to\s+(\w+)', command)
                book_id = tmp_match.group(1)
                ffrom = tmp_match.group(2)
                to = tmp_match.group(3)
        except:
            return '格式错误' + command
        parts = book_id.split('-')
        isbn = '-'.join(parts[:2])
        # 模拟移动操作，根据起点与终点操作：
        if ffrom == 'bro' and to == 'bs':
            if isbn not in self.bro or len(self.bro[isbn]) == 0 or book_id not in self.bro[isbn]:
                return '借还处查无此书 ' + book_id
            self.bro[isbn].remove(book_id)
            self.bs[isbn].append(book_id)
            self.book_tracks[book_id].append((self.datetime, "bro", "bs"))
        elif ffrom == 'ao' and to == 'bs':
            found = False
            for i in range(len(self.ao)):
                rec = self.ao[i]
                if rec[3] == book_id and rec[4] == False:
                    self.ao.pop(i)
                    self.bs[isbn].append(book_id)
                    self.book_tracks[book_id].append((self.datetime, "ao", "bs"))
                    found = True
                    break
            if not found:
                return '预约处查无此书或尚在留存中 ' + book_id
        elif ffrom == 'bs' and to == 'ao':
            if isbn not in self.bs or len(self.bs[isbn]) == 0 or book_id not in self.bs[isbn]:
                return '书架查无此书 ' + book_id
            # 查找预约记录
            found = False
            for i in range(len(self.aoLog)):
                rec = self.aoLog[i]
                if rec[0] == personId and rec[1] == isbn:
                    self.aoLog.pop(i)
                    found = True
                    break
            if not found:
                return '没有此人的预约记录 ' + personId
            self.bs[isbn].remove(book_id)
            if isOpenOrgnize:
                self.ao.append((self.datetime, personId, isbn, book_id, True))
            else:
                self.ao.append((self.datetime + timedelta(days=1), personId, isbn, book_id, True))
            self.book_tracks[book_id].append((self.datetime, "bs", "ao", f"for {personId}"))
        elif ffrom == 'bro' and to == 'ao':
            if isbn not in self.bro or len(self.bro[isbn]) == 0 or book_id not in self.bro[isbn]:
                return '借还处查无此书 ' + book_id
            found = False
            for i in range(len(self.aoLog)):
                rec = self.aoLog[i]
                if rec[0] == personId and rec[1] == isbn:
                    self.aoLog.pop(i)
                    found = True
                    break
            if not found:
                return '没有此人的预约记录 ' + personId
            self.bro[isbn].remove(book_id)
            if isOpenOrgnize:
                self.ao.append((self.datetime, personId, isbn, book_id, True))
            else:
                self.ao.append((self.datetime + timedelta(days=1), personId, isbn, book_id, True))
            self.book_tracks[book_id].append((self.datetime, "bro", "ao", f"for {personId}"))
        elif ffrom == 'bs' and to == 'bro':
            if isbn not in self.bs or len(self.bs[isbn]) == 0 or book_id not in self.bs[isbn]:
                return '书架查无此书 ' + book_id
            self.bs[isbn].remove(book_id)
            self.bro[isbn].append(book_id)
            self.book_tracks[book_id].append((self.datetime, "bs", "bro"))
        elif ffrom == 'ao' and to == 'bro':
            found = False
            for i in range(len(self.ao)):
                rec = self.ao[i]
                if rec[3] == book_id and rec[4] == False:
                    self.ao.pop(i)
                    self.bro[isbn].append(book_id)
                    self.book_tracks[book_id].append((self.datetime, "ao", "bro"))
                    found = True
                    break
            if not found:
                return '预约处查无此书或尚在留存中 ' + book_id
        else:
            return '起点和终点重复或不支持的转运' + command
        return ''

def check():
    config = json.load(open('config.json', encoding='utf-8'))
    input_file = config['input_file']
    output_file = config['output_file']
    inputs = open(input_file, 'r', encoding='utf-8').readlines()
    outputs = open(output_file, 'r', encoding='utf-8').readlines()
    library = Library()

    # 第一部分：根据输入前 n 行添加图书
    i = 1
    n = int(inputs[0].strip())
    while i <= n:
        tmp_match = re.match(r'([ABC]-\d{4})\s+(\d+).*', inputs[i])
        library.add_book(tmp_match.group(1), int(tmp_match.group(2)))
        i += 1
    j = 0
    # 处理后续每条动态指令
    while i < len(inputs) and j < len(outputs):
        input_command = inputs[i]
        i += 1
        output_command = []
        output_command.append(outputs[j].rstrip('\n'))
        j += 1
        if not ('-' in output_command[0] or int(output_command[0]) == 0):
            # 若首行不是数字，则按规定读取多行输出
            for k in range(0, int(output_command[0])):
                output_command.append(outputs[j + k].rstrip('\n'))
            j += int(output_command[0])
        if 'OPEN' in input_command:
            tmp_match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\].*', input_command)
            dt = date(int(tmp_match.group(1)), int(tmp_match.group(2)), int(tmp_match.group(3)))
            library.update(False, dt)
            if int(output_command[0]) > 0:
                for k in range(1, len(output_command)):
                    result = library.orgnize(True, output_command[k])
                    if result != '':
                        return result + ' 输入第' + str(i) + '行 输出第' + str(j) + '行'
            result = library.open_check()
            if result != '':
                return result + ' 输入第' + str(i) + '行 输出第' + str(j) + '行'
        elif 'CLOSE' in input_command:
            library.update(True, dt)
            if int(output_command[0]) > 0:
                for k in range(1, len(output_command)):
                    result = library.orgnize(False, output_command[k])
                    if result != '':
                        return result + ' 输入第' + str(i) + '行 输出第' + str(j) + '行'
        else:
            result = library.action(input_command, output_command[0])
            if result != '':
                return result + ' 输入第' + str(i) + '行 输出第' + str(j) + '行'
    return "Accepted!"

if __name__ == '__main__':
    print(check())