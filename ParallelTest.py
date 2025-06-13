import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import json

# 配置参数
folder_path = './testcase'
python_script = './quickInput_elevator2_parallel.py'
mode = 'windows'
num_workers = 15

def setup_worker_dirs():
    parallelism_dir = './Parallelism'
    os.makedirs(parallelism_dir, exist_ok=True)
    for i in range(1, num_workers + 1):
        worker_dir = os.path.join(parallelism_dir, f'worker_{i}')
        os.makedirs(worker_dir, exist_ok=True)
        if mode == 'windows':
            shutil.copy('./datainput_student_win64.exe', worker_dir)
        elif mode == 'mac':
            shutil.copy('./datainput_student_darwin_m1', worker_dir)
        shutil.copy('./code.jar', worker_dir)
        shutil.copy('./elevator2.jar', worker_dir)
        shutil.copy(python_script, worker_dir)

def run_test_in_worker(worker_id, test_files):
    worker_dir = os.path.join('./Parallelism', f'worker_{worker_id}')
    
    for test_file in test_files:
        shutil.copy(test_file, os.path.join(worker_dir, 'stdin.txt'))
        
        #print("worker-" + str(worker_id) + " is running " + test_file)
        # 运行子程序并捕获输出
        result = subprocess.run(['python', os.path.basename(python_script), str(worker_id)],
                                cwd=worker_dir, capture_output=True, text=True)
        
        # 解析子程序返回的 JSON 结果
        try:
            result_dict = json.loads(result.stdout)
        except json.JSONDecodeError:
            result_dict = {
                "worker_id": str(worker_id),
                "success": False,
                "log_file": "unknown"
            }
        result_dict["test_file"] = os.path.basename(test_file)
        
        # 实时打印结果
        worker_id = result_dict["worker_id"]
        test_file = result_dict["test_file"]
        if result_dict["success"]:
            print(f"Worker-{worker_id}-{test_file}: \033[32mAccepted!\033[0m")
        else:
            print(f"\nWorker-{worker_id}-{test_file}: \033[31mError occurred!\033[0m")
            print(f"Log file: {result_dict['log_file']}\n")
            # 将错误信息写入 output_error 文件
            with open("output_error.txt", "a") as error_file:  # 使用 "a" 模式追加写入
                error_file.write(f"Error occured in test_file and Log file: {result_dict['log_file']}\n")

def main():
    setup_worker_dirs()
    test_files = [os.path.join(folder_path, f"test_{i}.txt") for i in range(1, 4001)]
    test_files = [f for f in test_files if os.path.exists(f)]
    
    chunk_size = len(test_files) // num_workers
    worker_test_files = [test_files[i*chunk_size:(i+1)*chunk_size] for i in range(num_workers)]
    if len(test_files) % num_workers != 0:
        worker_test_files[-1].extend(test_files[num_workers*chunk_size:])
    
    # 并行运行 worker，不收集结果
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for i in range(num_workers):
            executor.submit(run_test_in_worker, i+1, worker_test_files[i])
    
    print("\033[32m\n\n所有测试文件处理完成！\033[0m")

if __name__ == "__main__":
    main()