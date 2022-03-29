#!/bin/bash

# 截取IP
IP=`ifconfig eth0 |awk -F " " 'NR==2{print $2}'`

# 定义使用率,并转换为数字
SPACE=`df -Ph |awk '{print int($5)}'`

for i in $SPACE;
do
  if [ $i -ge 90 ] then
    echo "$IP的磁盘使用率已经超过了90%，请及时处理"
  fi
done