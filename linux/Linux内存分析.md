# Linux 内存分析

## 一、内存定义

### 1、系统内存

我们在查看系统内存使⽤状况时，经常会常⽤free命令，具体可见如下输出
```shell
$ free -m
              total        used        free      shared  buff/cache   available
Mem:          14732        3233        6169          13        5329       11166
Swap:             0           0           0
```
可以看到，输出包括两⾏：Mem 和 Swap。

其中Mem表示系统中实际的物理内存；对于Memory来说，我们发现 total = used + free + buff/cache。

Swap表示交换分区（类似windows中的虚拟内存），是硬盘中⼀个独⽴的分区，⽤于在系统内存不够时，临时存储被释放的内存空间中的内容；对于Swap来说，三者的关系很简单，就是total = used + free。(在上⾯的例⼦中，由于这台ECS禁⽤swap空间，所以swap的值都是0。) 

而前三列 "total"、"used"、"free" 分别表示 总量，使⽤量和有多少空闲空间。
其中 buff 和 cache 分别表示存放了将要写到磁盘中的数据和从磁盘的读取的数据的内存。也就是说内存除了存储进程运⾏所需的运⾏时数据之外，还为了提⾼性能，缓存了⼀部分I/O数据。由于系统的cache和buffer可以被回收，所以可⽤的（available）内存⽐空闲的（free）要⼤。在部署了某些⾼I/O应⽤的主机中，available会⽐free看起来⼤很多，这是由于⼤量的内存空间⽤于缓存对磁盘的I/O数据。

