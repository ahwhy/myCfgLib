# 1 Prometheus Operator简介

## 1.1 Operator

Operator是由CoreOS公司开发的，用来扩展 Kubernetes API，特定的应用程序控制器，它用来创建、配置和管理复杂的有状态应用，如数据库、缓存和监控系统。Operator基于 Kubernetes 的资源和控制器概念之上构建，但同时又包含了应用程序特定的一些专业知识，比如创建一个数据库的Operator，则必须对创建的数据库的各种运维方式非常了解，创建Operator的关键是CRD（自定义资源）的设计。

CRD是对 Kubernetes API 的扩展，Kubernetes 中的每个资源都是一个 API 对象的集合，例如我们在YAML文件里定义的那些spec都是对 Kubernetes 中的资源对象的定义，所有的自定义资源可以跟 Kubernetes 中内建的资源一样使用 kubectl 操作。

Operator是将运维人员对软件操作的知识给代码化，同时利用 Kubernetes 强大的抽象来管理大规模的软件应用。目前CoreOS官方提供了几种Operator的实现，其中就包括本次介绍的主角：Prometheus Operator，Operator的核心实现就是基于 Kubernetes 的以下两个概念：

资源：对象的状态定义

控制器：观测、分析和行动，以调节资源的分布

当然如果有对应的需求也完全可以自己去实现一个Operator，接下来就来基于Odeon使用情况，给大家详细介绍下Prometheus-Operator的部署方法。



## 1.2 Prometheus Operator

首先我们先来了解下Prometheus-Operator的架构图：   ![image-20200806150127591](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20200806150127591.png)

上图是Prometheus-Operator官方提供的架构图，其中Operator是最核心的部分，作为一个控制器，他会去创建Prometheus、ServiceMonitor、AlertManager以及PrometheusRule4个CRD资源对象，然后会一直监控并维持这4个资源对象的状态。

其中创建的prometheus这种资源对象就是作为Prometheus Server存在，而ServiceMonitor就是exporter的各种抽象，exporter是用来提供专门提供metrics数据接口的工具，Prometheus就是通过ServiceMonitor提供的metrics数据接口去 pull 数据的，当然alertmanager这种资源对象就是对应的AlertManager的抽象，而PrometheusRule是用来被Prometheus实例使用的报警规则文件。

这样我们要在集群中监控什么数据，就变成了直接去操作 Kubernetes 集群的资源对象了。上图中的 Service 和 ServiceMonitor 都是 Kubernetes 的资源，一个 ServiceMonitor 可以通过 labelSelector 的方式去匹配一类 Service，Prometheus 也可以通过 labelSelector 去匹配多个ServiceMonitor。



## 1.3 Odeon Kubernetes集群监控情况

Odeon现有的Kubernetes集群监控体系相对完善，其大致情况如下：

\- 使用Prometheus来监控K8s集群及其内运行的服务；

\- 使用Prometheus Operator来集成K8s和Prometheus，一方面其自定义的资源类型和API便于在K8s内做Prometheus的安装、配置，另一方面社区围绕其已经做了很多可以拿来和借鉴的工作；

\- 单K8s集群内需要有完备自治的不依赖于集群外部服务的监控栈，如需要有告警AlertManager、展示Grafana组件；

\- 在各集群（包括各机房的物理机集群、K8s集群）内有各自监控栈的基础上，跨集群、跨DC的监控，可通过Prometheus联邦来实现；各地物理机集群上监控系统需要监控该地K8s集群存活。



# 2. Prometheus Operator的部署

## 2.1 适配kubenetes集群

### 2.1.1部署文件

​      git仓库：https://git.iflytek.com/Odeon/monitor-kubernetes.git

或  直接拷贝包至待部署集群后修改：monitor-kubernetes.tar.gz

### 2.1.2 文件架构

TIPS：

1、篇幅所限，展示部分文件；

2、odeon和ultron文件夹，为基于所属集群适配的部署文件，若有新集群需求，请新建文件夹拷贝配置文件进修改。

