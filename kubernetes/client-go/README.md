# Kubernetes Client-go 源码分析


## 文档简介

client-go项目 是与 kube-apiserver 通信的 clients 的具体实现。

如图所示，在编写自定义控制器的过程中大致依赖于如下组件，其中圆形的是自定义控制器中需要编码的部分，其他椭圆和圆角矩形的是 client-go 提供的一些"工具"。

![编写自定义控制器依赖的组件](./images/编写自定义控制器依赖的组件.jpg)


## 传送门

- [client-go 项目介绍](./01-client-go项目介绍.md)

- [client-go 源码分析之 WorkQueue](./02-client-go源码分析之WorkQueue.md)

- [client-go 源码分析之 DeltaFIFO](./03-client-go源码分析之DeltaFIFO.md)

- [client-go 源码分析之 Indexer 和 ThreadSafeStore](./04-client-go源码分析之Indexer与ThreadSafeStore.md)

- [client-go 源码分析之 ListerWatcher](./05-client-go源码分析之ListerWatcher.md)

- [client-go 源码分析之 Reflector](./06-client-go源码分析之Reflector.md)

- [client-go 源码分析之 Informer](./07-client-go源码分析之Informer.md)

- [client-go Examples](./examples/)