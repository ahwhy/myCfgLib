# Linux常用工具简介

## 一、Linux常用网络工具

### 1、ping

ping，用于探测两个主机间连通性以及响应速度，用法为：“ping 参数 目标主机”。其中参数为零到多个，目标主机可以是IP或者域名。

```
Usage: ping [-aAbBdDfhLnOqrRUvV] [-c count] [-i interval] [-I interface]
        [-m mark] [-M pmtudisc_option] [-l preload] [-p pattern] [-Q tos]
        [-s packetsize] [-S sndbuf] [-t ttl] [-T timestamp_option]
        [-w deadline] [-W timeout] [hop1 ...] destination
```

**PS:** 在ping过程中按下`ctrl+|`会打印出当前的summary信息，统计当前发送包数量、接收数量、丢包率等。

参数详解：

|        参数         |                             详解                             |
| :-----------------: | :----------------------------------------------------------: |
|         -a          |                        Audible ping.                         |
|         -A          |        自适应ping，根据ping包往返时间确定ping的速度；        |
|         -b          |                    允许ping一个广播地址；                    |
|         -B          |                 不允许ping改变包头的源地址；                 |
|    **-c count**     |                   ping指定次数后停止ping；                   |
|         -d          |                  使用Socket的SO_DEBUG功能；                  |
|    -F flow_label    | 为ping回显请求分配一个20位的“flow label”，如果未设置，内核会为ping随机分配； |
|       **-f**        |  极限检测，快速连续ping一台主机，ping的速度达到100次每秒；   |
|     -i interval     |        设定间隔几秒发送一个ping包，默认一秒ping一次；        |
|  **-I interface**   |          指定网卡接口、或指定的本机地址送出数据包；          |
|     -l preload      |          设置在送出要求信息之前，先行发出的数据包；          |
|         -L          |      抑制组播报文回送，只适用于ping的目标为一个组播地址      |
|         -n          |                  不要将ip地址转换成主机名；                  |
|     -p pattern      | 指定填充ping数据包的十六进制内容，在诊断与数据有关的网络错误时这个选项就非常有用，如：“-p ff”； |
|         -q          |          不显示任何传送封包的信息，只显示最后的结果          |
|       -Q tos        | 设置Qos(Quality of Service)，它是ICMP数据报相关位；可以是十进制或十六进制数，详见rfc1349和rfc2474文档； |
|         -R          | 记录ping的路由过程(IPv4 only)； 注意：由于IP头的限制，最多只能记录9个路由，其他会被忽略； |
|         -r          | 忽略正常的路由表，直接将数据包送到远端主机上，通常是查看本机的网络接口是否有问题；如果主机不直接连接的网络上，则返回一个错误。 |
|      -S sndbuf      | Set socket sndbuf. If not specified, it is selected to buffer not more than one packet. |
|    -s packetsize    | 指定每次ping发送的数据字节数，默认为“56字节”+“28字节”的ICMP头，一共是84字节； 包头+内容不能大于65535，所以最大值为65507（linux:65507, windows:65500）； |
|       -t ttl        | 设置TTL(Time To Live)为指定的值。该字段指定IP包被路由器丢弃之前允许通过的最大网段数； |
| -T timestamp_option | 设置IP timestamp选项,可以是下面的任何一个： 　　'tsonly' (only timestamps) 　　'tsandaddr' (timestamps and addresses) 　　'tsprespec host1 [host2 [host3]]' (timestamp prespecified hops). |
|       -M hint       | 设置MTU（最大传输单元）分片策略。 可设置为： 　　'do'：禁止分片，即使包被丢弃； 　　'want'：当包过大时分片； 　　'dont'：不设置分片标志（DF flag）； |
|       -m mark       |                          设置mark；                          |
|         -v          | 使ping处于verbose方式，它要ping命令除了打印ECHO-RESPONSE数据包之外，还打印其它所有返回的ICMP数据包； |
|         -U          | Print full user-to-user latency (the old behaviour). Normally ping prints network round trip time, which can be different f.e. due to DNS failures. |
|     -W timeout      |               以毫秒为单位设置ping的超时时间；               |
|     -w deadline     |                          deadline；                          |



### 2、netstat

netstat，用来查看**当前系统中建立的网络连接**，它会列出所有已经连接或者等待连接状态的连接。

```
 Usage: netstat [address_family_options] [--tcp|-t] [--udp|-u] [--udplite|-U] [--sctp|-S] [--raw|-w]
         [--  listening|-l] [--all|-a] [--  numeric|-n] [--numeric-hosts] [--numeric-ports][--numeric-users] 
         [--symbolic|-N] [--extend|-e[--extend|-e]] [--timers|-o] [--program|-p] [--verbose|-v] 
         [--continuous|-c] [--wide|-W] [delay]
```

常见参数：

|      参数       |                    详解                    |
| :-------------: | :----------------------------------------: |
|     -a(all)     |               列出所有端口；               |
|     -t(tcp)     |            仅显示tcp相关选项；             |
|     -u(udp)     |            仅显示udp相关选项；             |
| -x(unix socket) |        仅显示unix socket相关选项；         |
|       -n        | 拒绝显示别名，能显示数字的全部转化成数字； |
|       -l        |   仅列出有在 Listen (监听) 的服務状态；    |
|       -p        |         显示建立相关链接的程序名；         |
|       -r        |           显示路由信息，路由表；           |
|       -e        |         显示扩展信息，例如uid等；          |
|       -s        |            按各个协议进行统计；            |
|       -c        |    每隔一个固定时间，执行该netstat命令.    |

**PS:**

- LISTEN和LISTENING的状态只有用-a或者-l才能看到；
- netstat -r 可以查看本地路由表



### 3、ss

ss，是一个查看网络连接的工具(another utility to investigate sockets),***\*用来显示处于活动状态的套接字信息\****。

它可以用来获取socket统计信息，它可以显示和netstat类似的内容。但ss的优势在于它能够显示更多更详细的有关TCP和连接状态的信息，而且比netstat更快速更高效。当服务器的socket连接数量变得非常大时，无论是使用netstat命令还是直接cat /proc/net/tcp，执行速度都会很慢。当服务器维持的连接达到上万个的时候，使用netstat的时间会长很多。 而ss快的秘诀在于，它利用到了TCP协议栈中tcp_diag。tcp_diag是一个用于分析统计的模块，可以第一时间获得Linux 内核的信息，这就确保了ss的快捷高效。而系统若是中没有tcp_diag，ss也可以正常运行，只是效率会变得稍慢。

```
Usage: ss [ OPTIONS ] [ FILTER ]
```

常见参数：

|      参数       |           详解           |
| :-------------: | :----------------------: |
|    -a（all）    |     列出所有socket；     |
|    -t（tcp）    |      查看tcp连接；       |
|       -4        |      查看ipv4连接;       |
|  -s（summary）  |   显示 Sockets 摘要；    |
| -p（progress）  |   按各个协议进行统计；   |
| -l（listening） | 查看处于LISTEN状态的连接 |
|  -n（numeric）  |     不进行域名解析;      |
|  -r（resolve）  |      解析服务名称；      |
|  -m（memory）   |      显示内存情况。      |

例如：通过`ss`命令查看本地监听的所有端口(和netstat命令功能类似):

```
$ ss  -t -l -n -4
```



### 4、ifstat

