# client-go 源码分析之 Indexer 和 ThreadSafeStore

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


## 二、Client-go Indexer 与 ThreadSafeStore

Indexer主要为对象提供根据一定条件进行检索的能力，典型的实现是通过namespace/name来构造key，通过ThreadSafeStore来存储对象。换言之，Indexer主要依赖于ThreadSafeStore实现，是client-go提供的一种缓存机制，通过检索本地缓存可以有效降低apiserver的压力。

### 1. Indexer 接口和 cache 的实现

- `Indexer` 接口主要是在 `Store` 接口的基础上拓展了对象的检索功能
	- 代码在 `k8s.io/client-go/tools/cache` 包下
	- Indexer接口定义在index.go中
```golang
	// Indexer extends Store with multiple indices and restricts each
	// accumulator to simply hold the current object (and be empty after Delete).
	//
	// There are three kinds of strings here:
	//  1. a storage key, as defined in the Store interface,
	//  2. a name of an index, and
	//  3. an "indexed value", which is produced by an IndexFunc and
	//     can be a field value or any other string computed from the object.
	type Indexer interface {
		Store
		// Index returns the stored objects whose set of indexed values
		// intersects the set of indexed values of the given object, for the named index
		// 根据索引名和给定的对象，返回符合条件的所有对象
		Index(indexName string, obj interface{}) ([]interface{}, error)
		// IndexKeys returns the storage keys of the stored objects whose
		// set of indexed values for the named index includes the given indexed value
		// 根据索引名和索引值，返回符合条件的所有对象的key
		IndexKeys(indexName, indexedValue string) ([]string, error)
		// ListIndexFuncValues returns all the indexed values of the given index
		// 列出索引函数计算出来的所有索引值
		ListIndexFuncValues(indexName string) []string
		// ByIndex returns the stored objects whose set of indexed values
		// for the named index includes the given indexed value
		// 根据索引名和索引值，返回符合条件的所有对象
		ByIndex(indexName, indexedValue string) ([]interface{}, error)
		// GetIndexers return the indexers
		// 获取所有的Indexers，对应map[string]IndexFunc类型
		GetIndexers() Indexers

		// AddIndexers adds more indexers to this store.  If you call this after you already have data
		// in the store, the results are undefined.
		// AddIndexers 需要在数据加入存储前调用，添加更多的索引方法，默认只通过 namespace检索
		AddIndexers(newIndexers Indexers) error
	}

	// Indexers maps a name to an IndexFunc
	type Indexers map[string]IndexFunc

	// IndexFunc knows how to compute the set of indexed values for an object.
	type IndexFunc func(obj interface{}) ([]string, error)

	const (
		// NamespaceIndex is the lookup name for the most common index function, which is to index by the namespace field.
		NamespaceIndex string = "namespace"
	)
```

- `Indexer` 的默认实现是 `cache`，定义在 store.go中
	- 这里涉及两个类型 `keyFunc` 与 `ThreadSafeStore`
	- 从 `Indexer` 的方法的实现来看
		- 这里的逻辑就是调用 `keyFunc()`方法获取key，然后调用 `cacheStorage.Xxx()` 方法完成对应的增删改查过程
