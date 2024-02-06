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
- [Python官网](https://www.python.org/)
- [PEP 8 – Python 代码风格指南](https://peps.python.org/pep-0008/)
- [Python2.7 datamodel](https://docs.python.org/2/reference/datamodel.html)
- [Python2.7 library](http://docs.python.org/2/library/)
- [Python3 library](https://docs.python.org/3/library/index.html)
- [Python Modules](https://wiki.python.org/moin/UsefulModules)
- [Python WebFrameworks](https://wiki.python.org/moin/WebFrameworks)
- [Python Packages](https://pypi.org/)
- [Python Excel](https://www.python-excel.org/)
- [Pyinstaller](https://pyinstaller.org/en/stable/)
- [Pygame](https://www.pygame.org/)
- [Pyglet](https://pyglet.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [SQLite](https://www.sqlite.org/index.html)

### 3、其他概念

- PEP
    - PEP表示Python增强提案(Python Enhancement Proposal)
    - PEP是一个文档，它描述了使Python能够变得更好的一种方法
    - 其中一些不会影响语言(例如样式指南)，然而有一些可能会为Python新增# 或者删除某项特性
    - 其他一些则描述了过程，例如如何提交一个PEP# 或者如何把一个已有的PEP传递给另一个开发者


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
    - python中单引号和双引号使用完全相同；使用三引号('''# 或""")可以指定一个多行字符串；转义符 '\'；
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
    - 由一个# 或数个形态各异的大小整体组成的，构成集合的事物# 或对象称作元素# 或是成员
    - 基本功能是进行成员关系测试和删除重复元素
    - 可以使用大括号 `{ }` # 或者 `set()` 函数创建集合，注意：创建一个空集合必须用 `set()` 而不是 `{ }`，因为 `{ }` 是用来创建一个空字典。
    - 如：`parame = {value01,value02,...}` # 或 `set(value)`
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

#### d、python2.7中的不同点

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

- 数据类型

    |数据类型|格式|备注|
    |:------:|:------:|:------:|
    |String|“string”|必须要用双引号|
    |Number|1或1.5|可以使用一个整数或浮点数|
    |Boolean|true或false|没有引号，没有大写|
    |Array|[“thing”, “thing”]|可以用方括号保存任何的数据类型|
    |JSON object|{“key”: value}|和Python的字典不同，这个字典必须有一个用作键的字符串|
    |Null|null|没有引号，没有大写|

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

- `try/except` 执行代码，并捕获全部# 或者特定的错误

- 字符串格式化方法

	|方　　法|描　　述|示　例|
	|:------:|:------:|:------:|
	|.upper()|把所有字母转换为大写（又名全部大写）|'HELLO WORLD'|
	|.lower()|把所有字母转换为小写|'hello world'|
	|.capitalize()|把字符串中的首字母大写，并把剩余字母转换为小写|'Hello world'|
	|.title()|把首字母以及每个空格# 或者标点符号后面的字母转换为大写。其他字母转换为小写|'Hello World'|
    |input()|函数用于收集信息|
    |raw_input()|用于收集任何非数字的信息|
    |getpass()|需要用import导入 getpass库，用来收集隐藏信息|

- 标准库
    - `random` 生成随机数的一组模块
    - `os` 专用于与操作系统交互的一个包
    - `json` 用来生成和读取JavaScript Object Notation（JSON）文件的一个包，它提供了很多方法来存储和共享数据
    - `sqlite3` 用来创建、编辑和读取SQLite数据库的一个包
    - `datetime` 用来操作日期和时间的一个包，包括获取日期的相关信息、显示这些信息以及对日期/时间做数学运算
    - `getpass` 用来获取用户敏感信息的一个包
    - `this` 一个复活节彩蛋；当键入import this时，将输出Python的信息
    - `pprint` 用来以更易于阅读的格式打印数据的一个包
    - `from module import class/function` 只导入一个函数
    - `import module` 导入整个标准库，python会查看所有包含在Python路径下的文件夹
    - `help(module)` 显示一个模块的帮助文档

- 文件
    - `open('test.txt', 'r+w')` 打开test.txt文件
    - `open('test.txt').readlines()` 把test.txt文件内容保存到一个列表中
    - `open('test.txt').writelines(lines)` 接收一个列表lines，把lines中的每一项写入到这个文件中
    - `open('test.txt').close()` 关闭test.txt文件

- `os`
    - `os.getcmd()` 获取当前目录
    - `os.listdir('/tmp')` 获取目录/tmp下的内容
    - `os.walk('/tmp')` 接受一个路径，创建一个对象
    - `os.walk('/tmp').next()` 返回一个数组，包含：目录的路径、该目录中的子目录以及该目录中的文件
    - `os.makedirs('newfolder')` 创建一个目录
    - `os.stat('test.txt')` 获取test.txt文件属性

- `random`
    - `import random`
    - `random.randint(1, 100)` 返回一个 1 到 100 之间的随机数
    - `random.random()` 返回一个 0 到 1 之间的一个随机的浮点数
    - `random.uniform(1, 5)` 返回一个 1 到 5 之间的一个随机的浮点数
    - `random.choice(list)` 接受一个列表# 或者元组，然后从中随机地返回一个项

- `time`
    - `from datetime import time`
    - `from datetime`
    - `datetime.time(11, 30)` 11:30
    - `datetime.datetime(year=2024, day=26, month=1)` 可以做加减，得到 `datetime.timedelta(xxx)` 
    - `datetime.timedelta(xxx)` 包含了以天和秒为单位的时间量

- `json`
    - `import json`
    - `json.dump()` 用来把JSON传送到一个数据流
    - `json.dumps()` 以字符串形式返回一个有效的JSON
    - `vars()` 把一个对象中所存储的所有属性返回到一个字典中

### 4、进制

- 进制前缀

	|进制前缀|进　　制|
	|:------:|:------:|
	|0b|二进制|
	|0o|八进制|
	|0x|十六进制|

- 进制对照

	|十进制|0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|
	|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
	|十六进制|0|1|2|3|4|5|6|7|8|9|A|B|C|D|E|F|
	|二进制|0000|0001|0010|0011|0100|0101|0110|0111|1000|1001|1010|1011|1100|1101|1110|1111|

- 常用数字

	|十六进制|十进制|
	|:------:|:------:|
	|0x30|48|
	|0x31|49|
	|0x41|65|
	|0x61|97|
	|0x7F|127|
	|0xFF|255|

### 5、原码、反码、补码

- 原码、反码、补码的定义

	|类　　型|定　　义|
	|:------:|:------:|
	|原码|5 => 0b101 , 1 => 0b1 , -1 => -0b1 = bin(-1)  原码表达 => 字符串(输出)|
	|反码|正数的反码与原码相同；负数的反码符号位不变其余按位取反|
	|补码|正数的补码与原码相同；负数的补码符号为不变其余按位取反后 +1|

- 正数、负数

	|类　　型|定　　义|
	|:------:|:------:|
	|正数|三码一致|
	|负数|早期数字电路的CPU中的运算器实现了加法器，但是没有减法器，减法要转换成加法；负数在计算机中使用补码存储，-1的补码为 1111 1111|

```
     # 以 -1 为例，计算 -1 的补码
     # -1 => -0b1
     # 1000 0001 原码表示
     # 1111 1110 反码表示，符号位不变
     # 1111 1111 -1在计算机内存中真实表达 同时，也要看是有符号数，还是无符号数，如 0xFF
     # 0xFF FF FF FF FF FF -1
     # 0xFF FF FF FF FF FE -2
     # 0xFE 补码的补码就是原码
     # 0x 1 111 1110 
     # 0x 1 000 0010 -2
     # 5 + (-1) = 4
     # 0000 0101
     # 1111 1111 -1 补码      1000 0001 -1原码    
     #10000 0100  4
     #.溢出位丢弃 
```

- 位运算

	|运算符|定　　义|
	|:------:|:------:|
	|& 按位与|参与运算的两个值，如果两个相应位都为1，则该位的结果为1，否则为0|
	|\| 按位# 或|只要对应的二个二进位有一个为1时，结果位就为1|
	|^ 按位异|当两对应的二进位相异时，结果为1|
	|~ 按位取反|对数据的每个二进制位取反，即把1变为0，把0变为1。~x 类似于 -x-1|

```
~12
~12 => -13 
0000 1100 +12
1111 0011 取反，'~'你问他，你是几？最高位是1 ，所以计算机认为它是负数，负数的补码，为了给人看，故转原码
1000 1101 -13

10 ^ 9 按位异# 或  #异# 或 相异出1，相同出0；同# 或 相同出1，相异出0
0000 1010 10
0000 1001 9
----
0000 0011 3

10 ^ -9
0000 1010 10
1000 1001 -9
----
1000 0011 -3
```

- 位掩码
```
1100 0011 // 去后四位
0000 1111 // 位掩码的表现: 0舍弃 1保留
```

### 6、运算符

- 比较运算符
    - `<`
    - `>`
    - 比较，注意不要把不同类型的数据放一起比较

- 位运算符(见图真值表，# 或上)

- 短路运算符
    - 与 # 或 非 
    - `and` `or` `not` (逻辑表达式) 
    - `and` 如果前面的表达式等价为 False,后面就没有必要计算了，这个逻辑表达式最终一定等价为False
    - `or`  如果前面的表达式等价为 True ,后面就没有必要计算了，这个逻辑表达式最终一定等价为 True

```
a = 3
a > 2 and a < 5 => True and True => True
a > 2 or  a < 5 => True or  True => True  # True or ？ => True 短路 ；True or+ False 、 True or+ True
```

- 赋值运算符
    - Python为动态语言，赋值即定义
    - 如果一个变量已经定义，赋值相当于重新定义	

```
a = a + 1  =>  a += 1
a = a * b  =>  a *= b
a = a % b  =>  a %= b
a = a // b  =>  a //= b
a = a + b + c  =>  a += b + c
```

- 成员运算符
    - `in`
    - `not in`

- 身份运算符
    - `is`
    - `is not`

- 优先级
    - 单目运算符 优先级 大于双目运算符
    - 算术运算符 > 比较运算符 > 逻辑运算符

- `is` 和 `==`
    - `is` 判断两个变量是否是引用同一个内存地址
    - `==` 判断两个变量是否相等

### 7、分支与循环

#### a、分支

```python
    if condition1:
    	代码块1
    elif condition2:
    	代码块2
    elif condition3：
    	代码块3
    ......
    	代码块4
    else:
    	代码块*
    # TIPS:
    #     1、condition必须是一个bool类型，这个地方有一个隐式转换bool(condition)，相当于False等价
    #     2、if语句这行最后，会有一个冒号，冒号之后如果由多条语句的代码块，需要另起一行，并缩进
    #         a、if、for、def、class、等关键词后面都可以跟代码块
    #         b、这些关键词后面，如果有一条语句，也可以跟在这一行后面。例如 if 1>2: pass
    #         c、条件为假：0, false, '', None;
    #         d、条件为真：不为 0, True, 'None', 字符串不为空串
```
    
#### b、循环

- while 语句
```python
    while cond:
    	block

    while True:  #死循环
    	pass

    a=10
    while a：     #条件满足则进入循环
    	print(a)                     #print 默认输出是换行的，如果要实现不换行需要在变量末尾加上 end=""
    	a -= 1
```

- for 语句
```python
    for element in iteratable：
    	block

    for i in range(0，10):
    	print(i)

    # 内建函数  函数签名                       说明
    # range    range(stop)                 返回惰性的对象
    #          range(start，stop[,step])   可以生成一个序列，遍历它就可以得到这个序列的一个个元素
    #                                       前包后不包
```

- else子句
```python
    如果循环正常结束，else子句会被执行
    for i in range(0):
    	pass
    else:
    	print("ok")
    
    for i in range(0,10):
    	break
    else:
    	print("ok")
    
    for i in range(0,10):
    	continue
    else:
    	print("ok")
    
    有上例可知，一般情况下，循环正常执行，只要当前循环不是被break打断的，就可以执行else子句。哪怕是range(0)也可以执行else子句。
    
    while 循环语句和 for 循环语句使用 else 的区别：
        a)、如果 else 语句和 while 循环语句一起使用，则当条件变为 False 时，则执行 else 语句。
        b)、如果 else 语句和 for 循环语句一起使用，else 语句块只在 for 循环正常终止时执行
```

- continue
```python
    # 跳过当前循环的档次循环，继续下一次循环
    for i in range(0,10):
    	if i % 2 != 0: continue
    	print(i)
    
    for i in range(0,10):
    	if i % 2 != 0: 
    		continue
    	print(i)
    
    for i in range(0,10):
    	if i & 1: continue
    	print(i)
```

- 总结
    - continue和break是循环的控制语句，只影响当前循环，包括while、for循环
    - 如果循环嵌套，continue和break也只影响语句所在的那一层循环
    - continue和break只影响循环，所以if cond：break不是跳出if，而是终止if外的break所在的循环
    - break 语句可以跳出 for 和 while 的循环体。如果你从 for # 或 while 循环中终止，任何对应的循环 else 块将不执行。
    - continue 语句被用来告诉 Python 跳过当前循环块中的剩余语句，然后继续进行下一轮循环。

#### b、练习

- 给定一个不超过5位的正整数，判断该数的位数，依次打印出万位、千位、百位、十位、个位的数字
```python
# 思路：每一趟中，整除就能获得最高位置的数，取模就能获得除去最高位的数的剩余数字，且取模后的数字作为下一趟的待处理数字
# 	c = 54321  w = 10000
# 	第一趟 out = c // w   c = c % w   w = w // 10
# 	第二趟 out = c // w   c = c % w   w = w // 10
# 	......
c = int('54321')
w = 10000
for i in range(5):
	print(c // w)
	c %=  w
	w //= 10
```

- 给定一个不超过5位的正整数，判断该数是几位数，依次从万位打印到个位的数字
```python
# 思路：用上面的程序处理，从左到右处理数据，遇到0则长度减1，遇到第一个非0数字才开始打印并不再减1
c = int('54001')  # 00451,01230
w = 10000  # 拿10000来试验
length = 5  # 假设长度为5
flag = False  # 开关量，打标记
while w：
	x = c // w
	if not flag:
		if x:  # 找到第一个非0数字，从此开始打印
			flag = True
		else:
			length -= 1
	if flag:
		prinf(x)
	c = c % w
	w //= 10
print ('The length of number is', length)
```

- 给一个半径，求圆的面积和周长。圆周率3.14
```python
r = int(input('半径=:'))
print('面积=',int(3.14*r*r))
print('周长=',int(2*3.14*r))
```

- 输入两个数，比较大小后，从小到大升序打印
```python
a = int(input('please input a number:'))
b = int(input('please input a number:'))
if a > b:
	print(b)
	print(a)
else:
	print(a)
	print(b)

# 或
print(b,a) if a>b else print(a,b)  #三元表达式：真值 if 条件 else 假值
```

- 依次输入若干个整数，打印出最大值。如果输入为空，则退出程序。
```python
a = int(input('please input a number:'))
if a == 0:   # 或if not a(a = none)
	print('不能为空，程序退出')
	exit(-1)
while a > 0:
	b = int(input('please input a number:'))
	if b == 0:
		print('不能为空，程序退出')
		exit(-1)
	elif a > b:
		print('最大值为',a)
		break
	elif b > a:
		print('最大值为',b)
		break
```

- 依次输入若干个整数，求每次输入后的算术平均数。
```python
sum = int(input('输入一个正整数:'))
count = 1

while True:
	a = input('再输入一个正整数:')
	if not a:
		print('Bye')
		break
	n = int(a)
	sum += n
	avg = sum / count
	print("Avg is "，avg)
```

- 打印一个边长为n的正方形
```python
n = int(input('please input a number:'))
print('*'*n)
for i in range(n-2):
	print('*',' '*(n-2),'*')
print('*'*n)

# 或 
for i in range(n):
	if i == 0 or i == n - 1:  # 或 if i % (n - 1) == 0:
		print('*'*n)
	else
		print('*',' '*(n - 2),'*')

# 或
for i in range(n):
	print('*'*n) if i == 0 or i == n - 1 else print('*',' '*(n - 2),'*') #三元表达式

# 或
n = int(input('please input a number:'))
a = '*'
b = '*'
for i in range(n):
	a += '\t*'
	b += '\t'
else:
	b += '*'
	c = a + '\n' + (b + '\n')*(n-1) + a
	print(c)
```

- 求100以内所有奇数的和
```python
b = 0
for i in range(100):   # 或  range(1,100,2)
	if i % 2 :         # 或  if i % 2 == 1:
	    b += i
print(i)   
print(b)
```

- 判断学生成绩,成绩等级A-E, 其中 90 以上为A, 80-89为B ,70-79为C, 60-69为D, 60以下为E
```python
a = int(input("请输入成绩:"))
if a >= 90:
    print('成绩为A')
elif a >= 80:
    print('成绩为B')
elif a >= 70:
    print('成绩为C')
elif a >= 60:
    print('成绩为D')
else:
    print('成绩为E')
```

- 求1到5阶乘之和
```python
a = 1
b = 0
c = 1
for i in range(5):
	c *= a
	b += c
	a += 1
	print(c)
print(b)
```

- 给一个数，判断它是否是素数(质数，一个大于1的自然数只能被1和它本身整除)
```python
n = int(input('please input a number:'))
for i in range(2,a):
	if (a % i) == 0:
		print('不是素数')
		break
else
	print('是素数')
```

- 打印九九乘法表
```python
for i in range(1,10):
	line = ''
	for j in range(1,i+1):
		spaces = '  ' if j == 2 and i < 5 else ' '
		line += str(j) + '*' + str(i) + '=' + str(i * j) + spaces 
	print(line)
	
for i in range(1,10):
	for j in range(1, i+1):
		print("{}*{}={:<{}}".format(j, i, i*j, 3 if j > 1 else 2), end='\n' if j == i else '')
# "{0}*{1}={2:<2}".format(a,b,a*b)  {2:<2} 第一个2为索引, :为分隔符号, <为向左对齐, 第二个2为宽度

# 右对齐
for i in range(1,10):
	line = ''
	for j in range(i, 10):
		line += "{}*{}={:<{}}".format(j, i, i*j, 2 if j < 4 else 3)
	print("{:>62}".format(line))

a=1
while a < 10:
	b=1
	while b <= a:
		c = a * b
		print("%d*%d=%d"%(a,b,c), end="  ")
		b += 1 
	a += 1
	print("")

# 原九九乘法表逆时针输出
for i in range(9,0,-1):
    for j in range (1,i):
        print("\t",end="")
    for k in range (i,10):
        print("%dx%d=%d" % (i,k,k*i), end="\t")
    print()
```

- 用户登录验证,用户错误# 或密码错误都显示用户# 或密码错误,错误3次,则退出程序,验证成功显示登录信息
```python
name = str('qwer')
ps = str(123456)
cs = 0
while True:
    n = str(input('请输入账号:'))
    p = str(input('请输入密码:'))
    if n == name and p == ps:
        print('恭喜你登录成功了!')
        break
    else:
        print('账号# 或密码错误')
        cs += 1
        if cs == 3:
            print('你已经错误3次,程序退出')
            exit(-1)
```
            
- 打印出下列图形
```python
#    *
#   ***
#  *****
# *******
#  *****
#   ***
#    *
n = 7
e = n // 2

for i in range(-e, n-e):
	prespaces = -i if i < 0 else i  
	print(' ' * prespaces, end='')
	print((n - 2 * prespaces) * '*')
	
for i in range(-e, n-e):
	print(' ' * abs(i) + (n - 2 * abs(i)) * '*')
	
for i in range(-e, n-e):
	line = (n - 2 * abs(i)) * '*'
	print("{:^{}}".format(line,n))
	
# *******
#  *****
#   ***
#    *
#   ***
#  *****
# *******
n = 7
e = n // 2

for i in range(-e, n-e):
	print((3-abs(i))*' ' + (2 * abs(i) + 1) * '*')

for i in range(-e, n-e):
	print("{:^{}}".format((2 * abs(i) + 1) * '*', n))

#    *
#   **
#  ***
# *******
#    ***
#    **
#    *
n = 7
e = n // 2
x = n - e

for i in range(-e, x):
	if i < 0:
		line = (-i) * ' ' + (x + i) * '*'
	elif i == 0:
		line = '*' * n
	elif i > 0:
		line = ' ' * e + (x - i) * '*'
	print(line)
```

- 打印出100以内的斐波那契数列
```python
a = 0
b = 1
print(a)
print(b)
while True:
	c = a + b
	if c > 100:
		break
	a = b
	b = c
	print(c)

#!/usr/bin/python3
# Fibonacci series: 斐波纳契数列
# 两个元素的总和确定了下一个数
a, b = 0, 1
while b < 1000:
    print(b, end=',')            #关键字end可以用于将结果输出到同一行，# 或者在输出的末尾添加不同的字符
    a, b = b, a+b
# 结果：1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,

# PS:
# print() sep 参数使用：
# >>> a=10;b=388;c=98
# >>> print(a,b,c,sep='@')
# 10@388@98
```

- 求斐波那契数列第101项
```python
a = 0
b = 1
print(a)
print(b)
while True:
	c = a + b
	if c > 102:
		break
	a = b
	b = c
print(c)

a = 0
b = 1
# 手动打印前两项
print('{},{}'.format(0, a))
print('{},{}'.format(1, b))
index = 1
while True:
    c = a + b
    a = b
    b = c
    index += 1
    print('{},{}'.format(index, c))
    if index == 101:
        break

import functools
@functools.lru_cache()
def fib(n,a=0,b=1):
    return 1 if n < 3 else fib(n-1) + fib(n-2)
fib(101)
#573147844013817084101
```

- 求10W以内的质数
```python
n = int(input('please input a number:'))
for i in range(2,n): # 或(2,int(n ** 0.5) + 1)
	if (n % i) == 0:
		print('不是素数')
		break
else:
	print('是素数')

n = 1
a = 3
print('质数:'1)
while True:	
	if a >= 100001:
		break
	for i in range(2,a)
		if a % i == 0:
			pass
		else
			print(a)
			n += a
	a += 1
```
			
- 计算杨辉三角前6行,并打印出来
```python
num = input('请输入行数：')
num = int(num)
list1 =[] #list 用来保存杨辉三角
for n in range(num):
	row =[1] #保存行
	list1.append(row)
 	if n == 0:
    	print(row)
    	continue
	for m in range(1,n):
		row.append(list1[n - 1][m - 1] + list1[n - 1][m])
	row.append(1)
	print(row)
```

- a = 60 其二进制值为0b00111100
```python
n = 0 #用于计数
while a: #用移位方法求解，直到a移位为0为止
    if a & 1 == 1:
        n += 1 #将a与1进行位与操作，即可知道a的最后1位是否为1，若为1，则计数n增1，不然则无需变化n的值
    a >>= 1 #测试了a的最后一位后，将最后一位右移移除，重新赋值给a
print(n) #打印最后的计数数据
```

- 彩票游戏
```python
import random

t1="开始游戏"
t2="结束游戏"
print(t1.center(50,"*"))
data1=[]
money=int(input("输入投入的金额："))
print("你现在余额为：%d元"%money)
while 1:
    for i in range(6):
        n = random.choice([0, 1])
        data1.append(n)
    if money<2:
        print("你的余额不足，请充值")
        m=input("输入投入的金额：")
        if int(m)==0:
            break
        else:
            money=int(m)
    while 1:
        j=int(input("输入购买彩票数量"))
        if money-j*2<0:
            print("购买后余额不足，请重新输入")
        else:
            money = money - j * 2
            print("你现在余额为：%d元" % money)
            break
    print("提示：中奖数据有六位数，每位数为0# 或者1")
    n2=input("请猜测中奖数据：(输入的数字为0# 或1)")
    print(str(data1))
    f=[]
    for x in n2:
        f.append(x)
    f1 = str(f)
    f2 = f1.split("'")
    f3 = "".join(f2)
    print("你猜测的数据为：", f3)
    if f3==str(data1):
        print("中奖数字为：",data1)
        print("恭喜你中大奖啦")
        money=money+j*100
        print("你现在余额为：%d元" % money)
    else:
        print("中奖数字为：", data1)
        print("没有中奖，请继续加油")
    con = input("请问还要继续么？结束请输入no,继续请任意输入字符：")
    if con=="no":
        break
    data1=[]
print(t2.center(50,"*"))
print("你的余额为：%d元"%money)
```

- 生成直观的九连环解法：
```python
#!/usr/bin/python
x = ["-θ","-θ","-θ","-θ","-θ","-θ","-θ","-θ","-θ"]
y = ["—","—","—","—","—","—","—","—","—"]
def down(n, l): #拆解
    v = len(l) #计算数列个数用于改变数列对应位置
    if n>2:
        down(n-2, l) #拆下n-2的环
        l[v-n] = "—" #将v-n位"-θ"改为"—" 表示拆下
        for x in l:  #输出列表每一个元素
            print(x,end=' ')
        print() #换行
        up(n-2, l) #装上n-2位
        down(n-1, l)#拆下n-1位， 后面同理
    if n==2:
        l[v-2], l[v-1] ="—","—"
        for x in l:
            print(x,end=' ')
        print()
    if n<2:
        l[v-1] = "—"
        for x in l:
            print(x,end=' ')
        print()
def up(n, l):
    v = len(l)
    if n>2:
        up(n-1, l)
        down(n-2, l)
        l[v-n] = "-θ"
        for x in l:
            print(x,end=' ')
        print()
        up(n-2, l)
    if n==2:
        l[v-2], l[v-1] = "-θ","-θ"
        for x in l:
            print(x,end=' ')
        print()
    if n<2:
        l[v-1] ="-θ"
        for x in l:
            print(x,end=' ')
        print()
print("拆解\n")
for i in x:
    print(i,end=' ')
print()
down(9, x)
print('---------------------------------\n','装上\n')
for i in y:
    print(i,end=' ')
print()
up(9, y)
print("结束")

# 九连环拆解，递归算法
def down(n):
    if n>2:
        down(n-2)
        print('卸下',n,'环')
        up(n-2)
        down(n-1)
    if n==2:
        print('卸下 {},{} 环'.format(n,n-1))    
    if n<2:
        print('卸下',n,'环') 
        
def up(n):
    if n>2:
        up(n-1)
        down(n-2)
        print("装上",n,"环")
        up(n-2)
    if n==2:
        print("装上 %d,%d 环" % (n,n-1))
        
    if n<2:
        print("装上",n,"环")
print("拆解")
down(2)
print('---------------------------------\n','装上')
up(3)
print("结束")
```

### 8、函数

- 定义一个函数
    - 函数代码块以 `def` 关键词开头，后接函数标识符名称和圆括号 ()。
    - 任何传入参数和自变量必须放在圆括号中间，圆括号之间可以用于定义参数。
    - 函数的第一行语句可以选择性地使用文档字符串—用于存放函数说明。
    - 函数内容以冒号起始，并且缩进。

```python
def 函数名(参数列表):
    函数体
    return [表达式]        #结束函数，选择性地返回一个值给调用方。不带表达式的return相当于返回 None。
```

- 参数，以下是调用函数时可使用的正式参数类型：
    - 必需参数
    - 关键字参数
    - 默认参数    # 默认参数不在最后，会报错
    - 不定长参数
        - def(**kwargs) 把N个关键字参数转化为字典

- 变量作用域
    - 对于变量作用域，变量的访问以 L(Local) –> E(Enclosing) –> G(Global) –>B(Built-in) 的规则查找，即：在局部找不到，便会去局部外的局部找(例如闭包)，再找不到就会去全局找，再者去内建中找。
    - 内部函数，不修改全局变量可以访问全局变量；
    - 修改同名全局变量，则python会认为它是一个局部变量；
    - 在内部函数修改同名全局变量之前调用变量名称(如print sum)，则引发Unbound-LocalError

- 装饰器
    - 装饰器的作用就是为已经存在的对象添加额外的功能。
    - [Python 函数装饰器](https://www.runoob.com/w3cnote/python-func-decorators.html)

- 数字处理函数
    - `round()` 四舍六入取偶；4舍6入5看齐,奇进偶不进
    - `floor()` 向下取整；
    - `ceil()` 向上取整；
    - `int()` 取整数部分；
    - `min()`
    - `max()`
    - `pow(x,y)`    等于x**y
    - `math.sqrt()` 等于x**0.5

- 进制函数
    - 返回值是字符串
	- `bin()`
	- `oct()`
	- `hex()`
    - `math.pi` Π
    - `math.e` 自如常数    #math模块中还有对数函数、三角函数等

- 类型判断
    - `type(obj)`  返回类型，而不是字符串
    - `isinstance(obj,class_or_tuple)`  返回布尔值  
    - 区别
        - type 是用于求一个未知数据类型对象，而 isinstance 是用于判断一个对象是否是已知类型;
        - type 不认为子类是父类的一种类型，而 isinstance 会认为子类是父类的一种类型;
        - 可以用 isinstance 判断子类对象是否继承于父类，type 不行。

### 9、迭代器与生成器

- 迭代器有两个基本的方法：`iter()` 和 `next()`
    - 使用了 yield 的函数被称为生成器(generator)
        - 加了yield的函数，每次执行到有yield的时候，会返回yield后面的值 并且函数会暂停，直到下次调用# 或迭代终止；
        - 在一个 generator function 中，如果没有 return，则默认执行至函数完毕，如果在执行过程中 return，则直接抛出 StopIteration 终止迭代。
    - [Python3 迭代器与生成器](https://www.runoob.com/python3/python3-iterator-generator.html)
    - [Python yield 使用浅析](https://www.runoob.com/w3cnote/python-yield-used-analysis.html)

- 迭代、迭代器、生成器三个概念的联系和区别
    - 可迭代概念范围最大，生成器和迭代器肯定都可迭代，但可迭代不一定都是迭代器和生成器，比如上面说到的内置集合类数据类型。可以认为，在 Python 中，只要有集合特性的，都可迭代。
    - 迭代器，迭代器特点是，均可以使用 for in 和 next 逐一遍历。
    - 生成器，生成器一定是迭代器，也一定可迭代。


### 10、pickle 模块

- `pickle` 模块实现了基本的数据序列和反序列化
    - 通过 `pickle` 模块的序列化操作，可以将程序中运行的对象信息保存到文件中去，永久存储
    - 通过 `pickle` 模块的反序列化操作，可以将从文件中创建上一次程序保存的对象

- 基本接口
    - `pickle.dump(obj, file, [,protocol])`
    - 有了 pickle 这个对象，就能对 file 以读取的形式打开: `x = pickle.load(file)`
    - 注解：从 file 中读取一个字符串，并将它重构为原来的python对象
    - file: 类文件对象，有 `read()` 和 `readline()` 接口

- 例1
```python
#!/usr/bin/python3
import pickle

# 使用pickle模块将数据对象保存到文件
data1 = {'a': [1, 2.0, 3, 4+6j],
         'b': ('string', u'Unicode string'),
         'c': None}

selfref_list = [1, 2, 3]
selfref_list.append(selfref_list)

output = open('data.pkl', 'wb')

# Pickle dictionary using protocol 0.
pickle.dump(data1, output)

# Pickle the list using the highest protocol available.
pickle.dump(selfref_list, output, -1)

output.close()
```

- 例2
```python
#!/usr/bin/python3
import pprint, pickle

#使用pickle模块从文件中重构python对象
pkl_file = open('data.pkl', 'rb')

data1 = pickle.load(pkl_file)
pprint.pprint(data1)

data2 = pickle.load(pkl_file)
pprint.pprint(data2)

pkl_file.close()

- 例3 通过 pickle 序列化实现一个简单联系人信息管理
```python
import pickle
import os

datafile = 'person.data'
line = '======================================='
message = '''
=======================================
Welcome bookmark:
    press 1 to show list
    press 2 to add pepole
    press 3 to edit pepole
    press 4 to delete pepole
    press 5 to search pepole
    press 6 to show menu
    press 0 to quit
=======================================
'''
print(message)

class Person(object):
    """通讯录联系人"""
    def __init__(self, name, number):
        self.name = name
        self.number = number

# 获取数据
def get_data(filename=datafile):
    # 文件存在且不为空
    if os.path.exists(filename) and os.path.getsize(filename):
        with open(filename,'rb') as f:
            return pickle.load(f)
    return None
        
# 写入数据
def set_data(name, number, filename=datafile):

    personList = {} if get_data() == None else get_data()

    with open(filename,'wb') as f:
        personList[name] = Person(name,number)
        pickle.dump(personList,f)

# 保存字典格式的数据到文件
def save_data(dictPerson, filename=datafile):
    with open(filename,'wb') as f:
        pickle.dump(dictPerson,f)

# 显示所有联系人
def show_all():
    personList = get_data()
    if personList:
        for v in personList.values():
            print(v.name,v.number)
        print(line)
    else:
        print('not yet person,please add person')
        print(line)

# 添加联系人
def add_person(name,number):
    set_data(name,number)
    print('success add person')
    print(line)

# 编辑联系人
def edit_person(name,number):
    personList = get_data()
    if personList:
        personList[name] = Person(name,number)
        save_data(personList)
        print('success edit person')
        print(line)

# 删除联系人
def delete_person(name):
    personList = get_data()
    if personList:
        if name in personList:
            del personList[name]
            save_data(personList)
            print('success delete person')
        else:
            print(name,' is not exists in dict')
        print(line)

# 搜索联系人
def search_person(name):
    personList = get_data()
    if personList:
        if name in personList.keys():
            print(personList.get(name).name, personList.get(name).number)
        else:
            print('No this person of ',name)
        print(line)
        
while True:
    num = input('>>')

    if num == '1':
        print('show all personList:')
        show_all()
    elif num == '2':
        print('add person:')    
        name = input('input name>>')
        number = input('input number>>')
        add_person(name,number)
    elif num == '3':
        print('edit person:')
        name = input('input name>>')
        number = input('input number>>')
        edit_person(name,number)
    elif num == '4':
        print('delete person:')
        name = input('input name>>')
        delete_person(name)
    elif num == '5':
        print('search :')
        name = input('input name>>')
        search_person(name)
    elif num == '6':
        print(message)
    elif num == '0':
        break
    else:
        print('input error, please retry')
```

- 例4 文本中替换字符串
```python
"""replace strings in text"""

import os

def Replace(file_name, rep_word, new_word):
    with open(file_name) as f:
        content = []
        count = 0

        for eachline in f:
            if rep_word in eachline:
                count += eachline.count(rep_word)
                eachline = eachline.replace(rep_word, new_word)
            content.append(eachline)

        decide = input('文件 {0} 中共有{1}个【{2}】\n您确定要把所有的【{3}】替换为【{4}】吗？\n【YES/NO】：'.format\
                (file_name, count, rep_word, rep_word, new_word))

        if decide in ['YES', 'Yes', 'yes']:
            with open(file_name, 'w') as f:
                f.writelines(content)
            print('Succeed!')
        else:
            print('Exit!')

if __name__ == '__main__':
    while True:
        file_name = input('请输入文件名：')

        if file_name in os.listdir():
            rep_word = input('请输入需要替换的单词# 或字符：')
            new_word = input('请输入新的单词# 或字符：')
            Replace(file_name, rep_word, new_word)
            break
        else:
            print('Do not find such a file {}'.format(file_name))
```

### 11、格式化输出

#### a、整数的输出

- 格式化符号格式说明备注
    - `%o` 八进制 oct
    - `%d` 十进制 dec
    - `%x` 十六进制 hex

举个栗子
```python
print('%o' % 20) # 八进制24
print('%d' % 20) # 十进制20
print('%x' % 24) # 十六进制18
```

#### b、浮点数输出

- 格式化符号说明备注
    - `%f` 保留小数点后面六位有效数字 float
    - `%e` 保留小数点后面六位有效数字
    - `%g` 在保证六位有效数字的前提下，使用小数方式，否则使用科学计数法

```python
print('%f' % 1.11)         # 默认保留6位小数1.110000
print('%.1f' % 1.11)       # 取1位小数1.1
print('%e' % 1.11)         # 默认6位小数，用科学计数法1.110000e+00
print('%.3e' % 1.11)       # 取3位小数，用科学计数法1.110e+00
print('%g' % 1111.1111)    # 默认6位有效数字1111.11
print('%.7g' % 1111.1111)  # 取7位有效数字1111.111
print('%.2g' % 1111.1111)  # 取2位有效数字，自动转换为科学计数法1.1e+03
```

#### c、字符串输出

- 格式化符号说明备注 
    - `%s` 字符串输出 string
    - `%10s` 右对齐，占位符 10 位
    - `%-10s` 左对齐，占位符 10 位
    - `%.2s` 截取 2 位字符串 
    - `%10.2s` 10 位占位符，截取两位字符串

```python
print('%s' % 'hello world')       # 字符串输出hello world
print('%20s' % 'hello world')     # 右对齐，取20位，不够则补位         hello world
print('%-20s' % 'hello world')    # 左对齐，取20位，不够则补位hello world         
print('%.2s' % 'hello world')     # 取2位he
print('%10.2s' % 'hello world')   # 右对齐，取2位        he
print('%-10.2s' % 'hello world')  # 左对齐，取2位he

start = datetime.datetime.now()
delta = (datetime.datetime.now() - start).total_seconds()
print(delta)

#判断当前系统是否为 Linux，如果不满足条件则直接触发异常
import sys
assert ('linux' in sys.platform), "该代码只能在 Linux 下执行"
```