ifstat，简单的网络接口监测工具，可以查看对应网卡的网络流量概况。

```
$ ifstat        #-a参数显示所有网口
#kernel
Interface        RX Pkts/Rate    TX Pkts/Rate    RX Data/Rate    TX Data/Rate  
                 RX Errs/Drop    TX Errs/Drop    RX Over/Rate    TX Coll/Rate  
lo               290456K 0       290456K 0         3071M 0         3071M 0      
                       0 0             0 0             0 0             0 0      
em1              488765K 0       456601K 0         2287M 0         2953M 0      
                       0 256           0 0             0 0             0 0      
em2                    0 0             0 0             0 0             0 0      
                       0 0             0 0             0 0             0 0 
```



### 5、iftop

iftop，一款实时流量监控工具，必须以root身份才能运行。

```
$ iftop
```

- 第一行：带宽显示

- 中间部分：外部连接列表，即记录了哪些ip正在和本机的网络连接

- 中间部分右边：实时参数分别是该访问ip连接到本机2秒，10秒和40秒的平均流量

- =>代表发送数据，<= 代表接收数据

- 底部三行：表示 TX发送，RX接收和 TOTAL全部的流量

- 底部三行第二列：为你运行iftop到目前流量

- 底部三行第三列：为高峰值

- 底部三行第四列：为平均值


**PS:**

1、通过iftop的界面很容易找到哪个ip在霸占网络流量，这个是ifstat做不到的。不过iftop的流量显示单位是Mb,这个b是bit，是位，不是字节，而ifstat的KB，这个B就是字节了，byte是bit的8倍。

2、进入iftop画面后的一些操作命令(注意大小写)：

- 按h切换是否显示帮助;

- 按n切换显示本机的IP或主机名;

- 按s切换是否显示本机的host信息;

- 按d切换是否显示远端目标主机的host信息;

- 按t切换显示格式为2行/1行/只显示发送流量/只显示接收流量;

- 按N切换显示端口号或端口服务名称;

- 按S切换是否显示本机的端口信息;

- 按D切换是否显示远端目标主机的端口信息;

- **按p切换是否显示端口信息;**
- **按P切换暂停/继续显示;**
- 按b切换是否显示平均流量图形条;

- 按B切换计算2秒或10秒或40秒内的平均流量;

- 按T切换是否显示每个连接的总流量;

- 按q退出监控。



### 6、nc

nc(netcat)，可以根据需要创建各种不同类型的网络连接，其非常轻巧但功能强大。官方描述的功能包括:

- simple TCP proxies
- shell-script based HTTP clients and servers
- network daemon testing
- a SOCKS or HTTP ProxyCommand for ssh(1)
- and much, much more

能够实现简单的聊天工具、模拟ssh登录远程主机、远程传输文件等。

参考网址：https://www.cnblogs.com/misswangxing/p/11242859.html

echo stat|nc 127.0.0.1 2181



### 7、tcpdump

tcpdump(dump traffic on a network)，根据使用者的定义对网络上的数据包进行截获的包分析工具。 tcpdump可以将网络中传送的数据包的“头”完全截获下来提供分析。它支持针对网络层、协议、主机、网络或端口的过滤，并提供and、or、not等逻辑语句来帮助你去掉无用的信息。它能够实现`Wireshark`一样的功能，并且更加灵活自由。

```
 Usage: tcpdump [-DenNqvX] [-c count ] [-F file] [-i interface] [-r file] [-s snaplen] [-w file]
         [expression]
```

**抓包选项参数：**

|     参数     |                             详解                             |
| :----------: | :----------------------------------------------------------: |
|      -c      |                     指定要抓取的包数量；                     |
| -i interface |    指定tcpdump需要监听的接口，默认会抓取第一个网络接口；     |
|      -n      | 对地址以数字方式显式，否则显式为主机名，也就是说-n选项不做主机名解析； |
|     -nn      |   除了-n的作用外，还把端口显示为数值，否则显示端口服务名；   |
|      -P      | 指定要抓取的包是流入还是流出的包。可以给定的值为"in"、"out"和"inout"，默认为"inout"； |
|    -s len    | 设置tcpdump的数据包抓取长度为len，如果不设置默认将会是65535字节。对于要抓取的数据包较大时，长度设置不够可能会产生包截断，若出现包截断，输出行中会出现"[proto]"的标志(proto实际会显示为协议名)。但是抓取len越长，包的处理时间越长，并且会减少tcpdump可缓存的数据包的数量，从而会导致数据包的丢失，所以在能抓取我们想要的包的前提下，抓取长度越小越好。 |

**输出选项参数：**

| 参数 |                             详解                             |
| :--: | :----------------------------------------------------------: |
|  -e  | 输出的每行中都将包括数据链路层头部信息，例如源MAC和目标MAC； |
|  -q  | 快速打印输出，即打印很少的协议相关信息，从而输出行都比较简短； |
|  -X  |    输出包的头部数据，会以16进制和ASCII两种方式同时输出；     |
| -XX  | 输出包的头部数据，会以16进制和ASCII两种方式同时输出，更详细； |
|  -v  |             当分析和打印的时候，产生详细的输出；             |
| -vv  |                    产生比-v更详细的输出；                    |
| -vvv |                   产生比-vv更详细的输出。                    |

**其他功能性选项：**

| 参数 |                             详解                             |
| :--: | :----------------------------------------------------------: |
|  -D  | 列出可用于抓包的接口。将会列出接口的数值编号和接口名，它们都可以用于"-i"后； |
|  -F  | 从文件中读取抓包的表达式。若使用该选项，则命令行中给定的其他表达式都将失效； |
|  -w  | 将抓包数据输出到文件中而不是标准输出。可以同时配合"-G time"选项使得输出文件每time秒就自动切换到另一个文件。可通过"-r"选项载入这些文件以进行分析和打印除了-n的作用外，还把端口显示为数值，否则显示端口服务名； |
|  -r  | 从给定的数据包文件中读取数据。使用"-"表示从标准输入中读取。  |

**PS：**tcpdump只能抓取流经本机的数据包

例如：

1、需要抓取目标主机是`172.31.161.153`，通过端口`22`的传输数据包：

```
$ tcpdump -n -i em1 'dst host 172.31.161.153 && port 22' 
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on em1, link-type EN10MB (Ethernet), capture size 262144 bytes
18:45:31.585997 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 3878954338, win 65535, length 0
18:45:31.587041 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 149, win 65535, length 0
18:45:31.588128 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 297, win 65535, length 0
18:45:31.589418 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 445, win 65535, length 0
18:45:31.590076 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 593, win 65535, length 0
18:45:31.590783 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 741, win 65535, length 0
18:45:31.591562 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 889, win 65535, length 0
18:45:31.592394 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 1037, win 65535, length 0
18:45:31.593295 IP 172.16.12.202.56201 > 172.31.161.153.ssh: Flags [.], ack 1185, win 65535, length 0
...
470 packets captured
471 packets received by filter
0 packets dropped by kernel
```

2、抓取`HTTP`包:

```
 $ tcpdump  -XvvennSs 0 -i em1 tcp[20:2]=0x4745 or tcp[20:2]=0x4854
```

其中`0x4745`为`"GET"`前两个字母`"GE"`,`0x4854`为`"HTTP"`前两个字母`"HT"`。

