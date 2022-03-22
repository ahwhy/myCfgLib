# docker 容器

## 一、关于容器的理解

容器本身没有价值，有价值的是"容器编排"

容器，是一种 沙盒技术。顾名思义，沙盒就是能够像一个集装箱一样，把应用"装"起来的技术。
应用与应用之间，就因为有了边界而不至于相互干扰而被装进集装箱的应用，也可以被方便地搬来搬去，也就是 PaaS 理想的状态。

- 这个"边界"的实现手段：
	- 假如，现在要写一个计算加法的小程序，这个程序需要的输入来自于一个文件，计算完成后的结果则输出到另一个文件中
		- 由于计算机只认识 0 和 1，所以无论用哪种语言编写这段代码，后都需要通过某种方式 翻译成二进制文件，才能在计算机操作系统中运行起来
		- 而为了能够让这些代码正常运行，往往还要给它提供数据，比如这个加法程序所需要的输入文件
		- 这些数据加上代码本身的二进制文件，放在磁盘上，就是我们平常所说的一个"程序"，也叫代码的可执行镜像(executable image)
	- 然后，就是在计算机上运行这个"程序"
		- 首先，操作系统从"程序"中发现输入数据保存在一个文件中，所以这些数据就被会加载到内存中待命
		- 同时，操作系统又读取到了计算加法的指令，这时，它就需要指示 CPU 完成加法操作
		- 而 CPU 与内存协作进行加法计算，又会使用寄存器存放数值、内存堆栈保存执行的命令和变量
		- 同时，计算机里还有被打开的文件，以及各种各样的 I/O 设备在不断地 调用中修改自己的状态
		- 就这样，一旦"程序"被执行起来，它就从磁盘上的二进制文件，变成了计算机内存中的数据、寄存器里的值、堆栈中的指令、被打开的文件，以及各种设备的状态信息的一个集合
		- 像这样一个程序运起来后的计算机执行环境的总和，就是进程
	- 对于进程来说，它的静态表现就是程序，平常都安安静静地待在磁盘上
		- 而一旦运行起来，它就变成了计算机里的数据和状态的总和，这就是它的动态表现
		- 而容器技术的核心功能，就是通过约束和修改进程的动态表现，从而为其创造出一个"边界"
		- 对于 Docker 等大多数 Linux 容器来说，Cgroups 技术是用来制造约束的主要手段，而 Namespace 技术则是用来修改进程视图的主要方法

## 二、容器隔离 - Linux Namespace 技术

### Linux Namespace 

- 其是 Linux 系统的底层概念，在内核层实现
	- 即有一些不同类型的命名空间被部署在内核中，各个容器运行在同一个容器主进程并且公用同一个宿主机系统内核

| 隔离类型                                      | 功能                             | 系统调用参数  | 内核版本     |
| --------------------------------------------- | -------------------------------- | ------------- | ------------ |
| MNT Namespace (Mount)                       | 提供磁盘挂载和文件系统的隔离能力 | CLONE_NEWNS   | Linux 2.4.19 |
| IPC Namespace (Inter-Process Communication) | 提供进程间通信的隔离能力         | CLONE_NEWIPC  | Linux 2.6.19 |
| UTS Namespace  (UNIX Timesharing System)      | 提供主机名隔离能力               | CLONE_NEWUTS  | Linux 2.6.19 |
| PID Namespace (Process Identification)      | 提供进程间隔离能力               | CLONE_NEWPID  | Linux 2.4.24 |
| Net Namespace (Network)                     | 提供网络隔离能力                 | CLONE_NEWNET  | Linux 2.4.29 |
| User Namespace (User)                       | 提供用户隔离能力                 | CLONE_NEWUSER | Linux 3.8    |

在理解了 Namespace 的工作方式之后，就会发现跟真实存在的虚拟机不同，在使用 Docker 的时候，并没有一个真正的"Docker 容器"运行在宿主机里面。Docker 项目帮助用户启动的，还是原来的应用进程，只不过在创建这些进程时，Docker 为它们加上了各种各样的 Namespace 参数。
​这时，这些进程就会觉得自己是各自 PID Namespace 里的第 1 号进程，只能看到各自 Mount Namespace 里挂载的目录和文件，只能访问到各自 Network Namespace 里的网络设备，就仿佛运行在一个个"容器"里面，与世隔绝。
Namespace 技术实际上修改了应用进程看待整个计算机"视图"，即它的"视线"被操作系统做了限制，只能"看到"某些指定 的内容。

