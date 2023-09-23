# Kubernetes Deployment 源码分析

## 一、Deployment Controller 中的逻辑入口

### 1. startDeploymentController

先进入[Kubernetes项目](https://https://github.com/kubernetes/kubernetes)的 `cmd/kube-controller-manager/app` 包，在 `apps.go` 中可以看到 `startDeploymentController()` 函数，这个函数也就是 DeploymentController 的初始化和启动入口
```golang
  func startDeploymentController(ctx context.Context, controllerContext ControllerContext) (controller.Interface, bool, error) {
    // 通过 NewDeploymentController() 方法初始化一个DeploymentController实例
    dc, err := deployment.NewDeploymentController(
      ctx,
      controllerContext.InformerFactory.Apps().V1().Deployments(),
      controllerContext.InformerFactory.Apps().V1().ReplicaSets(),
      controllerContext.InformerFactory.Core().V1().Pods(),
      controllerContext.ClientBuilder.ClientOrDie("deployment-controller"),
    )
    if err != nil {
      return nil, true, fmt.Errorf("error creating Deployment controller: %v", err)
    }
    // 启动 DeploymentController
    go dc.Run(ctx, int(controllerContext.ComponentConfig.DeploymentController.ConcurrentDeploymentSyncs))
    return nil, true, nil
  }
```

在 `startDeploymentController()` 函数中先通过 `NewDeploymentController()` 方法初始化一个 DeploymentController 实例，这里的参数是 DeploymentInformer、ReplicaSetInformer、PodInformer 和 ClientSet，因而 DeploymentController 也就具备了获取 Deployment、ReplicaSet、Pod 三类资源变更事件以及 CURD apiserver 操作各种资源的能力。接着这个函数中又调用了 DeploymentController 的 `Run()` 方法来启动 DeploymentController，这里的参数 ConcurrentDeploymentSyncs 默认值是5，也就是默认情况下并发调谐的 Deployment 数量是5个。