指定`-A`以ACII码输出数据包，使用`-c`指定抓取包的个数。

3、 解析包数据

```
 $ tcpdump -c 2 -q -XX -vvv -nn -i ens33 tcp dst port 22
tcpdump: listening on em1, link-type EN10MB (Ethernet), capture size 262144 bytes
19:11:00.411247 IP (tos 0x10, ttl 58, id 65192, offset 0, flags [DF], proto TCP (6), length 40)
    172.16.12.202.56201 > 172.31.161.153.22: tcp 0
	0x0000:  1418 775c f635 7c1e 0624 d9cb 0800 4510  ..w\.5|..$....E.
	0x0010:  0028 fea8 4000 3a06 3b84 ac10 0cca ac1f  .(..@.:.;.......
	0x0020:  a199 db89 0016 0436 bb19 e737 84b2 5010  .......6...7..P.
	0x0030:  ffff a267 0000 0000 0000 0000            ...g........
19:11:00.411540 IP (tos 0x10, ttl 58, id 65193, offset 0, flags [DF], proto TCP (6), length 40)
    172.16.12.202.56201 > 172.31.161.153.22: tcp 0
	0x0000:  1418 775c f635 7c1e 0624 d9cb 0800 4510  ..w\.5|..$....E.
	0x0010:  0028 fea9 4000 3a06 3b83 ac10 0cca ac1f  .(..@.:.;.......
	0x0020:  a199 db89 0016 0436 bb19 e737 8546 5010  .......6...7.FP.
	0x0030:  ffff a1d3 0000 0000 0000 0000            ............
2 packets captured
29 packets received by filter
0 packets dropped by kernel
```



### 8、nslookup & dig

nslookup，用于交互式域名解析(query Internet name servers interactively)，也可以直接传入域名命令使用，比如查看`www.baidu.com`的ip地址：

```
$ nslookup www.baidu.com
Server:		10.255.254.88
Address:	10.255.254.88#53

Non-authoritative answer:
www.baidu.com	canonical name = www.a.shifen.com.
Name:	www.a.shifen.com
Address: 14.215.177.39
Name:	www.a.shifen.com
Address: 14.215.177.38
```

查看使用的DNS服务器地址：

```
$ nslookup
> www.baidu.com
Server:		10.255.254.88
Address:	10.255.254.88#53

Non-authoritative answer:
www.baidu.com	canonical name = www.a.shifen.com.
Name:	www.a.shifen.com
Address: 14.215.177.38
Name:	www.a.shifen.com
Address: 14.215.177.39
```

dig，也是域名解析工具(DNS lookup utility)，不过提供的信息更全面：

```
$ dig www.baidu.com

; <<>> DiG 9.9.4-RedHat-9.9.4-50.el7 <<>> www.baidu.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 40720
;; flags: qr rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;www.baidu.com.			IN	A

;; ANSWER SECTION:
www.baidu.com.		848	IN	CNAME	www.a.shifen.com.
www.a.shifen.com.	66	IN	A	14.215.177.39
www.a.shifen.com.	66	IN	A	14.215.177.38

;; Query time: 0 msec
;; SERVER: 10.255.254.88#53(10.255.254.88)
;; WHEN: Mon Aug 10 21:00:41 CST 2020
;; MSG SIZE  rcvd: 101
```



### 9、traceroute

traceroute，用于统计到目标主机的每一跳的网络状态（print the route packets trace to network host），这个命令常常用于判断网络故障，比如本地不通，可使用该命令探测出是哪个路由出问题了。如果网络很卡，该命令可判断哪里是瓶颈：

```
$  traceroute  -I -n www.baidu.com
traceroute to www.baidu.com (14.215.177.39), 30 hops max, 60 byte packets
 1  172.31.161.251  0.805 ms  1.259 ms  1.836 ms
 2  100.70.0.93  0.582 ms  0.971 ms  1.357 ms
 3  100.70.0.110  0.806 ms  1.223 ms  1.689 ms
 4  100.70.2.198  0.306 ms  0.477 ms  0.558 ms
 5  36.7.109.2  3.828 ms  4.175 ms  4.325 ms
 6  100.64.23.1  3.532 ms  3.585 ms  3.733 ms
 7  10.12.0.161  5.966 ms  6.562 ms  6.371 ms
 8  61.190.194.1  4.222 ms  4.112 ms  4.751 ms
 9  61.132.190.217  7.006 ms  7.389 ms  7.196 ms
10  * * *
11  113.96.4.126  34.313 ms  34.040 ms  34.010 ms
12  113.96.11.74  29.367 ms  29.507 ms  29.884 ms
13  14.215.32.90  27.951 ms  27.990 ms  27.839 ms
14  * * *
15  14.215.177.39  28.477 ms  25.913 ms  25.834 ms
```

可以看到，从主机到`www.baidu.com`共经过15跳，并统计了每一跳间的响应时间。

另外可以参考`tracepath`。



### 10、mtr

mtr，是一种网络诊断工具(a network diagnostic tool)，其把ping和traceroute并入一个程序的网络诊断工具中并实时刷新。

```
mtr -n www.baidu.com
```



## 二、Linux常用系统工具总结

### 1、turbostat 

turbostat，是linux系统下一种监控CPU性能的工具。

```
$ turbostat
```



### 2、**vmstat**

vmstat，一个很全面的性能分析工具，可以观察到系统的进程状态、内存使用、虚拟内存使用、磁盘的 IO、中断、上下问切换、CPU使用等。

```
$ vmstat
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 46450840 336308 48133600    0    0     1    14    0    0  0  0 99  0  0
```

**procs：**

- ​    r：运行队列中进程数量，这个值也可以判断是否需要增加CPU。（长期大于1）
- ​    b：因为io处于阻塞状态的进程数。

**memory：**

- swap：使用虚拟内存大小
- free：空闲物理内存大小
- buff：用作缓冲的内存大小
- cache：用作缓存的内存大小

**swap：**

- si：每秒从交换区写到内存的大小，由磁盘调入内存
- so：每秒写入交换区的内存大小，由内存调入磁盘
- bi：从块设备读入的数据总量（读磁盘）（KB/s）
- bo：写入到块设备的数据总量（写磁盘）（KB/s）

**system：**

- in:每秒产生的中断次数
- cs：每秒产生的上下文切换次数

**cpu：**

- us：用户进程消耗的CPU时间百分比
- sy：内核进程消耗的CPU时间百分比
- wa：IO等待消耗的CPU时间百分比
- id：CPU处在空闲状态时间百分比



### 3、 sar

sar（System Activity Reporter系统活动情况报告）是一种全面的系统性能分析工具，可以从多方面对系统的活动进行报告，包括：文件的读写情况、 系统调用的使用情况、磁盘I/O、CPU效率、内存使用状况、进程活动及IPC有关的活动等。

```
Usage: sar [-A] [ -B ] [ -b ] [ -C ] [ -d] [-H] [-h] [ -p] [-q] [-R] [-r] [-S] [-t] [-u[ALL]] [-V] [-v]
         [-W] [-w] [-y] [-I{int[,...]|SUM|ALL|XALL}] [-P{cpu[,...]|ALL}] [-m{keyword[,...]|ALL}] 
         [-n{keyword[,...]|ALL}] [-j{ID|LABEL|PATH|UUID|...}] [-f[filename]|-o[filename]|-[0-9]+] 
         [-i interval] [-s[hh:mm:ss]] [-e[hh:mm:ss] [interval[count]]
```

