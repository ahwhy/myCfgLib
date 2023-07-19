# Kubernetes Client-go

## 一、Client-go 项目介绍

### 1. client-go 项目结构

- client-go的包结构
  + kubernetes：这个包中放的是用client-gen自动生成的用来访问Kubernetes API的ClientSet，后面会经常看到ClientSet这个工具。
  + discovery：这个包提供了一种机制用来发现API Server支持的API资源。
  + dynamic：这个包中包含dynamic client，用来执行任意API资源对象的通用操作。
  + plugin/pkg/client/auth：这个包提供了可选的用于获取外部源证书的认证插件。
  + transport：这个包用于设置认证和建立连接。
  + tools/cache：这个包中放了很多和开发控制器相关的工具集。

### 2. client-go 版本规则

由于一些历史原因，client-go的版本规则经历了几次变化。不用去关注很早的版本都有哪些规则，简单理解client-go的版本就是一句话：

    Kubernetes版本大于或等于1.17.0时，cllient-go版本使用对应的v0.x.y；
    Kubernetes版本小于1.17.0时，client-go版本使用kubernetes-1.x.y。
    其中，x和y与Kubernetes版本号后两位保持一致，比如Kubernetes v1.17.0对应client-go v0.17.0。

这里说的client-go的版本 体现在tag上，我们在client-go的GitHub代码库的tag列表中可以直观地看到这些[tag](https://github.com/kubernetes/client-go/tags)。下表展示了以Kubernetes 1.17.0版本为中点，client-go和Kubernetes的版本对应关系。

![client-go与Kubernetes的版本对应关系](../images/Client-go与Kubernetes的版本对应关系.jpg)

如表所示，第一行是Kubernetes版本，第一列是client-go版本。在Kubernetes 1.17.0版本之后，client-go老的版本号规则为了更好的兼容性还是保留着，不过最好还是使用新版本号v0.x.y这种格式。

另外，client-go代码库的分支规则和tag又稍有区别，下面简单地通过下表看一下Kubernetes 1.15.n版本之后两个代码库的分支规则对应关系。

![client-go与Kubernetes的版本对应关系](../images/Client-go与Kubernetes%201.15n的版本之后分支对应关系.jpg)

如表所示，从1.18版本开始，两者的分支名称又对应起来了。其实client-go在Kubernetes 1.5版本以前就是现在的分支命名风格，不过从1.5之后变成了2.0，之后就是3.0、4.0、5.0……这种规则了，直到1.18版本。

### 3. 获取 client-go

在写代码的时候需要使用client-go，第一步肯定是通过go get来获取相应版本的client-go依赖。如果需要新版本，可以直接执行：`go get k8s.io/client-go@latest`;

不过这样并不靠谱，一般需要选择明确的版本，最好是和自己使用的Kubernetes集群版本完全一致。可以通过下面的命令来获取需要的版本：`go get k8s.io/client-go@v0.24.6`。


## 二、Client-go 简单使用

### 1. client-go 操作 deployment
