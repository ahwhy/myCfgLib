# client-go 源码分析之 Informer

## 一、Client-go 源码分析

### 1. client-go 源码概览

client-go项目 是与 kube-apiserver 通信的 clients 的具体实现，其中包含很多相关工具包，例如 `kubernetes`包 就包含与 Kubernetes API 通信的各种 ClientSet，而 `tools/cache`包 则包含很多强大的编写控制器相关的组件。

所以接下来我们以自定义控制器的底层实现原理为线索，来分析 client-go 中相关模块的源码实现。

如图所示，在编写自定义控制器的过程中大致依赖于如下组件，其中圆形的是自定义控制器中需要编码的部分，其他椭圆和圆角矩形的是 client-go 提供的一些"工具"。

![编写自定义控制器依赖的组件](./images/编写自定义控制器依赖的组件.jpg)

- client-go 的源码入口在 Kubernetes 项目的 `staging/src/k8s.io/client-go` 中，先整体查看上面涉及的相关模块，然后逐个深入分析其实现。
  + `Reflector` 从 apiserver 监听(watch)特定类型的资源，拿到变更通知后，将其丢到 DeltaFIFO 队列中
  + `Informer` 从 DeltaFIFO 中弹出(pop)相应对象，然后通过 Indexer 将对象和索引丢到本地 cache 中，再触发相应的事件处理函数(Resource Event Handlers)
  + `Indexer` 主要提供一个对象根据一定条件检索的能力，典型的实现是通过 namespace/name 来构造 key，通过 Thread Safe Store 来存储对象
  + `WorkQueue` 一般使用的是延时队列实现，在 Resource Event Handlers 中会完成将对象的 key 放入 WorkQueue 的过程，然后在自己的逻辑代码里从 WorkQueue 中消费这些 key
  + `ClientSet` 提供的是资源的 CURD 能力，与 apiserver 交互
  + `Resource Event Handlers` 一般在 Resource Event Handlers 中添加一些简单的过滤功能，判断哪些对象需要加到 WorkQueue 中进一步处理，对于需要加到 WorkQueue 中的对象，就提取其 key，然后入队
  + `Worker` 指的是我们自己的业务代码处理过程，在这里可以直接收到 WorkQueue 中的任务，可以通过 Indexer 从本地缓存检索对象，通过 ClientSet 实现对象的增、删、改、查逻辑


## 二、Client-go Informer

Informer 这个词的出镜率很高，与 `Reflector`、`WorkQueue` 等组件不同，`Informer` 相对来说更加模糊，在很多文章中都可以看到 Informer 的身影，在源码中真的去找一个叫作 Informer 的对象，却又发现找不到一个单纯的 Informer，但是有很多结构体或者接口中包含 Informer 这个词。

在一开始提到过 `Informer` 从 `DeltaFIFO` 中 Pop 相应的对象，然后通过 `Indexer` 将对象和索引丢到本地 `cache` 中，再触发相应的事件处理函数(Resource Event Handlers)的运行。接下来通过源码，重新来梳理一下整个过程。

### 1. Informer 即 Controller

**a. Controller 结构体与 Controller 接口**

Informer 通过一个 `Controller` 对象来定义，本身结构很简单，在 `k8s.io/client-go/tools/cache`包中的 controller.go 源文件中可以看到：
```golang
	// Controller的定义
	// `*controller` implements Controller
	type controller struct {
		config         Config
		reflector      *Reflector
		reflectorMutex sync.RWMutex
		clock          clock.Clock
	}
```
这里有熟悉的 `Reflector` ，可以猜到 `Informer` 启动时会去运行 `Reflector` ，从而通过 `Reflector` 实现 list-watch apiserver，更新"事件"到 `DeltaFIFO` 中用于进一步处理

继续看下 `controller` 对应的 `Controller` 接口：
```golang
	// Controller is a low-level controller that is parameterized by a
	// Config and used in sharedIndexInformer.
	type Controller interface {
		// Run does two things.  One is to construct and run a Reflector
		// to pump objects/notifications from the Config's ListerWatcher
		// to the Config's Queue and possibly invoke the occasional Resync
		// on that Queue.  The other is to repeatedly Pop from the Queue
		// and process with the Config's ProcessFunc.  Both of these
		// continue until `stopCh` is closed.
		Run(stopCh <-chan struct{})

		// HasSynced delegates to the Config's Queue
		HasSynced() bool

		// LastSyncResourceVersion delegates to the Reflector when there
		// is one, otherwise returns the empty string
		LastSyncResourceVersion() string
	}
```
这里的核心方法就是 `Run(stopCh<-chan struct{})`，Run 负责两件事情

  1) 构造 `Reflector` 利用 `ListerWatcher` 的能力将对象事件更新到 `DeltaFIFO`。
  2) 从 `DeltaFIFO` 中 `Pop` 对象后调用 `ProcessFunc` 来处理。

**b. Controller 的初始化**

在 controller.go 文件中有如下代码：
```golang
	// New makes a new Controller from the given Config.
	func New(c *Config) Controller {
		ctlr := &controller{
			config: *c,
			clock:  &clock.RealClock{},
		}
		return ctlr
	}

	// Config contains all the settings for one of these low-level controllers.
	type Config struct {
		// The queue for your objects - has to be a DeltaFIFO due to
		// assumptions in the implementation. Your Process() function
		// should accept the output of this Queue's Pop() method.
		Queue

		// Something that can list and watch your objects.
		ListerWatcher

		// Something that can process a popped Deltas.
		Process ProcessFunc

		// ObjectType is an example object of the type this controller is
		// expected to handle.
		ObjectType runtime.Object

		// ObjectDescription is the description to use when logging type-specific information about this controller.
		ObjectDescription string

		// FullResyncPeriod is the period at which ShouldResync is considered.
		FullResyncPeriod time.Duration

		// ShouldResync is periodically used by the reflector to determine
		// whether to Resync the Queue. If ShouldResync is `nil` or
		// returns true, it means the reflector should proceed with the
		// resync.
		ShouldResync ShouldResyncFunc

		// If true, when Process() returns an error, re-enqueue the object.
		// TODO: add interface to let you inject a delay/backoff or drop
		//       the object completely if desired. Pass the object in
		//       question to this interface as a parameter.  This is probably moot
		//       now that this functionality appears at a higher level.
		RetryOnError bool

		// Called whenever the ListAndWatch drops the connection with an error.
		WatchErrorHandler WatchErrorHandler

		// WatchListPageSize is the requested chunk size of initial and relist watch lists.
		WatchListPageSize int64
	}

	// ShouldResyncFunc is a type of function that indicates if a reflector should perform a
	// resync or not. It can be used by a shared informer to support multiple event handlers with custom
	// resync periods.
	type ShouldResyncFunc func() bool

	// ProcessFunc processes a single object.
	type ProcessFunc func(obj interface{}, isInInitialList bool) error
```
这里主要是传递了一个 `Config` 进来，核心逻辑便是 `Config` 从何而来以及后面要如何使用。

然后，先不关注 `NewInformer()` 的代码，实际开发中主要是使用 `SharedIndexInformer`，这两个入口初始化 `Controller` 的逻辑类似。
直接跟踪更实用的一个分支，查看 `func (s *sharedIndexInformer) Run(stopCh<-chan struct{})` 方法中如何调用 `New()`，代码位于 shared_informer.go 中：
```golang
	func (s *sharedIndexInformer) Run(stopCh <-chan struct{}) {
		defer utilruntime.HandleCrash()

		if s.HasStarted() {
			klog.Warningf("The sharedIndexInformer has started, run more than once is not allowed")
			return
		}

		func() {
			s.startedLock.Lock()
			defer s.startedLock.Unlock()

			// 初始化一个 DeltaFIFO
			fifo := NewDeltaFIFOWithOptions(DeltaFIFOOptions{
				KnownObjects:          s.indexer,
				EmitDeltaTypeReplaced: true,
				Transformer:           s.transform,
			})

			cfg := &Config{
				Queue:             fifo,
				ListerWatcher:     s.listerWatcher,
				ObjectType:        s.objectType,
				ObjectDescription: s.objectDescription,
				FullResyncPeriod:  s.resyncCheckPeriod,
				RetryOnError:      false,
				ShouldResync:      s.processor.shouldResync,

				Process:           s.HandleDeltas,
				WatchErrorHandler: s.watchErrorHandler,
			}

			// 通过 Config 创建一个 Controller
			s.controller = New(cfg)
			s.controller.(*controller).clock = s.clock
			s.started = true
		}()

		// Separate stop channel because Processor should be stopped strictly after controller
		processorStopCh := make(chan struct{})
		var wg wait.Group
		defer wg.Wait()              // Wait for Processor to stop
		defer close(processorStopCh) // Tell Processor to stop
		wg.StartWithChannel(processorStopCh, s.cacheMutationDetector.Run)
		wg.StartWithChannel(processorStopCh, s.processor.run)

		defer func() {
			s.startedLock.Lock()
			defer s.startedLock.Unlock()
			s.stopped = true // Don't want any new listeners
		}()
		// func (c *controller) Run(stopCh <-chan struct{})
		s.controller.Run(stopCh)
	}
```
从这里可以看到 `SharedIndexInformer` 的 `Run()` 过程中会构造一个 `Config`，然后创建 `Controller`，最后调用 `Controller` 的 `Run()`方法。