**常用参数：**

|   参数    |                  详解                  |
| :-------: | :------------------------------------: |
| -A（all） |            所有报告的总和；            |
|    -u     |      输出CPU使用情况的统计信息；       |
|    -v     | 输出inode、文件和其他内核表的统计信息; |
|    -d     |      输出每一个块设备的活动信息；      |
|    -r     |     输出内存和交换空间的统计信息；     |
|    -b     |     显示I/O和传送速率的统计信息；      |
|    -a     |             文件读写情况;              |
|    -c     |  输出进程统计信息，每秒创建的进程数；  |
|    -R     |        输出内存页面的统计信息；        |
|    -y     |           终端设备活动情况；           |
|    -w     |         输出系统交换活动信息。         |

**例如：**

**1. CPU资源监控**

每10秒采样一次，连续采样3次，观察CPU 的使用情况，并将采样结果以二进制形式存入当前目录下的文件test中：

```
$ sar -u -o test 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

11:53:12 AM     CPU     %user     %nice   %system   %iowait    %steal     %idle
11:53:22 AM     all      1.51      0.00      0.34      0.03      0.00     98.12
11:53:32 AM     all      0.72      0.00      0.32      0.06      0.00     98.91
11:53:42 AM     all      1.86      0.00      0.34      0.00      0.00     97.80
Average:        all      1.36      0.00      0.33      0.03      0.00     98.28
```

输出项说明：

- CPU：all 表示统计信息为所有 CPU 的平均值。

- %user：显示在用户级别(application)运行使用 CPU 总时间的百分比。

- %nice：显示在用户级别，用于nice操作，所占用 CPU 总时间的百分比。

- %system：在核心级别(kernel)运行所使用 CPU 总时间的百分比。

- %iowait：显示用于等待I/O操作占用 CPU 总时间的百分比。

- %steal：管理程序(hypervisor)为另一个虚拟进程提供服务而等待虚拟 CPU 的百分比。

- %idle：显示 CPU 空闲时间占用 CPU 总时间的百分比。


**PS:**

- 若 %iowait 的值过高，表示硬盘存在I/O瓶颈

- 若 %idle 的值高但系统响应慢时，有可能是 CPU 等待分配内存，此时应加大内存容量

- 若 %idle 的值持续低于1，则系统的 CPU 处理能力相对较低，表明系统中最需要解决的资源是 CPU 。

如果要查看二进制文件test中的内容，需键入如下sar命令：

```
sar -u -f test
```

**2. inode、文件和其他内核表监控**

每10秒采样一次，连续采样3次，观察核心表的状态，需键入如下

```
$ sar -v 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

12:15:25 PM dentunusd   file-nr  inode-nr    pty-nr
12:15:35 PM    904924     11392    686355         9
12:15:45 PM    903377     11392    685085         9
12:15:55 PM    901329     11456    684046         9
Average:       903210     11413    685162         9
```

输出项说明：

- dentunusd：目录高速缓存中未被使用的条目数量

- file-nr：文件句柄（file handle）的使用数量

- inode-nr：索引节点句柄（inode handle）的使用数量

- pty-nr：使用的pty数量


**3. 内存和交换空间监控**

每10秒采样一次，连续采样3次，监控内存分页：

```
$ sar -r 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

12:17:17 PM kbmemfree kbmemused %memused kbbuffers kbcached  kbcommit   %commit  kbactive  kbinact   kbdirty
12:17:27 PM   435528 131310332    99.67   1746500  98916516  66145668    50.21  64879408  54418012       500
12:17:37 PM   421056 131324804    99.68   1746532  98916572  66145812    50.21  64893512  54417960       504
12:17:47 PM   422480 131323380    99.68   1746500  98902628  66145944    50.21  64899000  54412364       372
Average:      426355 131319505    99.68   1746511  98911905  66145808    50.21  64890640  54416112       459
```

输出项说明：

- kbmemfree：这个值和free命令中的free值基本一致,所以它不包括buffer和cache的空间.

- kbmemused：这个值和free命令中的used值基本一致,所以它包括buffer和cache的空间.

- %memused：这个值是kbmemused和内存总量(不包括swap)的一个百分比.

- kbbuffers和kbcached：这两个值就是free命令中的buffer和cache.

- kbcommit：保证当前系统所需要的内存,即为了确保不溢出而需要的内存(RAM+swap).

- %commit：这个值是kbcommit与内存总量(包括swap)的一个百分比.


**4. 内存分页监控**

每10秒采样一次，连续采样3次，监控内存分页：

```
$ sar -B 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

01:59:31 PM  pgpgin/s pgpgout/s   fault/s  majflt/s  pgfree/s pgscank/s pgscand/s pgsteal/s    %vmeff
01:59:41 PM      0.00    133.50   6980.50      0.00   3747.70      0.00      0.00      0.00      0.00
01:59:51 PM      0.00    185.80   7021.30      0.00   3791.90      0.00      0.00      0.00      0.00
02:00:01 PM      0.00    151.70   6214.40      0.00   3184.30      0.00      0.00      0.00      0.00
Average:         0.00    157.00   6738.73      0.00   3574.63      0.00      0.00      0.00      0.00
```

输出项说明：

- pgpgin/s：表示每秒从磁盘或SWAP置换到内存的字节数(KB)

- pgpgout/s：表示每秒从内存置换到磁盘或SWAP的字节数(KB)

- fault/s：每秒钟系统产生的缺页数,即主缺页与次缺页之和(major + minor)

- majflt/s：每秒钟产生的主缺页数.

- pgfree/s：每秒被放入空闲队列中的页个数

- pgscank/s：每秒被kswapd扫描的页个数

- pgscand/s：每秒直接被扫描的页个数

- pgsteal/s：每秒钟从cache中被清除来满足内存需要的页个数

- %vmeff：每秒清除的页(pgsteal)占总扫描页(pgscank+pgscand)的百分比


**5. I/O和传送速率监控**

每10秒采样一次，连续采样3次，报告缓冲区的使用情况，需键入如下命令：

```
$ sar -b 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

02:05:02 PM       tps      rtps      wtps   bread/s   bwrtn/s
02:05:12 PM     16.90      0.00     16.90      0.00    245.90
02:05:22 PM     21.10      0.10     21.00      1.60    391.50
02:05:32 PM     14.30      0.00     14.30      0.00    209.60
Average:        17.43      0.03     17.40      0.53    282.33
```

输出项说明：

- tps：每秒钟物理设备的 I/O 传输总量

- rtps：每秒钟从物理设备读入的数据总量

- wtps：每秒钟向物理设备写入的数据总量

- bread/s：每秒钟从物理设备读入的数据量，单位为 块/s

- bwrtn/s：每秒钟向物理设备写入的数据量，单位为 块/s


**6. 进程队列长度和平均负载状态监控**

每10秒采样一次，连续采样3次，监控进程队列长度和平均负载状态：

```
$ sar -q 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

02:06:10 PM   runq-sz  plist-sz   ldavg-1   ldavg-5  ldavg-15   blocked
02:06:20 PM         0      4269      0.18      0.18      0.15         0
02:06:30 PM         0      4273      0.45      0.24      0.17         0
02:06:40 PM         1      4271      0.38      0.23      0.17         0
Average:            0      4271      0.34      0.22      0.16         0
```

