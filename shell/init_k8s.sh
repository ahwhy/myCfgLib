#!/bin/bash
set -o errexit

echo -e "[ Images distribute and load ] Start distributed and load images."

CONFIGFILE=kdeploy.yaml
kubernetesVersion=`cat $CONFIGFILE | grep kubernetesVersion | awk '{print $2}'`
PWD=`pwd`

if [ ! -d "$PWD/depend/binary/$kubernetesVersion" ]; then
    echo -e "$PWD/depend/binary/$kubernetesVersion directory does not exist."
    exit
fi

if [ ! -d "$PWD/depend/addons/calico/yaml/" ]; then
    echo -e "$PWD/depend/addons/calico/yaml/ directory does not exist."
    exit
fi

if [ `ls -A $PWD/depend/addons/calico/yaml/ | wc -w` -eq 0 ]; then
    echo -e "$PWD/depend/addons/calico/yaml/ can't is empty."
    exit
fi

if [ ! -f $PWD/depend/images/master-$kubernetesVersion.tar.gz ] || [ ! -f $PWD/depend/images/node-$kubernetesVersion.tar.gz ]; then
    echo -e "master-$kubernetesVersion.tar.gz or node-$kubernetesVersion.tar.gz does not exist."
    exit
fi

AlreadyInCluster=""
if which kubectl &>/dev/null && ps -ef | grep kube-apiserver | grep -v grep &>/dev/null; then
    AlreadyInCluster=`kubectl describe nodes | grep IP | awk '{print $2}'`
fi

master=`sed -n -e '/^master:/=' $CONFIGFILE`
node=`sed -n -e '/^node:/=' $CONFIGFILE`
master=$[master+1]
node=$[node-1]
masterIPs=`sed -n "${master},${node}p" $CONFIGFILE | grep -v \# | grep - | awk '{print $2}'`

etcd=0
if cat $CONFIGFILE | grep "etcd:" &>/dev/null; then
    etcd=`sed -n -e '/^etcd:/=' $CONFIGFILE`
fi

etcd=$[etcd-1]
nodeIPs=`sed -n "${node},${etcd}p" $CONFIGFILE | grep -v \# | grep - | awk '{print $2}'`

for ip in ${masterIPs[@]};
do
    if echo "${AlreadyInCluster[@]}" | grep -wq "$ip" &>/dev/null; then
        continue
    fi
    pssh -i -H $ip "mkdir -p /opt/kubernetes/images/"
    pscp -H $ip $PWD/depend/images/master-$kubernetesVersion.tar.gz /opt/kubernetes/images/
    pssh -t 0 -i -H $ip "tar -zxvf /opt/kubernetes/images/master-$kubernetesVersion.tar.gz -C /opt/kubernetes/images/;docker load -i /opt/kubernetes/images/master-$kubernetesVersion.tar"
    pssh -H $ip "docker tag hub.iflytek.com/k8s/pause:3.1 hub.iflytek.com/k8s/pause-amd64:3.1;docker tag hub.iflytek.com/k8s/pause-amd64:3.1 hub.iflytek.com/k8s/pause:3.1;"
    echo ""
done

for ip in ${nodeIPs[@]};
do
    if echo "${AlreadyInCluster[@]}" | grep -wq "$ip" &>/dev/null; then
        continue
    fi
    pssh -i -H $ip "mkdir -p /opt/kubernetes/images/"
    pscp -H $ip $PWD/depend/images/node-$kubernetesVersion.tar.gz /opt/kubernetes/images/
    pssh -t 0 -i -H $ip "tar -zxvf /opt/kubernetes/images/node-$kubernetesVersion.tar.gz -C /opt/kubernetes/images/;docker load -i /opt/kubernetes/images/node-$kubernetesVersion.tar"
    pssh -H $ip "docker tag hub.iflytek.com/k8s/pause:3.1 hub.iflytek.com/k8s/pause-amd64:3.1;docker tag hub.iflytek.com/k8s/pause-amd64:3.1 hub.iflytek.com/k8s/pause:3.1;"
    echo ""
done

echo -e "[ Images distribute and load ] Images has been distributed and load to every node."

