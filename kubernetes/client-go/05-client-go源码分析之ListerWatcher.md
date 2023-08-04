# client-go 源码分析之 ListerWatcher

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

ListerWatcher是Reflector的一个主要能力提供者，本节展示一下 ListerWatcher 是如何实现 `List()` 和 `Watch()` 过程的，ListerWatcher 的代码还是在 `k8s.io/client-go/tools/cache` 包中

### 1. ListWatch对象的初始化

- ListWatch对象和其创建过程都在listwatch.go中，先看一下ListWatch对象的定义
	- 这个结构体属性很简单，主要是 `ListFunc` 和 `WatchFunc`
	- 主要逻辑在 `NewFilteredListWatchFromClient()` 函数中，list和watch能力都是通过RESTClient提供的
	- 涉及一个 `Getter` 接口
```golang
	// ListFunc knows how to list resources
	type ListFunc func(options metav1.ListOptions) (runtime.Object, error)

	// WatchFunc knows how to watch resources
	type WatchFunc func(options metav1.ListOptions) (watch.Interface, error)

	// ListWatch knows how to list and watch a set of apiserver resources.  It satisfies the ListerWatcher interface.
	// It is a convenience function for users of NewReflector, etc.
	// ListFunc and WatchFunc must not be nil
	type ListWatch struct {
		ListFunc  ListFunc
		WatchFunc WatchFunc
		// DisableChunking requests no chunking for this list watcher.
		DisableChunking bool
	}

	// NewListWatchFromClient creates a new ListWatch from the specified client, resource, namespace and field selector.
	func NewListWatchFromClient(c Getter, resource string, namespace string, fieldSelector fields.Selector) *ListWatch {
		optionsModifier := func(options *metav1.ListOptions) {
			options.FieldSelector = fieldSelector.String()
		}
		return NewFilteredListWatchFromClient(c, resource, namespace, optionsModifier)
	}

	// NewFilteredListWatchFromClient creates a new ListWatch from the specified client, resource, namespace, and option modifier.
	// Option modifier is a function takes a ListOptions and modifies the consumed ListOptions. Provide customized modifier function
	// to apply modification to ListOptions with a field selector, a label selector, or any other desired options.
	func NewFilteredListWatchFromClient(c Getter, resource string, namespace string, optionsModifier func(options *metav1.ListOptions)) *ListWatch {
		// list某个namespace下的某个resource
		listFunc := func(options metav1.ListOptions) (runtime.Object, error) {
			optionsModifier(&options)
			return c.Get().
				Namespace(namespace).
				Resource(resource).
				VersionedParams(&options, metav1.ParameterCodec).
				Do(context.TODO()).
				Get()
		}
		// 监听某个namespace(命名空间)下的资源
		watchFunc := func(options metav1.ListOptions) (watch.Interface, error) {
			options.Watch = true
			optionsModifier(&options)
			return c.Get().
				Namespace(namespace).
				Resource(resource).
				VersionedParams(&options, metav1.ParameterCodec).
				Watch(context.TODO())
		}
		return &ListWatch{ListFunc: listFunc, WatchFunc: watchFunc}
	}
```

