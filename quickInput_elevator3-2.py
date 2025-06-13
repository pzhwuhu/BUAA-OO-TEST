from calendar import c
from logging import info
from math import e
import os
from pathlib import Path
import re
import sched
import shutil
import subprocess
import time

from sympy import N, true

input_to_terminal = True
epsilon = 1e-4

def intOf(str):
    if str.startswith("F"):
        return int(str[1:])
    elif str.startswith("B"):
        return -int(str[1:])
    
def strOf(num):
    if num >= 0:
        return "F" + str(num)
    else:
        return "B" + str(-num)

class Elevator:
    def __init__(self, id):
        self.id = id
        self.status = "WAIT"
        self.in_schedule = False
        self.cur_floor = "F1"
        self.last_floor = "F1"
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
        self.in_transfer_floor = False
        self.transfer_floor = "None"
        self.update_accept_time = 0
        self.update_accept_no_begin = False
        self.update_begin_no_end = False
        self.has_been_updated = False
        self.update_accept_no_begin_num = 0
        self.in_schedule = False
        self.limit_min_floor = "B4"
        self.limit_max_floor = "F7"
        self.passengers = []
        self.receive_outside = []
        
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
    # 确保elevator1.jar、stdin.txt和datainput_student_win64.exe / datainput_student_darwin_m1在当前目录下
    mode = 'windows' # 'mac' or 'windows'
    JavaTools.generate_jar(java_dir="../src", # .java文件所在目录
                           output_filename="code.jar", 
                           external_jar_path="elevator3.jar", # 外部jar包路径
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
    
    os.makedirs("log", exist_ok=True)
    output = "log/output_" + time.strftime("%m%d_%H%M%S") + ".txt" 
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
            if parts[0] == "SCHE" or parts[0] == "UPDATE":
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
        
    timeout = 100
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
                elif parts[0] == "SCHE" or parts[0] == "UPDATE":
                    print("\033[33m" + origin_line + "\033[0m", end="")
                else:
                    print(origin_line, end="")
            
            if parts[0] == "ARRIVE":
                power_conusmed += 0.4
                cur_floor = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                this_elevator.last_floor = this_elevator.cur_floor
                this_elevator.cur_floor = cur_floor
                if this_elevator.accept_nobegin == True:
                    this_elevator.accept2begin_arrive_num += 1
                    if this_elevator.accept2begin_arrive_num > 2:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": arrive num when accept but not begin exceed 2!", output, "red")
                if this_elevator.update_accept_no_begin == True:
                    this_elevator.update_accept_no_begin_num += 1
                    if this_elevator.update_accept_no_begin_num > 2:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": arrive num when update accept but not begin exceed 2!", output, "red")
                # 楼层限制判断
                if intOf(cur_floor) < intOf(this_elevator.limit_min_floor) or intOf(cur_floor) > intOf(this_elevator.limit_max_floor):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't arrive at floor " + cur_floor + " because of limit", output, "red")
                if this_elevator.has_been_updated and this_elevator.partner.cur_floor == cur_floor:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't arrive at floor " + cur_floor + " because of partner elevator is at this floor", output, "red")
                # 速度判断
                if (this_elevator.last_arrive_time == 0):
                    this_elevator.last_arrive_time = info_time
                else:
                    if (info_time - this_elevator.last_arrive_time) < float(this_elevator.speed) - epsilon :
                        error = True
                        Logger.log("Elevator " + elevator_id + ": speed is too fast! your speed need at least " + str(this_elevator.speed) , output, "red")
                # 非法移动判断
                if this_elevator.in_schedule == False and this_elevator.receive_outside_num == 0 and this_elevator.inside_passenger_num == 0:
                    if this_elevator.last_floor != this_elevator.transfer_floor:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't move when no schedule and no receive outside and no one inside, the transfer floor is " + this_elevator.transfer_floor, output, "red")
                if (this_elevator.update_begin_no_end == True):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't move after update begin but not end", output, "red")
                
            elif parts[0] == "RECEIVE":
                passenger_id = parts[1]
                elevator_id = parts[2]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                # 不能重复调度
                if this_passenger.need_dispatch == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't receive when already dispatch", output, "red")
                this_elevator.receive_outside_num += 1
                this_passenger.need_dispatch = False
                this_elevator.receive_outside.append(this_passenger)
                # 调度期间不能receive
                if this_elevator.in_schedule == True:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't receive when in schedule", output, "red")
                # 改造期间不能receive
                if (this_elevator.update_begin_no_end == True):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't receive when update begin but not end", output, "red")
                
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
                    for passenger in this_elevator.receive_outside:
                        passenger.need_dispatch = True
                        this_elevator.receive_outside_num -= 1
                    this_elevator.receive_outside.clear()
                    if this_elevator.door_is_open == True:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": you can't begin schedule when door is open", output, "red")
                
                elif (parts[1] == "END"):
                    elevator_id = parts[2]
                    this_elevator = elevators[int(elevator_id)]
                    this_elevator.in_schedule = False
                    this_elevator.speed = 0.4
                    if info_time - this_elevator.accept_time > 6 + epsilon:
                        error = True
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
            
            elif (parts[0] == "UPDATE"):
                    elevator_a_id = parts[2]
                    elevator_b_id = parts[3]
                    elevator_a = elevators[int(elevator_a_id)]
                    elevator_b = elevators[int(elevator_b_id)]
                    if parts[1] == "ACCEPT":
                        elevator_a.update_accept_time = info_time
                        elevator_b.update_accept_time = info_time
                        transfer_floor = parts[4]
                        elevator_a.transfer_floor = transfer_floor
                        elevator_b.transfer_floor = transfer_floor
                        elevator_a.update_accept_no_begin = True
                        elevator_b.update_accept_no_begin = True
                        elevator_a.partner = elevator_b
                        elevator_b.partner = elevator_a
                    elif parts[1] == "BEGIN":
                        elevator_a.update_begin_time = info_time
                        elevator_b.update_begin_time = info_time
                        elevator_a.update_accept_no_begin = False
                        elevator_b.update_accept_no_begin = False
                        elevator_a.update_begin_no_end = True
                        elevator_b.update_begin_no_end = True
                        for passenger in elevator_a.receive_outside:
                            passenger.need_dispatch = True
                            elevator_a.receive_outside_num -= 1
                        elevator_a.receive_outside.clear()
                        for passenger in elevator_b.receive_outside:
                            passenger.need_dispatch = True
                            elevator_b.receive_outside_num -= 1
                        elevator_b.receive_outside.clear()
                        if elevator_a.inside_passenger_num > 0:
                            error = True
                            Logger.log("Elevator " + elevator_a_id + ": you can't begin update when has passenger inside", output, "red")
                        if elevator_b.inside_passenger_num > 0:
                            error = True
                            Logger.log("Elevator " + elevator_b_id + ": you can't begin update when has passenger inside", output, "red")
                        if elevator_a.door_is_open == True:
                            error = True
                            Logger.log("Elevator " + elevator_a_id + ": you can't begin update when door is open", output, "red")
                        if elevator_b.door_is_open == True:
                            error = True
                            Logger.log("Elevator " + elevator_b_id + ": you can't begin update when door is open", output, "red")
                    elif parts[1] == "END":
                        elevator_a.in_transfer_floor = False
                        elevator_b.in_transfer_floor = False
                        if info_time - elevator_a.update_accept_time > 6.0 + epsilon or info_time - elevator_b.update_accept_time > 6.0 + epsilon:
                            error = True
                            Logger.log("Elevator " + elevator_a_id + " and " + elevator_b_id + ": Update time between accept and end exceed 6s", output, "red")
                        if info_time - elevator_a.update_begin_time < 1.0 - epsilon or info_time - elevator_b.update_begin_time < 1.0 - epsilon:
                            error = True
                            Logger.log("Elevator " + elevator_a_id + " and " + elevator_b_id + ": Update time between begin and end less than 1s", output, "red")
                        elevator_a.last_floor = elevator_a.cur_floor
                        elevator_b.last_floor = elevator_b.cur_floor
                        elevator_a.cur_floor = intOf(elevator_a.transfer_floor) + 1
                        elevator_b.cur_floor = intOf(elevator_b.transfer_floor) - 1
                        elevator_a.limit_min_floor = elevator_a.transfer_floor
                        elevator_b.limit_max_floor = elevator_b.transfer_floor
                        elevator_a.update_begin_no_end = False
                        elevator_b.update_begin_no_end = False
                        elevator_a.has_been_updated = True
                        elevator_b.has_been_updated = True
                        elevator_a.speed = 0.2
                        elevator_b.speed = 0.2
                          
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
                # 改造期间不能开门
                if (this_elevator.update_begin_no_end == True):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't open door after update begin but not end", output, "red")
                
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
                        if (info_time - this_elevator.door_open_time_in_schedule) < 1.0 - epsilon:
                            error = True
                            Logger.log("Elevator " + elevator_id + ": close door too fast in schedule at target floor", output, "red")
                # 改造期间不能关门
                if (this_elevator.update_begin_no_end == True):
                    error = True
                    Logger.log("Elevator " + elevator_id + ": you can't close door after update begin but not end", output, "red")
                
            elif (parts[0] == "OUT"):
                flag = parts[1]
                passenger_id = parts[2]
                target_floor = parts[3]
                elevator_id = parts[4]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                this_elevator.inside_passenger_num -= 1
                this_elevator.passengers.remove(this_passenger)
                if this_elevator.in_schedule == True and this_elevator.cur_floor != this_elevator.sche_target_floor:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't out in schedule expect arrive schedule target floor", output, "red")
                if this_elevator.door_is_open == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't out when door is closed", output, "red")
                if this_elevator.update_begin_no_end == True:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't out after update begin but not end", output, "red")
                if flag == "S": 
                    average_time += (info_time - this_passenger.request_time) * this_passenger.pri
                    this_passenger.need_dispatch = False
                    this_passenger.arrive = True
                    if this_elevator.cur_floor != this_passenger.to_floor:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": passenger " + str(this_passenger.id) + " don't arrive destination but input -S", output, "red")
                elif flag == "F":
                    this_passenger.need_dispatch = True
                    if this_elevator.cur_floor == this_passenger.to_floor:
                        error = True
                        Logger.log("Elevator " + elevator_id + ": passenger " + str(this_passenger.id) + " arrive destination but input -F", output, "red")
                    
            elif parts[0] == "IN":
                passenger_id = parts[1]
                target_floor = parts[2]
                elevator_id = parts[3]
                this_elevator = elevators[int(elevator_id)]
                this_passenger = passengers[int(passenger_id)]
                this_elevator.inside_passenger_num += 1
                this_elevator.passengers.append(this_passenger)
                if this_passenger not in this_elevator.receive_outside:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in when not receive", output, "red")
                this_elevator.receive_outside_num -= 1
                this_elevator.receive_outside.remove(this_passenger)
                this_passenger.need_dispatch = False
                if this_elevator.door_is_open == False:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in when door is closed", output, "red")
                if this_elevator.in_schedule == True and this_elevator.cur_floor != this_elevator.sche_target_floor:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in when schedule", output, "red")
                if this_elevator.update_begin_no_end == True:
                    error = True
                    Logger.log("Elevator " + elevator_id + ": passenger can't in after update begin but not end", output, "red")
            
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
            error = true
            print("Error output:", stderr)
            
    except subprocess.TimeoutExpired:
        print("Process timed out! Killing process...")
        process.kill() 
    if error == True:
        return False, output
    return all_arrived, output

check, output = main()
if check == True:
    #os.remove(output)
    print(" \033[32mAccepted!\033[0m")
else:
    print(" \033[31mError occurred! \033[0m" + output)