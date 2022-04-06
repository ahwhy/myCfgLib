# Linux 各目录及作用

## 根目录 文件系统 

通常情况下，根文件系统所占空间一般比较小，其中的绝大部分文件都不需要经常改动，因此 严格的文件和一个小的不经常改变的文件系统不容易损坏。
除了可能的一个叫/vmlinuz 标准的系统引导映像之外，根目录一般不含任何文件，所有其他文件在根文件系统的子目录中。

```
/bin 二进制可执行命令
/dev 设备特殊文件
/etc/rc.d 启动的配置文件和脚本
/home 用户主目录的基点，比如用户 user 的主目录就是/home/user，可以用~user 表示
/lib 标准程序设计库，又叫动态链接共享库，作用类似 windows 里的.dll 文件
/sbin 超级管理命令，这里存放的是系统管理员使用的管理程序
/tmp 公共的临时文件存储点
/root 系统管理员的主目录
/mnt 系统提供这个目录是让用户临时挂载其他的文件系统
/lost+found 这个目录平时是空的，系统非正常关机而留下"无家可归"的文件(windows 里的 .chk)的位置
/proc 虚拟的目录，是系统内存的映射；可直接访问这个目录来获取系统信息
/var 某些大文件的溢出区，比如各种服务的日志文件
/usr 最庞大的目录，要用到的应用程序和文件几乎都在这个目录，其中包含:
    /usr/x11R6 存放 xwindow 的目录
    /usr/bin 众多的应用程序
    /usr/sbin 超级用户的一些管理程序
    /usr/doclinux 文档
    /usr/includelinux 下开发和编译应用程序所需要的头文件
    /usr/lib 常用的动态链接库和软件包的配置文件
    /usr/man 帮助文档
    /usr/src 源代码，linux 内核的源代码就放在/usr/src/linux 里
    /usr/local/bin 本地增加的命令
    /usr/local/lib 本地增加的库根文件系统
```


### 1、/bin 目录
/bin 目录包含了引导启动所需的命令或普通用户可能用的命令(可能在引导启动后)。这些命令都是二进制文件的可执行程序(bin 是 binary--二进制的简称)，多是系统中重要的系统文件。

### 2、/sbin 目录
/sbin 目录类似/bin，也用于存储二进制文件。因为其中的大部分文件多是系统管理员使用的基本的系统程序，所以虽然普通用户必要且允许时可以使用，但一般不给普通用户使用。

### 3、/etc 目录
/etc 目录存放着各种系统配置文件，其中包括了用户信息文件/etc/passwd，系统初始化文件/etc/rc/等。linux 正是*这些文件才得以正常地运行。

### 4、/root 目录
/root 目录是超级用户的目录。

### 5、/lib 目录
/lib 目录是根文件系统上的程序所需的共享库，存放了根文件系统程序运行所需的共享文件。这些文件包含了可被许多程序共享的代码，以避免每个程序都包含有相同的子程序的副本，故可以使得可执行文件变得更小，节省空间。

### 6、/lib/modules 目录
/lib/modules 目录包含系统核心可加载各种模块，尤其是那些在恢复损坏的系统时重新引导系统所需的模块(例如网络和文件系统驱动)。

### 7、/dev 目录
/dev 目录存放了设备文件，即设备驱动程序，用户通过这些文件访问外部设备。比如，用户可以通过访问/dev/mouse 来访问鼠标的输入，就像访问其他文件一样。

### 8、/tmp 目录
/tmp 目录存放程序在运行时产生的信息和数据。但在引导启动后，运行的程序最好使用/var/tmp 来代替/tmp，因为前者可能拥有一个更大的磁盘空间。

### 9、/boot 目录
/boot 目录存放引导加载器(bootstraploader)使用的文件，如 lilo，核心映像也经常放在这里，而不是放在根目录中。但是如果有许多核心映像，这个目录就可能变得很大，这时使用单独的文件系统会更好一些。还有一点要注意的是，要确保核心映像必须在 die硬盘的前 1024 柱面内。

### 10、/mnt 目录
/mnt 目录是系统管理员临时安装(mount)文件系统的安装点。程序并不自动支持安装到/mnt。/mnt 下面可以分为许多子目录，例如/mnt/dosa 可能是使用 msdos 文件系统的软驱，而/mnt/exta 可能是使用 ext2 文件系统的软驱，/mnt/cdrom 光驱等等。

### 11、/proc,/usr,/var,/home 目录
其他文件系统的安装点。


## /etc 文件系统 

/etc 目录包含各种系统配置文件，以及其他的程序(阅读该程序的 man 页来了解)。
许多网络配置文件也在/etc 中。

