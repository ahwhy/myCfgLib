#!/bin/bash

sed -i 's/^search .*//g' /etc/resolv.conf
usermod -u 2000 hadoop
groupmod -g 2000 hadoop
groupadd hadoop -g 2000
adduser hadoop -u 2000 -g hadoop
yum -y install xfsprogs parted
i=1
k=1
sum=`cat /proc/partitions |awk '{print $4}' | grep 'sd[c-z]$' | wc -l`
while [ $i -lt $sum ]                   
do
j=`echo $i|awk '{printf "%c",97+$i}'`
#x=`cat /proc/partitions  | grep sd[$j]| awk '{print $3}' |awk '{sum+=$1} END {printf "%.2fT",sum*0.9/(1000000000)}'`
sleep 1s
PARTION=`cat /proc/partitions | grep sd[$j] |wc -l`
l=1
if [ $PARTION != 3 ];then
while [ $l -lt $PARTION ]
do
parted -s /dev/sd$j rm $l
sleep 2
l=$(($l+1))
done
fi
parted -s /dev/sd$j mklabel gpt
sleep 2

x=`cat /proc/partitions  | grep sd[$j]|grep -v sdb| awk '{print $3}' |awk '{sum+=$1} END {printf "%.1fT",sum*0.9/(1000000000)}'`
parted -s /dev/sd$j mkpart primary 1 $x && parted -s /dev/sd$j mkpart primary $x 100%
#mkfs.ext4 -T largefile -N 100000000 /dev/sd${j}1 >/dev/null
sleep 2s
mkfs.ext4  /dev/sd${j}1 && mkfs.ext4   /dev/sd${j}2
sleep 1s
mount="/dev/sd${j}1       /disk$(($k-1))  ext4    defaults        0       0"
mkdir /disk${k}
mount -t ext4 /dev/sd${j}1 /disk$(($k-1))
echo $mount >>/etc/fstab
mount="/dev/sd${j}2       /hre$(($k-1))  ext4    defaults        0       0"
mkdir /hre${k}
mount -t ext4 /dev/sd${j}2 /hre$(($k-1))
echo $mount >>/etc/fstab
mkdir  -p /hre${k}/hadoop-run-env
mkdir -p /disk${k}/hadoop-data
k=$(($k+1))
i=$(($i+1))
done
mount -a
chown -R hadoop:hadoop /hre*
chown -R hadoop:hadoop /disk*

#this is for hadoop dn
parted -s /dev/sdm mklabel gpt
sleep 2
x=`cat /proc/partitions  | grep sdm| awk '{print $3}' |awk '{sum+=$1} END {printf "%.1fT",sum*0.9/(1000000000)}'`
parted -s /dev/sdm mkpart primary 1 $x && parted -s /dev/sdm mkpart primary $x 100%
mkfs.ext4 /dev/sdm1 && mkfs.ext4 /dev/sdm2
mount="/dev/sdm1       /disk11  ext4    defaults        0       0"
mkdir /disk11
mount -t ext4 /dev/sdm1 /disk11
echo $mount >>/etc/fstab
mount="/dev/sdm2       /hre11  ext4    defaults        0       0"
mkdir /hre11
mount -t ext4 /dev/sdm2 /hre11
echo $mount >>/etc/fstab
mkdir  -p /hre11/hadoop-run-env
mkdir -p /disk11/hadoop-data
parted -s /dev/sdn mklabel gpt
sleep 2
x=`cat /proc/partitions  | grep sdn| awk '{print $3}' |awk '{sum+=$1} END {printf "%.1fT",sum*0.9/(1000000000)}'`
parted -s /dev/sdn mkpart primary 1 $x && parted -s /dev/sdn mkpart primary $x 100%
mkfs.ext4 /dev/sdn1 && mkfs.ext4 /dev/sdn2
mount="/dev/sdn1       /disk12  ext4    defaults        0       0"
mkdir /disk12
mount -t ext4 /dev/sdn1 /disk12
echo $mount >>/etc/fstab
mount="/dev/sdn2       /hre12  ext4    defaults        0       0"
mkdir /hre12
mount -t ext4 /dev/sdn2 /hre12
echo $mount >>/etc/fstab
mkdir  -p /hre12/hadoop-run-env
mkdir -p /disk12/hadoop-data
chown -R hadoop:hadoop /hre*
chown -R hadoop:hadoop /disk*
