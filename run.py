import subprocess
import datetime
import sympy as sp
from sympy import sympify, SympifyError


# 指定多个JAR包的路径
jar_files = [
    "1.jar",
    "2.jar",
    "3.jar",
    "4.jar",
    "5.jar",
    "6.jar",
    "hw_3.jar",
    "8.jar"
]

# 指定输入文件和输出文件
input_file = "input.txt"
output_file = "output.txt"

# 读取输入文件
def read_input_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"输入文件 {file_path} 未找到！")
        return None

# 运行JAR包并获取输出
def run_jar(jar_path, input_data):
    try:
        # 直接传入字符串作为输入数据
        result = subprocess.run(
            ["java", "-jar", jar_path],
            input=input_data,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # e.stderr 已经是字符串，无需解码
        return f"运行 {jar_path} 时出错: {e.stderr}"
    except Exception as e:
        return f"运行 {jar_path} 时发生错误: {str(e)}"

# 将结果写入输出文件
def write_output_file(file_path, content):
    try:
        with open(file_path, 'a') as file:  # 使用追加模式写入
            file.write(content)
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

# 主函数
def main():
    input_data = read_input_file(input_file)
    if input_data is None:
        return

    # 获取当前时间用于输出文件的记录
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_header = f"=============== {current_time} ===============\n"

    # 写入输出文件头部信息
    write_output_file(output_file, output_header)

    # 运行每个JAR包并收集输出
    all_outputs = []
    all_exprs = []
    for jar in jar_files:
        output = run_jar(jar, input_data)
        all_outputs.append(output)
        # 使用sympy库进行对拍比较
        try:
            expr = sympify(output)
            all_exprs.append(expr)
        except SympifyError:
            all_exprs.append(None)
            print(f"无法解析 {jar} 的输出为表达式: {output}")
        # 将每个JAR的输出写入文件
        write_output_file(output_file, f"JAR: {jar}\n{output}\n")

    # 将所有输出合并并打印到终端
    combined_output = "\n".join(all_outputs)
    print(combined_output)
    # 调用detail_cmp.py进行对拍
    if all_exprs.count(None) == 0:  # 确保所有表达式都成功解析
        for i in range(len(all_exprs)):
            for j in range(i + 1, len(all_exprs)):
                if sp.simplify(all_exprs[i] - all_exprs[j]) == 0:
                    print(f"表达式 {jar_files[i]} 和 {jar_files[j]} 等值")
                else:
                    print(f"表达式 {jar_files[i]} 和 {jar_files[j]} 不等值")
    else:
        print("存在无法解析的表达式，无法进行对拍比较")

    # 写入输出文件尾部信息
    output_footer = "========================================\n\n"
    write_output_file(output_file, output_footer)

if __name__ == "__main__":
    main()
