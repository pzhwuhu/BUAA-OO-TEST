## 使用说明

请按照最新的设置内容填写config信息，其中必填项为jar_path

## config说明：

### 测试相关
- test_num：测试样例数（本次设置为 5000）
- basic_command_num：基础指令数（本次设置为 1000）
- jar_path：jar包的路径（本次设置为 m.jar）
- del_temp_file：是否删除正确样例（本次设置为 true）

### 数据生成相关
- begin_date：最早起始日期（本次设置为 2025-1-1）  
- end_date：最晚结束日期（本次设置为 2025-3-30）  
- max_num_of_days_with_command：拥有基础指令天数的最大值（本次设置为 30）  
- max_num_of_book_identifier：每个类别书的标识符数目最大值（本次设置为 10）  
- max_num_of_book_for_each_identifier：每种书的最大数目（本次设置为 5）  
- max_num_of_person：人数最大值（本次设置为 10）

#### 指令概率设置
- borrow_prob：生成借书指令的概率（0.3）  
- query_prob：生成查询指令的概率（0.2）  
- order_prob：生成预约指令的概率（0.2）  
- read_prob：生成阅读指令的概率（0.3）  
- return_prob：对于每个成功的借书，生成归还指令的概率（0.9）  
- restore_prob：对于每个成功的预约，生成恢复指令的概率（0.4）  
- pick_1_prob：对于每个成功的预约，生成1个pick指令的概率（0.5）  
- pick_2_prob：对于每个成功的预约，生成2个pick指令的概率（0.5）

### 单文件检验
- input_file：输入文件路径（本次设置为 input.txt）  
- output_file：输出文件路径（本次设置为 output.txt）

## 数据生成逻辑
1. 在指定天数范围内随机生成基础指令（包括 query, borrow, order, read）。
2. 对于成功的特定基础指令，按概率生成后续指令：  
    - 对成功的borrow生成return指令（在当前天数与截止天数间随机生成）。  
    - 对成功的order生成pick指令（在当前天数与(当前天数+12)间随机生成）以及生成restore指令。

## 注意
为保证数据强度，建议不要将时间范围、max_num_of_book_identifier、max_num_of_book_for_each_identifier、max_num_of_person设置过大；  
同时，max_num_of_days_with_command需大于begin_date和end_date的差值。
