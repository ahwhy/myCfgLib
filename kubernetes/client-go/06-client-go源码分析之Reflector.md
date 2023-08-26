# client-go 源码分析之 Reflector

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


## 二、Client-go ListerWatcher

`Reflector` 的任务就是从 apiserver 监听(watch)特定类型的资源，拿到变更通知后，将其传入到 `DeltaFIFO` 队列中；`Reflector` 定义在 `k8s.io/client-go/tools/cache` 包下。

### 1. Reflector 的启动过程

代表 `Reflector` 的结构体属性比较多，如果不知道其工作原理的情况下去逐个看这些属性意义不大，所以这里先不去具体看这个结构体的定义，而是直接找到 `Run()` 方法，从 `Reflector` 的启动切入，源码在 reflector.go 中
```golang
	// Reflector watches a specified resource and causes all changes to be reflected in the given store.
	type Reflector struct {
		// name identifies this reflector. By default it will be a file:line if possible.
		name string
		// The name of the type we expect to place in the store. The name
		// will be the stringification of expectedGVK if provided, and the
		// stringification of expectedType otherwise. It is for display
		// only, and should not be used for parsing or comparison.
		typeDescription string
		// An example object of the type we expect to place in the store.
		// Only the type needs to be right, except that when that is
		// `unstructured.Unstructured` the object's `"apiVersion"` and
		// `"kind"` must also be right.
		expectedType reflect.Type
		// The GVK of the object we expect to place in the store if unstructured.
		expectedGVK *schema.GroupVersionKind
		// The destination to sync up with the watch source
		store Store
		// listerWatcher is used to perform lists and watches.
		listerWatcher ListerWatcher
		// backoff manages backoff of ListWatch
		backoffManager wait.BackoffManager
		resyncPeriod   time.Duration
		// clock allows tests to manipulate time
		clock clock.Clock
		// paginatedResult defines whether pagination should be forced for list calls.
		// It is set based on the result of the initial list call.
		paginatedResult bool
		// lastSyncResourceVersion is the resource version token last
		// observed when doing a sync with the underlying store
		// it is thread safe, but not synchronized with the underlying store
		lastSyncResourceVersion string
		// isLastSyncResourceVersionUnavailable is true if the previous list or watch request with
		// lastSyncResourceVersion failed with an "expired" or "too large resource version" error.
		isLastSyncResourceVersionUnavailable bool
		// lastSyncResourceVersionMutex guards read/write access to lastSyncResourceVersion
		lastSyncResourceVersionMutex sync.RWMutex
		// Called whenever the ListAndWatch drops the connection with an error.
		watchErrorHandler WatchErrorHandler
		// WatchListPageSize is the requested chunk size of initial and resync watch lists.
		// If unset, for consistent reads (RV="") or reads that opt-into arbitrarily old data
		// (RV="0") it will default to pager.PageSize, for the rest (RV != "" && RV != "0")
		// it will turn off pagination to allow serving them from watch cache.
		// NOTE: It should be used carefully as paginated lists are always served directly from
		// etcd, which is significantly less efficient and may lead to serious performance and
		// scalability problems.
		WatchListPageSize int64
		// ShouldResync is invoked periodically and whenever it returns `true` the Store's Resync operation is invoked
		ShouldResync func() bool
		// MaxInternalErrorRetryDuration defines how long we should retry internal errors returned by watch.
		MaxInternalErrorRetryDuration time.Duration
		// UseWatchList if turned on instructs the reflector to open a stream to bring data from the API server.
		// Streaming has the primary advantage of using fewer server's resources to fetch data.
		//
		// The old behaviour establishes a LIST request which gets data in chunks.
		// Paginated list is less efficient and depending on the actual size of objects
		// might result in an increased memory consumption of the APIServer.
		//
		// See https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/3157-watch-list#design-details
		UseWatchList bool
	}

	// Run repeatedly uses the reflector's ListAndWatch to fetch all the objects and subsequent deltas.
	// Run will exit when stopCh is closed.
	func (r *Reflector) Run(stopCh <-chan struct{}) {
		klog.V(3).Infof("Starting reflector %s (%s) from %s", r.typeDescription, r.resyncPeriod, r.name)
		wait.BackoffUntil(func() {
			// 主要逻辑在 Reflector.ListAndWatch() 方法中
			if err := r.ListAndWatch(stopCh); err != nil {
				r.watchErrorHandler(r, err)
			}
		}, r.backoffManager, true, stopCh)
		klog.V(3).Infof("Stopping reflector %s (%s) from %s", r.typeDescription, r.resyncPeriod, r.name)
	}

	// k8s.io/apimachinery/pkg/util/wait
	// BackoffUntil loops until stop channel is closed, run f every duration given by BackoffManager.
	//
	// If sliding is true, the period is computed after f runs. If it is false then period includes the runtime for f.
	func BackoffUntil(f func(), backoff BackoffManager, sliding bool, stopCh <-chan struct{}) {
		var t clock.Timer
		for {
			select {
			case <-stopCh:
				return
			default:
			}

			if !sliding {
				t = backoff.Backoff()
			}

			func() {
				defer runtime.HandleCrash()
				f()
			}()

			if sliding {
				t = backoff.Backoff()
			}

			// NOTE: b/c there is no priority selection in golang
			// it is possible for this to race, meaning we could
			// trigger t.C and stopCh, and t.C select falls through.
			// In order to mitigate we re-check stopCh at the beginning
			// of every loop to prevent extra executions of f().
			select {
			case <-stopCh:
				if !t.Stop() {
					<-t.C()
				}
				return
			case <-t.C():
			}
		}
	}
```
  
