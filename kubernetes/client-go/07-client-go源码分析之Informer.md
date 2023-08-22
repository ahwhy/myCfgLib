# client-go 源码分析之 Informer

## 一、Client-go 源码分析

### 1. client-go 源码概览

client-go项目 是与 kube-apiserver 通信的 clients 的具体实现，其中包含很多相关工具包，例如 `kubernetes`包 就包含与 Kubernetes API 通信的各种 ClientSet，而 `tools/cache`包 则包含很多强大的编写控制器相关的组件。

所以接下来我们以自定义控制器的底层实现原理为线索，来分析client-go中相关模块的源码实现。

如图所示，我们在编写自定义控制器的过程中大致依赖于如下组件，其中圆形的是自定义控制器中需要编码的部分，其他椭圆和圆角矩形的是client-go提供的一些"工具"。

![编写自定义控制器依赖的组件](./images/编写自定义控制器依赖的组件.jpg)

- client-go的源码入口在Kubernetes项目的 `staging/src/k8s.io/client-go` 中，先整体查看上面涉及的相关模块，然后逐个深入分析其实现。
  + Reflector：Reflector 从apiserver监听(watch)特定类型的资源，拿到变更通知后，将其丢到 DeltaFIFO队列 中。
  + Informer：Informer 从 DeltaFIFO 中弹出(pop)相应对象，然后通过 Indexer 将对象和索引丢到 本地cache中，再触发相应的事件处理函数(Resource Event Handlers)。
  + Indexer：Indexer 主要提供一个对象根据一定条件检索的能力，典型的实现是通过 namespace/name 来构造key，通过 Thread Safe Store 来存储对象。
  + WorkQueue：WorkQueue 一般使用的是延时队列实现，在Resource Event Handlers中会完成将对象的key放入WorkQueue的过程，然后在自己的逻辑代码里从WorkQueue中消费这些key。
  + ClientSet：ClientSet 提供的是资源的CURD能力，与apiserver交互。
  + Resource Event Handlers：一般在 Resource Event Handlers 中添加一些简单的过滤功能，判断哪些对象需要加到WorkQueue中进一步处理，对于需要加到WorkQueue中的对象，就提取其key，然后入队。
  + Worker：Worker指的是我们自己的业务代码处理过程，在这里可以直接收到WorkQueue中的任务，可以通过Indexer从本地缓存检索对象，通过ClientSet实现对象的增、删、改、查逻辑。


## 二、Client-go Informer

Informer 这个词的出镜率很高，与 `Reflector`、`WorkQueue` 等组件不同，`Informer` 相对来说更加模糊，在很多文章中都可以看到 Informer 的身影，在源码中真的去找一个叫作Informer的对象，却又发现找不到一个单纯的Informer，但是有很多结构体或者接口中包含Informer这个词。

在一开始提到过Informer从DeltaFIFO中Pop相应的对象，然后通过Indexer将对象和索引丢到本地cache中，再触发相应的事件处理函数（Resource Event Handlers）的运行。接下来通过源码，重新来梳理一下整个过程。

### 1. Informer 即 Controller

**a. Controller结构体与Controller接口**

Informer通过一个Controller对象来定义，本身结构很简单，在 `k8s.io/client-go/tools/cache`包中的 controller.go源文件中可以看到：
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
这里有熟悉的 Reflector ，可以猜到 `Informer` 启动时会去运行 `Reflector` ，从而通过 `Reflector` 实现 list-watch apiserver，更新"事件"到 `DeltaFIFO` 中用于进一步处理

继续看下controller对应的Controller接口：
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
这里的核心方法很明显是`Run(stopCh<-chan struct{})`，Run负责两件事情

  1）构造Reflector利用ListerWatcher的能力将对象事件更新到DeltaFIFO。

  2）从DeltaFIFO中Pop对象后调用ProcessFunc来处理。


**b. Controller的初始化**