### 为什么 Docker 项目比虚拟机更受欢迎的原因？

因为，使用虚拟化技术作为应用沙盒，就必须要由 Hypervisor 来负责创建虚拟机，这个虚拟机是真实存在的，并且它里面必须运行一个完整的 Guest OS 才能执行用户的应用进程。这就不可避免地带来了额外的资源消耗和占用。

​根据实验，一个运行着 CentOS 的 KVM 虚拟机启动后，在不做优化的情况下，虚拟机自己就需要占用 100~200 MB 内存。此外，用户应用运行在虚拟机里面，它对宿主机操作系统的调用就不可避免地要经过虚拟化软件的拦截和处理，这本身又是一层性能损耗，尤其对计算资源、网络和磁盘 I/O 的损耗非常大。

​而相比之下，容器化后的用户应用，却依然还是一个宿主机上的普通进程，这就意味着这些因为虚拟化而带来的性能损耗都是不存在的；而另一方面，使用 Namespace 作为隔离手 段的容器并不需要单独的 Guest OS，这就使得容器额外的资源占用几乎可以忽略不计。

### 容器的不足

​基于 Linux Namespace 的隔离机制相比于虚拟化技术也有很多不足之处，其中主要的问题就是：隔离得不彻底。
​首先，既然容器只是运行在宿主机上的一种特殊的进程，那么多个容器之间使用的就还是同 一个宿主机的操作系统内核。
​其次，在 Linux 内核中，有很多资源和对象是不能被 Namespace 化的，典型的例子就是：时间。

### MNT Namespace  - 基于 rootfs 的文件系统

​Mount Namespace 修改的，是容器进程对 文件系统"挂载点"的认知，而它对容器进程 视图的改变，一定是伴随着挂载操作(mount)才能生效。
​每个容器都要有独立的根文件系统有独立的用户空间，以实现在容器里面启动服务并且使用容器的运行环境，即一个宿主机是 ubuntu 的服务器，可以在里面启动一个 centos 运行环境的容器并且在容器里面启动一个 Nginx 服务，此Nginx 运行时使用的运行环境就是 centos系统目录的运行环境，但是在容器里面是不能访问宿主机的资源，宿主机是使用了 chroot 技术把容器锁定到一个指定的运行目录里面。(docker 会优先使用  pivot_root)

​Mount Namespace 正是基于对 chroot 的不断改良才被发明出来的，它也是 Linux 操作系统里的第一个 Namespace。
​为了能够让容器的这个根目录看起来更"真实"，一般会在这个容器的根目录下挂载一个完整操作系统的文件系统，比如 Ubuntu16.04 的 ISO。这样，在容器启动之后， 我们在容器里通过执行 "ls /" 查看根目录下的内容，就是 Ubuntu 16.04 的所有目录和文 件。
​而这个挂载在容器根目录上、用来为容器进程提供隔离后执行环境的文件系统，就是所谓的"容器镜像"。它还有一个更为专业的名字，叫作：rootfs(根文件系统)。一个最常见的 rootfs，或者说容器镜像，会包括如下所示的一些目录和文件，比如 /bin，/etc，/proc 等等

```
# ls / 
bin dev etc home lib lib64 mnt opt proc root run sbin sys tmp usr var
```

另外，需要明确的是，rootfs 只是一个操作系统所包含的文件、配置和目录，并不包括操作系统内核。在 Linux 操作系统中，这两部分是分开存放的，操作系统只有在开机启动时才会加载指定版本的内核镜像。

这就意味着，如果应用程序需要配置内核参数、加载额外的内核模块，以及跟内核进行直接的交互，就需要注意了：这些操作和依赖的对象，都是宿主机操作系统的内核，它对 于该机器上的所有容器来说是一个"全局变量"，牵一发而动全身。

这也是容器相比于虚拟机的主要缺陷之一：毕竟后者不仅有模拟出来的硬件机器充当沙盒， 而且每个沙盒里还运行着一个完整的 Guest OS 给应用随便折腾。
​
不过，正是由于 rootfs 的存在，容器才有了一个被反复宣传至今的重要特性：一致性。由于 rootfs 里打包的不只是应用，而是整个操作系统的文件和目录，也就意味着，应用以及它运行所需要的所有依赖，都被封装在了一起。

