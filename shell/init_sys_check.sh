#!/bin/bash
# 0 is ok
# 1 is problem

LOG="/opt/raid/check.log"
NF_XONNTRACK_MAX=4194304
DOCKER_VERSION="1.12.6"
DNS1="10.255.0.2"
DNS2="10.255.0.3"
URL="http://172.16.0.2/daily/check/"

set_flag(){
if [ $? -eq 0 ]; then
  flag=1
else
  flag=0
fi
}

set_flag1(){
if [ $? -eq 3 ]; then
  flag=0
else
  flag=1
fi
}

send(){
result=`grep 1 /opt/raid/check.log | xargs | sed -e "s/ /|/g"`
if [ -n "$result" ]; then 
    curl -m 10 -H "hostname: `hostname`" $URL  -d data=$result
fi
}

check_centos(){
	cat  /etc/centos-release | grep 7
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_power_max(){
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor | grep performance         
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_memory(){           
    dmesg | grep "memory read error"
    set_flag
    echo ${FUNCNAME[0]}:$flag >> $LOG
}

check_memory_swap(){
	sysctl -a | grep "vm.swappiness = 0"
    echo ${FUNCNAME[0]}:$? >> $LOG 
}

check_hugepages(){
	grep "never" /sys/kernel/mm/transparent_hugepage/defrag && grep "never" /sys/kernel/mm/transparent_hugepage/enabled
	echo ${FUNCNAME[0]}:$? >> $LOG 
}


check_dns254(){
    grep $DNS1 /etc/resolv.conf
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_dns255(){
    grep $DNS2 /etc/resolv.conf
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_ntp254(){
    grep $DNS1 /etc/ntp.conf
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_ntp255(){
    grep $DNS2 /etc/ntp.conf
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_firewall(){
	cat  /etc/centos-release | grep 7
	if [ $? -eq 0 ];then
	    systemctl status firewalld.service
	else
	    service iptables status
	fi
	set_flag1
	echo ${FUNCNAME[0]}:$flag >> $LOG
}

check_selinux(){
    getenforce | grep Disabled
    echo ${FUNCNAME[0]}:$? >> $LOG
}

check_networkmanger(){
	rpm -qa NetworkManager | grep Manager
	if [ $? -eq 0 ];then
	    service NetworkManager status
	    set_flag1
	    echo ${FUNCNAME[0]}:$flag >> $LOG
	else
	    set_flag
	    echo ${FUNCNAME[0]}:$flag >> $LOG
	fi
}

check_ip_forward(){
	sysctl -a |grep "net.ipv4.ip_forward = 1"
	echo ${FUNCNAME[0]}:$? >> $LOG
}

check_nf_conntrack_max(){
sysctl -a | grep nf_conntrack_max | grep  $NF_XONNTRACK_MAX
echo ${FUNCNAME[0]}:$? >> $LOG
}

check_docker_version(){
rpm -q docker
[ $? -eq 0 ] && rpm -q docker | grep $DOCKER_VERSION
echo ${FUNCNAME[0]}:$? >> $LOG
}

check_docker_port(){
echo >/dev/tcp/127.0.0.1/2375
set_flag
echo ${FUNCNAME[0]}:$? >> $LOG
}

echo > $LOG
check_centos
check_power_max
check_memory
check_memory_swap
check_hugepages
check_dns254
check_dns255
check_ntp254
check_ntp255
check_firewall
check_selinux
check_networkmanger
check_ip_forward
send
