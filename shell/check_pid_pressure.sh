#!/bin/sh

OK=0
NONOK=1
UNKNOWN=2

pidMax=$(cat /host/proc/sys/kernel/pid_max)
threshold=85
availablePid=$(($pidMax * $threshold / 100))
activePid=$(ls /host/proc/ |grep  -e "[0-9]" |wc -l)
if [ $activePid -gt $availablePid ]; then
    echo "Total running PIDs: $activePid, greater than $availablePid ($threshold% of pidMax $pidMax)"
    exit $NONOK
fi

echo "Has sufficient PID available"
exit $OK