- 上面涉及一个Getter接口，下面是 `Getter` 的定义，以及关联资源
```golang
	// Getter interface knows how to access Get method from RESTClient.
	type Getter interface {
		Get() *restclient.Request
	}

	// Request allows for building up a request to a server in a chained fashion.
	// Any errors are stored until the end of your call, so you only have to
	// check once.
	type Request struct {
		c *RESTClient

		warningHandler WarningHandler

		rateLimiter flowcontrol.RateLimiter
		backoff     BackoffManager
		timeout     time.Duration
		maxRetries  int

		// generic components accessible via method setters
		verb       string
		pathPrefix string
		subpath    string
		params     url.Values
		headers    http.Header

		// structural elements of the request that are part of the Kubernetes API conventions
		namespace    string
		namespaceSet bool
		resource     string
		resourceName string
		subresource  string

		// output
		err error

		// only one of body / bodyBytes may be set. requests using body are not retriable.
		body      io.Reader
		bodyBytes []byte

		retryFn requestRetryFunc
	}

	// 这里需要一个能够获得*restclient.Request的方式，我们实际使用时会用 rest.Interface 接口类型的实例
	// 这是一个相对底层的工具，封装的是 Kubernetes REST APIS 相应的动作，可以在 client-go 的 rest 包内的 client.go 源文件中看到
	// Interface captures the set of operations for generically interacting with Kubernetes REST apis.
	type Interface interface {
		GetRateLimiter() flowcontrol.RateLimiter
		Verb(verb string) *Request
		Post() *Request
		Put() *Request
		Patch(pt types.PatchType) *Request
		Get() *Request
		Delete() *Request
		APIVersion() schema.GroupVersion
	}

	// 上面 Interface 接口对应的实现，也可以在 client.go 文件中看到
	// RESTClient imposes common Kubernetes API conventions on a set of resource paths.
	// The baseURL is expected to point to an HTTP or HTTPS path that is the parent
	// of one or more resources.  The server should return a decodable API resource
	// object, or an api.Status object which contains information about the reason for
	// any failure.
	//
	// Most consumers should use client.New() to get a Kubernetes API client.
	type RESTClient struct {
		// base is the root URL for all invocations of the client
		base *url.URL
		// versionedAPIPath is a path segment connecting the base URL to the resource root
		versionedAPIPath string

		// content describes how a RESTClient encodes and decodes responses.
		content ClientContentConfig

		// creates BackoffManager that is passed to requests.
		createBackoffMgr func() BackoffManager

		// rateLimiter is shared among all requests created by this client unless specifically
		// overridden.
		rateLimiter flowcontrol.RateLimiter

		// warningHandler is shared among all requests created by this client.
		// If not set, defaultWarningHandler is used.
		warningHandler WarningHandler

		// Set specific behavior of the client.  If not set http.DefaultClient will be used.
		Client *http.Client
	}
```

- 上面的 `RESTClient` 和平时Operator代码中常用的ClientSet的关系，可以通过这个简单的例子了解一下
```golang
	// 在用 ClientSet 去 Get 一个指定名字的 DaemonSet 的时候，调用过程类似这样
	c.AppsV1().DaemonSets("default").Get(ctx, "demo-ds", metav1.GetOptions{})

	// 这里的Get其实就是利用了RESTClient提供的能力
	func (c *daemonSets) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1beta1.DaemonSet, err error) {
		// 即 RESTClient.Get()，返回的是 *rest.Request 对象
		err = c.client.Get().
		       Namespace(c.ns).
			   Resource("daemonsets").
			   Name(name).
			   VersionedParams(&options, scheme.ParameterCodec).
			   Do(ctx).
			   Into(result)
		return
	}
```

### 2. ListWatch对象的初始化

- 上面提到的 ListWatch 对象实现的是 `ListerWatcher` 接口，这个接口也在listwatch.go中定义
	- 这里内嵌了两个接口，分别是 `Lister` 和 `Watcher`
```golang
	// Lister is any object that knows how to perform an initial list.
	type Lister interface {
		// List should return a list type object; the Items field will be extracted, and the
		// ResourceVersion field will be used to start the watch in the right place.
		// List 的返回值是一个 list类型对象，也就是其中有 Items 字段，里面的 ResourceVersion 可以用来监听(watch)
		List(options metav1.ListOptions) (runtime.Object, error)
	}

	// Watcher is any object that knows how to start a watch on a resource.
	type Watcher interface {
		// Watch should begin a watch at the specified version.
		// 从指定的资源版本开始 watch
		Watch(options metav1.ListOptions) (watch.Interface, error)
	}

	// ListerWatcher is any object that knows how to perform an initial list and start a watch on a resource.
	type ListerWatcher interface {
		Lister
		Watcher
	}
```

- ListWatch对象的 `List()` 和 `Watch()` 的实现
```golang
	// List a set of apiserver resources
	func (lw *ListWatch) List(options metav1.ListOptions) (runtime.Object, error) {
		// ListWatch is used in Reflector, which already supports pagination.
		// Don't paginate here to avoid duplication.
		return lw.ListFunc(options)
	}

	// Watch a set of apiserver resources
	func (lw *ListWatch) Watch(options metav1.ListOptions) (watch.Interface, error) {
		return lw.WatchFunc(options)
	}
```