import os
import subprocess

# 定义文件夹路径和目标 Python 脚本路径
folder_path = './testcase1'  # 替换为实际的文件夹路径
python_script = './quickInput_elevator3-2.py'  # 替换为实际的 Python 脚本文件路径

# 按照顺序生成文件名并处理文件
i = 1
while True:
    filename = f"test_{i}.txt"
    file_path = os.path.join(folder_path, filename)

    # 如果文件不存在，则停止循环
    if not os.path.exists(file_path):
        break

    # 将文件内容写入 stdin.txt
    with open(file_path, 'r') as f:
        content = f.read()

    os.remove('stdin.txt')

    # 写入新的 stdin.txt 文件
    with open('stdin.txt', 'w') as stdin_file:
        stdin_file.write(content)

    # 启动目标 Python 文件中的 main 函数
    print(f"Testing {filename}...", end=" ---> ", flush=True)
    result = subprocess.run(['python', python_script])

    # 递增索引
    i += 1

print("\033[32m\n\nAll test files processed !\033[0m")