- free命令的所有输出值都是从/proc/meminfo中读出的
	- [Linux：/proc/meminfo参数详细解释](https://blog.csdn.net/whbing1471/article/details/105468139/)
```shell
$ cat /proc/meminfo
MemTotal:       15085684 kB
MemFree:         6313276 kB
MemAvailable:   11430672 kB
Buffers:          223732 kB
Cached:          4933308 kB
SwapCached:            0 kB
Active:          1230852 kB
Inactive:        6970088 kB
Active(anon):      10052 kB
Inactive(anon):  3036540 kB
Active(file):    1220800 kB
Inactive(file):  3933548 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Dirty:              1096 kB
Writeback:             0 kB
AnonPages:       2639548 kB
Mapped:          1090488 kB
Shmem:             13524 kB
Slab:             382124 kB
SReclaimable:     299992 kB
SUnreclaim:        82132 kB
KernelStack:       24976 kB
PageTables:        21860 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:     7542840 kB
Committed_AS:    8885024 kB
VmallocTotal:   34359738367 kB
VmallocUsed:           0 kB
VmallocChunk:          0 kB
Percpu:             4528 kB
HardwareCorrupted:     0 kB
AnonHugePages:   1609728 kB
ShmemHugePages:        0 kB
ShmemPmdMapped:        0 kB
FileHugePages:         0 kB
FilePmdMapped:         0 kB
CmaTotal:              0 kB
CmaFree:               0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
DirectMap4k:      259896 kB
DirectMap2M:    10225664 kB
DirectMap1G:     7340032 kB
```

- 相关命令
```shell
# top类的命令查看进程/线程、CPU、内存使用情况，CPU使用情况
$ top/htop/atop

# 实时内存
$ sar -r
$ sar -R

# 查看内存使用情况，内存、CPU、IO状态
$ vmstat 2
```
	

### 2、进程内存

通过free命令，我们可以看到系统总体的内存使⽤状况。但很多时需要查看特定进程（process）所消耗的内存，这时我们最常⽤的命令是 `ps`，这个命令的输出中有两列与内存相关，分别是VSZ和RSS。此外还有另外两个类似的指标——PSS和USS，这⾥将这四个⼀并讨论：

|缩写|全称|含义|
|:------:|:------:|:------:|
|VSZ(VSS)|Virtual Memory Size|虚拟内存⼤⼩，表明了该进程可以访问的所有内存，包括被交换的内存和共享库内。VSZ对于判断一个进程实际占用的内存并没有什么帮助。|
|RSS|Resident Set Size|常驻内存集合⼤⼩，表示相应进程在RAM中占⽤了多少内存，并不包含在Swap中占⽤的虚拟内存。包括进程所使⽤的共享库所占⽤的全部内存，即使某个共享库只在内存中加载了⼀次，所有使⽤了它的进程的RSS都会分别把它计算在内。（把所有进程的RSS加到⼀起，通常会⽐实际使⽤的内存⼤，因为⼀些共享库所⽤的内存重复计算了多次。）|
|PSS|Proportional Set Size|与RSS类似，唯⼀的区别是在计算共享库内存是是按⽐例分配。⽐如某个共享库占用了3M内存，同时被3个进程共享，那么在计算这3个进程的PSS时，该共享库这会贡献1兆内存。|
|USS|Unique Set Size|进程独⾃占⽤的物理内存，不包含Swap和共享库。|

这四者的⼤⼩关系是：VSS >= RSS >= PSS >= USS

进程的内存使⽤情况可以从 `/proc/PID/status` 中读取，⽐如
	- VmSize: 当前的Virtual Memory Size
	- VmRSS: Resident Set Size
	- VmLib: 进程所加载的动态库所占⽤的内存⼤⼩
```shell
# 以 kubelet进程为例
$ cat /proc/1606/status
Name:	kubelet
Umask:	0022
State:	S (sleeping)
Tgid:	1606
Ngid:	0
Pid:	1606
PPid:	1
TracerPid:	0
Uid:	0	0	0	0
Gid:	0	0	0	0
FDSize:	256
Groups:
NStgid:	1606
NSpid:	1606
NSpgid:	1606
NSsid:	1606
VmPeak:	 1344936 kB
VmSize:	 1344936 kB
VmLck:	       0 kB
VmPin:	       0 kB
VmHWM:	  155976 kB
VmRSS:	  147396 kB
RssAnon:	   79060 kB
RssFile:	   68336 kB
RssShmem:	       0 kB
VmData:	  266584 kB
VmStk:	     132 kB
VmExe:	   55220 kB
VmLib:	       0 kB
VmPTE:	     604 kB
VmSwap:	       0 kB
HugetlbPages:	       0 kB
CoreDumping:	0
THP_enabled:	1
Threads:	19
SigQ:	0/58832
SigPnd:	0000000000000000
ShdPnd:	0000000000000000
SigBlk:	fffffffc3bba3a00
SigIgn:	0000000000000000
SigCgt:	fffffffdffc1feff
CapInh:	0000000000000000
CapPrm:	0000003fffffffff
CapEff:	0000003fffffffff
CapBnd:	0000003fffffffff
CapAmb:	0000000000000000
NoNewPrivs:	0
Seccomp:	0
Speculation_Store_Bypass:	vulnerable
Cpus_allowed:	f
Cpus_allowed_list:	0-3
Mems_allowed:	00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000001
Mems_allowed_list:	0
voluntary_ctxt_switches:	723
nonvoluntary_ctxt_switches:	226
```

- 相关命令
```shell
# 使用ps命令，直接查看 vsz、rss
$ ps -eo pid,comm,cpu,mem,vsz,rss

# 统计前20内存占用
$ ps -eo pid,comm,rss | awk '{m=$3/1e6;s["*"]+=m;s[$2]+=m} END{for (n in s) printf"%10.3f GB %s\n",s[n],n}' | sort -nr | head -20

# 进程内存统计
$ process_name="${process_name}"
$ for i in $(ps -ef | grep ${process_name} | grep -v grep |awk '{print $2}'); do VmRSS=$(cat /proc/$i/status 2>/dev/null | grep VmRSS); [[ ! -z ${VmRSS} ]] && echo "PID: $i    ${VmRSS}"; done | sort -k4,4nr

# 查看进程排序后内存映射情况
$ pmap -x $pid | sort -n -k3 
# 进程内存地址分析
$ gdb --pid=$pid
$ (gdb) dump memory /tmp/xxx.dump 起始地址 结束地址
$ strings /tmp/xxx.dump | less
```


### 3、容器内存

cgroup是Linux内核提供的⼀种限制和查询⼀组进程资源使⽤的功能，docker⽤它实现了对容器可⽤资源的限制。⼀个容器的某类资源（例如：内存）对应系统中⼀个cgroup⼦系统（subsystem）hierachy中的节点（例如/sys/fs/cgroup/memory/docker下的⼦⽬录）。在这个⽬录中有很多⽂件提供了容器对系统资源使⽤状况的信息。⽐如：memory.stat⽂件包含了容器的内存状况:
```shell
$ cat memory.stat
cache 12288              
rss 57253888
rss_huge 8388608
mapped_file 0
swap 0
pgpgin 44462
pgpgout 39168
pgfault 77640
pgmajfault 0
inactive_anon 0
active_anon 57253888
inactive_file 0
active_file 12288
unevictable 0
hierarchical_memory_limit 9223372036854771712
hierarchical_memsw_limit 9223372036854771712
total_cache 12288
total_rss 57253888
total_rss_huge 8388608
total_mapped_file 0
total_swap 0
total_pgpgin 44462
total_pgpgout 39168
total_pgfault 77640
total_pgmajfault 0
total_inactive_anon 0
total_active_anon 57253888
total_inactive_file 0
total_active_file 12288
total_unevictable 0
```

Linux 中 关于cgroup中memory的文档
- [kernel memory](https://www.kernel.org/doc/Documentation/cgroup-v1/memory.txt)

```
# cgroup中memory类型的分类
memory.usage_in_bytes        已使用的内存总量(包含cache和buffer)(字节)，相当于Linux的used_meme
memory.limit_in_bytes        限制的内存总量(字节)，相当于linux的total_mem
memory.failcnt               申请内存失败次数计数
memory.memsw.usage_in_bytes  已使用的内存总量和swap(字节)
memory.memsw.limit_in_bytes  限制的内存总量和swap(字节)
memory.memsw.ailcnt          申请内存和swap失败次数计数
memory.stat                  内存相关状态

# memory.stat
cache           页缓存，包括 tmpfs(shmem)，单位为字节
rss             匿名和 swap 缓存，不包括 tmpfs(shmem)，单位为字节
mapped_file     映射的文件大小，包括 tmpfs(shmem)，单位为字节
(memory-mapped)     
pgpgin          存入内存中的页数
pgpgout         从内存中读取的页数
swap            swap用量，单位为字节
active_anon     在活跃的最近最少使用(LRU)列表中的匿名和 swap 缓存，包括 tmpfs(shmem)，单位为字节
inactive_anon   不活跃的 LRU 列表中的中的匿名和 swap 缓存，包括 tmpfs(shmem)，单位为字节
active_file     在活跃的 LRU 列表中的 file-backed 内存，单位为字节
inactive_file   不活跃的 LRU 列表中的 file-backed 内存，单位为字节
unevictable     无法再生的内存，单位为字节
hierarchical_memory_limit  包含 memory cgroup 的层级的内存限制，单位为字节
hierarchical_memsw_limit   包含 memory cgroup 的层级的内存加 swap 限制，单位为字节
```

- `kubectl top pod` 命令展示的是cgroup中的内存使用量

- 容器内top查看，是不准的，因为容器的cgroup和namespace隔离技术原因
	- 在pod中通过 `cat /sys/fs/cgroup/memory/memory.stat` 查看整体容器的cgoup 情况，查看其中的 rss + cache 的值

- kubectl top pod的内存计算公式
	- kubectl top pod 得到的内存使用量，并不是cadvisor 中的container_memory_usage_bytes，而是container_memory_working_set_bytes，计算方式为：
	- `container_memory_usage_bytes == container_memory_rss + container_memory_cache + kernel memory`
	- `container_memory_working_set_bytes = container_memory_usage_bytes - total_inactive_file(未激活的匿名缓存页)`
	- `container_memory_working_set_bytes = container_memory_rss + container_memory_cache + kernel memory(一般可忽略) - total_inactive_file`

- 查看容器内进程实际资源占用情况
	- 需要在node宿主机上，看对应进程的资源消耗


https://blog.csdn.net/sinat_26058371/article/details/86536213