```

monitor-kubernetes
├── ingress                         #监控组件自带nginx，无需修改
├── manifests                       #官方文件，需修改少数的环境变量
│  ├── prometheus-operator-alertmanagerCustomResourceDefinition.yaml 
│  ├── prometheus-operator-prometheusCustomResourceDefinition.yaml #CRD资源文件
│  ├── prometheus-operator-prometheusruleCustomResourceDefinition.yaml
│  ├── prometheus-operator-servicemonitorCustomResourceDefinition.yaml
│  ├── alertmanager-alertmanager.yaml 
│  ├── grafana-deployment.yaml 
│  ├── prometheus-prometheus.yaml
│  └── prometheus-rules.yaml        #Prometheus默认监控规则
├── odeon                           #基于Odeon现网集群适配的部署文件
└── ultron                          #基于Ultron集群适配的部署文件，下文以ultron进行介绍
   ├── alarm-sms-configMap.yaml     #告警接收组
   ├── alarm-sms-deployment.yaml
   ├── alarm-sms-service.yaml
   ├── alertmanager-secret.yaml     #告警发送规则
   ├── blackbox-exporter-deployment.yaml
   ├── blackbox-exporter-service.yaml
   ├── drone-cd-clusterRoleBinding.yaml
   ├── drone-cd-clusterRole.yaml
   ├── drone-cd-roleBinding.yaml
   ├── drone-cd-role.yaml
   ├── drone-cd-serviceAccount.yaml
   ├── gpu
   │  ├── gpu-exporter-clusterRoleBinding.yaml
   │  ├── gpu-exporter-clusterRole.yaml
   │  ├── gpu-exporter-daemonset.yaml
   │  ├── gpu-exporter-serviceAccount.yaml
   │  ├── gpu-exporter-serviceMonitor.yaml
   │  └── gpu-exporter-service.yaml
   ├── monitoring-ingress.yaml                    #域名配置文件
   ├── prometheus-additional-rules.yaml           #自定义告警规则
   ├── prometheus-additionalScrapeSecret.yaml
   └── README.md
```

### 2.1.3集群promid

1、根据集群归属，确定集群使用的promid

​		以Ultron上海集群为例，使用的 promid 为 **ultron-sha**

2、修改yaml文件

```
$ vim manifests/prometheus-roleBindingSpecificNamespaces.yaml
$ vim manifests/prometheus-roleSpecificNamespaces.yaml
$ vim manifests/prometheus-prometheus.yaml     #修改项为spec.externalLabels
---config---
  externalLabels:
    promid: ultron-sha
    env: prod-ultron-sha
```

### 2.1.4 域名

1、根据实际需求，确定集群搭建的监控页面访问的域名

​		以Ultron上海集群为例，使用的域名为 **sha-k8s-monitor.ultron.iflytek.com**

2、修改yaml文件：

```
$ vim manifests/prometheus-prometheus.yaml      #修改项为spec.externalUrl
---config---
externalUrl: http://sha-k8s-monitor.ultron.iflytek.com/prometheus                 
 
$ vim manifests/grafana-deployment.yaml         #修改项为spec.template.spec.containers.env
---config---
        env:
          - name: GF_SERVER_ROOT_URL
            value: http://sha-k8s-monitor.ultron.iflytek.com/grafana

$ vim Ultron/monitoring-ingress.yaml            #修改项为spec.rules.host
---config---   
spec: 
  rules:
  - host: sha-k8s-monitor.ultron.iflytek.com
```

3、为域名设置代理，域名 + 集群任意ip + 端口：30980

### 2.1.5 告警组和发送规则

1、根据集群实际维护人员，确定对应告警接收组，组成员和发送规则

2、yaml文件

```
$ vim Ultron/alarm-sms-configMap.yaml   #告警接收组

$ vim Ultron/alertmanager-secret.yaml   #告警发送规则
```

### 2.1.6 监控规则

1、根据集群实际需求，修改或者增加监控规则；

