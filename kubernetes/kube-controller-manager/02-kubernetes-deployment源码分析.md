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

### 2. DeploymentController 对象初始化

下面先看一下 DeploymentController 类型的定义。进入 `pkg/controller/deployment` 包，在 deployment_controller.go 文件中，可以看到DeploymentController 的定义
```golang
	// DeploymentController is responsible for synchronizing Deployment objects stored
	// in the system with actual running replica sets and pods.
	type DeploymentController struct {
		// ReplicaSet 操控器
		// rsControl is used for adopting/releasing replica sets.
		rsControl controller.RSControlInterface
		client    clientset.Interface

		eventBroadcaster record.EventBroadcaster
		eventRecorder    record.EventRecorder

		// To allow injection of syncDeployment for testing.
		syncHandler func(ctx context.Context, dKey string) error
		// used for unit testing
		enqueueDeployment func(deployment *apps.Deployment)

		// 用来从 cache 中 list/get 各类资源
		// dLister can list/get deployments from the shared informer's store
		dLister appslisters.DeploymentLister
		// rsLister can list/get replica sets from the shared informer's store
		rsLister appslisters.ReplicaSetLister
		// podLister can list/get pods from the shared informer's store
		podLister corelisters.PodLister

		// dListerSynced returns true if the Deployment store has been synced at least once.
		// Added as a member to the struct to allow injection for testing.
		dListerSynced cache.InformerSynced
		// rsListerSynced returns true if the ReplicaSet store has been synced at least once.
		// Added as a member to the struct to allow injection for testing.
		rsListerSynced cache.InformerSynced
		// podListerSynced returns true if the pod store has been synced at least once.
		// Added as a member to the struct to allow injection for testing.
		podListerSynced cache.InformerSynced

		// 限速队列
		// Deployments that need to be synced
		queue workqueue.RateLimitingInterface
	}

	// NewDeploymentController creates a new DeploymentController.
	func NewDeploymentController(ctx context.Context, dInformer appsinformers.DeploymentInformer, rsInformer appsinformers.ReplicaSetInformer, podInformer coreinformers.PodInformer, client clientset.Interface) (*DeploymentController, error) {
		// Event
		eventBroadcaster := record.NewBroadcaster()
		logger := klog.FromContext(ctx)
		// 初始化一个 DeploymentController 实例对象
		dc := &DeploymentController{
			client:           client,
			eventBroadcaster: eventBroadcaster,
			eventRecorder:    eventBroadcaster.NewRecorder(scheme.Scheme, v1.EventSource{Component: "deployment-controller"}),
			queue:            workqueue.NewNamedRateLimitingQueue(workqueue.DefaultControllerRateLimiter(), "deployment"),
		}
		// ClientSet
		dc.rsControl = controller.RealRSControl{
			KubeClient: client,
			Recorder:   dc.eventRecorder,
		}

		// ResourceEvnetHandler 配置
		dInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				dc.addDeployment(logger, obj)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				dc.updateDeployment(logger, oldObj, newObj)
			},
			// This will enter the sync loop and no-op, because the deployment has been deleted from the store.
			DeleteFunc: func(obj interface{}) {
				dc.deleteDeployment(logger, obj)
			},
		})
		rsInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				dc.addReplicaSet(logger, obj)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				dc.updateReplicaSet(logger, oldObj, newObj)
			},
			DeleteFunc: func(obj interface{}) {
				dc.deleteReplicaSet(logger, obj)
			},
		})
		podInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
			DeleteFunc: func(obj interface{}) {
				dc.deletePod(logger, obj)
			},
		})

		dc.syncHandler = dc.syncDeployment
		dc.enqueueDeployment = dc.enqueue

		// 各种 lister
		dc.dLister = dInformer.Lister()
		dc.rsLister = rsInformer.Lister()
		dc.podLister = podInformer.Lister()
		dc.dListerSynced = dInformer.Informer().HasSynced
		dc.rsListerSynced = rsInformer.Informer().HasSynced
		dc.podListerSynced = podInformer.Informer().HasSynced
		return dc, nil
	}

```


## 二、Deployment Controller 中的 ResourceEventHandler

- 关于 DeploymentController 的 ResourceEventHandler，具体来以下几个回调函数
	- addDeployment
	- updateDeployment
	- deleteDeployment
	- addReplicaSet
	- updateReplicaSet
	- deleteReplicaSet
	- deletePod