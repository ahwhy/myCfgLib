# Linux网卡配置

## 修改物理机Linux网卡名称

### 1、修改配置
- `/etc/default/grub`文件，GRUB_CMDLINE_LINUX 属性加上 `net.ifnames=0 biosdevname=0`

```shell
[root@controller ~]# vim /etc/default/grub
GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0 crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet"
```

### 2、重新加载配置
- `grub2-mkconfig -o /boot/grub2/grub.cfg`
```shell
[root@controller ~]# grub2-mkconfig -o /boot/grub2/grub.cfg 
Generating grub configuration file ... 
Found linux image: /boot/vmlinuz-3.10.0-693.5.2.el7.x86_64 
Found initrd image: /boot/initramfs-3.10.0-693.5.2.el7.x86_64.img 
Found linux image: /boot/vmlinuz-3.10.0-327.28.3.el7.x86_64 
Found initrd image: /boot/initramfs-3.10.0-327.28.3.el7.x86_64.img 
Found linux image: /boot/vmlinuz-3.10.0-327.el7.x86_64 
Found initrd image: /boot/initramfs-3.10.0-327.el7.x86_64.img 
Found linux image: /boot/vmlinuz-0-rescue-0ff0e879cd2f443cb90ec9afa4d66dfb 
Found initrd image: /boot/initramfs-0-rescue-0ff0e879cd2f443cb90ec9afa4d66dfb.img done
```

### 3、修改网卡名称
```shell
[root@controller ~]# cd /etc/sysconfig/network-scripts/
[root@controller network-scripts]# vim ifcfg-eno16777736
NAME=bond0 
DEVICE=bond0
[root@controller network-scripts]# mv ifcfg-eno16777736 ifcfg-bond0
```

### 4、添加规则
```shell
[root@controller ~]# vim /etc/udev/rules.d/90-eno-pix.rules
SUBSYSTEM=="net",ACTION=="add",DRIVERS=="?*",ATTR{address}=="00:0c:29:72:41:10", NAME="bond0"  # ATTR{address}为机器需要更改网卡名的网卡mac地址
```

### 5、重启机器
重启机器后，查看网卡名check


## Linux双网卡绑定

### 1、常用绑定模式
- Mode 0
	- 单纯网卡聚合，无负载功能无需交换机端做配置，跑满一张网卡后流量增加至另外一张

- Mode 1 
	- 主备模式，无需交换机做配置
	- 单网卡或网线故障，流量切换至另外一张网卡，更换网卡或网线后需重启网络服务，否则2张网卡会争主网卡权限，导致网络异常

- Mode 4
	- 负载均衡，需交换机端支持lacp协议，负载由交换机端完成
	- 无单点故障，较为稳定
	- 其中Centos系统NetworkManager服务关闭可能会导致绑定异常，网卡无法启动

- Mode 6
	- 负载均衡，由操作系统来完成，无需交换机做配置，占用系统资源，一般不建议采用

### 2、Centos/RHEL网卡配置
- eth0和eth1绑定模式mode4
```shell
[root@controller ~]# vim /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=none
DEVICE=eth0
ONBOOT=yes
MASTER=bond0
SLAVE=yes

[root@controller ~]# vim /etc/sysconfig/network-scripts/ifcfg-eth1
TYPE=Ethernet
BOOTPROTO=none
DEVICE=eth1
ONBOOT=yes
MASTER=bond0
SLAVE=yes

# 绑定后网卡ifcfg-bond0
[root@controller ~]# vim /etc/sysconfig/network-scripts/ifcfg-bond0
TYPE=Bond
DEVICE=bond0
BOOTPROTO=none
ONBOOT=yes
BONDING_MASTER=yes
BONDING_OPTS="xmit_hash_policy=layer2+3 mode=4 miimon=80"  # 其他模式，更改mode 后对应内容即可
IPADDR=192.168.0.11 
PREFIX=24
GATEWAY=192.168.0.1
DNS1=114.114.114.114
```

### 3、Ubuntu网卡配置
- eth0和eth1绑定模式mode4
```shell
[root@controller ~]# apt-get install-y slaves
[root@controller ~]# vim /etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet manual
bond-master bond0

auto eth1
iface eth1 inet manual
bond-master bond0

auto bond0
iface bond0 inet static
address  192.168.1.10
gateway  192.168.1.1
netmask  255.255.255.0
bond-salves all    # bond-slaves eth0 eth1
bond-mode 802.3ad  # bond-mode 1 其他模式，更改mode 后对应内容即可
bond-miimon 100
up ifenslave bond0 eth0 eth1
down ifenslave -d bond0 eth0 eth1 
```