```golang
	// `*cache` implements Indexer in terms of a ThreadSafeStore and an associated KeyFunc.
	type cache struct {
		// cacheStorage bears the burden of thread safety for the cache
		cacheStorage ThreadSafeStore
		// keyFunc is used to make the key for objects stored in and retrieved from items, and should be deterministic.
		keyFunc KeyFunc
	}

	var _ Store = &cache{}

	// Add inserts an item into the cache.
	func (c *cache) Add(obj interface{}) error {
		key, err := c.keyFunc(obj)
		if err != nil {
			return KeyError{obj, err}
		}
		c.cacheStorage.Add(key, obj)
		return nil
	}

	// Update sets an item in the cache to its updated state.
	func (c *cache) Update(obj interface{}) error {
		key, err := c.keyFunc(obj)
		if err != nil {
			return KeyError{obj, err}
		}
		c.cacheStorage.Update(key, obj)
		return nil
	}

	// Delete removes an item from the cache.
	func (c *cache) Delete(obj interface{}) error {
		key, err := c.keyFunc(obj)
		if err != nil {
			return KeyError{obj, err}
		}
		c.cacheStorage.Delete(key)
		return nil
	}

	// List returns a list of all the items.
	// List is completely threadsafe as long as you treat all items as immutable.
	func (c *cache) List() []interface{} {
		return c.cacheStorage.List()
	}

	// ListKeys returns a list of all the keys of the objects currently
	// in the cache.
	func (c *cache) ListKeys() []string {
		return c.cacheStorage.ListKeys()
	}

	// GetIndexers returns the indexers of cache
	func (c *cache) GetIndexers() Indexers {
		return c.cacheStorage.GetIndexers()
	}

	// Index returns a list of items that match on the index function
	// Index is thread-safe so long as you treat all items as immutable
	func (c *cache) Index(indexName string, obj interface{}) ([]interface{}, error) {
		return c.cacheStorage.Index(indexName, obj)
	}

	// IndexKeys returns the storage keys of the stored objects whose set of
	// indexed values for the named index includes the given indexed value.
	// The returned keys are suitable to pass to GetByKey().
	func (c *cache) IndexKeys(indexName, indexedValue string) ([]string, error) {
		return c.cacheStorage.IndexKeys(indexName, indexedValue)
	}

	// ListIndexFuncValues returns the list of generated values of an Index func
	func (c *cache) ListIndexFuncValues(indexName string) []string {
		return c.cacheStorage.ListIndexFuncValues(indexName)
	}

	// ByIndex returns the stored objects whose set of indexed values
	// for the named index includes the given indexed value.
	func (c *cache) ByIndex(indexName, indexedValue string) ([]interface{}, error) {
		return c.cacheStorage.ByIndex(indexName, indexedValue)
	}

	func (c *cache) AddIndexers(newIndexers Indexers) error {
		return c.cacheStorage.AddIndexers(newIndexers)
	}

	// Get returns the requested item, or sets exists=false.
	// Get is completely threadsafe as long as you treat all items as immutable.
	func (c *cache) Get(obj interface{}) (item interface{}, exists bool, err error) {
		key, err := c.keyFunc(obj)
		if err != nil {
			return nil, false, KeyError{obj, err}
		}
		return c.GetByKey(key)
	}

	// GetByKey returns the request item, or exists=false.
	// GetByKey is completely threadsafe as long as you treat all items as immutable.
	func (c *cache) GetByKey(key string) (item interface{}, exists bool, err error) {
		item, exists = c.cacheStorage.Get(key)
		return item, exists, nil
	}

	// Replace will delete the contents of 'c', using instead the given list.
	// 'c' takes ownership of the list, you should not reference the list again
	// after calling this function.
	func (c *cache) Replace(list []interface{}, resourceVersion string) error {
		items := make(map[string]interface{}, len(list))
		for _, item := range list {
			key, err := c.keyFunc(item)
			if err != nil {
				return KeyError{item, err}
			}
			items[key] = item
		}
		c.cacheStorage.Replace(items, resourceVersion)
		return nil
	}

	// NewStore returns a Store implemented simply with a map and a lock.
	func NewStore(keyFunc KeyFunc) Store {
		return &cache{
			cacheStorage: NewThreadSafeStore(Indexers{}, Indices{}),
			keyFunc:      keyFunc,
		}
	}

	// NewIndexer returns an Indexer implemented simply with a map and a lock.
	func NewIndexer(keyFunc KeyFunc, indexers Indexers) Indexer {
		return &cache{
			cacheStorage: NewThreadSafeStore(indexers, Indices{}),
			keyFunc:      keyFunc,
		}
	}
```

- `KeyFunc` 类型是这样定义的 `type KeyFunc func(obj interface{}) (string, error)`，即 给一个对象返回一个字符串类型的key
	- `KeyFunc` 的一个默认实现如下 `MetaNamespaceKeyFunc`
	- 可以看到一般情况下返回值是 `<namespace>/<name>`，如果namespace为空，则直接返回name。
```golang
	// ExplicitKey can be passed to MetaNamespaceKeyFunc if you have the key for
	// the object but not the object itself.
	type ExplicitKey string

	// MetaNamespaceKeyFunc is a convenient default KeyFunc which knows how to make
	// keys for API objects which implement meta.Interface.
	// The key uses the format <namespace>/<name> unless <namespace> is empty, then
	// it's just <name>.
	func MetaNamespaceKeyFunc(obj interface{}) (string, error) {
		if key, ok := obj.(ExplicitKey); ok {
			return string(key), nil
		}
		objName, err := ObjectToName(obj)
		if err != nil {
			return "", err
		}
		return objName.String(), nil
	}

	// ObjectToName returns the structured name for the given object,
	// if indeed it can be viewed as a metav1.Object.
	func ObjectToName(obj interface{}) (ObjectName, error) {
		meta, err := meta.Accessor(obj)
		if err != nil {
			return ObjectName{}, fmt.Errorf("object has no meta: %v", err)
		}
		return MetaObjectToName(meta), nil
	}

	// MetaObjectToName returns the structured name for the given object
	func MetaObjectToName(obj metav1.Object) ObjectName {
		if len(obj.GetNamespace()) > 0 {
			return ObjectName{Namespace: obj.GetNamespace(), Name: obj.GetName()}
		}
		return ObjectName{Namespace: "", Name: obj.GetName()}
	}
```

