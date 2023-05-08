# Kubernetes Operator 开发

## 一、概念定义

### 1.Operator 模式相关定义
- operator
    - Operator 模式 旨在记述（正在管理一个或一组服务的）运维人员的关键目标
    - 这些运维人员负责一些特定的应用和 Service，他们需要清楚地知道系统应该如何运行、如何部署以及出现问题时如何处理
    - [kubernetes operator](https://kubernetes.io/zh-cn/docs/concepts/extend-kubernetes/operator/)

### 2.Kubebuilder 相关定义
- Kubebuilder
    - Kubebuilder是一个使用CRDs构建K8S API的SDK
        - 提供脚手架工具初始化CRDs 工程，自动生成boilerplate代码和配置；
        - 提供代码库封装底层的k8s go-client；
    - 方便用户从零开始开发CRDs， Controllers和Admission Webhooks来扩展K8s

- 控制器模式
    - K8s的编排正是通过一个个控制器根据被控制对象的属性和字段来实现
    - 本质是一个无限循环（实际是事件驱动+定时同步来实现，不是无脑循环）不断地对比期望状态和实际状态
        - 如果有出入则进行Reconcile（调谐）逻辑将实际状态调整为期望状态
        - 期望状态就是我们的对象定义（通常是YAML文件），
        - 实际状态是集群里面当前的运行状态(通常来自于K8s集群内外相关资源的状态汇总)
        - 控制器的编排逻辑主要是第三步做的，这个操作被称为调谐 (Reconcile)，整个控制器调谐的过程称为 "Reconcile Loop"，调谐的最终结果一般是对被控制对象的某种写操作，比如增/删/改Pod
    - 在控制器中定义被控制对象是通过"模版"完成的
        - 比如 Deployment 里而的 template字段里的内容跟一个标准的Pod对象的API定义一样，所有被这个Deployment管理的Pod实例
        - 都是根据这个template字段的创建的，这就是PodTemplate，一个控制对象的定义一般是由上半部分的控制定义（期望状态），加上下半部分的被控制对象的模版组成

- Informer机制
    - Informer机制的核心是在本地维护了一份缓存，通过 ListAndWatch 的方法与 apiserver 做交互，实时同步集群的最新状态
        - 然后，在对象事件到来后 以事件触发的形式执行相应逻辑
        - 该方法能够避免对 apiserver造成过大的压力，同时能够实时映时最新集群状态，是控制器实现 "声明式" 定义的基础
    - client-go 包实现了 informer机制，每一个Informer都由reflector、Delta队列、缓存组成
        - reflector负责与apiserver交互并接受最新的集群信息
        - 队列负责接受井缓存通过ListAndWatch得到的信息
        - 缓存用于保存从Delta的对象

- 参考
    - [podtato-head](https://github.com/podtato-head/podtato-head)
    - [kubebuilder](https://github.com/kubernetes-sigs/kubebuilder)
    - [kubebuilder quick-start](https://book.kubebuilder.io/quick-start.html)


## 二、环境准备

### 1.安装 kubebuilder
```shell
# kubebuilder依赖
# https://github.com/kubernetes-sigs/kustomize 
# https://kubectl.docs.kubernetes.io/installation/kustomize/   (brew install kustomize)
# https://github.com/kubernetes-sigs/controller-tools

# download kubebuilder and install locally.
curl -L -o kubebuilder https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)
chmod +x kubebuilder && mv kubebuilder /usr/local/bin/

# Using master branch
https://go.kubebuilder.io/dl/master/$(go env GOOS)/$(go env GOARCH).
```

### 2.Create a Project
```shell
# create a project directory, and then run the init command.
mkdir project
cd project

# we'll use a domain of tutorial.kubebuilder.io,
# so all API groups will be <group>.tutorial.kubebuilder.io.
kubebuilder init --domain tutorial.kubebuilder.io --repo tutorial.kubebuilder.io/project

# Create an API
kubebuilder create api --group webapp --version v1 --kind Guestbook
```