### 2. 核心方法 Reflector.ListAndWatch()

- `Reflector.ListAndWatch()` 方法，是Reflector的核心逻辑之一
	- `ListAndWatch()` 方法是先列出特定资源的所有对象，然后获取其资源版本，接着使用这个资源版本来开始监听流程，监听到新版本资源后，通过`watchHandler()` 方法将其加入 `DeltaFIFO` 中；具体的实现，细化分为了几个方法
		- `watchList()` 方法，通过 `ENABLE_CLIENT_GO_WATCH_LIST_ALPHA` 变量，判断是否调用 `watchList()` 方法，会与 apiserve r建立一个数据流，来获得一致性的数据，即向 apiserver 发起一个 watch请求，并 调用`watchHandler()` 方法
		- `list()` 方法，如果没有 调用`watchList()` 方法，则调用 `list()` 方法，会 lists 所有的 items，并且记录并调用 resource version；而list(列选)到的最新元素会通过 `syncWith()` 方法添加一个 `Sync`类型的 `DeltaType` 到 `DeltaFIFO` 中，所以 list 操作本身也会触发后面的调谐逻辑
		- `startResync` 方法，会调用 `DeltaFIFO` 的 Replace 方法，即 `store.Replace`
		- `watch()` 方法向 apiserver 发起一个 watch请求，并 调用`watchHandler()` 方法
