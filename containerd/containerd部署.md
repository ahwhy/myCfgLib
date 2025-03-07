# Containerd 部署

## 资源链接
- [runc.amd64](https://github.com/opencontainers/runc/releases/download/v1.1.0/runc.amd64)
- [containerd-1.5.10-linux-amd64.tar.gz](https://github.com/containerd/containerd/releases/download/v1.5.10/containerd-1.5.10-linux-amd64.tar.gz)
- [crictl-v1.22.0-linux-amd64.tar.gz](https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.22.0/crictl-v1.22.0-linux-amd64.tar.gz)

## 使用二进制文件部署containerd

```shell
$ mv runc.amd64 runc
$ tar -xvf crictl-v1.23.0-linux-arm64.tar.gz 
$ chmod +x crictl runc
$ sudo cp crictl runc /usr/local/bin/

$ mkdir containerd
$ tar -xvf containerd-1.5.10-linux-amd64.tar.gz -C containerd
$ sudo cp containerd/bin/* /usr/bin/

# 创建 containerd 启动配置 config.toml:
$ sudo mkdir -p /etc/containerd/
$ cat <<EOF | sudo tee /etc/containerd/config.toml
version = 2

root = "/var/lib/containerd"
state = "/run/containerd"
disabled_plugins = []
required_plugins = ["io.containerd.grpc.v1.cri"]
oom_score = -999

# Alibaba Cloud Vendor enhancement configuration
# imports = ["/etc/containerd/alibabacloud.toml"]


[grpc]
  address = "/run/containerd/containerd.sock"
  max_recv_message_size = 16777216
  max_send_message_size = 16777216


[debug]
  address = "/run/containerd/debug.sock"
  level = "info"

[timeouts]
  "io.containerd.timeout.shim.cleanup" = "5s"
  "io.containerd.timeout.shim.load" = "5s"
  "io.containerd.timeout.shim.shutdown" = "3s"
  "io.containerd.timeout.task.state" = "2s"

[plugins]
  [plugins."io.containerd.gc.v1.scheduler"]
    pause_threshold = 0.02
    deletion_threshold = 0
    mutation_threshold = 100
    schedule_delay = "0s"
    startup_delay = "100ms"

  [plugins."io.containerd.grpc.v1.cri"]
    sandbox_image = "registry-vpc.cn-hangzhou.aliyuncs.com/acs/pause:3.5"
    ignore_image_defined_volumes = true

    [plugins."io.containerd.grpc.v1.cri".containerd]
      snapshotter = "overlayfs"
      default_runtime_name = "runc"
      disable_snapshot_annotations = true
      discard_unpacked_layers = false

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
          runtime_type = "io.containerd.runc.v2"
          privileged_without_host_devices = false
          [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
            NoPivotRoot = false
            NoNewKeyring = false
            SystemdCgroup = true

    [plugins."io.containerd.grpc.v1.cri".cni]
      bin_dir = "/opt/cni/bin"
      conf_dir = "/etc/cni/net.d"
      max_conf_num = 1

    [plugins."io.containerd.grpc.v1.cri".registry]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
          endpoint = ["https://registry-1.docker.io"]

  [plugins."io.containerd.internal.v1.opt"]
    path = "/opt/containerd"

  [plugins."io.containerd.internal.v1.restart"]
    interval = "10s"

  [plugins."io.containerd.metadata.v1.bolt"]
    content_sharing_policy = "shared"
EOF

# 创建 systemd 配置 containerd.service
$ cat <<EOF | sudo tee /etc/systemd/system/containerd.service
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target local-fs.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/bin/containerd

Type=notify
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
# Having non-zero Limit*s causes performance problems due to accounting overhead
# in the kernel. We recommend using cgroups to do container-local accounting.
LimitNPROC=infinity
LimitCORE=infinity
LimitNOFILE=1048576
# Comment TasksMax if your systemd version does not supports it.
# Only systemd 226 and above support this version.
TasksMax=infinity
OOMScoreAdjust=-999

[Install]
WantedBy=multi-user.target
EOF


$ sudo systemctl daemon-reload
$ sudo systemctl enable containerd
$ sudo systemctl start containerd

$ crictl config runtime-endpoint unix:///var/run/containerd/containerd.sock
$ crictl -h

# 查看 containerd 启动日志
$ journalctl -xe -u containerd --no-pager
```

## 使用 crictl 和 ctr 工具

```shell
# 查看 ctr 工具命令
$ ctr -n k8s.io -- help
$ ctr -n k8s.io containers list
$ ctr -n k8s.io c info xxxxxx
$ ctr -n k8s.io tasks ls

# 查看镜像层配置
$ ctr -n k8s.io content get sha256:xxx | python -m json.tool | less

# containerd 如何push本地镜像到镜像仓库
# ls
$ ctr --namespace k8s.io images ls

#tag
$ ctr --namespace k8s.io images tag docker.io/kennethreitz/httpbin:latest XXXXXXXX.com/test/docker.io:httpbin

#push
$ ctr --namespace k8s.io images push XXXXXXXX.com/test/docker.io:httpbin --user=XXXXXX
# 需要输入密码

# 通过 --creds 参数，可以直接拉取私有镜像，其中username和password需要替换真实用户名和密码
$ crictl  pull --creds  $username:$password registry.cn-hangzhou.aliyuncs.com/test-cri/busybox:latest

# 如果开启 config_path = "/etc/containerd/cert.d" 的配置方法
# http方式
$ mkdir -p /etc/containerd/cert.d/192.168.66.42:5000
$ cat << EOF > /etc/containerd/cert.d/192.168.66.42:5000/hosts.toml
server = "http://192.168.66.42:5000"

[host."http://192.168.66.42:5000"]
  capabilities = ["pull", "resolve", "push"]
EOF

# 自签证书
$ mkdir -p /etc/containerd/cert.d/harbor.test-cri.com
$ cat << EOF > /etc/containerd/cert.d/harbor.test-cri.com/hosts.toml
server = "https://harbor.test-cri.com"

[host."https://harbor.test-cri.com"]
  capabilities = ["pull", "resolve", "push"]
  skip_verify = true
  # ca = "/opt/ssl/ca.crt"  # 或者上传ca证书
EOF

# 进入 containerd 容器网络 namespace 中抓包
# 1、节点上找到pod id
crictl pods | grep {pod name}

# 2、通过pod id，找到容器 id
crictl ps | grep {pod id}

# 3、找到容器中的进程 id
crictl inspect {容器 id} | grep pid

# 4、进入进程的网络 namespace
nsenter -t {进程pid} -n

# 5、执行 ifconfig ，确定只有pod网卡，后通过 tcpdump 抓包
nohup tcpdump -i any port 6379 -C 30 -W 50 -w /tmp/test.pcap &
# 该命令在后台运行，会生成30个文件，每个文件50M，即占用1500MB空间，抓的是全部网卡6379端口的包，请根据实际情况调整一下抓包参数
```