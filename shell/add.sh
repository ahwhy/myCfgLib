#!/bin/sh
# shell中各类累加方法记录

count=1

count=$(($count+1))

count=$[$count+1]

count=`expr $count + 1`

let count++

let count+=1

echo $count