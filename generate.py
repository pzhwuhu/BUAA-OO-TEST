import random
import numpy as np
import json
from cyaron import Graph
from pathlib import Path

config = json.load(open('config.json', encoding='utf-8'))

def generate_data(input_file: str) -> None:
    """
    根据 config.json 中的配置生成社交网络测试指令，包含：
      - 用户、关系、标签
      - 公众号（create_official_account, delete_official_account, follow_official_account）
      - 文章（contribute_article, delete_article）
      - 消息相关：add_message, add_emoji_message, add_red_envelope_message, add_forward_message,
        send_message, store_emoji_id, delete_cold_emoji
      - 各类查询和复合指令 load_network
    同时保证转发消息中选择的 article 来自已创建的文章。
    
    本版本调整为：建图部分的指令固定输出，其它部分的指令按分区顺序追加，每个分区内采用“从上次位置到末尾随机插入”
    的策略，保证段内指令顺序较为有序。
    """
    # 随机总体指令数量
    command_num = random.randint(1000, int(config['command_limit']))
    node_num = random.randint(2, int(config['node_limit']))  # 总用户数
    isload = random.random()
    if isload < config['load_prob']:
        command_num -= 1
    graph_command_num = int(command_num * config['graph_prop'])
    tag_command_num = int(command_num * config['tag_prop'])
    message_command_num = int(command_num * config['message_prop'])
    account_command_num = int(command_num * config.get("account_prop", 0.15))
    query_command_num = command_num - graph_command_num - tag_command_num - account_command_num - message_command_num

    #####################
    # 1. 建图部分（固定顺序输出）
    dense_node_num = int((1.5 + (1 + 4 * graph_command_num) ** 0.5) / 2)
    edge_num = dense_node_num * (dense_node_num - 1) // 2
    dense_node_num += 1
    graph = Graph.graph(dense_node_num, edge_num, weight_limit=(1, 100))
    
    base_instructions = []
    node = set()
    edge = set()
    str_node = []
    str_edge = []
    # 边指令
    for tmpedge in graph.iterate_edges():
        node.add(tmpedge.start)
        str_edge.append('ar ' + str(tmpedge.start) + ' ' + str(tmpedge.end) + ' ' + str(tmpedge.weight))
        edge.add((tmpedge.start, tmpedge.end))
    # 用户指令
    for i in node:
        str_node.append('ap ' + str(i) + ' OO' + str(i) + ' ' + str(random.randint(1, 200)))
    # 补充外围节点
    for i in range(dense_node_num, node_num):
        tmpnode = get_int()
        str_node.append('ap ' + str(tmpnode) + ' OO' + str(i) + ' ' + str(random.randint(1, 200)))
        node.add(tmpnode)
    base_instructions.extend(str_node)
    base_instructions.extend(str_edge)
    
    #####################
    # 2. 随机图修改部分（新增节点、边、修改边）
    graph_modifications = []
    last_idx = 0
    # 用图改指令条数 = graph_command_num - len(base_instructions)
    remaining_graph = graph_command_num - len(base_instructions)
    while remaining_graph > 0:
        prob = random.random()
        tmpstr = ''
        if prob < 0.2:
            if random.random() < 0.5:
                tmpstr = 'ap ' + str(np.random.choice(list(node))) + ' OO_plus ' + str(random.randint(1, 200))
            else:
                node.add(get_int())
                tmpstr = 'ap ' + str(list(node)[-1]) + ' OO_random ' + str(random.randint(1, 200))
        elif prob < 0.7:
            if random.random() < 0.8:
                n1 = np.random.choice(list(node))
                n2 = np.random.choice(list(node))
                edge.add((n1, n2))
                tmpstr = 'ar ' + str(n1) + ' ' + str(n2) + ' ' + str(random.randint(1, 200))
            else:
                tmpstr = 'ar ' + str(get_int()) + ' ' + str(get_int()) + ' ' + str(random.randint(1, 200))
        else:
            if random.random() < 0.8 and edge:
                tmppos = random.randint(0, len(list(edge)) - 1)
                e = list(edge)[tmppos]
                tmpstr = 'mr ' + str(e[0]) + ' ' + str(e[1]) + ' ' + str(random.randint(-200, 100))
            else:
                tmpstr = 'mr ' + str(get_int()) + ' ' + str(get_int()) + ' ' + str(random.randint(-200, 100))
        # 在区间 [last_idx, len(graph_modifications)]内随机插入
        pos = random.randint(last_idx, len(graph_modifications))
        graph_modifications.insert(pos, tmpstr)
        last_idx = pos + 1
        remaining_graph -= 1

    #####################
    # 3. 标签指令部分
    tag_modifications = []
    last_idx = 0
    # dense 模式：先创建大部分 tag，再把相邻节点加进去
    dense_tag_num = int(tag_command_num * 3 / 4)
    tag_list = []
    tag_at = []   # 存放创建 tag 的指令
    tag_att = []  # 存放 add_to_tag 的指令
    while dense_tag_num > 0:
        # 随机选一个 person 作为 tag 的拥有者和 tag_id
        tag_id = random.randint(1, len(graph.edges) - 1)
        # 创建 tag：格式 at person_id tag_id
        tag_at.append(f"at {tag_id} {tag_id}")
        tag_list.append(tag_id)
        dense_tag_num -= 1
        # 把与这个 person 相连的所有 neighbor 加入到这个 tag 里
        for ed in graph.edges[tag_id]:
            if dense_tag_num <= 0:
                break
            # 找到另一个端点作为要加进 tag 的 person1
            neighbor = ed.end if ed.start == tag_id else ed.start
            # add_to_tag person1 person2(tag owner) tag_id
            tag_att.append(f"att {neighbor} {tag_id} {tag_id}")
            dense_tag_num -= 1
        if dense_tag_num <= 0:
            break

    # 把刚才生成的 at/att 指令都放到 tag_modifications 里
    tag_modifications.extend(tag_at)
    tag_modifications.extend(tag_att)

    # 接下来再生成剩余的随机 tag 操作……
    for j in range(0, len(tag_list) - 1):
        tag_att.append('att ' + str(graph.edges[tag_id][0]) + ' ' + str(tag_list[j]) + ' ' + str(tag_id))
        dense_tag_num -= 1
        if dense_tag_num <= 0:
            break
    tag_modifications.extend(tag_at)
    tag_modifications.extend(tag_att)
    # 随机 tag 操作余下的条数
    while tag_command_num > 0:
        prob = random.random()
        if prob < 0.3:
            # 创建 tag：at person tag_id
            owner = random.choice(list(node)) if node else get_int()
            tag_id = get_int()
            tag_modifications.append(f"at {owner} {tag_id}")
            tag_list.append(tag_id)
        elif prob < 0.5:
            # add_to_tag：att person1 person2(tag_owner) tag_id
            if node and tag_list:
                person = random.choice(list(node))
                tag_owner = random.choice(tag_list)
                tag_modifications.append(f"att {person} {tag_owner} {tag_owner}")
            else:
                x, y, z = get_int(), get_int(), get_int()
                tag_modifications.append(f"att {x} {y} {z}")
        elif prob < 0.7:
            # delete tag：dt tag_owner tag_id
            if tag_list:
                t = random.choice(tag_list)
                tag_modifications.append(f"dt {t} {t}")
            else:
                x, y = get_int(), get_int()
                tag_modifications.append(f"dt {x} {y}")
        else:
            # delete_from_tag：dft person tag_owner tag_id
            if node and tag_list:
                person = random.choice(list(node))
                tag_owner = random.choice(tag_list)
                tag_modifications.append(f"dft {person} {tag_owner} {tag_owner}")
            else:
                x, y, z = get_int(), get_int(), get_int()
                tag_modifications.append(f"dft {x} {y} {z}")
        tag_command_num -= 1

    #####################
    # 4. 账户与文章指令部分
    acct_modifications = []
    last_idx = 0
    # 记录创建公众号： account_id -> creator_id
    created_accounts = {}  # {account_id: creator_id}
    # 记录各公众号关注者： account_id -> set(follower_id)
    account_followers = {}
    # 记录文章： (account_id, article_id) -> contributor_id
    created_articles = {}

    # 按顺序创建公众号
    for _ in range(account_command_num // 4):
        acc_id = get_int()
        creator = int(np.random.choice(list(node)))
        inst = official_account_instr("coa", creator, acc_id)
        created_accounts[acc_id] = creator
        account_followers[acc_id] = {creator}
        acct_modifications.append(inst)

    # 按顺序增加关注者
    for _ in range(account_command_num // 3):
        if created_accounts:
            acc_id = random.choice(list(created_accounts.keys()))
            possible = set(node) - account_followers.get(acc_id, set())
            if possible:
                follower = random.choice(list(possible))
            else:
                follower = random.choice(list(node))
            account_followers[acc_id].add(follower)
            inst = f"foa {follower} {acc_id}"
            acct_modifications.append(inst)

    # 随机发表文章、删除文章和删除公众号
    for _ in range(account_command_num - len(acct_modifications)):
        prob = random.random()
        if prob < 0.4 and created_accounts:
            # 发表文章
            acc_id = random.choice(list(created_accounts.keys()))
            followers = list(account_followers.get(acc_id, []))
            if followers and random.random() < 0.8:
                contributor = random.choice(followers)
            else:
                contributor = created_accounts[acc_id]
            article_id = get_int()
            inst = article_instr("ca", contributor, acc_id, article_id)
            created_articles[(acc_id, article_id)] = contributor
            acct_modifications.append(inst)
        elif prob < 0.7 and created_articles:
            # 删除文章
            acc_id, article_id = random.choice(list(created_articles.keys()))
            contributor = created_articles[(acc_id, article_id)]
            inst = article_instr("da", contributor, acc_id, article_id)
            del created_articles[(acc_id, article_id)]
            acct_modifications.append(inst)
        elif created_accounts:
            # 删除公众号
            acc_id = random.choice(list(created_accounts.keys()))
            creator = created_accounts[acc_id]
            if random.random() < 0.8:
                inst = official_account_instr("doa", creator, acc_id)
            else:
                inst = official_account_instr("doa", random.choice(list(account_followers[acc_id])), acc_id)
            del created_accounts[acc_id]
            if acc_id in account_followers:
                del account_followers[acc_id]
            acct_modifications.append(inst)

    #####################
    # 5. 消息相关指令部分
    msg_modifications = []
    last_idx = 0
    message_ids = set()
    red = set()
    emoji = []
    # 将消息指令按概率分为几类
    am_cmd = int(message_command_num  // 2)
    remain_msg = message_command_num - am_cmd
    add_msg_modifications = []
    send_msg_modifications = []
    delete_cold_emoji_modifications = []

    while am_cmd > 0:
        prob = random.random()
        msg_id = get_int()
        while msg_id in message_ids:
            msg_id = get_int()
        message_ids.add(msg_id)
        tag_id = random.choice(tag_list) if tag_list else 1
        if edge:
            edge_id = random.randint(0, len(list(edge)) - 1)
            edge_list = list(edge)
        else:
            edge_id = 0
            edge_list = [(0,0)]
        if prob < 0.2:
            # add_emoji_message (aem)
            if len(emoji)==0 or random.random() < 0.8:
                emoji_id = random.randint(-1000, 1000)
            else:
                emoji_id = random.choice(emoji)
            emoji.append(emoji_id)
            insts = []
            insts.append('sei ' + str(emoji_id))
            if random.random() < 0.5:
                insts.append('aem ' + str(msg_id) + ' ' + str(emoji_id) + ' 0 ' +
                             str(edge_list[edge_id][0]) + ' ' + str(edge_list[edge_id][1]))
            else:
                insts.append('aem ' + str(msg_id) + ' ' + str(emoji_id) + ' 1 ' +
                             str(tag_id) + ' ' + str(tag_id))
            add_msg_modifications.extend(insts)
        elif prob < 0.4:
            # add_message (am)
            if random.random() < 0.5:
                inst = 'am ' + str(msg_id) + ' ' + str(random.randint(-1000, 1000)) + ' 0 ' + \
                       str(edge_list[edge_id][0]) + ' ' + str(edge_list[edge_id][1])
            else:
                inst = 'am ' + str(msg_id) + ' ' + str(random.randint(-1000, 1000)) + ' 1 ' + \
                       str(tag_id) + ' ' + str(tag_id)
            add_msg_modifications.append(inst)
        elif prob < 0.6:
            # add_red_envelope_message (arem)
            if random.random() < 0.5:
                inst = 'arem ' + str(msg_id) + ' ' + str(random.randint(0, 200)) + ' 0 ' + \
                       str(edge_list[edge_id][0]) + ' ' + str(edge_list[edge_id][1])
                red.add(edge_list[edge_id][0])
                red.add(edge_list[edge_id][1])
            else:
                inst = 'arem ' + str(msg_id) + ' ' + str(random.randint(0, 200)) + ' 1 ' + \
                       str(tag_id) + ' ' + str(tag_id)
                red.add(tag_id)
                if tag_id < len(graph.edges) and tag_id >= 0:
                    for j in range(min(10, len(graph.edges[tag_id]))):
                        red.add(graph.edges[tag_id][j].end)
            add_msg_modifications.append(inst)
        elif prob < 0.8:
            # add_forward_message (afm)
            if created_articles:
                acc_id, article_id = random.choice(list(created_articles.keys()))
            else:
                acc_id, article_id = get_int(), get_int()
            if random.random() < 0.5:
                inst = 'afm ' + str(msg_id) + ' ' + str(article_id) + ' 0 ' + \
                       str(edge_list[edge_id][0]) + ' ' + str(edge_list[edge_id][1])
            else:
                inst = 'afm ' + str(msg_id) + ' ' + str(article_id) + ' 1 ' + \
                       str(tag_id) + ' ' + str(tag_id)
            add_msg_modifications.append(inst)
        else:
            if random.random() < 0.5:
                inst = 'am ' + str(msg_id) + ' ' + str(random.randint(-1000, 1000)) + ' 0 ' + \
                       str(get_int()) + ' ' + str(get_int())
            else:
                inst = 'am ' + str(msg_id) + ' ' + str(random.randint(-1000, 1000)) + ' 1 ' + \
                       str(get_int()) + ' ' + str(get_int())
            add_msg_modifications.append(inst)
        am_cmd -= 1

    # 对余下的消息指令，同样插入
    while remain_msg > 0:
        prob = random.random()
        if prob < 0.5:
            inst = 'sm ' + str(random.choice(list(message_ids)))
            send_msg_modifications.append(inst)
        elif prob < 0.85:
            inst = 'dce ' + str(random.randint(1, 30))
            delete_cold_emoji_modifications.append(inst)
        elif prob < 0.95:
            new_id = get_int()
            while new_id in message_ids:
                new_id = get_int()
            message_ids.add(new_id)
            if random.random() < 0.5:
                inst = 'am ' + str(new_id) + ' ' + str(random.randint(-1000, 1000)) + ' 0 ' + \
                       str(get_int()) + ' ' + str(get_int())
            else:
                inst = 'am ' + str(new_id) + ' ' + str(random.randint(-1000, 1000)) + ' 1 ' + \
                       str(get_int()) + ' ' + str(get_int())
            add_msg_modifications.append(inst)
        else:
            new_id = get_int()
            while new_id in message_ids:
                new_id = get_int()
            message_ids.add(new_id)
            if random.random() < 0.5:
                inst = 'aem ' + str(new_id) + ' ' + str(random.randint(-1000, 1000)) + ' 0 ' + \
                       str(get_int()) + ' ' + str(get_int())
            else:
                inst = 'aem ' + str(new_id) + ' ' + str(random.randint(-1000, 1000)) + ' 1 ' + \
                       str(get_int()) + ' ' + str(get_int())
            add_msg_modifications.append(inst)
        remain_msg -= 1

    # 按顺序合并消息相关指令
    msg_modifications.extend(add_msg_modifications)
    msg_modifications.extend(send_msg_modifications)
    msg_modifications.extend(delete_cold_emoji_modifications)


    #####################
    # 拼接所有部分
    final_instructions = []
    final_instructions.extend(base_instructions)
    final_instructions.extend(graph_modifications)
    final_instructions.extend(tag_modifications)
    final_instructions.extend(acct_modifications)
    final_instructions.extend(msg_modifications)

    #####################
    # 6. 查询指令部分
    while query_command_num > 0:
        prob = random.random()
        if prob < 0.05:
            if random.random() < 0.99 and node:
                tmp = np.random.choice(list(node), 2)
                inst = 'qv ' + str(tmp[0]) + ' ' + str(tmp[1])
            else:
                inst = 'qv ' + str(get_int()) + ' ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.1:
            if random.random() < 0.99 and node:
                tmp = np.random.choice(list(node), 2)
                inst = 'qci ' + str(tmp[0]) + ' ' + str(tmp[1])
            else:
                inst = 'qci ' + str(get_int()) + ' ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.25:
            inst = 'qts'
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.3:
            if random.random() < 0.99 and node:
                inst = 'qba ' + str(np.random.choice(list(node)))
            else:
                inst = 'qba ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.35:
            inst = 'qcs'
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.4:
            if random.random() < 0.99:
                inst = 'qsp ' + str(np.random.choice(list(node))) + ' ' + str(np.random.choice(list(node)))
            else:
                inst = 'qsp ' + str(get_int()) + ' ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + 1, len(final_instructions)), inst)
        elif prob < 0.45:
            if random.random() < 0.99 and tag_list:
                inst = 'qtvs ' + str(np.random.choice(tag_list)) + ' ' + str(np.random.choice(tag_list))
            else:
                inst = 'qtvs ' + str(get_int()) + ' ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + 1, len(final_instructions)), inst)
        elif prob < 0.50:
            if random.random() < 0.99 and tag_list:
                inst = 'qtav ' + str(np.random.choice(tag_list)) + ' ' + str(np.random.choice(tag_list))
            else:
                inst = 'qtav ' + str(get_int()) + ' ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + 1, len(final_instructions)), inst)
        elif prob < 0.55:
            if random.random() < 0.99 and node:
                inst = 'qsv ' + str(np.random.choice(list(node)))
            else:
                inst = 'qsv ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + len(tag_modifications) + 1, len(final_instructions)), inst)
        elif prob < 0.70:
            if random.random() < 0.99 and node:
                inst = 'qrm ' + str(np.random.choice(list(node)))
            else:
                inst = 'qrm ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + len(tag_modifications) + 1, len(final_instructions)), inst)
        elif prob < 0.85:
            if random.random() < 0.99 and emoji:
                inst = 'qp ' + str(np.random.choice(list(emoji)))
            else:
                inst = 'qp ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + len(tag_modifications) + len(add_msg_modifications) + 1, len(final_instructions)), inst)
        else:
            if len(node) > 0 and random.random() < 0.99:
                inst = 'qm ' + str(np.random.choice(list(node)))
            else:
                inst = 'qm ' + str(get_int())
            final_instructions.insert(random.randint(len(base_instructions) + len(graph_modifications) + len(tag_modifications) + 1, len(final_instructions)), inst)
        query_command_num -= 1

    # -----------------------生成 load_network 指令 -----------------------
    if isload < config['load_prob']:
        load_node_num = random.randint(1, min(100, node_num, len(node)))
        load_edge_num = random.randint(int(load_node_num * (load_node_num - 1) / 20),
                                       int(load_node_num * (load_node_num - 1) / 2))
        load_section = []
        load_section.append('ln ' + str(load_node_num))
        load_node = random.sample(list(node), load_node_num)
        load_section.append(" ".join(str(x) for x in load_node))
        load_section.append(" ".join("OO_load_" + str(x) for x in load_node))
        load_section.append(" ".join(str(random.randint(1, 200)) for _ in range(load_node_num)))
        for i in range(2, load_node_num + 1):
            row = []
            for j in range(1, i):
                if random.random() < float(load_edge_num) / (load_node_num * (load_node_num - 1) / 2):
                    row.append(str(random.randint(1, 200)))
                else:
                    row.append('0')
            load_section.append(" ".join(row))
        load_section.extend(final_instructions)
        final_instructions = load_section

    # 写入文件
    with open(input_file, 'w') as f:
        path = Path(input_file)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        for line in final_instructions:
            f.write(line + "\n")


def get_int():
    return random.randint(-0x80000000, 0x7ffffff)


def official_account_instr(instr_name, person_id, account_id):
    """生成公众号相关指令
       create_official_account: coa
       delete_official_account: doa
    """
    if instr_name == "coa":
        return f"coa {person_id} {account_id} Account_{account_id}"
    return f"{instr_name} {person_id} {account_id}"


def article_instr(instr_name, person_id, account_id, article_id):
    """生成文章相关指令
       contribute_article: ca
       delete_article: da
    """
    if instr_name == "ca":
        return f"ca {person_id} {account_id} {article_id} Article_{article_id}"
    return f"{instr_name} {person_id} {account_id} {article_id}"


if __name__ == "__main__":
    generate_data('in.txt')