### 2. ThreadSafeStore的实现

**a. 接口与实现**

- `ThreadSafeStore` 是 `Indexer` 的核心逻辑所在
	- `Indexer` 的多数方法是直接调用内部 `cacheStorage` 属性的方法实现的
	- 接口定义在 thread_safe_store.go 中
```golang
	// ThreadSafeStore is an interface that allows concurrent indexed
	// access to a storage backend.  It is like Indexer but does not
	// (necessarily) know how to extract the Store key from a given
	// object.
	//
	// The guarantees of thread safety provided by List/Get are only valid if the caller
	// treats returned items as read-only. For example, a pointer inserted in the store
	// through `Add` will be returned as is by `Get`. Multiple clients might invoke `Get`
	// on the same key and modify the pointer in a non-thread-safe way. Also note that
	// modifying objects stored by the indexers (if any) will *not* automatically lead
	// to a re-index. So it's not a good idea to directly modify the objects returned by
	// Get/List, in general.
	type ThreadSafeStore interface {
		Add(key string, obj interface{})
		Update(key string, obj interface{})
		Delete(key string)
		Get(key string) (item interface{}, exists bool)
		List() []interface{}
		ListKeys() []string
		Replace(map[string]interface{}, string)
		Index(indexName string, obj interface{}) ([]interface{}, error)
		IndexKeys(indexName, indexedValue string) ([]string, error)
		ListIndexFuncValues(name string) []string
		ByIndex(indexName, indexedValue string) ([]interface{}, error)
		GetIndexers() Indexers

		// AddIndexers adds more indexers to this store.  If you call this after you already have data
		// in the store, the results are undefined.
		AddIndexers(newIndexers Indexers) error
		// Resync is a no-op and is deprecated
		Resync() error
	}

	// threadSafeMap implements ThreadSafeStore
	type threadSafeMap struct {
		lock  sync.RWMutex
		items map[string]interface{}

		// index implements the indexing functionality
		index *storeIndex
	}

	// storeIndex implements the indexing functionality for Store interface
	type storeIndex struct {
		// indexers maps a name to an IndexFunc
		indexers Indexers
		// indices maps a name to an Index
		indices Indices
	}

	// Indexers maps a name to an IndexFunc
	type Indexers map[string]IndexFunc

	// Indices maps a name to an Index
	type Indices map[string]Index

	// IndexFunc knows how to compute the set of indexed values for an object.
	type IndexFunc func(obj interface{}) ([]string, error)

	// Index maps the indexed value to a set of keys in the store that match on that value
	type Index map[string]sets.String

	// NewThreadSafeStore creates a new instance of ThreadSafeStore.
	func NewThreadSafeStore(indexers Indexers, indices Indices) ThreadSafeStore {
		return &threadSafeMap{
			items: map[string]interface{}{},
			index: &storeIndex{
				indexers: indexers,
				indices:  indices,
			},
		}
	}
```

![理解IndexFunc、Indexers和Indices几个对象](./images/理解IndexFunc、Indexers和Indices几个对象.jpg)

`Indexers` 中保存的是 `Index` 函数map，一个典型的实现是字符串namespace作为key，`IndexFunc` 类型的实现 `MetaNamespaceIndexFunc` 函数作为value，也就是通过namespace来检索时，借助 `Indexers` 可以拿到对应的计算 `Index` 的函数，接着调用这个函数把对象传进去，就可以计算出这个对象对应的key，就是具体的namespace值，比如default、kube-system这种格式的字符串。

然后在 `Indices` 中保存的也是一个map，key是上面计算出来的default这种格式的namespace值，value是一个set，而set表示的是这个default namespace下的一些具体pod的 `<namespace>/<name>` 这类格式字符串。最后拿着这个key，就可以在items中检索到对应的对象。

**b. Add()、Update()等方法的实现**

- threadSafeMap如何实现添加元素
	- `Add()`、`Update()`、`Delete()` 方法
	- 更复杂的逻辑在 `updateIndices()` 方法
