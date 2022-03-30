#!/bin/bash

# NOTE: THIS NTP SERVICE CHECK SCRIPT ASSUME THAT NTP SERVICE IS RUNNING UNDER SYSTEMD.
#       THIS IS JUST AN EXAMPLE. YOU CAN WRITE YOUR OWN NODE PROBLEM PLUGIN ON DEMAND.

OK=0
NONOK=1
UNKNOWN=2

ntpStatus=1
systemctl status ntpd.service | grep 'Active:' | grep -q running
if [ $? -ne 0 ]; then
    ntpStatus=0
fi

chronydStatus=1
systemctl status chronyd.service | grep 'Active:' | grep -q running
if [ $? -ne 0 ]; then
    chronydStatus=0
fi

if [ $ntpStatus -eq 0 ] && [ $chronydStatus -eq 0 ]; then
    echo "NTP service is not running"
    exit $NONOK
fi

echo "NTP service is running"
exit $OK
