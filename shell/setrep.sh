#!/usr/bin/env bash

# 设置文件副本数为1

if [ $# -ne 1 ]; then
  echo "param input error"
  exit 1
fi

LIST=$1

for line in $(cat $LIST); do
  echo $line
  sudo -u hdfs hadoop fs -setrep -w -R 1 $line
done
