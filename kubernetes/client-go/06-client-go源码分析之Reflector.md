# client-go 源码分析之 Reflector

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


## 二、Client-go ListerWatcher

Reflector 的任务就是从 apiserver 监听(watch)特定类型的资源，拿到变更通知后，将其传入到 DeltaFIFO 队列中；Reflector定义在 `k8s.io/client-go/tools/cache` 包下。

### 1. Reflector的启动过程

代表 `Reflector` 的结构体属性比较多，如果不知道其工作原理的情况下去逐个看这些属性意义不大，所以这里先不去具体看这个结构体的定义，而是直接找到Run()方法，从 Reflector 的启动切入，源码在 reflector.go中
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

	// Run repeatedly uses the reflector's ListAndWatch to fetch all the
	// objects and subsequent deltas.
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
  
### 2. 核心方法：Reflector.ListAndWatch()

- `Reflector.ListAndWatch()` 方法有将近200行，是Reflector的核心逻辑之一
	- `ListAndWatch()` 方法是先列出特定资源的所有对象，然后获取其资源版本，接着使用这个资源版本来开始监听流程
	- 监听到新版本资源后，将其加入 `DeltaFIFO` 的动作是在 `watchHandler()` 方法中具体实现的
	- 在此之前list（列选）到的最新元素会通过 `syncWith()` 方法添加一个 `Sync`类型的 `DeltaType` 到 `DeltaFIFO` 中，所以 list操作本身也会触发后面的调谐逻辑
```golang
	// ListAndWatch first lists all items and get the resource version at the moment of call,
	// and then use the resource version to watch.
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
		// TODO(#115478): see if this function could be turned
		//  into a method and see if error handling
		//  could be unified with the r.watch method
		isErrorRetriableWithSideEffectsFn := func(err error) bool {
			if canRetry := isWatchErrorRetriable(err); canRetry {
				klog.V(2).Infof("%s: watch-list of %v returned %v - backing off", r.name, r.typeDescription, err)
				<-r.backoffManager.Backoff().C()
				return true
			}
			if isExpiredError(err) || isTooLargeResourceVersionError(err) {
				// we tried to re-establish a watch request but the provided RV
				// has either expired or it is greater than the server knows about.
				// In that case we reset the RV and
				// try to get a consistent snapshot from the watch cache (case 1)
				r.setIsLastSyncResourceVersionUnavailable(true)
				return true
			}
			return false
		}

		initTrace := trace.New("Reflector WatchList", trace.Field{Key: "name", Value: r.name})
		defer initTrace.LogIfLong(10 * time.Second)
		for {
			select {
			case <-stopCh:
				return nil, nil
			default:
			}

			resourceVersion = ""
			lastKnownRV := r.rewatchResourceVersion()
			temporaryStore = NewStore(DeletionHandlingMetaNamespaceKeyFunc)
			// TODO(#115478): large "list", slow clients, slow network, p&f
			//  might slow down streaming and eventually fail.
			//  maybe in such a case we should retry with an increased timeout?
			timeoutSeconds := int64(minWatchTimeout.Seconds() * (rand.Float64() + 1.0))
			options := metav1.ListOptions{
				ResourceVersion:      lastKnownRV,
				AllowWatchBookmarks:  true,
				SendInitialEvents:    pointer.Bool(true),
				ResourceVersionMatch: metav1.ResourceVersionMatchNotOlderThan,
				TimeoutSeconds:       &timeoutSeconds,
			}
			start := r.clock.Now()

			w, err = r.listerWatcher.Watch(options)
			if err != nil {
				if isErrorRetriableWithSideEffectsFn(err) {
					continue
				}
				return nil, err
			}
			bookmarkReceived := pointer.Bool(false)
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
		// We successfully got initial state from watch-list confirmed by the
		// "k8s.io/initial-events-end" bookmark.
		initTrace.Step("Objects streamed", trace.Field{Key: "count", Value: len(temporaryStore.List())})
		r.setIsLastSyncResourceVersionUnavailable(false)
		if err = r.store.Replace(temporaryStore.List(), resourceVersion); err != nil {
			return nil, fmt.Errorf("unable to sync watch-list result: %v", err)
		}
		initTrace.Step("SyncWith done")
		r.setLastSyncResourceVersion(resourceVersion)

		return w, nil
	}

	// list simply lists all items and records a resource version obtained from the server at the moment of the call.
	// the resource version can be used for further progress notification (aka. watch).
	func (r *Reflector) list(stopCh <-chan struct{}) error {
		var resourceVersion string
		options := metav1.ListOptions{ResourceVersion: r.relistResourceVersion()}

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
			pager := pager.New(pager.SimplePageFunc(func(opts metav1.ListOptions) (runtime.Object, error) {
				return r.listerWatcher.List(opts)
			}))
			switch {
			case r.WatchListPageSize != 0:
				pager.PageSize = r.WatchListPageSize
			case r.paginatedResult:
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
				list, paginatedResult, err = pager.ListWithAlloc(context.Background(), metav1.ListOptions{ResourceVersion: r.relistResourceVersion()})
			}
			close(listCh)
		}()
		select {
		case <-stopCh:
			return nil
		case r := <-panicCh:
			panic(r)
		case <-listCh:
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
```

