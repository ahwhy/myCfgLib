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

	// ConcurrentDeploymentSyncs 默认值是5，也就是默认情况下并发调谐的 Deployment 数量是5个
	func RecommendedDefaultDeploymentControllerConfiguration(obj *kubectrlmgrconfigv1alpha1.DeploymentControllerConfiguration) {
		if obj.ConcurrentDeploymentSyncs == 0 {
			obj.ConcurrentDeploymentSyncs = 5
		}
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


	// syncDeployment will sync the deployment with the given key.
	// This function is not meant to be invoked concurrently with the same key.
	func (dc *DeploymentController) syncDeployment(ctx context.Context, key string) error {
		logger := klog.FromContext(ctx)
		namespace, name, err := cache.SplitMetaNamespaceKey(key)
		if err != nil {
			logger.Error(err, "Failed to split meta namespace cache key", "cacheKey", key)
			return err
		}

		startTime := time.Now()
		logger.V(4).Info("Started syncing deployment", "deployment", klog.KRef(namespace, name), "startTime", startTime)
		defer func() {
			logger.V(4).Info("Finished syncing deployment", "deployment", klog.KRef(namespace, name), "duration", time.Since(startTime))
		}()

		deployment, err := dc.dLister.Deployments(namespace).Get(name)
		if errors.IsNotFound(err) {
			logger.V(2).Info("Deployment has been deleted", "deployment", klog.KRef(namespace, name))
			return nil
		}
		if err != nil {
			return err
		}

		// Deep-copy otherwise we are mutating our cache.
		// TODO: Deep-copy only when needed.
		d := deployment.DeepCopy()

		everything := metav1.LabelSelector{}
		if reflect.DeepEqual(d.Spec.Selector, &everything) {
			dc.eventRecorder.Eventf(d, v1.EventTypeWarning, "SelectingAll", "This deployment is selecting all pods. A non-empty selector is required.")
			if d.Status.ObservedGeneration < d.Generation {
				d.Status.ObservedGeneration = d.Generation
				dc.client.AppsV1().Deployments(d.Namespace).UpdateStatus(ctx, d, metav1.UpdateOptions{})
			}
			return nil
		}

		// List ReplicaSets owned by this Deployment, while reconciling ControllerRef
		// through adoption/orphaning.
		rsList, err := dc.getReplicaSetsForDeployment(ctx, d)
		if err != nil {
			return err
		}
		// List all Pods owned by this Deployment, grouped by their ReplicaSet.
		// Current uses of the podMap are:
		//
		// * check if a Pod is labeled correctly with the pod-template-hash label.
		// * check that no old Pods are running in the middle of Recreate Deployments.
		podMap, err := dc.getPodMapForDeployment(d, rsList)
		if err != nil {
			return err
		}

		if d.DeletionTimestamp != nil {
			return dc.syncStatusOnly(ctx, d, rsList)
		}

		// Update deployment conditions with an Unknown condition when pausing/resuming
		// a deployment. In this way, we can be sure that we won't timeout when a user
		// resumes a Deployment with a set progressDeadlineSeconds.
		if err = dc.checkPausedConditions(ctx, d); err != nil {
			return err
		}

		if d.Spec.Paused {
			return dc.sync(ctx, d, rsList)
		}

		// rollback is not re-entrant in case the underlying replica sets are updated with a new
		// revision so we should ensure that we won't proceed to update replica sets until we
		// make sure that the deployment has cleaned up its rollback spec in subsequent enqueues.
		if getRollbackTo(d) != nil {
			return dc.rollback(ctx, d, rsList)
		}

		scalingEvent, err := dc.isScalingEvent(ctx, d, rsList)
		if err != nil {
			return err
		}
		if scalingEvent {
			return dc.sync(ctx, d, rsList)
		}

		switch d.Spec.Strategy.Type {
		case apps.RecreateDeploymentStrategyType:
			return dc.rolloutRecreate(ctx, d, rsList, podMap)
		case apps.RollingUpdateDeploymentStrategyType:
			return dc.rolloutRolling(ctx, d, rsList)
		}
		return fmt.Errorf("unexpected deployment strategy type: %s", d.Spec.Strategy.Type)
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

### 1. Deployment 变更事件相关函数

还是看 deployment_controller.go 源文件，可以找到 `addDeployment`、`updateDeployment` 和 `deleteDeployment` 三个方法的代码
```golang
	func (dc *DeploymentController) addDeployment(logger klog.Logger, obj interface{}) {
		d := obj.(*apps.Deployment)
		logger.V(4).Info("Adding deployment", "deployment", klog.KObj(d))
		// 新增 deployment 事，直接入队
		dc.enqueueDeployment(d)
	}

	func (dc *DeploymentController) updateDeployment(logger klog.Logger, old, cur interface{}) {
		oldD := old.(*apps.Deployment)
		curD := cur.(*apps.Deployment)
		// old deployment 只用来打印一次日志
		logger.V(4).Info("Updating deployment", "deployment", klog.KObj(oldD))
		// cur deployment 入队
		dc.enqueueDeployment(curD)
	}

	func (dc *DeploymentController) deleteDeployment(logger klog.Logger, obj interface{}) {
		d, ok := obj.(*apps.Deployment)
		if !ok {
			// 处理 DeletedFinalStateUnknown 的场景
			tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("couldn't get object from tombstone %#v", obj))
				return
			}
			d, ok = tombstone.Obj.(*apps.Deployment)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("tombstone contained object that is not a Deployment %#v", obj))
				return
			}
		}
		logger.V(4).Info("Deleting deployment", "deployment", klog.KObj(d))
		// 入队
		dc.enqueueDeployment(d)
	}

	// dc.enqueueDeployment = dc.enqueue
	func (dc *DeploymentController) enqueue(deployment *apps.Deployment) {
		key, err := controller.KeyFunc(deployment)
		if err != nil {
			utilruntime.HandleError(fmt.Errorf("couldn't get key for object %#v: %v", deployment, err))
			return
		

		dc.queue.Add(key)
	}

	// 如果删除了一个对象，但在与 apiserver 断开连接时错过了 watch deletion 事件，则 DeletedFinalStateUnknown 被放入 DeltaFIFO
	// 在这种情况下，我们不知道对象的最终 "resting" 状态，所以包含的 "Obj" 有可能是陈旧的
	// DeletedFinalStateUnknown is placed into a DeltaFIFO in the case where an object
	// was deleted but the watch deletion event was missed while disconnected from
	// apiserver. In this case we don't know the final "resting" state of the object, so
	// there's a chance the included `Obj` is stale.
	type DeletedFinalStateUnknown struct {
		Key string
		Obj interface{}
	}
```

### 2. ReplicaSet 变更事件相关方法

同样在 deployment_controller.go 源文件中，可以找到 `addReplicaSet`、`updateReplicaSet` 和 `deleteReplicaSet` 方法
```golang
	// addReplicaSet 方法
	// addReplicaSet enqueues the deployment that manages a ReplicaSet when the ReplicaSet is created.
	func (dc *DeploymentController) addReplicaSet(logger klog.Logger, obj interface{}) {
		rs := obj.(*apps.ReplicaSet)

		// 如果准备删除，重启过程中就会收取 Added 事件，此时直接调用删除方法 deleteReplicaSet
		if rs.DeletionTimestamp != nil {
			// On a restart of the controller manager, it's possible for an object to
			// show up in a state that is already pending deletion.
			dc.deleteReplicaSet(logger, rs)
			return
		}
		// 查询对应的 deployment
		// If it has a ControllerRef, that's all that matters.
		if controllerRef := metav1.GetControllerOf(rs); controllerRef != nil {
			d := dc.resolveControllerRef(rs.Namespace, controllerRef)
			if d == nil {
				return
			}
			logger.V(4).Info("ReplicaSet added", "replicaSet", klog.KObj(rs))
			dc.enqueueDeployment(d)
			return
		}

		// 如果是一个孤儿 replicaSet，则尝试寻找接管的 deployment
		// Otherwise, it's an orphan. Get a list of all matching Deployments and sync
		// them to see if anyone wants to adopt it.
		ds := dc.getDeploymentsForReplicaSet(logger, rs)
		if len(ds) == 0 {
			return
		}
		logger.V(4).Info("Orphan ReplicaSet added", "replicaSet", klog.KObj(rs))
		// 一般只有一个 deployment，但也不能排除多个 deployment 的情况，这里的 ds 也是 []*apps.Deployment 类型
		for _, d := range ds {
			dc.enqueueDeployment(d)
		}
	}

	// getDeploymentsForReplicaSet returns a list of Deployments that potentially
	// match a ReplicaSet.
	func (dc *DeploymentController) getDeploymentsForReplicaSet(logger klog.Logger, rs *apps.ReplicaSet) []*apps.Deployment {
		deployments, err := util.GetDeploymentsForReplicaSet(dc.dLister, rs)
		if err != nil || len(deployments) == 0 {
			return nil
		}
		// Because all ReplicaSet's belonging to a deployment should have a unique label key,
		// there should never be more than one deployment returned by the above method.
		// If that happens we should probably dynamically repair the situation by ultimately
		// trying to clean up one of the controllers, for now we just return the older one
		if len(deployments) > 1 {
			// ControllerRef will ensure we don't do anything crazy, but more than one
			// item in this list nevertheless constitutes user error.
			logger.V(4).Info("user error! more than one deployment is selecting replica set",
				"replicaSet", klog.KObj(rs), "labels", rs.Labels, "deployment", klog.KObj(deployments[0]))
		}
		return deployments
	}

	// GetDeploymentsForReplicaSet returns a list of Deployments that potentially
	// match a ReplicaSet. Only the one specified in the ReplicaSet's ControllerRef
	// will actually manage it.
	// Returns an error only if no matching Deployments are found.
	func GetDeploymentsForReplicaSet(deploymentLister appslisters.DeploymentLister, rs *apps.ReplicaSet) ([]*apps.Deployment, error) {
		if len(rs.Labels) == 0 {
			return nil, fmt.Errorf("no deployments found for ReplicaSet %v because it has no labels", rs.Name)
		}

		// TODO: MODIFY THIS METHOD so that it checks for the podTemplateSpecHash label
		dList, err := deploymentLister.Deployments(rs.Namespace).List(labels.Everything())
		if err != nil {
			return nil, err
		}

		var deployments []*apps.Deployment
		for _, d := range dList {
			selector, err := metav1.LabelSelectorAsSelector(d.Spec.Selector)
			if err != nil {
				// This object has an invalid selector, it does not match the replicaset
				continue
			}
			// If a deployment with a nil or empty selector creeps in, it should match nothing, not everything.
			if selector.Empty() || !selector.Matches(labels.Set(rs.Labels)) {
				continue
			}
			deployments = append(deployments, d)
		}

		if len(deployments) == 0 {
			return nil, fmt.Errorf("could not find deployments set for ReplicaSet %s in namespace %s with labels: %v", rs.Name, rs.Namespace, rs.Labels)
		}

		return deployments, nil
	}

	// updateReplicaSet 方法
	// updateReplicaSet figures out what deployment(s) manage a ReplicaSet when the ReplicaSet
	// is updated and wake them up. If the anything of the ReplicaSets have changed, we need to
	// awaken both the old and new deployments. old and cur must be *apps.ReplicaSet
	// types.
	func (dc *DeploymentController) updateReplicaSet(logger klog.Logger, old, cur interface{}) {
		curRS := cur.(*apps.ReplicaSet)
		oldRS := old.(*apps.ReplicaSet)
		if curRS.ResourceVersion == oldRS.ResourceVersion {
			// Resync 时 ResourceVersion 相同，不处理直接返回
			// Periodic resync will send update events for all known replica sets.
			// Two different versions of the same replica set will always have different RVs.
			return
		}

		curControllerRef := metav1.GetControllerOf(curRS)
		oldControllerRef := metav1.GetControllerOf(oldRS)
		controllerRefChanged := !reflect.DeepEqual(curControllerRef, oldControllerRef)
		if controllerRefChanged && oldControllerRef != nil {
			// 如果 rs 的 ref 变了，就需要通知旧的 rs 对应的 deployment
			// The ControllerRef was changed. Sync the old controller, if any.
			if d := dc.resolveControllerRef(oldRS.Namespace, oldControllerRef); d != nil {
				dc.enqueueDeployment(d)
			}
		}
		// If it has a ControllerRef, that's all that matters.
		if curControllerRef != nil {
			d := dc.resolveControllerRef(curRS.Namespace, curControllerRef)
			if d == nil {
				return
			}
			logger.V(4).Info("ReplicaSet updated", "replicaSet", klog.KObj(curRS))
			dc.enqueueDeployment(d)
			return
		}

		// Otherwise, it's an orphan. If anything changed, sync matching controllers
		// to see if anyone wants to adopt it now.
		labelChanged := !reflect.DeepEqual(curRS.Labels, oldRS.Labels)
		if labelChanged || controllerRefChanged {
			// 如果是一个孤儿 replicaSet，则尝试寻找接管的 deployment
			ds := dc.getDeploymentsForReplicaSet(logger, curRS)
			if len(ds) == 0 {
				return
			}
			logger.V(4).Info("Orphan ReplicaSet updated", "replicaSet", klog.KObj(curRS))
			for _, d := range ds {
				dc.enqueueDeployment(d)
			}
		}
	}

	// resolveControllerRef returns the controller referenced by a ControllerRef,
	// or nil if the ControllerRef could not be resolved to a matching controller
	// of the correct Kind.
	func (dc *DeploymentController) resolveControllerRef(namespace string, controllerRef *metav1.OwnerReference) *apps.Deployment {
		// We can't look up by UID, so look up by Name and then verify UID.
		// Don't even try to look up by Name if it's the wrong Kind.
		if controllerRef.Kind != controllerKind.Kind {
			return nil
		}
		d, err := dc.dLister.Deployments(namespace).Get(controllerRef.Name)
		if err != nil {
			return nil
		}
		if d.UID != controllerRef.UID {
			// The controller we found with this Name is not the same one that the
			// ControllerRef points to.
			return nil
		}
		return d
	}

	// deleteReplicaSet 方法
	// deleteReplicaSet enqueues the deployment that manages a ReplicaSet when
	// the ReplicaSet is deleted. obj could be an *apps.ReplicaSet, or
	// a DeletionFinalStateUnknown marker item.
	func (dc *DeploymentController) deleteReplicaSet(logger klog.Logger, obj interface{}) {
		rs, ok := obj.(*apps.ReplicaSet)

		// When a delete is dropped, the relist will notice a pod in the store not
		// in the list, leading to the insertion of a tombstone object which contains
		// the deleted key/value. Note that this value might be stale. If the ReplicaSet
		// changed labels the new deployment will not be woken up till the periodic resync.
		if !ok {
			// 处理 DeletedFinalStateUnknown 的场景
			tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("couldn't get object from tombstone %#v", obj))
				return
			}

			rs, ok = tombstone.Obj.(*apps.ReplicaSet)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("tombstone contained object that is not a ReplicaSet %#v", obj))
				return
			}
		}

		// 孤儿 replicaSet 被删除时，没有 deployment 需要关心
		controllerRef := metav1.GetControllerOf(rs)
		if controllerRef == nil {
			// No controller should care about orphans being deleted.
			return
		}
		d := dc.resolveControllerRef(rs.Namespace, controllerRef)
		if d == nil {
			return
		}
		logger.V(4).Info("ReplicaSet deleted", "replicaSet", klog.KObj(rs))
		dc.enqueueDeployment(d)
	}

	// GetControllerOf returns a pointer to a copy of the controllerRef if controllee has a controller
	func GetControllerOf(controllee Object) *OwnerReference {
		ref := GetControllerOfNoCopy(controllee)
		if ref == nil {
			return nil
		}
		cp := *ref
		return &cp
	}

	// GetControllerOf returns a pointer to the controllerRef if controllee has a controller
	func GetControllerOfNoCopy(controllee Object) *OwnerReference {
		refs := controllee.GetOwnerReferences()
		for i := range refs {
			if refs[i].Controller != nil && *refs[i].Controller {
				return &refs[i]
			}
		}
		return nil
	}
```

### 3. Pod 变更事件相关函数

同样在 deployment_controller.go 源文件中，可以找到 `deletePod` 方法
```golang
	// deletePod will enqueue a Recreate Deployment once all of its pods have stopped running.
	func (dc *DeploymentController) deletePod(logger klog.Logger, obj interface{}) {
		pod, ok := obj.(*v1.Pod)

		// When a delete is dropped, the relist will notice a pod in the store not
		// in the list, leading to the insertion of a tombstone object which contains
		// the deleted key/value. Note that this value might be stale. If the Pod
		// changed labels the new deployment will not be woken up till the periodic resync.
		if !ok {
			// 处理 DeletedFinalStateUnknown 的场景
			tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("couldn't get object from tombstone %#v", obj))
				return
			}
			pod, ok = tombstone.Obj.(*v1.Pod)
			if !ok {
				utilruntime.HandleError(fmt.Errorf("tombstone contained object that is not a pod %#v", obj))
				return
			}
		}
		// 孤儿 pod 被删除时，没有 deployment 需要关心
		d := dc.getDeploymentForPod(logger, pod)
		if d == nil {
			return
		}
		logger.V(4).Info("Pod deleted", "pod", klog.KObj(pod))
		if d.Spec.Strategy.Type == apps.RecreateDeploymentStrategyType {
			// Sync if this Deployment now has no more Pods.
			rsList, err := util.ListReplicaSets(d, util.RsListFromClient(dc.client.AppsV1()))
			if err != nil {
				return
			}
			podMap, err := dc.getPodMapForDeployment(d, rsList)
			if err != nil {
				return
			}
			numPods := 0
			for _, podList := range podMap {
				numPods += len(podList)
			}
			if numPods == 0 {
				dc.enqueueDeployment(d)
			}
		}
	}

	// getDeploymentForPod returns the deployment managing the given Pod.
	func (dc *DeploymentController) getDeploymentForPod(logger klog.Logger, pod *v1.Pod) *apps.Deployment {
		// Find the owning replica set
		var rs *apps.ReplicaSet
		var err error
		controllerRef := metav1.GetControllerOf(pod)
		// controllerRef 不存在
		if controllerRef == nil {
			// No controller owns this Pod.
			return nil
		}
		// controllerRef 不是 replicaSet
		if controllerRef.Kind != apps.SchemeGroupVersion.WithKind("ReplicaSet").Kind {
			// Not a pod owned by a replica set.
			return nil
		}
		rs, err = dc.rsLister.ReplicaSets(pod.Namespace).Get(controllerRef.Name)
		if err != nil || rs.UID != controllerRef.UID {
			logger.V(4).Info("Cannot get replicaset for pod", "ownerReference", controllerRef.Name, "pod", klog.KObj(pod), "err", err)
			return nil
		}

		// Now find the Deployment that owns that ReplicaSet.
		controllerRef = metav1.GetControllerOf(rs)
		if controllerRef == nil {
			return nil
		}
		return dc.resolveControllerRef(rs.Namespace, controllerRef)
	}
```