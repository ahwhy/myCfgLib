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

Informer 这个词的出镜率很高，与 Reflector、WorkQueue等组件不同，Informer相对来说更加模糊，在很多文章中都可以看到 Informer 的身影，在源码中真的去找一个叫作Informer的对象，却又发现找不到一个单纯的Informer，但是有很多结构体或者接口中包含Informer这个词。

在一开始提到过Informer从DeltaFIFO中Pop相应的对象，然后通过Indexer将对象和索引丢到本地cache中，再触发相应的事件处理函数（Resource Event Handlers）的运行。接下来通过源码，重新来梳理一下整个过程。

### 1. Informer 即 Controller

**a. Controller结构体与Controller接口**

Informer通过一个Controller对象来定义，本身结构很简单，在k8s.io/client-go/tools/cache包中的controller.go源文件中可以看到

Controller的定义：
这里有我们熟悉的Reflector，可以猜到Informer启动时会去运行Reflector，从而通过Reflector实现list-watch apiserver，更新“事件”到DeltaFIFO中用于进一步处理。我们继续了解controller对应的Controller接口：
这里的核心方法很明显是Run(stopCh<-chan struct{})，Run负责两件事情：
1）构造Reflector利用ListerWatcher的能力将对象事件更新到DeltaFIFO。
2）从DeltaFIFO中Pop对象后调用ProcessFunc来处理。

2.Controller的初始化
同样，在controller.go文件中有如下代码：
这里没有太多的逻辑，主要是传递了一个Config进来，可以猜到核心逻辑是Config从何而来以及后面如何使用。我们先向上跟踪Config从哪里来，New()的调用有几个地方，我们不去看newInformer()分支的代码，因为实际开发中主要是使用SharedIndexInformer，两个入口初始化Controller的逻辑类似，直接跟踪更实用的一个分支，查看func (s *sharedIndexInformer) Run(stopCh<-chan struct{})方法中如何调用New()，代码位于shared_informer.go中：
这里只保留了主要代码，后面会分析SharedIndexInformer，所以先不纠结SharedIndexInformer的细节，我们从这里可以看到SharedIndexInformer的Run()过程中会构造一个Config，然后创建Controller，最后调用Controller的Run()方法。另外，这里也可以看到前面分析过的DeltaFIFO、ListerWatcher等，其中的Process:s.HandleDeltas这一行也比较重要，Process属性的类型是ProcessFunc，可以看到具体的ProcessFunc是HandleDeltas方法。

3.Controller的启动

上面提到Controller的初始化本身没有太多的逻辑，主要是构造了一个Config对象传递进来，所以Controller启动时肯定会有这个Config的使用逻辑。我们回到controller.go文件具体查看：
这里的代码逻辑很简单，构造Reflector后运行起来，然后执行c.processLoop，显然Controller的业务逻辑隐藏在processLoop方法中。我们继续来看processLoop的代码逻辑。4.processLoop
这里的代码逻辑是从DeltaFIFO中Pop出一个对象丢给PopProcessFunc处理，如果失败了就re-enqueue到DeltaFIFO中。我们前面提到过这里的PopProcessFunc由HandleDeltas()方法来实现，所以这里的主要逻辑就转到了HandleDeltas()是如何实现的。5.HandleDeltas()
如果大家记不清DeltaFIFO的存储结构，可以回到前面相关章节看一下DeltaFIFO的结构图，然后回到这里查看源码。代码位于shared_informer.go文件中：
代码逻辑都落在processDeltas()函数的调用上，我们继续看下面的代码：
这里的代码逻辑主要是遍历一个Deltas中的所有Delta，然后根据Delta的类型来决定如何操作Indexer，也就是更新本地cache，同时分发相应的通知。

### 2. SharedIndexInformer对象

1.SharedIndexInformer是什么
在Operator开发中，如果不使用controller-runtime库，也就是不通过Kubebuilder等工具来生成脚手架，经常会用到SharedInformerFactory，比如典型的sample-controller中的main()函数：
这里可以看到我们依赖于kubeInformerFactory.Apps().V1().Deployments()提供一个Informer，其中的Deployments()方法返回的是DeploymentInformer类型，DeploymentInformer又是什么呢？我们继续往下看，在client-go的informers/apps/v1包的deployment.go文件中有相关定义：
可以看到所谓的DeploymentInformer是由Informer和Lister组成的，也就是说平时编码时用到的Informer本质就是一个SharedIndexInformer。