输出项说明：

- runq-sz：运行队列的长度（等待运行的进程数）

- plist-sz：进程列表中进程（processes）和线程（threads）的数量

- ldavg-1：最后1分钟的系统平均负载（System load average）

- ldavg-5：过去5分钟的系统平均负载

- ldavg-15：过去15分钟的系统平均负载


**7. 系统交换活动信息监控**

每10秒采样一次，连续采样3次，监控系统交换活动信息：

```
$ sar -W 10 3
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

02:07:05 PM  pswpin/s pswpout/s
02:07:15 PM      0.00      0.00
02:07:25 PM      0.00      0.00
02:07:35 PM      0.00      0.00
Average:         0.00      0.00
```

输出项说明：

- pswpin/s：每秒系统换入的交换页面（swap page）数量

- pswpout/s：每秒系统换出的交换页面（swap page）数量


**8. 设备使用情况监控**

例如，每10秒采样一次，连续采样3次，报告设备使用情况，需键入如下命令：

```shell
$ sar -d 10 3 -p
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

02:07:57 PM       DEV       tps  rd_sec/s  wr_sec/s  avgrq-sz  avgqu-sz     await     svctm     %util
02:08:07 PM       sda      8.80      0.00     93.10     10.58      0.00      0.01      0.01      0.01
02:08:07 PM       sdb      1.40      0.00     44.00     31.43      0.00      0.00      0.00      0.00
02:08:07 PM       sdc      1.40      0.00     41.60     29.71      0.00      0.07      0.07      0.01
02:08:07 PM       sdd      1.40      0.00     41.60     29.71      0.00      0.00      0.00      0.00
02:08:07 PM       sde      1.40      0.00     41.60     29.71      0.00      0.00      0.00      0.00
02:08:07 PM       sdg      1.40      0.00     41.60     29.71      0.00      0.00      0.00      0.00
02:08:07 PM       sdf      1.90      0.00     46.40     24.42      0.00      0.00      0.00      0.00
02:08:07 PM       sdh      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:07 PM       sdi      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:07 PM       sdj      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:07 PM       sdk      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:07 PM       sdl      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:07 PM       sdm      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00

02:08:07 PM       DEV       tps  rd_sec/s  wr_sec/s  avgrq-sz  avgqu-sz     await     svctm     %util
02:08:17 PM       sda     11.40      0.00    113.30      9.94      0.00      0.10      0.05      0.06
02:08:17 PM       sdb      2.00      0.00     32.00     16.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdc      1.00      0.00     22.40     22.40      0.00      0.00      0.00      0.00
02:08:17 PM       sdd      1.00      0.00     24.00     24.00      0.00      0.00      0.00      0.00
02:08:17 PM       sde      1.60      0.00     28.00     17.50      0.00      0.00      0.00      0.00
02:08:17 PM       sdg      1.30      0.00     24.80     19.08      0.00      0.00      0.00      0.00
02:08:17 PM       sdf      1.00      0.00     24.00     24.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdh      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdi      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdj      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdk      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdl      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:17 PM       sdm      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00

02:08:17 PM       DEV       tps  rd_sec/s  wr_sec/s  avgrq-sz  avgqu-sz     await     svctm     %util
02:08:27 PM       sda     13.40      0.00    201.40     15.03      0.00      0.01      0.01      0.01
02:08:27 PM       sdb      1.00      0.00     24.00     24.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdc      1.40      0.00     24.00     17.14      0.00      0.00      0.00      0.00
02:08:27 PM       sdd      1.50      0.00     28.80     19.20      0.00      0.00      0.00      0.00
02:08:27 PM       sde      1.00      0.00     22.40     22.40      0.00      0.00      0.00      0.00
02:08:27 PM       sdg      0.80      0.00     20.00     25.00      0.00      0.12      0.12      0.01
02:08:27 PM       sdf      1.00      0.00     24.00     24.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdh      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdi      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdj      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdk      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdl      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
02:08:27 PM       sdm      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00

Average:          DEV       tps  rd_sec/s  wr_sec/s  avgrq-sz  avgqu-sz     await     svctm     %util
Average:          sda     11.20      0.00    135.93     12.14      0.00      0.04      0.02      0.03
Average:          sdb      1.47      0.00     33.33     22.73      0.00      0.00      0.00      0.00
Average:          sdc      1.27      0.00     29.33     23.16      0.00      0.03      0.03      0.00
Average:          sdd      1.30      0.00     31.47     24.21      0.00      0.00      0.00      0.00
Average:          sde      1.33      0.00     30.67     23.00      0.00      0.00      0.00      0.00
Average:          sdg      1.17      0.00     28.80     24.69      0.00      0.03      0.03      0.00
Average:          sdf      1.30      0.00     31.47     24.21      0.00      0.00      0.00      0.00
Average:          sdh      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:          sdi      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:          sdj      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:          sdk      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:          sdl      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
Average:          sdm      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00

```

输出项说明：

- 参数 **-p** 可以打印出sda,hdc等磁盘设备名称,如果不用参数-p,设备节点则有可能是dev8-0,dev22-0

- tps:每秒从物理磁盘I/O的次数.多个逻辑请求会被合并为一个I/O磁盘请求,一次传输的大小是不确定的.

- rd_sec/s:每秒读扇区的次数.

- wr_sec/s:每秒写扇区的次数.

- avgrq-sz:平均每次设备I/O操作的数据大小(扇区).

- avgqu-sz:磁盘请求队列的平均长度.

- await:从请求磁盘操作到系统完成处理,每次请求的平均消耗时间,包括请求队列等待时间,单位是毫秒(1秒=1000毫秒).

- svctm:系统处理每次请求的平均时间,不包括在请求队列中消耗的时间.

- %util:I/O请求占CPU的百分比,比率越大,说明越饱和.


**PS：**

- 1、avgqu-sz 的值较低时，设备的利用率较高。

- 2、当%util的值接近 1% 时，表示设备带宽已经占满。

**9、要判断系统瓶颈问题，有时需几个 sar 命令选项结合起来**

怀疑CPU存在瓶颈，可用 sar -u 和 sar -q 等来查看

怀疑内存存在瓶颈，可用 sar -B、sar -r 和 sar -W 等来查看

怀疑I/O存在瓶颈，可用 sar -b、sar -u 和 sar -d 等来查看



### 4、lsof 

lsof，全名list opened files，也就是列举系统中已经被打开的文件。Linux环境中，任何事物都是文件，设备是文件，目录是文件，甚至sockets也是文件。所以，lsof是linux最常用的命令之一。

```
Usage: lsof [-?abChKlnNOPRtUvVX] [-A A] [-c c] [+c c] [+|-d d] [+|-D D] [+|-e s] [+|-f[cfgGn]] [-F[f]]
        [-g[s]] [-i[i]] [-k k] [+|-L[l]] [+|-m m] [+|-M][-o [o]] [-p s] [+|-r[t[m<fmt>]]] [-s [p:s]] 
        [-S [t]] [-T [t]] [-u s] [+|-w] [-x [fl]] [-z [z]] [-Z [Z]] [--] [names]
```

**常用参数：**

