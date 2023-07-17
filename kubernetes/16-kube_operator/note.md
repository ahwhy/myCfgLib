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
kubebuilder init --domain tutorial.kubebuilder.io --repo tutorial.kubebuilder.io/project --owner ahwhya@outlook.com

# init git
git init
git add . &&  git commit -m "Init project" --author "ahwhya <ahwhya@outlook.com>"

# Create an API
kubebuilder create api --group webapp --version v1 --kind Guestbook 
```

### 3.File Tree
```shell
$ kubebuilder init --domain application.operator.io --repo github.com/ahwhy/application-operator --owner ahwhya@outlook.com

$ kubebuilder create api --group apps --version v1 --kind Application

$ tree ./application-operator
./application-operator
├── Dockerfile                                                  # 最终Operator程序编译、构建镜像的逻辑就在这里，我们可以通过修改这个文件来解决一些镜像构建相关的问题，比如Go语言依赖下载的默认GOPROXY配置在国内不一定能访问到，可以在其中配置国内的proxy地址等
├── Makefile                                                    # 这是解放劳动力的工具，这里实现了通过make ×××轻松实现整个程序的编译构建、镜像推送、部署、卸载等操作
├── PROJECT                                                     # PROJECT：这个文件中可以看到项目的一些元数据，比如domain、projectName、repo等信息；添加api后，会增加 resources.api 字段
├── README.md
├── api                                                         # api：这个目录中包含刚才添加的API，这里的application_types.go文件是核心数据结构
│   └── v1
│       ├── application_types.go
│       ├── groupversion_info.go
│       └── zz_generated.deepcopy.go
├── bin
│   └── controller-gen
├── cmd
│   └── main.go
├── config                                                      # config：这个目录中放置了很多个YAML文件；其中包括RBAC权限相关的YAML文件、Prometheus监控服务发现(ServiceMonitor)相关的YAML文件、控制器(Manager)本身部署的YAML文件等。
│   ├── crd                                                     # config/crd：存放的是crd部署相关的kustomize文件
│   │   ├── bases                                               # config/crd/bases/：添加api后，这个目录中新增了一个apps.danielhu.cn_applications.yaml文件，也就是Application类型的CRD配置
│   │   │   └── apps.application.operator.io_applications.yaml
│   │   ├── kustomization.yaml
│   │   ├── kustomizeconfig.yaml
│   │   └── patches
│   │       ├── cainjection_in_applications.yaml
│   │       └── webhook_in_applications.yaml
│   ├── default
│   │   ├── kustomization.yaml
│   │   ├── manager_auth_proxy_patch.yaml
│   │   └── manager_config_patch.yaml
│   ├── manager
│   │   ├── kustomization.yaml
│   │   └── manager.yaml
│   ├── prometheus
│   │   ├── kustomization.yaml
│   │   └── monitor.yaml
│   ├── rbac
│   │   ├── application_editor_role.yaml                       # application_editor_role.yaml：定义了一个有applications资源编辑权限的ClusterRole
│   │   ├── application_viewer_role.yaml                       # application_viewer_role.yaml：定义了一个有applications资源查询权限的ClusterRole
│   │   ├── auth_proxy_client_clusterrole.yaml
│   │   ├── auth_proxy_role.yaml
│   │   ├── auth_proxy_role_binding.yaml
│   │   ├── auth_proxy_service.yaml
│   │   ├── kustomization.yaml
│   │   ├── leader_election_role.yaml
│   │   ├── leader_election_role_binding.yaml
│   │   ├── role.yaml                                          # config/rbac/role.yaml：这里面定义的是一个ClusterRole，manager-role，这是后面Controller部署后将充当的"角色"；该文件定义了对applications资源的创建、删除、查询、更新等操作
│   │   ├── role_binding.yaml
│   │   └── service_account.yaml
│   └── samples
│       ├── apps_v1_application.yaml                           # samples/apps_v1_application.yaml：这是一个CR示例文件，从这个文件的骨架很容易看到通过填充内容即可用来创建一个自定义资源Application类型的实例
│       └── kustomization.yaml
├── go.mod                                                     # 添加api后，会增加 BDD测试相关的ginkgo和gomega依赖
├── go.sum
├── hack
│   └── boilerplate.go.txt                                     # 每个文件头Copyright会加上--owner参数的内容，这个Copyright就是来自hack/boilerplate.go.txt文件
└── internal
    └── controller                                             # controllers/：这里包含控制器的代码逻辑入口。Reconcile函数，"调谐"(Reconcile) 这个词会贯穿整个 Operator
        ├── application_controller.go
        └── suite_test.go

$ make manifests
$ make install
$ make run

$ make undeploy
$ make uninstall
```