在controller.go文件中有如下代码：
```golang
	// New makes a new Controller from the given Config.
	func New(c *Config) Controller {
		ctlr := &controller{
			config: *c,
			clock:  &clock.RealClock{},
		}
		return ctlr
	}
```
这里主要是传递了一个 `Config` 进来，核心逻辑便是 `Config` 从何而来以及后面要如何使用。

然后，先不关注 `NewInformer()` 的代码，实际开发中主要是使用 `SharedIndexInformer`，这两个入口初始化Controller的逻辑类似。
直接跟踪更实用的一个分支，查看 `func (s *sharedIndexInformer) Run(stopCh<-chan struct{})` 方法中如何调用 `New()`，代码位于shared_informer.go中：
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
		s.controller.Run(stopCh)
	}
```
从这里可以看到 `SharedIndexInformer` 的 `Run()` 过程中会构造一个 `Config`，然后创建 `Controller`，最后调用 `Controller` 的 `Run()`方法。

另外，这里也可以看到前面分析过的DeltaFIFO、ListerWatcher等，其中的Process:s.HandleDeltas这一行也比较重要，Process属性的类型是ProcessFunc，可以看到具体的ProcessFunc是HandleDeltas方法。


**c. Controller的启动**

上面提到 `Controller` 的初始化本身没有太多的逻辑，主要是构造了一个 `Config` 对象传递进来，所以 `Controller` 启动时肯定会有这个 `Config` 的使用逻，回到controller.go文件继续查看：
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
		wg.StartWithChannel(stopCh, r.Run)

		// 执行 Controller 的 processLoop
		wait.Until(c.processLoop, time.Second, stopCh)
		wg.Wait()
	}
```
这里的代码逻辑很简单，构造 `Reflector` 后运行起来，然后执行 `c.processLoop`，显然 `Controller` 的业务逻辑隐藏在 processLoop方法中。


**d. processLoop**

这里的代码逻辑是从 `DeltaFIFO` 中Pop出一个对象丢给 `PopProcessFunc` 处理，如果失败了就 re-enqueue 到 `DeltaFIFO` 中。前面提到过这里的 `PopProcessFunc` 由 `HandleDeltas()` 方法来实现，所以这里的主要逻辑就转到了 `HandleDeltas()` 是如何实现的。
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

`HandleDeltas()` 代码逻辑都落在 `processDeltas() `函数的调用上，位于shared_informer.go文件中：
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
```
这里的代码逻辑主要是遍历一个 `Deltas` 中的所有 `Delta`，然后根据 `Delta` 的类型来决定如何操作 `Indexer` ，也就是更新本地cache，同时分发相应的通知。


### 2. SharedIndexInformer对象

**a. 1.SharedIndexInformer是什么**

在 Operator 开发中，如果不使用 controller-runtime库，也就是不通过 Kubebuilder 等工具来生成脚手架，就经常会用到 `SharedInformerFactory`。

在 client-go 的 `informers/apps/v1`包的deployment.go文件中有 `DeploymentInformer` 类型的相关定义：
```golang
	// DeploymentInformer provides access to a shared informer and lister for
	// Deployments.
	type DeploymentInformer interface {
		Informer() cache.SharedIndexInformer
		Lister() v1.DeploymentLister
	}
