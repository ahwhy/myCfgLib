# Python笔记

## 一、前置准备

### 1、Linux环境准备
```shell
# 利用alternatives切换不同环境
# https://segmentfault.com/a/1190000040473419?sort=newest
$ alternatives --config --list

# 安装和调用 python3
# pip源 https://mirrors.tuna.tsinghua.edu.cn/help/pypi/
$ python -V
$ pip -V
$ pip install jupyter
$ ipython
$ jupyter notebook

# 文件开头
#! /usr/bin/env python3

# 创建vcmdb的虚拟环境
$ pip3 install virtualenv
$ virtualenv -p /var/bin/python3.6 vcmdb

# 进入vcmdb的python环境
$ . ./vcmdb/bin/activate
$ python -V
# 退出
$ deactivate
```

### 2、相关文档
- [python官网](https://www.python.org/)
- [PEP 8 – Python 代码风格指南](https://peps.python.org/pep-0008/)
- [Python2.7 datamodel](https://docs.python.org/2/reference/datamodel.html)

### 3、其他概念

- PEP
    - PEP表示Python增强提案(Python Enhancement Proposal)
    - PEP是一个文档，它描述了使Python能够变得更好的一种方法
    - 其中一些不会影响语言(例如样式指南)，然而有一些可能会为Python新增或者删除某项特性
    - 其他一些则描述了过程，例如如何提交一个PEP或者如何把一个已有的PEP传递给另一个开发者



## 二、基础知识

### 1、语言类型
- 语言类型
    - 静态语言，标识符定义后不可以更改，如：go，java
    - 动态语言，标识符定义后可以更改 ，如：python，javascript
    - 强类型语言，不同类型直接不可以进行操作，如：python 
    - 弱类型语言，如：javascript，`"a" + 1 = a1`

### 2、计算机组成
    输入设备 → 存储器 → 输出设备
              ||   |
     CPU:  运算器  控制器 

- CPU：包含 寄存器 和 多级缓存 cache

- 缓存命中：始端用户访问加速节点时，如果该节点有缓存住了要被访问的数据时就叫做命中，如果没有的话需要回原服务器取，就是没有命中。取数据的过程与用户访问是同步进行的，所以即使是重新取的新数据，用户也不会感觉到有延时。 命中率=命中数/(命中数+没有命中数)， 缓存命中率是判断加速效果好坏的重要因素之一

- 晶体振荡器：有一些电子设备需要频率高度稳定的交流信号，而LC振荡器稳定性较差，频率容易漂移(即产生的交流信号频率容易变化)。在振荡器中采用一个特殊的元件——石英晶体，可以产生高度稳定的信号，这种采用石英晶体的振荡器称为晶体振荡器。

- 南北桥：靠近CPU的为北桥芯片，主要负责控制AGP显卡、内存与CPU之间的数据交换；靠近PCI槽的为南桥芯片，主要负责软驱、硬盘、键盘以及附加卡的数据交换。

### 3、数据类型

#### a、数值型
- 整型 int
    - 如 1

- 浮点型 float
    - 如 1.23、3E-2

- 复数 complex
    - 如 1 + 2j、1.1 + 2.2j

- 布尔型 bool
    - 非0 即为真，如 True 比较运算符返回值    
    - 在数值上下文环境中，True 被当作 1，False 被当作 0
    - 其他类型值转换 bool值时，除了 ''、""、''''''、""""""、0、()、[]、{}、None、0.0、0L、0.0+0.0j、False 为 False 外，其他都为 True

#### b、序列  sequence
- 字符串 str
    - python中单引号和双引号使用完全相同；使用三引号('''或""")可以指定一个多行字符串；转义符 '\'；
    - 反斜杠可以用来转义，使用r可以让反斜杠不发生转义，如 `r"this is a line with \n"` 则\n会显示，并不是换行；
    - 字符串可以用 `+` 运算符连接在一起，用 `* 运算符重复；
    - Python 中的字符串有两种索引方式，从左往右以 0 开始，从右往左以 -1 开始
    - Python中的字符串不能改变；
    - Python 没有单独的字符类型，一个字符就是长度为 1 的字符串；
    - 字符串的截取的语法格式如下：变量[头下标:尾下标:步长]
    - 字节序列 bytes 
    - 字节序列(可变) bytearray

- 列表 list
    - 变量[头下标:尾下标]，如：`list = [ 'abcd', 786 , 2.23, 'runoob', 70.2 ]`；
    - 索引值以 0 为开始值，-1 为从末尾的开始位置；
    - 与Python字符串不一样的是，列表中的元素是可以改变的；
    - 列表list、链表Linked List、栈stack、队列queue

- 元组 tuple
    - 元组(tuple)与列表类似，不同之处在于元组的元素不能修改
    - 元组写在小括号 () 里，元素之间用逗号隔开
    - 如：`tuple = ( 'abcd', 786 , 2.23, 'runoob', 70.2 )`

- 区别
    - 列表可以修改，而字符串和元组不能；
    - 列表推导式书写形式
        - 如果希望表达式推导出一个元组，就必须使用括号
        - `[表达式 for 变量 in 列表]`
        - `[表达式 for 变量 in 列表 if 条件]`
        - `[3*x for x in vec if x > 3]` 
        - [12, 18]

#### c、键值对  
- 集合 set
    - 由一个或数个形态各异的大小整体组成的，构成集合的事物或对象称作元素或是成员
    - 基本功能是进行成员关系测试和删除重复元素
    - 可以使用大括号 `{ }` 或者 `set()` 函数创建集合，注意：创建一个空集合必须用 `set()` 而不是 `{ }`，因为 `{ }` 是用来创建一个空字典。
    - 如：`parame = {value01,value02,...}` 或 `set(value)`
    - 集合推导式(Set comprehension)
        - `[ 表达式 for 变量 in 列表 if 条件  a = {x for x in 'abracadabra' if x not in 'abc'} ]` 类似列表推导式

- 字典 dict 
    - (key-value) 列表是有序的对象集合，字典是无序的对象集合
    - 两者之间的区别，字典当中的元素是通过键来存取的，而不是通过偏移存取
    - 字典是一种映射类型，字典用 `{ }` 标识，它是一个无序的 键(key) : 值(value) 的集合。键(key)必须使用不可变类型
    - 在同一个字典中，键(key)必须是唯一的。如：`dict([('Runoob', 1), ('Google', 2), ('Taobao', 3)])`、`{x: x**2 for x in (2, 4, 6)}`、`dict(Runoob=1, Google=2, Taobao=3)`
    - 字典推导式 `{key:value for variable in iterable [if expression]}`
        - 执行步骤
        - 1、for 循环：遍历可迭代对象，将其值赋给变量。
        - 2、if 语句：筛选满足 if 条件的结果。
        - 3、存储结构：以键值对的方式存储在字典中。

- 区别
    - 列表和元组不会把相同的值合并，但是集合会把相同的合并
    - 无序：集合是无序的，所以不支持索引；字典同样也是无序的，但由于其元素是由键(key)和值(value)两个属性组成的键值对，可以通过键(key)来进行索引
    - 元素唯一性：集合是无重复元素的序列，会自动去除重复元素；字典因为其key唯一性，所以也不会出现相同元素。

- 不可变数据(3个):Number(数字)、String(字符串)、Tuple(元组)
- 可变数据(3个):List(列表)、Dictionary(字典)、Set(集合)

#### d、python2.7中的基本数据类型

- 基本数据类型

	|数据类型|存储内容|示　例|
	|:------:|:------:|:------:|
    |integer (int)|整数|1, 3, -6, 1000, 5967|
    |float|浮点数，也叫做小数|3.14, 1.5, -2.8, 5.0|
    |long|非常大的数字|10000000000000005|
    |string|存储字母、数字、空格和符号| "Hello", "^", " ", "42"|
    |list|用方括号括住的一组项，并且项之间用逗号分隔|[1, 2, 4], [], ["Nevada", "California"], ["hello", 5]|
    |tuple|用圆括号括住的项的列表，这些项不能改变。通常，tuple保存的值全部都是相关的，例如人的生日、喜欢的颜色和名字| (1, 2, 4), (), ("Nevada", "California"), ("hello", 5)|
    |dictionary |已经配对的键和值的列表，用花括号括住|{'apple': 'red', 'sky': 'blue', 'dirt': 'brown'}|

-  为假的数据类型的值

	|数据类型| 值 |
	|:------:|:------:|
	|integer|0|
	|float|0.0|
	|long|0|
	|string|""|
	|list|[]|
	|dictionary|{}|
	|tuple|()|

- `try/except` 执行代码，并捕获全部或者特定的错误

- 字符串格式化方法

	|方　　法|描　　述|示　例|
	|:------:|:------:|:------:|
	|.upper()|把所有字母转换为大写（又名全部大写）|'HELLO WORLD'|
	|.lower()|把所有字母转换为小写|'hello world'|
	|.capitalize()|把字符串中的首字母大写，并把剩余字母转换为小写|'Hello world'|
	|.title()|把首字母以及每个空格或者标点符号后面的字母转换为大写。其他字母转换为小写|'Hello World'|
    |input()|函数用于收集信息|
    |raw_input()|用于收集任何非数字的信息|
    |getpass()|需要用import导入 getpass库，用来收集隐藏信息|


### 4、进制
0b 二进制
0o 八进制
0x 十六进制
0x30 48
0x31 49
0x41 65
0x61 97
0x7F 127
0xFF 255
十六进制   0     1     2     3     4     5     6     7     8     9     A     B     C     D     E     F 
二进制   0000  0001  0010  0011  0100  0101  0110  0111  1000  1001  1010  1011  1100  1101  1110  1111 
十进制     0     1     2     3     4     5     6     7    8     9     10    11    12    13    14    15 