### 1、/etc/rc 或/etc/rc.d 或/etc/rc?.d
启动、或改变运行级时运行的脚本或脚本的目录。

### 2、/etc/passwd
用户数据库，其中的域给出了用户名、真实姓名、用户起始目录、加密口令和用户的其他信息。

### 3、/etc/fdprm
软盘参数表，用以说明不同的软盘格式。可用 setfdprm 进行设置。更多的信息见 setfdprm 的帮助页。

### 4、/etc/fstab
指定启动时需要自动安装的文件系统列表。也包括用 swapon-a 启用的 swap 区的信息。

### 5、/etc/group
类似/etc/passwd，但说明的不是用户信息而是组的信息。包括组的各种数据。

### 6、/etc/inittab
init 的配置文件。

### 7、/etc/issue
包括用户在登录提示符前的输出信息。通常包括系统的一段短说明或欢迎信息。具体内容由系统管理员确定。

### 8、/etc/magic
"file"的配置文件。包含不同文件格式的说明，"file"基于它猜测文件类型。

### 9、/etc/motd
motd 是 messageoftheday 的缩写，用户成功登录后自动输出。内容由系统管理员确定。常用于通告信息，如计划关机时间的警告等。

### 10、/etc/mtab
当前安装的文件系统列表。由脚本(script)初始化，并由 mount 命令自动更新。当需要一个当前安装的文件系统的列表时使用(例如 df 命令)。

### 11、/etc/shadow
在安装了影子(shadow)口令软件的系统上的影子口令文件。影子口令文件将/etc/passwd 文件中的加密口令移动到/etc/shadow 中，而后者只对超级用户(root)可读。这使破译口令更困难，以此增加系统的安全性。

### 12、/etc/login.defs
login 命令的配置文件。

### 13、/etc/printcap
类似/etc/termcap，但针对打印机。语法不同。

### 14、/etc/profile、/etc/csh.login、/etc/csh.cshrc
登录或启动时 bourne 或 cshells 执行的文件。这允许系统管理员为所有用户建立全局缺省环境。

### 15、/etc/securetty
确认安全终端，即哪个终端允许超级用户(root)登录。一般只列出虚拟控制台，这样就不可能(至少很困难)通过调制解调器(moden)或网络闯入系统并得到超级用户特权。

### 16、/etc/shells
列出可以使用的 shell。chsh 命令允许用户在本文件指定范围内改变登录的 shell。提供一台机器ftp服务的服务进程ftpd检查用户shell是否列在/etc/shells文件中，如果不是，将不允许该用户登录。

### 17、/etc/termcap
终端性能数据库。说明不同的终端用什么"转义序列"控制。写程序时不直接输出转义序列(这样只能工作于特定品牌的终端)，而是从/etc/termcap 中查找要做的工作的正确序列。
这样，多数的程序可以在多数终端上运行。


## /dev 文件系统 

/dev 目录包括所有设备的设备文件。设备文件用特定的约定命名，这在设备列表中说明。设备文件在安装时由系统产生，以后可以用 /dev/makedev 描述。
/dev/makedev.local 是系统管理员为本地设备文件(或连接)写的描述文稿(即如一些非标准设备驱动不是标准makedev 的一部分)。

### 1、/dev/console
系统控制台，也就是直接和系统连接的监视器。

### 2、/dev/hd
ide 硬盘驱动程序接口。如: /dev/hda 指的是第一个硬盘，had1 则是指/dev/hda 的第一个分区。如系统中有其他的硬盘，则依次为/dev/hdb、/dev/hdc、......；如有多个分区则依次为hda1、hda2......

### 3、/dev/sd
scsi 磁盘驱动程序接口。如有系统有 scsi 硬盘，就不会访问/dev/had，而会访问/dev/sda。

### 4、/dev/fd
软驱设备驱动程序。如: /dev/fd0 指系统的第一个软盘，也就是通常所说的 a: 盘，/dev/fd1 指第二个软盘，......而/dev/fd1h1440 则表示访问驱动器 1 中的 4.5 高密盘。

### 5、/dev/st
scsi 磁带驱动器驱动程序。

### 6、/dev/tty
提供虚拟控制台支持。如: /dev/tty1 指的是系统的第一个虚拟控制台，/dev/tty2 则是系统的第二个虚拟控制台。

### 7、/dev/pty
提供远程登陆伪终端支持。在进行 telnet 登录时就要用到/dev/pty 设备。

### 8、/dev/ttys
计算机串行接口，对于 dos 来说就是"com1"口。