另外，这里也可以看到前面分析过的 `DeltaFIFO`、`ListerWatcher` 等，其中的 `Process: s.HandleDeltas` 这一行也比较重要，`Process` 属性的类型是 `ProcessFunc`，可以看到具体的 `ProcessFunc` 是 `HandleDeltas` 方法。

**c. Controller 的启动**

上面提到 `Controller` 的初始化本身没有太多的逻辑，主要是构造了一个 `Config` 对象传递进来，所以 `Controller` 启动时肯定会有这个 `Config` 的使用逻辑，回到 controller.go 文件继续查看：
```golang
	// Run begins processing items, and will continue until a value is sent down stopCh or it is closed.
	// It's an error to call Run more than once.
	// Run blocks; call via go.
	func (c *controller) Run(stopCh <-chan struct{}) {
		defer utilruntime.HandleCrash()
		go func() {
			<-stopCh
			c.config.Queue.Close()
		}()
		// 利用 Config 中的配置构造 Reflector
		r := NewReflectorWithOptions(
			c.config.ListerWatcher,
			c.config.ObjectType,
			// 若由上面的 sharedIndexInformer 追踪而来，此时传入的 Queue 为 DeltaFIFO
			c.config.Queue,
			ReflectorOptions{
				ResyncPeriod:    c.config.FullResyncPeriod,
				TypeDescription: c.config.ObjectDescription,
				Clock:           c.clock,
			},
		)
		r.ShouldResync = c.config.ShouldResync
		r.WatchListPageSize = c.config.WatchListPageSize
		if c.config.WatchErrorHandler != nil {
			r.watchErrorHandler = c.config.WatchErrorHandler
		}

		c.reflectorMutex.Lock()
		c.reflector = r
		c.reflectorMutex.Unlock()

		var wg wait.Group

		// 启动 Reflector
		// func (r *Reflector) Run(stopCh <-chan struct{})
		wg.StartWithChannel(stopCh, r.Run)

		// 执行 Controller 的 processLoop
		wait.Until(c.processLoop, time.Second, stopCh)
		wg.Wait()
	}
```
这里的代码逻辑很简单，构造 `Reflector` 后运行起来，然后执行 `c.processLoop`，显然 `Controller` 的业务逻辑隐藏在 `processLoop` 方法中。

**d. processLoop**

这里的代码逻辑是从 `DeltaFIFO` 中 Pop 出一个对象丢给 `PopProcessFunc` 处理，如果失败了就 re-enqueue 到 `DeltaFIFO` 中。前面提到过这里的 `PopProcessFunc` 由 `HandleDeltas()` 方法来实现，所以这里的主要逻辑就转到了 `HandleDeltas()` 是如何实现的。
```golang
	// processLoop drains the work queue.
	// TODO: Consider doing the processing in parallel. This will require a little thought
	// to make sure that we don't end up processing the same object multiple times
	// concurrently.
	//
	// TODO: Plumb through the stopCh here (and down to the queue) so that this can
	// actually exit when the controller is stopped. Or just give up on this stuff
	// ever being stoppable. Converting this whole package to use Context would
	// also be helpful.
	func (c *controller) processLoop() {
		for {
			// config 的 Process 属性为 s.HandleDelta
			// type PopProcessFunc func(obj interface{}, isInInitialList bool) error
			obj, err := c.config.Queue.Pop(PopProcessFunc(c.config.Process))
			if err != nil {
				if err == ErrFIFOClosed {
					return
				}
				if c.config.RetryOnError {
					// This is the safe way to re-enqueue.
					c.config.Queue.AddIfNotPresent(obj)
				}
			}
		}
	}
```

**e. HandleDeltas()**

`HandleDeltas()` 代码逻辑都落在 `processDeltas()` 函数的调用上，位于 shared_informer.go 文件中：
```golang
	func (s *sharedIndexInformer) HandleDeltas(obj interface{}, isInInitialList bool) error {
		s.blockDeltas.Lock()
		defer s.blockDeltas.Unlock()

		if deltas, ok := obj.(Deltas); ok {
			return processDeltas(s, s.indexer, deltas, isInInitialList)
		}
		return errors.New("object given as Process argument is not Deltas")
	}

	// Multiplexes updates in the form of a list of Deltas into a Store, and informs
	// a given handler of events OnUpdate, OnAdd, OnDelete
	func processDeltas(
		// Object which receives event notifications from the given deltas
		handler ResourceEventHandler,
		clientState Store,
		deltas Deltas,
		isInInitialList bool,
	) error {
		// from oldest to newest
		// 对于每个 Deltas 来说，其中保存了很多 Delta，也就是对应不同类型的多个对象，这里的遍历会从旧往新里走
		for _, d := range deltas {
			obj := d.Object

			switch d.Type {
			// 除了 Deleted 外的所有情况
			case Sync, Replaced, Added, Updated:
				if old, exists, err := clientState.Get(obj); err == nil && exists {
					// 通过 indexer 从 cache 中查询当前 Object，如果存在则更新 indexer 中的对象
					if err := clientState.Update(obj); err != nil {
						return err
					}
					// 调用 ResourceEventHandler 的 OnUpdate()
					handler.OnUpdate(old, obj)
				} else {
					// 将对象添加到 indexer 中
					if err := clientState.Add(obj); err != nil {
						return err
					}
					// 调用 ResourceEventHandler 的 OnAdd()
					handler.OnAdd(obj, isInInitialList)
				}
			case Deleted:
				// 如果是删除操作，则从 indexer 中删除这个对象
				if err := clientState.Delete(obj); err != nil {
					return err
				}
				// 调用 ResourceEventHandler 的 OnDelete()
				handler.OnDelete(obj)
			}
		}
		return nil
	}

	// ResourceEventHandler can handle notifications for events that
	// happen to a resource. The events are informational only, so you
	// can't return an error.  The handlers MUST NOT modify the objects
	// received; this concerns not only the top level of structure but all
	// the data structures reachable from it.
	//   - OnAdd is called when an object is added.
	//   - OnUpdate is called when an object is modified. Note that oldObj is the
	//     last known state of the object-- it is possible that several changes
	//     were combined together, so you can't use this to see every single
	//     change. OnUpdate is also called when a re-list happens, and it will
	//     get called even if nothing changed. This is useful for periodically
	//     evaluating or syncing something.
	//   - OnDelete will get the final state of the item if it is known, otherwise
	//     it will get an object of type DeletedFinalStateUnknown. This can
	//     happen if the watch is closed and misses the delete event and we don't
	//     notice the deletion until the subsequent re-list.
	type ResourceEventHandler interface {
		OnAdd(obj interface{}, isInInitialList bool)
		OnUpdate(oldObj, newObj interface{})
		OnDelete(obj interface{})
	}

	// Conforms to ResourceEventHandler
	func (s *sharedIndexInformer) OnAdd(obj interface{}, isInInitialList bool) {
		// Invocation of this function is locked under s.blockDeltas, so it is
		// save to distribute the notification
		s.cacheMutationDetector.AddObject(obj)
		s.processor.distribute(addNotification{newObj: obj, isInInitialList: isInInitialList}, false)
	}

	type addNotification struct {
		newObj          interface{}
		isInInitialList bool
	}

	// Conforms to ResourceEventHandler
	func (s *sharedIndexInformer) OnUpdate(old, new interface{}) {
		isSync := false

		// If is a Sync event, isSync should be true
		// If is a Replaced event, isSync is true if resource version is unchanged.
		// If RV is unchanged: this is a Sync/Replaced event, so isSync is true

		if accessor, err := meta.Accessor(new); err == nil {
			if oldAccessor, err := meta.Accessor(old); err == nil {
				// Events that didn't change resourceVersion are treated as resync events
				// and only propagated to listeners that requested resync
				isSync = accessor.GetResourceVersion() == oldAccessor.GetResourceVersion()
			}
		}

		// Invocation of this function is locked under s.blockDeltas, so it is
		// save to distribute the notification
		s.cacheMutationDetector.AddObject(new)
		s.processor.distribute(updateNotification{oldObj: old, newObj: new}, isSync)
	}

	type updateNotification struct {
		oldObj interface{}
		newObj interface{}
	}

	// Conforms to ResourceEventHandler
	func (s *sharedIndexInformer) OnDelete(old interface{}) {
		// Invocation of this function is locked under s.blockDeltas, so it is
		// save to distribute the notification
		s.processor.distribute(deleteNotification{oldObj: old}, false)
	}

	type deleteNotification struct {
		oldObj interface{}
	}
```
这里的代码逻辑主要是遍历一个 `Deltas` 中的所有 `Delta`，然后根据 `Delta` 的类型来决定如何操作 `Indexer`，也就是更新本地 `cache`，同时分发相应的通知。

