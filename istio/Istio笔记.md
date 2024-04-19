# Istio笔记

## 一、基础概念

### 1. 相关概念

软件是当今公司的命脉。随着我们进入一个更加数字化的世界，消费者在与企业交互时期待获得便利的高质量服务，而软件将被用作传递这种体验的媒介。客户不能很好地遵守结构、流程或预定义的框架。客户的需求和需要是流动的、动态的和不可预测的，我们的公司和软件系统也需要具有这些相同的特征。对于有些公司（比如初创公司）来说，能否构建灵活的、能够应对不可预测的市场环境的软件系统，将决定其成败。对于其他公司（比如现有的公司）来说，若不能将软件作为一种区分标准，则将意味着增长放缓、衰落，并最终倒闭。

- 面向服务的架构 SOA
    - SOA是建设企业IT生态系统的架构指导思想中的一种，它把服务视作基本的业务功能单元，由平台中立性的接口契约定义
    - SOA目前的实现方式有两种: 分布式服务化和集中式管理
        - 分布式服务化: 常见的实现有Dubbo、Finagle和ICE等; 
        - 集中式管理: 以ESB为基础支撑技术，较流行的商业实现有WMB (IBM)、OSB (Oracle)，开源实现有Mule、ServiceMix和OpenESB等; 
    - SOA的两大基石
        - RPC: 远程过程调用，是一种通用目的系统通信手段，它把被调用者称为服务提供者(Provider) ，把调用者称为服务消费者(Consumer)，并将对象转换为便于网络传输的二进制或文本数据的过程称为序列化(Serialization)
            - 常见的RPC技术有Cobra、RMI、WebService、JSON-RPC、XML-RPC、Thrift、Protocol Buffer和 gRPC等;
            - 按照调用方式，可分为四种模式:RR(Request-Response)、Oneway(单向调用)、Future(异步)和Callback(回调);
        - MQ: N个系统之间互相通信时，利用MQ可以进行系统间解耦，并借助于失败策略、重试等机 制完成错误处理;
            - 点对点模式
            - 发布订阅模式

- 微服务架构 MSA
    - 微服务中的调用链路较之传统的分布式系统长了很多，于链路上发生故障的概率也必然随之增大，且存在性能损耗，于是，系统规划时必须考虑如何进行雪崩预防、功能降级、超时、重试、熔断、服务隔离等服务管理;
    - 在微服务架构中，服务很小、独立且松散耦合;
    - 每个服务都是一个单独的代码库，可由小型开发团队管理;
    - 服务可以独立部署，团队可以更新现有服务而无需重建和重新部署整个 应用程序;
    - 每个服务负责持久保存自己的数据或外部状态，这与传统模型中使用单 独的数据层处理数据持久性有所不同;
    - 各服务间使用规范定义的API进行相互通信，每个服务隐藏了自身的内部 实施细节;
    - 各服务不需要共享相同的技术堆栈、库或框架，各维护团队完全可以使 用熟悉的技术栈进行程序开发;

- 微服务架构中的进程间通信
    - 微服务构架将应用程序构建为一组服务，这些服务必须经常协作才能处理各种外部请求;而服务实例通常是运行于多台机器上的不同进程，因此必须使用进程间通 信机制进行交互
    - 客户端与服务端的交互方式
        - 一对一
            - 同步模式: 请求/响应
            - 异步模式: 异步请求/响应、单向通知(客户端发出请求但不期望响应)
        - 一对多
            - 异步模式
                - 发布/订阅:客户端发布通知消息，被零个或多个感兴趣者订阅
                - 发布/异步响应:客户端发布请求消息，然后等待从感兴趣的服务发回的响应

- 基于同步远程过程调用的通信
    - 基于同步模式的远程过程调用的通信模型中，无论工作于“阻塞”模式或者是“ 响应式的非阻塞”模式，客户端都假定响应将及时到达
        - REST: 基于HTTP协议的进程间通信机制
            - 优点: 简单、支持请求/响应式通信、易于穿透防火墙等;
            - 缺点: 仅支持请求/响应、客户端必须知道服务实例的位置(URL)，难以在单个请求中获取多个资 源等;
        - gRPC: 二进制的消息协议，客户端与服务端之间使用HTTP/2以protocol buffer的格式 交互二进制消息;
            - 优势
                - 具有高效、紧凑的进程间通信机制;
                - 设计具有复杂更新操作的API非常简单;
                - 支持在远程过程调用和消息传递过程中使用双向流式消息交互; 
                - 实现了客户端和用各种语言编写的服务端之间的互操作性;
            - 弊端
                - 与基于REST/JSON的API机制相比，JavaScript客户端使用基于gRPC的API需要做更多的工作;
                - 同步通信机制，存在局部故障问题;
    - 局部故障风险: 分布式系统中，客户端与服务端是独立的进程，服务端很有可能无法在有限的时间内对客户端的请求作出响应，进而很可能触发多级客户端的连锁 反应导致大面积故障或系统雪崩;
        - 客户端调用服务端时，它应该使用Netflix描述的方法保护自己
        - 网络超时:不要无限期阻塞
        - 限制客户端向服务端发出的请求的数量:充分考虑服务端的承载能力
        - 使用断路器:监控客户端发出请求的成功和失败数量，失败比例超过阈值即启用断路机制，从而让 后续的请求立即失效;经过一定的时长后再继续尝试，并在调用成功后解除断路器;
    - 使用服务发现
        - 微服务实例具有动态分配的网络位置，而且由于动态扩展、故障和升级，服务实例集也 可能会动态修改;
            - 应用层服务发现: 客户端与服务端直接通过服务注册表交互;
            - 平台层服务发现: 通过部署基础设施来处理服务发现，例如kubernetes等;

- 基于异步消息模式的通信
    - 消息由描述正在发送的数据的元数据的消息头，以及数据部分的消息正文组成，并通过消息通道进行交换;
        - 消息类型: 文档(仅包含数据)、命令和事件
        - 消息通道: 点对点、发布/订阅
    - 消息代理
        - 无代理架构: 服务间直接交换消息，ZeroMQ;
        - 基于代理的消息
            - Apache ActiveMQ
            - RabbitMQ
            - Apache Kafka
            - Apache Pulsar
    - 优势: 松耦合、消息缓存、通信灵活
    - 劣势: 潜在的性能瓶颈、单点故障、操作复杂等

