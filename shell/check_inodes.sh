#!/bin/bash
# check inode utilization on block device of mounting point /
OK=0
NONOK=1
UNKNOWN=2

iuse=$(df -i | grep "/$" | grep -e [0-9]*% -o | tr -d %)

if [[ $iuse -gt 80 ]]; then
echo "current inode usage is over 80% on node"
exit $NONOK
fi
echo "node has no inode pressure"
exit $OK