```golang
	// ListAndWatch first lists all items and get the resource version at the moment of call, and then use the resource version to watch.
	// It returns error if ListAndWatch didn't even try to initialize watch.
	func (r *Reflector) ListAndWatch(stopCh <-chan struct{}) error {
		klog.V(3).Infof("Listing and watching %v from %s", r.typeDescription, r.name)
		var err error
		var w watch.Interface
		fallbackToList := !r.UseWatchList

		if r.UseWatchList {
			w, err = r.watchList(stopCh)
			if w == nil && err == nil {
				// stopCh was closed
				return nil
			}
			if err != nil {
				if !apierrors.IsInvalid(err) {
					return err
				}
				klog.Warning("the watch-list feature is not supported by the server, falling back to the previous LIST/WATCH semantic")
				fallbackToList = true
				// Ensure that we won't accidentally pass some garbage down the watch.
				w = nil
			}
		}

		if fallbackToList {
			err = r.list(stopCh)
			if err != nil {
				return err
			}
		}

		resyncerrc := make(chan error, 1)
		cancelCh := make(chan struct{})
		defer close(cancelCh)
		go r.startResync(stopCh, cancelCh, resyncerrc)
		return r.watch(w, stopCh, resyncerrc)
	}

	// watchList establishes a stream to get a consistent snapshot of data
	// from the server as described in https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/3157-watch-list#proposal
	//
	// case 1: start at Most Recent (RV="", ResourceVersionMatch=ResourceVersionMatchNotOlderThan)
	// Establishes a consistent stream with the server.
	// That means the returned data is consistent, as if, served directly from etcd via a quorum read.
	// It begins with synthetic "Added" events of all resources up to the most recent ResourceVersion.
	// It ends with a synthetic "Bookmark" event containing the most recent ResourceVersion.
	// After receiving a "Bookmark" event the reflector is considered to be synchronized.
	// It replaces its internal store with the collected items and
	// reuses the current watch requests for getting further events.
	//
	// case 2: start at Exact (RV>"0", ResourceVersionMatch=ResourceVersionMatchNotOlderThan)
	// Establishes a stream with the server at the provided resource version.
	// To establish the initial state the server begins with synthetic "Added" events.
	// It ends with a synthetic "Bookmark" event containing the provided or newer resource version.
	// After receiving a "Bookmark" event the reflector is considered to be synchronized.
	// It replaces its internal store with the collected items and
	// reuses the current watch requests for getting further events.
	func (r *Reflector) watchList(stopCh <-chan struct{}) (watch.Interface, error) {
		var w watch.Interface
		var err error
		var temporaryStore Store
		var resourceVersion string
		// TODO(#115478): see if this function could be turned into a method and see if error handling could be unified with the r.watch method
		// 错误处理，划分各类场景
		isErrorRetriableWithSideEffectsFn := func(err error) bool {
			// Watch Error
			if canRetry := isWatchErrorRetriable(err); canRetry {
				klog.V(2).Infof("%s: watch-list of %v returned %v - backing off", r.name, r.typeDescription, err)
				<-r.backoffManager.Backoff().C()
				return true
			}
			if isExpiredError(err) || isTooLargeResourceVersionError(err) {
				// we tried to re-establish a watch request but the provided RV has either expired or it is greater than the server knows about.
				// In that case we reset the RV and try to get a consistent snapshot from the watch cache (case 1)
				// 我们试图重新建立一个 watch 请求，但是提供的 RV 已经过期或者比服务器知道的要大。在这种情况下，我们重置 RV 并尝试从 watch 缓存中获取一致的快照
				// 设置了这个属性后，下一次 list 会从 etcd 中获取
				r.setIsLastSyncResourceVersionUnavailable(true)
				return true
			}
			return false
		}

		// trace 用于记录操作耗时，这里的逻辑是把超过10秒的步骤打印出来
		initTrace := trace.New("Reflector WatchList", trace.Field{Key: "name", Value: r.name})
		defer initTrace.LogIfLong(10 * time.Second)
		for {
			select {
			// stopCh 收到消息，则直接返回
			case <-stopCh:
				return nil, nil
			default:
			}

			resourceVersion = ""
			// 查询 lastSyncResourceVersion，如果 isLastSyncResourceVersionUnavailable 为 true 则返回 ""
			lastKnownRV := r.rewatchResourceVersion()
			temporaryStore = NewStore(DeletionHandlingMetaNamespaceKeyFunc)
			// TODO(#115478): large "list", slow clients, slow network, p&f might slow down streaming and eventually fail. maybe in such a case we should retry with an increased timeout?
			// 超时时间为 5-10 分钟
			timeoutSeconds := int64(minWatchTimeout.Seconds() * (rand.Float64() + 1.0))
			options := metav1.ListOptions{
				ResourceVersion:      lastKnownRV,
				// 用于降低 apiserver 压力，bookmark 类型响应的对象主要只有 RV 信息
				AllowWatchBookmarks:  true,
				SendInitialEvents:    pointer.Bool(true),
				ResourceVersionMatch: metav1.ResourceVersionMatchNotOlderThan,
				// 如果超时没有接收到任何 Event，则需要停止监听，避免阻塞
				TimeoutSeconds:       &timeoutSeconds,
			}
			start := r.clock.Now()

			// 调用 watch 开始监听
			// client-go源码分析之ListerWatcher 215行
			// Watch(options metav1.ListOptions) (watch.Interface, error)
			w, err = r.listerWatcher.Watch(options)
			if err != nil {
				if isErrorRetriableWithSideEffectsFn(err) {
					continue
				}
				return nil, err
			}
			bookmarkReceived := pointer.Bool(false)
			// 核心逻辑
			err = watchHandler(start, w, temporaryStore, r.expectedType, r.expectedGVK, r.name, r.typeDescription,
				func(rv string) { resourceVersion = rv },
				bookmarkReceived,
				r.clock, make(chan error), stopCh)
			if err != nil {
				w.Stop() // stop and retry with clean state
				if err == errorStopRequested {
					return nil, nil
				}
				if isErrorRetriableWithSideEffectsFn(err) {
					continue
				}
				return nil, err
			}
			if *bookmarkReceived {
				break
			}
		}
		// We successfully got initial state from watch-list confirmed by the "k8s.io/initial-events-end" bookmark.
		//
		// Step adds a new step with a specific message. Call this at the end of an execution step to record how long it took.
		// The Fields add key value pairs to provide additional details about the trace step.
		initTrace.Step("Objects streamed", trace.Field{Key: "count", Value: len(temporaryStore.List())})
		// list 成功，设置 isLastSyncResourceVersionUnavailable 为 false
		r.setIsLastSyncResourceVersionUnavailable(false)
		if err = r.store.Replace(temporaryStore.List(), resourceVersion); err != nil {
			return nil, fmt.Errorf("unable to sync watch-list result: %v", err)
		}
		initTrace.Step("SyncWith done")
		r.setLastSyncResourceVersion(resourceVersion)

		return w, nil
	}

	var (
		// We try to spread the load on apiserver by setting timeouts for
		// watch requests - it is random in [minWatchTimeout, 2*minWatchTimeout].
		minWatchTimeout = 5 * time.Minute
	)

	// list simply lists all items and records a resource version obtained from the server at the moment of the call.
	// the resource version can be used for further progress notification (aka. watch).
	func (r *Reflector) list(stopCh <-chan struct{}) error {
		var resourceVersion string
		// relistResourceVersion 决定了 reflector 应该从哪个resource version 开始 list 或 relist
		options := metav1.ListOptions{ResourceVersion: r.relistResourceVersion()}

		// trace 用于记录操作耗时，这里的逻辑是把超过10秒的步骤打印出来
		initTrace := trace.New("Reflector ListAndWatch", trace.Field{Key: "name", Value: r.name})
		defer initTrace.LogIfLong(10 * time.Second)
		var list runtime.Object
		var paginatedResult bool
		var err error
		listCh := make(chan struct{}, 1)
		panicCh := make(chan interface{}, 1)
		go func() {
			defer func() {
				if r := recover(); r != nil {
					panicCh <- r
				}
			}()
			// Attempt to gather list in chunks, if supported by listerWatcher, if not, the first
			// list request will return the full response.
			// 开始尝试收集 list 的 chunks
			pager := pager.New(pager.SimplePageFunc(func(opts metav1.ListOptions) (runtime.Object, error) {
				// client-go源码分析之ListerWatcher 208行
				// List(options metav1.ListOptions) (runtime.Object, error)
				return r.listerWatcher.List(opts)
			}))
			switch {
			case r.WatchListPageSize != 0:
				pager.PageSize = r.WatchListPageSize
			case r.paginatedResult:
				// 我们最初得到一个分页的结果。假设该资源和服务器支持分页请求(即观察缓存可能被禁用)，并保留默认的分页大小设置。
				// We got a paginated result initially. Assume this resource and server honor
				// paging requests (i.e. watch cache is probably disabled) and leave the default
				// pager size set.
			case options.ResourceVersion != "" && options.ResourceVersion != "0":
				// User didn't explicitly request pagination.
				//
				// With ResourceVersion != "", we have a possibility to list from watch cache,
				// but we do that (for ResourceVersion != "0") only if Limit is unset.
				// To avoid thundering herd on etcd (e.g. on master upgrades), we explicitly
				// switch off pagination to force listing from watch cache (if enabled).
				// With the existing semantic of RV (result is at least as fresh as provided RV),
				// this is correct and doesn't lead to going back in time.
				//
				// We also don't turn off pagination for ResourceVersion="0", since watch cache
				// is ignoring Limit in that case anyway, and if watch cache is not enabled
				// we don't introduce regression.
				pager.PageSize = 0
			}

			list, paginatedResult, err = pager.ListWithAlloc(context.Background(), options)
			if isExpiredError(err) || isTooLargeResourceVersionError(err) {
				r.setIsLastSyncResourceVersionUnavailable(true)
				// Retry immediately if the resource version used to list is unavailable.
				// The pager already falls back to full list if paginated list calls fail due to an "Expired" error on
				// continuation pages, but the pager might not be enabled, the full list might fail because the
				// resource version it is listing at is expired or the cache may not yet be synced to the provided
				// resource version. So we need to fallback to resourceVersion="" in all to recover and ensure
				// the reflector makes forward progress.
				// ListWithAlloc的工作方式类似于List，但避免保留对p.PageFn返回的items slice的引用
				list, paginatedResult, err = pager.ListWithAlloc(context.Background(), metav1.ListOptions{ResourceVersion: r.relistResourceVersion()})
			}
			close(listCh)
		}()
		select {
		case <-stopCh:
			return nil
		case r := <-panicCh:
			panic(r)
		case <-listCh: // 等待上个 goroutine 跑完？
		}
		initTrace.Step("Objects listed", trace.Field{Key: "error", Value: err})
		if err != nil {
			klog.Warningf("%s: failed to list %v: %v", r.name, r.typeDescription, err)
			return fmt.Errorf("failed to list %v: %w", r.typeDescription, err)
		}

		// We check if the list was paginated and if so set the paginatedResult based on that.
		// However, we want to do that only for the initial list (which is the only case
		// when we set ResourceVersion="0"). The reasoning behind it is that later, in some
		// situations we may force listing directly from etcd (by setting ResourceVersion="")
		// which will return paginated result, even if watch cache is enabled. However, in
		// that case, we still want to prefer sending requests to watch cache if possible.
		//
		// Paginated result returned for request with ResourceVersion="0" mean that watch
		// cache is disabled and there are a lot of objects of a given type. In such case,
		// there is no need to prefer listing from watch cache.
		if options.ResourceVersion == "0" && paginatedResult {
			r.paginatedResult = true
		}

		r.setIsLastSyncResourceVersionUnavailable(false) // list was successful
		listMetaInterface, err := meta.ListAccessor(list)
		if err != nil {
			return fmt.Errorf("unable to understand list result %#v: %v", list, err)
		}
		resourceVersion = listMetaInterface.GetResourceVersion()
		initTrace.Step("Resource version extracted")
		// 将 list 到的 item 添加到 store 中，这里的 store 也就是 DeltaFIFO，也即 添加一个 SyncDeltaType，不过这里的 resourceVersion 值并没有实际用到。
		items, err := meta.ExtractListWithAlloc(list)
		if err != nil {
			return fmt.Errorf("unable to understand list result %#v (%v)", list, err)
		}
		initTrace.Step("Objects extracted")
		if err := r.syncWith(items, resourceVersion); err != nil {
			return fmt.Errorf("unable to sync list result: %v", err)
		}
		initTrace.Step("SyncWith done")
		r.setLastSyncResourceVersion(resourceVersion)
		initTrace.Step("Resource version updated")
		return nil
	}

	// syncWith replaces the store's items with the given list.
	func (r *Reflector) syncWith(items []runtime.Object, resourceVersion string) error {
		found := make([]interface{}, 0, len(items))
		for _, item := range items {
			found = append(found, item)
		}
		return r.store.Replace(found, resourceVersion)
	}

	// startResync periodically calls r.store.Resync() method.
	// Note that this method is blocking and should be
	// called in a separate goroutine.
	func (r *Reflector) startResync(stopCh <-chan struct{}, cancelCh <-chan struct{}, resyncerrc chan error) {
		resyncCh, cleanup := r.resyncChan()
		defer func() {
			cleanup() // Call the last one written into cleanup
		}()
		for {
			select {
			case <-resyncCh:
			case <-stopCh:
				return
			case <-cancelCh:
				return
			}
			if r.ShouldResync == nil || r.ShouldResync() {
				klog.V(4).Infof("%s: forcing resync", r.name)
				if err := r.store.Resync(); err != nil {
					resyncerrc <- err
					return
				}
			}
			cleanup()
			resyncCh, cleanup = r.resyncChan()
		}
	}

	// resyncChan returns a channel which will receive something when a resync is required, and a cleanup function.
	func (r *Reflector) resyncChan() (<-chan time.Time, func() bool) {
		if r.resyncPeriod == 0 {
			return neverExitWatch, func() bool { return false }
		}
		// The cleanup function is required: imagine the scenario where watches
		// always fail so we end up listing frequently. Then, if we don't
		// manually stop the timer, we could end up with many timers active
		// concurrently.
		t := r.clock.NewTimer(r.resyncPeriod)
		return t.C(), t.Stop
	}

	// watch simply starts a watch request with the server.
	func (r *Reflector) watch(w watch.Interface, stopCh <-chan struct{}, resyncerrc chan error) error {
		var err error
		retry := NewRetryWithDeadline(r.MaxInternalErrorRetryDuration, time.Minute, apierrors.IsInternalError, r.clock)

		for {
			// give the stopCh a chance to stop the loop, even in case of continue statements further down on errors
			select {
			case <-stopCh:
				return nil
			default:
			}

			// start the clock before sending the request, since some proxies won't flush headers until after the first watch event is sent
			start := r.clock.Now()

			if w == nil {
				timeoutSeconds := int64(minWatchTimeout.Seconds() * (rand.Float64() + 1.0))
				options := metav1.ListOptions{
					ResourceVersion: r.LastSyncResourceVersion(),
					// We want to avoid situations of hanging watchers. Stop any watchers that do not
					// receive any events within the timeout window.
					TimeoutSeconds: &timeoutSeconds,
					// To reduce load on kube-apiserver on watch restarts, you may enable watch bookmarks.
					// Reflector doesn't assume bookmarks are returned at all (if the server do not support
					// watch bookmarks, it will ignore this field).
					AllowWatchBookmarks: true,
				}

				w, err = r.listerWatcher.Watch(options)
				if err != nil {
					if canRetry := isWatchErrorRetriable(err); canRetry {
						klog.V(4).Infof("%s: watch of %v returned %v - backing off", r.name, r.typeDescription, err)
						select {
						case <-stopCh:
							return nil
						case <-r.backoffManager.Backoff().C():
							continue
						}
					}
					return err
				}
			}

			err = watchHandler(start, w, r.store, r.expectedType, r.expectedGVK, r.name, r.typeDescription, r.setLastSyncResourceVersion, nil, r.clock, resyncerrc, stopCh)
			// Ensure that watch will not be reused across iterations.
			// 确保监视不会在迭代中重用，新一轮的调用会传递新的 watch.Interface
			w.Stop()
			w = nil
			retry.After(err)
			if err != nil {
				if err != errorStopRequested {
					switch {
					case isExpiredError(err):
						// Don't set LastSyncResourceVersionUnavailable - LIST call with ResourceVersion=RV already
						// has a semantic that it returns data at least as fresh as provided RV.
						// So first try to LIST with setting RV to resource version of last observed object.
						klog.V(4).Infof("%s: watch of %v closed with: %v", r.name, r.typeDescription, err)
					case apierrors.IsTooManyRequests(err):
						klog.V(2).Infof("%s: watch of %v returned 429 - backing off", r.name, r.typeDescription)
						select {
						case <-stopCh:
							return nil
						case <-r.backoffManager.Backoff().C():
							continue
						}
					case apierrors.IsInternalError(err) && retry.ShouldRetry():
						klog.V(2).Infof("%s: retrying watch of %v internal error: %v", r.name, r.typeDescription, err)
						continue
					default:
						klog.Warningf("%s: watch of %v ended with: %v", r.name, r.typeDescription, err)
					}
				}
				return nil
			}
		}
	}

	// LastSyncResourceVersion is the resource version observed when last sync with the underlying store
	// The value returned is not synchronized with access to the underlying store and is not thread-safe
	func (r *Reflector) LastSyncResourceVersion() string {
		r.lastSyncResourceVersionMutex.RLock()
		defer r.lastSyncResourceVersionMutex.RUnlock()
		return r.lastSyncResourceVersion
	}

	func (r *Reflector) setLastSyncResourceVersion(v string) {
		r.lastSyncResourceVersionMutex.Lock()
		defer r.lastSyncResourceVersionMutex.Unlock()
		r.lastSyncResourceVersion = v
	}

	// relistResourceVersion determines the resource version the reflector should list or relist from.
	// Returns either the lastSyncResourceVersion so that this reflector will relist with a resource
	// versions no older than has already been observed in relist results or watch events, or, if the last relist resulted
	// in an HTTP 410 (Gone) status code, returns "" so that the relist will use the latest resource version available in
	// etcd via a quorum read.
	// 当 r.isLastSyncResourceVersionUnavailable 为 true时，返回 ""；当 r.lastSyncResourceVersion 为 "" 时，返回 "0"
	// 区别是 relistResourceVersion 为 "" 会直接请求到 etcd，获取一个新的版本；而 relistResourceVersion 为 "0"，则访问 cache
	func (r *Reflector) relistResourceVersion() string {
		r.lastSyncResourceVersionMutex.RLock()
		defer r.lastSyncResourceVersionMutex.RUnlock()

		if r.isLastSyncResourceVersionUnavailable {
			// Since this reflector makes paginated list requests, and all paginated list requests skip the watch cache
			// if the lastSyncResourceVersion is unavailable, we set ResourceVersion="" and list again to re-establish reflector
			// to the latest available ResourceVersion, using a consistent read from etcd.
			return ""
		}
		if r.lastSyncResourceVersion == "" {
			// For performance reasons, initial list performed by reflector uses "0" as resource version to allow it to
			// be served from the watch cache if it is enabled.
			return "0"
		}
		return r.lastSyncResourceVersion
	}

	// rewatchResourceVersion determines the resource version the reflector should start streaming from.
	func (r *Reflector) rewatchResourceVersion() string {
		r.lastSyncResourceVersionMutex.RLock()
		defer r.lastSyncResourceVersionMutex.RUnlock()
		if r.isLastSyncResourceVersionUnavailable {
			// initial stream should return data at the most recent resource version.
			// the returned data must be consistent i.e. as if served from etcd via a quorum read
			return ""
		}
		return r.lastSyncResourceVersion
	}

	// setIsLastSyncResourceVersionUnavailable sets if the last list or watch request with lastSyncResourceVersion returned
	// "expired" or "too large resource version" error.
	func (r *Reflector) setIsLastSyncResourceVersionUnavailable(isUnavailable bool) {
		r.lastSyncResourceVersionMutex.Lock()
		defer r.lastSyncResourceVersionMutex.Unlock()
		r.isLastSyncResourceVersionUnavailable = isUnavailable
	}

	// setIsLastSyncResourceVersionUnavailable sets if the last list or watch request with lastSyncResourceVersion returned
	// "expired" or "too large resource version" error.
	func (r *Reflector) setIsLastSyncResourceVersionUnavailable(isUnavailable bool) {
		r.lastSyncResourceVersionMutex.Lock()
		defer r.lastSyncResourceVersionMutex.Unlock()
		r.isLastSyncResourceVersionUnavailable = isUnavailable
	}

	func isExpiredError(err error) bool {
		// In Kubernetes 1.17 and earlier, the api server returns both apierrors.StatusReasonExpired and
		// apierrors.StatusReasonGone for HTTP 410 (Gone) status code responses. In 1.18 the kube server is more consistent
		// and always returns apierrors.StatusReasonExpired. For backward compatibility we can only remove the apierrors.IsGone
		// check when we fully drop support for Kubernetes 1.17 servers from reflectors.
		return apierrors.IsResourceExpired(err) || apierrors.IsGone(err)
	}

	func isTooLargeResourceVersionError(err error) bool {
		if apierrors.HasStatusCause(err, metav1.CauseTypeResourceVersionTooLarge) {
			return true
		}
		// In Kubernetes 1.17.0-1.18.5, the api server doesn't set the error status cause to
		// metav1.CauseTypeResourceVersionTooLarge to indicate that the requested minimum resource
		// version is larger than the largest currently available resource version. To ensure backward
		// compatibility with these server versions we also need to detect the error based on the content
		// of the error message field.
		if !apierrors.IsTimeout(err) {
			return false
		}
		apierr, ok := err.(apierrors.APIStatus)
		if !ok || apierr == nil || apierr.Status().Details == nil {
			return false
		}
		for _, cause := range apierr.Status().Details.Causes {
			// Matches the message returned by api server 1.17.0-1.18.5 for this error condition
			if cause.Message == "Too large resource version" {
				return true
			}
		}

		// Matches the message returned by api server before 1.17.0
		if strings.Contains(apierr.Status().Message, "Too large resource version") {
			return true
		}

		return false
	}

	// isWatchErrorRetriable determines if it is safe to retry a watch error retrieved from the server.
	func isWatchErrorRetriable(err error) bool {
		// If this is "connection refused" error, it means that most likely apiserver is not responsive.
		// It doesn't make sense to re-list all objects because most likely we will be able to restart
		// watch where we ended.
		// If that's the case begin exponentially backing off and resend watch request.
		// Do the same for "429" errors.
		// 此时直接 re-list 已经没有用了，apiserver 暂时拒绝服务
		if utilnet.IsConnectionRefused(err) || apierrors.IsTooManyRequests(err) {
			return true
		}
		return false
	}
```

