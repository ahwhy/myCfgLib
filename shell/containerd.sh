#!/bin/sh
# 刷新容器中host文件

array_list=`docker ps |grep -v POD |grep -v kube-proxy |grep -v calico-node |grep -v install-cni | grep -v CONTAINER|awk '{print $1}'`
for container_id in ${array_list};
do
   echo ${container_id}
   container_host_file=`docker inspect ${container_id} |grep etc-hosts |grep Source |awk -F: '{print $2}' |awk -F\" '{print $2}'`
   #cat /etc/hosts > ${container_host_file}
   if test -z ${container_host_file} ; then
     echo ${container_id} "is Null"
   else
     echo "Before cat /etc/hosts"
     cat ${container_host_file}
     #cat  
     cat /etc/hosts > ${container_host_file}
     
     echo "After cat /etc/hosts"
     cat ${container_host_file}
   fi
done