|    参数    |                        详解                        |
| :--------: | :------------------------------------------------: |
|     -a     |              列出打开文件存在的进程；              |
| -c<进程名> |             列出指定进程所打开的文件；             |
|     -v     |       输出inode、文件和其他内核表的统计信息;       |
|     -g     |                列出GID号进程详情；                 |
| -d<文件号> |              列出占用该文件号的进程；              |
|  +d<目录>  |              列出目录下被打开的文件；              |
|  +D<目录>  |            递归列出目录下被打开的文件;             |
|  -n<目录>  |                列出使用NFS的文件；                 |
|  -i<条件>  | 列出符合条件的进程。（4、6、协议、:端口、 @ip ）； |
| -p<进程号> |            列出指定进程号所打开的文件；            |
|     -u     |                 列出UID号进程详情;                 |
|     -h     |                   显示帮助信息;                    |
|     -v     |                   显示版本信息.                    |

**例如：**

**1、无参数**

如果不加任何参数，就会列出所有被打开的文件：

```
$ lsof (COMMAND PID USER FD TYPE DEVICE SIZE NODE NAME)
...
java      102471 102796     hadoop  mem       REG        8,2      44448      99553 /usr/lib64/librt-2.17.so
java      102471 102796     hadoop  mem       REG        8,2    1139680      99531 /usr/lib64/libm-2.17.so
java      102471 102796     hadoop  mem       REG        8,2    2127336      99523 /usr/lib64/libc-2.17.so
java      102471 102796     hadoop  mem       REG        8,2      19776      99529 /usr/lib64/libdl-2.17.so
...
```

lsof输出各列信息的意义如下：

- COMMAND：进程的名称

- PID：进程标识符

- PPID：父进程标识符（需要指定-R参数）

- USER：进程所有者

- PGID：进程所属组

- FD：文件描述符，应用程序通过文件描述符识别该文件。如cwd、txt等


   （1）cwd：表示current work dirctory，即：应用程序的当前工作目录，这是该应用程序启动的目录，除非它本身对这个目录进行更改

   （2）txt ：该类型的文件是程序代码，如应用程序二进制文件本身或共享库，如上列表中显示的 /sbin/init 程序

   （3）lnn：library references (AIX);

   （4）er：FD information error (see NAME column);

   （5）jld：jail directory (FreeBSD);

   （6）ltx：shared library text (code and data);

   （7）mxx ：hex memory-mapped type number xx.

   （8）m86：DOS Merge mapped file;

   （9）mem：memory-mapped file;

   （10）mmap：memory-mapped device;

   （11）pd：parent directory;

   （12）rtd：root directory;

   （13）tr：kernel trace file (OpenBSD);

   （14）v86 VP/ix mapped file;

   （15）0：表示标准输出

   （16）1：表示标准输入

   （17）2：表示标准错误

​     一般在标准输出、标准错误、标准输入后还跟着文件状态模式：r、w、u等

   （1）u：表示该文件被打开并处于读取/写入模式

   （2）r：表示该文件被打开并处于只读模式

   （3）w：表示该文件被打开并处于

   （4）空格：表示该文件的状态模式为unknow，且没有锁定

​    （5）-：表示该文件的状态模式为unknow，且被锁定

​     同时在文件状态模式后面，还跟着相关的锁

​    （1）N：for a Solaris NFS lock of unknown type;

​    （2）r：for read lock on part of the file;

   （3）R：for a read lock on the entire file;

   （4）w：for a write lock on part of the file;（文件的部分写锁）

   （5）W：for a write lock on the entire file;（整个文件的写锁）

   （6）u：for a read and write lock of any length;

   （7）U：for a lock of unknown type;

   （8）x：for an SCO OpenServer Xenix lock on part   of the file;

   （9）X：for an SCO OpenServer Xenix lock on the   entire file;

   （10）space：if there is no lock.

- TYPE：文件类型，如DIR、REG等，常见的文件类型


   （1）DIR：表示目录

   （2）CHR：表示字符类型

   （3）BLK：块设备类型

   （4）UNIX： UNIX 域套接字

   （5）FIFO：先进先出 (FIFO) 队列

   （6）IPv4：网际协议 (IP) 套接字

- DEVICE：指定磁盘的名称

- SIZE：文件的大小

- NODE：索引节点（文件在磁盘上的标识）

- NAME：打开文件的确切名称


**2、查找某个文件相关的进程(查看谁正在使用某个文件)**

```
$ lsof /iflymonitor/test-monitor/var/app.log
COMMAND     PID USER   FD   TYPE DEVICE SIZE/OFF      NODE NAME
test-m 61012 root    1w   REG    8,2   214691 536878207 /iflymonitor/test-monitor/var/app.log
test-m 61012 root    2w   REG    8,2   214691 536878207 /iflymonitor/test-monitor/var/app.log
```

**3、递归查看某个目录的文件信息**

```
$ lsof +D /iflymonitor/
COMMAND     PID USER   FD   TYPE DEVICE SIZE/OFF       NODE NAME
test-m 61012 root  cwd    DIR    8,2      162 1611346584 /iflymonitor/test-monitor
test-m 61012 root  txt    REG    8,2 10595616 1611346619 /iflymonitor/test-monitor/test-monitor
test-m 61012 root    1w   REG    8,2   213027  536878207 /iflymonitor/test-monitor/var/app.log
test-m 61012 root    2w   REG    8,2   213027  536878207 /iflymonitor/test-monitor/var/app.log
```

**PS:** 使用了+D，对应目录下的所有子目录和文件都会被列出

**4、列出某个用户打开的文件信息**

```
$ lsof -u grafana
COMMAND      PID    USER   FD      TYPE             DEVICE SIZE/OFF       NODE NAME
grafana-s 188742 grafana  cwd       DIR                8,2       86 1098440931 /usr/share/grafana
grafana-s 188742 grafana  rtd       DIR                8,2     4096         64 /
grafana-s 188742 grafana  txt       REG                8,2 47938856     677816 /usr/sbin/grafana-server
grafana-s 188742 grafana  mem       REG                8,2  2127336      99523 /usr/lib64/libc-2.17.so
grafana-s 188742 grafana  mem       REG                8,2    19776      99529 /usr/lib64/libdl-2.17.so
grafana-s 188742 grafana  mem       REG                8,2   144792      99549 /usr/lib64/libpthread-2.17.so
grafana-s 188742 grafana  mem       REG                8,2   164264      85948 /usr/lib64/ld-2.17.so
grafana-s 188742 grafana    0r      CHR                1,3      0t0       2052 /dev/null
grafana-s 188742 grafana    1u     unix 0xffff881438bdf800      0t0   64811079 socket
grafana-s 188742 grafana    2u     unix 0xffff881438bdf800      0t0   64811079 socket
grafana-s 188742 grafana    3w      REG                8,2    56079   12453323 /var/log/grafana/grafana.log
grafana-s 188742 grafana    4u  a_inode                0,9        0       8616 [eventpoll]
grafana-s 188742 grafana    5u      REG                8,2   655360  553282420 /var/lib/grafana/grafana.db
grafana-s 188742 grafana    6u     IPv6           64822779      0t0        TCP bajie001:hbci->bajie001:55782 (ESTABLISHED)
grafana-s 188742 grafana    8u      REG                8,2   655360  553282420 /var/lib/grafana/grafana.db
grafana-s 188742 grafana    9u     IPv6           64812465      0t0        TCP *:hbci (LISTEN)
```