### 9、/dev/cua
计算机串行接口，与调制解调器一起使用的设备。

### 10、/dev/null
"黑洞"，所有写入该设备的信息都将消失。例如: 当想要将屏幕上的输出信息隐藏起来时，只要将输出信息输入到/dev/null 中即可。


## /usr 文件系统 

/usr 是个很重要的目录，通常这一文件系统很大，因为所有程序安装在这里。/usr 里的所有文件一般来自 linux 发行版(distribution)；
本地安装的程序和其他东西在 /usr/local 下，因为这样可以在升级新版系统或新发行版时无须重新安装全部程序。
/usr 目录下的许多内容是可选的，但这些功能会使用户使用系统更加有效。/usr 可容纳许多大型的软件包和它们的配置文件。

### 1、/usr/x11r6
包含 xwindow 系统的所有可执行程序、配置文件和支持文件。为简化 x 的开发和安装，x 的文件没有集成到系统中。
xwindow 系统是一个功能强大的图形环境，提供了大量的图形工具程序。用户如果对 microsoftwindows 或 machintosh 比较熟悉的话，就不会对 xwindow 系统感到束手无策了。

### 2、/usr/x386
类似/usr/x11r6，但是是专门给 x11release5 的。

### 3、/usr/bin
集中了几乎所有用户命令，是系统的软件库。另有些命令在/bin 或/usr/local/bin 中。

### 4、/usr/sbin
包括了根文件系统不必要的系统管理命令，例如多数服务程序。

### 5、/usr/share/man、/usr/share/info、/usr/share/doc
这些目录包含所有手册页、gnu 信息文档和各种其他文档文件。
每个联机手册的"节"都有两个子目录。例如: /usr/share/man/man1 中包含联机手册第一节的源码(没有格式化的原始文件)，/usr/share/man/cat1 包含第一节已格式化的内容。联机手册分为以下九节: 命令、系统调用、库函数、设备、文件格式、游戏、宏软件包、系统管理和核心程序。

### 6、/usr/include
包含了 c 语言的头文件，这些文件多以.h 结尾，用来描述 c 语言程序中用到的数据结构、子过程和常量。为了保持一致性，这实际上应该放在/usr/lib 下，但习惯上一直沿用了这个名字。

### 7、/usr/lib
包含了程序或子系统的不变的数据文件，包括一些 site-wide 配置文件。
名字 lib 来源于库(library)；编程的原始库也存在/usr/lib 里。当编译程序时，程序便会和其中的库进行连接。也有许多程序把配置文件存入其中。

### 8、/usr/local
本地安装的软件和其他文件放在这里。这与/usr 很相似。用户可能会在这发现一些比较大的软件包，如 tex、emacs 等。


## /var 文件系统 
/var 包含系统一般运行时要改变的数据。通常这些数据所在的目录的大小是要经常变化或扩充的。原来/var 目录中有些内容是在/usr 中的，但为了保持/usr 目录的相对稳定，就把那些需要经常改变的目录放到/var 中了。
每个系统是特定的，即不通过网络与其他计算机共享。

### 1、/var/cache/man
包括了格式化过的帮助(man)页。
帮助页的源文件一般存在/usr/share/man/man 中；有些 man页可能有预格式化的版本，存在/usr/share/man/cat 中。
而其他的 man 页在第一次看时都需要格式化，格式化完的版本存在/var/cache/man 中，这样其他人再看相同的页时就无须等待格式化了。

### 2、/var/lib
存放系统正常运行时要改变的文件。

### 3、/var/local
存放/usr/local 中安装的程序的可变数据(即系统管理员安装的程序)。注意，如果必要，即使本地安装的程序也会使用其他/var 目录，例如/var/lock。

### 4、/var/lock
锁定文件。许多程序遵循在/var/lock 中产生一个锁定文件的约定，以用来支持他们正在使用某个特定的设备或文件。其他程序注意到这个锁定文件时，就不会再使用这个设备或文件。

### 5、/var/log
各种程序的日志(log)文件，尤其是 login(/var/log/wtmplog 纪录所有到系统的登录和注销)和 syslog(/var/log/messages 纪录存储所有核心和系统程序信息)。
/var/log 里的文件经常不确定地增长，应该定期清除。

### 6、/var/run
保存在下一次系统引导前有效的关于系统的信息文件。例如，/var/run/utmp 包含当前登录的用户的信息。

### 7、/var/spool
放置"假脱机(spool)"程序的目录，如 mail、news、打印队列和其他队列工作的目录。
每个不同的 spool 在/var/spool 下有自己的子目录，例如，用户的邮箱就存放在/var/spool/mail 中。