### 3. 核心方法 Reflector.watchHandler()

- 下面是 `watchHander()` 方法的实现，同样在 reflector.go 中
	- 在 `watchHandler()` 方法中完成了将监听到的 Event(事件)根据其 EventType(事件类型)分别调用 `DeltaFIFO` 的 `Add()/Update()/Delete()`等方法，完成对象追加到 `DeltaFIFO` 队列的过程
	- `watchHandler()` 方法的调用在一个 for 循环中，所以一轮调用 `watchHandler()` 工作流程完成后函数退出，新一轮的调用会传递进来新的 `watch.Interface` 和 `resourceVersion` 等
```golang
	// watchHandler watches w and sets setLastSyncResourceVersion
	func watchHandler(start time.Time,
		w watch.Interface,
		store Store,
		expectedType reflect.Type,
		expectedGVK *schema.GroupVersionKind,
		name string,
		expectedTypeName string,
		setLastSyncResourceVersion func(string),
		exitOnInitialEventsEndBookmark *bool,
		clock clock.Clock,
		errc chan error,
		stopCh <-chan struct{},
	) error {
		eventCount := 0
		if exitOnInitialEventsEndBookmark != nil {
			// set it to false just in case somebody
			// made it positive
			*exitOnInitialEventsEndBookmark = false
		}

	loop:
		for {
			select {
			case <-stopCh:
				return errorStopRequested
			case err := <-errc:
				return err
			// 接收 event 事件
			case event, ok := <-w.ResultChan():
				if !ok {
					// 失败，则跳回 loop
					break loop
				}
				// 如果是 Error 
				if event.Type == watch.Error {
					return apierrors.FromObject(event.Object)
				}
				// 创建 Reflector 时，会指定一个 expectedType
				if expectedType != nil {
					// 类型不匹配
					if e, a := expectedType, reflect.TypeOf(event.Object); e != a {
						utilruntime.HandleError(fmt.Errorf("%s: expected type %v, but watch event object had type %v", name, e, a))
						continue
					}
				}
				// 没有对应GO语言结构体的对象，可以通过这种方式来指定期望类型
				if expectedGVK != nil {
					if e, a := *expectedGVK, event.Object.GetObjectKind().GroupVersionKind(); e != a {
						utilruntime.HandleError(fmt.Errorf("%s: expected gvk %v, but watch event object had gvk %v", name, e, a))
						continue
					}
				}
				meta, err := meta.Accessor(event.Object)
				if err != nil {
					utilruntime.HandleError(fmt.Errorf("%s: unable to understand watch event %#v", name, event))
					continue
				}
				// 新的 ResourceVersion
				resourceVersion := meta.GetResourceVersion()
				// 调用 DeltaFIFO 的 Add/Update/Delete 等方法完成不同类型 Event的处理
				switch event.Type {
				case watch.Added:
					err := store.Add(event.Object)
					if err != nil {
						utilruntime.HandleError(fmt.Errorf("%s: unable to add watch event object (%#v) to store: %v", name, event.Object, err))
					}
				case watch.Modified:
					err := store.Update(event.Object)
					if err != nil {
						utilruntime.HandleError(fmt.Errorf("%s: unable to update watch event object (%#v) to store: %v", name, event.Object, err))
					}
				case watch.Deleted:
					// TODO: Will any consumers need access to the "last known
					// state", which is passed in event.Object? If so, may need
					// to change this.
					err := store.Delete(event.Object)
					if err != nil {
						utilruntime.HandleError(fmt.Errorf("%s: unable to delete watch event object (%#v) from store: %v", name, event.Object, err))
					}
				case watch.Bookmark:
					// A `Bookmark` means watch has synced here, just update the resourceVersion
					if _, ok := meta.GetAnnotations()["k8s.io/initial-events-end"]; ok {
						if exitOnInitialEventsEndBookmark != nil {
							*exitOnInitialEventsEndBookmark = true
						}
					}
				default:
					utilruntime.HandleError(fmt.Errorf("%s: unable to understand watch event %#v", name, event))
				}
				// 更新 resourceVersion
				setLastSyncResourceVersion(resourceVersion)
				if rvu, ok := store.(ResourceVersionUpdater); ok {
					rvu.UpdateResourceVersion(resourceVersion)
				}
				eventCount++
				if exitOnInitialEventsEndBookmark != nil && *exitOnInitialEventsEndBookmark {
					watchDuration := clock.Since(start)
					klog.V(4).Infof("exiting %v Watch because received the bookmark that marks the end of initial events stream, total %v items received in %v", name, eventCount, watchDuration)
					return nil
				}
			}
		}

		// 耗时
		watchDuration := clock.Since(start)
		// 耗时小于 1s，并且没有收到 event，异常情况
		if watchDuration < 1*time.Second && eventCount == 0 {
			return fmt.Errorf("very short watch: %s: Unexpected watch close - watch lasted less than a second and no items received", name)
		}
		klog.V(4).Infof("%s: Watch close - %v total %v items received", name, expectedTypeName, eventCount)
		return nil
	}

	// ResourceVersionUpdater is an interface that allows store implementation to
	// track the current resource version of the reflector. This is especially
	// important if storage bookmarks are enabled.
	type ResourceVersionUpdater interface {
		// UpdateResourceVersion is called each time current resource version of the reflector
		// is updated.
		UpdateResourceVersion(resourceVersion string)
	}
```