事实上，对于大多数开发者而言，他们对应用依赖的理解，一直局限在编程语言层面。比如 Golang 的 Godeps.json。但实际上，一个一直以来很容易被忽视的事实是，对一个应用来 说，操作系统本身才是它运行所需要的最完整的"依赖库"。

有了容器镜像"打包操作系统"的能力，这个最基础的依赖环境也终于变成了应用沙盒的一部分。这就赋予了容器所谓的一致性：无论在本地、云端，还是在一台任何地方的机器上， 用户只需要解压打包好的容器镜像，那么这个应用运行所需要的完整的执行环境就被重现出来了。

这种深入到操作系统级别的运行环境一致性，打通了应用在本地开发和远端执行环境之间难以逾越的鸿沟。

### 镜像的分层 —— Docker 公司在实现 Docker 镜像时并没有沿用以前制作 rootfs 的标准流 程，而是做了一个小小的创新： 

Docker 在镜像的设计中，引入了层(layer)的概念。用户制作镜像的每一步操作，都会生成一个层，也就是一个增量 rootfs，这用到了一种叫作联合文件系统(Union File System)的能力。Union File System 也叫 UnionFS，最主要的功能是将多个不同位置的目录联合挂载。

目前 docker 过使用的文件系统有：aufs devicemapper overlay overlay2

### 容器 volume 卷

容器 volume 卷挂载  使用的是Linux 的绑定挂载(bind mount)机制。它的主要作用是，将一个目录或者文件，而不是整个设备，挂载到一个指定的目录上。并且， 这时在该挂载点上进行的任何操作，只是发生在被挂载的目录或者文件上，而原挂载点的内容则会被隐藏起来且不受影响。

其实，从Linux 内核层来看，绑定挂载实际上是一个 inode 替换的过程。在 Linux 操作系统中，inode 可以理解为存放文件内容的"对象"，而 dentry，也叫 目录项，就是访问这个 inode 所使用的"指针"。

正如上图所示，mount --bind /home /test，会将 /home 挂载到 /test 上。相当于 将 /test 的 dentry，重定向到了 /home 的 inode。这样当修改 /test 目录时，实际修 改的是 /home 目录的 inode。这也就是为何，一旦执行 umount 命令，/test 目录原先的 内容就会恢复：因为修改真正发生在的，是 /home 目录里。

而比如 Docker on Mac，以及 Windows Docker(Hyper-V 实现)，实际上是基于虚拟化技术实现的，

## 三、容器资源限制 - Linux Cgroups 技术

​Linux Cgroups 的全称是 Linux Control Group ，是 Linux 内核中用来为进程设置资源限制的一个重要功能。它最主要的作用，就是限制一个进程 组能够使用的资源上限，包括 CPU、内存、磁盘、网络带宽等等。此外，还能够对进程进行优先级设置，以及将进程挂起和恢复等操作。

### 验证系统cgroups

在 Linux 中，Cgroups 给用户暴露出来的操作接口是文件系统，即它以文件和目录的方式 组织在操作系统的 /sys/fs/cgroup 路径下。以CentOS 7.4为例，它的输出结果，是一系列文件系统目录。

```
# mount -t cgroup 
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd)
cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,perf_event)
cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,blkio)
cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,devices)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,hugetlb)
cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,memory)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpuacct,cpu)
cgroup on /sys/fs/cgroup/net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,net_prio,net_cls)
```

查看CentOS 7.4的内核中，支持的cgroups的功能。

```
# cat /boot/config-3.10.0-693.el7.x86_64 | grep CGROUP
CONFIG_CGROUPS=y
# CONFIG_CGROUP_DEBUG is not set
CONFIG_CGROUP_FREEZER=y
CONFIG_CGROUP_PIDS=y
CONFIG_CGROUP_DEVICE=y
CONFIG_CGROUP_CPUACCT=y
CONFIG_CGROUP_HUGETLB=y
CONFIG_CGROUP_PERF=y
CONFIG_CGROUP_SCHED=y
CONFIG_BLK_CGROUP=y
# CONFIG_DEBUG_BLK_CGROUP is not set
CONFIG_NETFILTER_XT_MATCH_CGROUP=m
CONFIG_NET_CLS_CGROUP=y
CONFIG_NETPRIO_CGROUP=y
```