```golang
	func (c *threadSafeMap) Add(key string, obj interface{}) {
		c.Update(key, obj)
	}

	func (c *threadSafeMap) Update(key string, obj interface{}) {
		c.lock.Lock()
		defer c.lock.Unlock()
		oldObject := c.items[key]
		c.items[key] = obj
		c.index.updateIndices(oldObject, obj, key)
	}

	func (c *threadSafeMap) Delete(key string) {
		c.lock.Lock()
		defer c.lock.Unlock()
		if obj, exists := c.items[key]; exists {
			c.index.updateIndices(obj, nil, key)
			delete(c.items, key)
		}
	}

	// updateIndices modifies the objects location in the managed indexes:
	// - for create you must provide only the newObj
	// - for update you must provide both the oldObj and the newObj
	// - for delete you must provide only the oldObj
	// updateIndices must be called from a function that already has a lock on the cache
	func (i *storeIndex) updateIndices(oldObj interface{}, newObj interface{}, key string) {
		var oldIndexValues, indexValues []string
		var err error
		for name, indexFunc := range i.indexers {
			if oldObj != nil {
				oldIndexValues, err = indexFunc(oldObj)
			} else {
				oldIndexValues = oldIndexValues[:0]
			}
			if err != nil {
				panic(fmt.Errorf("unable to calculate an index entry for key %q on index %q: %v", key, name, err))
			}

			if newObj != nil {
				indexValues, err = indexFunc(newObj)
			} else {
				indexValues = indexValues[:0]
			}
			if err != nil {
				panic(fmt.Errorf("unable to calculate an index entry for key %q on index %q: %v", key, name, err))
			}

			index := i.indices[name]
			if index == nil {
				index = Index{}
				i.indices[name] = index
			}

			if len(indexValues) == 1 && len(oldIndexValues) == 1 && indexValues[0] == oldIndexValues[0] {
				// We optimize for the most common case where indexFunc returns a single value which has not been changed
				continue
			}

			for _, value := range oldIndexValues {
				i.deleteKeyFromIndex(key, value, index)
			}
			for _, value := range indexValues {
				i.addKeyToIndex(key, value, index)
			}
		}
	}
```

### 3. 各种Index方法的实现

**a. Index()方法**

- `Index()` 方法的实现，其作用是给定一个 obj 和 indexName
	- 例如 pod1 和 namespace，然后返回 pod1 所在 namespace 下的所有 pod
```golang
	// Index returns a list of items that match the given object on the index function.
	// Index is thread-safe so long as you treat all items as immutable.
	func (c *threadSafeMap) Index(indexName string, obj interface{}) ([]interface{}, error) {
		c.lock.RLock()
		defer c.lock.RUnlock()

		storeKeySet, err := c.index.getKeysFromIndex(indexName, obj)
		if err != nil {
			return nil, err
		}

		list := make([]interface{}, 0, storeKeySet.Len())
		for storeKey := range storeKeySet {
			list = append(list, c.items[storeKey])
		}
		return list, nil
	}
```

**b. ByIndex()方法**

- `ByIndex()` 方法的实现，直接传递indexedValue，就不需要通过obj去计算key了
	- 例如 indexName==namespace&indexValue==default 就是直接检索default下的资源对象
```golang
	// ByIndex returns a list of the items whose indexed values in the given index include the given indexed value
	func (c *threadSafeMap) ByIndex(indexName, indexedValue string) ([]interface{}, error) {
		c.lock.RLock()
		defer c.lock.RUnlock()

		set, err := c.index.getKeysByIndex(indexName, indexedValue)
		if err != nil {
			return nil, err
		}
		list := make([]interface{}, 0, set.Len())
		for key := range set {
			list = append(list, c.items[key])
		}

		return list, nil
	}
```

**c. IndexKeys()方法**

- `IndexKeys()` 方法的实现，和上面的方法返回obj列表的方式不同，这里只返回key列表，即 `[]string{"default/pod_1"}` 这种格式的数据
```golang
	// IndexKeys returns a list of the Store keys of the objects whose indexed values in the given index include the given indexed value.
	// IndexKeys is thread-safe so long as you treat all items as immutable.
	func (c *threadSafeMap) IndexKeys(indexName, indexedValue string) ([]string, error) {
		c.lock.RLock()
		defer c.lock.RUnlock()

		set, err := c.index.getKeysByIndex(indexName, indexedValue)
		if err != nil {
			return nil, err
		}
		return set.List(), nil
	}
```