2、yaml文件（PS：以Ultron为例，若有新集群，请新建文件夹，并根据对应格式修改）

```
$ vim manifests/prometheus-rules.yaml  #官方默认监控规则

$ vim ultron/prometheus-additional-rules.yaml      #自定义监控规则

$ vim ultron/prometheus-additionalScrapeSecret.yaml   #自定义监控规则secret
```



## 2.2 部署流程

```
$ kubectl label node Master01 prometheus=k8s-pv-0  
                                                     #将两个Prometheus主容器数据目录通过PV挂载在两个Masters上
$ kubectl label node Master02 prometheus=k8s-pv-1  
                                                    
$ mkdir  /data/prometheus                            #创建挂载的文件夹

$ kubectl apply -f manifests

$ kubectl apply -f ultron

$ sh ingress/apply.sh 
```



## 2.3 部署完成后check

部署完成后，会创建一个名为monitoring的 namespace，所以资源对象对将部署在该命名空间下面，此外 Operator 会自动创建4个 CRD 资源对象：

```
$ kubectl get crd |grep coreos 
 alertmanagers.monitoring.coreos.com      2020-07-23T12:36:50Z
 prometheuses.monitoring.coreos.com      2020-07-23T12:36:50Z
 prometheusrules.monitoring.coreos.com     2020-07-23T12:36:50Z
 servicemonitors.monitoring.coreos.com     2020-07-23T12:36:50Z 
```

可以在 monitoring 命名空间下面查看所有的 Pod，其中 alertmanager 和 prometheus 是用 StatefulSet 控制器管理的，其中还有一个比较核心的 prometheus-operator 的 Pod，用来控制其他资源对象和监听对象变化的（下面只展示了部分Pod）：

```
$ kubectl get pods -n monitoring
NAME                                  READY   STATUS    RESTARTS   AGE
alarm-sms-58bc6b8858-d7vvs            1/1     Running   0          11d
alertmanager-main-0                   2/2     Running   0          11d
alertmanager-main-1                   2/2     Running   0          11d
alertmanager-main-2                   2/2     Running   0          11d
blackbox-exporter-6646f7bf95-7x72x    1/1     Running   0          11d
blackbox-exporter-6646f7bf95-cd8rj    1/1     Running   0          11d
gpu-exporter-2hkm4                    2/2     Running   0          11d
grafana-745b6b567c-wds9g              1/1     Running   0          11d
kube-state-metrics-79c4f984b7-mkhtb   4/4     Running   0          11d
node-exporter-42dcl                   2/2     Running   0          11d
prometheus-adapter-758ddcddf8-6xnxx   1/1     Running   0          11d
prometheus-k8s-0                      3/3     Running   0          11d
prometheus-k8s-1                      3/3     Running   0          11d
prometheus-operator-d64559d96-bbmjn   1/1     Running   0          11d 
```

之前提到过，Prometheus Operator创建了Prometheus、ServiceMonitor、AlertManager以及PrometheusRule 4个CRD资源对象，下面依次展示了其创建的资源对象。

CRD - Prometheus

```
$ kubectl get Prometheus -n monitoring 
   NAME   AGE
   k8s    11d
```

CRD - ServiceMonitor

```
$ kubectl get ServiceMonitor -n monitoring 
   NAME                      AGE
   alertmanager              11d
   coredns                   11d
   gpu-exporter              11d
   grafana                   11d
   kube-apiserver            11d
   kube-controller-manager   11d
   kube-scheduler            11d
   kube-state-metrics        11d
   kubelet                   11d
   node-exporter             11d
   prometheus                11d
   prometheus-operator       11d
```

CRD - AlertManager

```
$ kubectl get AlertManager -n monitoring 
   NAME  AGE
   main  11d
```

 CRD - PrometheusRule

```
$ kubectl get PrometheusRule -n monitoring 
   NAME                          AGE
   prometheus-additional-rules   11d
   prometheus-k8s-rules          11d
```