### cgroups 具体实现

```
blkio，为块设备设定 I/O 限制，一般用于磁盘等设备；
cpu，使用调度程序为 cgroup 任务提供 cpu 的访问；
cpuacct， 产生 cgroup 任务的 cpu 资源报告；
cpuset，为进程分配单独的 CPU 核和对应的内存节点；
memory，设置每个 cgroup 的内存限制以及产生内存资源报告；
devices，允许或拒绝 cgroup 任务对设备的访问；
freezer，暂停和恢复 cgroup 任务；
net_cls，标记每个网络包以供 cgroup 方便使用；
ns，命名空间子系统；
perf_event，增加了对每 group 的监测跟踪的能力，可以检测属于某个特定的group的所有线程以及运行在特定CPU上的线程。
```

### 应用实例

在 /sys/fs/cgroup 下面有很多诸如 cpuset、cpu、 memory 这样的子目录， 也叫子系统。这些都是这台机器当前可以被 Cgroups 进行限制的资源种类。而在子系统 对应的资源种类下，就可以看到该类资源具体可以被限制的方法。比如，对 CPU 子系统 来说，就可以看到如下几个配置文件。

```
# ls /sys/fs/cgroup/cpu/
cgroup.clone_children  cgroup.procs          cpuacct.stat   cpuacct.usage_percpu  cpu.cfs_quota_us  cpu.rt_runtime_us  cpu.stat  kubepods           release_agent  tasks
cgroup.event_control   cgroup.sane_behavior  cpuacct.usage  cpu.cfs_period_us     cpu.rt_period_us  cpu.shares         docker    notify_on_release  system.slice   user.slice
```

其中 cfs_period 和 cfs_quota ，这两个参数需要组合使用，可以用来限制进程在长度为 cfs_period 的一段时间内，只能被分配到总量为 cfs_quota 的 CPU 时间。首先，要在对应的子系统下面创建一个目录，比如，现在进入 /sys/fs/cgroup/cpu 目录 下：

```
# mkdir /sys/fs/cgroup/cpu/test && cd /sys/fs/cgroup/cpu/test
# ls
cgroup.clone_children  cgroup.procs  cpuacct.usage         cpu.cfs_period_us  cpu.rt_period_us   cpu.shares  notify_on_release  cgroup.event_control   cpuacct.stat  cpuacct.usage_percpu  cpu.cfs_quota_us   cpu.rt_runtime_us  cpu.stat    tasks
```

这个目录就称为一个"控制组"。可以会发现，操作系统会在新创建的 test 目录 下，自动生成该子系统对应的资源限制文件。然后后台执行这样一条脚本：

```
#  while : ; do : ; done &
[1] 148615
```

它执行了一个死循环，可以把计算机的 CPU 吃到 100%，根据它的输出，可以看到这个脚本在后台运行的进程号(PID)是 148615，可以用 top 指令来确认一下 CPU 有没有被打满：

```
# top
top - 16:01:08 up 8 days,  1:30,  3 users,  load average: 0.90, 0.72, 0.63
Tasks: 607 total,   2 running, 572 sleeping,   0 stopped,  33 zombie
%Cpu(s):  4.6 us,  0.7 sy,  0.0 ni, 94.7 id,  0.0 wa,  0.0 hi,  0.1 si,  0.0 st

   PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                                 
148615 root      20   0  118948   4228    316 R 100.0  0.0   0:32.01 bash           
```

而此时，可以通过查看 container 目录下的文件，看到 container 控制组里的 CPU quota 还没有任何限制(即：-1)，CPU period 则是默认的 100 ms(100000 us)：

```
# cat /sys/fs/cgroup/cpu/test/cpu.cfs_quota_us 
-1
# cat /sys/fs/cgroup/cpu/test/cpu.cfs_period_us 
100000
```

可以通过修改这些文件的内容来设置限制，比如，向 test 组里的 cfs_quota 文件写入 20 ms(20000 us)：

```
 $ echo 20000 > /sys/fs/cgroup/cpu/test/cpu.cfs_quota_us
```

这它意味着在每 100 ms 的时间里，被该 控制组限制的进程只能使用 20 ms 的 CPU 时间，也就是说这个进程只能使用到 20% 的 CPU 带宽。接下来，把被限制的进程的 PID 写入 test 组里的 tasks 文件，上面的设置就会 对该进程生效了。

