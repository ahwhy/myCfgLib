#!/bin/sh

systemctl stop firewalld.service
systemctl disable firewalld.service
setenforce 0
sed -i "s/SELINUX=enforcing/SELINUX=disabled/" /etc/selinux/config

#ssh basic
sed -i "s/#UseDNS yes/UseDNS no/"  /etc/ssh/sshd_config
sed -i 's/^GSSAPIAuthentication yes$/GSSAPIAuthentication no/g' /etc/ssh/sshd_config
sed -i 's/#   StrictHostKeyChecking ask/StrictHostKeyChecking=no/' /etc/ssh/ssh_config
systemctl restart sshd.service

#disable NetworkManager
systemctl status NetworkManager
systemctl stop NetworkManager
systemctl disable NetworkManager
systemctl status NetworkManager

#net tuning
echo 1 > /proc/sys/net/ipv4/ip_forward

#vm.max_map_count tuning
sysctl -w vm.max_map_count=655360
echo 'vm.max_map_count=655360' >>  /etc/sysctl.conf

#ulimit
ulimit -SHn 655360
echo "* - nofile 655360" > /etc/security/limits.d/20-nproc.conf

#TODO Other kenerl param for K8S
cat >> /etc/sysctl.conf << FORMAT
net.ipv4.ip_forward=1
vm.max_map_count=655360
vm.swappiness=0
net.ipv4.tcp_syncookies=1 
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_tw_recycle=1
net.ipv4.tcp_fin_timeout=30
FORMAT
sysctl -p

#TMOUT
sed -i 's/TMOUT/\#TMOUT/g'  /etc/profile
source /etc/profile