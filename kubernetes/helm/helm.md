# 使用 Helm 打包应用

## 一、了解 Helm

Helm 是一个 Kubernetes 包管理工具，就像 Linux 系列的 Yum 和 Apt 一样，Helm 通过 chart 的方式组织 Kubernetes 之上的应用资源。当完成一个云原生应用的业务逻辑编码后，需要部署到 Kubernetes 集群中，繁多的 YAML 配置编写和维护过程是比较枯燥的，使用 Helm 能够很大程度上降低Kubernetes之上微服务部署的复杂度，提高工作效率。

### 1. Chart

一个 Chart 指的是一个 Helm 包，类似 Yum 的 rpm 包或者 Apt 的 dpkg 包，涵盖一个软件安装所需的一切"物料"，Chart 中包含的是在 Kubernetes 中运行的一个云原生应用方方面面的资源配置。

### 2. Repository

用来放置和分发 Chart 包的地方就叫 Repository，即 Chart 仓库的意思。

### 3. Release

一个 Chart 包可以在同一个 Kubernetes 集群中被多次部署，每次部署产生的实例就叫作一个 Release。比如同样一个 Web 应用打包成 Chart 之后，可以在 dev 和 prod 两个 namespace 中分别部署一份实例，出于不同的目的，这里的两个实例就是两个 Release。

### 4. ArtifactHub

类似于 DockerHub 和 GitHub ，Helm 的 Chart 也有一个 Hub，其地址是 https://artifacthub.io。并且，ArtifactHub中存放的不只是Chart，还有kubectl plugins、OLM operators、Tekton tasks等。


## 二、Helm 的安装