```
# echo 148615 > /sys/fs/cgroup/cpu/test/tasks 
```

使用 top 可以看到，计算机的 CPU 使用率立刻降到了 20%(%Cpu : 20.5)。

```
# top
top - 16:03:16 up 8 days,  1:32,  3 users,  load average: 1.22, 1.09, 0.79
Tasks: 599 total,   2 running, 564 sleeping,   0 stopped,  33 zombie
%Cpu(s):  2.0 us,  0.7 sy,  0.0 ni, 97.2 id,  0.0 wa,  0.0 hi,  0.1 si,  0.0 st

   PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                                 
148615 root      20   0  118948   4228    316 R  20.5  0.0   2:17.05 bash 
```

简单地理解，Linux Cgroups 就是一个子系统目录加上 一组资源限制文件的组合。而对于 Docker 等 Linux 容器项目来说，它们只需要在每个子系统下面，为每个容器创建一个控制组(即创建一个新目录)，然后在启动容器进程之后， 把这个进程的 PID 填写到对应控制组的 tasks 文件中就可以了。

一个正在运行的 Docker 容器，其实就是一个启用了 多个 Linux Namespace 的应用进程，而这个进程能够使用的资源量，则受 Cgroups 配置 的限制。
这也是容器技术中一个非常重要的概念，即：容器是一个"单进程"模型。

### 容器的不足

跟 Namespace 的情况类似，Cgroups 对资源的限制能力也有很多不完善的地方， 被提及多的自然是 /proc 文件系统的问题。
众所周知，Linux 下的 /proc 目录存储的是记录当前内核运行状态的一系列特殊文件，用户 可以通过访问这些文件，查看系统以及当前正在运行的进程的信息，比如 CPU 使用情况、 内存占用率等，这些文件也是 top 指令查看系统信息的主要数据来源。

如果在容器里执行 top 指令，就会发现，它显示的信息居然是宿主机的 CPU 和内 存数据，而不是当前容器的数据。
造成这个问题的原因就是，/proc 文件系统并不知道用户通过 Cgroups 给这个容器做了什 么样的资源限制，即：/proc 文件系统不了解 Cgroups 限制的存在。
生产环境中，这个问题必须进行修正，否则应用程序在容器里读取到的 CPU 核数、可用 内存等信息都是宿主机上的数据，这会给应用的运行带来非常大的困惑和风险。这也是在企 业中，容器化应用碰到的一个常见问题，也是容器相较于虚拟机另一个不尽如人意的地方。

### docker

docker并不是容器技术，docker只是容器的UI，manger，管理系统

### Docker exec 是怎么做到进入容器里的呢

Linux Namespace 创建的隔离空间虽然看不见摸不着，但一个进程的 Namespace 信息在宿主机上是确确实实存在的，并且是以一个文件的方式存在。
比如，通过如下指令，可以看到当前正在运行的 Docker 容器的进程号(PID)是 25686：

```
#  docker inspect --format '{{ .State.Pid }}'  4ddf4638572d 
25686
```

可以通过查看宿主机的 proc 文件，看到这个 25686 进程的所有 Namespace 对 应的文件：

```
#ls -l  /proc/25686/ns 
total 0 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 cgroup -> cgroup:[4026531835] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 ipc -> ipc:[4026532278] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 mnt -> mnt:[4026532276] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 net -> net:[4026532281] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 pid -> pid:[4026532279] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 pid_for_children -> pid:[4026532279] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 user -> user:[4026531837] 
lrwxrwxrwx 1 root root 0 Aug 13 14:05 uts -> uts:[4026532277]
```

可以看到，一个进程的每种 Linux Namespace，都在它对应的 /proc/[进程号]/ns 下有一 个对应的虚拟文件，并且链接到一个真实的 Namespace 文件上。
有了这样一个可以"hold 住"所有 Linux Namespace 的文件，我们就可以对 Namespace 做一些很有意义事情了，比如：加入到一个已经存在的 Namespace 当中。
这也就意味着：一个进程，可以选择加入到某个进程已有的 Namespace 当中，从而达 到"进入"这个进程所在容器的目的，这正是 docker exec 的实现原理。

### 总结

