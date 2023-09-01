# Kubernetes 项目依赖包分析

## 一、了解 Kubernetes 其他项目

在开发 Operator 项目时，除了用到 `client-go` 外，还会依赖很多 `k8s.io` 下的项目

### 1. API项目

从项目名称 `API` 上，就可以大致猜到这个项目中存放的是 Kubernetes 的 API 定义，API 的定义单独放到一个项目中是为了解决循环依赖问题。需要使用到 API 定义的项目主要是 `k8s.io/client-go`、`k8s.io/apimachinery`和`k8s.io/apiserver`

- `API` 项目的 [GitHub地址](https://github.com/kubernetes/api)

从API项目的目录结构可以很容易找到熟悉的内容：
```shell
$ tree -L 1 ./api
# 第一层目录都是 API Group
./api
├── admission
├── admissionregistration
├── apidiscovery
├── apiserverinternal
├── apps
├── authentication
├── authorization
├── autoscaling
├── batch
├── certificates
├── code-of-conduct.md
├── coordination
├── core
├── discovery
├── doc.go
├── events
├── extensions
├── flowcontrol
├── go.mod
├── go.sum
├── imagepolicy
├── networking
├── node
├── policy
├── rbac
├── resource
├── roundtrip_test.go
├── scheduling
├── storage
└── testdata

$ tree -L 1 ./api/apps
# API Group 层下，则是 Version 所在的目录
./api/apps
├── OWNERS
├── v1      # 对应 apps/v1 下所有的 Kind
├── v1beta1
└── v1beta2
```

在 `api/apps/v1/types.go` 这里有很多平时经常见的类型定义，比如 `StatefulSet`、`Deployment`、`DaemonSet`、`ReplicaSet` 等。所以以后 在开发的过程中想要操作某个 API，但是又不清楚这个 API 资源定义如何引用，就可以到 `k8s.io/api` 项目中查看。
```golang
    // StatefulSet represents a set of pods with consistent identities.
    // Identities are defined as:
    //   - Network: A single stable DNS and hostname.
    //   - Storage: As many VolumeClaims as requested.
    //
    // The StatefulSet guarantees that a given network identity will always
    // map to the same storage identity.
    type StatefulSet struct {
        metav1.TypeMeta `json:",inline"`
        // Standard object's metadata.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
        // +optional
        metav1.ObjectMeta `json:"metadata,omitempty" protobuf:"bytes,1,opt,name=metadata"`

        // Spec defines the desired identities of pods in this set.
        // +optional
        Spec StatefulSetSpec `json:"spec,omitempty" protobuf:"bytes,2,opt,name=spec"`

        // Status is the current status of Pods in this StatefulSet. This data
        // may be out of date by some window of time.
        // +optional
        Status StatefulSetStatus `json:"status,omitempty" protobuf:"bytes,3,opt,name=status"`
    }

    // Deployment enables declarative updates for Pods and ReplicaSets.
    type Deployment struct {
        metav1.TypeMeta `json:",inline"`
        // Standard object's metadata.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
        // +optional
        metav1.ObjectMeta `json:"metadata,omitempty" protobuf:"bytes,1,opt,name=metadata"`

        // Specification of the desired behavior of the Deployment.
        // +optional
        Spec DeploymentSpec `json:"spec,omitempty" protobuf:"bytes,2,opt,name=spec"`

        // Most recently observed status of the Deployment.
        // +optional
        Status DeploymentStatus `json:"status,omitempty" protobuf:"bytes,3,opt,name=status"`
    }

    type DaemonSet struct {
        metav1.TypeMeta `json:",inline"`
        // Standard object's metadata.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
        // +optional
        metav1.ObjectMeta `json:"metadata,omitempty" protobuf:"bytes,1,opt,name=metadata"`

        // The desired behavior of this daemon set.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
        // +optional
        Spec DaemonSetSpec `json:"spec,omitempty" protobuf:"bytes,2,opt,name=spec"`

        // The current status of this daemon set. This data may be
        // out of date by some window of time.
        // Populated by the system.
        // Read-only.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
        // +optional
        Status DaemonSetStatus `json:"status,omitempty" protobuf:"bytes,3,opt,name=status"`
    }

    // ReplicaSet ensures that a specified number of pod replicas are running at any given time.
    type ReplicaSet struct {
        metav1.TypeMeta `json:",inline"`

        // If the Labels of a ReplicaSet are empty, they are defaulted to
        // be the same as the Pod(s) that the ReplicaSet manages.
        // Standard object's metadata.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
        // +optional
        metav1.ObjectMeta `json:"metadata,omitempty" protobuf:"bytes,1,opt,name=metadata"`

        // Spec defines the specification of the desired behavior of the ReplicaSet.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
        // +optional
        Spec ReplicaSetSpec `json:"spec,omitempty" protobuf:"bytes,2,opt,name=spec"`

        // Status is the most recently observed status of the ReplicaSet.
        // This data may be out of date by some window of time.
        // Populated by the system.
        // Read-only.
        // More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
        // +optional
        Status ReplicaSetStatus `json:"status,omitempty" protobuf:"bytes,3,opt,name=status"`
    }
```

另外，`k8s.io/api` 项目和 `k8s.io/client-go` 同样是从 `k8s.io/kubernetes` 项目的 staging 下同步过来的，也就是说给 `k8s.io/api` 项目贡献代码同样需要提交到 Kubernetes 主库。


### 2. apimachinery项目

machinery 是"机械、组织、体制、系统"的意思，从项目名称上看，这个项目实现的是各种和 API 相关操作的封装

- `apimachinery` 项目的 [GitHub地址](https://github.com/kubernetes/apimachinery)。

`apimachinery` 项目的作用是为了解耦用到 Kubernetes API 的服务端和客户端，实现了很多公共类型依赖，主要包含Scheme、类型转换、编码解码等逻辑。依赖 apimachinery 的项目主要是 `k8s.io/kubernetes`、`k8s.io/client-go` 和 `k8s.io/apiserver` 等

`k8s.io/apimachinery` 项目同样也是从 `k8s.io/kubernetes`项目的 staging 下同步过来的，给 `k8s.io/apimachinery` 项目贡献代码同样需要提交到 Kubernetes 主库。


### 3. controller-runtime项目

与前面介绍的 `k8s.io/api` 和 `k8s.io/apimachinery` 等项目不同，`controller-runtime` 是 kubernetes-sigs 组织下的一个独立项目，而不是一个 Kubernetes 项目的 staging 项目。

这个项目主要包含用于构建 Kubernetes 风格控制器的 Go 语言包集合，主要在 Kubebuilder 和 Operator SDK 中被使用。简而言之，controller-runtime 是用来引导用户编写最佳实践的 Kubernetes Controllers 的。

- `controller-runtime` 项目的 [GitHub地址](https://github.com/kubernetes-sigs/controller-runtime) 

在使用 Kubebuilder 的时候，会自动生成代码，其中用的很多能力都是 `controller-runtime` 提供的。

**a. Managers**

所有的 `Controller` 和 `Webhook` 最终都是由 `Managers` 来运行的，`Managers` 负责 `Controllers` 和 `Webhooks` 的运行、公共依赖项的设置(pkg/runtime/inject)，比如 `shared caches` 和 `clients`、管理 `leader` 选举(pkg/leaderelection)等。

另外，`Managers` 还通过 signal handler 实现了 Pod 运行终止时的优雅退出功能(pkg/manager/signals)。

**b. Controllers**

`Controllers`(pkg/controller) 使用 `events`(pkg/event) 来触发调谐请求，可以手动创建 `Controllers`，但是一般都是通过 `Builder`(pkg/builder) 来创建的，这样可以简化 `event` 源码(pkg/handler)，比如 Kubernetes 资源对象的变更消息，到 event 处理器之间的关联逻辑编码，或者将一个调谐请求加入所属的队列。

`Predicates`(pkg/predicate) 可以被用来过滤哪些 event 最后会触发调谐过程，其中有一些预置公用代码逻辑用于实现一些进阶场景。

**c. Reconcilers**

`Controllers` 的逻辑是在 `Reconcilers` 中实现的，`Reconciler` 函数的核心逻辑是拿到一个包含 name 和 namespace 的对象的调谐请求，然后调谐这个对象，最终返回一个响应或者一个表明是否需要二次调谐的错误。

**d. Clients and Caches**

`Reconcilers` 使用 `Clients`(pkg/client) 来访问API对象，Managers 提供的默认 Client 从本地共享缓存 (pkg/cache) 中读取数据，直接写到 API Server，但是 `Clients` 也可以配置成不经过缓存直接和 API Server 交互。当其他结构化的数据被请求时，缓存中会自动更新监听到的对象。

默认单独的Client 并不保证缓存的写安全，也不保证创建、查询的一致性。代码不应该假设创建、更新成功的资源能够马上得到更新后的资源。

`Caches` 也许有对应的 `Indexes`，它可以通过 `FieldIndexer`(pkg/client) 从 `Managers` 中获取。

`Indexes` 可以被用来快速且简单地通过特定字段检索所有的对象。

**e. Schemes**

`Schemes`(pkg/scheme) 用来关联Go类型和对应的 Kubernetes API 类型(Group-Version-Kinds)的。

**f. Webhooks**

`Webhooks`(pkg/webhook/admission) 也许会被直接实现，但是一般还是使用 `builder`(pkg/webhook/admission/builder) 来创建。它们通过被 `Managers` 管理的 `server`(pkg/webhook) 来运行。

**g. Logging and Metrics**

`Logging`(pkg/log) 是通过 `logr`(https://godoc.org/github.com/go-logr/logr) 日志接口实现的结构化数据，使用 `Zap`(https://go.uber.org/zap,pkg/log/zap) 提供了简单的日志配置。也可以使用其他基于 `logr` 实现的日志工具作为 `controller-runtime` 的日志实现。

`Metrics`(pkg/metrics)注册到了controller-runtime-specific Prometheus metrics registry中，`Manager`可以通过 HTTP Endpoint 来提供 `Metrics` 服务。

**h. Testing**

通过 test 环境(pkg/envtest)可以简单地给 `Controllers` 与 `Webhooks` 构建单元测试和集成测试。

`envtest` 会自动复制一份 ETCD 和 kube-apiserver 到合适的地方，然后提供一个正确的方式来自动连接到 API Server。

`envtest` 通过一些设计也可以和Ginkgo测试框架一起工作。
