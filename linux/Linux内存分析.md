# Linux 内存分析

## 一、内存定义

### 1、系统内存

我们在查看系统内存使⽤状况时，经常会常⽤free命令。下⾯是在⼀台centos物理机中执⾏free后的
输出:

```shell
$ free -m
              total        used        free      shared  buff/cache   available
Mem:          15470        2202         406          36       12862       12962
Swap:             0           0           0
```
输出包括两⾏：Mem和 Swap 。
其中Mem表示系统中实际的物理内存；Swap表示交换分区（类似windows中的虚拟内存），是硬盘中⼀个独⽴的分区，⽤于在系统内存不够时，临时存储被释放的内存空间中的内容。上⾯的前三列"total"、"used"、"free"分别表示总量，使⽤量和有多少空闲空间。

对于Swap来说，三者的关系很简单，就是total = used + free。(在上⾯的例⼦中，由于这台主机禁⽤swap空间，所以swap的值都是0。) 对于Memory来说，我们发现total = used + free + buff/cache。其中buff和cache分别表示存放了将要写到磁盘中的数据和从磁盘的读取的数据的内存。也就是说内存除了存储进程运⾏所需的运⾏时数据之外，还为了提⾼性能，缓存了⼀部分I/O数据。由于系统的cache和buffer可以被回收，所以可⽤的（available）内存⽐空闲的（free）要⼤。在部署了某些⾼I/O应⽤的主机中，available会⽐free看起来⼤很多，这是由于⼤量的内存空间⽤于缓存对磁盘的I/O数据。

- free命令的所有输出值都是从/proc/meminfo中读出的
```shell
$ cat /proc/meminfo 
MemTotal:       15842292 kB
MemFree:          417648 kB
MemAvailable:   13275572 kB
Buffers:          314792 kB
Cached:         12231084 kB
SwapCached:            0 kB
Active:          3048112 kB
Inactive:       11343544 kB
Active(anon):      21844 kB
Inactive(anon):  1801548 kB
Active(file):    3026268 kB
Inactive(file):  9541996 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Dirty:               644 kB
Writeback:             0 kB
AnonPages:       1733900 kB
Mapped:           872040 kB
Shmem:             37472 kB
Slab:             697224 kB
SReclaimable:     625652 kB
SUnreclaim:        71572 kB
KernelStack:       23828 kB
PageTables:        16896 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:     7921144 kB
Committed_AS:   10523224 kB
VmallocTotal:   34359738367 kB
VmallocUsed:           0 kB
VmallocChunk:          0 kB
Percpu:             3872 kB
HardwareCorrupted:     0 kB
AnonHugePages:   1093632 kB
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
DirectMap4k:      371384 kB
DirectMap2M:    12980224 kB
DirectMap1G:     3145728 kB
```

### 2、进程内存

通过free命令，我们可以看到系统总体的内存使⽤状况。但很多时需要查看特定进程（process）所消耗的内存，这时我们最常⽤的命令是ps，这个命令的输出中有两列与内存相关，分别是VSZ和RSS。
此外还有另外两个类似的指标——PSS和USS，这⾥将这四个⼀并讨论：

|缩写|全称|含义|
|:------:|:------:|:------:|
|VSZ(VSS)|Virtual Memory Size|虚拟内存⼤⼩，表明了该进程可以访问的所有内存，包括被交换的内存和共享库内。VSZ对于判断一个进程实际占用的内存并没有什么帮助。|
|RSS|Resident Set Size|常驻内存集合⼤⼩，表示相应进程在RAM中占⽤了多少内存，并不包含在Swap中占⽤的虚拟内存。包括进程所使⽤的共享库所占⽤的全部内存，即使某个共享库只在内存中加载了⼀次，所有使⽤了它的进程的RSS都会分别把它计算在内。（把所有进程的RSS加到⼀起，通常会⽐实际使⽤的内存⼤，因为⼀些共享库所⽤的内存重复计算了多次。）|
|PSS|Proportional Set Size|与RSS类似，唯⼀的区别是在计算共享库内存是是按⽐例分配。⽐如某个共享库占用了3M内存，同时被3个进程共享，那么在计算这3个进程的PSS时，该共享库这会贡献1兆内存。|
|USS|Unique Set Size|进程独⾃占⽤的物理内存，不包含Swap和共享库。|

这四者的⼤⼩关系是：VSS >= RSS >= PSS >= USS

- 进程的内存使⽤情况可以从/proc/PID/status中读取，⽐如
	- VmSize: 当前的Virtual Memory Size
	- VmRSS: Resident Set Size
	- VmLib：进程所加载的动态库所占⽤的内存⼤⼩
	- `ps -eo pid,comm,rss | awk '{m=$3/1e6;s["*"]+=m;s[$2]+=m} END{for (n in s) printf"%10.3f GB %s\n",s[n],n}' | sort -nr | head -20`   统计前20内存占用
```golang
# 内存统计
$ process_name="kubelet"
$ for i in $(ps -ef | grep ${process_name} | grep -v grep |awk '{print $2}'); do VmRSS=$(cat /proc/$i/status 2>/dev/null | grep VmRSS); [[ ! -z ${VmRSS} ]] && echo "PID: $i    ${VmRSS}"; done | sort -k4,4nr
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