### 2. 服务网格中的相关概念

服务网格是一个相对较新的术语，用来描述分布式应用程序网络基础设施，让应用程序安全、有弹性、可观测和可控制。它描述了一个由数据平面和控制平面组成的架构，数据平面使用应用层代理来管理网络流量，控制平面用于管理代理。这种架构使我们能够在应用程序之外构建网络功能，而无须依赖特定的编程语言或框架。

- 什么是服务网格，为什么需要使用服务网格
    - 服务网格可以最大限度地提高整个组织的开发速度，它支持数千个独立的微服务，这些微服务自动支持扩缩容策略
    - 为了将应用程序与基础设施解耦，Istio是朝着这个方向迈出的第三步
    - 第一步，Docker提供了一种将应用程序(及其依赖库)与运行它的机器分开打包的方法
    - 第二步，Kubernetes使创建自动化服务变得很容易，以帮助实现服务自动伸缩和管理
    - Docker和Kubernetes共同推动了微服务的实际改造迁移运动，而通过Istio，则得以实现第三步：应用程序解耦
    - 但是实现服务快速迭代不仅仅是将其与机器分离，服务还必须与共享策略解耦。每个企业都有适用于所有服务的策略，一般情况下这些策略被嵌入服务中，作为代码的一部分，或者作为服务依赖的库。无论怎样，这些策略都很难被更新并重新执行。
    - Istio将大量流量控制策略(主要是涉及API的策略)从应用服务转移到服务网格中，通过部署在服务前的代理来实现。当正确完成这一操作时，所有的服务不需要做额外工作就能满足这些策略，而且更改策略也不需要更新应用服务。这就是我们追求的解耦。

- 转移到，面向服务的架构(SOA)时，必须要解决的问题：
    - 防止故障超出隔离边界。
    - 构建能够响应环境变化的应用程序/服务。
    - 建立能够在部分失效条件下运行的系统。
    - 理解整个系统在不断变化和发展时发生了什么。
    - 无法控制系统的运行时行为。
    - 随着攻击面的增加，加强安全防护。
    - 降低系统变更产生的风险。
    - 执行关于谁、什么东西可以使用系统组件，以及何时可以使用系统组件的策略。

- 有些模式已经发展完善，可以缓解应用程序的这类问题，使应用程序更有弹性，以应对计划外的、意想不到的故障：
    - 客户端负载均衡——为客户端提供可能的端点列表，并让它决定调用哪一个。
    - 服务发现——一种用于查找特定逻辑服务端点列表的机制，这些端点是健康的且定期更新。
    - 熔断——在一段时间内对表现异常的服务进行屏蔽。
    - bulkheading——在调用服务时，使用显式的阈值（连接、线程、会话等）限制客户端资源的使用。
    - 超时——在调用服务时，对Request、Socket、Liveness等执行时间限制。
    - 重试——重试失败的请求。
    - 重试限制——对重试的次数进行限制：限制在给定的时间段内重试的次数（例如，在10s的窗口内，只有50%的请求重试）。
    - 最后期限——给出请求上下文，说明一个响应可以持续多久；如果超过了最后期限，就不再处理请求。
    - 总的来说，这些类型的模式可以被认为是应用程序网络。它们与网络栈较低层的类似结构有很多重叠之处，只不过它们是在消息层而不是在包层操作的。

- Istio控制面的功能
    - 为运维人员指定所需路由/弹性行为的API
    - 让数据平面使用其配置的API
    - 数据平面服务发现的抽象
    - 用于指定使用策略的API
    - 证书的颁发和轮换
    - 分配工作负载标识
    - 统一遥测采集
    - 配置sidecar注入
    - 网络边界的规范，以及如何访问它们

