from calendar import c
import json
from math import e
import os
from pathlib import Path
import re
import sched
import shutil
import subprocess
import sys
import time

input_to_terminal = False

class Elevator:
    def __init__(self, id):
        self.id = id
        self.status = "WAIT"
        self.in_schedule = False
        self.cur_floor = "F1"
        self.speed = 0.4  # 0.4s/floor
        self.last_arrive_time = 0
        self.accept_nobegin = False
        self.accept_time = 0
        self.accept2begin_arrive_num = 0
        self.sche_target_floor = 0
        self.door_open_time_in_schedule = 0
        self.inside_passenger_num = 0
        self.receive_outside_num = 0 
        self.door_is_open = False
        
class Passenger:
    def __init__(self, id, pri, from_floor, to_floor, request_time):
        self.id = id
        self.pri = pri
        self.from_floor = from_floor
        self.to_floor = to_floor
        self.request_time = request_time
        self.arrive = False
        self.in_elevator = False
        self.need_dispatch = True
        self.cur_floor = from_floor

class Schedule:
    def __init__(self, elevator_id, speed, target_floor):
        self.elevator_id = elevator_id
        self.modified_speed = speed
        self.target_floor = target_floor
        self.done = False

class JavaTools:
    def __init__(self):
        pass

    def generate_jar(java_dir, output_filename = "test.jar",external_jar_path = "", compile_output_dir = "./out/test", jar_output_dir = "./", mode = "windows"):
        """
        生成jar包
        
        Args:
            java_dir: java文件所在目录
            output_filename: jar包输出文件名
            compile_output_dir: 编译class输出目录
            jar_output_path: jar包输出目录
        
        return: 
            是否成功
        """
        if (mode == 'mac'):
            java_dir = os.path.expanduser(java_dir)
            external_jar_path = os.path.expanduser(external_jar_path)
        
        # 检查compile_output_dir是否存在，不存在则创建
        os.makedirs(compile_output_dir, exist_ok=True)
        
        # 使用os删除compile_output_dir下的所有文件
        if os.path.exists(compile_output_dir):
            for file_name in os.listdir(compile_output_dir):
                file_path = os.path.join(compile_output_dir, file_name)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # 删除文件或符号链接
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # 删除子目录
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
        
        # 编译file_path中的所有java文件
        java_files = list(Path(java_dir).rglob("*.java"))
        #print("Found Java files:")
        #print("\n".join(str(file) for file in java_files))
        process = subprocess.Popen(
            ['javac', '-d', compile_output_dir, '-encoding', 'utf-8', '-classpath', external_jar_path] + [str(file) for file in java_files],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            if (mode == 'mac'):
                print(f"Error in compiling {java_dir}: {stderr.decode('utf-8', errors='ignore')}")
            elif (mode == 'windows'):
                print(f"Error in compiling {java_dir}: {stderr.decode('gbk', errors='ignore')}")
            return False

        # 生成MANIFEST.MF文件
        with open('MANIFEST.MF', 'w') as f:
            f.write('Main-Class: MainClass\n')
            f.write(f'Class-Path: {os.path.basename(external_jar_path)}\n')

        process = subprocess.Popen(
            ['jar', 'cfm', output_filename, 'MANIFEST.MF', '-C', compile_output_dir, jar_output_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error in creating {output_filename}: {stderr.decode('gbk', errors='ignore')}")
            return False
        return True
    
    
class Logger:
    def log(str, log_output, color):
        with open(log_output, "a") as f:
            f.write(str)
            f.write('\n')
        if input_to_terminal == True:
            if color == "red":
                print("\033[31m" + str + "\033[0m")
            elif color == "green":
                print("\033[32m" + str + "\033[0m")
            elif color == "yellow":
                print("\033[33m" + str + "\033[0m")
            elif color == "blue":
                print("\033[34m" + str + "\033[0m")
            else:
                print(str)
    
def main():
    #从命令行参数获取 worker_id（由主测试程序传递）
    worker_id = None
    if len(sys.argv) > 1:
        worker_id = sys.argv[1]  # 例如 "1" 表示 worker_1

    # 确保elevator1.jar、stdin.txt和datainput_student_win64.exe / datainput_student_darwin_m1在当前目录下
    mode = 'windows' # 'mac' or 'windows'
    JavaTools.generate_jar(java_dir="../../../src", # .java文件所在目录
                           output_filename="code.jar", 
                           external_jar_path="elevator2.jar", # 外部jar包路径
                           compile_output_dir="compile",
                           jar_output_dir="./", 
                           mode = mode)
    if (mode == 'mac'):
        os.system('chmod +x datainput_student_darwin_m1')
        cmd = "./datainput_student_darwin_m1 | java -jar code.jar"
    elif (mode == 'windows'):
        cmd = ".\\datainput_student_win64.exe | java -jar code.jar"

    passengers = [Passenger(0, 0, 0, 0, 0) for i in range(1000)]
    elevators = [None] + [Elevator(i) for i in range(1, 7)]
    schedules = [None for _ in range(7)]
        
    # 需要记录的数据
    Trun = 0
    average_time = 0
    power_conusmed = 0
    total_pri = 0
    
    # 定义 log 目录的绝对路径
    log_dir = os.path.abspath("../../log")
    # 生成输出文件路径
    output = os.path.join(log_dir, "output_worker_" + worker_id + time.strftime("_%m%d_%H%M%S") + ".txt")
    with open("stdin.txt", "r") as f:
        line = f.readline()
            
        while line:
            with open(output, "a") as out:
                out.write(line)
            
            match = re.search(r"\[(\d+(\.\d+)?)\]", line)
            if match:
                request_time = float(match.group(1))
                
            line = re.sub(r"\[\d+(\.\d+)?\]\s*", "", line)
            parts = line.strip().split('-')
            if parts[0] == "SCHE":
                pass
            else:
                passenger_id = parts[0]
                priority = parts[2]
                from_floor = parts[4]
                to_floor = parts[6]
                passengers[int(passenger_id)] = Passenger(int(passenger_id), int(priority), from_floor, to_floor, request_time)
                total_pri += int(parts[2])
                
            line = f.readline()
        with open(output, "a") as out:
                out.write('\n')
        
    timeout = 120
    start_time = time.time()
    error = False
    try:
        # 启动进程
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 逐行读取并实时打印输出
        final_info_time = 0
        for line in iter(process.stdout.readline, ''):
            with open(output, "a") as f:
                f.write(line)
                
            match = re.search(r"\[(.*)?(\d+(\.\d+)?)\]", line)
            if match:
                info_time = float(match.group(1))
                final_info_time = info_time
                pass
            
            origin_line = line
            
            # 去掉时间戳
            line = re.sub(r"\[(.*)?\d+(\.\d+)?\]\s*", "", line)
            parts = line.strip().split('-')
            
            # 重点展示RECEIVE行和SCHE行
            if input_to_terminal == True:
                if parts[0] == "RECEIVE":
                    print("\033[34m" + origin_line + "\033[0m", end="")
                elif parts[0] == "SCHE":
                    print("\033[33m" + origin_line + "\033[0m", end="")
                else:
                    print(origin_line, end="")
            
            if parts[0] == "ARRIVE":
                power_conusmed += 0.4
                cur_floor = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                this_elevator.cur_floor = cur_floor
                if this_elevator.accept_nobegin == True:
                    this_elevator.accept2begin_arrive_num += 1
                    if this_elevator.accept2begin_arrive_num > 2:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": arrive num when accept but not begin exceed 2!", output, "red")
                # 速度判断
                if (this_elevator.last_arrive_time == 0):
                    this_elevator.last_arrive_time = info_time
                else:
                    # 保留小数点后四位进行比较
                    delta = round(info_time - this_elevator.last_arrive_time, 4)
                    speed = round(float(this_elevator.speed), 4)
                    if delta < speed:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": speed is too fast! your speed need at least " + str(this_elevator.speed) , output, "red")
                # 非法移动判断
                if this_elevator.in_schedule == False and this_elevator.receive_outside_num == 0 and this_elevator.inside_passenger_num == 0:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't move when no schedule and no receive outside and no one inside", output, "red")
                
            elif parts[0] == "RECEIVE":
                passenger_id = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                this_elevator.receive_outside_num += 1
                # 不能重复调度
                if this_passenger.need_dispatch == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't receive when already dispatch", output, "red")
                # 调度期间不能receive
                if this_elevator.in_schedule == True:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't receive when in schedule", output, "red")
                
            elif parts[0] == "SCHE":
                if (parts[1] == "ACCEPT"):
                    elevator_id = parts[2]
                    modified_speed = parts[3]
                    target_floor = parts[4]
                    this_elevator = elevators[int(elevator_id)]
                    if schedules[int(elevator_id)] == None:
                        schedules[int(elevator_id)] = Schedule(elevator_id, modified_speed, target_floor)
                    elif schedules[int(elevator_id)].done == True:
                        schedules[int(elevator_id)] = Schedule(elevator_id, modified_speed, target_floor)
                    else:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't accept schedule when last schedule undone", output, "red")
                    this_elevator.accept_nobegin = True
                    this_elevator.accept_time = info_time
                    this_elevator.sche_target_floor = target_floor
                    
                if (parts[1] == "BEGIN"):
                    elevator_id = parts[2]
                    this_elevator = elevators[int(elevator_id)]
                    this_elevator.speed = schedules[int(elevator_id)].modified_speed
                    this_elevator.in_schedule = True
                    this_elevator.accept_nobegin = False
                    this_elevator.accept2begin_arrive_num = 0
                    if this_elevator.door_is_open == True:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't begin schedule when door is open", output, "red")
                    
                elif (parts[1] == "END"):
                    elevator_id = parts[2]
                    this_elevator = elevators[int(elevator_id)]
                    this_elevator.in_schedule = False
                    this_elevator.speed = 0.4
                    delta = round(info_time - this_elevator.accept_time, 4)
                    threshold = round(6.0, 4)
                    if delta > threshold:
                        Logger.log("Elevator " + elevator_id + ": Time between accept and end exceed 6s", output, "red")
                    if this_elevator.door_is_open == True:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't end schedule when door is open", output, "red")
                    if this_elevator.inside_passenger_num > 0:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't end schedule because has passenger inside", output, "red")
                    if schedules[int(elevator_id)] != None:
                        schedules[int(elevator_id)].done = True
                    else:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't end schedule when no schedule begin", output, "red")
                
            elif (parts[0] == "OPEN"):
                power_conusmed += 0.1
                cur_floor = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                # 重复开门检测
                if (this_elevator.door_is_open == True):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't open door when door is already open", output, "red")
                this_elevator.door_is_open = True
                # 调度期间开门检测
                if (this_elevator.in_schedule == True):
                    if (this_elevator.cur_floor != this_elevator.sche_target_floor):
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't open door in Schedule when not arrive target floor", output, "red")
                    else:
                        this_elevator.door_open_time_in_schedule = info_time
                
            elif (parts[0] == "CLOSE"):
                power_conusmed += 0.1
                cur_floor = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                # 重复关门检测
                if (this_elevator.door_is_open == False):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't close door when door is already close", output, "red")
                this_elevator.door_is_open = False
                # 调度期间关门检测
                if (this_elevator.in_schedule == True):
                    if (this_elevator.cur_floor != this_elevator.sche_target_floor):
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't close door in Schedule when not arrive target floor", output, "red")
                    else:
                        delta = round(info_time - this_elevator.door_open_time_in_schedule, 4)
                        threshold = round(1.0, 4)
                        if delta < threshold:
                            Logger.log("Elevator " + elevator_id + ": close door too fast in schedule at target floor", output, "red")

                
            elif (parts[0] == "OUT"):
                flag = parts[1]
                passenger_id = parts[2]
                cur_floor = parts[3]
                elevator_id = parts[4]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                this_elevator.inside_passenger_num -= 1
                this_passenger.cur_floor = cur_floor
                if this_elevator.in_schedule == True and this_elevator.cur_floor != this_elevator.sche_target_floor:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't out in schedule expect arrive schedule target floor", output, "red")
                if this_elevator.door_is_open == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't out when door is closed", output, "red")
                if flag == "S": 
                    average_time += (info_time - this_passenger.request_time) * this_passenger.pri
                    this_passenger.need_dispatch = False
                    this_passenger.arrive = True
                    if (this_elevator.cur_floor != this_passenger.to_floor):
                        error = True
                        Logger.log("Elevator " + elevator_id + ": passenger " + str(this_passenger.id) + " don't arrive destination but input -S", output, "red")
                elif flag == "F":
                    this_passenger.need_dispatch = True
                    if (this_elevator.cur_floor == this_passenger.to_floor):
                        error = True
                        Logger.log("Elevator " + elevator_id + ": passenger " + str(this_passenger.id) + " arrive destination but input -F", output, "red")
                    
            elif parts[0] == "IN":
                passenger_id = parts[1]
                cur_floor = parts[2]
                elevator_id = parts[3]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                this_elevator.inside_passenger_num += 1
                # 判断乘客当前楼层是否正确
                if this_passenger.cur_floor != cur_floor and this_passenger.arrive == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger " + str(this_passenger.id) + " can't enter the elevator because he is at " + this_passenger.cur_floor, output, "red")
                if this_elevator.door_is_open == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in when door is closed", output, "red")
                if this_elevator.in_schedule == True and this_elevator.cur_floor != this_elevator.sche_target_floor:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in when schedule", output, "red")
            
            # 判断是否超时
            if time.time() - start_time > timeout:
                raise subprocess.TimeoutExpired(cmd, timeout)
            
        average_time /= total_pri
        
        all_arrived = True
        for passenger in passengers:
            if passenger.id == 0:
                continue
            if passenger.arrive == False:
                all_arrived = False
                Logger.log("Passenger " + str(passenger.id) + " did not arrive at the destination!", output, "red")
        
        if all_arrived:
            Logger.log("All passengers arrived!", output, "green")
            
        if error:
            Logger.log("Error occurred!", output, "red")
            
        Logger.log("Run Time: " + str(max(final_info_time, time.time() - start_time)), output, "blue")
        Logger.log("Average Time: " + str(average_time), output, "blue")
        Logger.log("Power Consumed: " + str(power_conusmed), output, "blue")

        # 等待进程结束（确保 stderr 也被读取）
        process.stdout.close()
        stderr = process.stderr.read()
        process.wait()
        if stderr:
            Logger.log("Error output:", stderr)
            error = True
            
    except subprocess.TimeoutExpired:
        Logger.log(worker_id + "Process timed out! Killing process...")
        error = True
        process.kill()

    # 返回结果
    result = {
        "worker_id": worker_id,
        "success": not error and all_arrived,
        "log_file": output
    }
    print(json.dumps(result))
    if result["success"]:
        os.remove(output)
    return result

if __name__ == "__main__":
    result = main()