import random
import os

# 定义常量
MAX_INT = (1 << 31) - 1
ELEVATOR_POOL = [1, 2, 3, 4, 5, 6]
FLOOR_POOL = ['B4', 'B3', 'B2', 'B1', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
SCHE_FLOOR_POOL = ['B2', 'B1', 'F1', 'F2', 'F3', 'F4', 'F5']
SPEEDS = [0.2, 0.3, 0.4, 0.5]
MAX_SCHE_COUNT = 12
MIN_SCHE_INTERVAL = 6.0
TIME_LIMIT = 48.0  # 最大时间限制
REQUEST_COUNT_RANGE = (40, 70)
GROUP_SIZE_RANGE = (5, 8)
SCENARIO_PROBS = {'high_concurrent': 0.2, 'high_concentration': 0.15, 
                  'high_burst': 0.15, 'random': 0.5}
SCHE_PROB_IN_RANDOM = 0.2

# 生成唯一ID
def get_id(used_ids):
    id = random.randint(1, MAX_INT % 1000) 
    while id in used_ids:
        id = random.randint(1, MAX_INT % 1000)
    used_ids[id] = True
    return id

# 生成组间时间间隔（确保非负且不超过 TIME_LIMIT）
def get_time_gap(current_time):
    remaining_time = TIME_LIMIT - current_time
    chance = random.randint(0, MAX_INT) % 100
    if chance < 2:
        gap = min(10.0, remaining_time)
    elif chance >= 98:
        gap = min(5.0, remaining_time)
    elif chance >= 5 and chance < 10 or chance >= 90 and chance < 95:
        gap = min(random.uniform(3, 6), remaining_time)
    elif chance >= 10 and chance < 45 or chance >= 55 and chance < 90:
        gap = min(random.uniform(1, 3), remaining_time)
    else:
        gap = min(random.uniform(0.1, 0.6), remaining_time)
    return max(gap, 0.0)  # 确保非负

# 生成组内小时间间隔（确保非负且不超过 TIME_LIMIT）
def get_intra_group_time_gap(current_time):
    remaining_time = TIME_LIMIT - current_time
    return min(random.uniform(0, 1), remaining_time)

# 楼层选择
def get_floor(is_sche=False):
    return random.choice(SCHE_FLOOR_POOL if is_sche else FLOOR_POOL)

# 生成优先级指数
def get_priority():
    return random.randint(1, 100)

# 生成临时调度速度
def get_sche_speed():
    return random.choice(SPEEDS)

# 生成普通请求
def generate_request(id, priority, time, from_floor=None, to_floor=None):
    from_floor = get_floor() if from_floor is None else from_floor
    to_floor = get_floor() if to_floor is None else to_floor
    while to_floor == from_floor:
        to_floor = get_floor()
    return f'[{format(time, ".1f")}]' \
           f'{id}-PRI-{priority}-FROM-{from_floor}-TO-{to_floor}\n'

# 生成临时调度
def generate_schedule(elevator, time):
    target_floor = get_floor(is_sche=True)
    speed = get_sche_speed()
    return f'[{format(time, ".1f")}]SCHE-{elevator}-{speed}-{target_floor}\n'

# 生成一组请求
def generate_group(used_ids, base_time, group_size, last_sche_times, sche_count, has_high_burst):
    lines = []
    probs = SCENARIO_PROBS.copy()
    if has_high_burst:
        probs['high_burst'] = 0.0
        total = sum(probs.values())
        for key in probs:
            probs[key] /= total  # 重新归一化概率
    scenario = random.choices(list(probs.keys()), weights=list(probs.values()), k=1)[0]

    current_time = base_time  # 从组的基准时间开始

    if scenario == 'high_concurrent':  # 高并发：同一时刻
        for _ in range(group_size):
            id = get_id(used_ids)
            priority = get_priority()
            lines.append(generate_request(id, priority, current_time))

    elif scenario == 'high_concentration':  # 高集中：时间递增
        fixed_floor = get_floor()
        is_from_fixed = random.choice([True, False])
        for _ in range(group_size):
            id = get_id(used_ids)
            priority = get_priority()
            if is_from_fixed:
                lines.append(generate_request(id, priority, current_time, from_floor=fixed_floor))
            else:
                lines.append(generate_request(id, priority, current_time, to_floor=fixed_floor))
            current_time += get_intra_group_time_gap(current_time)

    elif scenario == 'high_burst':  # 高突发：仅5条调度，同一时刻
        available_elevators = [e for e in ELEVATOR_POOL 
                             if current_time - last_sche_times[e] >= MIN_SCHE_INTERVAL]
        if len(available_elevators) >= 5 and sche_count + 5 <= MAX_SCHE_COUNT:
            sche_count += 5
            for elevator in random.sample(available_elevators, 5):
                lines.append(generate_schedule(elevator, current_time))
                last_sche_times[elevator] = current_time
            has_high_burst = True

    else:  # random：随机生成，时间递增
        for _ in range(group_size):
            if (random.choices([True, False], weights=[SCHE_PROB_IN_RANDOM, 1 - SCHE_PROB_IN_RANDOM])[0] 
                and sche_count < MAX_SCHE_COUNT):
                available_elevators = [e for e in ELEVATOR_POOL 
                                     if current_time - last_sche_times[e] >= MIN_SCHE_INTERVAL]
                if available_elevators:
                    elevator = random.choice(available_elevators)
                    lines.append(generate_schedule(elevator, current_time))
                    last_sche_times[elevator] = current_time
                    sche_count += 1
            else:
                id = get_id(used_ids)
                priority = get_priority()
                lines.append(generate_request(id, priority, current_time))
            current_time += get_intra_group_time_gap(current_time)

    return lines, sche_count, has_high_burst, current_time  # 返回组内最大时间

# 生成电梯请求数据和临时调度
def generate_input():
    used_ids = {}
    stdin_lines = []
    max_requests = random.randint(REQUEST_COUNT_RANGE[0], REQUEST_COUNT_RANGE[1])
    time = 1.0  # 全局时间，从 1.0 开始
    request_count = 0
    sche_count = 0
    last_sche_times = {e: -MIN_SCHE_INTERVAL for e in ELEVATOR_POOL}
    has_high_burst = False

    while request_count < max_requests and time < TIME_LIMIT:
        group_size = random.randint(GROUP_SIZE_RANGE[0], GROUP_SIZE_RANGE[1])
        if sche_count < MAX_SCHE_COUNT or request_count < max_requests:
            group_lines, sche_count, has_high_burst, max_group_time = generate_group(
                used_ids, time, group_size, last_sche_times, sche_count, has_high_burst
            )
            stdin_lines.extend(group_lines)
            for line in group_lines:
                if 'SCHE' not in line:
                    request_count += 1
            # 更新全局时间为组内最大时间加上组间间隔
            time = max_group_time + get_time_gap(max_group_time)
            if time > TIME_LIMIT:  # 如果超过 50 秒，停止生成
                break

    return stdin_lines, request_count, sche_count

# 主函数
def main():
    test_num = 5000  # 定义生成数量常量
    testcase_dir = 'testcase'  # 定义存放文件的文件夹

    # 创建 testcase 文件夹
    if not os.path.exists(testcase_dir):
        os.makedirs(testcase_dir)

    # 生成 test_num 个文件
    for i in range(test_num):
        stdin_lines, request_count, sche_count = generate_input()
        file_path = os.path.join(testcase_dir, f'test_{i + 1}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(stdin_lines)
        print(f"Generated {request_count} requests and {sche_count} schedules in {file_path}")

# 调用主函数
if __name__ == '__main__':
    main()
