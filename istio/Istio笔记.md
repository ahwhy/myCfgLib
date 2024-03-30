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

$ kubectl -n istio-system port-forward grafana 3000
$ istioctl dashboard grafana

$ istioctl dashboard jaeger 
```

### 2. BookInfo


## 三、Envoy

Envoy被设计为通过应用程序的进程外运行来避免开发人员受到网络问题的影响。这意味着用任何编程语言或用任何框架编写的任何应用程序都可以利用这些特性。此外，尽管服务架构（SOA、微服务等）是目前流行的架构，但Envoy并不关心是微服务，还是用任何语言编写的单体应用程序，只要它们使用的是Envoy能够理解的协议（如HTTP），Envoy就可以提供价值。

Envoy是一个非常通用的代理，可以扮演不同的角色：作为集群边缘的代理（作为一个入口点），或者作为单个主机或服务组的共享代理，甚至作为我们在Istio中看到的每个服务的代理。通过Istio，每个服务实例都部署一个Envoy代理，以实现最大的灵活性、最佳性能和控制。你使用了一种部署模式（sidecar服务代理），并不意味着你不能使用Envoy提供的优势。事实上，让代理在边缘和应用程序中具有相同的实现，可以使基础设施更容易操作和理解。所以，Envoy可以被部署在集群边缘作为流量入口，也可以被部署在集群内组成服务网格，以充分控制和观察流量的完整调用链路。

- Envoy的核心功能
    - 监听器（Listener）——向外部公开一个应用程序可以连接的端口。例如，80端口上的监听器接收流量，并将任何配置的行为应用于该流量。
    - 路由（Route）——如何处理进入监听器的流量的路由规则。例如，如果传入一个请求并匹配/catalog，则将该流量定向到catalog集群。
    - 集群（Cluster）——特定的上游服务，Envoy可以将流量路由到这些服务。例如，catalog-v1和catalog-v2可以是单独的集群，路由可以指定将流量定向到catalog服务的v1或v2的规则。

Envoy在传递通信方向性时使用的术语与其他代理类似。例如，流量从下游系统进入监听器。该流量被路由到Envoy的一个集群，该集群负责将该流量发送到上游系统。流量从下游经过Envoy流向上游。

Envoy是一个很好的构建模块的原因之一是它支持通过gRPC/REST API进行动态配置。
Envoy之前的开源代理不是为Kubernetes这样的动态环境设计的。它们使用静态的配置文件，需要重新启动才能使配置变化生效。
另外，Envoy提供xDS（*发现服务）API，用于动态配置。它还支持热重启，这使得Envoy可以在不放弃任何活动连接的情况下重新初始化。

Envoy支持通过XDS API进行动态配置。Envoy连接到配置服务器，并使用LDS、RDS、EDS、CDS和其他XDS API请求其配置
Envoy的xDS是一个API集合，包括监听器发现服务（LDS）、集群发现服务（CDS）、端点发现服务（EDS）、路由发现服务（RDS）等。
Envoy配置服务器实现这些API，并作为Envoy的动态配置源。在启动过程中，Envoy会与配置服务器通信（通常是通过gRPC）并订阅配置变化。当环境发生变化时，配置服务器会将变化流向Envoy。


- [Envoy代理](https://www.envoyproxy.io)
- Envoy被用于Ingress控制器 [Contour](https://projectcontour.io)
- [API网关 Amb-assador](https://www.getambassador.io)
- [Gloo](https://docs.solo.io/gloo/)
- [OSM](https://github.com/openservicemesh/osm)



SMI 服务网格结构接口
Istio提供了SMI中所包含的所有功能。
SMI社区维护了一个适配器（https://github.com/servicemeshinterface/smi-adapter-istio），

sidecar模式 Linkerd、Istio

代理节点模式 一个节点部署一个 envoy
遵循这种架构的服务网格包括 Consul Connect（https://www.consul.io/docs/connect）和 Maesh（https://containo.us/maesh）。

