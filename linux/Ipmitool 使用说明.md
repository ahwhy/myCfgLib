# ipmitool使用笔记

## ipmitool安装配置

```shell
# 安装
$ yum install ipmitool

# 加载模块
$ modprobe ipmi_poweroff
$ modprobe ipmi_watchdog
$ modprobe ipmi_msghandler  
$ modprobe ipmi_devintf  
$ modprobe ipmi_si 

# 启动程序
$ service ipmi start

# lanplus是操作远程机器，如果要操作本地机器，需要把lanplus换成 open 
# 设置pxe启动
$ ipmitool -I lanplus -H {ipmi} -U {user} -P {passwd} chassis bootdev pxe
# 重启机器
$ ipmitool -I lanplus -H {ipmi} -U {user} -P {passwd} chassis power cycle

# 本机重启bmc
# warm表示软重启；cold表示硬重启
$ ipmitool mc reset <warm|cold>

# 网络配置
$ ipmitool lan set 1 ipsrc static;
$ ipmitool lan set 1 ipaddr 192.168.7.60;
$ ipmitool lan set 1 netmask 255.255.255.0; 
$ ipmitool lan set 1 defgw ipaddr 192.168.7.1;
$ ipmitool lan set 1 access on

本机重启bmc
$ ipmitool mc reset <warm|cold>  warm表示软重启；cold表示硬重启

# 其他
# 查看当前ipmi 地址
$ ipmitool lan print
# 查看日志
$ ipmitool sel list
# 查清除日志
$ ipmitool sel clear 
```


## ipmitool命令

### 1、服务器状态管理
- 查看开关机状态 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) power status`

- 开机:
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) power on`

- 关机
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) power off`

- 重启 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) power reset`

### 2、IP网络设置
[ChannelNo] 字段是可选的，ChannoNo为1(Share Nic网络)或者8(BMC独立管理网络)；设置网络参数，必须首先设置IP为静态，然后再进行其他设置；

- 查看网络信息: 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) lan print [ChannelNo]`

- 修改IP为静态还是DHCP模式: 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) lan set <ChannelNo> ipsrc <static/dhcp>`

- 修改IP地址: 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) lan set <ChannelNo> ipaddr <IPAddress>`

- 修改子网掩码: 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) lan set <ChannelNo> netmask <NetMask>`

- 修改默认网关: 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) lan set <ChannelNo> defgw ipaddr <默认网关>`

### 3、硬件信息
- 查看FRU信息 
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) fru list`

- 重启动BMC
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) mc reset <warm/cold>`

- 查看SDR Sensor信息
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) sdr`

- 查看Sensor信息
	- `ipmitool -H (BMC的管理IP地址) -I lanplus -U (BMC登录用户名) -P (BMC 登录用户名的密码) sensor list`


## 其他

- [ipmitool使用手册](https://blog.csdn.net/xinqidian_xiao/article/details/80924897)

- 各厂商服务器IPMI默认用户
	- 戴尔IPMI默认用户名: root 密码: calvin
	- 曙光IPMI默认用户名: admin 密码: admin     
	- 浪潮IPMI默认用户名: admin 密码: admin     
	- H3C IPMI默认用户名: admin 密码: Password@_
	- 华为IPMI默认用户名: root 密码: Huawei12#$