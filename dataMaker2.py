import random
import os

# 定义常量
MAX_INT = (1 << 31) - 1
ELEVATOR_POOL = [1, 2, 3, 4, 5, 6]
FLOOR_POOL = ['B4', 'B3', 'B2', 'B1', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7']
SCHE_FLOOR_POOL = ['B2', 'B1', 'F1', 'F2', 'F3', 'F4', 'F5']
SPEEDS = [0.2, 0.3, 0.4, 0.5]
MAX_SCHE_COUNT = 20
MIN_SCHE_UPDATE_INTERVAL = 8.0
TIME_LIMIT = 48.0  # 最大时间限制
REQUEST_COUNT_RANGE = (60, 90)

# 生成唯一ID
def get_id(used_ids):
    id = random.randint(1, MAX_INT % 1000)
    while id in used_ids:
        id = random.randint(1, MAX_INT % 1000)
    used_ids[id] = True
    return id

# 生成阶段间时间间隔（0-2秒）
def get_stage_time_gap():
    return random.uniform(0, 2)

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

# 生成双轿厢改造请求
def generate_update(time, updated_elevators):
    available_elevators = [e for e in ELEVATOR_POOL if e not in updated_elevators]
    if len(available_elevators) < 2:
        return None
    elevator_a, elevator_b = random.sample(available_elevators, 2)
    target_floor = get_floor(is_sche=True)
    updated_elevators.update([elevator_a, elevator_b])
    return f'[{format(time, ".1f")}]UPDATE-{elevator_a}-{elevator_b}-{target_floor}\n'

# 生成 30-40 条 REQUEST（50% 随机，50% 高集中）
def generate_requests(used_ids, current_time, num_requests=None):
    lines = []
    num_requests = num_requests
    if random.random() < 0.5:  # 50% 随机
        for _ in range(num_requests):
            id = get_id(used_ids)
            priority = get_priority()
            lines.append(generate_request(id, priority, current_time))
    else:  # 50% 高集中
        fixed_floor = get_floor()
        is_from_fixed = random.choice([True, False])
        for _ in range(num_requests):
            id = get_id(used_ids)
            priority = get_priority()
            if is_from_fixed:
                lines.append(generate_request(id, priority, current_time, from_floor=fixed_floor))
            else:
                lines.append(generate_request(id, priority, current_time, to_floor=fixed_floor))
    return lines

# 生成电梯请求数据
def generate_input():
    used_ids = {}
    stdin_lines = []
    max_requests = random.randint(REQUEST_COUNT_RANGE[0], REQUEST_COUNT_RANGE[1])
    current_time = 1.0
    request_count = 0
    sche_count = 0
    update_count = 0
    updated_elevators = set()

    # 选择生成模式：60% 模式1，40% 模式2
    mode = random.choices(['mode1', 'mode2'], weights=[0.6, 0.4])[0]

    if mode == 'mode1':
        # 模式1：t=1.0 生成 2-3 UPDATE 和 30-40 REQUEST
        num_updates = random.randint(2, 3)
        available_elevators = [e for e in ELEVATOR_POOL if e not in updated_elevators]
        if len(available_elevators) >= 2 * num_updates:
            for _ in range(num_updates):
                update_line = generate_update(current_time, updated_elevators)
                if update_line:
                    stdin_lines.append(update_line)
                    update_count += 1

        current_time += random.uniform(0, 0.5)
        num_requests = random.randint(20, 40)
        if request_count + num_requests + update_count <= max_requests:
            request_lines = generate_requests(used_ids, current_time, num_requests)
            stdin_lines.extend(request_lines)
            request_count += len(request_lines)

        # 间隔 0-2 秒
        current_time += get_stage_time_gap()
        if current_time < TIME_LIMIT:
            # t=current_time 生成 30-40 REQUEST
            num_requests = random.randint(30, 40)
            if request_count + num_requests + update_count <= max_requests:
                request_lines = generate_requests(used_ids, current_time, num_requests)
                stdin_lines.extend(request_lines)
                request_count += len(request_lines)

    else:
        # 模式2：t=1.0 生成 3-6 SCHE，30-40 REQUEST，2-3 UPDATE
        # 先记录初始可用电梯
        available_elevators = [e for e in ELEVATOR_POOL if e not in updated_elevators]

        # 生成 3-6 SCHE
        num_sche = random.randint(3, 6)
        if len(available_elevators) >= num_sche and sche_count + num_sche <= MAX_SCHE_COUNT:
            sche_count += num_sche
            for elevator in random.sample(available_elevators, num_sche):
                stdin_lines.append(generate_schedule(elevator, current_time))

        # 生成 30-40 REQUEST
        num_requests = random.randint(20, 40)
        if request_count + num_requests + update_count <= max_requests:
            request_lines = generate_requests(used_ids, current_time, num_requests)
            stdin_lines.extend(request_lines)
            request_count += len(request_lines)

        current_time += random.uniform(8, 9)
        # 生成 2-3 UPDATE
        num_updates = random.randint(2, 3)
        available_elevators = [e for e in ELEVATOR_POOL if e not in updated_elevators]
        if len(available_elevators) >= 2 * num_updates:
            for _ in range(num_updates):
                update_line = generate_update(current_time, updated_elevators)
                if update_line:
                    stdin_lines.append(update_line)
                    update_count += 1

        # 间隔 0-2 秒
        current_time += get_stage_time_gap()
        if current_time < TIME_LIMIT:
            # t=current_time 生成 30-40 REQUEST
            num_requests = random.randint(30, 40)
            if request_count + num_requests + update_count + sche_count > max_requests:
                num_requests = random.randint(10, 30)
            request_lines = generate_requests(used_ids, current_time, num_requests)
            stdin_lines.extend(request_lines)
            request_count += len(request_lines)

    return stdin_lines, request_count, sche_count, update_count

# 主函数
def main():
    test_num = 1000
    testcase_dir = 'testcase2'

    if not os.path.exists(testcase_dir):
        os.makedirs(testcase_dir)

    for i in range(test_num):
        stdin_lines, request_count, sche_count, update_count = generate_input()
        file_path = os.path.join(testcase_dir, f'test_{i + 1}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(stdin_lines)
        print(f"Generated {request_count} requests, {sche_count} schedules, and {update_count} updates in {file_path}")

if __name__ == '__main__':
    main()