**5、列出某个程序进程所打开的文件信息**

```
$ lsof -c grafana
```

**PS:**  -c 选项将会列出所有以grafana这个进程开头的程序的文件，也可以写成 lsof | grep mysql。

**6、列出除了某个用户外的被打开的文件信息**

```
$ lsof -u ^root
```

**PS:**  ^这个符号在用户名之前，将会把是root用户打开的进程不让显示

**7、列出多个进程号对应的文件信息**

```
$ lsof -p 1,2,3
```

**8、列出COMMAND列中包含字符串" sshd"，且文件描符的类型为txt的文件信息**

```
$ lsof -c sshd -a -d txt
```

**9、列出网络相关信息**

由于在Linux中一切皆文件，那socket、pipe等也是文件，因此能够查看网络连接以及网络设备，其中和网络最相关的是`-i`选项，它输出符合条件的进程（4、6、协议、:端口、 @ip等），它的格式为`[46][protocol][@hostname|hostaddr][:service|port]`,

**例如：**

列出所有的网络连接

```
$ lsof -i
```

实例14：列出所有tcp 网络连接信息

```
$ lsof -i tcp
```

实例15：列出所有udp网络连接信息

```
$ lsof -i udp
```

查看22端口有没有打开，哪个进程打开的:

```
$ lsof -i :22
COMMAND    PID USER   FD   TYPE     DEVICE SIZE/OFF NODE NAME
sshd      1443 root    3u  IPv4      52710      0t0  TCP *:ssh (LISTEN)
sshd      1443 root    4u  IPv6      52712      0t0  TCP *:ssh (LISTEN)
```

可以指定多个条件，但默认是OR关系的，如果需要AND关系，必须传入`-a`参数，查看22端口并且使用Ipv6连接的进程：

```
$ lsof -c sshd -i 6 -a -i :22
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
sshd    1443 root    4u  IPv6  52712      0t0  TCP *:ssh (LISTEN)
```

列出所有与`192.168.56.1`（我的宿主机IP地址）的ipv4连接：

```
$ lsof -i 4@172.31.161.153
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
grafana-s 188742    grafana    6u  IPv6  64822779      0t0  TCP bajie001:hbci->bajie001:55782 (ESTABLISHED)
prometheu 194065       root    9u  IPv4  64847906      0t0  TCP bajie001:55782->bajie001:hbci (ESTABLISHED)
prometheu 194065       root   10u  IPv4  64847916      0t0  TCP bajie001:50888->bajie003:jetdirect (ESTABLISHED)
```

数据恢复



### 5、top 

top，是Linux下常用的性能分析工具，能够实时显示系统中各个进程的资源占用状况，类似于Windows的任务管理器。

```
$ top
```

**第一行，任务队列信息，同 uptime 命令的执行结果**

- 系统时间：19:46:15

- 运行时间：up 20 days,

- 当前登录用户：  9 users

- 负载均衡(uptime)  load average: 0.28, 0.37, 0.44  (average后面的三个数分别是1分钟、5分钟、15分钟的负载情况)

  load average数据是每隔5秒钟检查一次活跃的进程数，然后按特定算法计算出的数值。如果这个数除以逻辑CPU的数量，结果高于5的时候就表明系统在超负荷运转了


**第二行，Tasks — 任务（进程）**

总进程:465 total, 运行:1 running, 休眠:463 sleeping, 停止: 1 stopped, 僵尸进程: 0 zombie

**第三行，cpu状态信息**

- 0.4%us【user space】— 用户空间占用CPU的百分比。

- 1.1%sy【sysctl】— 内核空间占用CPU的百分比。
- 0.0%ni【】— 改变过优先级的进程占用CPU的百分比

- 98.5%id【idolt】— 空闲CPU百分比
- 0.0%wa【wait】— IO等待占用CPU的百分比

- 0.0%hi【Hardware IRQ】— 硬中断占用CPU的百分比

- 0.0%si【Software Interrupts】— 软中断占用CPU的百分比


**第四行,内存状态**

   KiB Mem :   13174585+total,  8154900 free, 10979576 used, 11261138+buff/cache【缓存的内存量】

**第五行，swap交换分区信息**

   KiB Swap:        0 total,        0 free,        0 used. 11652272+avail Mem【缓冲的交换区总量】

**第七行以下：各进程（任务）的状态监控**

- PID — 进程id
- USER — 进程所有者
- PR — 进程优先级
- NI — nice值。负值表示高优先级，正值表示低优先级
- VIRT — 进程使用的虚拟内存总量，单位kb。VIRT=SWAP+RES
- RES — 进程使用的、未被换出的物理内存大小，单位kb。RES=CODE+DATA
- SHR — 共享内存大小，单位kb
- S —进程状态。D=不可中断的睡眠状态 R=运行 S=睡眠 T=跟踪/停止 Z=僵尸进程
- %CPU — 上次更新到现在的CPU时间占用百分比
- %MEM — 进程使用的物理内存百分比
- TIME+ — 进程使用的CPU时间总计，单位1/100秒
- COMMAND — 进程名称（命令名/命令行）

**常用命令说明：**

- Ctrl+L：擦除并且重写屏幕

- K：终止一个进程。系统将提示用户输入需要终止的进程PID，以及需要发送给该进程什么样的信号。一般的终止进程可以使用15信号；如果不能正常结束那就使用信号9强制结束该进程。默认值是信号15。在安全模式中此命令被屏蔽。

- i：忽略闲置和僵死进程。这是一个开关式命令。

- q：退出程序

- r:重新安排一个进程的优先级别。系统提示用户输入需要改变的进程PID以及需要设置的进程优先级值。输入一个正值将使优先级降低，反之则可以使该进程拥有更高的优先权。默认值是10。

- S：切换到累计模式。

- s：改变两次刷新之间的延迟时间。系统将提示用户输入新的时间，单位为s。如果有小数，就换算成m s。输入0值则系统将不断刷新，默认值是5 s。需要注意的是如果设置太小的时间，很可能会引起不断刷新，从而根本来不及看清显示的情况，而且系统负载也会大大增加。

- f或者F：从当前显示中添加或者删除项目。

- o或者O：改变显示项目的顺序

- l：切换显示平均负载和启动时间信息。

- m:切换显示内存信息。

- t:切换显示进程和CPU状态信息。

- c:切换显示命令名称和完整命令行。

- M:根据驻留内存大小进行排序。

- P:根据CPU使用百分比大小进行排序。

- T:根据时间/累计时间进行排序。

- W:将当前设置写入~/.toprc文件中。



### 6、htop

htop，是一个Linux下的交互式的进程浏览器，可以用来替换Linux下的top命令。

```
$ htop
```

**左边部分：**从上至下，分别为，cpu、内存、交换分区的使用情况；

**右边部分：**Tasks为进程总数，当前运行的进程数、Load average为系统1分钟，5分钟，10分钟的平均负载情况、Uptime为系统运行的时间。

**中间各项**：

- PID：进行的标识号
- USER：运行此进程的用户
- PRI：进程的优先级
- NI：进程的优先级别值，默认的为0，可以进行调整
- VIRT：进程占用的虚拟内存值
- RES：进程占用的物理内存值
- SHR：进程占用的共享内存值
- S：进程的运行状况，R表示正在运行、S表示休眠，等待唤醒、Z表示僵死状态
- %CPU：该进程占用的CPU使用率
- %MEM：该进程占用的物理内存和总内存的百分比
- TIME+：该进程启动后占用的总的CPU时间
- COMMAND：进程启动的启动命令名称