- 常用链接
    - [服务网格 Istio](https://istio.io)
    - [academy](https://academy.tetrate.io/)
    - [EBook istio-in-action](https://livebook.manning.com/book/istio-in-action)
    - [Manning 网站](https://www.manning.com)
    - [book-source-code](https://github.com/istioinaction/book-source-code)
    - Twitter创建了[Finagle](https://twitter.github.io/finagle)，这是一个Scala库，其所有的微服务都嵌入其中。它处理负载均衡、断路、自动重试、遥测等。
    - Netflix开发了[Hystrix](https://github.com/Netflix/Hystrix)，这是一个类似的Java应用库。
    - [Istio - Supported Kubernetes Versions ](https://istio.io/latest/docs/releases/supported-releases/#support-status-of-istio-releases)


## 二、网格的基础操作

### 1. 网格的安装
```shell
# 下载安装包
$ curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.4 TARGET_ARCH=x86_64 sh -

$ ./bin/istioctl version
no ready Istio pods in "istio-system"
1.20.4

# 确认集群是否满足网格安装
$ istioctl x precheck
✔ No issues found when checking the cluster. Istio is safe to install or upgrade!
  To get started, check out https://istio.io/latest/docs/setup/getting-started/

# 安装demo版本
$ istioctl install --set profile=demo -y
✔ Istio core installed
✔ Istiod installed
✔ Egress gateways installed
✔ Ingress gateways installed
✔ Installation complete                                                                                                                                                                                     Made this installation the default for injection and validation.

$ kubectl -n istio-system get pod
NAME                                    READY   STATUS    RESTARTS   AGE
istio-egressgateway-78bc76c8d4-sq6lw    1/1     Running   0          4m18s
istio-ingressgateway-6dcb6668bb-88fxw   1/1     Running   0          4m18s
istiod-65c86cbd5-7b6bb                  1/1     Running   0          4m32s

# 验证网格安装是否完成
$  istioctl verify-install 
1 Istio control planes detected, checking --revision "default" only
✔ ClusterRole: istiod-clusterrole-istio-system.istio-system checked successfully
✔ ClusterRole: istiod-gateway-controller-istio-system.istio-system checked successfully
✔ ClusterRoleBinding: istiod-clusterrole-istio-system.istio-system checked successfully
✔ ClusterRoleBinding: istiod-gateway-controller-istio-system.istio-system checked successfully
✔ ConfigMap: istio.istio-system checked successfully
✔ Deployment: istiod.istio-system checked successfully
✔ ConfigMap: istio-sidecar-injector.istio-system checked successfully
✔ MutatingWebhookConfiguration: istio-sidecar-injector.istio-system checked successfully
✔ PodDisruptionBudget: istiod.istio-system checked successfully
✔ ClusterRole: istio-reader-clusterrole-istio-system.istio-system checked successfully
✔ ClusterRoleBinding: istio-reader-clusterrole-istio-system.istio-system checked successfully
✔ Role: istiod.istio-system checked successfully
✔ RoleBinding: istiod.istio-system checked successfully
✔ Service: istiod.istio-system checked successfully
✔ ServiceAccount: istiod.istio-system checked successfully
✔ ValidatingWebhookConfiguration: istio-validator-istio-system.istio-system checked successfully
✔ Deployment: istio-ingressgateway.istio-system checked successfully
✔ PodDisruptionBudget: istio-ingressgateway.istio-system checked successfully
✔ Role: istio-ingressgateway-sds.istio-system checked successfully
✔ RoleBinding: istio-ingressgateway-sds.istio-system checked successfully
✔ Service: istio-ingressgateway.istio-system checked successfully
✔ ServiceAccount: istio-ingressgateway-service-account.istio-system checked successfully
✔ Deployment: istio-egressgateway.istio-system checked successfully
✔ PodDisruptionBudget: istio-egressgateway.istio-system checked successfully
✔ Role: istio-egressgateway-sds.istio-system checked successfully
✔ RoleBinding: istio-egressgateway-sds.istio-system checked successfully
✔ Service: istio-egressgateway.istio-system checked successfully
✔ ServiceAccount: istio-egressgateway-service-account.istio-system checked successfully
✔ ServiceAccount: istio-reader-service-account.istio-system checked successfully
✔ CustomResourceDefinition: wasmplugins.extensions.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: destinationrules.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: envoyfilters.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: gateways.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: proxyconfigs.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: serviceentries.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: sidecars.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: virtualservices.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: workloadentries.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: workloadgroups.networking.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: authorizationpolicies.security.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: peerauthentications.security.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: requestauthentications.security.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: telemetries.telemetry.istio.io.istio-system checked successfully
✔ CustomResourceDefinition: istiooperators.install.istio.io.istio-system checked successfully
Checked 15 custom resource definitions
Checked 3 Istio Deployments
✔ Istio is installed and verified successfully

# 查看网格版本
$ istioctl version
client version: 1.20.4
control plane version: 1.20.4
data plane version: 1.20.4 (2 proxies)

# 安装控制平面的支持组件
$ kubectl apply -f ./samples/addons/
serviceaccount/grafana created
configmap/grafana created
service/grafana created
deployment.apps/grafana created
configmap/istio-grafana-dashboards created
configmap/istio-services-grafana-dashboards created
deployment.apps/jaeger created
service/tracing created
service/zipkin created
service/jaeger-collector created
serviceaccount/kiali created
configmap/kiali created
clusterrole.rbac.authorization.k8s.io/kiali-viewer created
clusterrole.rbac.authorization.k8s.io/kiali created
clusterrolebinding.rbac.authorization.k8s.io/kiali created
role.rbac.authorization.k8s.io/kiali-controlplane created
rolebinding.rbac.authorization.k8s.io/kiali-controlplane created
service/kiali created
deployment.apps/kiali created
serviceaccount/loki created
configmap/loki created
configmap/loki-runtime created
service/loki-memberlist created
service/loki-headless created
service/loki created
statefulset.apps/loki created
serviceaccount/prometheus created
configmap/prometheus created
clusterrole.rbac.authorization.k8s.io/prometheus created
clusterrolebinding.rbac.authorization.k8s.io/prometheus created
service/prometheus created
deployment.apps/prometheus created

$ kubectl -n istio-system get pod
NAME                                    READY   STATUS    RESTARTS   AGE
grafana-7bd5db55c4-fqrd7                1/1     Running   0          65s     # 可视化由代理生成并由 Promethues收集的指标
istio-egressgateway-78bc76c8d4-sq6lw    1/1     Running   0          19m
istio-ingressgateway-6dcb6668bb-88fxw   1/1     Running   0          19m
istiod-65c86cbd5-7b6bb                  1/1     Running   0          19m
jaeger-78756f7d48-jfml9                 1/1     Running   0          65s     # 分布式追踪系统，通过服务网格对请求流进行可视化
kiali-55bfd5c754-s54tx                  1/1     Running   0          65s     # 服务网格的Web控制台
prometheus-67f6764db9-dcm7j             2/2     Running   0          64s     # 收集生成的指标并将其存储为时序数据

# 开启sidecar注入
$ kubectl label namespace default istio-injection=enabled

$ istioctl proxy-config routes deploy/istio-ingressgateway.istio-system
NAME     VHOST NAME     DOMAINS     MATCH                  VIRTUAL SERVICE
         backend        *           /stats/prometheus*
         backend        *           /healthz/ready*

$ kubectl -n istio-system port-forward svc/grafana 3000
$ kubectl -n istio-system port-forward svc/kiali 20001

$ istioctl dashboard grafana
$ istioctl dashboard jaeger

$ istioctl analyze
✔ No validation issues found when analyzing namespace: default.
```

### 2. 入门案例

#### Bookinfo

Istio的入门案例中，有个经典的BookInfo的案例。通过`kubectl apply -f ./bookinfo`命令，安装下[bookinfo的系列资源](./BookInfo/)。

[BookInfo yaml](https://github.com/istio/istio/blob/master/samples/bookinfo/platform/kube/bookinfo.yaml)

#### Httpbin

httpbin是一个用于测试的开源应用，常用于Web调试。部署[该应用](./httpbin/)后，可以方便地查看HTTP请求的Method、Header和授权等信息。

执行以下命令，访问httpbin的/status/200。

```shell
$ kubectl apply -f httpbin
gateway.networking.istio.io/httpbin created
virtualservice.networking.istio.io/httpbin-vs created
serviceaccount/httpbin created
service/httpbin created
deployment.apps/httpbin created

# curl http://${网关IP}/status/200 -v
# curl http://${网关IP}/status/418 -v
# curl http://${网关IP}/status/403 -v
# curl http://${网关IP}/headers -H test-header:test-value  -v
$ curl http://2x.x.x.x:80/headers -H test-header:test-value  -v
*   Trying 2x.x.x.x:80...
* Connected to 2x.x.x.x (2x.x.x.x) port 443 (#0)
> GET /headers HTTP/1.1
> Host: 2x.x.x.x:80
> User-Agent: curl/7.86.0
> Accept: */*
> test-header:test-value
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 200 OK
< server: istio-envoy
< date: Thu, 28 Mar 2024 07:45:40 GMT
< content-type: application/json
< content-length: 649
< access-control-allow-origin: *
< access-control-allow-credentials: true
< x-envoy-upstream-service-time: 5
<
{
  "headers": {
    "Accept": "*/*",
    "Host": "2x.x.x.x:80",
    "Test-Header": "test-value",
    "User-Agent": "curl/7.86.0",
    "X-B3-Parentspanid": "332acd102be11a04",
    "X-B3-Sampled": "1",
    "X-B3-Spanid": "9123e3081ef8321e",
    "X-B3-Traceid": "25a8096b170aec15332acd102be11a04",
    "X-Envoy-Attempt-Count": "1",
    "X-Envoy-External-Address": "140.205.11.230",
    "X-Forwarded-Client-Cert": "By=spiffe://cluster.local/ns/default/sa/httpbin;Hash=f24ddfc1afc2cd85f4c987ec50ae3385ce5fc07f3235d4bf6983b6680a21c848;Subject=\"\";URI=spiffe://cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"
  }
}
* Connection #0 to host 2x.x.x.x left intact
```


## 三、Envoy

### 1. 什么是Envoy

Envoy是C++编写的，并以Bazel为构建系统。被设计为通过应用程序的进程外运行来避免开发人员受到网络问题的影响。这意味着用任何编程语言或用任何框架编写的任何应用程序都可以利用这些特性。此外，尽管服务架构（SOA、微服务等）是目前流行的架构，但Envoy并不关心是微服务，还是用任何语言编写的单体应用程序，只要它们使用的是Envoy能够理解的协议（如HTTP），Envoy就可以提供价值。

Envoy是一个非常通用的代理，可以扮演不同的角色：作为集群边缘的代理（作为一个入口点），或者作为单个主机或服务组的共享代理，甚至作为我们在Istio中看到的每个服务的代理。通过Istio，每个服务实例都部署一个Envoy代理，以实现最大的灵活性、最佳性能和控制。你使用了一种部署模式（sidecar服务代理），并不意味着你不能使用Envoy提供的优势。事实上，让代理在边缘和应用程序中具有相同的实现，可以使基础设施更容易操作和理解。所以，Envoy可以被部署在集群边缘作为流量入口，也可以被部署在集群内组成服务网格，以充分控制和观察流量的完整调用链路。

Envoy在传递通信方向性时使用的术语与其他代理类似。例如，流量从下游系统进入监听器。该流量被路由到Envoy的一个集群，该集群负责将该流量发送到上游系统。流量从下游经过Envoy流向上游。

- [请求通过监听器从下游系统进入，然后经过路由规则，最后到达集群，该集群将其发送到上游服务](./images/请求通过监听器从下游系统进入，然后经过路由规则，最后到达集群，该集群将其发送到上游服务.jpg)

- Envoy的核心功能
    - 集群(Cluster): 集群是Envoy连接到的一组逻辑上相似的端点;在v2中，RDS通过路由指向集群，CDS提供集群配置，而Envoy通过EDS发现集群成员，即端点;
    - 下游(Downstream): 下游主机连接到Envoy，发送请求并接收响应，它们是Envoy的客户端;
    - 上游(Upstream): 上游主机接收来自Envoy的连接和请求并返回响应，它们是Envoy代理的后端服务器;
    - 端点(Endpoint): 端点即上游主机，是一个或多个集群的成员，可通过EDS发现;
    - 侦听器(Listener): 侦听器是能够由下游客户端连接的命名网络位置，例如端口或unix域套接字等;例如，80端口上的监听器接收流量，并将任何配置的行为应用于该流量;
    - 路由(Route): 如何处理进入监听器的流量的路由规则。例如，如果传入一个请求并匹配/catalog，则将该流量定向到catalog集群。
    - 位置(Locality): 上游端点运行的区域拓扑，包括地域、区域和子区域等;
    - 管理服务器(Management Server): 实现v2 API的服务器，它支持复制和分片，并且能够在不同的物理机器上实现针对不同xDS API的API服务;
    - 地域(Region): 区域所属地理位置;
    - 区域(Zone): AWS中的可用区(AZ)或GCP中的区域等;
    - 子区域: Envoy实例或端点运行的区域内的位置，用于支持区域内的多个负载均衡目标;
    - xDS:CDS 、EDS、HDS 、LDS、RLS(Rate Limit)、RDS 、SDS、VHDS和RTDS等API的统称


- 性能: 除了大量功能外，Envoy还提供极高的吞吐量和低尾延迟差异，同时消耗相对较少的CPU和RAM;

- 可扩展性: Envoy在L4和L7上提供丰富的可插拔过滤器功能，允许用户轻松添加新功能;

- API可配置性:Envoy提供了一组可由控制平面服务实现的管理API，也称为xDS API
    - 若控制平面实现了这所有的API，则可以使用通用引导配置在整个基础架构中运行Envoy
    - 所有进一步的配置更改都可通过管理服务器无缝地进行动态传递，使得Envoy永远不需要重新启动
    - 于是，这使得Envoy成为一个通用数据平面，当与足够复杂的控制平面相结合时，可大大降低整体操作复杂性


### 2. Envoy的功能特性

#### 服务发现

与使用特定于运行时的库来进行客户端服务发现不同，Envoy可以为应用程序自动完成此任务。通过配置Envoy从一个简单的发现API中查找服务端点，应用程序可以不知道如何找到服务端点。发现API（Discovery API）是一个简单的REST API，可用于包装其他常见的服务发现API（如HashiCorp Consul、Apache ZooKeeper、Netflix Eureka等）。Istio的控制平面实现了这个开箱即用的API。

Envoy是一个很好的构建模块的原因之一是它支持通过gRPC/REST API进行动态配置。
Envoy之前的开源代理不是为Kubernetes这样的动态环境设计的。它们使用静态的配置文件，需要重新启动才能使配置变化生效。
另外，Envoy提供xDS（*发现服务）API，用于动态配置。它还支持热重启，这使得Envoy可以在不放弃任何活动连接的情况下重新初始化。

Envoy xDS API存在多个版本
    - v1 API 仅使用 JSON/REST，本质上是轮询
    - v2 API 是 v1 的演进，而不是革命，它是 v1 功能的超集，新的API模式使用 proto3 指定，并同时以 gRPC 和 REST + JSON/YAML 端点实现
    - v1，v2 已经不再支持，v3 xDS API是今后主要最终的主要版本，将永远受到支持。
    - [api_supported_versions](https://www.envoyproxy.io/docs/envoy/latest/api/api_supported_versions)

Envoy支持通过XDS API进行动态配置。Envoy连接到配置服务器，并使用LDS、RDS、EDS、CDS和其他XDS API请求其配置
Envoy的xDS是一个API集合，包括监听器发现服务（LDS）、集群发现服务（CDS）、端点发现服务（EDS）、路由发现服务（RDS）等。
Envoy配置服务器实现这些API，并作为Envoy的动态配置源。在启动过程中，Envoy会与配置服务器通信（通常是通过gRPC）并订阅配置变化。当环境发生变化时，配置服务器会将变化流向Envoy。

Envoy是专门构建的，依赖对服务发现目录的最终一致性更新。这意味着在分布式系统中，我们不能期望知道可以通信的所有服务的确切状态，以及它们是否可用。我们能做的最好的事情是利用手头的知识，主动和被动地进行健康检查，并且不期望结果可能是最新的（它们也不可能是最新的）。
Istio通过提供驱动Envoy的服务发现机制配置的高级资源集，抽象出了很多这样的细节。

#### 负载均衡

Envoy实现了一些应用程序可以利用的高级负载均衡算法，例如位置感知负载均衡。此时，Envoy足够聪明，可以阻止任何位置边界的流量，除非它符合某些标准，并将提供更好的流量负载均衡。例如，除非造成故障，否则Envoy会确保将服务间流量路由到同一位置的实例。

Envoy为以下策略提供了开箱即用的负载均衡算法：
    - 随机
    - 轮询
    - 权重，最小请求数
    - 一致性哈希

#### 流量和请求路由

因为Envoy可以解析像HTTP/1.1和HTTP/2这样的应用程序协议，所以它可以使用复杂的路由规则将流量定向到特定的后端集群。Envoy可以执行基本的反向代理路由，如虚拟主机和上下文路径匹配路由；还可以执行基于头和优先级的路由、路由的重试和超时，以及故障注入。

#### 流量转移和镜像特性

Envoy支持基于百分比（即权重）的流量分割/转移，这使得敏捷团队能够使用持续交付技术来降低风险，比如金丝雀发布。尽管这样可以将风险影响范围缩减到最小，但金丝雀发布仍然要处理实时用户流量。
Envoy也可以复制流量，将流量镜像到另一个Envoy集群。可以将这种镜像功能看作类似于流量分割的东西，但上游集群看到的请求是实时流量的副本；因此，我们可以将被镜像的流量路由到一个服务的新版本，而不需要真正地对实时生产流量进行操作。这是一个非常强大的功能，可以在不影响客户的情况下使用生产流量测试服务变更。

#### 网络弹性

Envoy可以用来解决某些类型的弹性问题，但请注意，调整和配置参数是应用程序的责任。一方面，Envoy可以自动执行请求超时和请求级重试（每次重试超时）。当请求经历间歇性的网络不稳定时，这种类型的重试行为非常有用。另一方面，重试放大可能导致级联失败，Envoy允许限制重试行为。还要注意，我们可能仍然需要应用程序级重试，并且不能完全将重试任务交给Envoy。此外，当Envoy调用上游集群时，可以为它配置bulkheading特性，比如限制正在运行的连接或未完成的请求的数量，并快速处理所有超过这些阈值的请求（在这些阈值上有些抖动）。最后，Envoy可以执行异常点检测，它的行为类似于熔断器，当节点行为不符合预期时，将其从负载均衡池中弹出。

#### HTTP/2和gRPC

HTTP/2是对HTTP协议的一个重大改进，它允许在单个连接上复用请求、服务端推送交互、流交互和请求反压力。Envoy从一开始就被构建为一个HTTP/1.1和HTTP/2代理，为下游和上游的每个协议提供代理功能。也就是说，Envoy可以接受HTTP/1.1连接并转为HTTP/2请求——反之亦然——或者代理传入的HTTP/2请求到上游HTTP/2集群。gRPC是一个使用Google Protocol Buffers（Protobuf）的RPC协议，它位于HTTP/2之上，同时也得到了Envoy的天然支持。这些都是强大的特性（在实现中很难得到正确的实现），并将Envoy与其他服务代理区分开来。

#### 可观测性之指标收集

Envoy的目标之一就是帮助人们理解网络。Envoy收集了大量的指标来实现这一目标。它追踪调用它的下游系统、服务器本身，以及向其发送请求的上游集群的多维指标。Envoy的统计数据以计数器、量表或直方图的形式进行追踪。

Envoy可以使用可配置的适配器和格式发送统计数据。Envoy支持以下功能，开箱即用：
    - StatsD
    - Datadog;DogStatsD
    - Hystrix格式化
    - 通用指标服务

#### 可观测性之分布式调用链路追踪

Envoy可以向OpenTracing引擎报告追踪的span，以可视化调用链路中的流量、跳转和延迟。这意味着不必安装特殊的OpenTracing库。此外，应用程序负责传播必要的Zipkin头文件，这可以通过薄包装器库来完成。

Envoy生成一个x-request-id头来关联跨服务的调用，还可以在触发追踪时生成初始的x-b3*头。应用程序负责传播的头信息如下：
    - x-b3-traceid
    - x-b3-spanid
    - x-b3-parentspanid
    - x-b3-sampled
    - x-b3-flags

#### 自动终止和发起TLS

Envoy可以在集群的边缘和服务代理网格的深处终止以特定服务为目的地的传输层安全（Transport Level Security，TLS）流量。一个更有趣的功能是，Envoy可以用来代表应用程序向上游集群发起TLS流量。对于企业开发人员和运维人员来说，这意味着我们不必处理特定于语言的设置和密钥库或信任库。只要在请求路径中有Envoy，我们就可以自动获得TLS，甚至双向TLS。

#### 限流

弹性的一个重要方面是能够限制对受保护资源的访问。诸如数据库、缓存或共享服务这样的资源可能会因为各种原因而受到保护：
    - 调用开销很大（每次调用的开销）。
    - 缓慢或不可预测的延迟。
    - 保护免受饥饿的公平算法。

特别是当服务被配置为重试时，我们不希望放大系统中某些故障的影响。为了帮助控制这些场景中的请求，我们可以使用全局限流服务。Envoy可以在网络（每个连接）和HTTP（每个请求）级别上与限流服务集成。我们将在第14章中展示如何做到这一点。

#### Envoy扩展

Envoy的核心是一个字节处理引擎，可以在其上构建协议（第7层）编解码器（称为过滤器）。Envoy使构建额外的过滤器成为一级用例，并且是为特定用例扩展Envoy的一种令人兴奋的方式。Envoy过滤器是用C++编写的，并编译成Envoy二进制文件。此外，Envoy还支持Lua脚本和WebAssembly（Wasm），以一种侵入性更小的方式扩展Envoy的功能。


### 3. Envoy的配置方式

Envoy的架构支持非常灵活的配置方式: 简单部署场景可以使用纯静态配置，而更复杂的部署场景则可以逐步添加需要的动态配置机制;
    - 纯静态配置: 用户自行提供侦听器、过滤器链、集群及HTTP路由(http代理场景)，上游端点的发现仅可通过DNS服务进行，且配置的重新加载必须通过内置的热重启(hot restart)完成;
    - 仅使用EDS: EDS提供的端点发现功能可有效规避DNS的限制(响应中的最大记录数等 );
    - 使用EDS和CDS: CDS能够让Envoy以优雅的方式添加、更新和删除上游集群，于是，初始配置时，Envoy无须事先了解所有上游集群;
    - EDS、CDS和RDS: 动态发现路由配置;RDS与EDS、CDS一起使用时，为用户提供了构建复杂路由拓扑的能力(流量转移、蓝/绿部署等);
    - EDS、CDS、RDS和LDS: 动态发现侦听器配置，包括内嵌的过滤器链;启用此四种发现服务后，除了较罕见的配置变动、证书轮替或更新Envoy程序之外，几乎无须再热重启 Envoy;
    - EDS、CDS、RDS、LDS和SDS: 动态发现侦听器密钥相关的证书、私钥及TLS会话票据，以及对证书验证逻辑的配置(受信任的根证书和撤销机制等);

关于动态配置，Envoy可以使用一组API来执行内联配置更新，而无须重启。它只需要一个简单的引导配置文件，将配置指向正确的发现服务API；其余都是动态配置的。Envoy使用以下API进行动态配置：
    - LDS（Listener Discovery Service）——允许Envoy查询应该在该代理上公开哪些监听器的API。
    - RDS（Route Discovery Service）——监听器配置的一部分，指定使用哪些路由。这是LDS的一个子集，用于确定应该使用静态配置还是动态配置。
    - CDS（Cluster Discovery Service）——这个API允许Envoy发现该代理应该拥有哪些集群以及每个集群各自的配置。
    - EDS（Endpoint Discovery Service）——集群配置的一部分，指定用于特定集群的端点。这是CDS的一个子集。
    - SDS（Secret Discovery Service）——用于分发证书的API。
    - ADS（Aggregate Discovery Service）——对其他API的所有更改的序列化流。你可以使用这个API按顺序获取所有更改。

这些API被统称为xDS服务。配置时可以使用其中一种或几种组合；不需要把它们都用上。注意，Envoy的xDS API是建立在最终一致性的前提下的，正确的配置最终会收敛。例如，Envoy可以通过一个新路由来更新RDS，该路由将流量路由到一个还没有在CDS中更新的foo集群。在CDS更新之前，该路由可能会引入路由错误。Envoy引入了ADS来解释这个竞争条件，Istio为代理配置的更改实现ADS。

```yaml
# https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/configuration-static#configuration-static
static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 10000
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          access_log:
          - name: envoy.access_loggers.stdout
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
          http_filters:
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
          route_config:
            name: local_route
            virtual_hosts:
            - name: local_service
              domains: ["*"]
              routes:
              - match:
                  prefix: "/"
                route:
                  host_rewrite_literal: www.envoyproxy.io
                  cluster: service_envoyproxy_io
  clusters:
  - name: service_envoyproxy_io
    type: LOGICAL_DNS
    # Comment out the following line to test on v6 networks
    dns_lookup_family: V4_ONLY
    load_assignment:
      cluster_name: service_envoyproxy_io
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: www.envoyproxy.io
                port_value: 443
    transport_socket:
      name: envoy.transport_sockets.tls
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
        sni: www.envoyproxy.io

# https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/configuration-dynamic-filesystem
node:
  cluster: test-cluster
  id: test-id

dynamic_resources:
  cds_config:
    resource_api_version: V3
    path: /var/lib/envoy/cds.yaml
  lds_config:
    resource_api_version: V3
    path: /var/lib/envoy/lds.yaml

# /var/lib/envoy/lds.yaml
resources:
- "@type": type.googleapis.com/envoy.config.listener.v3.Listener
  name: listener_0
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 10000
  filter_chains:
  - filters:
    - name: envoy.http_connection_manager
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
        stat_prefix: ingress_http
        http_filters:
        - name: envoy.router
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
        route_config:
          name: local_route
          virtual_hosts:
          - name: local_service
            domains:
            - "*"
            routes:
            - match:
                prefix: "/"
              route:
                host_rewrite_literal: www.envoyproxy.io
                cluster: example_proxy_cluster

# /var/lib/envoy/cds.yaml
resources:
- "@type": type.googleapis.com/envoy.config.cluster.v3.Cluster
  name: example_proxy_cluster
  type: STRICT_DNS
  typed_extension_protocol_options:
    envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
      "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
      explicit_http_config:
        http2_protocol_options: {}
  load_assignment:
    cluster_name: example_proxy_cluster
    endpoints:
    - lb_endpoints:
      - endpoint:
          address:
            socket_address:
              address: www.envoyproxy.io
              port_value: 443
  transport_socket:
    name: envoy.transport_sockets.tls
    typed_config:
      "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
      sni: www.envoyproxy.io

# https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/configuration-dynamic-control-plane
node:
  cluster: test-cluster
  id: test-id

dynamic_resources:
  ads_config:
    api_type: GRPC
    transport_api_version: V3
    grpc_services:
    - envoy_grpc:
        cluster_name: xds_cluster
  cds_config:
    resource_api_version: V3
    ads: {}
  lds_config:
    resource_api_version: V3
    ads: {}

static_resources:
  clusters:
  - type: STRICT_DNS
    typed_extension_protocol_options:
      envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
        "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
        explicit_http_config:
          http2_protocol_options: {}
    name: xds_cluster
    load_assignment:
      cluster_name: xds_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: my-control-plane
                port_value: 18000

# Bootstrap (proto)
{
  "node": {...},
  "static_resources": {...},
  "dynamic_resources": {...},
  "cluster_manager": {...},
  "hds_config": {...},
  "flags_path": ...,
  "stats_sinks": [],
  "deferred_stat_options": {...},
  "stats_config": {...},
  "stats_flush_interval": {...},
  "stats_flush_on_admin": ...,
  "watchdog": {...},
  "watchdogs": {...},
  "tracing": {...},
  "layered_runtime": {...},
  "admin": {...},
  "overload_manager": {...},
  "enable_dispatcher_stats": ...,
  "header_prefix": ...,
  "stats_server_version_override": {...},
  "use_tcp_for_dns_lookups": ...,
  "dns_resolution_config": {...},
  "typed_dns_resolver_config": {...},
  "bootstrap_extensions": [],
  "fatal_actions": [],
  "default_socket_interface": ...,
  "inline_headers": [],
  "perf_tracing_file_path": ...,
  "default_regex_engine": {...},
  "xds_config_tracker_extension": {...},
  "application_log_config": {...},
  "grpc_async_client_manager_config": {...}
}
```

### 4. Envoy的工作方式

Envoy使用单进程/多线程的架构模型，一个主线程(Main thread)负责实现各类管理任务，而一些工作线程(Worker threads)则负责执行监听、过滤和转发 等代理服务器的核心功能
    - 主线程: 负责Envoy程序的启动和关闭、xDS API调用处理(包括DNS、健康状态检测和集群管理等)、运行时 配置、统计数据刷新、管理接口维护和其它线程管理(信号和热重启等)等，相关的所有事件均以异步非阻塞 模式完成;
    - 工作线程: 默认情况下，Envoy根据当前主机CPU核心数来创建等同数量的工作线程，不过，管理员也可以通过程序选项--concurrency具体指定; 每个工作线程运行一个非阻塞型事件循环，负责为每个侦听器监听指定的套接字、接收新请求、为每个连接初始一个过滤器栈并处理此连接整个生命周期中的所有事件;
    - 文件刷写线程: Envoy写入的每个文件都有一个专用、独立的阻塞型刷写线程，当工作线程需要写入文件时，数据实际上被移入内存缓冲区，最终通过文件刷写线程同步至文件中

Envoy通过侦听器监听套接字并接收客户端请求，而Envoy的所有工作线程会同时共同监听用户配置的所有套接字，对于某次连接请求，由内核负责将其派发至某个具体的工作线程处理; 随后，相关的工作线程基于特定的处理逻辑分别由相关组件依次完成连接管理;

- [Envoy连接处理](./images/Envoy连接处理.png)

- 常用链接
    - [Envoy代理](https://www.envoyproxy.io)
    - [Envoy被用于Ingress控制器 Contour](https://projectcontour.io)
    - [API网关 Amb-assador](https://www.getambassador.io)
    - [Gloo](https://docs.solo.io/gloo/)
    - [OSM](https://github.com/openservicemesh/osm)


## 四、Istio

- 特性
  - 入口网关对进入服务网格的流量提供细粒度控制。
  - 使用Gateway资源，我们可以为特定的主机配置允许进入网格的流量类型。
  - 就像网格中的任何服务一样，网关使用VirtualService资源路由流量。
  - 每台主机单独配置支持以下TLS模式：
    - 使用SIMPLE TLS模式加密和防止中间人攻击。
    - 使用MUTUAL TLS模式双向验证服务器和客户端。
    - 使用带有PASSTHROUGH TLS模式的SNI头允许反向代理加密流量。
  - 对于目前不支持的L7协议，Istio支持纯TCP流量。但纯TCP流量不具备高级特性，例如重试、复杂的路由等。

### 1. Gateway

- Gateway pod里的进程，pilot-agent进程会对Envoy代理进行初始化
```shell
$ kubectl -n istio-system exec -it istio-ingressgateway-6dcb6668bb-88fxw bash
kubectl exec [POD] [COMMAND] is DEPRECATED and will be removed in a future version. Use kubectl exec [POD] -- [COMMAND] instead.
istio-proxy@istio-ingressgateway-6dcb6668bb-88fxw:/$ ps -ef
UID          PID    PPID  C STIME TTY          TIME CM
istio-p+       1       0  0 Mar26 ?        00:12:18 /usr/local/bin/pilot-agent proxy router --domain istio-system.svc.cluster.local --proxyLogLevel=warning --proxyComponentLogLevel=misc:error --log_output
istio-p+      16       1  0 Mar26 ?        01:08:35 /usr/local/bin/envoy -c etc/istio/proxy/envoy-rev.json --drain-time-s 45 --drain-strategy immediate --local-address-ip-version v4 --file-flush-interval-
istio-p+      40       0  0 11:55 pts/0    00:00:00 bash
istio-p+      48      40  0 11:55 pts/0    00:00:00 ps -ef
```

- Gateway yaml
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: test-gateway
  namespace: default
spec:
  selector:
    istio: ingressgateway     # 具体的网关实现
  servers:
  - port:
      number: 80              # 暴露的端口
      name: http
      protocol: HTTP
    hosts:
    - "*.bookinfo.com"        # 端口对应的主机
    tls:
      httpsRedirect: true     # sends 302 redirect for http requests 重定向 HTTP 到 HTTPS
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*.bookinfo.com"
    tls:
      mode: SIMPLE
      serverCertificate: /etc/certs/servercert.pem
      privateKey: /etc/certs/privatekey.pem
```

- 查看生成的网格规则
```shell
$ istioctl -n istio-system proxy-config listener deploy/istio-ingressgateway
ADDRESSES PORT  MATCH DESTINATION
0.0.0.0   8080  ALL   Route: http.8080
0.0.0.0   8443  ALL   Route: http.8443
0.0.0.0   15021 ALL   Inline Route: /healthz/ready*
0.0.0.0   15090 ALL   Inline Route: /stats/prometheus*

$ istioctl -n istio-system proxy-config route deploy/istio-ingressgateway -o json --name http.8080
[
    {
        "name": "http.8080",  # istio-ingressgateway 默认监听8080
        "virtualHosts": [
            {
                "name": "*:80",
                "domains": [
                    "*"
                ],
                "routes": [
                    ...
                ],
                "includeRequestAttemptCount": true
            }
        ],
        "validateClusters": false,
        "maxDirectResponseBodySizeBytes": 1048576,
        "ignorePortInHostMatching": true
    }
]
```

- TCP流量
  - [GO (TCP) Echo](https://github.com/cjimti/go-echo)
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: goecho-gateway
  namespace: default
spec:
  selector:
    istio: ingressgateway     # 具体的网关实现
  servers:
  - port:
      number: 31400           # 暴露的端口
      name: tcp-goEcho
      protocol: TCP
    hosts:
    - "*"          # 端口对应的主机
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: goecho-vs
spec:
  hosts:
  - "*"
  gateways:
  - goecho-gateway
  http:
  - match:
    - port: 31400
    route:
    - destination:
        host: tcp-echo-service
        port:
          number: 2701
```

### 2. Telemetry

- 生产级Istio安装禁用了访问日志记录
  - 可以通过设置 accessLogFile属性来改变这一默认行为。将其打印到标准输出流：
    - `istioctl install --set mechConfig.accessLogFile=/dev/stdout`

- 在默认情况下，访问日志记录是关闭的
  - 这是有意义的，因为生产集群有数百个或数千个工作负载，每个工作负载都处理大量流量。
  - 此外，由于每个请求都要从一个服务跳到另一个服务，因此产生的访问日志记录量会使所有日志记录系统不堪重负。
  - 目前的方法是只对特别关注的工作负载使用Telemetry API（遥测）启用访问日志记录（在Istio 1.12中作为Alpha级别新增的功能）。
```yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: dupe-2
  namespace: istio-system
spec:
  selector:
    matchLabels:
      app: reviews # Multiple telemetries have the same selector, should generate errors for both
  metrics:
    - providers:
        - name: prometheus
      overrides:
        - match:
            metric: ALL_METRICS
          disabled: false
```

- 遥测定义为与istio-system命名空间中的选择器匹配的Pod启用访问日志记录
  - 如果已将Istio安装配置为将访问日志打印到标准输出流，则不需要进行访问日志记录，因为所有的工作负载都已将日志打印到控制台

- Istio配置，如遥测（telemetry）、sidecar、对等认证（peer authentication）等，可以被应用于不同的作用域并具有不同的优先级
  - 网格级配置——被应用于整个网格的工作负载。网格级配置必须被应用在Istio安装命名空间中，并且没有工作负载选择器。
  - 命名空间级配置——被应用于命名空间中所有的工作负载。命名空间范围的配置被应用于我们想要配置的工作负载的命名空间，而且也没有工作负载选择器。这个被应用于工作负载的命名空间级配置将覆盖所有网格级配置。
  - 特定于工作负载的配置——只被应用于与配置应用的命名空间中工作负载选择器匹配的工作负载（如前面的代码所示）。特定于工作负载的配置会覆盖网格级和命名空间级的配置。注意：Istio定义了如下默认提供程序：prometheus、stack-driver和envoy。你可以在网格配置中使用ExtensionProvider API定义自定义提供程序。

- Istio配置，如遥测（telemetry）、sidecar、对等认证（peer authentication）等，可以被应用于不同的作用域并具有不同的优先级
  - 网格级配置——被应用于整个网格的工作负载。网格级配置必须被应用在Istio安装命名空间中，并且没有工作负载选择器。
  - 命名空间级配置——被应用于命名空间中所有的工作负载。命名空间范围的配置被应用于我们想要配置的工作负载的命名空间，而且也没有工作负载选择器。这个被应用于工作负载的命名空间级配置将覆盖所有网格级配置。
  - 特定于工作负载的配置——只被应用于与配置应用的命名空间中工作负载选择器匹配的工作负载（如前面的代码所示）。特定于工作负载的配置会覆盖网格级和命名空间级的配置。注意：Istio定义了如下默认提供程序：prometheus、stack-driver和envoy。你可以在网格配置中使用ExtensionProvider API定义自定义提供程序。




SMI 服务网格结构接口
Istio提供了SMI中所包含的所有功能。
SMI社区维护了一个适配器（https://github.com/servicemeshinterface/smi-adapter-istio），

sidecar模式 Linkerd、Istio

代理节点模式 一个节点部署一个 envoy
遵循这种架构的服务网格包括 Consul Connect（https://www.consul.io/docs/connect）和 Maesh（https://containo.us/maesh）。