### 8、/var/tmp
比/tmp 允许更大的或需要存在较长时间的临时文件。注意系统管理员可能不允许/var/tmp 有很旧的文件。


## /proc 文件系统
 
/proc 文件系统是一个伪的文件系统，就是说它是一个实际上不存在的目录，因而这是一个非常特殊的目录。
它并不存在于某个磁盘上，而是由核心在内存中产生。这个目录用于提供关于系统的信息。
下面说明一些最重要的文件和目录(/proc 文件系统在 procman 页中有更详细的说明)。

### 1、/proc/x
关于进程 x 的信息目录，这一 x 是这一进程的标识号。每个进程在/proc 下有一个名为自己进程号的目录。

### 2、/proc/cpuinfo
存放处理器(cpu)的信息，如 cpu 的类型、制造商、型号和性能等。

### 3、/proc/devices
当前运行的核心配置的设备驱动的列表。

### 4、/proc/dma
显示当前使用的 dma 通道。

### 5、/proc/filesystems
核心配置的文件系统信息。

### 6、/proc/interrupts
显示被占用的中断信息和占用者的信息，以及被占用的数量。

### 7、/proc/ioports
当前使用的 i/o 端口。

### 8、/proc/kcore
系统物理内存映像。与物理内存大小完全一样，然而实际上没有占用这么多内存；它仅仅是在程序访问它时才被创建。(注意: 除非把它拷贝到什么地方，否则/proc 下没有任何东西占用任何磁盘空间。)

### 9、/proc/kmsg
核心输出的消息，也会被送到 syslog。

### 10、/proc/ksyms
核心符号表。

### 11、/proc/loadavg
系统"平均负载"；3 个没有意义的指示器指出系统当前的工作量。

### 12、/proc/meminfo
各种存储器使用信息，包括物理内存和交换分区(swap)。

### 13、/proc/modules
存放当前加载了哪些核心模块信息。

### 14、/proc/net
网络协议状态信息。

#### 主机级别的流量信息 /proc/net/snmp && /proc/net/netstat
- `/proc/net/snmp` 文件提供 主机各层的IP、ICMP、ICMPMsg、TCP、UDP详细数据

- `/proc/net/netstat` 文件提供 主机的收发包数、收包字节数据
	- 查看 SYN 丢包是否全都是 PAWS 校验失败导致 `cat /proc/net/netstat | grep TcpE| awk '{print $15, $22}'`

- `/proc/net/dev` 查看网卡中数据包的转发情况

#### 进程级别的流量信息 /proc/net/snmp && /proc/net/netstat
- `/proc/net/tcp` 文件提供 tcp的四元组和 inode信息

- `/proc/net/udp` 文件提供 udp的四元组和 inode信息

- `/proc/{pid}/fd/` 文件提供 pid 及 socket inode文件描述符的映射关系
	- `netstat -antp | grep pid | wc -l` 用netstat来统计进程的connection数量
	- `cd /proc/$pid/fd && ls -al | grep socket | wc -l` 到/proc/$pid/fd下统计socket类型的fd数量
	- [netstat统计的tcp连接数与⁄proc⁄pid⁄fd下socket类型fd数量不一致的分析](https://hengyun.tech/netstat-difference-proc-fd-socket-stat/)

### 15、/proc/self
存放到查看/proc 的程序的进程目录的符号连接。当 2 个进程查看/proc 时，这将会是不同的连接。这主要便于程序得到它自己的进程目录。

### 16、/proc/stat
系统的不同状态，例如，系统启动后页面发生错误的次数。

### 17、/proc/uptime
系统启动的时间长度。

### 18、/proc/version
核心版本。

### 19、/proc/{pid}/cgroup 进程cgroup信息
- `/proc/{pid}/cgroup` 文件提供 进程cgroup信息，可用于获取容器信息
	- [Kubernetes 根据 PID 获取 Pod 名称](https://www.jianshu.com/p/1ea7ec6f98ed)

- 容器cgroup残留
	- `kubelet[1264599]: I0218 10:11:57.155941 1264599 kubelet_pods.go:981] Pod "xxxx-xxxx(6923ffa2-3c15-4aa7-8f15-7a18a4b3745b)" is terminated, but pod cgroup sandbox has not been cleaned up`
	- 在节点查询到上面的日志，定位到有cgroup残留
	- 可以在 节点上手动删除一下terminating中的几个pod的这个cgroup
	- `rmdir /sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod6923ffa2_3c15_4aa7_8f15_7a18a4b3745b.slice`
