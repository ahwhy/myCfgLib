# docker 部署
    
## 资源链接
- [官方rpm包 docker-ce-18.06.3.ce-3.el7.x86_64.rpm](https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-18.06.3.ce-3.el7.x86_64.rpm)
- [二进制文件包 docker-18.06.3-ce.tgz](http://mirrors.aliyun.com/docker-ce/linux/static/stable/x86_64/docker-18.06.3-ce.tgz)

## 使用二进制文件部署docker

```shell
$ tar -xzvf docker-18.06.3-ce.tgz 
$ cp docker/* /usr/bin
$ cp docker.service docker.socket containerd.service  /lib/systemd/system/
$ systemctl unmask containerd
$ systemctl unmask docker
$ systemctl unmask docker.socket
$ systemctl enable docker
$ systemctl enable containerd
$ systemctl start docker
$ systemctl start containerd

$ cat << EOF | sudo tee /lib/systemd/system/docker.service
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
ExecStart=/usr/bin/dockerd -H 127.0.0.1:2375 -H unix:///var/run/docker.sock --insecure-registry=172.16.59.151 --insecure-registry=hub.iflytek.com --registry-mirror=https://registry.docker-cn.com --default-ulimit=core=0:0 --live-restore
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
EOF

$ cat << EOF | sudo tee /lib/systemd/system/docker.socket
[Unit]
Description=Docker Socket for the API
PartOf=docker.service

[Socket]
ListenStream=/var/run/docker.sock
SocketMode=0660
SocketUser=root
SocketGroup=docker

[Install]
WantedBy=sockets.target
EOF

$ cat << EOF | sudo tee /lib/systemd/system/containerd.service
#   Copyright 2018-2020 Docker Inc.

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at

#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/bin/containerd
KillMode=process
Delegate=yes
LimitNOFILE=1048576
# Having non-zero Limit*s causes performance problems due to accounting overhead
# in the kernel. We recommend using cgroups to do container-local accounting.
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity

[Install]
WantedBy=multi-user.target
EOF
```