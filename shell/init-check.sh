#!/usr/bin/env bash

#set -o errexit

# check ntpd
if ! rpm -q ntp > /dev/null 2>&1; then
    yum -y install ntp > /dev/null 2>&1
fi

echo "#perfer 表示『优先使用』的服务器
server 10.255.254.88 prefer
#下面没有prefer参数，做为备用NTP时钟上层服务器地址，我这里设置的是公网，语音云则可以设置其他两地NTP IP。
server 10.255.255.88
#我们每一个system clock的频率都有小小的误差,这个就是为什么机器运行一段时间后会不精确. NTP会自动来监测我们时钟的误差值并予以调整.但问题是这是一个冗长的过程,所以它会把记录下来的误差先写入driftfile.这样即使你重新开机以后之前的计算结果也就不会丢了
driftfile /var/lib/ntp/ntp.drift
statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable
filegen clockstats file clockstats type day enable
# By default, exchange time with everybody, but don't allow configuration.
restrict -4 default kod notrap nomodify nopeer noquery
restrict -6 default kod notrap nomodify nopeer noquery
# Local users may interrogate the ntp server more closely.
restrict 127.0.0.1
restrict ::1" > /etc/ntp.conf

echo "****************************************"
echo "check ntpd"

systemctl start ntpd
systemctl enable ntpd

systemctl status ntpd.service > /dev/null 2>&1
if [ $? -eq 0 ];then
    echo -e "\033[47;30m [ntpd is Right] \033[0m"
else
    echo -e "\033[47;31;5m [ntpd is Failure] \033[0m"
fi
echo "****************************************"

# check dns
echo "nameserver 10.255.254.88
nameserver 10.255.255.88
search localdomain" > /etc/resolv.conf
echo "check dns"
echo -e "\033[47;30m [dns has been changed] \033[0m"
echo "****************************************"

# check swap
echo "check swap"
swapoff -a
swap=`free |grep -i swap|awk '{print $2}'`
if [ $? -eq 0 ];then
    echo -e "\033[47;30m [swap is Closed] \033[0m"
else
    echo -e "\033[47;31;5m [swap is Open] \033[0m"
fi
echo "****************************************"

# check firewall
echo "check firewalld"
if rpm -q firewalld  &> /dev/null 2>&1; then
    systemctl stop firewalld
    systemctl disable firewalld
fi

systemctl status firewalld.service > /dev/null 2>&1
if [ $? -eq 0 ];then
  echo -e "\033[47;31;5m [firewalld is Failure] \033[0m"
else
  echo -e "\033[47;30m [firewalld is Right] \033[0m"
fi
echo "****************************************"

# check selinux
sed -i '/^SELINUX=/c\SELINUX=disabled' /etc/sysconfig/selinux
setenforce 0 > /dev/null 2>&1

selinux_status=`getenforce`
echo "check selinux"
if [ $selinux_status = Disabled ];then
  echo -e "\033[47;30m [selinux is Right] \033[0m"
else
  echo -e "\033[47;31;5m [selinux is Failure] \033[0m"
fi
echo "****************************************"

# check fs
echo "check filesystem"
mount | grep '/ type xfs' > /dev/null 2>&1
if [ $? -eq 0 ];then
  echo -e "\033[47;30m [filesystem is Right] \033[0m"
else
  echo -e "\033[47;31;5m [filesystem is Failure] \033[0m"
fi
echo "****************************************"

# check os
echo "check os type"
os_type=`systemctl get-default`
if [ $os_type = multi-user.target ];then
  echo -e "\033[47;30m [os type is multi-user.target] \033[0m"
else
  echo -e "\033[47;31;5m [os type is not multi-user.target] \033[0m"
fi
echo "****************************************"

# change kernel
echo "check kernel"
echo '* soft  nproc  10240000
* hard  nproc  10240000
* soft  nofile  10240000
* hard  nofile  10240000' >> /etc/security/limits.conf
echo 'net.ipv4.ip_forward = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 60
net.ipv4.ip_local_port_range = 1024 65500
net.ipv4.tcp_max_syn_backlog= 10240
net.ipv4.tcp_max_tw_buckets = 6000
fs.nr_open=102400000
net.ipv6.conf.all.disable_ipv6 =1
net.ipv6.conf.default.disable_ipv6 =1
net.ipv6.conf.lo.disable_ipv6 =1
net.core.somaxconn   = 1024
net.core.netdev_max_backlog = 10240
vm.swappiness = 0
vm.overcommit_memory = 1
vm.max_map_count = 262144
net.ipv4.ip_local_reserved_ports = 111,179,22,49152,24007,10248,10249,9100,32556,10255,10256,20050,31763,30679,30008,32571,30208,8099,31589,31238,2375,1736,31529,10250,9099 /etc/sysctl.confecho net.ipv4.ip_forward = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 60
net.ipv4.ip_local_port_range = 1024 65500
net.ipv4.tcp_max_syn_backlog= 10240
net.ipv4.tcp_max_tw_buckets = 6000
fs.nr_open=102400000
net.ipv6.conf.all.disable_ipv6 =1
net.ipv6.conf.default.disable_ipv6 =1
net.ipv6.conf.lo.disable_ipv6 =1
net.core.somaxconn   = 1024
net.core.netdev_max_backlog = 10240
vm.swappiness = 0
vm.overcommit_memory = 1
vm.max_map_count = 262144
net.ipv4.ip_local_reserved_ports = 111,179,22,49152,24007,10248,10249,9100,32556,10255,10256,20050,31763,30679,30008,32571,30208,8099,31589,31238,2375,1736,31529,10250,9099
kernel.pid_max = 102400' >> /etc/sysctl.conf
sysctl -p >> /dev/null 2>&1
echo -e "\033[47;30m [kernel has been changed] \033[0m"
echo "****************************************"

# check repo file
echo "check repo file"
cd /etc/yum.repos.d && mkdir -p backup && mv * backup >> /dev/null 2>&1
wget 172.16.59.181/files/yum.tar.gz -P /etc/yum.repos.d >> /dev/null 2>&1
tar -zxvf /etc/yum.repos.d/yum.tar.gz -C /etc/yum.repos.d/ >> /dev/null 2>&1
yum clean all >> /dev/null 2>&1
yum makecache >> /dev/null 2>&1
echo -e "\033[47;30m [repo file has been changed] \033[0m"
echo "****************************************"

#  check cpu performance
echo "check cpu performance"
if ! rpm -q tuned  > /dev/null 2>&1; then
    yum -y install tuned > /dev/null 2>&1
fi


ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1
if [ $? -eq 0 ];then
    cpuP=`cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor|uniq`
    echo -e "\033[35m[cpu mode is $cpuP]\033[0m"
else
    echo -e "\033[47;31;5m [check cpu performance Failed] \033[0m"
fi