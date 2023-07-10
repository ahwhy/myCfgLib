#!/bin/bash
#set fileformat=unix
#set -o errexit

a="docker-ce-18.09.6-3.el7.x86_64"
b="docker-ce-cli-18.09.6-3.el7.x86_64"
 
#NO.1 Ready Yum
echo "start NO.1 Ready Yum"
if [ ! -d /etc/yum.repos.d/bak ]; then
    mkdir /etc/yum.repos.d/bak
    echo "Create /etc/yum.repos.d/bak"
fi
mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/bak/
wget -P /etc/yum.repos.d/ http://172.16.0.2/source/docker-ce.repo  &> /dev/null
wget -P /etc/yum.repos.d/ http://172.16.0.2/source/centos/aliyun/Centos-7-aliyun.repo  &> /dev/null
yum clean all >> /dev/null 2>&1
yum makecache >> /dev/null 2>&1
echo -e "\033[47;30m [----- NO.1 Yum Is Ready-----] \033[0m"
echo "****************************************"

#NO.2 Install Docker
echo "start NO.2 Install Docker"
yum -y remove docker-ce-*
yum -y install $a $b
if [ ! -d /data/docker ]; then
    mkdir /data/docker
    echo "Create /data/docker"
fi
cat > /usr/lib/systemd/system/docker.service <<FORMAT

[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target

[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
# exists and systemd currently does not support the cgroup feature set required
# for containers run by docker
ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT
ExecStart=/usr/bin/dockerd -H 127.0.0.1:2375 -H unix:///var/run/docker.sock --insecure-registry=hub.ilinux.cn --registry-mirror=https://registry.docker-cn.com --default-ulimit=core=0:0 --live-restore --graph /data/docker
ExecReload=/bin/kill -s HUP $MAINPID
# Having non-zero Limit*s causes performance problems due to accounting overhead
# in the kernel. We recommend using cgroups to do container-local accounting.
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
# Uncomment TasksMax if your systemd version supports it.
# Only systemd 226 and above support this version.
#TasksMax=infinity
TimeoutStartSec=0
# set delegate yes so that systemd does not reset the cgroups of docker containers
Delegate=yes
# kill only the docker process, not all processes in the cgroup
KillMode=process
# restart the docker process if it exits prematurely
Restart=on-failure
StartLimitBurst=3
StartLimitInterval=60s

[Install]
WantedBy=multi-user.target 

FORMAT
echo -e "\033[47;30m [----- NO.2 Install Docker IS Done-----] \033[0m"
echo "****************************************"

#NO.3 Install Nvidia-Docker&&Kubernetes
echo "start NO.3 Install Nvidia-Docker&&Kubernetes"
if [ -f nvidia-docker2-v20200514.tar.gz]; then
    tar -xzvf /root/nvidia-docker2-v20200514.tar.gz  &> /dev/null
    cd /root/nvidia-docker2
    sh install.sh  &> /dev/null
    cat > /etc/docker/daemon.json <<FORMAT 
{
"default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}  
FORMAT
else
    echo -e "\033[47;31;5m [----- Nvidia-Docker File Is No Existing -----] \033[0m"
fi
if [ -f nvidia_k8s-plugin.tar.gz ]; then
	 tar -xzvf /root/nvidia_k8s-plugin.tar.gz  &> /dev/null
	 docker load -i /root/nvidia_k8s-plugin/nvidia_k8s-device-plugin_beta.tar 
	 echo -e "\033[47;30m [----- NO.3 Install Nvidia-Docker&&Kubernetes Is Done-----] \033[0m"
else
    echo -e "\033[47;31;5m [----- Nvidia-Kubernetes File Is No Existing -----] \033[0m"
fi
echo "****************************************"

#NO.4 Ready Docker 
echo "start NO.4 Ready Docker"
systemctl daemon-reload
systemctl enable docker
systemctl restart docker
echo -e "\033[47;30m [----- NO.4 Docker Is Running-----] \033[0m"
echo "****************************************"

#修改kubelet
#ll /usr/bin/ | grep kubelet
#systemctl status kubelet.service
#systemctl stop kubelet.service
#mv /usr/bin/kubelet /usr/bin/kubelet.bak.20200813_1100
#scp /usr/bin/kubelet root@10.0.0.111:/usr/bin/
#New Kubelet (nokmem Bug Version /usr/bin/kubelet)
#chmod a+x /usr/bin/kubelet
#systemctl start kubelet.service
#kubectl get node
#kubectl describe node node005-sha.ultron.odeon.cn
#https://www.jianshu.com/p/4be507244abf
#cat /sys/fs/cgroup/memory/kubepods/burstable/pod<pod-id>/<containerID>/memory.kmem.slabinfo
#cat /sys/fs/cgroup/memory/kubepods/burstable/pod<podid>/<containerID>/memory.kmem.usage_in_bytes