### 4. Reflector的初始化

- `NewReflector()` 的参数中有一个 `ListerWatcher`类型的 `lw`，还有一个 `expectedType` 和 `store`
	+ `lw` 就是 `ListerWatcher`
	+ `expectedType` 指定期望关注的类型
	+ `store` 是一个 `DeltaFIFO` ( 或者 `Indexer` & `ThreadSafeStore` ? )

加在一起就是 `Reflector` 通过 `ListWatcher` 提供的能力去 list-watch apiserver，然后完成将 `Event` 加到 `DeltaFIFO` 中
```golang
	// NewNamespaceKeyedIndexerAndReflector creates an Indexer and a Reflector
	// The indexer is configured to key on namespace
	func NewNamespaceKeyedIndexerAndReflector(lw ListerWatcher, expectedType interface{}, resyncPeriod time.Duration) (indexer Indexer, reflector *Reflector) {
		indexer = NewIndexer(MetaNamespaceKeyFunc, Indexers{NamespaceIndex: MetaNamespaceIndexFunc})
		reflector = NewReflector(lw, expectedType, indexer, resyncPeriod)
		return indexer, reflector
	}

	// NewReflector creates a new Reflector with its name defaulted to the closest source_file.go:line in the call stack
	// that is outside this package. See NewReflectorWithOptions for further information.
	func NewReflector(lw ListerWatcher, expectedType interface{}, store Store, resyncPeriod time.Duration) *Reflector {
		return NewReflectorWithOptions(lw, expectedType, store, ReflectorOptions{ResyncPeriod: resyncPeriod})
	}

	// NewNamedReflector creates a new Reflector with the specified name. See NewReflectorWithOptions for further
	// information.
	func NewNamedReflector(name string, lw ListerWatcher, expectedType interface{}, store Store, resyncPeriod time.Duration) *Reflector {
		return NewReflectorWithOptions(lw, expectedType, store, ReflectorOptions{Name: name, ResyncPeriod: resyncPeriod})
	}

	// ReflectorOptions configures a Reflector.
	type ReflectorOptions struct {
		// Name is the Reflector's name. If unset/unspecified, the name defaults to the closest source_file.go:line
		// in the call stack that is outside this package.
		Name string

		// TypeDescription is the Reflector's type description. If unset/unspecified, the type description is defaulted
		// using the following rules: if the expectedType passed to NewReflectorWithOptions was nil, the type description is
		// "<unspecified>". If the expectedType is an instance of *unstructured.Unstructured and its apiVersion and kind fields
		// are set, the type description is the string encoding of those. Otherwise, the type description is set to the
		// go type of expectedType..
		TypeDescription string

		// ResyncPeriod is the Reflector's resync period. If unset/unspecified, the resync period defaults to 0
		// (do not resync).
		ResyncPeriod time.Duration

		// Clock allows tests to control time. If unset defaults to clock.RealClock{}
		Clock clock.Clock
	}


	// NewReflectorWithOptions creates a new Reflector object which will keep the
	// given store up to date with the server's contents for the given
	// resource. Reflector promises to only put things in the store that
	// have the type of expectedType, unless expectedType is nil. If
	// resyncPeriod is non-zero, then the reflector will periodically
	// consult its ShouldResync function to determine whether to invoke
	// the Store's Resync operation; `ShouldResync==nil` means always
	// "yes".  This enables you to use reflectors to periodically process
	// everything as well as incrementally processing the things that
	// change.
	func NewReflectorWithOptions(lw ListerWatcher, expectedType interface{}, store Store, options ReflectorOptions) *Reflector {
		reflectorClock := options.Clock
		if reflectorClock == nil {
			reflectorClock = clock.RealClock{}
		}
		r := &Reflector{
			name:            options.Name,
			resyncPeriod:    options.ResyncPeriod,
			typeDescription: options.TypeDescription,
			listerWatcher:   lw,
			store:           store,
			// We used to make the call every 1sec (1 QPS), the goal here is to achieve ~98% traffic reduction when
			// API server is not healthy. With these parameters, backoff will stop at [30,60) sec interval which is
			// 0.22 QPS. If we don't backoff for 2min, assume API server is healthy and we reset the backoff.
			// 重试机制，退避算法，可以有效降低 apiserver 的负载，也就是重试间隔会越来越长
			backoffManager:    wait.NewExponentialBackoffManager(800*time.Millisecond, 30*time.Second, 2*time.Minute, 2.0, 1.0, reflectorClock),
			clock:             reflectorClock,
			watchErrorHandler: WatchErrorHandler(DefaultWatchErrorHandler),
			expectedType:      reflect.TypeOf(expectedType),
		}

		if r.name == "" {
			r.name = naming.GetNameFromCallsite(internalPackages...)
		}

		if r.typeDescription == "" {
			r.typeDescription = getTypeDescriptionFromObject(expectedType)
		}

		if r.expectedGVK == nil {
			r.expectedGVK = getExpectedGVKFromObject(expectedType)
		}

		if s := os.Getenv("ENABLE_CLIENT_GO_WATCH_LIST_ALPHA"); len(s) > 0 {
			r.UseWatchList = true
		}

		return r
	}

	func getTypeDescriptionFromObject(expectedType interface{}) string {
		if expectedType == nil {
			return defaultExpectedTypeName
		}

		reflectDescription := reflect.TypeOf(expectedType).String()

		obj, ok := expectedType.(*unstructured.Unstructured)
		if !ok {
			return reflectDescription
		}

		gvk := obj.GroupVersionKind()
		if gvk.Empty() {
			return reflectDescription
		}

		return gvk.String()
	}

	func getExpectedGVKFromObject(expectedType interface{}) *schema.GroupVersionKind {
		obj, ok := expectedType.(*unstructured.Unstructured)
		if !ok {
			return nil
		}

		gvk := obj.GroupVersionKind()
		if gvk.Empty() {
			return nil
		}

		return &gvk
	}

	// internalPackages are packages that ignored when creating a default reflector name. These packages are in the common
	// call chains to NewReflector, so they'd be low entropy names for reflectors
	var internalPackages = []string{"client-go/tools/cache/"}

	// The WatchErrorHandler is called whenever ListAndWatch drops the
	// connection with an error. After calling this handler, the informer
	// will backoff and retry.
	//
	// The default implementation looks at the error type and tries to log
	// the error message at an appropriate level.
	//
	// Implementations of this handler may display the error message in other
	// ways. Implementations should return quickly - any expensive processing
	// should be offloaded.
	type WatchErrorHandler func(r *Reflector, err error)

	// DefaultWatchErrorHandler is the default implementation of WatchErrorHandler
	func DefaultWatchErrorHandler(r *Reflector, err error) {
		switch {
		case isExpiredError(err):
			// Don't set LastSyncResourceVersionUnavailable - LIST call with ResourceVersion=RV already
			// has a semantic that it returns data at least as fresh as provided RV.
			// So first try to LIST with setting RV to resource version of last observed object.
			klog.V(4).Infof("%s: watch of %v closed with: %v", r.name, r.typeDescription, err)
		case err == io.EOF:
			// watch closed normally
		case err == io.ErrUnexpectedEOF:
			klog.V(1).Infof("%s: Watch for %v closed with unexpected EOF: %v", r.name, r.typeDescription, err)
		default:
			utilruntime.HandleError(fmt.Errorf("%s: Failed to watch %v: %v", r.name, r.typeDescription, err))
		}
	}
```

### 5. 小结

`Reflector` 的职责很清晰，要做的事情是保持 `DeltaFIFO` 中的 `items` 持续更新，具体实现是通过 `ListerWatcher` 提供的 list-watch(列选-监听)能力来列选指定类型的资源，这时会产生一系列 Sync 事件，然后通过列选到的 `ResourceVersion` 来开启监听过程，而监听到新的事件后，会和前面提到的Sync事件一样，都通过 `DeltaFIFO` 提供的方法构造相应的 `DeltaType` 添加到 `DeltaFIFO` 中。

当然，前面提到的更新也并不是直接修改 `DeltaFIFO` 中已经存在的元素，而是添加一个新的 `DeltaType` 到队列中。另外，`DeltaFIFO` 中添加新 `DeltaType` 时也会有一定的去重机制。

这里还有一个细节就是监听过程不是一劳永逸的，监听到新的事件后，会拿着对象的新 `ResourceVersion` 重新开启一轮新的监听过程。当然，这里的 watc h调用也有超时机制，一系列的健壮性措施，所以脱离 `Reflector`(Informer) 直接使用list-watch还是很难直接写出一套健壮的代码逻辑。