综上所述，容器只是一种特殊的进程容器，实际上是一个由 Linux Namespace、 Linux Cgroups 和 rootfs 三种技术构建出来的进程的隔离环境。

- 从这个结构中不难看出，一个正在运行的 Linux 容器，其实可以被"一分为二"地看待
	- 一组联合挂载在 /var/lib/docker/aufs(容器存储引擎)/mnt 上的 rootfs，这一部分我们称为"容器镜 像"(Container Image)，是容器的静态视图
	- 一个由 Namespace+Cgroups 构成的隔离环境，这一部分我们称为"容器运行 时"(Container Runtime)，是容器的动态视图
	- 镜像在没有运行的时候，是一个静态的文件系统，一但运行起来就是一个容器，具有独立的用户空间，内部有一个id为1的进程
	- 因为容器的隔离不彻底，所以需要极端的彻底隔离的场景下，传统的主机级虚拟化，依然有用武之地

## 四、容器编排 -  Kubernetes

Kubernetes 项目的架构，跟它的原型项目 Borg 非常类似，都由 Master 和 Node 两种节点组成，而这两种角色分别对应着控制节点和计算节点。
其中，控制节点，即 Master 节点，由三个紧密协作的独立组件组合而成，它们分别是负责 API 服务的 kube-apiserver、负责调度的 kube-scheduler，以及负责容器编排的 kubecontroller-manager。整个集群的持久化数据，则由 kube-apiserver 处理后保存在 Etcd 中。

而计算节点上最核心的部分，则是一个叫作 kubelet 的组件。
在 Kubernetes 项目中，kubelet 主要负责同容器运行时(比如 Docker 项目)打交道。 而这个交互所依赖的，是一个称作 CRI(Container Runtime Interface)的远程调用接 口，这个接口定义了容器运行时的各项核心操作，比如：启动一个容器需要的所有参数。
这也是为何，Kubernetes 项目并不关心你部署的是什么容器运行时、使用的什么技术实 现，只要你的这个容器运行时能够运行标准的容器镜像，它就可以通过实现 CRI 接入到 Kubernetes 项目当中。
而具体的容器运行时，比如 Docker 项目，则一般通过 OCI 这个容器运行时规范同底层的 Linux 操作系统进行交互，即：把 CRI 请求翻译成对 Linux 操作系统的调用(操作 Linux Namespace 和 Cgroups 等)

此外，kubelet 还通过 gRPC 协议同一个叫作 Device Plugin 的插件进行交互。这个插 件，是 Kubernetes 项目用来管理 GPU 等宿主机物理设备的主要组件，也是基于 Kubernetes 项目进行机器学习训练、高性能作业支持等工作必须关注的功能

kubelet 的另一个重要功能，则是调用网络插件和存储插件为容器配置网络和持久化存 储。这两个插件与 kubelet 进行交互的接口，分别是 CNI(Container Networking Interface)和 CSI(Container Storage Interface)。

``` 
   # kubernetes的接口
   Container Storage Interface (CSI)
   Container Network Interface (CNI)
   Container Runtime Interface (CRI)
   Container Volume  Interface (CVI)
   Oracle Call Interface  (OCI)
```

除了应用与应用之间的关系外，应用运行的形态是影响"如何容器化这个应用"的第二个重 要因素。

Kubernetes 定义了新的、基于 Pod 改进后的对象。比如 Job，用来描述一次性运 行的 Pod(比如，大数据任务)；

相比之下，在 Kubernetes 项目中，我们所推崇的使用方法是：

首先，通过一个"编排对象"，比如 Pod、Job、CronJob 等，来描述你试图管理的应 用；
然后，再为它定义一些"服务对象"，比如 Service、Secret、Horizontal Pod Autoscaler(自动水平扩展器)等。这些对象，会负责具体的平台级功能。这种使用方法，就是所谓的"声明式 API"。这种 API 对应的"编排对象"和"服务对 象"，都是 Kubernetes 项目中的 API 对象(API Object)。

在 Kubernetes 之前，很多项目都没办法管理"有状态"的容器，即，不能从一台宿主 机"迁移"到另一台宿主机上的容器。
要知道迁移的是容器的rootfs，但是一些动态视图是没 有办法伴随迁移一同进行迁移的。到目前为止，迁移都是做不到的，只能删除后在新的节点上重新创建