**交互按键**：

| 按键      | 详解                                       |
| --------- | ------------------------------------------ |
| h，？，F1 | 查看htop使用说明                           |
| S，F2     | htop 设定                                  |
| /，F3     | 搜索进程                                   |
| \，F4     | 增量进程过滤器                             |
| t，F5     | 显示树形结构                               |
| <, >，F6  | 选择排序方式                               |
| [，F7     | 可减少nice值可以提高对应进程的优先级       |
| ]，F8     | 可增加nice值，降低对应进程的优先级         |
| k，F9     | 可对进程传递信号                           |
| q，F10    | 结束htop                                   |
| u         | 只显示一个给定的用户的过程                 |
| U         | 取消标记所有的进程                         |
| H         | 显示或隐藏用户线程                         |
| K         | 显示或隐藏内核线程                         |
| F         | 跟踪进程                                   |
| P         | 按CPU 使用排序                             |
| M         | 按内存使用排序                             |
| T         | 按Time+ 使用排序                           |
| l         | 显示进程打开的文件                         |
| I         | 倒转排序顺序                               |
| s         | 选择某进程，按s:用strace追踪进程的系统调用 |



### 7、iostat 

iostat，是I/O statistics（输入/输出统计）的缩写，iostat工具将对系统的磁盘操作活动进行监视。它的特点是汇报磁盘活动统计情况，同时也会汇报出CPU使用情况。iostat也有一个弱点，就是它不能对某个进程进行深入分析，仅对系统的整体情况进行分析

```
$ iostat
Linux 3.10.0-693.el7.x86_64 (bajie001) 	08/12/2020 	_x86_64_	(32 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           0.36    0.00    0.23    0.01    0.00   99.40

Device:            tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
sda              11.91         5.25       345.42    9138086  600971965
sdb               0.55         0.11         6.30     195037   10963836
sdc               0.34         0.11         4.39     190345    7632440
sdd               0.40         0.10         5.14     168893    8944640
sde               0.43         0.10         5.40     179373    9400860
sdg               0.40         0.10         5.13     166005    8933728
sdf               0.43         0.10         5.36     165625    9328660
sdh               0.02         0.10         0.00     165789        680
sdi               0.02         0.10         0.00     166001        696
sdj               0.43        10.25        72.97   17827725  126958328
sdk               0.02         0.10         0.00     166109       1024
sdl               0.02         0.09         0.00     148481        696
sdm               0.00         0.00         0.00       8621        68
```

**cpu属性值：**

- %user：CPU处在用户模式下的时间百分比。

- %nice：CPU处在带NICE值的用户模式下的时间百分比。

- %system：CPU处在系统模式下的时间百分比。

- %iowait：CPU等待输入输出完成时间的百分比。

- %steal：管理程序维护另一个虚拟处理器时，虚拟CPU的无意识等待时间百分比。

- %idle：CPU空闲时间百分比。

**PS:**

- 如果%iowait的值过高，表示硬盘存在I/O瓶颈

- 如果%idle值高，表示CPU较空闲

- 如果%idle值高但系统响应慢时，可能是CPU等待分配内存，应加大内存容量。

- 如果%idle值持续低于10，表明CPU处理能力相对较低，系统中最需要解决的资源是CPU。


**磁盘属性值说明:**

- tps：该设备每秒的传输次数

- kB_read/s：每秒从设备（drive expressed）读取的数据量；

- kB_wrtn/s：每秒向设备（drive expressed）写入的数据量；

- kB_read：  读取的总数据量；

- kB_wrtn：写入的总数量数据量；

**例如：**

**定时显示所有信息**

```
$ iostat 2 3   #每隔2秒刷新显示，且显示3次
```

**显示指定磁盘信息**

```
$ iostat -d /dev/sda
```

**显示tty和Cpu信息**

```
$ iostat -t
```

**以M为单位显示所有信息**

```
$ iostat -m
```

**查看cpu状态**

```
$ iostat -c 1 1
```

**查看设备使用率（%util）、响应时间（await）**

```
$ iostat -d -x -k 1 1  #-d 显示磁盘使用情况，-x 显示详细信息
Linux 3.10.0-693.el7.x86_64 	08/12/2020 	_x86_64_	(64 CPU)

Device:   rrqm/s   wrqm/s   r/s   w/s   rkB/s   wkB/s avgrq-sz avgqu-sz  await r_await w_await  svctm  %util
sda       0.00    0.09   1.09   5.30   56.65  3557.72   441.22    0.43   26.54    1.65   28.30   0.19   0.31
sdb       0.01    3.03   34.93  19.52  4315.91 4482.88   23.21    2.47   45.28    4.63  118.02   0.63   3.42
```

**PS:**

- rrqm/s： 每秒进行 merge 的读操作数目.即 delta(rmerge)/s

- wrqm/s： 每秒进行 merge 的写操作数目.即 delta(wmerge)/s

- %util： 一秒中有百分之多少的时间用于 I/O

- 如果%util接近100%，说明产生的I/O请求太多，I/O系统已经满负荷

-   idle小于70% IO压力就较大了，一般读取速度有较多的wait。



### 8、iotop

```
$ iotop
```

**常用参数：**

| **参数** |                           **详解**                           |
| :------: | :----------------------------------------------------------: |
|    -o    | --only只显示正在产生I/O的进程或线程。除了传参，可以在运行过程中按o生效； |
|    -b    |            --batch非交互模式，一般用来记录日志；             |
|  -n NUM  |             --iter=NUM设置监测的次数，默认无限;              |
|  -d SEC  | --delay=SEC设置每次监测的间隔，默认1秒，接受非整形数据例如1.1； |
|    -p    |                --pid=PID指定监测的进程/线程；                |
| -u USER  |            --user=USER指定监测某个用户产生的I/O；            |
|    -P    |        --processes仅显示进程，默认iotop显示所有线程;         |
|    -a    |           --accumulated显示累积的I/O，而不是带宽；           |
|    -k    |                   --kilobytes使用kB单位；                    |
|    -t    |              --time 加上时间戳，非交互非模式；               |
|    -q    | --quiet 禁止头几行，非交互模式，有三种指定方式:<br/>-q 只在第一次监测时显示列名<br/>　　-qq 永远不显示列名。<br/>　　-qqq 永远不显示I/O汇总。 |

**交互按键：**

- left和right方向键：改变排序
- r：反向排序。
- o：切换至选项--only。
- p：切换至--processes选项。
- a：切换至--accumulated选项。
- q：退出。
- i：改变线程的优先级。

**例如：**

**只显示正在产生I/O的进程或线程。除了传参，可以在运行过程中按o生效。**

```
$ iotop  -o
```

**时间刷新间隔2秒，输出5次**

```
$ iotop  -d 2 -n 5
```

**非交互式，输出5次，间隔2秒，输出到屏幕，也可输出到日志文本，用于监控某时间段的io信息**

```
$ iotop -botq -n 5 -d 2 
```

**非交互式，输出pid为8382的进程信息**

```
$ iotop -botq -p 8382
```
