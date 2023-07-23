# Kubernetes API 简介

## 一、了解 Kubernetes API

Kubernetes集群中有一个kube-apiserver组件，所有组件需要操作集群资源时都通过调用kube-apiserver提供的RESTful接口来实现。而kube-apiserver进一步和ETCD交互，完成资源信息的更新，另外kube-apiserver也是集群内唯一和ETCD直接交互的组件。

Kubernetes中的资源本质就是一个API对象，这个对象的"期望状态"被API Server保存在ETCD中，然后提供RESTful接口用于更新这些对象。我们可以直接和API Server交互，使用"声明"的方式来管理这些资源(API对象)，也可以通过kubectl这种命令行工具，或者client-go这类SDK。

当 Initializer 更新用户的 Pod 对象的时候，必须使用 PATCH API 来完成。而这种 PATCH API，正是声明式 API 最主要的能力。在 Kubernetes 项目中，一个 API 对象在 Etcd 里的完整资源路径，是由: Group(API 组)、Version(API 版本)和 Resource(API 资源类型)三个部分组成的。 

- [Kubernetes官网的API文档](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.23/)


## 二、使用 Kubernetes API

这里以一个 Deployment资源 的增删改查操作为例，展示一下如何与API Server交互。

### 1. 通过 Curl 访问API

- 由于kube-apiserver默认提供的是HTTPS服务，而且是双向TLS认证，这里通过kubectl来代理API Server服务
```shell
# Creates a proxy server or application-level gateway between localhost and the Kubernetes API server.
$ kubectl proxy --port=8080
Starting to serve on 127.0.0.1:8080

# 验证代理正常
$ curl 127.0.0.1:8080/version
{
  "major": "1",
  "minor": "24+",
  "gitVersion": "v1.24.6-aliyun.1",
  "gitCommit": "5296768e052ba56e92b5d5bf7b52d33973a34c6f",
  "gitTreeState": "clean",
  "buildDate": "2023-04-19T06:36:28Z",
  "goVersion": "go1.18.6",
  "compiler": "gc",
  "platform": "linux/amd64"
}%
```

- 通过简单的HTTP请求来和API Server交互
```shell
# 使用本地的配置文件来描述Deployment资源
$ vim ../07-workload/deployment-demo.yaml

# Deployment的创建API是
# POST /apis/apps/v1/namespaces/{namespace}/deployments
# 执行下面的curl命令在default命名空间下创建一个Deployment
$ curl -X POST \
   -H 'Content-Type: application/yaml' \
   --data-binary '@../07-workload/deployment-demo.yaml' \
   http://127.0.0.1:8080/apis/apps/v1/namespaces/default/deployments
{
  "kind": "Deployment",
  "apiVersion": "apps/v1",
  "metadata": {
    "name": "deployment-demo",
    "namespace": "default",
    "uid": "156f497b-b1b2-4c84-911d-5cb6dadfe874",
    "resourceVersion": "2482631",
    "generation": 1,
    "creationTimestamp": "2023-07-18T03:11:02Z",
    "managedFields": []
  },
...
  "status": {}
}%

# 可以看到API Server会响应一个新创建的资源的详细对象描述(采用JSON格式)
$ kubectl get deployment
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
deployment-demo   4/4     4            4           4m

# Deployment的删除API是
# DELETE /apis/apps/v1/namespaces/{namespace}/deployments/name
# 执行下面的命令删除前面在default命名空间下创建的Deployment
$ curl -X DELETE \
   -H 'Content-Type: application/yaml' \
   --data '
   gracePeriodSeconds: 0
   orphanDependents: false' \
   http://127.0.0.1:8080/apis/apps/v1/namespaces/default/deployments/deployment-demo
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Success",
  "details": {
    "name": "deployment-demo",
    "group": "apps",
    "kind": "deployments",
    "uid": "156f497b-b1b2-4c84-911d-5cb6dadfe874"
  }
}%
# 删除操作成功的响应体是一个Status类型的对象，可以很清晰地看到这次被删除的对象所对应的group、kind、name、uid等详细信息

# 查看某个api资源是否区分命名空间
$ kubectl apiversion --namespace=true
```

### 2. 通过 Kubectl Raw 访问 API

- 直接使用kubectl xxx --raw来访问API
```shell
# Raw URI to request from the server. Uses the transport specified by the kubeconfig file.
kubectl get --raw /version
{
  "major": "1",
  "minor": "24+",
  "gitVersion": "v1.24.6-aliyun.1",
  "gitCommit": "5296768e052ba56e92b5d5bf7b52d33973a34c6f",
  "gitTreeState": "clean",
  "buildDate": "2023-04-19T06:36:28Z",
  "goVersion": "go1.18.6",
  "compiler": "gc",
  "platform": "linux/amd64"
}%

# 通过kubectl get --raw可以实现和curl类似的效果，不需要指定API Server的地址，同样的认证信息也不需要，这里默认用了kubeconfig中的连接信息
$ kubectl get --raw /apis/apps/v1/namespaces/default/deployments/deployment-demo
{"kind":"Deployment","apiVersion":"apps/v1",...}
```


## 三、理解 GVK - 组、版本与类型

GVK就是Group、Version、Kind三个词的首字母缩写。我们在描述Kubernetes API时经常会用到这样一个四元组：Groups、Versions、Kinds和Resources。

它们具体的含义如下：
- Groups和Versions
  - 一个Kubernetes API Group表示的是一些相关功能的集合，比如apps这个Group里面就包含deployments、replicasets、daemonsets、statefulsets等资源，这些资源都是应用工作负载相关的
  - 一个Group可以有一个或多个Versions，不难理解这里的用意，毕竟随着时间的推移，一个Group中的API难免有所变化。以前的Kubernetes版本创建Deployment时apiVersion用过apps/v1beta1和apps/v1beta2，现在已经是apps/v1了。

- Kinds和Resources
  - 每个group-version(确定版本的一个组)中都包含一个或多个API类型，这些类型就是这里说的Kinds。每个Kind在不同的版本中一般会有所差异，但是每个版本的Kind要能够存储其他版本Kind的资源类型，无论是通过存储在字段里实现还是通过存储在注解中实现，这也就意味着使用老版本的API存储新版本类型数据不会引起数据丢失或污染。
  - 至于Resources，指的是一个Kind的具体使用，比如Pod类型对应的资源是pods
    - 例如我们可以创建5个pods资源，其类型是Pod
    - 描述资源的单词都是小写的，就像pods，而对应的类型一般就是这个资源的首字母大写单词的单数形式，比如pods对应Pod
  - 类型和资源往往是一一对应的，尤其是在CRD的实现上
    - 常见的特例就是为了支持HorizontalPodAutoscaler(HPA)和不同类型交互，Scale类型对应的资源有deployments/scale和replicasets/scale两种

通过一个GroupVersionKind(GVK)可以确定一个具体的类型，同样的 确定一个资源也就可以通过GroupVersionResource(GVR)来实现。