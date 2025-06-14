# 电梯调度评测机

这是一个用于测试电梯调度算法的评测系统。该系统支持多种测试模式，包括单用例测试、批量测试和并行测试。
正确性校验部分(quickInput_elevator2_refactor.py)来自于@[Accepted0424](https://github.com/Accepted0424), 我负责测试用例构造和并行测试

## 文件结构

```
.
├── src/                    # 源代码目录
├── test/                   # 测试相关文件
│   ├── testcase/          # 测试用例目录
│   ├── quickInput_elevator2_refactor.py    # 单用例测试脚本
│   ├── quickInput_elevator2_parallel.py    # 并行测试脚本
│   ├── autoTest.py        # 批量测试脚本
│   ├── ParallelTest.py    # 并行测试主脚本
│   └── dataMaker.py       # 测试用例生成器
│   └── stdin.txt          # 标准输入重定向
```

## 使用说明

### 1. 单用例测试

* 用于测试单个测试用例：
```bash
python quickInput_elevator2_refactor.py
```
  * 代码L11可以选择是否将输出打印到终端，input_to_terminal = True
  * 错误信息将记录在`output_error.txt`中
### 2. 批量测试

* 用于测试testcase目录下的所有测试用例：

```bash
python autoTest.py
```
* 该脚本会自动测试testcase/下的所有用例
### 3. 并行测试

* 使用多线程并行测试多个用例：

```bash
python ParallelTest.py
```
* 该脚本会在Parallelism/下生成多个工作目录，然后多线程并行运行，只将最后的正确与否返回到主程序打印
* 可以在quickInput_elevator2_parallel 的L146修改源文件路径（默认src）, L169修改log目录
### 4. 生成测试用例

生成新的测试用例：

```bash
python dataMaker.py
```

## 配置说明

确保以下文件存在：
   - `elevator2.jar`
   - `datainput_student_win64.exe`（Windows）或 `datainput_student_darwin_m1`（macOS）

## 批量测试

- 测试结果将保存在`log`目录下
- **成功通过的测试用例的日志文件会被自动删除**

## 注意事项

1. 确保Java源代码路径配置正确
2. 确保所有依赖文件都在正确的位置
3. 并行测试时注意系统资源占用
4. 测试用例生成器可以根据需要调整参数 