杨傲
2.SharedIndexInformer接口的定义
回到shared_informer.go文件中，可以看到SharedIndexInformer接口的定义：
这里的Indexer就很熟悉了，SharedInformer又是什么呢？我们继续往下看：3.sharedIndexInformer结构体的定义
继续来看SharedIndexInformer接口的实现sharedIndexerInformer是如何定义的，同样在shared_informer.go文件中查看代码：
这里的Indexer、Controller、ListerWatcher等都是熟悉的组件，sharedProcessor在前面已经遇到过，这也是一个需要关注的重点逻辑，5.7.3节专门来分析sharedProcessor的实现逻辑。4.sharedIndexInformer的启动
继续来看sharedIndexInformer的Run()方法，其代码在shared_informer.go文件中，这里除了将在5.7.3节介绍的sharedProcessor外，几乎已经没有陌生的内容了：

### 3. sharedProcessor对象
sharedProcessor中维护了processorListener集合，然后分发通知对象到listeners，先研究结构定义，其代码在shared_informer.go中：
这里可以看到一个processorListener类型，下面看一下这个类型是怎么定义的：
可以看到processorListener中有一个ResourceEventHandler，这是我们认识的组件。processorListener有三个主要方法：
·run()。
·add(notification interface{})。
·pop()。
我们逐一来看这三个方法的实现：


### 4. 关于SharedInformerFactory
SharedInformerFactory是在开发Operator的过程中经常会接触到的一个比较高层的抽象对象，接下来开始详细分析这个对象的源码。SharedInformerFactory定义在k8s.io/client-go/tools/cache包下。下文在不做特殊说明的情况下，提到的所有源文件都指的是这个包内的源文件。1.SharedInformerFactory的定义
SharedInformerFactory接口定义在factory.go文件中：
这里可以看到一个internalinterfaces.SharedInformerFactory接口，我们看一下这个接口的定义，代码在internalinterfaces/factory_interfaces.go中：
这里可以看到熟悉的SharedIndexInformer。
然后了解ForResource(resource schema.GroupVersionResource) (GenericInformer,error)这行代码的逻辑，这里接收一个GVR，返回了一个GenericInformer。什么是GenericInformer呢？我们在generic.go中可以看到相应的定义：
接着看SharedInformerFactory接口剩下的一大堆相似的方法，我们以Apps() apps.Interface为例，这个Interface定义在apps/interface.go中：
这时大家的关注点肯定是这里的v1.Interface类型是怎么定义的，继续到apps/v1/interface.go文件中查看：
到这里已经有看着很眼熟的Deployments() DeploymentInformer之类的代码了，前面看过DeploymentInformer的定义：
现在也就不难理解SharedInformerFactory的作用了，它提供了所有API group-version的资源对应的SharedIndexInformer，也就不难理解前面引用的sample-controller中的这行代码：
通过其可以拿到一个Deployment资源对应的SharedIndexInformer。2.SharedInformerFactory的初始化
继续来看SharedInformerFactory的New()逻辑，其代码在factory.go中：
可以看到参数非常简单，主要是需要一个ClientSet，毕竟ListerWatcher的能力本质还是client提供的。继续来看这里调用的NewSharedInformerFactoryWithOptions()函数：
杨傲
3.SharedInformerFactory的启动过程
最后查看SharedInformerFactory是如何启动的，Start()方法同样位于factory.go源文件中：

### 5. 小结
我们从一个基础Informer-Controller开始介绍，先分析了Controller的能力，其通过构造Reflector并启动从而能够获取指定类型资源的“更新”事件，然后通过事件构造Delta放到DeltaFIFO中，进而在processLoop中从DeltaFIFO里pop Deltas来处理，一方面将对象通过Indexer同步到本地cache（也就是一个ThreadSafeStore），另一方面调用ProcessFunc来处理这些Delta。
然后SharedIndexInformer提供了构造Controller的能力，通过HandleDeltas()方法实现上面提到的ProcessFunc，同时还引入了sharedProcessor在HandleDeltas()中用于事件通知的处理。sharedProcessor分发事件通知时，接收方是内部继续抽象出来的processorListener，在processorListener中完成了ResourceEventHandler回调函数的具体调用。
最后SharedInformerFactory又进一步封装了提供所有API资源对应的SharedIndexInformer的能力。也就是说一个SharedIndexInformer可以处理一种类型的资源，比如Deployment或者Pod等，而通过SharedInformerFactory可以轻松构造任意已知类型的SharedIndexInformer。另外，这里用到了ClientSet提供的访问所有API资源的能力，通过它也就能够完整实现整套Informer程序逻辑了。
