#!/bin/bash

cluster=$(kubectl get quota -n odeon -oyaml | grep -A 4 used)
echo -e "Cluster:$1"
echo -e "Cluster-quota:\n${cluster}"

kubectl get node | grep -v NAME | awk '{print $1}' > node.ip
cat node.ip | while read name;do
LAB=$(kubectl get node $name --show-labels | awk '{print $6}' | grep -v LABELS | awk -F "," '{for(i=1;i<=NF;i++) a[i,NR]=$i}END{for(i=1;i<=NF;i++) {for(j=1;j<=NR;j++) printf a[i,j] "";print ""}}' | egrep "server|datax-node" | tr "\n" ","|sed -e 's/,$/\n/')
CPU=$(kubectl describe node $name | grep -B 3 "Events" | awk '{print $1$2}' | grep \()    #Requests
MEM=$(kubectl describe node $name | grep -B 3 "Events" | awk '{print $5$6}' | grep \()    #Requests
echo -e "${name}    LAB:${LAB}  CPU:${CPU}  MEM:${MEM}"
done