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

		wg.StartWithChannel(stopCh, r.Run)

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
		for _, d := range deltas {
			obj := d.Object

			switch d.Type {
			case Sync, Replaced, Added, Updated:
				if old, exists, err := clientState.Get(obj); err == nil && exists {
					if err := clientState.Update(obj); err != nil {
						return err
					}
					handler.OnUpdate(old, obj)
				} else {
					if err := clientState.Add(obj); err != nil {
						return err
					}
					handler.OnAdd(obj, isInInitialList)
				}
			case Deleted:
				if err := clientState.Delete(obj); err != nil {
					return err
				}
				handler.OnDelete(obj)
			}
		}
		return nil
	}
```
这里的代码逻辑主要是遍历一个Deltas中的所有Delta，然后根据Delta的类型来决定如何操作Indexer，也就是更新本地cache，同时分发相应的通知。