```
这里可以看到 `DeploymentInformer` 是由 `Informer` 和 `Lister` 组成的。


**b. SharedIndexInformer接口的定义**

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
	//
	// The authoritative state of an object is what apiservers provide
	// access to, and an object goes through a strict sequence of states.
	// An object state is either (1) present with a ResourceVersion and
	// other appropriate content or (2) "absent".
	//
	// A SharedInformer maintains a local cache --- exposed by GetStore(),
	// by GetIndexer() in the case of an indexed informer, and possibly by
	// machinery involved in creating and/or accessing the informer --- of
	// the state of each relevant object.  This cache is eventually
	// consistent with the authoritative state.  This means that, unless
	// prevented by persistent communication problems, if ever a
	// particular object ID X is authoritatively associated with a state S
	// then for every SharedInformer I whose collection includes (X, S)
	// eventually either (1) I's cache associates X with S or a later
	// state of X, (2) I is stopped, or (3) the authoritative state
	// service for X terminates.  To be formally complete, we say that the
	// absent state meets any restriction by label selector or field
	// selector.
	//
	// For a given informer and relevant object ID X, the sequence of
	// states that appears in the informer's cache is a subsequence of the
	// states authoritatively associated with X.  That is, some states
	// might never appear in the cache but ordering among the appearing
	// states is correct.  Note, however, that there is no promise about
	// ordering between states seen for different objects.
	//
	// The local cache starts out empty, and gets populated and updated
	// during `Run()`.
	//
	// As a simple example, if a collection of objects is henceforth
	// unchanging, a SharedInformer is created that links to that
	// collection, and that SharedInformer is `Run()` then that
	// SharedInformer's cache eventually holds an exact copy of that
	// collection (unless it is stopped too soon, the authoritative state
	// service ends, or communication problems between the two
	// persistently thwart achievement).
	//
	// As another simple example, if the local cache ever holds a
	// non-absent state for some object ID and the object is eventually
	// removed from the authoritative state then eventually the object is
	// removed from the local cache (unless the SharedInformer is stopped
	// too soon, the authoritative state service ends, or communication
	// problems persistently thwart the desired result).
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
	//
	// A delete notification exposes the last locally known non-absent
	// state, except that its ResourceVersion is replaced with a
	// ResourceVersion in which the object is actually absent.
	type SharedInformer interface {
		// AddEventHandler adds an event handler to the shared informer using
		// the shared informer's resync period.  Events to a single handler are
		// delivered sequentially, but there is no coordination between
		// different handlers.
		// It returns a registration handle for the handler that can be used to
		// remove the handler again, or to tell if the handler is synced (has
		// seen every item in the initial list).
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
		AddEventHandlerWithResyncPeriod(handler ResourceEventHandler, resyncPeriod time.Duration) (ResourceEventHandlerRegistration, error)
		// RemoveEventHandler removes a formerly added event handler given by
		// its registration handle.
		// This function is guaranteed to be idempotent, and thread-safe.
		RemoveEventHandler(handle ResourceEventHandlerRegistration) error
		// GetStore returns the informer's local cache as a Store.
		GetStore() Store
		// GetController is deprecated, it does nothing useful
		GetController() Controller
		// Run starts and runs the shared informer, returning after it stops.
		// The informer will be stopped when stopCh is closed.
		Run(stopCh <-chan struct{})
		// HasSynced returns true if the shared informer's store has been
		// informed by at least one full LIST of the authoritative state
		// of the informer's object collection.  This is unrelated to "resync".
		//
		// Note that this doesn't tell you if an individual handler is synced!!
		// For that, please call HasSynced on the handle returned by
		// AddEventHandler.
		HasSynced() bool
		// LastSyncResourceVersion is the resource version observed when last synced with the underlying
		// store. The value returned is not synchronized with access to the underlying store and is not
		// thread-safe.
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
		SetTransform(handler TransformFunc) error

		// IsStopped reports whether the informer has already been stopped.
		// Adding event handlers to already stopped informers is not possible.
		// An informer already stopped will never be started again.
		IsStopped() bool
	}
```


**c. sharedIndexInformer结构体的定义**

`SharedIndexInformer` 接口的实现 sharedIndexerInformer的定义，同样在shared_informer.go文件中查看代码：
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
		objectType runtime.Object

		// objectDescription is the description of this informer's objects. This typically defaults to
		objectDescription string

		// resyncCheckPeriod is how often we want the reflector's resync timer to fire so it can call
		// shouldResync to check if any of our listeners need a resync.
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
		s.controller.Run(stopCh)
	}
```

### 3. sharedProcessor对象

`sharedProcessor` 中维护了 `processorListener` 集合，然后分发通知对象到 `listeners`，其代码在shared_informer.go中：
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
