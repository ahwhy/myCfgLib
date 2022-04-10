#!/bin/bash

OK=0
NONOK=1
UNKNOWN=2

check_url='http://100.100.100.200/latest/meta-data/instance/spot/termination-time'
for ((i=1; i<=5; i ++))
do
  resp=$(curl --max-time 5 -s $check_url)
  if [ $? != 0 ]; then
    sleep 1
  else
    echo $resp
    date --date $resp +"%s"
    if [ $? != 0 ]; then
      exit $OK
    else
      echo "instance is going to be terminated at $resp"
      exit $NONOK
    fi
  fi
done
echo "curl $check_url exe fail after try 5 times"
exit $OK