### 2. SharedIndexInformer对象

**a. 1.SharedIndexInformer 是什么**

在 Operator 开发中，如果不使用 controller-runtime 库，也就是不通过 Kubebuilder 等工具来生成脚手架，就经常会用到 `SharedInformerFactory`。

- 一个典型的例子，`sample-controller` 中的 `main()`函数
	- [sample-controller](https://github.com/kubernetes/sample-controller)
```golang
	func main() {
		// ...
		cfg, err := clientcmd.BuildConfigFromFlags(masterURL, kubeconfig)
		kubeClient, err := kubernetes.NewForConfig(cfg)
		exampleClient, err := clientset.NewForConfig(cfg)
		// ...

		// kubeinformers "k8s.io/client-go/informers"
		kubeInformerFactory := kubeinformers.NewSharedInformerFactory(kubeClient, time.Second*30)
		exampleInformerFactory := informers.NewSharedInformerFactory(exampleClient, time.Second*30)

		controller := NewController(ctx, kubeClient, exampleClient,
			kubeInformerFactory.Apps().V1().Deployments(),
			exampleInformerFactory.Samplecontroller().V1alpha1().Foos())

		// notice that there is no need to run Start methods in a separate goroutine. (i.e. go kubeInformerFactory.Start(ctx.done())
		// Start method is non-blocking and runs all registered informers in a dedicated goroutine.
		kubeInformerFactory.Start(ctx.Done())
		exampleInformerFactory.Start(ctx.Done())
		// ...

		if err = controller.Run(ctx, 2); err != nil {
			logger.Error(err, "Error running controller")
			klog.FlushAndExit(klog.ExitFlushTimeout, 1)
		}
	}
```

这里可以看到 `sample-controller` 依赖于 `kubeInformerFactory.Apps().V1().Deployments()` 提供一个 `Informer`，其中的 `Deployments()` 方法返回的是 `DeploymentInformer` 类型，在 client-go 的 `informers/apps/v1` 包的 deployment.go 文件中有 `DeploymentInformer` 类型的相关定义：
```golang
	// DeploymentInformer provides access to a shared informer and lister for Deployments.
	type DeploymentInformer interface {
		Informer() cache.SharedIndexInformer
		Lister() v1.DeploymentLister
	}
```
这里可以看到 `DeploymentInformer` 是由 `Informer` 和 `Lister` 组成的，也就是说上面例子中，编码时用到的 `Informer` 本质就是一个  `SharedIndexInformer`。

**b. SharedIndexInformer 接口的定义**

回到 tools/cache/shared_informer.go 文件中，可以看到 `SharedIndexInformer`接口的定义：
```golang
	// SharedIndexInformer provides add and get Indexers ability based on SharedInformer.
	type SharedIndexInformer interface {
		SharedInformer
		// AddIndexers add indexers to the informer before it starts.
		AddIndexers(indexers Indexers) error
		GetIndexer() Indexer
	}

	// SharedInformer provides eventually consistent linkage of its
	// clients to the authoritative state of a given collection of
	// objects.  An object is identified by its API group, kind/resource,
	// namespace (if any), and name; the `ObjectMeta.UID` is not part of
	// an object's ID as far as this contract is concerned.  One
	// SharedInformer provides linkage to objects of a particular API
	// group and kind/resource.  The linked object collection of a
	// SharedInformer may be further restricted to one namespace (if
	// applicable) and/or by label selector and/or field selector.
	// SharedInformer 提供了其客户端到给定对象集合的可信状态的最终一致的链接。
	// 对象由其 API group、kind/resource、namespace(如果有的话)和 name 来标识；
	// 就此协定而言，"ObjectMeta.UID" 不是对象 ID 的一部分。
	// 一个 SharedInformer 提供了到特定 API group、kind/resource 的对象的链接。
	// SharedInformer 的链接对象集合可以进一步被限制到一个 namespace(如果适用的话)、label selector、field selector。
	//
	// The authoritative state of an object is what apiservers provide
	// access to, and an object goes through a strict sequence of states.
	// An object state is either (1) present with a ResourceVersion and
	// other appropriate content or (2) "absent".
	// 对象的可信状态是 apiservers 提供访问的内容，对象经历一系列严格的状态。
	// 对象状态 (1)与资源版本和其他适当的内容一起出现，(2)"不存在"。
	//
	// The local cache starts out empty, and gets populated and updated
	// during `Run()`.
	// 本地缓存开始时为空，在 "Run()" 期间被填充和更新。
	//
	// The keys in the Store are of the form namespace/name for namespaced
	// objects, and are simply the name for non-namespaced objects.
	// Clients can use `MetaNamespaceKeyFunc(obj)` to extract the key for
	// a given object, and `SplitMetaNamespaceKey(key)` to split a key
	// into its constituent parts.
	//
	// Every query against the local cache is answered entirely from one
	// snapshot of the cache's state.  Thus, the result of a `List` call
	// will not contain two entries with the same namespace and name.
	// 针对本地缓存的每个查询都完全由缓存状态的一个快照来回答。
	// 因此，"List" 调用的结果不会包含两个具有相同命名空间和名称的条目。
	//
	// A client is identified here by a ResourceEventHandler.  For every
	// update to the SharedInformer's local cache and for every client
	// added before `Run()`, eventually either the SharedInformer is
	// stopped or the client is notified of the update.  A client added
	// after `Run()` starts gets a startup batch of notifications of
	// additions of the objects existing in the cache at the time that
	// client was added; also, for every update to the SharedInformer's
	// local cache after that client was added, eventually either the
	// SharedInformer is stopped or that client is notified of that
	// update.  Client notifications happen after the corresponding cache
	// update and, in the case of a SharedIndexInformer, after the
	// corresponding index updates.  It is possible that additional cache
	// and index updates happen before such a prescribed notification.
	// For a given SharedInformer and client, the notifications are
	// delivered sequentially.  For a given SharedInformer, client, and
	// object ID, the notifications are delivered in order.  Because
	// `ObjectMeta.UID` has no role in identifying objects, it is possible
	// that when (1) object O1 with ID (e.g. namespace and name) X and
	// `ObjectMeta.UID` U1 in the SharedInformer's local cache is deleted
	// and later (2) another object O2 with ID X and ObjectMeta.UID U2 is
	// created the informer's clients are not notified of (1) and (2) but
	// rather are notified only of an update from O1 to O2. Clients that
	// need to detect such cases might do so by comparing the `ObjectMeta.UID`
	// field of the old and the new object in the code that handles update
	// notifications (i.e. `OnUpdate` method of ResourceEventHandler).
	//
	// A client must process each notification promptly; a SharedInformer
	// is not engineered to deal well with a large backlog of
	// notifications to deliver.  Lengthy processing should be passed off
	// to something else, for example through a
	// `client-go/util/workqueue`.
	// Client 必须及时处理每个通知；SharedInformer 不能很好地处理大量积压的通知。
	// 冗长的处理过程应该被传递给其他组件，例如通过 "client-go/util/workqueue"。
	type SharedInformer interface {
		// AddEventHandler adds an event handler to the shared informer using
		// the shared informer's resync period.  Events to a single handler are
		// delivered sequentially, but there is no coordination between
		// different handlers.
		// It returns a registration handle for the handler that can be used to
		// remove the handler again, or to tell if the handler is synced (has
		// seen every item in the initial list).
		// 可以添加自定义的 ResourceEventHandler
		AddEventHandler(handler ResourceEventHandler) (ResourceEventHandlerRegistration, error)
		// AddEventHandlerWithResyncPeriod adds an event handler to the
		// shared informer with the requested resync period; zero means
		// this handler does not care about resyncs.  The resync operation
		// consists of delivering to the handler an update notification
		// for every object in the informer's local cache; it does not add
		// any interactions with the authoritative storage.  Some
		// informers do no resyncs at all, not even for handlers added
		// with a non-zero resyncPeriod.  For an informer that does
		// resyncs, and for each handler that requests resyncs, that
		// informer develops a nominal resync period that is no shorter
		// than the requested period but may be longer.  The actual time
		// between any two resyncs may be longer than the nominal period
		// because the implementation takes time to do work and there may
		// be competing load and scheduling noise.
		// It returns a registration handle for the handler that can be used to remove
		// the handler again and an error if the handler cannot be added.
		// 附带 resync 间隔配置，resyncPeriod 设置为 0 表示不关心 resync
		AddEventHandlerWithResyncPeriod(handler ResourceEventHandler, resyncPeriod time.Duration) (ResourceEventHandlerRegistration, error)
		// RemoveEventHandler removes a formerly added event handler given by
		// its registration handle.
		// This function is guaranteed to be idempotent, and thread-safe.
		RemoveEventHandler(handle ResourceEventHandlerRegistration) error
		// GetStore returns the informer's local cache as a Store.
		// 这里的 Store 指的是 Indexer
		GetStore() Store
		// GetController is deprecated, it does nothing useful
		GetController() Controller
		// Run starts and runs the shared informer, returning after it stops.
		// The informer will be stopped when stopCh is closed.
		// 通过 Run 方法启动
		Run(stopCh <-chan struct{})
		// HasSynced returns true if the shared informer's store has been
		// informed by at least one full LIST of the authoritative state
		// of the informer's object collection.  This is unrelated to "resync".
		//
		// Note that this doesn't tell you if an individual handler is synced!!
		// For that, please call HasSynced on the handle returned by
		// AddEventHandler.
		// 这里和 resync 没有关系，表示 Indexer 至少更新过一次全量的对象
		HasSynced() bool
		// LastSyncResourceVersion is the resource version observed when last synced with the underlying
		// store. The value returned is not synchronized with access to the underlying store and is not
		// thread-safe.
		// 最后一次拿到的 RV
		LastSyncResourceVersion() string

		// The WatchErrorHandler is called whenever ListAndWatch drops the
		// connection with an error. After calling this handler, the informer
		// will backoff and retry.
		//
		// The default implementation looks at the error type and tries to log
		// the error message at an appropriate level.
		//
		// There's only one handler, so if you call this multiple times, last one
		// wins; calling after the informer has been started returns an error.
		//
		// The handler is intended for visibility, not to e.g. pause the consumers.
		// The handler should return quickly - any expensive processing should be
		// offloaded.
		// 用于每次 ListAndWatch 连接断开时回调，主要是日志记录的作用
		SetWatchErrorHandler(handler WatchErrorHandler) error

		// The TransformFunc is called for each object which is about to be stored.
		//
		// This function is intended for you to take the opportunity to
		// remove, transform, or normalize fields. One use case is to strip unused
		// metadata fields out of objects to save on RAM cost.
		//
		// Must be set before starting the informer.
		//
		// Please see the comment on TransformFunc for more details.
		// 用于在对象存储前执行一些操作
		SetTransform(handler TransformFunc) error

		// IsStopped reports whether the informer has already been stopped.
		// Adding event handlers to already stopped informers is not possible.
		// An informer already stopped will never be started again.
		IsStopped() bool
	}
```

**c. sharedIndexInformer结构体的定义**

- `sharedIndexerInformer` 实现 `SharedIndexInformer` 接口，共有3个主要组件，同样在 shared_informer.go 文件中查看代码
	- `indexer Indexer` 带索引的本地 cache
	- `controller Controller` Controller 控制器
		- 使用 ListerWatcher 拉取 objects/notifications，并推送至 DeltaFIFO
		- DeltaFIFO 的 knownObjects，为 sharedIndexerInformer 的 indexer
		- 从 DeltaFIFO 弹出 Deltas 后，通过 sharedIndexInformer.HandleDeltas 进行处理
		- HandleDeltas 的每次调用都是在 DeltaFIFO 加锁的情况下完成的，它依次处理每个Delta
		- 对于每个 Delta，将会更新本地 cache 并将相关通知填充到 sharedProcessor 中
	- `processor *sharedProcessor` 负责将这些通知转发给每个 informer 的客户端
```golang
	// `*sharedIndexInformer` implements SharedIndexInformer and has three
	// main components.  One is an indexed local cache, `indexer Indexer`.
	// The second main component is a Controller that pulls
	// objects/notifications using the ListerWatcher and pushes them into
	// a DeltaFIFO --- whose knownObjects is the informer's local cache
	// --- while concurrently Popping Deltas values from that fifo and
	// processing them with `sharedIndexInformer::HandleDeltas`.  Each
	// invocation of HandleDeltas, which is done with the fifo's lock
	// held, processes each Delta in turn.  For each Delta this both
	// updates the local cache and stuffs the relevant notification into
	// the sharedProcessor.  The third main component is that
	// sharedProcessor, which is responsible for relaying those
	// notifications to each of the informer's clients.
	type sharedIndexInformer struct {
		indexer    Indexer
		controller Controller

		processor             *sharedProcessor
		cacheMutationDetector MutationDetector

		listerWatcher ListerWatcher

		// objectType is an example object of the type this informer is expected to handle. If set, an event
		// with an object with a mismatching type is dropped instead of being delivered to listeners.
		// 表示当前 Informer 期望关注的类型，主要是 GVK 信息
		objectType runtime.Object

		// objectDescription is the description of this informer's objects. This typically defaults to
		objectDescription string

		// resyncCheckPeriod is how often we want the reflector's resync timer to fire so it can call
		// shouldResync to check if any of our listeners need a resync.
		// reflector 的 resync 计时器计时间隔，通知所有的 listener 执行 resync
		resyncCheckPeriod time.Duration
		// defaultEventHandlerResyncPeriod is the default resync period for any handlers added via
		// AddEventHandler (i.e. they don't specify one and just want to use the shared informer's default
		// value).
		defaultEventHandlerResyncPeriod time.Duration
		// clock allows for testability
		clock clock.Clock

		started, stopped bool
		startedLock      sync.Mutex

		// blockDeltas gives a way to stop all event distribution so that a late event handler
		// can safely join the shared informer.
		blockDeltas sync.Mutex

		// Called whenever the ListAndWatch drops the connection with an error.
		watchErrorHandler WatchErrorHandler

		transform TransformFunc
	}
```
这里的 `Indexer`、`Controller`、`ListerWatcher` 等都是熟悉的组件，`sharedProcessor` 在前面已经遇到过，这也是一个需要关注的重点逻辑

**d. sharedIndexInformer的启动**

继续来看 `sharedIndexInformer` 的 `Run()` 方法，其代码在 shared_informer.go 文件中：
```golang
	func (s *sharedIndexInformer) Run(stopCh <-chan struct{}) {
		defer utilruntime.HandleCrash()

		if s.HasStarted() {
			klog.Warningf("The sharedIndexInformer has started, run more than once is not allowed")
			return
		}

		func() {
			s.startedLock.Lock()
			defer s.startedLock.Unlock()

			// 初始化一个 DeltaFIFO
			fifo := NewDeltaFIFOWithOptions(DeltaFIFOOptions{
				KnownObjects:          s.indexer,
				EmitDeltaTypeReplaced: true,
				Transformer:           s.transform,
			})

			cfg := &Config{
				Queue:             fifo,
				ListerWatcher:     s.listerWatcher,
				ObjectType:        s.objectType,
				ObjectDescription: s.objectDescription,
				FullResyncPeriod:  s.resyncCheckPeriod,
				RetryOnError:      false,
				ShouldResync:      s.processor.shouldResync,

				Process:           s.HandleDeltas,
				WatchErrorHandler: s.watchErrorHandler,
			}

			// 通过 Config 创建一个 Controller
			s.controller = New(cfg)
			s.controller.(*controller).clock = s.clock
			s.started = true
		}()

		// Separate stop channel because Processor should be stopped strictly after controller
		processorStopCh := make(chan struct{})
		var wg wait.Group
		defer wg.Wait()              // Wait for Processor to stop
		defer close(processorStopCh) // Tell Processor to stop
		wg.StartWithChannel(processorStopCh, s.cacheMutationDetector.Run)
		wg.StartWithChannel(processorStopCh, s.processor.run)

		defer func() {
			s.startedLock.Lock()
			defer s.startedLock.Unlock()
			s.stopped = true // Don't want any new listeners
		}()
		// func (c *controller) Run(stopCh <-chan struct{})
		s.controller.Run(stopCh)
	}
```

### 3. sharedProcessor对象

`sharedProcessor` 中维护了 `processorListener` 集合，然后分发通知对象到 `listeners`，其代码在 shared_informer.go 中
```golang
	// sharedProcessor has a collection of processorListener and can
	// distribute a notification object to its listeners.  There are two
	// kinds of distribute operations.  The sync distributions go to a
	// subset of the listeners that (a) is recomputed in the occasional
	// calls to shouldResync and (b) every listener is initially put in.
	// The non-sync distributions go to every listener.
	type sharedProcessor struct {
		listenersStarted bool
		listenersLock    sync.RWMutex
		// Map from listeners to whether or not they are currently syncing
		listeners map[*processorListener]bool
		clock     clock.Clock
		wg        wait.Group
	}

	// processorListener relays notifications from a sharedProcessor to
	// one ResourceEventHandler --- using two goroutines, two unbuffered
	// channels, and an unbounded ring buffer.  The `add(notification)`
	// function sends the given notification to `addCh`.  One goroutine
	// runs `pop()`, which pumps notifications from `addCh` to `nextCh`
	// using storage in the ring buffer while `nextCh` is not keeping up.
	// Another goroutine runs `run()`, which receives notifications from
	// `nextCh` and synchronously invokes the appropriate handler method.
	//
	// processorListener also keeps track of the adjusted requested resync
	// period of the listener.
	type processorListener struct {
		nextCh chan interface{}
		addCh  chan interface{}

		// 核心属性
		handler ResourceEventHandler

		syncTracker *synctrack.SingleFileTracker

		// pendingNotifications is an unbounded ring buffer that holds all notifications not yet distributed.
		// There is one per listener, but a failing/stalled listener will have infinite pendingNotifications
		// added until we OOM.
		// TODO: This is no worse than before, since reflectors were backed by unbounded DeltaFIFOs, but
		// we should try to do something better.
		pendingNotifications buffer.RingGrowing

		// requestedResyncPeriod is how frequently the listener wants a
		// full resync from the shared informer, but modified by two
		// adjustments.  One is imposing a lower bound,
		// `minimumResyncPeriod`.  The other is another lower bound, the
		// sharedIndexInformer's `resyncCheckPeriod`, that is imposed (a) only
		// in AddEventHandlerWithResyncPeriod invocations made after the
		// sharedIndexInformer starts and (b) only if the informer does
		// resyncs at all.
		requestedResyncPeriod time.Duration
		// resyncPeriod is the threshold that will be used in the logic
		// for this listener.  This value differs from
		// requestedResyncPeriod only when the sharedIndexInformer does
		// not do resyncs, in which case the value here is zero.  The
		// actual time between resyncs depends on when the
		// sharedProcessor's `shouldResync` function is invoked and when
		// the sharedIndexInformer processes `Sync` type Delta objects.
		resyncPeriod time.Duration
		// nextResync is the earliest time the listener should get a full resync
		nextResync time.Time
		// resyncLock guards access to resyncPeriod and nextResync
		resyncLock sync.Mutex
	}
```
可以看到 `processorListener` 中有一个 `ResourceEventHandler`，这是我们认识的组件。

- `processorListener` 有三个主要方法
	+ `run()` 从 nextCh 中拿通知，然后根据其类型去调用 ResourceEventHandler 相应的 OnAdd()/OnUpdate()/OnDelete() 方法
	+ `add(notification interface{})`
	+ `pop()`
```golang
	// 方法 run()
	// 这里的逻辑很清晰，从 nextCh 中拿通知，然后根据其类型去调用 ResourceEventHandler 相应的 OnAdd()/OnUpdate()/OnDelete() 方法
	func (p *processorListener) run() {
		// this call blocks until the channel is closed.  When a panic happens during the notification
		// we will catch it, **the offending item will be skipped!**, and after a short delay (one second)
		// the next notification will be attempted.  This is usually better than the alternative of never
		// delivering again.
		stopCh := make(chan struct{})
		wait.Until(func() {
			for next := range p.nextCh {
				switch notification := next.(type) {
				case updateNotification:
					p.handler.OnUpdate(notification.oldObj, notification.newObj)
				case addNotification:
					p.handler.OnAdd(notification.newObj, notification.isInInitialList)
					if notification.isInInitialList {
						p.syncTracker.Finished()
					}
				case deleteNotification:
					p.handler.OnDelete(notification.oldObj)
				default:
					utilruntime.HandleError(fmt.Errorf("unrecognized notification: %T", next))
				}
			}
			// the only way to get here is if the p.nextCh is empty and closed
			close(stopCh)
		}, 1*time.Second, stopCh)
	}

	// 方法 add()
	func (p *processorListener) add(notification interface{}) {
		if a, ok := notification.(addNotification); ok && a.isInInitialList {
			p.syncTracker.Start()
		}
		// 将通知放到 addCh 中，下面的 pop() 方法中先执行到的 case 是第二个
		p.addCh <- notification
	}

	// 方法 pop()
	func (p *processorListener) pop() {
		defer utilruntime.HandleCrash()
		defer close(p.nextCh) // Tell .run() to stop

		var nextCh chan<- interface{}
		var notification interface{}
		for {
			select {
			// 下面将获取到的通知添加到 nextCh 中，供 run() 方法中消费
			case nextCh <- notification:
				// 分发通知
				// Notification dispatched
				var ok bool
				// 从 pendingNotifications 中消费通知，生产者在下面的 case 中
				notification, ok = p.pendingNotifications.ReadOne()
				if !ok { // Nothing to pop
					nextCh = nil // Disable this select case
				}
			// 逻辑从这里开始，从 addCh 中提取通知
			case notificationToAdd, ok := <-p.addCh:
				if !ok {
					return
				}
				if notification == nil { // No notification to pop (and pendingNotifications is empty)
					// Optimize the case - skip adding to pendingNotifications
					notification = notificationToAdd
					nextCh = p.nextCh
				} else { // There is already a notification waiting to be dispatched
					// 新添加到通知丢到 pendingNotifications 中
					p.pendingNotifications.WriteOne(notificationToAdd)
				}
			}
		}
	}
```
可以看到 `processorListener` 提供了一定的缓冲机制来接收 `notification`，然后去消费这些 `notification` 调用 `ResourceEventHandler` 相关方法。

- 接下来继续查看 `sharedProcessor` 的几种主要方法
	+ `addListener()` 调用前面 `listener` 的 `run()` 和 `pop()` 方法
	+ `distribute()` 调用 `sharedProcessor` 内部维护的所有 `listener` 的 `add()` 方法
	+ `run()` 和前面 `addListener()`方法类似，也就是调用`listener` 的 `run()` 和 `pop()` 方法
```golang
	func (p *sharedProcessor) addListener(listener *processorListener) ResourceEventHandlerRegistration {
		p.listenersLock.Lock()
		defer p.listenersLock.Unlock()

		if p.listeners == nil {
			p.listeners = make(map[*processorListener]bool)
		}

		p.listeners[listener] = true

		if p.listenersStarted {
			p.wg.Start(listener.run)
			p.wg.Start(listener.pop)
		}

		return listener
	}

	func (p *sharedProcessor) distribute(obj interface{}, sync bool) {
		p.listenersLock.RLock()
		defer p.listenersLock.RUnlock()

		for listener, isSyncing := range p.listeners {
			switch {
			case !sync:
				// non-sync messages are delivered to every listener
				listener.add(obj)
			case isSyncing:
				// sync messages are delivered to every syncing listener
				listener.add(obj)
			default:
				// skipping a sync obj for a non-syncing listener
			}
		}
	}

	func (p *sharedProcessor) run(stopCh <-chan struct{}) {
		func() {
			p.listenersLock.RLock()
			defer p.listenersLock.RUnlock()
			for listener := range p.listeners {
				p.wg.Start(listener.run)
				p.wg.Start(listener.pop)
			}
			p.listenersStarted = true
		}()
		<-stopCh

		p.listenersLock.Lock()
		defer p.listenersLock.Unlock()
		for listener := range p.listeners {
			close(listener.addCh) // Tell .pop() to stop. .pop() will tell .run() to stop
		}

		// Wipe out list of listeners since they are now closed
		// (processorListener cannot be re-used)
		p.listeners = nil

		// Reset to false since no listeners are running
		p.listenersStarted = false

		p.wg.Wait() // Wait for all .pop() and .run() to stop
	}
```
至此，基本就分析完 `sharedProcessor`、`SharedIndexInformer` 的能力和逻辑了。

### 4. 关于SharedInformerFactory

**a. SharedInformerFactory的定义**

`SharedInformerFactory` 接口定义在 informers/factory.go 文件中：
```golang
	// SharedInformerFactory provides shared informers for resources in all known
	// API group versions.
	//
	// It is typically used like this:
	//
	//	ctx, cancel := context.Background()
	//	defer cancel()
	//	factory := NewSharedInformerFactory(client, resyncPeriod)
	//	defer factory.WaitForStop()    // Returns immediately if nothing was started.
	//	genericInformer := factory.ForResource(resource)
	//	typedInformer := factory.SomeAPIGroup().V1().SomeType()
	//	factory.Start(ctx.Done())          // Start processing these informers.
	//	synced := factory.WaitForCacheSync(ctx.Done())
	//	for v, ok := range synced {
	//	    if !ok {
	//	        fmt.Fprintf(os.Stderr, "caches failed to sync: %v", v)
	//	        return
	//	    }
	//	}
	//
	//	// Creating informers can also be created after Start, but then
	//	// Start must be called again:
	//	anotherGenericInformer := factory.ForResource(resource)
	//	factory.Start(ctx.Done())
	type SharedInformerFactory interface {
		internalinterfaces.SharedInformerFactory

		// Start initializes all requested informers. They are handled in goroutines
		// which run until the stop channel gets closed.
		Start(stopCh <-chan struct{})

		// Shutdown marks a factory as shutting down. At that point no new
		// informers can be started anymore and Start will return without
		// doing anything.
		//
		// In addition, Shutdown blocks until all goroutines have terminated. For that
		// to happen, the close channel(s) that they were started with must be closed,
		// either before Shutdown gets called or while it is waiting.
		//
		// Shutdown may be called multiple times, even concurrently. All such calls will
		// block until all goroutines have terminated.
		Shutdown()

		// WaitForCacheSync blocks until all started informers' caches were synced
		// or the stop channel gets closed.
		WaitForCacheSync(stopCh <-chan struct{}) map[reflect.Type]bool

		// ForResource gives generic access to a shared informer of the matching type.
		ForResource(resource schema.GroupVersionResource) (GenericInformer, error)

		// InformerFor returns the SharedIndexInformer for obj using an internal
		// client.
		InformerFor(obj runtime.Object, newFunc internalinterfaces.NewInformerFunc) cache.SharedIndexInformer

		Admissionregistration() admissionregistration.Interface
		Internal() apiserverinternal.Interface
		Apps() apps.Interface
		Autoscaling() autoscaling.Interface
		Batch() batch.Interface
		Certificates() certificates.Interface
		Coordination() coordination.Interface
		Core() core.Interface
		Discovery() discovery.Interface
		Events() events.Interface
		Extensions() extensions.Interface
		Flowcontrol() flowcontrol.Interface
		Networking() networking.Interface
		Node() node.Interface
		Policy() policy.Interface
		Rbac() rbac.Interface
		Resource() resource.Interface
		Scheduling() scheduling.Interface
		Storage() storage.Interface
	}

	// 首先看下 internalinterfaces.SharedInformerFactory 接口，在 internalinterfaces/factory_interfaces.go 中
	// SharedInformerFactory a small interface to allow for adding an informer without an import cycle
	type SharedInformerFactory interface {
		Start(stopCh <-chan struct{})
		InformerFor(obj runtime.Object, newFunc NewInformerFunc) cache.SharedIndexInformer
	}

	// 接着了解下 ForResource ，这里接收了一个 GVR，返回了一个 GenericInformer
	// ForResource gives generic access to a shared informer of the matching type
	// TODO extend this to unknown resources with a client pool
	func (f *sharedInformerFactory) ForResource(resource schema.GroupVersionResource) (GenericInformer, error) {
		switch resource {
		// Group=admissionregistration.k8s.io, Version=v1
		case v1.SchemeGroupVersion.WithResource("mutatingwebhookconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1().MutatingWebhookConfigurations().Informer()}, nil
		case v1.SchemeGroupVersion.WithResource("validatingwebhookconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1().ValidatingWebhookConfigurations().Informer()}, nil

			// Group=admissionregistration.k8s.io, Version=v1alpha1
		case v1alpha1.SchemeGroupVersion.WithResource("validatingadmissionpolicies"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1alpha1().ValidatingAdmissionPolicies().Informer()}, nil
		case v1alpha1.SchemeGroupVersion.WithResource("validatingadmissionpolicybindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1alpha1().ValidatingAdmissionPolicyBindings().Informer()}, nil

			// Group=admissionregistration.k8s.io, Version=v1beta1
		case v1beta1.SchemeGroupVersion.WithResource("mutatingwebhookconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1beta1().MutatingWebhookConfigurations().Informer()}, nil
		case v1beta1.SchemeGroupVersion.WithResource("validatingwebhookconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Admissionregistration().V1beta1().ValidatingWebhookConfigurations().Informer()}, nil

			// Group=apps, Version=v1
		case appsv1.SchemeGroupVersion.WithResource("controllerrevisions"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1().ControllerRevisions().Informer()}, nil
		case appsv1.SchemeGroupVersion.WithResource("daemonsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1().DaemonSets().Informer()}, nil
		case appsv1.SchemeGroupVersion.WithResource("deployments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1().Deployments().Informer()}, nil
		case appsv1.SchemeGroupVersion.WithResource("replicasets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1().ReplicaSets().Informer()}, nil
		case appsv1.SchemeGroupVersion.WithResource("statefulsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1().StatefulSets().Informer()}, nil

			// Group=apps, Version=v1beta1
		case appsv1beta1.SchemeGroupVersion.WithResource("controllerrevisions"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta1().ControllerRevisions().Informer()}, nil
		case appsv1beta1.SchemeGroupVersion.WithResource("deployments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta1().Deployments().Informer()}, nil
		case appsv1beta1.SchemeGroupVersion.WithResource("statefulsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta1().StatefulSets().Informer()}, nil

			// Group=apps, Version=v1beta2
		case v1beta2.SchemeGroupVersion.WithResource("controllerrevisions"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta2().ControllerRevisions().Informer()}, nil
		case v1beta2.SchemeGroupVersion.WithResource("daemonsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta2().DaemonSets().Informer()}, nil
		case v1beta2.SchemeGroupVersion.WithResource("deployments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta2().Deployments().Informer()}, nil
		case v1beta2.SchemeGroupVersion.WithResource("replicasets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta2().ReplicaSets().Informer()}, nil
		case v1beta2.SchemeGroupVersion.WithResource("statefulsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Apps().V1beta2().StatefulSets().Informer()}, nil

			// Group=autoscaling, Version=v1
		case autoscalingv1.SchemeGroupVersion.WithResource("horizontalpodautoscalers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Autoscaling().V1().HorizontalPodAutoscalers().Informer()}, nil

			// Group=autoscaling, Version=v2
		case v2.SchemeGroupVersion.WithResource("horizontalpodautoscalers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Autoscaling().V2().HorizontalPodAutoscalers().Informer()}, nil

			// Group=autoscaling, Version=v2beta1
		case v2beta1.SchemeGroupVersion.WithResource("horizontalpodautoscalers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Autoscaling().V2beta1().HorizontalPodAutoscalers().Informer()}, nil

			// Group=autoscaling, Version=v2beta2
		case v2beta2.SchemeGroupVersion.WithResource("horizontalpodautoscalers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Autoscaling().V2beta2().HorizontalPodAutoscalers().Informer()}, nil

			// Group=batch, Version=v1
		case batchv1.SchemeGroupVersion.WithResource("cronjobs"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Batch().V1().CronJobs().Informer()}, nil
		case batchv1.SchemeGroupVersion.WithResource("jobs"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Batch().V1().Jobs().Informer()}, nil

			// Group=batch, Version=v1beta1
		case batchv1beta1.SchemeGroupVersion.WithResource("cronjobs"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Batch().V1beta1().CronJobs().Informer()}, nil

			// Group=certificates.k8s.io, Version=v1
		case certificatesv1.SchemeGroupVersion.WithResource("certificatesigningrequests"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Certificates().V1().CertificateSigningRequests().Informer()}, nil

			// Group=certificates.k8s.io, Version=v1alpha1
		case certificatesv1alpha1.SchemeGroupVersion.WithResource("clustertrustbundles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Certificates().V1alpha1().ClusterTrustBundles().Informer()}, nil

			// Group=certificates.k8s.io, Version=v1beta1
		case certificatesv1beta1.SchemeGroupVersion.WithResource("certificatesigningrequests"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Certificates().V1beta1().CertificateSigningRequests().Informer()}, nil

			// Group=coordination.k8s.io, Version=v1
		case coordinationv1.SchemeGroupVersion.WithResource("leases"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Coordination().V1().Leases().Informer()}, nil

			// Group=coordination.k8s.io, Version=v1beta1
		case coordinationv1beta1.SchemeGroupVersion.WithResource("leases"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Coordination().V1beta1().Leases().Informer()}, nil

			// Group=core, Version=v1
		case corev1.SchemeGroupVersion.WithResource("componentstatuses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().ComponentStatuses().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("configmaps"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().ConfigMaps().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("endpoints"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Endpoints().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("events"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Events().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("limitranges"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().LimitRanges().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("namespaces"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Namespaces().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("nodes"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Nodes().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("persistentvolumes"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().PersistentVolumes().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("persistentvolumeclaims"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().PersistentVolumeClaims().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("pods"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Pods().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("podtemplates"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().PodTemplates().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("replicationcontrollers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().ReplicationControllers().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("resourcequotas"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().ResourceQuotas().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("secrets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Secrets().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("services"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().Services().Informer()}, nil
		case corev1.SchemeGroupVersion.WithResource("serviceaccounts"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Core().V1().ServiceAccounts().Informer()}, nil

			// Group=discovery.k8s.io, Version=v1
		case discoveryv1.SchemeGroupVersion.WithResource("endpointslices"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Discovery().V1().EndpointSlices().Informer()}, nil

			// Group=discovery.k8s.io, Version=v1beta1
		case discoveryv1beta1.SchemeGroupVersion.WithResource("endpointslices"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Discovery().V1beta1().EndpointSlices().Informer()}, nil

			// Group=events.k8s.io, Version=v1
		case eventsv1.SchemeGroupVersion.WithResource("events"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Events().V1().Events().Informer()}, nil

			// Group=events.k8s.io, Version=v1beta1
		case eventsv1beta1.SchemeGroupVersion.WithResource("events"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Events().V1beta1().Events().Informer()}, nil

			// Group=extensions, Version=v1beta1
		case extensionsv1beta1.SchemeGroupVersion.WithResource("daemonsets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Extensions().V1beta1().DaemonSets().Informer()}, nil
		case extensionsv1beta1.SchemeGroupVersion.WithResource("deployments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Extensions().V1beta1().Deployments().Informer()}, nil
		case extensionsv1beta1.SchemeGroupVersion.WithResource("ingresses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Extensions().V1beta1().Ingresses().Informer()}, nil
		case extensionsv1beta1.SchemeGroupVersion.WithResource("networkpolicies"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Extensions().V1beta1().NetworkPolicies().Informer()}, nil
		case extensionsv1beta1.SchemeGroupVersion.WithResource("replicasets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Extensions().V1beta1().ReplicaSets().Informer()}, nil

			// Group=flowcontrol.apiserver.k8s.io, Version=v1alpha1
		case flowcontrolv1alpha1.SchemeGroupVersion.WithResource("flowschemas"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1alpha1().FlowSchemas().Informer()}, nil
		case flowcontrolv1alpha1.SchemeGroupVersion.WithResource("prioritylevelconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1alpha1().PriorityLevelConfigurations().Informer()}, nil

			// Group=flowcontrol.apiserver.k8s.io, Version=v1beta1
		case flowcontrolv1beta1.SchemeGroupVersion.WithResource("flowschemas"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta1().FlowSchemas().Informer()}, nil
		case flowcontrolv1beta1.SchemeGroupVersion.WithResource("prioritylevelconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta1().PriorityLevelConfigurations().Informer()}, nil

			// Group=flowcontrol.apiserver.k8s.io, Version=v1beta2
		case flowcontrolv1beta2.SchemeGroupVersion.WithResource("flowschemas"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta2().FlowSchemas().Informer()}, nil
		case flowcontrolv1beta2.SchemeGroupVersion.WithResource("prioritylevelconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta2().PriorityLevelConfigurations().Informer()}, nil

			// Group=flowcontrol.apiserver.k8s.io, Version=v1beta3
		case v1beta3.SchemeGroupVersion.WithResource("flowschemas"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta3().FlowSchemas().Informer()}, nil
		case v1beta3.SchemeGroupVersion.WithResource("prioritylevelconfigurations"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Flowcontrol().V1beta3().PriorityLevelConfigurations().Informer()}, nil

			// Group=internal.apiserver.k8s.io, Version=v1alpha1
		case apiserverinternalv1alpha1.SchemeGroupVersion.WithResource("storageversions"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Internal().V1alpha1().StorageVersions().Informer()}, nil

			// Group=networking.k8s.io, Version=v1
		case networkingv1.SchemeGroupVersion.WithResource("ingresses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1().Ingresses().Informer()}, nil
		case networkingv1.SchemeGroupVersion.WithResource("ingressclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1().IngressClasses().Informer()}, nil
		case networkingv1.SchemeGroupVersion.WithResource("networkpolicies"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1().NetworkPolicies().Informer()}, nil

			// Group=networking.k8s.io, Version=v1alpha1
		case networkingv1alpha1.SchemeGroupVersion.WithResource("clustercidrs"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1alpha1().ClusterCIDRs().Informer()}, nil
		case networkingv1alpha1.SchemeGroupVersion.WithResource("ipaddresses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1alpha1().IPAddresses().Informer()}, nil

			// Group=networking.k8s.io, Version=v1beta1
		case networkingv1beta1.SchemeGroupVersion.WithResource("ingresses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1beta1().Ingresses().Informer()}, nil
		case networkingv1beta1.SchemeGroupVersion.WithResource("ingressclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Networking().V1beta1().IngressClasses().Informer()}, nil

			// Group=node.k8s.io, Version=v1
		case nodev1.SchemeGroupVersion.WithResource("runtimeclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Node().V1().RuntimeClasses().Informer()}, nil

			// Group=node.k8s.io, Version=v1alpha1
		case nodev1alpha1.SchemeGroupVersion.WithResource("runtimeclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Node().V1alpha1().RuntimeClasses().Informer()}, nil

			// Group=node.k8s.io, Version=v1beta1
		case nodev1beta1.SchemeGroupVersion.WithResource("runtimeclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Node().V1beta1().RuntimeClasses().Informer()}, nil

			// Group=policy, Version=v1
		case policyv1.SchemeGroupVersion.WithResource("poddisruptionbudgets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Policy().V1().PodDisruptionBudgets().Informer()}, nil

			// Group=policy, Version=v1beta1
		case policyv1beta1.SchemeGroupVersion.WithResource("poddisruptionbudgets"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Policy().V1beta1().PodDisruptionBudgets().Informer()}, nil
		case policyv1beta1.SchemeGroupVersion.WithResource("podsecuritypolicies"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Policy().V1beta1().PodSecurityPolicies().Informer()}, nil

			// Group=rbac.authorization.k8s.io, Version=v1
		case rbacv1.SchemeGroupVersion.WithResource("clusterroles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1().ClusterRoles().Informer()}, nil
		case rbacv1.SchemeGroupVersion.WithResource("clusterrolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1().ClusterRoleBindings().Informer()}, nil
		case rbacv1.SchemeGroupVersion.WithResource("roles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1().Roles().Informer()}, nil
		case rbacv1.SchemeGroupVersion.WithResource("rolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1().RoleBindings().Informer()}, nil

			// Group=rbac.authorization.k8s.io, Version=v1alpha1
		case rbacv1alpha1.SchemeGroupVersion.WithResource("clusterroles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1alpha1().ClusterRoles().Informer()}, nil
		case rbacv1alpha1.SchemeGroupVersion.WithResource("clusterrolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1alpha1().ClusterRoleBindings().Informer()}, nil
		case rbacv1alpha1.SchemeGroupVersion.WithResource("roles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1alpha1().Roles().Informer()}, nil
		case rbacv1alpha1.SchemeGroupVersion.WithResource("rolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1alpha1().RoleBindings().Informer()}, nil

			// Group=rbac.authorization.k8s.io, Version=v1beta1
		case rbacv1beta1.SchemeGroupVersion.WithResource("clusterroles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1beta1().ClusterRoles().Informer()}, nil
		case rbacv1beta1.SchemeGroupVersion.WithResource("clusterrolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1beta1().ClusterRoleBindings().Informer()}, nil
		case rbacv1beta1.SchemeGroupVersion.WithResource("roles"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1beta1().Roles().Informer()}, nil
		case rbacv1beta1.SchemeGroupVersion.WithResource("rolebindings"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Rbac().V1beta1().RoleBindings().Informer()}, nil

			// Group=resource.k8s.io, Version=v1alpha2
		case v1alpha2.SchemeGroupVersion.WithResource("podschedulingcontexts"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Resource().V1alpha2().PodSchedulingContexts().Informer()}, nil
		case v1alpha2.SchemeGroupVersion.WithResource("resourceclaims"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Resource().V1alpha2().ResourceClaims().Informer()}, nil
		case v1alpha2.SchemeGroupVersion.WithResource("resourceclaimtemplates"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Resource().V1alpha2().ResourceClaimTemplates().Informer()}, nil
		case v1alpha2.SchemeGroupVersion.WithResource("resourceclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Resource().V1alpha2().ResourceClasses().Informer()}, nil

			// Group=scheduling.k8s.io, Version=v1
		case schedulingv1.SchemeGroupVersion.WithResource("priorityclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Scheduling().V1().PriorityClasses().Informer()}, nil

			// Group=scheduling.k8s.io, Version=v1alpha1
		case schedulingv1alpha1.SchemeGroupVersion.WithResource("priorityclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Scheduling().V1alpha1().PriorityClasses().Informer()}, nil

			// Group=scheduling.k8s.io, Version=v1beta1
		case schedulingv1beta1.SchemeGroupVersion.WithResource("priorityclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Scheduling().V1beta1().PriorityClasses().Informer()}, nil

			// Group=storage.k8s.io, Version=v1
		case storagev1.SchemeGroupVersion.WithResource("csidrivers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1().CSIDrivers().Informer()}, nil
		case storagev1.SchemeGroupVersion.WithResource("csinodes"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1().CSINodes().Informer()}, nil
		case storagev1.SchemeGroupVersion.WithResource("csistoragecapacities"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1().CSIStorageCapacities().Informer()}, nil
		case storagev1.SchemeGroupVersion.WithResource("storageclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1().StorageClasses().Informer()}, nil
		case storagev1.SchemeGroupVersion.WithResource("volumeattachments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1().VolumeAttachments().Informer()}, nil

			// Group=storage.k8s.io, Version=v1alpha1
		case storagev1alpha1.SchemeGroupVersion.WithResource("csistoragecapacities"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1alpha1().CSIStorageCapacities().Informer()}, nil
		case storagev1alpha1.SchemeGroupVersion.WithResource("volumeattachments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1alpha1().VolumeAttachments().Informer()}, nil

			// Group=storage.k8s.io, Version=v1beta1
		case storagev1beta1.SchemeGroupVersion.WithResource("csidrivers"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1beta1().CSIDrivers().Informer()}, nil
		case storagev1beta1.SchemeGroupVersion.WithResource("csinodes"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1beta1().CSINodes().Informer()}, nil
		case storagev1beta1.SchemeGroupVersion.WithResource("csistoragecapacities"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1beta1().CSIStorageCapacities().Informer()}, nil
		case storagev1beta1.SchemeGroupVersion.WithResource("storageclasses"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1beta1().StorageClasses().Informer()}, nil
		case storagev1beta1.SchemeGroupVersion.WithResource("volumeattachments"):
			return &genericInformer{resource: resource.GroupResource(), informer: f.Storage().V1beta1().VolumeAttachments().Informer()}, nil

		}

		return nil, fmt.Errorf("no informer found for %v", resource)
	}

	// GenericInformer is type of SharedIndexInformer which will locate and delegate to other
	// sharedInformers based on type
	type GenericInformer interface {
		Informer() cache.SharedIndexInformer
		Lister() cache.GenericLister
	}

	// GenericLister is a lister skin on a generic Indexer
	type GenericLister interface {
		// List will return all objects across namespaces
		List(selector labels.Selector) (ret []runtime.Object, err error)
		// Get will attempt to retrieve assuming that name==key
		Get(name string) (runtime.Object, error)
		// ByNamespace will give you a GenericNamespaceLister for one namespace
		ByNamespace(namespace string) GenericNamespaceLister
	}

	// 最后看 SharedInformerFactory 接口剩下的这部分，一大堆相似的方法
	// 以 "Apps() apps.Interface" 为例，在apps/interface.go中
	// Interface provides access to each of this group's versions.
	type Interface interface {
		// V1 provides access to shared informers for resources in V1.
		V1() v1.Interface
		// V1beta1 provides access to shared informers for resources in V1beta1.
		V1beta1() v1beta1.Interface
		// V1beta2 provides access to shared informers for resources in V1beta2.
		V1beta2() v1beta2.Interface
	}

	// v1.Interface 在 apps/v1/interface.go 中
	// Interface provides access to all the informers in this group version.
	type Interface interface {
		// ControllerRevisions returns a ControllerRevisionInformer.
		ControllerRevisions() ControllerRevisionInformer
		// DaemonSets returns a DaemonSetInformer.
		DaemonSets() DaemonSetInformer
		// Deployments returns a DeploymentInformer.
		Deployments() DeploymentInformer
		// ReplicaSets returns a ReplicaSetInformer.
		ReplicaSets() ReplicaSetInformer
		// StatefulSets returns a StatefulSetInformer.
		StatefulSets() StatefulSetInformer
	}

	// DeploymentInformer 接口，在 apps/v1/deployment.go 中
	// DeploymentInformer provides access to a shared informer and lister for
	// Deployments.
	type DeploymentInformer interface {
		Informer() cache.SharedIndexInformer
		Lister() v1.DeploymentLister
	}

	// DeploymentLister helps list Deployments.
	// All objects returned here must be treated as read-only.
	type DeploymentLister interface {
		// List lists all Deployments in the indexer.
		// Objects returned here must be treated as read-only.
		List(selector labels.Selector) (ret []*v1.Deployment, err error)
		// Deployments returns an object that can list and get Deployments.
		Deployments(namespace string) DeploymentNamespaceLister
		DeploymentListerExpansion
	}
```
现在也就不难理解 `SharedInformerFactory` 的作用了，它提供了所有 `API group-version` 的资源对应的 `SharedIndexInformer`。

而前面引用的 sample-controller 中的这行代码 `kubeInformerFactory.Apps().V1().Deployments()`，通过其可以拿到一个 Deployment 资源对应的 `SharedIndexInformer`。

**b. SharedInformerFactory的初始化**

继续来看 `NewSharedInformerFactory` 的逻辑，其代码在 factory.go 中：
```golang
	// NewSharedInformerFactory constructs a new instance of sharedInformerFactory for all namespaces.
	func NewSharedInformerFactory(client kubernetes.Interface, defaultResync time.Duration) SharedInformerFactory {
		return NewSharedInformerFactoryWithOptions(client, defaultResync)
	}

	// NewFilteredSharedInformerFactory constructs a new instance of sharedInformerFactory.
	// Listers obtained via this SharedInformerFactory will be subject to the same filters
	// as specified here.
	// Deprecated: Please use NewSharedInformerFactoryWithOptions instead
	func NewFilteredSharedInformerFactory(client kubernetes.Interface, defaultResync time.Duration, namespace string, tweakListOptions internalinterfaces.TweakListOptionsFunc) SharedInformerFactory {
		return NewSharedInformerFactoryWithOptions(client, defaultResync, WithNamespace(namespace), WithTweakListOptions(tweakListOptions))
	}

	// NewSharedInformerFactoryWithOptions constructs a new instance of a SharedInformerFactory with additional options.
	func NewSharedInformerFactoryWithOptions(client kubernetes.Interface, defaultResync time.Duration, options ...SharedInformerOption) SharedInformerFactory {
		factory := &sharedInformerFactory{
			client:           client,
			namespace:        v1.NamespaceAll, // 空字符串 const NamespaceAll = ""
			defaultResync:    defaultResync,
			// 可以存放不同类型的 SharedIndexInformer
			informers:        make(map[reflect.Type]cache.SharedIndexInformer),
			startedInformers: make(map[reflect.Type]bool),
			customResync:     make(map[reflect.Type]time.Duration),
		}

		// Apply all options
		for _, opt := range options {
			factory = opt(factory)
		}

		return factory
	}

	// SharedInformerOption defines the functional option type for SharedInformerFactory.
	type SharedInformerOption func(*sharedInformerFactory) *sharedInformerFactory

	type sharedInformerFactory struct {
		client           kubernetes.Interface
		namespace        string
		tweakListOptions internalinterfaces.TweakListOptionsFunc
		lock             sync.Mutex
		defaultResync    time.Duration
		customResync     map[reflect.Type]time.Duration

		informers map[reflect.Type]cache.SharedIndexInformer
		// startedInformers is used for tracking which informers have been started.
		// This allows Start() to be called multiple times safely.
		startedInformers map[reflect.Type]bool
		// wg tracks how many goroutines were started.
		wg sync.WaitGroup
		// shuttingDown is true when Shutdown has been called. It may still be running
		// because it needs to wait for goroutines.
		shuttingDown bool
	}
```

**c. SharedInformerFactory的启动过程**

最后查看 `SharedInformerFactory` 是如何启动的，其 `Start()` 方法同样位于 factory.go 源文件中：
```golang
	func (f *sharedInformerFactory) Start(stopCh <-chan struct{}) {
		f.lock.Lock()
		defer f.lock.Unlock()

		if f.shuttingDown {
			return
		}

		for informerType, informer := range f.informers {
			// 同类型只会调用一次
			if !f.startedInformers[informerType] {
				f.wg.Add(1)
				// We need a new variable in each loop iteration,
				// otherwise the goroutine would use the loop variable
				// and that keeps changing.
				informer := informer
				go func() {
					defer f.wg.Done()
					informer.Run(stopCh) // 最后的入口
				}()
				f.startedInformers[informerType] = true
			}
		}
	}
```

### 5. 小结

本文从一个基础 Informer-Controller 开始介绍，先分析了 `Controller` 的能力，其通过构造 `Reflector` 并启动从而能够获取指定类型资源的"更新"事件，然后通过事件构造 `Delta` 放到 `DeltaFIFO` 中，进而在 `processLoop` 中从 `DeltaFIFO` 里 pop `Deltas` 来处理，一方面将对象通过 `Indexer` 同步到本地 cache (也就是一个 `ThreadSafeStore` )，另一方面调用 `ProcessFunc` 来处理这些 `Delta`。

然后 `SharedIndexInformer` 提供了构造 `Controller` 的能力，通过 `HandleDeltas()` 方法实现上面提到的 `ProcessFunc`，同时还引入了 `sharedProcessor` 在 `HandleDeltas()` 中用于事件通知的处理。`sharedProcessor` 分发事件通知时，接收方是内部继续抽象出来的 `processorListener`，在 `processorListener` 中完成了 `ResourceEventHandler` 回调函数的具体调用。

最后 `SharedInformerFactory` 又进一步封装了提供所有 API 资源对应的 `SharedIndexInformer` 的能力。也就是说一个 `SharedIndexInformer` 可以处理一种类型的资源，比如 Deployment 或者 Pod 等，而通过 `SharedInformerFactory` 可以轻松构造任意已知类型的 `SharedIndexInformer`。另外，这里用到了 `ClientSet` 提供的访问所有 API 资源的能力，通过它也就能够完整实现整套 `Informer` 程序逻辑了。