在 Helm 的 [release页面](https://github.com/helm/helm/releases) 可以看到当前最新的发布版本，可以选择下载自己系统对应的 Helm 版本
```shell
➜ wget https://get.helm.sh/helm-v3.13.0-darwin-amd64.tar.gz
--2023-09-30 20:54:50--  https://get.helm.sh/helm-v3.13.0-darwin-amd64.tar.gz
2023-09-30 21:02:56 (34.6 KB/s) - 已保存 “helm-v3.13.0-darwin-amd64.tar.gz” [17027759/17027759])

# 在环境中下载解压后会得到一个 darwin-arm64 目录
➜ tar -xzvf helm-v3.13.0-darwin-amd64.tar.gz
x darwin-amd64/
x darwin-amd64/LICENSE
x darwin-amd64/helm
x darwin-amd64/README.md

# 接着将 darwin-arm64 中的 Helm 文件存放到合适的位置
➜ sudo mv darwin-amd64/helm /usr/local/bin/

➜ helm version
version.BuildInfo{Version:"v3.13.0", GitCommit:"825e86f6a7a38cef1112bfa606e4127a706749b1", GitTreeState:"clean", GoVersion:"go1.20.8"}
```


## 二、Helm 的常用操作

介绍 Helm 的一下常用基础命令。

### 1. 搜索 Chart 包

安装好 Helm 客户端命令后，可以通过 search 命令来找到自己想要的 Chart 包
```shell
# 以 kube-prometheus-stack 为例，可以在 ArtifactHub 中搜索相应的Chart
# 如果输出结果太宽，通过 `--max-col-width` 来指定输出宽度
➜ helm search hub kube-prometheus-stack --max-col-width=100
URL                                                                             	CHART VERSION	APP VERSION	DESCRIPTION
https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack      	51.2.0       	v0.68.0    	kube-prometheus-stack collects Kubernetes manifests, Grafana dashboards, and Prometheus rules com...

➜ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

➜ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "jetstack" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

➜ helm repo list
NAME                	URL
jetstack            	https://charts.jetstack.io
prometheus-community	https://prometheus-community.github.io/helm-charts

➜ helm search repo prometheus-community
NAME                                              	CHART VERSION	APP VERSION	DESCRIPTION
prometheus-community/alertmanager                 	1.7.0        	v0.26.0    	The Alertmanager handles alerts sent by client ...
prometheus-community/alertmanager-snmp-notifier   	0.1.2        	v1.4.0     	The SNMP Notifier handles alerts coming from Pr...
prometheus-community/jiralert                     	1.6.0        	v1.3.0     	A Helm chart for Kubernetes to install jiralert
prometheus-community/kube-prometheus-stack        	51.2.0       	v0.68.0    	kube-prometheus-stack collects Kubernetes manif...
prometheus-community/kube-state-metrics           	5.13.0       	2.10.0     	Install kube-state-metrics to generate and expo...
prometheus-community/prom-label-proxy             	0.6.0        	v0.7.0     	A proxy that enforces a given label in a given ...
prometheus-community/prometheus                   	25.0.0       	v2.47.0    	Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-adapter           	4.6.0        	v0.11.1    	A Helm chart for k8s prometheus adapter
prometheus-community/prometheus-blackbox-exporter 	8.4.0        	v0.24.0    	Prometheus Blackbox Exporter
prometheus-community/prometheus-cloudwatch-expo...	0.25.2       	0.15.4     	A Helm chart for prometheus cloudwatch-exporter
prometheus-community/prometheus-conntrack-stats...	0.5.7        	v0.4.15    	A Helm chart for conntrack-stats-exporter
prometheus-community/prometheus-consul-exporter   	1.0.0        	0.4.0      	A Helm chart for the Prometheus Consul Exporter
prometheus-community/prometheus-couchdb-exporter  	1.0.0        	1.0        	A Helm chart to export the metrics from couchdb...
prometheus-community/prometheus-druid-exporter    	1.1.0        	v0.11.0    	Druid exporter to monitor druid metrics with Pr...
prometheus-community/prometheus-elasticsearch-e...	5.3.1        	v1.6.0     	Elasticsearch stats exporter for Prometheus
prometheus-community/prometheus-fastly-exporter   	0.2.0        	7.2.4      	A Helm chart for the Prometheus Fastly Exporter
prometheus-community/prometheus-ipmi-exporter     	0.1.0        	1.6.1      	This is an IPMI exporter for Prometheus.
prometheus-community/prometheus-json-exporter     	0.7.1        	v0.5.0     	Install prometheus-json-exporter
prometheus-community/prometheus-kafka-exporter    	2.7.0        	v1.7.0     	A Helm chart to export the metrics from Kafka i...
prometheus-community/prometheus-modbus-exporter   	0.1.0        	0.4.0      	A Helm chart for prometheus-modbus-exporter
prometheus-community/prometheus-mongodb-exporter  	3.4.0        	0.39.0     	A Prometheus exporter for MongoDB metrics
prometheus-community/prometheus-mysql-exporter    	2.0.0        	v0.15.0    	A Helm chart for prometheus mysql exporter with...
prometheus-community/prometheus-nats-exporter     	2.13.0       	0.12.0     	A Helm chart for prometheus-nats-exporter
prometheus-community/prometheus-nginx-exporter    	0.1.1        	0.11.0     	A Helm chart for the Prometheus NGINX Exporter
prometheus-community/prometheus-node-exporter     	4.23.1       	1.6.1      	A Helm chart for prometheus node-exporter
prometheus-community/prometheus-operator          	9.3.2        	0.38.1     	DEPRECATED - This chart will be renamed. See ht...
prometheus-community/prometheus-operator-admiss...	0.7.0        	0.68.0     	Prometheus Operator Admission Webhook
prometheus-community/prometheus-operator-crds     	6.0.0        	v0.68.0    	A Helm chart that collects custom resource defi...
prometheus-community/prometheus-pgbouncer-exporter	0.1.1        	1.18.0     	A Helm chart for prometheus pgbouncer-exporter
prometheus-community/prometheus-pingdom-exporter  	2.5.0        	20190610-1 	A Helm chart for Prometheus Pingdom Exporter
prometheus-community/prometheus-pingmesh-exporter 	0.3.0        	v1.1.0     	Prometheus Pingmesh Exporter
prometheus-community/prometheus-postgres-exporter 	5.1.0        	v0.14.0    	A Helm chart for prometheus postgres-exporter
prometheus-community/prometheus-pushgateway       	2.4.1        	v1.6.1     	A Helm chart for prometheus pushgateway
prometheus-community/prometheus-rabbitmq-exporter 	1.8.1        	v0.29.0    	Rabbitmq metrics exporter for prometheus
prometheus-community/prometheus-redis-exporter    	6.0.0        	v1.54.0    	Prometheus exporter for Redis metrics
prometheus-community/prometheus-smartctl-exporter 	0.6.0        	v0.11.0    	A Helm chart for Kubernetes
prometheus-community/prometheus-snmp-exporter     	1.8.0        	v0.21.0    	Prometheus SNMP Exporter
prometheus-community/prometheus-stackdriver-exp...	4.3.1        	0.13.0     	Stackdriver exporter for Prometheus
prometheus-community/prometheus-statsd-exporter   	0.10.1       	v0.24.0    	A Helm chart for prometheus stats-exporter
prometheus-community/prometheus-to-sd             	0.4.2        	0.5.2      	Scrape metrics stored in prometheus format and ...
prometheus-community/prometheus-windows-exporter  	0.1.1        	0.22.0     	A Helm chart for prometheus windows-exporter
```

- Helm Repository 的常用基础命令
    - `helm search hub [KEYWORD] [flags]` 在 ArtifactHub 中从所有的 Repository 内搜索相关 Chart
    - `helm repo add [NAME] [URL] [flags]` 本地添加一个 Repository
    - `helm repo list [flags]` 列出本地所有 Repository，list 可以简写为 ls
    - `helm search repo [keyword] [flags]` 在本地 Repository 搜索匹配的 Chart


### 2. 安装 Chart 包

**a. 通过 Helm 安装一个 kube-prometheus-stack 实例**

有了 Chart 包之后，下一步是安装这个包：
```shell
# 安装命令格式
➜ helm install -h
Usage:
  helm install [NAME] [CHART] [flags]
```
NAME 指的是 Instance 的名字。CHART 就是要使用的 Chart 包地址，既可以是远程仓库中的包，也可以是本地的 Chart 压缩包，或者是解压后的 Chart 包。

以 kube-prometheus-stack 的安装为例：
```shell
➜ helm install prometheus-community/kube-prometheus-stack -n monitoring -g

➜ kubectl -n monitoring get all

# 通过 helm ls 来列出所有已经安装的Chart
➜ helm ls -A
NAME                             	NAMESPACE             	REVISION	UPDATED                                	STATUS  	CHART                                  	APP VERSION
ack-ai-installer                 	kube-system           	1       	2023-09-06 17:24:03.416385009 +0800 CST	deployed	ack-ai-installer-1.8.2                 	1.6.2
ack-alibaba-cloud-metrics-adapter	kube-system           	1       	2023-08-22 19:50:37.352569378 +0800 CST	deployed	ack-alibaba-cloud-metrics-adapter-1.3.2	0.1.3
ack-arena                        	kube-system           	1       	2023-09-06 17:23:58.458383158 +0800 CST	deployed	ack-arena-0.9.10                       	0.9.10
ack-cost-exporter                	kube-system           	1       	2023-07-31 17:55:39.866086761 +0800 CST	deployed	ack-cost-exporter-1.0.13               	0.1
ack-extend-network-controller    	kube-system           	1       	2023-09-08 16:05:29.777366722 +0800 CST	deployed	ack-extend-network-controller-0.6.0    	v0.6.0
ack-node-local-dns               	kube-system           	1       	2023-07-27 11:29:56.632436778 +0800 CST	deployed	ack-node-local-dns-1.5.6               	1.5.6
ack-node-problem-detector        	kube-system           	1       	2023-07-27 11:29:55.453833841 +0800 CST	deployed	ack-node-problem-detector-1.2.16       	0.8.0
gateway-api                      	kube-system           	1       	2023-07-27 11:29:45.756573354 +0800 CST	deployed	gateway-api-0.6.0                      	v0.6.0

# 通过 helm status 来查看某个Chart实例的状态
➜ helm -n kube-system status ack-node-problem-detector
NAME: ack-node-problem-detector
LAST DEPLOYED: Thu Jul 27 11:29:55 2023
NAMESPACE: kube-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

- `helm install` 每个参数的对应含义
    - `prometheus-community/kube-prometheus-stack` 表示Chart地址，也就是在本地仓库 prometheus-community 中的 kube-prometheus-stack
    - `-n monitoring` 等价于 `--namespace monitoring`，表示这个实例将安装在 monitoring 命名空间下，如果这个命名空间不存在，则会被自动创建
    - `-g` 等价于 `--generate-name`，表示不手动指定实例名，而是自动生成一个名字来使用

**b. Helm 安装资源的顺序**

Helm 安装各种 Kubernetes 是遵循一定顺序的，比如 Namespace 和 Deployment 都需要创建时

- 具体安装顺序为
    - `Namespace`
    - `NetworkPolicy`
    - `ResourceQuota`
    - `LimitRange`
    - `PodSecurityPolicy`
    - `PodDisruptionBudget`
    - `ServiceAccount`
    - `Secret`
    - `SecretList`
    - `ConfigMap`
    - `StorageClass`
    - `PersistentVolume`
    - `PersistentVolumeClaim`
    - `CustomResourceDefinition`
    - `ClusterRole`
    - `ClusterRoleList`
    - `ClusterRoleBinding`
    - `ClusterRoleBindingList`
    - `Role`
    - `RoleList`
    - `RoleBinding`
    - `RoleBindingList`
    - `Service`
    - `DaemonSet`
    - `Pod`
    - `ReplicationController`
    - `ReplicaSet`
    - `Deployment`
    - `HorizontalPodAutoscaler`
    - `StatefulSet`
    - `Job`
    - `CronJob`
    - `Ingress`
    - `APIService`

**c. 其他安装方法**

包括直接使用本地 Repository 中的 Chart 索引来安装一个实例，共有 4 种方法来完成安装过程。

- 这4种方法分别是
    - `helm install chartrepo/chartname` 直接从Repository安装
    - `helm install ./chartname-1.2.3.tgz` 通过helm pull下载
    - `helm install ./chartname` 解压这个压缩包
    - `helm install https://chartrepo.com/charts/chartname-1.2.3.tgz `从一个远程地址安装

### 3. 自定义 Chart 配置

前面通过 helm install 命令部署了一个 kube-prometheus-stack 实例，但是没有对这个实例进行任何配置。大多数情况下，需要知道部署的应用支持哪些配置项，然后根据具体的应用场景去调整相应的配置，比如部署到开发环境时分配更小的内存和实例数，部署到生产环境需要更大的内存和实例数分配。

**a. helm show values**
```shell
# 通过 helm show values，查看一个 Chart 的配置
➜ helm show values prometheus-community/kube-prometheus-stack
nameOverride: ""
...
```

**b. helm pull**
```shell
# 将这个 Chart 下载后，解压压缩包中的配置文件
➜ helm pull prometheus-community/kube-prometheus-stack
```

**c. 自定义配置内容**
```shell
# 直接将需要自定义的配置写入新文件
➜ cat <<EOF >values.replicas.txt
prometheus:
  prometheusSpec:
    replicas: 2
...
EOF

# 通过 -f values.replicas.txt 加载配置
➜ helm install prometheus-community/kube-prometheus-stack -n monitoring -g -f values.replicas.txt

# 或者通过 --set 来指定自定义配置项
➜ helm install prometheus-community/kube-prometheus-stack -n monitoring -g --set prometheus.prometheusSpec.replicas=2
```

--set参数 与 yaml配置 的对应关系
![--set参数 与 yaml配置 的对应关系]()


### 4. Release 升级、回滚、卸载

当一个 Chart 发布了新版本，或者想要更新同一个版本 Chart 包的一个实例时，可以通过 `helm upgrade` 命令来完成。如果更新之后需要回滚，则可以对应使用 `helm rollback` 命令。不知道想要回滚到哪个版本，就使用 `helm history` 命令；而删除这个 Chart 实例，就是使用 `helm uninstall` 命令。

- 具体格式如下
    - `helm upgrade [RELEASE] [CHART] [flags]` 更新一个Chart实例
    - `helm history RELEASE_NAME [flags]` 打印一个Release的所有历史修订版本(Revisions)
    - `helm rollback<RELEASE>[REVISION] [flags]` 回滚一个Release到指定版本
    - `helm uninstall RELEASE_NAME [...] [flags]` 删除一个Chart实例

### 5. Helm 命令的常用参数

- Helm 的 install/upgrade/rollback 等子命令都有几个很有用的参数
    - `--timeout` 等待 Kubernetes 命令执行完成的超时时间，默认是 50 毫秒，这里的值是一个 Golang 的 Duration
    - `--wait` 等待所有的 Pod 变成准备(ready)状态，PVC 完成绑定，deployments 至少有(Desired Pods 减去 maxUnavailable Pods)数量处于准备状态，Service 都有 IP 成功绑定；如果到了 --timeout 指定的超时时间，那么这个 Release 就会被标记为 FAILED 状态

## 四、封装一个新的 Chart 包

Helm 将描述一个应用如何将 Kubernetes 之上部署的各种相关资源文件打包在一起，这个打包格式或者这个包叫作 Chart。Chart 就是一个包含很多文件的目录，这个目录可以被打成一个有版本的压缩包，也可以被部署。

### 1. Chart 的目录结构

还是以 kube-prometheus-stack 为例，通过 helm pull 命令下载这个 Chart 包，然后解压缩，看其中的目录结构。
```shell
➜ helm pull prometheus-community/kube-prometheus-stack

➜ tar -xzvf kube-prometheus-stack-51.2.0.tgz
```
解压缩后会得到一个 kube-prometheus-stack 目录，也就是这个 Chart 的根目录，与 Chart 的名字相同，但是没有版本号信息。

- kube-prometheus-stack 中主要有如下的文件/目录：
    - `Chart.yaml` 包含 Chart 基本信息的 YAML 文件
    - `README.md` 可选的 readme 文件
    - `CONTRIBUTING.md` 可选的贡献者指引文件
    - `Chart.lock` 当前Chart的依赖锁定文件
    - `values.yaml` 当前Chart的默认配置文件
    - `charts/` 这个目录中放置的是当前Chart依赖的所有Chart
    - `crds/` 自定义资源配置存放目录，也就是当前Chart相关的所有CRD资源
    - `templates/` 存放模板文件的目录，模板与values配置加在一起可以渲染成完整的Kubernetes配置文件
    - `templates/NOTES.txt` 可选的纯文本使用帮助信息，也就是完成安装操作后控制台输出的帮助信息文本

### 2. Chart.yaml文件

Chart.yaml 是一个必选文件，其中存放的是一个 Chart 的基本描述信息，格式如下：
```yaml
apiVersion: The chart API version, always "v1" (required)                  # Chart 的 API 版本（必选）
name: The name of the chart (required)                                     # Chart 的名字（必选）
version: A SemVer 2 version (required)                                     # 一个 SemVer 2 格式的版本信息（必选）
kubeVersion: A SemVer range of compatible Kubernetes versions (optional)   # 一个用来描述兼容的 Kubernetes版本的 SemVer 格式范围信息（可选）
description: A single-sentence description of this project (optional)      # 当前项目的一句话描述（可选）
type:                                                                      # 当前 Chart 的类型（可选）
keywords:
  - A list of keywords about this project (optional)                       # 当前项目的一些关键字（可选）
home: The URL of this project's home page (optional)                       # 当前项目的主页URL（可选）
sources:
  - A list of URLs to source code for this project (optional)              # 当前项目的源码URL列表（可选）
dependencies:                                                              # 当前项目的依赖列表（可选）
  - name:                                                                  # 依赖的 Chart 的名字
    version:                                                               # 依赖的 Chart 的版本
    repository:                                                            # 依赖的 Chart 代码库的 URL
    condition:                                                             # 一个可选的 YAML 配置路径，需要是 bool 值，用来表示指定当前 Chart 是否启用
    tags:                                                                  # 可选的 tag 配置
      - 
    import-values:                                                         # 可选
    alias:                                                                 # 当前 Chart 的别名，主要用在一个 Chart 需要被多次添加的时候
maintainers: # (optional)                                                  # 可选
  - name: The maintainer's name (required for each maintainer)             # 维护者姓名
    email: The maintainer's email (optional for each maintainer)           # 维护者电子邮箱
    url: A URL for the maintainer (optional for each maintainer)           # 维护者个人站点URL
engine: gotpl # The name of the template engine (optional, defaults to gotpl)
icon: A URL to an SVG or PNG image to be used as an icon (optional).       # 一个 SVG 或者 PNG 格式的图标图片 URL（可选）
appVersion: The version of the app that this contains (optional). This needn't be SemVer.  # 可选的应用版本信息，不必是 SemVer 格式（可选）
deprecated: Whether this chart is deprecated (optional, boolean)           # 标记当前 Chart 是否废弃，用 bool 值（可选）
tillerVersion: The version of Tiller that this chart requires. This should be expressed as a SemVer range: ">2.0.0" (optional)
annotations:                                                               # 目前 Helm 已经不允许在 Chart.yaml 中添加额外的配置项，如果需要额外的自定义配置，只能添加在注解中。
  example:                                                                 # 注解列表（可选）
```
每个Chart需要有明确的版本信息，Version 在 kube-prometheus-stack 中的当前值是 51.2.0，对应压缩包名字是 kube-prometheus-stack-51.2.0.tgz，也就是 Chart.yaml 中的Version 字段会被用在 Chart 包的名字中。

这个 Version 的格式是 SemVer 2，[SemVer 的具体定义](https://semver.org/spec/v2.0.0.html)可以直接查阅。SemVer 也就是 Semantic Versioning 的简写，翻译过来就是"语义版本"的意思。平时经常看到的 x.y.z 格式的版本号，也就是 MAJOR.MINOR.PATCH (主版本号.小版本号.补丁版本号)格式，就是 SemVer 版本格式。

apiVersion 字段目前都是配置成 v2 版本，在以前也用过 v1 版本，虽然 Helm3 目前也能识别 v1 版本，但是除非有不好绕过的历史兼容性负担，否则一般都使用 v2 版本。

type 表示这个 Chart 的类型，这里的类型默认是 application，另一个可选值是 library。

kubeVersion 字段用来描述兼容的 Kubernetes 版本信息，这个字段会被 Helm 识别，并且在部署时进行兼容性校验。

- 这里有一些规则需要了解：
    - `>=1.10.0 <1.23.0` 这种记录会被解析成 Kubernetes 版本，需要不小于 1.10.0 且小于 1.23.0。
    - `>=1.10.0 <1.20.0 ||>=1.20.1 <=1.23.0` "或"的含义，可以通过"||"操作符来描述，这种写法表示 Kubernetes 版本在除了 1.20.0 之外的 [1.10.0,1.23.0] 之间。
    - `>=1.10.0 <=1.23.0 !=1.20.0` 上面这种排除 1.20.0 版本的方式可以用更简单的方式来描述，就是这里的 !=。
    - `=、!=、<、>、<=、>=` 这些操作符都可以用。
    - `～1.2.3` 表示补丁版本可以随意选择，也就是 >=1.2.3<=1.3.0 的意思。
    - `^1.2.3` 表示小版本号可以随意选择，也就是 >=1.2.3<=2.0.0 的意思。

- 参考文档
    - [Helm chart指南](https://zhuanlan.zhihu.com/p/463692559)

### 3. Chart依赖管理

一个 Chart 和一个普通的 Go 语言项目一样，绕不开依赖管理的问题。一个 Chart 可以依赖 N个其他 Chart，这些依赖 Chart 可以动态链接到当前 Chart 中，通过定义在 Chart.yaml 中的 dependencies 字段。另外，也可以直接将依赖的 Chart 直接放置到 chart/ 目录下，静态管理这些依赖 Chart。

前面介绍 Chart.yaml 文件时已经提到过 dependencies 字段了，大致含义是这样的：
```yaml
dependencies:            # 当前项目的依赖列表（可选）
  - name:                # 依赖的 Chart 的名字
    version:             # 依赖的 Chart 的版本
    repository:          # 依赖的 Chart 代码库的 URL
    condition:           # 一个可选的 YAML 配置路径，需要是 bool 值，用来表示指定当前 Chart 是否启用
    tags:                # 可选的 tag 配置
      - 
    import-values:       # 可选
    alias:               # 当前 Chart 的别名，主要用在一个 Chart 需要被多次添加的时候
```

这里的 repository 是一个依赖 Chart 的代码库 URL，这个 URL 也是需要通过 `helm repo add` 命令添加到本地 Repository 列表中的，这时同样可以通过 `helm repo add` 命令使用的 NAME 来替换 URL 填入 `dependencies[x].repository` 中。

当 Chart.yaml 中定义好 dependencies 之后，就可以通过 `helm dependency update` 命令将所有的依赖 Chart 下载到本地的 chart/ 目录下。

- helm dependency
    - `helm dependency update CHART [flags]` 根据Chart.yaml文件中的依赖定义更新本地依赖。
    - `helm dependency list CHART [flags]` 列出当前Chart的所有依赖。
    - `helm dependency build CHART [flags]` 从Chart.lock重建本地charts/下的本地依赖。
    - 另外，dependency子命令可以简写为dep，update可以简写为up，list可以简写为ls。
