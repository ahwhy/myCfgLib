#!/bin/bash

# 主机存活检测
# 192.168.0.1
# 192.168.0.2

for i in `cat /root/ping.txt` 
 do 
  ping  -w 1 $i > /dev/null 2>&1
    if [ $? -eq 0 ]
     then
       echo "The server(${i}) status is UP"
     else
       echo "The server(${i}) status is DOWN"
    fi
 done
