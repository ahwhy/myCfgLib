# 基于官方二进制文件部署高可用kubernetes集群

## 准备软件包以及参考文档

- [参考实验](http://blog.mykernel.cn/2021/02/05/%E9%AB%98%E5%8F%AF%E7%94%A8Kubernetes/#%E5%9F%BA%E4%BA%8Ek8s%E5%AE%98%E6%96%B9%E4%BA%8C%E8%BF%9B%E5%88%B6%E7%A8%8B%E5%BA%8F%E9%83%A8%E7%BD%B2k8s%E9%9B%86%E7%BE%A4)

- [kubernetes官方项目地址](https://github.com/kubernetes/kubernetes)



## 基本信息

系统版本：Ubuntu 18.04.4 

kubernetes版本：1.20.2

集群信息：
| 节点名称        | IP             | 命令                                     | 角色 |
| --------------- | -------------- | ---------------------------------------- | ---- |
| kube20-master01 | 192.168.137.51 | hostnamectl set-hostname kube20-master01 | Etcd |
| kube20-master02 | 192.168.137.52 | hostnamectl set-hostname kube20-master02 | Etcd |
| kube20-master03 | 192.168.137.53 | hostnamectl set-hostname kube20-master03 | Etcd |
| kube20-node01   | 192.168.137.54 | hostnamectl set-hostname kube20-node01   |      |



## 初始化系统环境

### 主机名host解析

```
# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	Base-Ubuntu

# The following lines are desirable for IPv6 capable hosts

::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.137.51 kube20-master01

192.168.137.52 kube20-master02

192.168.137.53 kube20-master03

192.168.137.54 kube20-master04
```



###  各节点ipvs模型

Centos版

```
# /etc/sysconfig/modules/ipvs.modules
#!/bin/bash
ipvs_mods_dir="/usr/lib/modules/$(uname -r)/kernel/net/netfilter/ipvs" 
#  /usr/lib/modules/ 存在多个内核版本。$(uname -r) 当前内核版本 kernel/net/netfilter/ipvs 里面 内核 模块名.ko.xz
for mod in $(ls $ipvs_mods_dir | grep -o "^[^.]*"); do 
# .ko结尾，去掉.ko
    /sbin/modinfo -F filename $mod  &> /dev/null # 探测模块存在
    if [ $? -eq 0 ]; then
        /sbin/modprobe $mod
    fi
done

# chmod +x /etc/sysconfig/modules/ipvs.modules
# /etc/sysconfig/modules/ipvs.modules
```

Ubuntu版

```
# 临时启用
# for i in $(ls /lib/modules/$(uname -r)/kernel/net/netfilter/ipvs|grep -o "^[^.]*");do echo $i; /sbin/modinfo -F filename $i >/dev/null 2>&1 && /sbin/modprobe $i; done

# 永久启用
# ls /lib/modules/$(uname -r)/kernel/net/netfilter/ipvs|grep -o "^[^.]*" >> /etc/modules

# 检查是否开启
# lsmod | grep ip_vs
```

### 系统资源限制优化

```
#vim /etc/security/limits.conf
root  soft  core      unlimited
root  hard  core      unlimited
root  soft  nproc     1000000
root  hard  nproc     1000000
root  soft  nofile    1000000
root  hard  nofile    1000000
root  soft  memlock   32000
root  hard  memlock   32000
root  soft  msgqueue  8192000
root  hard  msgqueue  8192000
*     soft  core      unlimited
*     hard  core      unlimited
*     soft  nproc     1000000
*     hard  nproc     1000000
*     soft  nofile    1000000
*     hard  nofile    1000000
*     soft  memlock   32000
*     hard  memlock   32000
*     soft  msgqueue  8192000
*     hard  msgqueue  8192000
```

### 内核参数优化

```
# 1：开启严格的反向路径校验。对每个进来的数据包，校验其反向路径是否是最佳路径。如果反向路径不是最佳路径，则直接丢弃该数据包。
#  减少DDoS攻击,校验数据包的反向路径，如果反向路径不合适，则直接丢弃数据包，避免过多的无效连接消耗系统资源。
#  防止IP Spoofing,校验数据包的反向路径，如果客户端伪造的源IP地址对应的反向路径不在路由表中，或者反向路径不是最佳路径，则直接丢弃数据包，不会向伪造IP的客户端回复响应。
net.ipv4.conf.default.rp_filter = 1
# 监听非本机, 避免切换VIP后在启动服务, 用户就会中断请求。
net.ipv4.ip_nonlocal_bind = 1
# 转发
net.ipv4.ip_forward = 1
#处理无源路由的包
net.ipv4.conf.default.accept_source_route = 0
#关闭sysrq功能
kernel.sysrq = 0
#core文件名中添加pid作为扩展名
kernel.core_uses_pid = 1
# tcp_syncookies是一个开关，是否打开SYN Cookie功能，该功能可以防止部分SYN攻击。tcp_synack_retries和tcp_syn_retries定义SYN的重试次数。
net.ipv4.tcp_syncookies = 1
# docker
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-arptables = 1
# docker运行时，需要设置为1
fs.may_detach_mounts = 1
#修改消息队列长度
kernel.msgmnb = 65536
kernel.msgmax = 65536
#设置最大内存共享段大小bytes
kernel.shmmax = 68719476736
kernel.shmall = 4294967296

net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_sack = 1
net.core.wmem_default = 8388608
net.core.rmem_default = 8388608
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.netdev_max_backlog = 262144
# net.core.somaxconn 是Linux中的一个kernel参数，表示socket监听（listen）的backlog上限。什么是backlog呢？backlog就是socket的监听队列，当一个请求（request）尚未被处理或建立时，他会进入backlog。而socket server可以一次性处理backlog中的所有请求，处理后的请求不再位于监听队列中。当server处理请求较慢，以至于监听队列被填满后，新来的请求会被拒绝。 
net.core.somaxconn = 20480
net.core.optmem_max = 81920
# tcp_max_syn_backlog 进入SYN包的最大请求队列.默认1024.对重负载服务器,增加该值显然有好处.
net.ipv4.tcp_max_syn_backlog = 262144
net.ipv4.tcp_syn_retries = 3
net.ipv4.tcp_retries1 = 3
net.ipv4.tcp_retries2 = 15
# 在使用 iptables 做 nat 时，发现内网机器 ping 某个域名 ping 的通，而使用 curl 测试不通, 原来是 net.ipv4.tcp_timestamps 设置了为 1 ，即启用时间戳
net.ipv4.tcp_timestamps = 0
# tw_reuse 只对客户端起作用，开启后客户端在1s内回收
net.ipv4.tcp_tw_reuse = 1
# recycle 同时对服务端和客户端启作用。如果服务端断开一个NAT用户“可能”会影响。 当TIMEOUT状态过多时，建议启用
net.ipv4.tcp_tw_recycle = 0
net.ipv4.tcp_fin_timeout = 1
# Nginx 之类的中间代理一定要关注这个值，因为它对你的系统起到一个保护的作用，一旦端口全部被占用，服务就异常了。 tcp_max_tw_buckets 能帮你降低这种情况的发生概率，争取补救时间。
net.ipv4.tcp_max_tw_buckets = 20000
# 这个值表示系统所能处理不属于任何进程的socket数量，当我们需要快速建立大量连接时，就需要关注下这个值了。 
net.ipv4.tcp_max_orphans = 327680
# 15. 现大量fin-wait-1
#首先，fin发送之后，有可能会丢弃，那么发送多少次这样的fin包呢？fin包的重传，也会采用退避方式，在2.6.358内核中采用的是指数退避，2s，4s，最后的重试次数是由
net.ipv4.tcp_synack_retries = 1
net.ipv4.tcp_syncookies = 1
# KeepAlive的空闲时长，或者说每次正常发送心跳的周期，默认值为7200s（2小时）
net.ipv4.tcp_keepalive_time = 300
# KeepAlive探测包的发送间隔，默认值为75s
net.ipv4.tcp_keepalive_intvl = 30
# 在tcp_keepalive_time之后，没有接收到对方确认，继续发送保活探测包次数，默认值为9（次）
net.ipv4.tcp_keepalive_probes = 3
# 允许超载使用内存，避免内存快到极限报错
# overcommit_memory 0 redis启动前向内核申请maxmemory, 够ok. 不够error.
# 1  redis启动前向内核申请maxmemory,内核不统计内存是否够用, 允许分配redis使用全部内存。
# 2  redis启动前向内核申请maxmemory,内核允许redis使用全部内存+swap空间内存。
vm.overcommit_memory = 1
#
# 0,内存不足启动oom killer. 1内存不足,kernel panic(系统重启) 或oom. 2. 内存不足, 强制kernel panic. (系统重启) 
vm.panic_on_oom=0
vm.swappiness = 10
#net.ipv4.conf.eth1.rp_filter = 0
#net.ipv4.conf.lo.arp_ignore = 1
#net.ipv4.conf.lo.arp_announce = 2
#net.ipv4.conf.all.arp_ignore = 1
#net.ipv4.conf.all.arp_announce = 2
net.ipv4.tcp_mem = 786432 1048576 1572864
net.ipv4.tcp_rmem = 4096 87380 4194304
net.ipv4.tcp_wmem = 4096 16384 4194304
# 随机端口的范围
net.ipv4.ip_local_port_range = 10001 65000

# inotify监听文件数量
fs.inotify.max_user_watches=89100

# 文件打开数量
# 所有进程 
fs.file-max=52706963
# 单个进程
fs.nr_open=52706963
```

其他还包括免密、iptables、firewalld 、NetworkManager 、ntpd等，具体步骤略



## 部署高可用Etcd

etcd存放所有资源，不允许任何人访问，而且etcd基于restful(http/https)风格API提供服务，所以etcd最好使用数字证书认证。

1. etcd彼此间通信：2380, 证书认证。每个节点有一个证书完成对等通信。

2. 任何客户端访问etcd: 2379端口，证书认证

   - 客户端提供证书
   - 每个etcd有一个服务端证书。

3. etcd专用的证书

   | 证书                                                         | 通信             |
   | ------------------------------------------------------------ | ---------------- |
   | etcd-ca                                                      | 颁发证书         |
   | etcd1-peer，etcd2-peer，etcd3-peer                           | 基于2380端口通信 |
   | etcd1-server， etcd2-server， etcd3-server， client（每个api server使用） | 基于2379端口通信 |

   每个节点需要拥有的etcd相关证书，即：

   一个ca

   一个peer证书（全部一样）

   一个server证书（全部一样），一个client证书（全部一样）

### 部署etcd

-  extras/apt
-  二进制部署

etcd版本 etcd-v2、etcd-v3，kubernetes新版使用v3

```
root@kube20-master01:~# apt update                                            #缓存
Hit:1 http://mirrors.aliyun.com/ubuntu bionic InRelease
Get:2 http://mirrors.aliyun.com/ubuntu bionic-security InRelease [88.7 kB]       
Get:3 http://mirrors.aliyun.com/ubuntu bionic-updates InRelease [88.7 kB]        
Get:4 http://mirrors.aliyun.com/ubuntu bionic-proposed InRelease [242 kB]
Get:5 http://mirrors.aliyun.com/ubuntu bionic-backports InRelease [74.6 kB]
Get:6 http://mirrors.aliyun.com/ubuntu bionic-security/multiverse Sources [5,236 B]
Get:7 http://mirrors.aliyun.com/ubuntu bionic-security/universe Sources [275 kB]                             
Fetched 15.3 MB in 10s (1,529 kB/s)
Reading package lists... Done
Building dependency tree 
Reading state information... Done
192 packages can be upgraded. Run 'apt list --upgradable' to see them.

root@kube20-master01:~#  apt-cache  madison etcd                             #查看版本
      etcd | 3.2.17+dfsg-1 | http://mirrors.aliyun.com/ubuntu bionic/universe amd64 Packages
      etcd | 3.2.17+dfsg-1 | http://mirrors.aliyun.com/ubuntu bionic/universe i386 Packages
      etcd | 3.2.17+dfsg-1 | http://mirrors.aliyun.com/ubuntu bionic/universe Sources
      
root@kube20-master01:~# apt install etcd                                     #安装etcd
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  etcd-client etcd-server pipexec
The following NEW packages will be installed:
  etcd etcd-client etcd-server pipexec
0 upgraded, 4 newly installed, 0 to remove and 192 not upgraded.
Need to get 12.4 MB of archives.
After this operation, 52.2 MB of additional disk space will be used.
Do you want to continue? [Y/n] Y
Get:1 http://mirrors.aliyun.com/ubuntu bionic/universe amd64 pipexec amd64 2.5.5-1 [16.8 kB]
Get:2 http://mirrors.aliyun.com/ubuntu bionic/universe amd64 etcd-client amd64 3.2.17+dfsg-1 [8,137 kB]
Get:3 http://mirrors.aliyun.com/ubuntu bionic/universe amd64 etcd-server amd64 3.2.17+dfsg-1 [4,285 kB]
Get:4 http://mirrors.aliyun.com/ubuntu bionic/universe amd64 etcd all 3.2.17+dfsg-1 [2,516 B]
Fetched 12.4 MB in 3s (3,642 kB/s)
Selecting previously unselected package pipexec.
(Reading database ... 67273 files and directories currently installed.)
Preparing to unpack .../pipexec_2.5.5-1_amd64.deb ...
Unpacking pipexec (2.5.5-1) ...
Selecting previously unselected package etcd-client.
Preparing to unpack .../etcd-client_3.2.17+dfsg-1_amd64.deb ...
Unpacking etcd-client (3.2.17+dfsg-1) ...
Selecting previously unselected package etcd-server.
Preparing to unpack .../etcd-server_3.2.17+dfsg-1_amd64.deb ...
Unpacking etcd-server (3.2.17+dfsg-1) ...
Selecting previously unselected package etcd.
Preparing to unpack .../etcd_3.2.17+dfsg-1_all.deb ...
Unpacking etcd (3.2.17+dfsg-1) ...
Setting up pipexec (2.5.5-1) ...
Setting up etcd-client (3.2.17+dfsg-1) ...
Setting up etcd-server (3.2.17+dfsg-1) ...
Adding system user `etcd' (UID 112) ...
Adding new group `etcd' (GID 116) ...
Adding new user `etcd' (UID 112) with group `etcd' ...
Creating home directory `/var/lib/etcd/' ...
Setting up etcd (3.2.17+dfsg-1) ...
Processing triggers for systemd (237-3ubuntu10.33) ...
Processing triggers for man-db (2.8.3-2ubuntu0.1) ...
Processing triggers for ureadahead (0.100.0-21) ...

root@kube20-master01:~# etcd --version                                     #查看安装版本
etcd Version: 3.2.17
Git SHA: Not provided (use ./build instead of go build)
Go Version: go1.10
Go OS/Arch: linux/amd64
```

### etcd配置文件

-  不使用证书调度通信
-  使用证书认证

客户端

```
root@kube20-master01:~# dpkg -L etcd-client
/.
/usr
/usr/bin
/usr/bin/etcd-dump-db
/usr/bin/etcd-dump-logs
/usr/bin/etcd2-backup-coreos
/usr/bin/etcdctl
/usr/share
/usr/share/doc
/usr/share/doc/etcd-client
/usr/share/doc/etcd-client/changelog.Debian.gz
/usr/share/doc/etcd-client/copyright
/usr/share/lintian
/usr/share/lintian/overrides
/usr/share/lintian/overrides/etcd-client
/usr/share/man
/usr/share/man/man1
/usr/share/man/man1/etcdctl.1.gz
```

服务端

```
root@kube20-master01:~# dpkg -L etcd-server
/.
/etc
/etc/default
/etc/default/etcd
/etc/init.d
/etc/init.d/etcd
/lib
/lib/systemd
/lib/systemd/system
/lib/systemd/system/etcd.service
/usr
/usr/bin
/usr/bin/etcd
/usr/share
/usr/share/doc
/usr/share/doc/etcd-server
/usr/share/doc/etcd-server/benchmarks
/usr/share/doc/etcd-server/benchmarks/README.md
/usr/share/doc/etcd-server/benchmarks/etcd-2-1-0-alpha-benchmarks.md
/usr/share/doc/etcd-server/benchmarks/etcd-2-2-0-benchmarks.md
/usr/share/doc/etcd-server/benchmarks/etcd-2-2-0-rc-benchmarks.md
/usr/share/doc/etcd-server/benchmarks/etcd-2-2-0-rc-memory-benchmarks.md
/usr/share/doc/etcd-server/benchmarks/etcd-3-demo-benchmarks.md
/usr/share/doc/etcd-server/benchmarks/etcd-3-watch-memory-benchmark.md
/usr/share/doc/etcd-server/benchmarks/etcd-storage-memory-benchmark.md.gz
/usr/share/doc/etcd-server/branch_management.md
/usr/share/doc/etcd-server/changelog.Debian.gz
/usr/share/doc/etcd-server/copyright
/usr/share/doc/etcd-server/demo.md.gz
/usr/share/doc/etcd-server/dev-guide
/usr/share/doc/etcd-server/dev-guide/api_concurrency_reference_v3.md.gz
/usr/share/doc/etcd-server/dev-guide/api_grpc_gateway.md
/usr/share/doc/etcd-server/dev-guide/api_reference_v3.md.gz
/usr/share/doc/etcd-server/dev-guide/apispec
/usr/share/doc/etcd-server/dev-guide/apispec/swagger
/usr/share/doc/etcd-server/dev-guide/apispec/swagger/rpc.swagger.json.gz
/usr/share/doc/etcd-server/dev-guide/apispec/swagger/v3election.swagger.json.gz
/usr/share/doc/etcd-server/dev-guide/apispec/swagger/v3lock.swagger.json.gz
/usr/share/doc/etcd-server/dev-guide/experimental_apis.md
/usr/share/doc/etcd-server/dev-guide/grpc_naming.md
/usr/share/doc/etcd-server/dev-guide/interacting_v3.md.gz
/usr/share/doc/etcd-server/dev-guide/limit.md
/usr/share/doc/etcd-server/dev-guide/local_cluster.md
/usr/share/doc/etcd-server/dev-internal
/usr/share/doc/etcd-server/dev-internal/discovery_protocol.md.gz
/usr/share/doc/etcd-server/dev-internal/logging.md
/usr/share/doc/etcd-server/dev-internal/release.md.gz
/usr/share/doc/etcd-server/dl_build.md
/usr/share/doc/etcd-server/docs.md.gz
/usr/share/doc/etcd-server/faq.md.gz
/usr/share/doc/etcd-server/integrations.md.gz
/usr/share/doc/etcd-server/learning
/usr/share/doc/etcd-server/learning/api.md.gz
/usr/share/doc/etcd-server/learning/api_guarantees.md.gz
/usr/share/doc/etcd-server/learning/auth_design.md.gz
/usr/share/doc/etcd-server/learning/data_model.md
/usr/share/doc/etcd-server/learning/glossary.md
/usr/share/doc/etcd-server/learning/why.md.gz
/usr/share/doc/etcd-server/metrics.md.gz
/usr/share/doc/etcd-server/op-guide
/usr/share/doc/etcd-server/op-guide/authentication.md.gz
/usr/share/doc/etcd-server/op-guide/clustering.md.gz
/usr/share/doc/etcd-server/op-guide/configuration.md.gz
/usr/share/doc/etcd-server/op-guide/container.md.gz
/usr/share/doc/etcd-server/op-guide/etcd-sample-grafana.png
/usr/share/doc/etcd-server/op-guide/etcd3_alert.rules.gz
/usr/share/doc/etcd-server/op-guide/failures.md
/usr/share/doc/etcd-server/op-guide/gateway.md.gz
/usr/share/doc/etcd-server/op-guide/grafana.json.gz
/usr/share/doc/etcd-server/op-guide/grpc_proxy.md.gz
/usr/share/doc/etcd-server/op-guide/hardware.md.gz
/usr/share/doc/etcd-server/op-guide/maintenance.md.gz
/usr/share/doc/etcd-server/op-guide/monitoring.md.gz
/usr/share/doc/etcd-server/op-guide/performance.md.gz
/usr/share/doc/etcd-server/op-guide/recovery.md
/usr/share/doc/etcd-server/op-guide/runtime-configuration.md.gz
/usr/share/doc/etcd-server/op-guide/runtime-reconf-design.md.gz
/usr/share/doc/etcd-server/op-guide/security.md.gz
/usr/share/doc/etcd-server/op-guide/supported-platform.md
/usr/share/doc/etcd-server/op-guide/v2-migration.md.gz
/usr/share/doc/etcd-server/op-guide/versioning.md
/usr/share/doc/etcd-server/platforms
/usr/share/doc/etcd-server/platforms/aws.md.gz
/usr/share/doc/etcd-server/platforms/container-linux-systemd.md.gz
/usr/share/doc/etcd-server/platforms/freebsd.md
/usr/share/doc/etcd-server/production-users.md.gz
/usr/share/doc/etcd-server/reporting_bugs.md
/usr/share/doc/etcd-server/rfc
/usr/share/doc/etcd-server/rfc/v3api.md.gz
/usr/share/doc/etcd-server/tuning.md.gz
/usr/share/doc/etcd-server/upgrades
/usr/share/doc/etcd-server/upgrades/upgrade_3_0.md.gz
/usr/share/doc/etcd-server/upgrades/upgrade_3_1.md.gz
/usr/share/doc/etcd-server/upgrades/upgrade_3_2.md.gz
/usr/share/doc/etcd-server/upgrades/upgrading-etcd.md
/usr/share/doc/etcd-server/v2
/usr/share/doc/etcd-server/v2/04_to_2_snapshot_migration.md
/usr/share/doc/etcd-server/v2/README.md
/usr/share/doc/etcd-server/v2/admin_guide.md.gz
/usr/share/doc/etcd-server/v2/api.md.gz
/usr/share/doc/etcd-server/v2/api_v3.md.gz
/usr/share/doc/etcd-server/v2/auth_api.md.gz
/usr/share/doc/etcd-server/v2/authentication.md.gz
/usr/share/doc/etcd-server/v2/backward_compatibility.md.gz
/usr/share/doc/etcd-server/v2/benchmarks
/usr/share/doc/etcd-server/v2/benchmarks/README.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-2-1-0-alpha-benchmarks.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-2-2-0-benchmarks.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-2-2-0-rc-benchmarks.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-2-2-0-rc-memory-benchmarks.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-3-demo-benchmarks.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-3-watch-memory-benchmark.md
/usr/share/doc/etcd-server/v2/benchmarks/etcd-storage-memory-benchmark.md.gz
/usr/share/doc/etcd-server/v2/branch_management.md
/usr/share/doc/etcd-server/v2/clustering.md.gz
/usr/share/doc/etcd-server/v2/configuration.md.gz
/usr/share/doc/etcd-server/v2/dev
/usr/share/doc/etcd-server/v2/dev/release.md.gz
/usr/share/doc/etcd-server/v2/discovery_protocol.md.gz
/usr/share/doc/etcd-server/v2/docker_guide.md
/usr/share/doc/etcd-server/v2/errorcode.md
/usr/share/doc/etcd-server/v2/etcd_alert.rules.gz
/usr/share/doc/etcd-server/v2/faq.md.gz
/usr/share/doc/etcd-server/v2/glossary.md
/usr/share/doc/etcd-server/v2/implementation-faq.md
/usr/share/doc/etcd-server/v2/internal-protocol-versioning.md
/usr/share/doc/etcd-server/v2/libraries-and-tools.md.gz
/usr/share/doc/etcd-server/v2/members_api.md
/usr/share/doc/etcd-server/v2/metrics.md.gz
/usr/share/doc/etcd-server/v2/other_apis.md
/usr/share/doc/etcd-server/v2/platforms
/usr/share/doc/etcd-server/v2/platforms/freebsd.md
/usr/share/doc/etcd-server/v2/production-users.md
/usr/share/doc/etcd-server/v2/proxy.md.gz
/usr/share/doc/etcd-server/v2/reporting_bugs.md
/usr/share/doc/etcd-server/v2/rfc
/usr/share/doc/etcd-server/v2/rfc/v3api.md.gz
/usr/share/doc/etcd-server/v2/runtime-configuration.md.gz
/usr/share/doc/etcd-server/v2/runtime-reconf-design.md.gz
/usr/share/doc/etcd-server/v2/security.md.gz
/usr/share/doc/etcd-server/v2/tuning.md.gz
/usr/share/doc/etcd-server/v2/upgrade_2_1.md.gz
/usr/share/doc/etcd-server/v2/upgrade_2_2.md.gz
/usr/share/doc/etcd-server/v2/upgrade_2_3.md.gz
/usr/share/lintian
/usr/share/lintian/overrides
/usr/share/lintian/overrides/etcd-server
/usr/share/man
/usr/share/man/man1
/usr/share/man/man1/etcd.1.gz
/usr/share/doc/etcd-server/README.md.gz

root@kube20-master01:~# cat /lib/systemd/system/etcd.service
[Unit]
Description=etcd - highly-available key value store
Documentation=https://github.com/coreos/etcd
Documentation=man:etcd
After=network.target
Wants=network-online.target

[Service]
Environment=DAEMON_ARGS=
Environment=ETCD_NAME=%H
Environment=ETCD_DATA_DIR=/var/lib/etcd/default       # 数据目录
EnvironmentFile=-/etc/default/%p                      # 配置文件
Type=notify
User=etcd
PermissionsStartOnly=true
#ExecStart=/bin/sh -c "GOMAXPROCS=$(nproc) /usr/bin/etcd $DAEMON_ARGS"
ExecStart=/usr/bin/etcd $DAEMON_ARGS
Restart=on-abnormal
#RestartSec=10s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
Alias=etcd2.service

root@kube20-master01:~# cat /etc/default/etcd         #配置文件
ETCD_DATA_DIR="/var/lib/etcd/k8s.etcd"       # 数据存放位置
ETCD_LISTEN_PEER_URLS="https://192.168.137.51:2380"    # 监听只能是ip     # “监听” 3个etcd raft协议心跳地址 error verifying flags, expected IP in URL for binding (https://master01.magedu.com:2380). See 'etcd --help'.
ETCD_LISTEN_CLIENT_URLS="https://192.168.137.51:2379"       # “监听” client 与etcd通信的接口 # 暴露给客户端添加127.0.0.1
ETCD_NAME="kube20-master01"                             # etcd集群的节点名 # 和INITIAL_CLUSTER的KEY一样
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://kube20-master01:2380"  # 工作为集群时，对外“通告”自已协议接口
ETCD_ADVERTISE_CLIENT_URLS="https://kube20-master01:2379"        # 工作为集群时，对外“通告”自已客户访问接口
ETCD_INITIAL_CLUSTER="kube20-master01=https://kube20-master01:2380,kube20-master02=https://kube20-master02:2380,kube20-master03=https://kube20-master03:2380"        # 集群成员
	# 静态初始化，写进来
	# 动态初始化，通过另一个集群发现自已的节点
ETCD_INITIAL_CLUSTER_TOKEN="k8s-etcd-cluster" 

# client访问etcd 2379使用https通信
ETCD_CERT_FILE="/etc/etcd/pki/server.crt" # 提供给client证书
ETCD_KEY_FILE="/etc/etcd/pki/server.key"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt" # 检验client的证书
ETCD_AUTO_TLS="false"    # 自动生成etcd server证书


# 各节点间通信也叫peer通信 # 2380端口通信
ETCD_PEER_CERT_FILE="/etc/etcd/pki/peer.crt"  # 简单使用相同证书，检验对端的CN得吻合
ETCD_PEER_KEY_FILE="/etc/etcd/pki/peer.key"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt"  # 签发etcd证书和验证peer证书的ca.
ETCD_PEER_AUTO_TLS="false"
```

### 配置https *

至少2个节点存在才有法定票数，至少配置2个节点才可以启动etcd

#### 生成证书

[http://blog.mykernel.cn/2021/01/29/%E8%AE%A4%E8%AF%81%E3%80%81%E6%8E%88%E6%9D%83%E5%8F%8A%E5%87%86%E5%85%A5%E6%8E%A7%E5%88%B6/#%E5%88%B6%E4%BD%9C%E8%B4%A6%E6%88%B7](http://blog.mykernel.cn/2021/01/29/认证、授权及准入控制/#制作账户)

[k8s-certs-generator](https://github.com/iKubernetes/k8s-certs-generator)

证书要求

[https://kubernetes.io/zh/docs/setup/best-practices/certificates/#%E6%89%8B%E5%8A%A8%E9%85%8D%E7%BD%AE%E8%AF%81%E4%B9%A6](https://kubernetes.io/zh/docs/setup/best-practices/certificates/#手动配置证书)

CA

| **路径**               | 默认 CN                   | **描述**                                                     |
| ---------------------- | ------------------------- | ------------------------------------------------------------ |
| ca.crt,key             | kubernetes-ca             | Kubernetes 通用 CA                                           |
| etcd/ca.crt,key        | etcd-ca                   | 与 etcd 相关的所有功能                                       |
| front-proxy-ca.crt,key | kubernetes-front-proxy-ca | 用于 [前端代理](https://kubernetes.io/zh/docs/tasks/extend-kubernetes/configure-aggregation-layer/) |

\# 制作ca
\# https://kubernetes.io/zh/docs/concepts/cluster-administration/certificates/

.cer/.crt是用于存放证书，它是2进制形式存放的，不含私钥。
.pem跟crt/cer的区别是它以Ascii来表示

##### CSR - 准备3个ca csr，并生成ca证书

```
root@kube20-master01:~# mkdir k8s-cert
root@kube20-master01:~# cd k8s-cert
root@kube20-master01:~/k8s-cert# curl -L https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -o cfssl
root@kube20-master01:~/k8s-cert# chmod +x cfssl
root@kube20-master01:~/k8s-cert# curl -L https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -o cfssljson
root@kube20-master01:~/k8s-cert# chmod +x cfssljson
root@kube20-master01:~/k8s-cert# curl -L https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64 -o cfssl-certinfo
root@kube20-master01:~/k8s-cert# chmod +x cfssl-certinfo
root@kube20-master01:~/k8s-cert# mkdir cert
root@kube20-master01:~/k8s-cert/cert# cd cert
```

k8s-ca csr CN=kubernetes-ca

```
root@kube20-master01:~/k8s-cert/cert# cat k8s-ca-csr.json 
{
+  "CN": "kubernetes-ca",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
+    "C": "China",                          
+    "ST": "AnHui",
+    "L": "HeFei",
+    "O": "system:none",
+    "OU": "system"
  }],
+    "hosts": []
}
```

> CSR是Certificate Signing Request的英文缩写，即证书请求文件，也就是证书申请者在申请数字证书时由CSP(加密服务提供者)在生成私钥的同时也生成证书请求文件，证书申请者只要把CSR文件提交给证书颁发机构后，证书颁发机构使用其根证书私钥签名就生成了证书公钥文件，也就是颁发给用户的证书。
>
> CN
>
> C 国家
>
> ST 省
>
> L 城市
>
> O 组织
>
> OU 组织
>
> K8S中使用CN作用户名和O作为组，非常关键
>
> hosts即下表中的SAN， 但是从证书要求中的CA并没有names中的要求，只有CN要求，所以下面随意
>
> | 默认 CN                       | 父级 CA                   | O (位于 Subject 中) | 类型           | 主机 (SAN)                                          |
> | ----------------------------- | ------------------------- | ------------------- | -------------- | --------------------------------------------------- |
> | kube-etcd                     | etcd-ca                   |                     | server, client | `localhost`, `127.0.0.1`                            |
> | kube-etcd-peer                | etcd-ca                   |                     | server, client | `<hostname>`, `<Host_IP>`, `localhost`, `127.0.0.1` |
> | kube-etcd-healthcheck-client  | etcd-ca                   |                     | client         |                                                     |
> | kube-apiserver-etcd-client    | etcd-ca                   | system:masters      | client         |                                                     |
> | kube-apiserver                | kubernetes-ca             |                     | server         | `<hostname>`, `<Host_IP>`, `<advertise_IP>`, `[1]`  |
> | kube-apiserver-kubelet-client | kubernetes-ca             | system:masters      | client         |                                                     |
> | front-proxy-client            | kubernetes-front-proxy-ca |                     | client         |                                                     |
>
> [1]: 用来连接到集群的不同 IP 或 DNS 名 （就像 [kubeadm](https://kubernetes.io/zh/docs/reference/setup-tools/kubeadm/kubeadm/) 为负载均衡所使用的固定 IP 或 DNS 名，`kubernetes`、`kubernetes.default`、`kubernetes.default.svc`、 `kubernetes.default.svc.cluster`、`kubernetes.default.svc.cluster.local`）。
>
> 其中，`kind` 对应一种或多种类型的 [x509 密钥用途](https://godoc.org/k8s.io/api/certificates/v1beta1#KeyUsage)：
>
> | kind   | 密钥用途                       |
> | ------ | ------------------------------ |
> | server | 数字签名、密钥加密、服务端认证 |
> | client | 数字签名、密钥加密、客户端认证 |
>
> > **说明：**
> >
> > 上面列出的 Hosts/SAN 是推荐的配置方式；如果需要特殊安装，则可以在所有服务器证书上添加其他 SAN。
>
> > **说明：**
> >
> > 对于 kubeadm 用户：
> >
> > - 不使用私钥，将证书复制到集群 CA 的方案，在 kubeadm 文档中将这种方案称为外部 CA。
> > - 如果将以上列表与 kubeadm 生成的 PKI 进行比较，你会注意到，如果使用外部 etcd，则不会生成 `kube-etcd`、`kube-etcd-peer` 和 `kube-etcd-healthcheck-client` 证书

生成ca证书

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -initca k8s-ca-csr.json  | ../cfssljson -bare k8s-ca
2021/02/12 17:23:45 [INFO] generating a new CA key and certificate from CSR
2021/02/12 17:23:45 [INFO] generate received request
2021/02/12 17:23:45 [INFO] received CSR
2021/02/12 17:23:45 [INFO] generating key: rsa-2048
2021/02/12 17:23:45 [INFO] encoded CSR
2021/02/12 17:23:45 [INFO] signed certificate with serial number 572934946694303468054845835054425722268629866538
```

etcd-ca csr CN=etcd-ca

```
root@kube20-master01:~/k8s-cert/cert# cp k8s-ca-csr.json etcd-ca-csr.json 
root@kube20-master01:~/k8s-cert/cert# cat etcd-ca-csr.json
{
+  "CN": "etcd-ca",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",                          
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
root@ubuntu-template:~/cert# ../cfssl gencert -initca etcd-ca-csr.json  | ../cfssljson -bare etcd-ca
2021/02/12 17:37:47 [INFO] generating a new CA key and certificate from CSR
2021/02/12 17:37:47 [INFO] generate received request
2021/02/12 17:37:47 [INFO] received CSR
2021/02/12 17:37:47 [INFO] generating key: rsa-2048
2021/02/12 17:37:48 [INFO] encoded CSR
2021/02/12 17:37:48 [INFO] signed certificate with serial number 294206733164489908103574822262548328689745708507
```

proxy-front-ca CN=kubernetes-front-proxy-ca

```
root@kube20-master01:~/k8s-cert/cert#  cp etcd-ca-csr.json kubernetes-front-proxy-ca.json
root@kube20-master01:~/k8s-cert/cert#  cat kubernetes-front-proxy-ca.json
{
+  "CN": "kubernetes-front-proxy-ca",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",                          
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
root@kube20-master01:~/k8s-cert/cert#  ../cfssl gencert -initca kubernetes-front-proxy-ca.json | ../cfssljson -bare  kubernetes-front-proxy-ca
2021/02/12 17:38:06 [INFO] generating a new CA key and certificate from CSR
2021/02/12 17:38:06 [INFO] generate received request
2021/02/12 17:38:06 [INFO] received CSR
2021/02/12 17:38:06 [INFO] generating key: rsa-2048
2021/02/12 17:38:07 [INFO] encoded CSR
2021/02/12 17:38:07 [INFO] signed certificate with serial number 362134948534929172182747115197702689866999482275
```

验证

```
root@kube20-master01:~/k8s-cert/cert# ls *.pem
etcd-ca-key.pem  etcd-ca.pem  k8s-ca-key.pem  k8s-ca.pem  kubernetes-front-proxy-ca-key.pem  kubernetes-front-proxy-ca.pem
```

准备所以ca的配置文件

```
root@kube20-master01:~/k8s-cert/cert# cat common-config.json 
{
    "signing": {
        "default": {
+            "expiry": "876000h" 
        },
        "profiles": {
            "kubernetes-ca": { 
+                "expiry": "876000h",
                "usages": [
                    "signing",
                    "key encipherment",
+                    "server auth",
+                    "client auth"
                ]
            },
            "etcd-ca": {
+                "expiry": "87600h",  
                "usages": [
                    "signing",
                    "key encipherment",
 +                   "server auth",
 +                   "client auth"
                ]
            },
            "kubernetes-front-proxy-ca": {
+                "expiry": "87600h", 
                "usages": [
                    "signing",
                    "key encipherment",
+                    "server auth",
+                    "client auth"
                ]
            }
        }
    }
}
```

> profiles 一级键为上面ca的CSR的CN名 profiles kubernetes-front-proxy-ca etcd-ca kubernetes-ca
>
> expiry 过期时间，此处100年
>
> server auth 完成服务端认证, 签发服务端证书
>
> client auth 完成客户端认证，签发客户端证书
>
> 多个默认CN，../cfssl gencert -profile=kubernetes-ca调用哪个父级CA配置
>
> | 默认 CN                       | 父级 CA                   | O (位于 Subject 中) | 类型           | 主机 (SAN)                                          |
> | ----------------------------- | ------------------------- | ------------------- | -------------- | --------------------------------------------------- |
> | kube-etcd                     | etcd-ca                   |                     | server, client | `localhost`, `127.0.0.1`                            |
> | kube-etcd-peer                | etcd-ca                   |                     | server, client | `<hostname>`, `<Host_IP>`, `localhost`, `127.0.0.1` |
> | kube-etcd-healthcheck-client  | etcd-ca                   |                     | client         |                                                     |
> | kube-apiserver-etcd-client    | etcd-ca                   | system:masters      | client         |                                                     |
> | kube-apiserver                | kubernetes-ca             |                     | server         | `<hostname>`, `<Host_IP>`, `<advertise_IP>`, `[1]`  |
> | kube-apiserver-kubelet-client | kubernetes-ca             | system:masters      | client         |                                                     |
> | front-proxy-client            | kubernetes-front-proxy-ca |                     | client         |                                                     |

##### 准备etcd相关的证书

| 默认 CN                      | 建议的密钥路径              | 建议的证书路径              | 命令    | 密钥参数       | 证书参数        |
| ---------------------------- | --------------------------- | --------------------------- | ------- | -------------- | --------------- |
| kube-etcd                    | etcd/server.key             | etcd/server.crt             | etcd    | –key-file      | –cert-file      |
| kube-etcd-peer               | etcd/peer.key               | etcd/peer.crt               | etcd    | –peer-key-file | –peer-cert-file |
| etcd-ca                      |                             | etcd/ca.crt                 | etcdctl |                | –cacert         |
| kube-etcd-healthcheck-client | etcd/healthcheck-client.key | etcd/healthcheck-client.crt | etcdctl | –key           | –cert           |

准备etcd server证书

```
root@kube20-master01:~/k8s-cert/cert# cat etcd-server-csr.json
{
+  "CN": "kube-etcd",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",                          
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
    "hosts": [
+	"192.168.137.51",
+	"192.168.137.52",
+	"192.168.137.53",
+	"127.0.0.1"
	]
}
```

> 由以上表格可知，CN的值
>
> hosts为连接etcd server的可用地址范围

签发证书

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem --config=common-config.json -profile=etcd-ca etcd-server-csr.json | ../cfssljson -bare etcd-server
2021/02/12 18:19:01 [INFO] generate received request
2021/02/12 18:19:01 [INFO] received CSR
2021/02/12 18:19:01 [INFO] generating key: rsa-2048
2021/02/12 18:19:01 [INFO] encoded CSR
2021/02/12 18:19:01 [INFO] signed certificate with serial number 530383301666795920199552496839487979738994665927
2021/02/12 18:19:01 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
```

准备etcd对等证书

```
root@kube20-master01:~/k8s-cert/cert# cp etcd-server-csr.json etcd-peer-csr.json
root@kube20-master01:~/k8s-cert/cert# cat etcd-peer-csr.json
{
+  "CN": "kube-etcd-peer",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
    "hosts": [
+	"192.168.137.51",
+	"192.168.137.52",
+	"192.168.137.53",
	"127.0.0.1"
	]
}
```

> CN
>
> hosts 因为是通用的，所以连接客户端可以是任意etcd节点

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem      --config=common-config.json -profile=etcd-ca      etcd-peer-csr.json | ../cfssljson -bare etcd-peer
2021/02/12 18:27:37 [INFO] generate received request
2021/02/12 18:27:37 [INFO] received CSR
2021/02/12 18:27:37 [INFO] generating key: rsa-2048
2021/02/12 18:27:37 [INFO] encoded CSR
2021/02/12 18:27:37 [INFO] signed certificate with serial number 457720406412167240514992926808797403291663687404
2021/02/12 18:27:37 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
```

客户端连接etcd的证书

```
root@kube20-master01:~/k8s-cert/cert# cp etcd-server-csr.json kube-etcd-healthcheck-client-csr.json
root@kube20-master01:~/k8s-cert/cert# cat kube-etcd-healthcheck-client-csr.json
{
+  "CN": "kube-etcd-healthcheck-client",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
```

> CN 就是上面的CN
>
> 因为自已不提供服务，所以主机不用写

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem      --config=common-config.json -profile=etcd-ca      kube-etcd-healthcheck-client-csr.json | ../cfssljson -bare kube-etcd-healthcheck-client
2021/02/12 18:44:15 [INFO] generate received request
2021/02/12 18:44:15 [INFO] received CSR
2021/02/12 18:44:15 [INFO] generating key: rsa-2048
2021/02/12 18:44:15 [INFO] encoded CSR
2021/02/12 18:44:15 [INFO] signed certificate with serial number 689362486960204540510139217921186983814225194628
2021/02/12 18:44:15 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
```

api 连接etcd的证书

```
root@kube20-master01:~/k8s-cert/cert# cp etcd-server-csr.json kube-apiserver-etcd-client-csr.json
root@kube20-master01:~/k8s-cert/cert# cat kube-apiserver-etcd-client-csr.json
{
+  "CN": "kube-apiserver-etcd-client",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
+    "O": "system:masters",
    "OU": "system"
  }],
+    "hosts": []
}
```

> CN 就是上面的CN
>
> 因为自已不提供服务，所以主机不用写
>
> O 需要k8s集群管理员

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem      --config=common-config.json -profile=etcd-ca      kube-apiserver-etcd-client-csr.json | ../cfssljson -bare kube-apiserver-etcd-client
2021/02/12 18:50:27 [INFO] generate received request
2021/02/12 18:50:27 [INFO] received CSR
2021/02/12 18:50:27 [INFO] generating key: rsa-2048
2021/02/12 18:50:27 [INFO] encoded CSR
2021/02/12 18:50:27 [INFO] signed certificate with serial number 86926247680740453051036793438350228567734239152
2021/02/12 18:50:27 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
```

将证书准备成上面建议的文件名

```
install -dv /etc/etcd/pki/
# server
cp etcd-server.pem /etc/etcd/pki/server.crt 
cp etcd-server-key.pem /etc/etcd/pki/server.key
# ca
cp etcd-ca.pem /etc/etcd/pki/ca.crt
cp etcd-ca-key.pem /etc/etcd/pki/ca.key
# peer
cp etcd-peer.pem /etc/etcd/pki/peer.crt
cp etcd-peer-key.pem /etc/etcd/pki/peer.key
# client
cp kube-etcd-healthcheck-client.pem /etc/etcd/pki/client.crt
cp kube-etcd-healthcheck-client-key.pem /etc/etcd/pki/client.key

# api client
install -dv /etc/kubernetes/pki/
cp kube-apiserver-etcd-client.pem /etc/kubernetes/pki/apiserver-etcd-client.crt
cp kube-apiserver-etcd-client-key.pem /etc/kubernetes/pki/apiserver-etcd-client.key
```

2380 peer证书同

2379 server证书同

```
ssh-keygen  -t rsa -b 4096 -P '' -f ~/.ssh/id_rsa
ssh-copy-id 172.16.0.101:
ssh-copy-id 172.16.0.102:
ssh-copy-id 172.16.0.103:
scp -rp /etc/{etcd,kubernetes}  192.168.137.51:/etc
scp -rp /etc/{etcd,kubernetes}  192.168.137.52:/etc
scp -rp /etc/{etcd,kubernetes}  192.168.137.53:/etc


# 检验
tree /etc/etcd
tree /etc/kubernetes
```

如果以上方法配置证书，直接跳到配置etcd01

```
# ca
root@kube20-master01:~# git clone https://github.com/iKubernetes/k8s-certs-generator.git

# 生成证书 
bash  gencerts.sh etcd
magedu.com

# 注意如果使用 10.96.0.0/16 K8S配置的首个集群IP是10.64.0.1，暂时不清楚原因
# 10.96.0.0/16 K8S配置的首个集群IP是10.96.0.1，暂时不清楚原因。状态这个又不在公网使用，直接使用默认值
bash  gencerts.sh k8s
magedu.com
kubernetes
Enter the IP Address in default namespace  
	of the Kubernetes API Server[10.96.0.1]: 10.96.0.1 # 这里填
master01 master02 master03

root@kube20-master01:~/k8s-certs-generator# ls etcd/pki/
ca.crt  ca.key    # CA

apiserver-etcd-client.crt  apiserver-etcd-client.key   # 连接etcd客户端
server.crt  server.key # client连接etcd, etcd提供的证书 
client.crt  client.key  # 其他客户端
peer.crt  peer.key     # etcd各节点间提供的证书  
```

#### 配置etcd01 *

走的协议https

```
root@kube20-master01:~# chown etcd.etcd /etc/etcd/pki/*.key
root@kube20-master01:~# cat /etc/default/etcd 
ETCD_DATA_DIR="/var/lib/etcd/k8s-etcd"
ETCD_LISTEN_PEER_URLS="https://192.168.137.51:2380"
ETCD_LISTEN_CLIENT_URLS="https://192.168.137.51:2379"
ETCD_NAME="192.168.137.51"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.137.51:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.137.51:2379"
ETCD_INITIAL_CLUSTER="192.168.137.51=https://192.168.137.51:2380,192.168.137.52=https://192.168.137.52:2380,192.168.137.53=https://192.168.137.53:2380"
ETCD_INITIAL_CLUSTER_TOKEN="k8s-etcd-cluster"

ETCD_CERT_FILE="/etc/etcd/pki/server.crt"
ETCD_KEY_FILE="/etc/etcd/pki/server.key"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt" 
ETCD_AUTO_TLS="false"   
ETCD_PEER_CERT_FILE="/etc/etcd/pki/peer.crt"
ETCD_PEER_KEY_FILE="/etc/etcd/pki/peer.key"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt"
ETCD_PEER_AUTO_TLS="false"

root@kube20-master01:~# rm -fr /var/lib/etcd/k8s-etcd
```

配置unit    #https://blog.csdn.net/lonnng2004/article/details/88964763

```
root@kube20-master01:~# vim /lib/systemd/system/etcd.service
Restart=on-failure
```

#### 配置etcd02*

```
root@kube20-master02:~# chown etcd.etcd /etc/etcd/pki/*.key
root@kube20-master02:~# cat /etc/default/etcd 
ETCD_DATA_DIR="/var/lib/etcd/k8s-etcd"
ETCD_LISTEN_PEER_URLS="https://192.168.137.52:2380"   
ETCD_LISTEN_CLIENT_URLS="https://192.168.137.52:2379"  
ETCD_NAME="192.168.137.52"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.137.52:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.137.52:2379"
ETCD_INITIAL_CLUSTER="192.168.137.51=https://192.168.137.51:2380,192.168.137.52=https://192.168.137.52:2380,192.168.137.53=https://192.168.137.53:2380"
ETCD_INITIAL_CLUSTER_TOKEN="k8s-etcd-cluster"

ETCD_CERT_FILE="/etc/etcd/pki/server.crt"
ETCD_KEY_FILE="/etc/etcd/pki/server.key"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt" 
ETCD_AUTO_TLS="false"   
ETCD_PEER_CERT_FILE="/etc/etcd/pki/peer.crt"
ETCD_PEER_KEY_FILE="/etc/etcd/pki/peer.key"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt"
ETCD_PEER_AUTO_TLS="false"

root@kube20-master02:~# rm -fr /var/lib/etcd/k8s-etcd
```

配置unit

```
root@kube20-master02:~# vim /lib/systemd/system/etcd.service
Restart=on-failure
```

#### 配置etcd03*

```
root@kube20-master03:~# chown etcd.etcd /etc/etcd/pki/*.key
root@kube20-master03:~# cat /etc/default/etcd 
ETCD_DATA_DIR="/var/lib/etcd/k8s-etcd"
ETCD_LISTEN_PEER_URLS="https://192.168.137.53:2380"   
ETCD_LISTEN_CLIENT_URLS="https://192.168.137.53:2379"  
ETCD_NAME="192.168.137.53"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.137.53:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.137.53:2379"
ETCD_INITIAL_CLUSTER="192.168.137.51=https://192.168.137.51:2380,192.168.137.52=https://192.168.137.52:2380,192.168.137.53=https://192.168.137.53:2380"
ETCD_INITIAL_CLUSTER_TOKEN="k8s-etcd-cluster"

ETCD_CERT_FILE="/etc/etcd/pki/server.crt"
ETCD_KEY_FILE="/etc/etcd/pki/server.key"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt" 
ETCD_AUTO_TLS="false"   
ETCD_PEER_CERT_FILE="/etc/etcd/pki/peer.crt"
ETCD_PEER_KEY_FILE="/etc/etcd/pki/peer.key"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/etcd/pki/ca.crt"
ETCD_PEER_AUTO_TLS="false"

root@kube20-master03:~# rm -fr /var/lib/etcd/k8s-etcd
```

配置unit

```
root@kube20-master03:~# vim /lib/systemd/system/etcd.service
Restart=on-failure
```

#### 启动Etcd集群

```
# 各节点执行
systemctl daemon-reload 
systemctl restart etcd
systemctl status etcd
systemctl enable etcd

etcdctl   --endpoints=https://192.168.137.51:2379 --cert-file=/etc/etcd/pki/client.crt --key-file=/etc/etcd/pki/client.key --ca-file=/etc/etcd/pki/ca.crt  member list 
etcdctl   --endpoints=https://192.168.137.52:2379 --cert-file=/etc/etcd/pki/client.crt --key-file=/etc/etcd/pki/client.key --ca-file=/etc/etcd/pki/ca.crt  member list 
etcdctl   --endpoints=https://192.168.137.53:2379 --cert-file=/etc/etcd/pki/client.crt --key-file=/etc/etcd/pki/client.key --ca-file=/etc/etcd/pki/ca.crt  member list 
```

#### 常用命令

```
# 集群健康检测
export NODE_IPS="192.168.137.51 192.168.137.52 192.168.137.53" 
root@kube20-master01:~# for ip in ${NODE_IPS}; do ETCDCTL_API=3  etcdctl  --endpoints=https://${ip}:2379  --cacert=/etc/etcd/pki/ca.crt --cert=/etc/etcd/pki/client.crt --key=/etc/etcd/pki/client.key   endpoint health; done 
https://192.168.137.51:2379 is healthy: successfully committed proposal: took = 2.487239ms
https://192.168.137.52:2379 is healthy: successfully committed proposal: took = 1.77157ms
https://192.168.137.53:2379 is healthy: successfully committed proposal: took = 3.064988ms

# 以下命令若不条件对应证书路径，需在配置文件中添加：http://127.0.0.1:2379
# --endpoints=https://${ip}:2379  --cacert=/etc/etcd/pki/ca.crt --cert=/etc/etcd/pki/client.crt --key=/etc/etcd/pki/client.key
ETCDCTL_API=3  etcdctl  --help
ETCDCTL_API=3  etcdctl  member list   --

ETCDCTL_API=3  etcdctl  get  / --prefix --keys-only   #以路径的方式所有key信息 
ETCDCTL_API=3  etcdctl  get  --prefix /calico         #查看etcd中calico的相关数据

ETCDCTL_API=3  etcdctl  put  /testkey "test for linux36"          #增    
ETCDCTL_API=3  etcdctl  get  /testkey                             #查  
ETCDCTL_API=3  etcdctl  put  /testkey "test for linux36-new"      #改    
ETCDCTL_API=3  etcdctl  del  /testkey                             #删

# 集群数据备份 https://www.cnblogs.com/chenqionghe/p/10622859.html
ETCDCTL_API=3  etcdctl  snapshot save     snapshot.db                              #数据备份
ETCDCTL_API=3  etcdctl  snapshot restore  snapshot.db  --datadir=/opt/etcd-testdir #将数据恢复到一个新的不存在的目录中
```



## 部署k8s

### 生成k8s证书及配置 *

| 默认 CN        | 父级 CA       | O (位于 Subject 中) | 类型   | 主机 (SAN)                                         |
| -------------- | ------------- | ------------------- | ------ | -------------------------------------------------- |
| kube-apiserver | kubernetes-ca |                     | server | `<hostname>`, `<Host_IP>`, `<advertise_IP>`, `[1]` |

| 默认 CN                       | 建议的密钥路径               | 建议的证书路径               | 命令           | 密钥参数               | 证书参数                      |
| ----------------------------- | ---------------------------- | ---------------------------- | -------------- | ---------------------- | ----------------------------- |
| etcd-ca                       | etcd/ca.key                  | etcd/ca.crt                  | kube-apiserver |                        | –etcd-cafile                  |
| kube-apiserver-etcd-client    | apiserver-etcd-client.key    | apiserver-etcd-client.crt    | kube-apiserver | –etcd-keyfile          | –etcd-certfile                |
| kubernetes-ca                 | ca.key                       | ca.crt                       | kube-apiserver |                        | –client-ca-file               |
| kube-apiserver                | apiserver.key                | apiserver.crt                | kube-apiserver | –tls-private-key-file  | –tls-cert-file                |
| kube-apiserver-kubelet-client | apiserver-kubelet-client.key | apiserver-kubelet-client.crt | kube-apiserver | –kubelet-client-key    | –kubelet-client-certificate   |
| front-proxy-ca                | front-proxy-ca.key           | front-proxy-ca.crt           | kube-apiserver |                        | –requestheader-client-ca-file |
| front-proxy-client            | front-proxy-client.key       | front-proxy-client.crt       | kube-apiserver | –proxy-client-key-file | –proxy-client-cert-file       |

生成kube-apiserver的server证书

```
root@kube20-master01:~/k8s-cert/cert# cat kube-apiserver-csr.json
{
+  "CN": "kube-apiserver",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
    "hosts": [
+    "192.168.137.51",
+    "192.168.137.52",
+    "192.168.137.53",
+    "10.64.0.1",
+    "kubernetes-api.mykernel.cn",
+    "kubernetes",
+    "kubernetes.default",
+    "kubernetes.default.svc",
+    "kubernetes.default.svc.cluster",
+    "kubernetes.default.svc.cluster.local",
+    "127.0.0.1"
	]
}
```

> master集群地址
>
> 10.64.0.1 集群内部api service地址
>
>  本次打算使用10.76.0.0/12网络，所以集群的首个地址是10.64.0.1/12
>
>  10.<0100 1100>.0.0
>
>  全1.<1111 0000>.0.0 掩码
>
>  10.<0100 0000>.0.0 运算结果：10.64.0.0/12 ,所以第一个是10.64.0.1
>
>  参考：[http://blog.mykernel.cn/2021/02/08/IP%E5%9C%B0%E5%9D%80%E6%8D%A2%E7%AE%97/](http://blog.mykernel.cn/2021/02/08/IP地址换算/)
>
> 访问https的端点
>
> [https://kubernetes-api.mykernel.cn](https://kubernetes-api.mykernel.cn/) 集群外部入口的域名
>
> [https://192.168.137.51:6443](https://172.16.0.101:6443/) [https://192.168.137.52:6443](https://172.16.0.102:6443/) [https://192.168.137.53:6443](https://172.16.0.103:6443/) 由于api server在3个节点上，证书用于3个位置，所以有3个地址。
>
> [https://10.64.0.1](https://10.64.0.1/) 表示用户访问过来的地址，是10.64.0.1, 别人提供的证书的hosts包含这个地址，证书才有效。
>
> hosts表示，这个证书可以工作的位置并提供的端点。
>
> 如果给这个证书放在3个api server上，也给nginx使用，并且如果nginx提供的域名是[www.magedu.com](http://www.magedu.com/), 所以hosts添加[www.magedu.com](http://www.magedu.com/)

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca      kube-apiserver-csr.json | ../cfssljson -bare kube-apiserver
2021/02/13 19:07:30 [INFO] generate received request
2021/02/13 19:07:30 [INFO] received CSR
2021/02/13 19:07:30 [INFO] generating key: rsa-2048
2021/02/13 19:07:30 [INFO] encoded CSR
2021/02/13 19:07:30 [INFO] signed certificate with serial number 184641680166666388161817679183199617201534181463
2021/02/13 19:07:30 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~/k8s-cert/cert# find . -mmin -1
.
./kube-apiserver-key.pem
./kube-apiserver.pem
./kube-apiserver.csr
```

api 连接kubelet，发出命令调用docker引擎启动pod

| 默认 CN                       | 父级 CA       | O (位于 Subject 中) | 类型   | **主机 (SAN)** |
| ----------------------------- | ------------- | ------------------- | ------ | -------------- |
| kube-apiserver-kubelet-client | kubernetes-ca | system:masters      | client |                |

| 默认 CN                       | 建议的密钥路径               | 建议的证书路径               | 命令           | 密钥参数            | 证书参数                    |
| ----------------------------- | ---------------------------- | ---------------------------- | -------------- | ------------------- | --------------------------- |
| kube-apiserver-kubelet-client | apiserver-kubelet-client.key | apiserver-kubelet-client.crt | kube-apiserver | –kubelet-client-key | –kubelet-client-certificate |

```
root@kube20-master01:~/k8s-cert/cert# cp kube-apiserver-csr.json kube-apiserver-kubelet-client-csr.json
root@kube20-master01:~/k8s-cert/cert# cat kube-apiserver-kubelet-client-csr.json
{
+  "CN": "kube-apiserver-kubelet-client",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
+    "O": "system:masters",
    "OU": "system"
  }],
+    "hosts": []
}
```

> cn, o, hosts

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca      kube-apiserver-kubelet-client-csr.json | ../cfssljson -bare kube-apiserver-kubelet-client
2021/02/13 19:12:21 [INFO] generate received request
2021/02/13 19:12:21 [INFO] received CSR
2021/02/13 19:12:21 [INFO] generating key: rsa-2048
2021/02/13 19:12:21 [INFO] encoded CSR
2021/02/13 19:12:21 [INFO] signed certificate with serial number 496225717759994069577708208414829186130732717111
2021/02/13 19:12:21 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~/k8s-cert/cert# find . -mmin -1
.
./kube-apiserver-kubelet-client-csr.json
./kube-apiserver-kubelet-client-key.pem
./kube-apiserver-kubelet-client.pem
./kube-apiserver-kubelet-client.csr
```

| 默认 CN            | 建议的密钥路径         | 建议的证书路径         | 命令                    | 密钥参数               | 证书参数                      |
| ------------------ | ---------------------- | ---------------------- | ----------------------- | ---------------------- | ----------------------------- |
| front-proxy-client | front-proxy-client.key | front-proxy-client.crt | kube-apiserver          | –proxy-client-key-file | –proxy-client-cert-file       |
| front-proxy-ca     | front-proxy-ca.key     | front-proxy-ca.crt     | kube-controller-manager |                        | –requestheader-client-ca-file |
| front-proxy-ca     | front-proxy-ca.key     | front-proxy-ca.crt     | kube-apiserver          |                        | –requestheader-client-ca-file |

| 默认 CN            | 父级 CA                   | O (位于 Subject 中) | 类型   | 主机 (SAN) |
| ------------------ | ------------------------- | ------------------- | ------ | ---------- |
| front-proxy-client | kubernetes-front-proxy-ca |                     | client |            |

api server里是aggregator 反代内部的api server, 如果用户自定义api server, 需要使用自定义资源时，就需要在api server反代到aggregated pod, 所以也需要证书

```
root@kube20-master01:~/k8s-cert/cert# cp kube-apiserver-csr.json front-proxy-client-csr.json
root@kube20-master01:~/k8s-cert/cert# cat front-proxy-client-csr.json
{
+  "CN": "front-proxy-client",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}

root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca      front-proxy-client-csr.json | ../cfssljson -bare front-proxy-client
2021/02/13 19:17:35 [INFO] generate received request
2021/02/13 19:17:35 [INFO] received CSR
2021/02/13 19:17:35 [INFO] generating key: rsa-2048
2021/02/13 19:17:36 [INFO] encoded CSR
2021/02/13 19:17:36 [INFO] signed certificate with serial number 133623264107732499922600814561057672513832601933
2021/02/13 19:17:36 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~/k8s-cert/cert# find . -mmin -1
.
./kube-apiserver-kubelet-client-key.pem
./kube-apiserver-kubelet-client.pem
./kube-apiserver-kubelet-client.csr
./front-proxy-client-csr.json
```

准备目录结构

```
# ca
cp k8s-ca.pem /etc/kubernetes/pki/ca.crt
cp k8s-ca-key.pem /etc/kubernetes/pki/ca.key
# api -> kubelet
cp  kube-apiserver-kubelet-client.pem /etc/kubernetes/pki/apiserver-kubelet-client.crt
cp  kube-apiserver-kubelet-client-key.pem /etc/kubernetes/pki/apiserver-kubelet-client.key
# api的 aggregator -> aggregated pod
cp front-proxy-client.pem  /etc/kubernetes/pki/front-proxy-client.crt
cp front-proxy-client-key.pem  /etc/kubernetes/pki/front-proxy-client.key

# api的 aggregator 与 aggregated通信的ca
cp kubernetes-front-proxy-ca.pem /etc/kubernetes/pki/front-proxy-ca.crt
cp kubernetes-front-proxy-ca-key.pem /etc/kubernetes/pki/front-proxy-ca.key

# service account key
cp k8s-ca.pem /etc/kubernetes/pki/sa.pub
cp k8s-ca-key.pem /etc/kubernetes/pki/sa.key

# 生成token
BOOTSTRAP_TOKEN="$(head -c 6 /dev/urandom | md5sum | head -c 6).$(head -c 16 /dev/urandom | md5sum | head -c 16)"
echo "$BOOTSTRAP_TOKEN,\"system:bootstrapper\",10001,\"system:bootstrappers\"" > /etc/kubernetes/token.csv

# api server的证书
cp kube-apiserver.pem /etc/kubernetes/pki/apiserver.crt
cp kube-apiserver-key.pem /etc/kubernetes/pki/apiserver.key
```

以上生成证书后，略过以下生成证书直接配置api server组件

```
root@kube20-master01:~/k8s-certs-generator# pwd
/root/k8s-certs-generator
root@kube20-master01:~/k8s-certs-generator# ls
etcd  etcd-certs-gen.sh  gencerts.sh  k8s-certs-gen.sh  openssl.conf  README.md
root@master01:~/k8s-certs-generator# bash gencerts.sh k8s
Enter Domain Name [ilinux.io]: magedu.com              # 主机名后缀
Enter Kubernetes Cluster Name [kubernetes]: kubernetes # 集群名无所谓
Enter the IP Address in default namespace 
  of the Kubernetes API Server[10.96.0.1]:  10.96.0.1           # api地址暴露在默认名称空间中，这个应该使用service网段的第1个地址
Enter Master servers name[master01 master02 master03]: master01 master02 master03       # 主机名master01.magedu.com 但是之前domain name已经写了，所以会自动补后缀      


root@kube20-master01:~/k8s-certs-generator# tree kubernetes/
kubernetes/ # 公用证书
├── CA # k8s CA证书
│   ├── ca.crt
│   └── ca.key
├── front-proxy # 用户 -> aggregator -> 自定义APIservice: api http-> 自定义pod; 自定义pod -> api可以使用 front-proxy-client.crt
│   ├── front-proxy-ca.crt
│   ├── front-proxy-ca.key
│   ├── front-proxy-client.crt
│   └── front-proxy-client.key
├── ingress
│   ├── ingress-server.crt
│   ├── ingress-server.key
│   └── patches
│       └── ingress-tls.patch
├── kubelet
│   ├── auth
│   │   ├── bootstrap.conf
│   │   └── kube-proxy.conf
│   └── pki
│       ├── ca.crt
│       ├── kube-proxy.crt
│       └── kube-proxy.key
├── master01 # master01专用目录
│   ├── auth
│   │   ├── admin.conf
│   │   ├── controller-manager.conf
│   │   └── scheduler.conf
│   ├── pki
│   │   ├── apiserver.crt
│   │   ├── apiserver-etcd-client.crt # etcd生成的给api server客户端证书
│   │   ├── apiserver-etcd-client.key
│   │   ├── apiserver.key
│   │   ├── apiserver-kubelet-client.crt
│   │   ├── apiserver-kubelet-client.key
│   │   ├── ca.crt
│   │   ├── ca.key
│   │   ├── front-proxy-ca.crt #
│   │   ├── front-proxy-ca.key
│   │   ├── front-proxy-client.crt
│   │   ├── front-proxy-client.key
│   │   ├── kube-controller-manager.crt
│   │   ├── kube-controller-manager.key
│   │   ├── kube-scheduler.crt
│   │   ├── kube-scheduler.key
│   │   ├── sa.key
│   │   └── sa.pub
│   └── token.csv # 基于token认证的配置文件
```

准备证书

```
scp -rp kubernetes/master01 master01:/etc/kubernetes
scp -rp kubernetes/master02 master02:/etc/kubernetes
scp -rp kubernetes/master03 master03:/etc/kubernetes

# 检验
root@kube20-master01:~/k8s-certs-generator# ls /etc/kubernetes/
auth  pki  token.csv

root@kube20-master02:~# ls /etc/kubernetes/
auth  pki  token.csv

root@kube20-master03:~# ls /etc/kubernetes/
auth  pki  token.csv
root@kube20-master03:~# tree /etc/kubernetes/
/etc/kubernetes/
├── auth
│   ├── admin.conf                # root权限
│   ├── controller-manager.conf   # kubeconfig,用户为system:kube-controller-manager, 已经集群内建绑定应有的权限
│   └── scheduler.conf            # kubeconfig,用户为system:kube-scheduler, 已经集群内建绑定应有的权限
├── pki                 # 证书
│   ├── apiserver.crt
│   ├── apiserver-etcd-client.crt
│   ├── apiserver-etcd-client.key
│   ├── apiserver.key
│   ├── apiserver-kubelet-client.crt
│   ├── apiserver-kubelet-client.key
│   ├── ca.crt
│   ├── ca.key
│   ├── front-proxy-ca.crt
│   ├── front-proxy-ca.key
│   ├── front-proxy-client.crt
│   ├── front-proxy-client.key
│   ├── kube-controller-manager.crt
│   ├── kube-controller-manager.key
│   ├── kube-scheduler.crt
│   ├── kube-scheduler.key
│   ├── sa.key
│   └── sa.pub
└── token.csv # 完成bootstrap的token和用户和组保存位置，可以用来对用户授权
```

### 配置master01 *

```
root@kube20-master01:~# tar xvf kubernetes-server-linux-amd64.tar.gz -C /usr/local/

root@kube20-master01:/usr/local# tree kubernetes/server/
kubernetes/server/
└── bin
    ├── apiextensions-apiserver
    ├── kubeadm
    ├── kube-aggregator
    ├── kube-apiserver
    ├── kube-apiserver.docker_tag
    ├── kube-apiserver.tar
    ├── kube-controller-manager
    ├── kube-controller-manager.docker_tag
    ├── kube-controller-manager.tar
    ├── kubectl
    ├── kubelet
    ├── kube-proxy
    ├── kube-proxy.docker_tag
    ├── kube-proxy.tar
    ├── kube-scheduler
    ├── kube-scheduler.docker_tag
    ├── kube-scheduler.tar
    └── mounter
    
1 directory, 18 files
```

各个程序的配置文件写起来麻烦，有现成的

https://github.com/iKubernetes/k8s-bin-inst

```
root@kube20-master01:~# git clone https://github.com/iKubernetes/k8s-bin-inst
```

#### api server配置介绍

```
k8s-bin-inst/master/etc/kubernetes/config
# 所有应用程序公共配置
KUBE_LOGTOSTDERR="--logtostderr=true" # 日志

# journal message level, 0 is debug
# 级别，生产不应该是debug
KUBE_LOG_LEVEL="--v=0"

# Should this cluster be allowed to run privileged docker containers
# 允许特权容器
KUBE_ALLOW_PRIV="--allow-privileged=true"
```

api sever

```
# 监听地址
KUBE_API_ADDRESS="--advertise-address=0.0.0.0"

# 端口 insecure-port非0就是8080
KUBE_API_PORT="--secure-port=6443 --insecure-port=0"

# 修改为etcd集群地址
KUBE_ETCD_SERVERS="--etcd-servers=https://k8s-master01.ilinux.io:2379,https://k8s-master02.ilinux.io:2379,https://k8s-master03.ilinux.io:2379"

# 集群地址，要和生产证书的默认地址在同一个网段
KUBE_SERVICE_ADDRESSES="--service-cluster-ip-range=10.96.0.0/12"

# 启动准入控制器
KUBE_ADMISSION_CONTROL="--enable-admission-plugins=NodeRestriction"

# authorization-mode启动认证插件
# client-ca-file 客户端认证ca
# enable-bootstrap-token-auth node引导时基于引导令牌认证. 那么多kubelet生成证书麻烦
	# 1. api server内部有自动签署工具：--controllers=*,bootstrapsigner,tokencleanerr, 拿着令牌的账号属于system:bootstrappers 组
	# 2. kubelet在node节点起动时，自动生成一个key, csr.
	# 3. node的kubelet 第一次连接api server时, 先认证共享密钥，共享密钥认证通过，kubelet才可以将csr发给api server
	# 4. api server签署证书，将证书返回给node
# server端支持的token  --token-auth-file=/etc/kubernetes/token.csv 
	
# Api -> ETCD
# etcd-* apiserver连接etcd的ca/证书

# Api -> kubelet
# kubelet-* k8s api server需要通知kubelet, 连接https

# Api aggregator -> aggregated pod
# proxy* api server需要连接aggregator. 
# requestheader* aggregated的pod, 允许哪个证书来认证。 aggregator向后端代理时添加的首部。

# service-account-key-file 每个pod有默认的serviceaccount, 而且这个serviceaccount会使用密钥连接api server, 需要确定pod的service身份。
## 是公钥加密的 sa.pub公钥，sa.key私钥在 apiserver服务端。所以pod使用公钥签名，apiserver 使用私钥解密确认pod身份发送的信息没有被篡改。

# ApiServer 自已的证书
# tls* api server作为server端的证书

KUBE_API_ARGS="--authorization-mode=Node,RBAC \ 
    --client-ca-file=/etc/kubernetes/pki/ca.crt \
    --enable-bootstrap-token-auth=true \
    --token-auth-file=/etc/kubernetes/token.csv \
    --etcd-cafile=/etc/etcd/pki/ca.crt \
    --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt \
    --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key \
    --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt \
    --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key \
    --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname \
    --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt \
    --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key \
    --requestheader-allowed-names=front-proxy-client \
    --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
    --requestheader-extra-headers-prefix=X-Remote-Extra- \
    --requestheader-group-headers=X-Remote-Group \
    --requestheader-username-headers=X-Remote-User\
    --service-account-key-file=/etc/kubernetes/pki/sa.pub \
    --tls-cert-file=/etc/kubernetes/pki/apiserver.crt \
    --tls-private-key-file=/etc/kubernetes/pki/apiserver.key"
```

unit-file

```
root@kube20-master01:~# cat k8s-bin-inst/master/unit-files/kube-apiserver.service 
[Unit]
Description=Kubernetes API Server
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=network.target
After=etcd.service

[Service]
EnvironmentFile=-/etc/kubernetes/config 
EnvironmentFile=-/etc/kubernetes/apiserver 
User=kube # 启动服务的用户
ExecStart=/usr/local/kubernetes/server/bin/kube-apiserver \
	    $KUBE_LOGTOSTDERR \
	    $KUBE_LOG_LEVEL \
	    $KUBE_ETCD_SERVERS \
	    $KUBE_API_ADDRESS \
	    $KUBE_API_PORT \
	    $KUBELET_PORT \
	    $KUBE_ALLOW_PRIV \
	    $KUBE_SERVICE_ADDRESSES \
	    $KUBE_ADMISSION_CONTROL \
	    $KUBE_API_ARGS
Restart=on-failure
Type=notify
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

#### 配置api server组件 *

```
root@kube20-master01:~# git clone https://github.com/iKubernetes/k8s-bin-inst
root@kube20-master01:~# cp -a k8s-bin-inst/master/etc/kubernetes/* /etc/kubernetes/
root@kube20-master01:~# cp -a k8s-bin-inst/master/unit-files/* /lib/systemd/system/

# 检验 master端的配置，kubeconfig,证书
root@kube20-master01:~# tree /etc/kubernetes/
/etc/kubernetes/
├── apiserver # 配置
├── auth # kubeconfig
│   ├── admin.conf
│   ├── controller-manager.conf
│   └── scheduler.conf
├── config # 配置
├── controller-manager # 配置
├── pki # 证书
│   ├── apiserver.crt
│   ├── apiserver-etcd-client.crt
│   ├── apiserver-etcd-client.key
│   ├── apiserver.key
│   ├── apiserver-kubelet-client.crt
│   ├── apiserver-kubelet-client.key
│   ├── ca.crt
│   ├── ca.key
│   ├── front-proxy-ca.crt
│   ├── front-proxy-ca.key
│   ├── front-proxy-client.crt
│   ├── front-proxy-client.key
│   ├── kube-controller-manager.crt
│   ├── kube-controller-manager.key
│   ├── kube-scheduler.crt
│   ├── kube-scheduler.key
│   ├── sa.key
│   └── sa.pub
├── scheduler # 配置
└── token.csv # bootstrapper

# unit文件
```

修改config文件

> 日志级别，0调度方便，生产中为1-2甚至更高

修改api server文件

> etcd
>
> service cluster ip range 和生成证书的网络一样

```
# /etc/kubernetes/apiserver 

KUBE_API_ADDRESS="--advertise-address=0.0.0.0"

# The port on the local server to listen on.
KUBE_API_PORT="--secure-port=6443 --insecure-port=0"

# Comma separated list of nodes in the etcd cluster
+KUBE_ETCD_SERVERS="--etcd-servers=https://192.168.137.51:2379,https://192.168.137.52:2379,https://192.168.137.53:2379"

# Address range to use for services
+KUBE_SERVICE_ADDRESSES="--service-cluster-ip-range=10.64.0.0/12"

# default admission control policies
KUBE_ADMISSION_CONTROL="--enable-admission-plugins=NodeRestriction"

# Add your own!
KUBE_API_ARGS="--authorization-mode=Node,RBAC \
    --client-ca-file=/etc/kubernetes/pki/ca.crt \
    --enable-bootstrap-token-auth=true \
    --etcd-cafile=/etc/etcd/pki/ca.crt \
    --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt \
    --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key \
    --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt \
    --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key \
    --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname \
    --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt \
    --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key \
    --requestheader-allowed-names=front-proxy-client \
    --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
    --requestheader-extra-headers-prefix=X-Remote-Extra- \
    --requestheader-group-headers=X-Remote-Group \
    --requestheader-username-headers=X-Remote-User\
    --service-account-key-file=/etc/kubernetes/pki/sa.pub \
+	--service-account-signing-key-file=/etc/kubernetes/pki/sa.key \
+	--service-account-issuer=api \
+   --service-node-port-range=20000-50000 \
+   --enable-aggregator-routing=true \
    --tls-cert-file=/etc/kubernetes/pki/apiserver.crt \
    --tls-private-key-file=/etc/kubernetes/pki/apiserver.key \
    --token-auth-file=/etc/kubernetes/token.csv  "
```

> 10.96.0.0/12 要和生成证书的service API同网段
>
> –enable-aggregator-routing=true 在master没有配置kube-proxy就不会将service变为ipvs/iptables规则，所以需要指定此选项

> https://jpweber.io/blog/a-look-at-tokenrequest-api/

修改unit文件

> 准备kube用户

k8s临时状态数据

```
root@kube20-master01:~# useradd -r kube
root@kube20-master01:~# chown kube.kube /etc/kubernetes/pki/*.key
```

token文件

```
root@kube20-master01:~# cat /etc/kubernetes/token.csv
edb330.48fee401ef38cd26,"system:bootstrapper",10001,"system:bootstrappers"

# 第1个字段是 kubelet认证的token
# 第2个字段是 认证之后的用户
# 第4个字段是 认证之后的组
```

启动

配置日志级别

```
root@kube20-master01:~# cat /etc/kubernetes/config 
###
# kubernetes system config
#
# The following values are used to configure various aspects of all
# kubernetes services, including
#
#   kube-apiserver.service
#   kube-controller-manager.service
#   kube-scheduler.service
#   kubelet.service
#   kube-proxy.service
# logging to stderr means we get it in the systemd journal
KUBE_LOGTOSTDERR="--logtostderr=true"

# journal message level, 0 is debug
+KUBE_LOG_LEVEL="--v=10"

# Should this cluster be allowed to run privileged docker containers
KUBE_ALLOW_PRIV="--allow-privileged=true"

root@kube20-master01:~# systemctl start kube-apiserver
root@kube20-master01:~# systemctl status kube-apiserver
root@kube20-master01:~# systemctl enable kube-apiserver

# 切换终端查看日志
root@kube20-master01:~# journalctl -u kube-apiserver --since="$(date -d"-10 second" +"%F %T")"


# 避免重启主机集群异常
root@kube20-master01:~# systemctl enable kube-apiserver

# 启动慢，连接etcd需要初始化
```

#### 配置kubectl命令

生成管理员账号, 由于上面的kubelet-client属于system:masters组，直接使用这个证书生成master即可

```
# 生成配置文件
/usr/local/kubernetes/server/bin/kubectl config set-cluster kubernetes --server=https://192.168.137.51:6443  --certificate-authority=/etc/kubernetes/pki/ca.crt  --embed-certs=true  --kubeconfig=/etc/kubernetes/auth/admin.conf

# 设定集群用户
/usr/local/kubernetes/server/bin/kubectl config set-credentials admin --client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt --client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key --username=admin --embed-certs=true  --kubeconfig=/etc/kubernetes/auth/admin.conf
	#--username=admin 集群用户，无所谓，重点是证书的用户
	
#查看证书信息
root@kube20-master01:~# ./cfssl-certinfo -cert /etc/kubernetes/pki/apiserver-kubelet-client.crt 
  "subject": {
+    "common_name": "kube-apiserver-kubelet-client", # 这个不重要， 因为基于管理员授权
    "country": "China",
    "organization": "system:masters",
    "organizational_unit": "system",
    "locality": "HeFei",
    "province": "AnHui",
    "names": [
      "China",
      "AnHui",
      "HeFei",
+      "system:masters", # 集群管理员
      "system",
      "kube-apiserver-kubelet-client"
    ]
  },
  
# 设定上下文
/usr/local/kubernetes/server/bin/kubectl config set-context admin@kubernetes --cluster=kubernetes --user=admin --kubeconfig=/etc/kubernetes/auth/admin.conf

# 切换当前上下文
 /usr/local/kubernetes/server/bin/kubectl config use-context admin@kubernetes --kubeconfig=/etc/kubernetes/auth/admin.conf
 
 
 # 查看配置 
root@kube20-master01:~# /usr/local/kubernetes/server/bin/kubectl config view --kubeconfig=/etc/kubernetes/auth/admin.conf
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.137.51:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: admin
  name: admin@kubernetes
current-context: admin@kubernetes
kind: Config
preferences: {}
users:
- name: admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
    username: admin
```

脚本已经生成连接当前集群的管理账号

```
root@kube20-master01:~# install -dv ~/.kube
root@kube20-master01:~# cp /etc/kubernetes/auth/admin.conf ~/.kube/config

root@kube20-master01:~# ln -sv /usr/local/kubernetes/server/bin/kubectl /usr/bin/

root@kube20-master01:~# kubectl config view 
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.137.51:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: admin
  name: admin@kubernetes
current-context: admin@kubernetes
kind: Config
preferences: {}
users:
- name: admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
    username: admin
```

查看主节点的端口

```
root@kube20-master01:~# ss -tnl | grep 6443
LISTEN   0         20480                     *:6443                   *:*       

root@kube20-master01:~# kubectl get all -A
NAMESPACE   NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
default     service/kubernetes   ClusterIP   10.64.0.1    <none>        443/TCP   12m

# service是iptables/ipvs规则所以只有在kube-proxy启动才有用。
# 生成证书是10.64.0.1 加入证书，这个IP将不能在集群内通信，需要重建集群，使用这个IP作为入口
```

#### 允许node加入集群

添加system:bootstraper 用户 绑定 system:node-bootstrapper 角色，即用户就有了可以拉起一个node的权限

```
# api server通过这个 token文件，来认证kubelet
root@kube20-master01:~# cat /etc/kubernetes/token.csv 
edb330.48fee401ef38cd26,"system:bootstrapper",10001,"system:bootstrappers"

# kubelet的bootstrapper选项对应的Kubeconfig是token生成的文件，用户只要携带token(bootstrap kubeconfig中的credential 并不是用户)， apiserver只要识别到token和master一致，就当作第2和第4个字段对应的用户和组。

# 所以只要授权到用户和组，拿着token来的人就可以有对应的权限。
```

- 角色 - 用户

  ```
  root@kube20-master01:~# kubectl create clusterrolebinding system:bootstrapper --user=system:bootstrapper --clusterrole=system:node-bootstrapper
  ```

- 角色 - 组

  ```
  root@kube20-master01:~# kubectl create clusterrolebinding system:bootstrapper --group=system:bootstrappers --clusterrole=system:node-bootstrapper
  ```

```
root@kube20-master01:~# kubectl get clusterrolebinding system:bootstrapper
NAME                  ROLE                                   AGE
system:bootstrapper   ClusterRole/system:node-bootstrapper   25s
```

因为api server端启动的token认证信息的这个用户(第2个字段)，这个组(4字段)，默认不允许bootstrapper, 所以以上就授权

```
root@kube20-master01:~# cat /etc/kubernetes/token.csv 
edb330.48fee401ef38cd26,"system:bootstrapper",10001,"system:bootstrappers"
```

然后api server启动指定这个 token, node节点启动kubelet指定的配置文件用户

```
kubelet --bootstrap-kubeconfig=/etc/kubernetes/auth/bootstrap.conf
```

node的kubelet 第一次连接api server时, 先认证共享密钥（cdde8f.75e1739dd28b5499，共享密钥认证通过，api 就识别为2/4字段的用户或组，并且用户有拉集群的权限，kubelet才可以将csr发给api server, kube-controller才签发证书

查看kubelet与kube-apiserver通信

```
root@kube20-master01:~# systemctl status kube-apiserver
```

接下来配置kube-controller，就可以完成签发证书

#### controller manager配置介绍

```
# 通用配置
root@kube20-master01:~# cat /etc/kubernetes/config
略，参考 api server配置介绍

# controller manager配置
root@kube20-master01:~# cat /etc/kubernetes/controller-manager 
# --bind-address=127.0.0.1  自已监听地址127.0.0.1 因为api server绑定在0.0.0.0 所以可以直接与api server通信
# --cluster-cidr=10.244.0.0/16 # pod网络插件的网段; flannel 10.244.0.0/16; calico 192.168.0.0/16;
# --node-cidr-mask-size=24  # flannel会给每个节点划分一个子网，这个子网的掩码是多长？ 24位就是划分255个子网
#  --service-cluster-ip-range=10.96.0.0/12  # service的网段

# cluster-signing* controller-manager给kubelet签发证书的ca

# authentication* 连接api server的kubeconfig文件
    # kubectl config view --kubeconfig=/etc/kubernetes/auth/controller-manager.conf
    #users:
    #- name: system:kube-controller-manager # controller-manager用户的用户名, 需要k8s内置的用户名，api server启动时将这个用户绑定至了controller-manager应该有的角色上。system:kube-controller-manager

# --controllers=*,bootstrapsigner,tokencleaner 
	# kubelet提交 证书签署请求 csr. signer来签署
	# tokencleaner 会清理token. 
	# 为了避免node盗用，应该api server指定的token定期换，node加入时就需要新的token
	
#  --leader-elect=true 默认controller启动分布式锁，抢占endpoint资源


KUBE_CONTROLLER_MANAGER_ARGS="--bind-address=127.0.0.1 \
    --allocate-node-cidrs=true \
    --service-cluster-ip-range=10.96.0.0/12 \
    --authentication-kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --authorization-kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --client-ca-file=/etc/kubernetes/pki/ca.crt \
    --cluster-cidr=10.244.0.0/16 \
    --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt \
    --cluster-signing-key-file=/etc/kubernetes/pki/ca.key \
    --controllers=*,bootstrapsigner,tokencleaner \
    --kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --leader-elect=true \
    --node-cidr-mask-size=24 \
    --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
    --root-ca-file=/etc/kubernetes/pki/ca.crt \
    --service-account-private-key-file=/etc/kubernetes/pki/sa.key \
    --use-service-account-credentials=true"
```

#### 配置controller manager组件 *

先生成证书 [https://kubernetes.io/zh/docs/setup/best-practices/certificates/#%E6%89%8B%E5%8A%A8%E9%85%8D%E7%BD%AE%E8%AF%81%E4%B9%A6](https://kubernetes.io/zh/docs/setup/best-practices/certificates/#手动配置证书)

| 文件名                  | 凭据名称                   | 默认 CN                               | O (位于 Subject 中) |
| ----------------------- | -------------------------- | ------------------------------------- | ------------------- |
| admin.conf              | default-admin              | kubernetes-admin                      | system:masters      |
| kubelet.conf            | default-auth               | system:node:`<nodeName>` （参阅注释） | system:nodes        |
| controller-manager.conf | default-controller-manager | system:kube-controller-manager        |                     |
| scheduler.conf          | default-scheduler          | system:kube-scheduler                 |                     |

```
root@kube20-master01:~/k8s-cert/cert# cp kube-apiserver-csr.json kube-controller-manager-csr.json
root@kube20-master01:~/k8s-cert/cert# cat kube-controller-manager-csr.json 
{
+  "CN": "system:kube-controller-manager",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
```

> 因为是controller连接kube-apiserver,所以仅是client.

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca     kube-controller-manager-csr.json | ../cfssljson -bare kube-controller-manager
2021/02/15 16:34:22 [INFO] generate received request
2021/02/15 16:34:22 [INFO] received CSR
2021/02/15 16:34:22 [INFO] generating key: rsa-2048
2021/02/15 16:34:22 [INFO] encoded CSR
2021/02/15 16:34:22 [INFO] signed certificate with serial number 639401750551026602122567318430777534064679532660
2021/02/15 16:34:22 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~/k8s-cert/cert#  find . -mmin -1
.
./kube-controller-manager.pem
./kube-controller-manager-csr.json
./kube-controller-manager-key.pem
./kube-controller-manager.csr
```

准备一些证书文件

```
export KUBECONFIG=/etc/kubernetes/auth/controller-manager.conf
export ADDR=https://192.168.137.51:6443
export USERNAME=default-controller-manager
export CERT=kube-controller-manager.pem
export KEY=kube-controller-manager-key.pem

kubectl config set-cluster default-cluster --server=$ADDR --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs
kubectl config set-credentials $USERNAME --client-certificate=$CERT --client-key=$KEY --username=$USERNAME --embed-certs=true 
kubectl config set-context default-system --cluster default-cluster --user $USERNAME
kubectl config use-context default-system
export KUBECONFIG=
chown kube.kube /etc/kubernetes/auth/controller-manager.conf

root@kube20-master01:~/k8s-cert/cert# cat /etc/kubernetes/controller-manager 
KUBE_CONTROLLER_MANAGER_ARGS="--bind-address=127.0.0.1 \
    --allocate-node-cidrs=true \
+    --service-cluster-ip-range=10.64.0.0/12 \
    --authentication-kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --authorization-kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --client-ca-file=/etc/kubernetes/pki/ca.crt \
+    --cluster-cidr=10.244.0.0/16 \
    --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt \
    --cluster-signing-key-file=/etc/kubernetes/pki/ca.key \
    --controllers=*,bootstrapsigner,tokencleaner \
    --kubeconfig=/etc/kubernetes/auth/controller-manager.conf \
    --leader-elect=true \
+    --node-cidr-mask-size=24 \
    --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt \
    --root-ca-file=/etc/kubernetes/pki/ca.crt \
    --service-account-private-key-file=/etc/kubernetes/pki/sa.key \
+    --horizontal-pod-autoscaler-sync-period=5s \
+    --node-monitor-grace-period 20s \
+    --leader-elect-resource-lock=endpoints \
    --use-service-account-credentials=true"
```

> service-cluster-ip-range 证书会指定，api server会指定
>
> cluster-cidr 网络插件的网段
>
> 新版默认锁的leases资源，我们也可以锁endpoints资源，保证抢占到资源的组件是主组件

```
root@kube20-master01:~/k8s-cert/cert# systemctl start kube-controller-manager
root@kube20-master01:~/k8s-cert/cert# systemctl status kube-controller-manager
● kube-controller-manager.service - Kubernetes Controller Manager
   Loaded: loaded (/lib/systemd/system/kube-controller-manager.service; disabled; vendor preset: enabled)
   Active: active (running) since Sat 2021-02-06 14:30:51 CST; 2s ago
     Docs: https://github.com/GoogleCloudPlatform/kubernetes
 Main PID: 6284 (kube-controller)
    Tasks: 8 (limit: 2318)
   CGroup: /system.slice/kube-controller-manager.service
           └─6284 /usr/local/kubernetes/server/bin/kube-controller-manager --logtostderr=true --v=0 --bind-address=127.0.0.1 --allocate-node-cidrs=true --authentication-kubeconfig=/etc/kubernetes/auth/controller-manager.conf --authorization-kubeconfig=/etc/kubernetes/auth/controller-manager.conf --client-ca-file=/

Feb 06 14:30:51 master01.magedu.com systemd[1]: Started Kubernetes Controller Manager.
Feb 06 14:30:52 master01.magedu.com kube-controller-manager[6284]: I0206 14:30:52.483592    6284 serving.go:331] Generated self-signed cert in-memory

root@kube20-master01:~# systemctl enable kube-controller-manager

root@kube20-master01:~/k8s-cert/cert# kubectl get cs
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS      MESSAGE                                                                                       ERROR
scheduler            Unhealthy   Get "http://127.0.0.1:10251/healthz": dial tcp 127.0.0.1:10251: connect: connection refused   
controller-manager   Healthy     ok                                                                                            
etcd-0               Healthy     {"health": "true"}                                                                            
etcd-1               Healthy     {"health": "true"}                                                                            
etcd-2               Healthy     {"health": "true"} 

# 确保有权限，这是 kubectl get leases.coordination.k8s.io -A
root@kube20-master01:~/cert# kubectl get leases --kubeconfig=/etc/kubernetes/auth/controller-manager.conf   -A
NAMESPACE     NAME                      HOLDER                                                      AGE
kube-system   kube-controller-manager   master01.mykernel.cn_0ba4eb7f-40af-4f88-b2d5-a41792c85a86   15m

root@kube20-master01:~/cert# kubectl get endpoints --kubeconfig=/etc/kubernetes/auth/controller-manager.conf   -n kube-system
NAME                      ENDPOINTS   AGE
kube-controller-manager   <none>      109s
```

#### kube-scheduler配置介绍

```
root@kube20-master01:~/cert# cat /etc/kubernetes/scheduler 
# kubeconfig 连接api server
# root@kube20-master01:~# kubectl config view --kubeconfig=/etc/kubernetes/auth/scheduler.conf
# users:
# - name: system:kube-scheduler # 必须这个用户名，因为默认集群binding了这个用户至scheduler应有的权限

# leader-elect 分布式高可用，必须启用

KUBE_SCHEDULER_ARGS="--address=127.0.0.1 \
    --kubeconfig=/etc/kubernetes/auth/scheduler.conf \
    --leader-elect=true"
```

#### 配置kube-scheduler组件 *

先生成证书 [https://kubernetes.io/zh/docs/setup/best-practices/certificates/#%E6%89%8B%E5%8A%A8%E9%85%8D%E7%BD%AE%E8%AF%81%E4%B9%A6](https://kubernetes.io/zh/docs/setup/best-practices/certificates/#手动配置证书)

| 文件名                  | 凭据名称                   | 默认 CN                               | O (位于 Subject 中) |
| ----------------------- | -------------------------- | ------------------------------------- | ------------------- |
| admin.conf              | default-admin              | kubernetes-admin                      | system:masters      |
| kubelet.conf            | default-auth               | system:node:`<nodeName>` （参阅注释） | system:nodes        |
| controller-manager.conf | default-controller-manager | system:kube-controller-manager        |                     |
| scheduler.conf          | default-scheduler          | system:kube-scheduler                 |                     |

```
root@kube20-master01:~/k8s-cert/cert# cp kube-apiserver-csr.json kube-scheduler-csr.json 
root@kube20-master01:~/k8s-cert/cert# cat kube-scheduler-csr.json 
{
+  "CN": "system:kube-scheduler",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
```

> 因为是kube-scheduler连接kube-apiserver,所以仅是client.

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca     kube-scheduler-csr.json | ../cfssljson -bare kube-scheduler
2021/02/15 18:44:03 [INFO] generate received request
2021/02/15 18:44:03 [INFO] received CSR
2021/02/15 18:44:03 [INFO] generating key: rsa-2048
2021/02/15 18:44:03 [INFO] encoded CSR
2021/02/15 18:44:03 [INFO] signed certificate with serial number 165731775402271130233555402135821838855977635676
2021/02/15 18:44:03 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~/k8s-cert/cert# find . -mmin -1
.
./kube-scheduler-csr.json
./kube-scheduler.pem
./kube-scheduler.csr
./kube-scheduler-key.pem
```

准备一些证书文件

```
export KUBECONFIG=/etc/kubernetes/auth/scheduler.conf # 配置文件中指定这个位置
export ADDR=https://192.168.137.51:6443  # 运行kube-scheduler节点的api server, 如果都指向、一个位置，api server压力大
export USERNAME=default-scheduler
export CERT=kube-scheduler.pem
export KEY=kube-scheduler-key.pem

kubectl config set-cluster default-cluster --server=$ADDR --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs
kubectl config set-credentials $USERNAME --client-certificate=$CERT --client-key=$KEY --username=$USERNAME --embed-certs=true 
kubectl config set-context default-system --cluster default-cluster --user $USERNAME
kubectl config use-context default-system

chown kube.kube $KUBECONFIG
export KUBECONFIG=

root@kube20-master01:~# systemctl start kube-scheduler
root@kube20-master01:~# systemctl status kube-scheduler
root@kube20-master01:~# systemctl enable kube-scheduler

# 查看抢占资源
root@kube20-master01:~# kubectl get leases -A
NAMESPACE     NAME                      HOLDER                                                      AGE
kube-system   kube-controller-manager   master01.mykernel.cn_0ba4eb7f-40af-4f88-b2d5-a41792c85a86   22m
kube-system   kube-scheduler            master01.mykernel.cn_73fff66d-9912-4df0-98a1-e1e672f07ba2   69s
root@kube20-master01:~# kubectl get cs
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS    MESSAGE              ERROR
controller-manager   Healthy   ok                   
scheduler            Healthy   ok                   
etcd-0               Healthy   {"health": "true"}   
etcd-2               Healthy   {"health": "true"}   
etcd-1               Healthy   {"health": "true"}   
root@kube20-master01:~# kubectl get all -A
NAMESPACE   NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
default     service/kubernetes   ClusterIP   10.64.0.1    <none>        443/TCP   52m
```

### 配置node01添加master01 *

node节点需要运行Pod: (kubelet + docker)

期望service 工作 ipvs模式，需要装入ipvs模块

Node节点初始化，略

#### 安装部署docker容器引擎

```
# docker 和 二进制下载版本一样
```

- [mirror docker](https://developer.aliyun.com/mirror/docker-ce?spm=a2c6h.13651102.0.0.3e221b11JBwFyb)


```
# step 1: 安装必要的一些系统工具
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
# step 2: 安装GPG证书
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key add -
# Step 3: 写入软件源信息
sudo add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

# 安装指定版本的Docker-CE:
# Step 1: 查找Docker-CE的版本:
apt-cache madison docker-ce
#   docker-ce | 17.03.1~ce-0~ubuntu-xenial | https://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial/stable amd64 Packages
#   docker-ce | 17.03.0~ce-0~ubuntu-xenial | https://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial/stable amd64 Packages
# Step 2: 安装指定版本的Docker-CE: (VERSION例如上面的17.03.1~ce-0~ubuntu-xenial)
sudo apt-get -y install docker-ce=[VERSION]
```

由于官方二进制是 1.20.2, 所以依此选择docker版本

```
root@kube20-node01:~# apt install docker-ce=5:20.10.2~3-0~ubuntu-bionic -y
```

配置docker加速器

```
root@kube20-node01:/etc/docker# cat /etc/docker/daemon.json 
{
	"registry-mirrors": ["https://9916w1ow.mirror.aliyuncs.com"]
}
root@kube20-node01:~# docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.2
root@kube20-node01:~# docker pull coredns/coredns:1.8.0
root@kube20-node01:~# docker pull quay.io/coreos/flannel:v0.13.1-rc2
root@kube20-node01:~# docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.2 coredns/coredns:1.8.0 quay.io/coreos/flannel:v0.13.1-rc2 -o node.tar
root@kube20-node01:~# scp node.tar kube20-master01
```

#### kubelet配置介绍

v 1.12版本之后，kubelet/kube-proxy支持配置文件加载参数

```
root@kube20-node01:~# tar xvf kubernetes-node-linux-amd64.tar.gz  -C /usr/local
kubernetes/node/
kubernetes/node/bin/
kubernetes/node/bin/kube-proxy
kubernetes/node/bin/kubeadm
kubernetes/node/bin/kubectl
kubernetes/node/bin/kubelet
```

配置文件

```
root@kube20-node01:~# tree k8s-bin-inst/nodes/var/lib/
k8s-bin-inst/nodes/var/lib/
├── kubelet
│   └── config.yaml
└── kube-proxy
    └── config.yaml
```

kubelet配置

```
root@kube20-master01:~# cat k8s-bin-inst/nodes/var/lib/kubelet/config.yaml 
+address: 0.0.0.0 # 监听地址
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    cacheTTL: 2m0s
    enabled: true
  x509:
+    clientCAFile: /etc/kubernetes/pki/ca.crt # kubelet的CA
+authorization: # 认证方式
  mode: Webhook
  webhook:
    cacheAuthorizedTTL: 5m0s
    cacheUnauthorizedTTL: 30s
+cgroupDriver: cgroupfs # 得和docker引擎保持一致。需要调用docker引擎启动Pod # docker info | grep 'Cgroup Driver'
cgroupsPerQOS: true
+clusterDNS: # 指定DNS的service地址用于Pod访问DNS.
+- 10.64.0.10
+clusterDomain: cluster.local # 指定集群域名后缀
configMapAndSecretChangeDetectionStrategy: Watch
containerLogMaxFiles: 5
containerLogMaxSize: 10Mi
contentType: application/vnd.kubernetes.protobuf
cpuCFSQuota: true
cpuCFSQuotaPeriod: 100ms
cpuManagerPolicy: none
cpuManagerReconcilePeriod: 10s
enableControllerAttachDetach: true
enableDebuggingHandlers: true
enforceNodeAllocatable:
- pods
eventBurst: 10
eventRecordQPS: 5
evictionHard:
  imagefs.available: 15%
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
evictionPressureTransitionPeriod: 5m0s
+failSwapOn: false              # swap启用状态下是否报错
fileCheckFrequency: 20s
hairpinMode: promiscuous-bridge
healthzBindAddress: 127.0.0.1
healthzPort: 10248
httpCheckFrequency: 20s
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
imageMinimumGCAge: 2m0s
iptablesDropBit: 15
iptablesMasqueradeBit: 14
kind: KubeletConfiguration
kubeAPIBurst: 10
kubeAPIQPS: 5
makeIPTablesUtilChains: true
maxOpenFiles: 1000000
maxPods: 110
nodeLeaseDurationSeconds: 40
nodeStatusUpdateFrequency: 10s
oomScoreAdj: -999
podPidsLimit: -1
port: 10250
registryBurst: 10
registryPullQPS: 5
resolvConf: /etc/resolv.conf
rotateCertificates: true
runtimeRequestTimeout: 2m0s
serializeImagePulls: true
+staticPodPath: /etc/kubernetes/manifests 
streamingConnectionIdleTimeout: 4h0m0s
syncFrequency: 1m0s
volumeStatsAggPeriod: 1m0s
```

> 集群dns: 10.64.0.10

配置文件

/etc/kubernetes配置文件

```
root@kube20-master01:~# cat k8s-bin-inst/nodes/etc/kubernetes/kubelet 

KUBELET_ADDRESS="--address=0.0.0.0"

# KUBELET_PORT="--port=10250"


# network-plugin k8s节点两个网络插件
 # 1. cni, 手工部署不会生成二进制程序
 # 2. kubenet

# config kubelet的配置

# kubeconfig 指定kubelet接入api server.
	# 平时通信使用
	# 在启动kubelet时生成kubeconfig文件
	
# bootstrap-kubeconfig 以bootstrapper方式加入集群。加入使用



KUBELET_ARGS="--network-plugin=cni \
    --config=/var/lib/kubelet/config.yaml \
    --kubeconfig=/etc/kubernetes/auth/kubelet.conf \
    --bootstrap-kubeconfig=/etc/kubernetes/auth/bootstrap.conf"
```

查看 unit文件

```
root@kube20-master01:~# cat k8s-bin-inst/nodes/unit-files/kubelet.service 
[Unit]
Description=Kubernetes Kubelet Server
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/var/lib/kubelet
EnvironmentFile=-/etc/kubernetes/config
EnvironmentFile=-/etc/kubernetes/kubelet
ExecStart=/usr/local/kubernetes/node/bin/kubelet \
	    $KUBE_LOGTOSTDERR \
	    $KUBE_LOG_LEVEL \
	    $KUBELET_API_SERVER \
	    $KUBELET_ADDRESS \
	    $KUBELET_PORT \
	    $KUBELET_HOSTNAME \
	    $KUBE_ALLOW_PRIV \
	    $KUBELET_ARGS
Restart=on-failure
KillMode=process
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> 注意没有写明默认用户，则是管理员运行

查看bootstrapper的证书

```
root@kube20-master01:~# kubectl config view --kubeconfig=k8s-certs-generator/kubernetes/kubelet/auth/bootstrap.conf 
apiVersion: v1
clusters:
#- cluster:
+    certificate-authority-data: DATA+OMITTED # kubelet会获取这个公钥来签署证书，生成kubelet连接apiserver的kubeconfig
+    server: https://kubernetes-api.magedu.com:6443 # kubelet会获取这个地址作为api 入口
  name: kubernetes
contexts:
#- context:
    cluster: kubernetes
    user: system:bootstrapper
  name: system:bootstrapper@kubernetes
current-context: system:bootstrapper@kubernetes
kind: Config
preferences: {}
users:
#- name: system:bootstrapper
  user:
    token: REDACTED
```

#### 配置kubelet组件 *

基于bootstrapper方式加入集群，

1. 基于token认证，签发证书
2. 随后认证，基于证书认证

或者直接加入集群

| 文件名       | 凭据名称     | 默认 CN                               | O (位于 Subject 中) |
| ------------ | ------------ | ------------------------------------- | ------------------- |
| kubelet.conf | default-auth | system:node:`<nodeName>` （参阅注释） | system:nodes        |

k8s api server是高可用的，所以node节点的组件`kubelet`, `kube-proxy`是连接高可用节点的位置，是https认证连接，所以连接的地址是在api server的hosts列表中

```
root@kube20-master01:~/k8s-cert/cert# ../cfssl-certinfo -cert kube-apiserver.pem{
  "subject": {
    "common_name": "kube-apiserver",
    "country": "China",
    "organization": "system:HuaYang",
    "organizational_unit": "system",
    "locality": "ChengDu",
    "province": "SiChuan",
    "names": [
      "China",
      "SiChuan",
      "ChengDu",
      "system:HuaYang",
      "system",
      "kube-apiserver"
    ]
  },
  "sans": [
+    "kubernetes-api.mykernel.cn", # 集群入口
    "kubernetes",
    "kubernetes.default",
    "kubernetes.default.svc",
    "kubernetes.default.svc.cluster",
    "kubernetes.default.svc.cluster.local",
    "172.16.0.101",
    "172.16.0.102",
    "172.16.0.103",
    "10.64.0.1",
    "127.0.0.1"
  ],
```

由于Kubelet启动时，也是使用bootstrap的kubeconfig文件

```
export KUBECONFIG=/etc/kubernetes/auth/bootstrap.conf  # 配置文件中指定这个位置
export ADDR=https://kubernetes-api.mykernel.cn:6443 # 运行kube-scheduler节点的api server, 如果都指向 一个位置，api server压力大
export USERNAME=system:bootstrapper # 使用token认证时，不需要用户名，但是需要指定集群用户名，这个与认证无关，可以写system:bootstrapper，方便记忆
export TOKEN=edb330.48fee401ef38cd26

kubectl config set-cluster default-cluster --server=$ADDR --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs
kubectl config set-credentials $USERNAME --token=$TOKEN
kubectl config set-context default-system --cluster default-cluster --user $USERNAME
kubectl config use-context default-system

chown kube.kube $KUBECONFIG
export KUBECONFIG=
```

生成bootstrap配置

```
export DOMAIN=mykernel.cn
bash deploy.sh node01.mykernel.cn
root@kube20-master01:~# ssh kube20-node01 "install -dv /etc/kubernetes/{auth,pki}"
root@kube20-master01:~# scp /etc/kubernetes/auth/bootstrap.conf kube20-node01:/etc/kubernetes/auth/
root@kube20-master01:~# scp -rp k8s-bin-inst/nodes/var/lib/* kube20-node01:/var/lib/
# unit file
root@kube20-master01:~# scp k8s-bin-inst/nodes/unit-files/* kube20-node01:/lib/systemd/system/
# 配置文件
root@kube20-master01:~# scp k8s-bin-inst/nodes/etc/kubernetes/{config,kubelet} kube20-node01:/etc/kubernetes/

# CA证书
root@kube20-master01:~# scp k8s-cert/cert/k8s-ca.pem  kube20-node01:/etc/kubernetes/pki/ca.crt
```

如果cfssl生成证书跳过以下代码配置证书环节，直接查看集群入口

```
root@kube20-master01:~# scp -rp k8s-bin-inst/nodes/etc/kubernetes/ kube20-node01:/etc/
root@kube20-node01:~# ls /etc/kubernetes/ # 全是配置文件
config  kubelet  proxy

root@kube20-master01:~# scp -rp k8s-bin-inst/nodes/var/lib/* kube20-node01:/var/lib/
# 验证
root@node01:~# ls /var/lib/kube* -d # 全是配置文件
/var/lib/kubelet  /var/lib/kube-proxy

#证书
root@kube20-master01:~# scp -rp k8s-certs-generator/kubernetes/kubelet/* kube20-node01:/etc/kubernetes/
root@kube20-master01:~# tree  k8s-certs-generator/kubernetes/kubelet/
k8s-certs-generator/kubernetes/kubelet/
├── auth
│   ├── bootstrap.conf  # kubelet加入集群
│   └── kube-proxy.conf 
└── pki
    ├── ca.crt 
    ├── kube-proxy.crt
    └── kube-proxy.key

# 验证auth, pki目录
root@kube20-node01:~# ls /etc/kubernetes/auth/ # 拉集群的bootstrap, 专为kubelet自动生成证书。而kube-proxy是静态生成证书
bootstrap.conf  kube-proxy.conf
root@kube20-node01:~# ls /etc/kubernetes/pki/
ca.crt  kube-proxy.crt  kube-proxy.key

# unit file
root@master01:~# scp k8s-bin-inst/nodes/unit-files/* kube20-node01:/lib/systemd/system/
```

配置集群入口

```
root@kube20-node01:~#:~# cat /etc/kubernetes/auth/bootstrap.conf 
#- name: kubernetes
  cluster:
+    server: https://kubernetes-api.magedu.com:6443 
```

> 此地址的修改会在生成kubelet的配置也会是对应的入口的域名
>
> 这个域名也是生成证书时，加入的域名 集群名-api.域名

```
root@kube20-node01:~# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	Base-Ubuntu

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.137.51 kube20-master01 kubernetes-api.mykernel.cn
192.168.137.52 kube20-master02
192.168.137.53 kube20-master03
192.168.137.54 kube20-node01

root@kube20-node01:~# ping kubernetes-api.mykernel.cn
PING kube20-master01 (192.168.137.51) 56(84) bytes of data.
64 bytes from kube20-master01 (192.168.137.51): icmp_seq=1 ttl=64 time=0.523 ms
64 bytes from kube20-master01 (192.168.137.51): icmp_seq=2 ttl=64 time=0.805 ms
^C
--- kube20-master01 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.523/0.664/0.805/0.141 ms

```

提供cni插件

- [containernetworking](https://github.com/containernetworking/plugins/releases)

![image-20210206152305669](http://myapp.img.mykernel.cn/image-20210206152305669.png)

找到符合平台的插件

```
root@kube20-node01:~# wget https://github.com/containernetworking/plugins/releases/download/v0.9.0/cni-plugins-linux-amd64-v0.9.0.tgz
```

要求插件位置必须在/opt/cni/bin 目录, 以下两个选项传递给kubelet可以指定cni插件目录，和对接网络的配置

–cni-bin-dir=/usr/bin
–cni-conf-dir=/etc/cni/net.d

指定Pod的基础容器

–pod-infra-container-image=

```
root@kube20-node01:~# install -dv /opt/cni/bin
install: creating directory '/opt/cni'
install: creating directory '/opt/cni/bin'
root@kube20-node01:~# tar -zxvf cni-plugins-linux-amd64-v0.9.0.tgz -C /opt/cni/bin
./
./macvlan
./flannel # flannel插件
./static
./vlan
./portmap
./host-local
./vrf
./bridge
./tuning
./firewall
./host-device
./sbr
./loopback
./dhcp
./ptp
./ipvlan
./bandwidth
```

去掉KUBE_ALLOW_PRIV, 此flag已经 废弃

https://github.com/cloudnativelabs/kube-router/issues/761

```
root@kube20-node01:~# cat /lib/systemd/system/kubelet.service
[Unit]
Description=Kubernetes Kubelet Server
Documentation=https://github.com/GoogleCloudPlatform/kubernetes
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/var/lib/kubelet
EnvironmentFile=-/etc/kubernetes/config
EnvironmentFile=-/etc/kubernetes/kubelet
ExecStart=/usr/local/kubernetes/node/bin/kubelet \
	    $KUBE_LOGTOSTDERR \
	    $KUBE_LOG_LEVEL \
	    $KUBELET_API_SERVER \
	    $KUBELET_ADDRESS \
	    $KUBELET_PORT \
	    $KUBELET_HOSTNAME \
-	    $KUBE_ALLOW_PRIV \
	    $KUBELET_ARGS
Restart=on-failure
KillMode=process
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> KUBE_ALLOW_PRIV 就是config通用配置的allow-privileged=true

```
root@kube20-node01:~# grep -n server /etc/kubernetes/auth/*.conf 
/etc/kubernetes/auth/bootstrap.conf:5:   server: https://kubernetes-api.mykernel.cn:6443
```

> api server高可用主要给kubelet使用，所以这个域名应该是api server的入口

kubelet启动, 会根据/etc/kubernetes/auth/bootstrap.conf文件自动生成kubeconfig文件，所以api server是一致

kubeconfig文件中包含kubelet的证书

```
root@kube20-node01:~# ls /etc/kubernetes/auth/kubelet.conf
ls: cannot access '/etc/kubernetes/auth/kubelet.conf': No such file or directory

root@kube20-node01:~# systemctl start kubelet
root@kube20-node01:~# systemctl status kubelet
root@kube20-node01:~# systemctl enable kubelet
root@kube20-node01:~# grep -n server /etc/kubernetes/auth/*.conf 
/etc/kubernetes/auth/bootstrap.conf:5:    server: https://kubernetes-api.mykernel.cn:6443
+/etc/kubernetes/auth/kubelet.conf:5:    server: https://kubernetes-api.mykernel.cn:6443

root@kube20-node01:~# cat /etc/kubernetes/auth/kubelet.conf
users:
+- name: default-auth
  user:
+    client-certificate: /var/lib/kubelet/pki/kubelet-client-current.pem
+    client-key: /var/lib/kubelet/pki/kubelet-client-current.pem
```

直接签发的证书的是没有任何权限的，需要授权。controller 完成签发证书和分配 pod的子网

查看kube-apiserver和kube-controller的状态

```
root@master01:~# systemctl status kube-controller-manager
● kube-controller-manager.service - Kubernetes Controller Manager
   Loaded: loaded (/lib/systemd/system/kube-controller-manager.service; disabled; vendor preset: enabled)
   Active: inactive (dead)
     Docs: https://github.com/GoogleCloudPlatform/kubernetes

# 启动kube-controller
root@master01:~# systemctl start kube-controller-manager
root@master01:~# systemctl enable kube-controller-manager


# 查看api server状态
 systemctl status kube-apiserver
```

验证kube-scheduler状态

```
systemctl status kube-scheduler
```

解析api 域名至其中一个api server, api作了高可用后，再dns解析指向 高可用的入口：keepalived vip或 nginx+keepalived的vip或dns3个A记录至3个Api Server.

> 当前使用hosts文件解析

```
root@kube20-node01:~# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	Base-Ubuntu

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.137.51 kube20-master01 kubernetes-api.mykernel.cn
192.168.137.52 kube20-master02
192.168.137.53 kube20-master03
192.168.137.54 kube20-node01
```

测试Ping

```
root@kube20-node01:~# ping kubernetes-api.mykernel.cn
PING kube20-master01 (192.168.137.51) 56(84) bytes of data.
64 bytes from kube20-master01 (192.168.137.51): icmp_seq=1 ttl=64 time=0.523 ms
64 bytes from kube20-master01 (192.168.137.51): icmp_seq=2 ttl=64 time=0.805 ms
^C
--- kube20-master01 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.523/0.664/0.805/0.141 ms
```

配置dns文件位置

```
root@kube20-node01:~# cat /var/lib/kubelet/config.yaml 
address: 0.0.0.0
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    cacheTTL: 2m0s
    enabled: true
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
  webhook:
    cacheAuthorizedTTL: 5m0s
    cacheUnauthorizedTTL: 30s
cgroupDriver: cgroupfs
cgroupsPerQOS: true
+clusterDNS:
+- 10.64.0.10
clusterDomain: cluster.local
configMapAndSecretChangeDetectionStrategy: Watch
containerLogMaxFiles: 5
containerLogMaxSize: 10Mi
contentType: application/vnd.kubernetes.protobuf
cpuCFSQuota: true
cpuCFSQuotaPeriod: 100ms
cpuManagerPolicy: none
cpuManagerReconcilePeriod: 10s
enableControllerAttachDetach: true
enableDebuggingHandlers: true
enforceNodeAllocatable:
- pods
eventBurst: 10
eventRecordQPS: 5
evictionHard:
  imagefs.available: 15%
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
evictionPressureTransitionPeriod: 5m0s
failSwapOn: false
fileCheckFrequency: 20s
hairpinMode: promiscuous-bridge
healthzBindAddress: 127.0.0.1
healthzPort: 10248
httpCheckFrequency: 20s
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
imageMinimumGCAge: 2m0s
iptablesDropBit: 15
iptablesMasqueradeBit: 14
kind: KubeletConfiguration
kubeAPIBurst: 10
kubeAPIQPS: 5
makeIPTablesUtilChains: true
maxOpenFiles: 1000000
maxPods: 110
nodeLeaseDurationSeconds: 40
nodeStatusUpdateFrequency: 10s
oomScoreAdj: -999
podPidsLimit: -1
port: 10250
registryBurst: 10
registryPullQPS: 5
+resolvConf: /run/systemd/resolve/resolv.conf
rotateCertificates: true
runtimeRequestTimeout: 2m0s
serializeImagePulls: true
staticPodPath: /etc/kubernetes/manifests
streamingConnectionIdleTimeout: 4h0m0s
syncFrequency: 1m0s
volumeStatsAggPeriod: 1m0s
```

> ubuntu需要
>
> 并且dns是配置容器中的dns

```
systemctl restart kubelet
```

#### master接入node *

```
root@kube20-master01:~# kubectl get csr
NAME        AGE     SIGNERNAME                                    REQUESTOR             CONDITION
csr-f29np   45s   kubernetes.io/kube-apiserver-client-kubelet   system:bootstrapper   Pending

# 签署证书
root@kube20-master01:~# kubectl certificate approve csr-f29np
certificatesigningrequest.certificates.k8s.io/csr-f29np approved
root@kube20-master01:~# kubectl get csr
NAME        AGE     SIGNERNAME                                    REQUESTOR             CONDITION
csr-f29np   2m40s   kubernetes.io/kube-apiserver-client-kubelet   system:bootstrapper   Approved,Issued

root@kube20-master01:~/.kube# kubectl describe csr csr-f29np
Name:               csr-f29np
Labels:             <none>
Annotations:        <none>
CreationTimestamp:  Mon, 15 Feb 2021 20:54:17 +0800
Requesting User:    system:bootstrapper
Signer:             kubernetes.io/kube-apiserver-client-kubelet
Status:             Approved,Issued
Subject:
         Common Name:    system:node:kube20-node01
         Serial Number:  
         Organization:   system:nodes
Events:  <none>

root@kube20-master01:~# kubectl get node
NAME                STATUS     ROLES    AGE   VERSION
kube20-node01       NotReady   <none>   14s   v1.20.2
```

> #https://blog.csdn.net/weixin_33754065/article/details/89620508
>
> kubelet 首次启动通过加载 `bootstrap.kubeconfig` 中的用户 Token 和 apiserver CA 证书发起首次 CSR 请求，这个 Token 被预先内置在 apiserver 节点的 token.csv 中，其身份为 `kubelet-bootstrap` 用户和 `system:bootstrappers` 用户组；想要首次 CSR 请求能成功(成功指的是不会被 apiserver 401 拒绝)，则需要先将 `kubelet-bootstrap` 用户和 `system:node-bootstrapper` 内置 ClusterRole 绑定；
>
> 对于首次 CSR 请求可以手动批准，也可以将 `system:bootstrappers` 用户组与 `approve-node-client-csr` ClusterRole 绑定实现自动批准(1.8 之前这个 ClusterRole 需要手动创建，1.8 后 apiserver 自动创建，并更名为`system:certificates.k8s.io:certificatesigningrequests:nodeclient`)
>
> 默认签署的的证书只有 1 年有效期，如果想要调整证书有效期可以通过设置 kube-controller-manager 的 `--experimental-cluster-signing-duration` 参数实现，该参数默认值为 `8760h0m0s`
>
> 对于证书自动续签，需要通过协调两个方面实现；第一，想要 kubelet 在证书到期后自动发起续期请求，则需要在 kubelet 启动时增加 `--feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true` 来实现；第二，想要让 controller manager 自动批准续签的 CSR 请求需要在 controller manager 启动时增加 `--feature-gates=RotateKubeletServerCertificate=true` 参数，并绑定对应的 RBAC 规则；**同时需要注意的是 1.7 版本的 kubelet 自动续签后需要手动重启 kubelet 以使其重新加载新证书，而 1.8 后只需要在 kublet 启动时附带 `--rotate-certificates` 选项就会自动重新加载新证书**

是NotReady，还需要启动kube-proxy

```
root@@kube20-master01:~# systemctl status kube-controller-manager
Feb 15 20:56:48 kube20-master01 kube-controller-manager[6679]: W0215 20:56:48.219016    6679 node_lifecycle_controller.go:1044] Missing timestamp for Node kube20-node01. Assuming now as a timestamp.
Feb 15 20:56:48 kube20-master01 kube-controller-manager[6679]: I0215 20:56:48.219081    6679 node_lifecycle_controller.go:1195] Controller detected that all Nodes are not-Ready. Entering master disruption mode.
Feb 15 20:56:48 kube20-master01 kube-controller-manager[6679]: I0215 20:56:48.219143    6679 event.go:291] "Event occurred" object="kube20-node01" kind="Node" apiVersion="v1" type="Normal" reason="RegisteredNode" message="Node kube20-node01 event: Registered Node kube20-node01 in Controller"
```

#### kube-proxy配置文件

也支持–config加载配置文件, 默认在/var/lib/kube-proxy目录下

```
root@kube20-node01:~# cat /var/lib/kube-proxy/config.yaml 
apiVersion: kubeproxy.config.k8s.io/v1alpha1
+bindAddress: 0.0.0.0 # 自已监听地址
clientConnection:
  acceptContentTypes: ""
  burst: 10
  contentType: application/vnd.kubernetes.protobuf
  kubeconfig: /etc/kubernetes/auth/kube-proxy.conf
  qps: 5
+clusterCIDR: 10.244.0.0/16 # pod网络
configSyncPeriod: 15m0s
conntrack:
  max: null
  maxPerCore: 32768
  min: 131072
  tcpCloseWaitTimeout: 1h0m0s
  tcpEstablishedTimeout: 24h0m0s
enableProfiling: false
+healthzBindAddress: 0.0.0.0:10256 # 健康状态检测的地址和端口
hostnameOverride: ""
iptables:
  masqueradeAll: false
  masqueradeBit: 14
  minSyncPeriod: 0s
  syncPeriod: 30s
+ipvs: # lvs
  excludeCIDRs: null
  minSyncPeriod: 0s
+  scheduler: ""      # 调度算法
  syncPeriod: 30s
kind: KubeProxyConfiguration
+metricsBindAddress: 127.0.0.1:10249 # 指标采集的端口
+mode: ipvs            # 定义ipvs规则的service. 需要系统加载ipvs模块
nodePortAddresses: null
oomScoreAdj: -999
portRange: ""
```

配置node节点的ipvs规则

配置文件

```
root@kube20-master01:~# tail -n 100000 k8s-bin-inst/nodes/etc/kubernetes/{config,proxy}
==> k8s-bin-inst/nodes/etc/kubernetes/config <== # 公共配置
###
# kubernetes system config
#
# The following values are used to configure various aspects of all
# kubernetes services, including
#
#   kube-apiserver.service
#   kube-controller-manager.service
#   kube-scheduler.service
#   kubelet.service
#   kube-proxy.service
# logging to stderr means we get it in the systemd journal
KUBE_LOGTOSTDERR="--logtostderr=true"

# journal message level, 0 is debug
KUBE_LOG_LEVEL="--v=0"

# Should this cluster be allowed to run privileged docker containers
KUBE_ALLOW_PRIV="--allow-privileged=true"

==> k8s-bin-inst/nodes/etc/kubernetes/proxy <==  # 配置文件，直接加载
###
# kubernetes proxy config

# Add your own!
KUBE_PROXY_ARGS="--config=/var/lib/kube-proxy/config.yaml"
```

#### 配置kube-proxy组件 *

请发kube-proxy证书，这个需要手动签发

```
root@kube20-master01:~/k8s-cert/cert# cp kube-scheduler-csr.json kube-proxy-csr.json
root@kube20-master01:~/k8s-cert/cert# cat kube-proxy-csr.json
{
+  "CN": "system:kube-proxy",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names":[{
    "C": "China",
    "ST": "AnHui",
    "L": "HeFei",
    "O": "system:none",
    "OU": "system"
  }],
+    "hosts": []
}
```

> 连接api 即可 hosts”: []

```
root@kube20-master01:~/k8s-cert/cert#  ../cfssl gencert -ca=k8s-ca.pem -ca-key=k8s-ca-key.pem      --config=common-config.json -profile=kubernetes-ca     kube-proxy-csr.json | ../cfssljson -bare kube-proxy
2021/02/15 21:03:26 [INFO] generate received request
2021/02/15 21:03:26 [INFO] received CSR
2021/02/15 21:03:26 [INFO] generating key: rsa-2048
2021/02/15 21:03:26 [INFO] encoded CSR
2021/02/15 21:03:26 [INFO] signed certificate with serial number 138700669788496421032601180495726111576493906802
2021/02/15 21:03:26 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

root@kube20-master01:~# scp k8s-bin-inst/nodes/etc/kubernetes/{config,proxy} kube20-node01:/etc/kubernetes/

root@kube20-master01:~# scp -rp k8s-bin-inst/nodes/var/lib/kube-proxy/ kube20-node01:/var/lib/


# 生成证书
#/etc/kubernetes/auth/kube-proxy.conf 
export KUBECONFIG=/etc/kubernetes/auth/kube-proxy.conf  # 配置文件中指定这个位置
export ADDR=https://kubernetes-api.mykernel.cn:6443 # 运行kube-scheduler节点的api server, 如果都指向 一个位置，api server压力大
export USERNAME=default-scheduler
export CERT=kube-proxy.pem
export KEY=kube-proxy-key.pem

kubectl config set-cluster default-cluster --server=$ADDR --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs
kubectl config set-credentials $USERNAME --client-certificate=$CERT --client-key=$KEY --username=$USERNAME --embed-certs=true 
kubectl config set-context default-system --cluster default-cluster --user $USERNAME
kubectl config use-context default-system

chown kube.kube $KUBECONFIG
kubectl config view

export KUBECONFIG=

root@kube20-master01:~/k8s-cert/cert# scp /etc/kubernetes/auth/kube-proxy.conf kube20-node01:/etc/kubernetes/auth/kube-proxy.conf
```

如果使用以上cfssl生成证书，跳过这一步

```
root@kube20-master01:~# scp k8s-bin-inst/nodes/etc/kubernetes/{config,proxy} kube20-node01:/etc/kubernetes/
#验证
root@kube20-node01:~# ls /etc/kubernetes/
auth  config  kubelet  pki  proxy   # config, proxy

root@kube20-master01:~# scp -rp k8s-bin-inst/nodes/var/lib/kube-proxy/ kube20-node01:/var/lib/
# 验证
root@kube20-node01:~# ls /var/lib/kube-proxy/
config.yaml


root@kube20-master01:~# scp k8s-certs-generator/kubernetes/kubelet/auth/kube-proxy.conf  kube20-node01:/etc/kubernetes/auth/
# 验证
root@kube20-node01:~# ls /etc/kubernetes/auth/
bootstrap.conf  kubelet.conf  kube-proxy.conf # kube-proxy 证书认证连接api server kubeconfig 
root@kube20-node01:~# cat /etc/kubernetes/auth/kube-proxy.conf 
apiVersion: v1
kind: Config
clusters:
 - name: kubernetes
  cluster:
    server: https://kubernetes-api.magedu.com:6443
    certificate-authority-data: 
users:
 - name: system:kube-proxy
  user:
    client-certificate-data: 
    client-key-data: 
contexts:
 - context:
    cluster: kubernetes
+    user: system:kube-proxy # 证书中必须是这个用户名，kubeconfig文件中的user这个无所谓
  name: system:kube-proxy@kubernetes
current-context: system:kube-proxy@kubernetes
```

这个system:kube-proxy用户默认绑定在集群内建的角色上

```
root@kube20-master01:~# kubectl describe clusterrolebinding system:node-proxier
Name:         system:node-proxier
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:  ClusterRole
  Name:  system:node-proxier
Subjects:
  Kind  Name               Namespace
  ----  ----               ---------
+  User  system:kube-proxy  
```

配置kube-proxy的pod网络

```
root@kube20-node01:~# cat /var/lib/kube-proxy/config.yaml 
apiVersion: kubeproxy.config.k8s.io/v1alpha1
bindAddress: 0.0.0.0
clientConnection:
  acceptContentTypes: ""
  burst: 10
  contentType: application/vnd.kubernetes.protobuf
  kubeconfig: /etc/kubernetes/auth/kube-proxy.conf
  qps: 5
clusterCIDR: 10.244.0.0/16
configSyncPeriod: 15m0s
conntrack:
  max: null
  maxPerCore: 32768
  min: 131072
  tcpCloseWaitTimeout: 1h0m0s
  tcpEstablishedTimeout: 24h0m0s
enableProfiling: false
healthzBindAddress: 0.0.0.0:10256
hostnameOverride: ""
ipvs:
  excludeCIDRs: null
  minSyncPeriod: 0s
+  scheduler: "rr"
  syncPeriod: 30s
kind: KubeProxyConfiguration
metricsBindAddress: 127.0.0.1:10249
+mode: "ipvs"
nodePortAddresses: null
oomScoreAdj: -999
portRange: ""
```

> 由于我们使用flannel就直接使用10.244.0.0/16

配置ipvs模块

```
root@kube20-node01:~# cat > /etc/modules-load.d/10-k8s-modules.conf <<EOF
br_netfilter
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack_ipv4
EOF
for i in br_netfilter ip_vs ip_vs_rr ip_vs_wrr ip_vs_sh nf_conntrack_ipv4; do modprobe $i; done

# 验证
lsmod | grep ip_vs
ip_vs_sh               16384  0
ip_vs_wrr              16384  0
ip_vs_rr               16384  0
ip_vs                 147456  6 ip_vs_rr,ip_vs_sh,ip_vs_wrr
nf_conntrack          131072  8 xt_conntrack,nf_nat_masquerade_ipv4,nf_conntrack_ipv4,nf_nat,ipt_MASQUERADE,nf_nat_ipv4,nf_conntrack_netlink,ip_vs
libcrc32c              16384  4 nf_conntrack,nf_nat,raid456,ip_vs
```

安装ipset命令

```
apt install -y ipset ipvsadm

# 后期ipvsadm -Ln 查看规则
root@kube20-node01:~# systemctl enable kube-proxy
root@kube20-node01:~# systemctl start kube-proxy

root@kube20-node01:~# systemctl status kube-proxy
```

### 配置网络插件 *

controller, kube-proxy使用

-  二进制部署flannel/calico
-  pod运行flannel

https://github.com/coreos/flannel

```
For Kubernetes v1.17+ kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
root@kube20-master01:~# wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

编辑 kube-flannel.yml

```
126   net-conf.json: |
127     {
128       "Network": "10.244.0.0/16",
129       "Backend": {
+130         "Type": "vxlan",
+131         "DirectRouting": true
132       }
133     }
```

> 注意”DirectRouting”:  true 前面是空格，用space键补上，不要使用TAB

```
root@kube20-master01:~# kubectl apply -f kube-flannel.yml
podsecuritypolicy.policy/psp.flannel.unprivileged created     # pod的psp策略
clusterrole.rbac.authorization.k8s.io/flannel created         # clusterrole
clusterrolebinding.rbac.authorization.k8s.io/flannel created  # 绑定
serviceaccount/flannel created                                # sa, pod中进程的权限
configmap/kube-flannel-cfg created                            # cm就是上面编辑的部署
daemonset.apps/kube-flannel-ds created                        # daemonset, 每个节点一个Pod
```

在过程中查看node节点

```
root@kube20-node01:~# docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED              STATUS              PORTS     NAMES
b36f62df3d22   dee1cac4dd20           "/opt/bin/flanneld -…"   11 minutes ago       Up 11 minutes                 k8s_kube-flannel_kube-flannel-ds-2lwv8_kube-system_3112ad79-f9c7-4b43-bccf-780dcdbc60e1_0
f301979e8e03   k8s.gcr.io/pause:3.2   "/pause"                 11 minutes ago       Up 11 minutes                 k8s_POD_kube-flannel-ds-2lwv8_kube-system_3112ad79-f9c7-4b43-bccf-780dcdbc60e1_0

# Pod基础架构容器
root@kube20-master01:~# kubectl get pods -n kube-system 
NAME                       READY   STATUS    RESTARTS   AGE
kube-flannel-ds-2lwv8      1/1     Running   0          12m
```

查看集群状态

```
root@kube20-master01:~# kubectl get node
NAME                STATUS   ROLES    AGE     VERSION
# 节点自动签发证书，所以后面的node节点直接以3.10步骤添加即可
kube20-node01   Ready    <none>   42h   v1.20.1
```

现在集群正常了，将master组件的日志级别调低

```
/root@kube20-master01:~# vim /etc/kubernetes/config 
16 KUBE_LOG_LEVEL="--v=0"
root@kube20-master01:~# systemctl restart kube-apiserver.service kube-controller-manager.service kube-scheduler.service
```

### 配置coredns *

- [coredns](https://github.com/coredns/deployment/tree/master/kubernetes)

```
root@kube20-master01:~# git clone https://github.com/coredns/deployment.git

root@kube20-master01:~/deployment/kubernetes# ./deploy.sh -i 10.64.0.10 -d cluster.local | kubectl apply -f -
root@kube20-master01:~#  kubectl get pods -n kube-system -o wide
NAME                       READY   STATUS    RESTARTS   AGE     IP               NODE            NOMINATED NODE   READINESS GATES
coredns-6ccb5d565f-9kzrr   1/1     Running   0          3m41s   10.244.0.3       kube20-node01   <none>           <none>
kube-flannel-ds-2lwv8      1/1     Running   0          13m     192.168.137.54   kube20-node01   <none>           <none>

root@kube20-node01:~#ping 10.244.0.3
PING 10.244.0.3 (10.244.0.3) 56(84) bytes of data.
64 bytes from 10.244.0.3: icmp_seq=1 ttl=64 time=0.039 ms
^C
--- 10.244.0.3 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.039/0.039/0.039/0.000 ms
```

> node节点可达
>
> master没安装kube-proxy

测试dns

```
root@kube20-master01:~# kubectl get svc -n kube-system
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
kube-dns   ClusterIP   10.64.0.10   <none>        53/UDP,53/TCP,9153/TCP   12m
root@kube20-master01:~# kubectl describe svc -n kube-system
Name:              kube-dns
Namespace:         kube-system
Labels:            k8s-app=kube-dns
                   kubernetes.io/cluster-service=true
                   kubernetes.io/name=CoreDNS
Annotations:       prometheus.io/port: 9153
                   prometheus.io/scrape: true
Selector:          k8s-app=kube-dns
Type:              ClusterIP
IP Families:       <none>
IP:                10.64.0.10
IPs:               10.64.0.10
Port:              dns  53/UDP
TargetPort:        53/UDP
Endpoints:         10.244.0.3:53
Port:              dns-tcp  53/TCP
TargetPort:        53/TCP
Endpoints:         10.244.0.3:53
Port:              metrics  9153/TCP
TargetPort:        9153/TCP
Endpoints:         10.244.0.3:9153
Session Affinity:  None
Events:            <none>

root@kube20-node01:~# host -t A kube-dns.kube-system.svc.cluster.local  10.244.0.3
Using domain server:
Name: 10.244.0.3
Address: 10.244.0.3#53
Aliases: 

kube-dns.kube-system.svc.cluster.local has address 10.64.0.10
```

### 测试pod *

```
root@kube20-master01:~# kubectl create deployment myapp --replicas=1 --image=ikubernetes/myapp:v1 
root@kube20-master01:~# kubectl create service clusterip myapp --tcp=80:80

root@kube20-master01:~# kubectl get pods -o wide
NAME                    READY   STATUS    RESTARTS   AGE   IP           NODE            NOMINATED NODE   READINESS GATES
myapp-7d4b7b84b-hk68s   1/1     Running   0          72s   10.244.0.4   kube20-node01   <none>           <none>

root@kube20-master01:~# kubectl describe service myapp
Endpoints:         10.244.0.4:80

root@kube20-master01:~/deployment/kubernetes# kubectl edit svc myapp
 27   type: NodePort     
root@kube20-master01:~# kubectl get svc myapp
NAME    TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
myapp   NodePort   10.66.140.172   <none>        80:38793/TCP   3m49s
```

> 外部访问 node节点的 172.16.0.104:32953


node节点查看ipvs规则

```
root@kube20-node01:~# apt install ipvsadm
root@kube20-node01:~# ipvsadm -Ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
  
root@kube20-master01:~/:~# kubectl -n default exec -it myapp-7d4b7b84b-hk68s -- sh
/ # cat /etc/resolv.conf
nameserver 10.64.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5

/ # ping www.baidu.com
PING www.baidu.com (112.80.248.76): 56 data bytes
64 bytes from 112.80.248.76: seq=0 ttl=53 time=16.865 ms
64 bytes from 112.80.248.76: seq=1 ttl=53 time=17.568 ms
^C
--- www.baidu.com ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 16.865/17.216/17.568 ms
```

## 高可用master *

-  复制配置
-  启动

### 复制配置和证书

```
root@kube20-master01:~/k8s# ls
kubernetes-node-linux-amd64.tar.gz  kubernetes-server-linux-amd64.tar.gz

root@kube20-master01:~/k8s# scp kubernetes-server-linux-amd64.tar.gz kube20-master02:/root/
# 配置 和 kube20-master01 一致
root@kube20-master01:~/k8s# scp  -rp /etc/kubernetes/ kube20-master02:/etc/ 

root@kube20-master02:/etc/kubernetes/auth# sed -i "s/192.168.137.51:6443/192.168.137.52:6443/g" ./*
root@kube20-master02:~# tar -xzvf kubernetes-server-linux-amd64.tar.gz -C /usr/local

# 证书
# 先清理从kube20-master01复制过来的证书信息
root@kube20-master02:~# rm -fr /etc/kubernetes/{auth,pki,token.csv}
root@kube20-master01:~# scp -rp k8s-certs-generator/kubernetes/master03/* kube20-master02:/etc/kubernetes

# 验证
root@kube20-master02:~# ls /etc/kubernetes/
apiserver  auth  config  controller-manager  pki  scheduler  token.csv

root@kube20-master01:~# scp -rp k8s-bin-inst/master/unit-files/* kube20-master02:/lib/systemd/system/
```

### 启动

```
root@kube20-master02:~# useradd -r kube
root@kube20-master02:~# chown kube.kube /etc/kubernetes/pki/*.key

root@kube20-master02:~# systemctl enable kube-apiserver kube-controller-manager kube-scheduler
root@kube20-master02:~# systemctl restart kube-apiserver kube-controller-manager kube-scheduler
```

### 验证kubelet命令

```
root@kube20-master02:~# mkdir ~/.kube
root@kube20-master02:~# cp /etc/kubernetes/auth/admin.conf .kube/config
root@kube20-master02:~# ln -sv /usr/local/kubernetes/server/bin/kubectl /usr/bin/
root@kube20-master02:~# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
+    server: https://kubernetes-api.mykernel.cn:6443
```

配置域名解析

```
root@master02:~# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	Base-Ubuntu

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.137.51 kube20-master01
192.168.137.52 kube20-master02 kubernetes-api.mykernel.cn
192.168.137.53 kube20-master03
192.168.137.54 kube20-node01
```

并将此节点的controller, kube-scheduler指向高可用的api server

```
vim /etc/kubernetes/auth/controller-manager.conf
+    server: https://kubernetes-api.mykernel.cn:6443

vim /etc/kubernetes/auth/scheduler.conf 
+    server: https://kubernetes-api.mykernel.cn:6443
```

重启

```
root@kube20-master02:/etc/kubernetes/auth# chown kube.kube controller-manager.conf kube-proxy.conf  scheduler.conf bootstrap.conf

root@kube20-master02:/etc/kubernetes/auth# systemctl restart kube-apiserver kube-controller-manager kube-scheduler
```

获取当前锁位置

```
root@kube20-master02:~# kubectl get leases -A
NAMESPACE         NAME                      HOLDER                                                 AGE
kube-node-lease   kube20-node01             kube20-node01                                          44h
kube-system       kube-controller-manager   kube20-master02_6b7a5308-b044-40b5-9b32-0f739b7d9da1   46h
kube-system       kube-scheduler            kube20-master02_422babed-e875-4a11-a024-d823906047a9   46h
```

停止master01

```
root@kube20-master01:~# poweroff
```

配置node01指向master02

```
root@node01:~# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	Base-Ubuntu

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.137.51 kube20-master01 
192.168.137.52 kube20-master02 kubernetes-api.mykernel.cn
192.168.137.53 kube20-master03
192.168.137.54 kube20-node01
```

查看锁资源

```
root@kube20-master02:~# kubectl get leases -A
NAMESPACE         NAME                      HOLDER                                                 AGE
kube-node-lease   kube20-node01             kube20-node01                                          45h
kube-system       kube-controller-manager   kube20-master02_4b2b0306-de92-4fce-9385-88eca6bbfadb   47h
kube-system       kube-scheduler            kube20-master03_13eb1ed8-93b6-452c-9679-f8f0fedb2d12   47h

# controller-manager因为我调整了选项，所以在endpoints上
root@kube20-master02:~# kubectl -n kube-system describe endpoints kube-controller-manager
  Normal  LeaderElection  58m   kube-controller-manager  master02.mykernel.cn_e7a78440-3001-4871-866c-99662b667e54 became leader
```

现在已经完成api/controller/scheduler高可用，高可用方式：

- node节点添加nginx -> 3个api server.
- 3 api 前端添加 4层负载。所有节点使用/etc/hosts文件指向这个外部的vip
- 3 api + keepalived VIP漂移
- 3 api地址直接在DNS上添加3个A记录

阿里云：

- keepalived的VIP：haip
- 内网SLB



## node节点快速添加 *

```
root@kube20-node01:~# docker save  k8s.gcr.io/pause:3.2 coredns/coredns:1.8.0 quay.io/coreos/flannel:v0.13.1-rc2 -o node.tar
root@kube20-node01:~# scp node.tar kube20-node02:/root/
root@kube20-node02:~# docker load -i node.tar 
ba0dae6243cc: Loading layer [==================================================>]  684.5kB/684.5kB
Loaded image: k8s.gcr.io/pause:3.2
225df95e717c: Loading layer [==================================================>]  336.4kB/336.4kB
69ae2fbf419f: Loading layer [==================================================>]  42.24MB/42.24MB
Loaded image: coredns/coredns:1.8.0
50644c29ef5a: Loading layer [==================================================>]  5.845MB/5.845MB
0be670d27a91: Loading layer [==================================================>]  11.42MB/11.42MB
90679e912622: Loading layer [==================================================>]  2.267MB/2.267MB
6db5e246b16d: Loading layer [==================================================>]  45.69MB/45.69MB
97320fed8db7: Loading layer [==================================================>]   5.12kB/5.12kB
8a984b390686: Loading layer [==================================================>]  9.216kB/9.216kB
3b729894a01f: Loading layer [==================================================>]   7.68kB/7.68kB
Loaded image: quay.io/coreos/flannel:v0.13.1-rc2
```

在node01上完成以下脚本制作脚本

```
root@kube20-node01:~# mkdir node
root@kube20-node01:~# mv kubernetes-node-linux-amd64.tar.gz cni-plugins-linux-amd64-v0.9.0.tgz node.tar node
root@kube20-node01:~# cd node
# 配置和证书
root@kube20-node01:~# cp -a /etc/kubernetes/  .
# 清理kubelet
root@kube20-node01:~# rm -f kubernetes/auth/kubelet.conf 
# 配置
root@kube20-node01:~# cp -a /var/lib/kube* .
# unit
root@kube20-node01:~# cp /lib/systemd/system/kubelet.service /lib/systemd/system/kube-proxy.service .
# hosts
root@kube20-node01:~# cp /etc/hosts .
```

编辑脚本

```
#!/bin/bash

pkill apt-get
pkill apt-get

hostnamectl set-hostname $1
sed -i -e 's@us.archive.ubuntu.com@mirrors.aliyun.com@g' -e 's@security.ubuntu.com@mirrors.aliyun.com@g' /etc/apt/sources.list

apt update

apt -y install chrony && systemctl enable chronyd && systemctl restart chronyd
cp hosts /etc/hosts

# step 1: 安装必要的一些系统工具
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
# step 2: 安装GPG证书
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key add -
# Step 3: 写入软件源信息
sudo add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

apt install docker-ce=5:20.10.2~3-0~ubuntu-bionic -y
systemctl start docker
systemctl enable docker

# pod infra, flannel, dns
docker load -i node.tar 

# cni plugins
install -dv /opt/cni/bin
tar xvf cni-plugins-linux-amd64-v0.9.0.tgz -C /opt/cni/bin

# kubelet and kube-proxy
tar -xzvf kubernetes-node-linux-amd64.tar.gz  -C /usr/local/
install -dv /etc/kubernetes/{auth,pki}
# config and certificate
cp -a kubernetes /etc/
rm -f kubernetes/auth/kubelet.conf 

# config
cp -a  kubelet kube-proxy /var/lib/

# unit
cp kubelet.service kube-proxy.service /lib/systemd/system/

# ipvs
cat > /etc/modules-load.d/10-k8s-modules.conf <<EOF
br_netfilter
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack_ipv4
EOF
for i in br_netfilter ip_vs ip_vs_rr ip_vs_wrr ip_vs_sh nf_conntrack_ipv4; do modprobe $i; done

# start
systemctl enable kube-proxy kubelet
systemctl restart kube-proxy kubelet

root@kube20-node01:~# ls
cni-plugins-linux-amd64-v0.9.0.tgz  hosts  install.sh  kubelet  kubelet.service  kube-proxy  kube-proxy.service  kubernetes  kubernetes-node-linux-amd64.tar.gz  kubernetes-v1.20.2.tar  node.tar
```

node02执行

```
install -dv node
root@ubuntu-template:~# tar xvf kubernetes-v1.20.2.tar -C node
root@ubuntu-template:~/node# bash install.sh kube20-node02
```

master节点查看

```
root@kube20-master02:~# kubectl get csr
NAME        AGE    SIGNERNAME                                    REQUESTOR                        CONDITION
csr-74vwv   64s    kubernetes.io/kube-apiserver-client-kubelet   system:node:kube20-node02   Pending


root@kube20-master02:~# kubectl certificate approve csr-74vwv 
certificatesigningrequest.certificates.k8s.io/csr-74vwv approved


root@kube20-master02:~# kubectl get node
NAME                 STATUS     ROLES    AGE    VERSION
kube20-node01        Ready      <none>   137m   v1.20.2
kube20-node02        NotReady   <none>   5s     v1.20.2


#等待flannel启动
root@kube20-master02:~# kubectl get node
NAME                 STATUS   ROLES    AGE    VERSION
kube20-node01        Ready    <none>   138m   v1.20.2
kube20-node02        Ready    <none>   35s    v1.20.2 # Ready
```

测试将pod规模扩容，看是否到node02

```
root@kube20-master02:~# kubectl scale deploy/myapp --replicas=5
root@kube20-master02:~# kubectl get pods -o wide -w
NAME                    READY   STATUS              RESTARTS   AGE   IP           NODE                 NOMINATED NODE   READINESS GATES
myapp-7d4b7b84b-fnm9d   0/1     ContainerCreating   0          6s    <none>       kube20-node01 <none>           <none>
myapp-7d4b7b84b-hphjq   0/1     Pending             0          6s    <none>       kube20-node02 <none>           <none>
myapp-7d4b7b84b-jx5gq   1/1     Running             0          43m   10.244.0.8   kube20-node01 <none>           <none>
myapp-7d4b7b84b-mbfxp   0/1     ContainerCreating   0          6s    <none>       kube20-node02 <none>           <none>
myapp-7d4b7b84b-sh646   1/1     Running             0          43m   10.244.0.9   kube20-node01 <none>           <none>
myapp-7d4b7b84b-hphjq   0/1     ContainerCreating   0          6s    <none>       kube20-node02 <none>           <none>

# 已经自动调度到node02
```

测试跨主机的两个pod通信，依赖node节点有ipv4.ip_forward规则



## 部署容器监控及告警

Prometheus + 钉钉 + grafana

告警：PromQL

展示：PromQL

参考：[http://blog.mykernel.cn/2021/02/03/%E8%B5%84%E6%BA%90%E6%8C%87%E6%A0%87%E4%B8%8EHPA%E6%8E%A7%E5%88%B6%E5%99%A8/#hpa](http://blog.mykernel.cn/2021/02/03/资源指标与HPA控制器/#hpa)

- adaptor内置核心指标
- cumstom metrics完成基于pod指标自动伸缩



## 部署ELK

直接裸机部署

参考：[http://blog.mykernel.cn/2020/12/23/%E9%83%A8%E7%BD%B2elasticsearch/](http://blog.mykernel.cn/2020/12/23/部署elasticsearch/)

参考：[http://blog.mykernel.cn/2020/11/19/Kibana%E6%9F%A5%E8%AF%A2%E6%85%A2/](http://blog.mykernel.cn/2020/11/19/Kibana查询慢/)

es和kibana和logstash和fluentd或filebeat 版本尽可能一样

redis

访问链路：Pod（fluentd + jar/nginx) -> redis svc -> redis pod -> logstash …. -> elasticsearch