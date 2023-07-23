# client-go 项目介绍

## 一、Client-go 项目介绍

### 1. client-go 项目结构

- client-go的包结构
  + kubernetes：这个包中放的是用client-gen自动生成的用来访问Kubernetes API的ClientSet，后面会经常看到ClientSet这个工具。
  + discovery：这个包提供了一种机制用来发现API Server支持的API资源。
  + dynamic：这个包中包含dynamic client，用来执行任意API资源对象的通用操作。
  + plugin/pkg/client/auth：这个包提供了可选的用于获取外部源证书的认证插件。
  + transport：这个包用于设置认证和建立连接。
  + tools/cache：这个包中放了很多和开发控制器相关的工具集。

### 2. client-go 版本规则

由于一些历史原因，client-go的版本规则经历了几次变化。不用去关注很早的版本都有哪些规则，简单理解client-go的版本就是一句话：

    Kubernetes版本大于或等于1.17.0时，cllient-go版本使用对应的v0.x.y；
    Kubernetes版本小于1.17.0时，client-go版本使用kubernetes-1.x.y。
    其中，x和y与Kubernetes版本号后两位保持一致，比如Kubernetes v1.17.0对应client-go v0.17.0。

这里说的client-go的版本 体现在tag上，我们在client-go的GitHub代码库的tag列表中可以直观地看到这些[tag](https://github.com/kubernetes/client-go/tags)。下表展示了以Kubernetes 1.17.0版本为中点，client-go和Kubernetes的版本对应关系。

![client-go与Kubernetes的版本对应关系](./images/Client-go与Kubernetes的版本对应关系.jpg)

如表所示，第一行是Kubernetes版本，第一列是client-go版本。在Kubernetes 1.17.0版本之后，client-go老的版本号规则为了更好的兼容性还是保留着，不过最好还是使用新版本号v0.x.y这种格式。

另外，client-go代码库的分支规则和tag又稍有区别，下面简单地通过下表看一下Kubernetes 1.15.n版本之后两个代码库的分支规则对应关系。

![client-go与Kubernetes的版本对应关系](./images/Client-go与Kubernetes%201.15n的版本之后分支对应关系.jpg)

如表所示，从1.18版本开始，两者的分支名称又对应起来了。其实client-go在Kubernetes 1.5版本以前就是现在的分支命名风格，不过从1.5之后变成了2.0，之后就是3.0、4.0、5.0……这种规则了，直到1.18版本。

### 3. 获取 client-go

在写代码的时候需要使用client-go，第一步肯定是通过go get来获取相应版本的client-go依赖。如果需要新版本，可以直接执行：`go get k8s.io/client-go@latest`;

不过这样并不靠谱，一般需要选择明确的版本，最好是和自己使用的Kubernetes集群版本完全一致。可以通过下面的命令来获取需要的版本：`go get k8s.io/client-go@v0.24.6`。


## 二、Client-go 简单使用

### 1. client-go 操作 deployment

- 初始化 DeploymentInterface类型 实例
```golang
  // 获取 home 路径
	homePath := homedir.HomeDir()
	if homePath == "" {
		log.Fatal("failed to get the home directory")
	}
  // 构建 kubeconfig 绝对路径
	kubeconfig := filepath.Join(homePath, ".kube", "config")

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		log.Fatal(err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}

  // 初始化一个DeploymentInterface类型的实例
	dpClient := clientset.AppsV1().Deployments(coreV1.NamespaceDefault)
```

- 实现 createDeployment()函数
```golang
	func createDeployment(dpClient v1.DeploymentInterface) error {
		replicas := int32(2)
		newDp := &appsv1.Deployment{
			ObjectMeta: metav1.ObjectMeta{
				Name: "kube-demoapp",
			},
			Spec: appsv1.DeploymentSpec{
				Replicas: &replicas,
				Selector: &metav1.LabelSelector{
					MatchLabels: map[string]string{
						"app": "kube-demoapp",
					},
				},
				Template: coreV1.PodTemplateSpec{
					ObjectMeta: metav1.ObjectMeta{
						Labels: map[string]string{
							"app": "kube-demoapp",
						},
					},
					Spec: coreV1.PodSpec{
						Containers: []coreV1.Container{
							{
								Name:  "demoapp",
								Image: "ikubernetes/demoapp:v1.0",
								Ports: []coreV1.ContainerPort{
									{
										Name:          "demoapp",
										Protocol:      coreV1.ProtocolTCP,
										ContainerPort: 8080,
									},
								},
							},
						},
					},
				},
			},
		}
		_, err := dpClient.Create(context.TODO(), newDp, metav1.CreateOptions{})

		return err
	}

	// 函数调用
	log.Println("create Deployment")
	if err := createDeployment(dpClient); err != nil {
		log.Fatal(err)
	}
	<-time.Tick(1 * time.Minute)
```

- 实现 updateDeployment()函数
```golang
	func updateDeployment(dpClient v1.DeploymentInterface) error {
		dp, err := dpClient.Get(context.TODO(), "kube-demoapp", metav1.GetOptions{})
		if err != nil {
			return err
		}
		dp.Spec.Template.Spec.Containers[0].Image = "ikubernetes/demoapp:v1.1"

		return retry.RetryOnConflict(
			retry.DefaultBackoff, func() error {
				_, err = dpClient.Update(context.TODO(), dp, metav1.UpdateOptions{})
				return err
			},
		)
	}

	// 函数调用
	log.Println("update Deployment")
	if err := updateDeployment(dpClient); err != nil {
		log.Fatal(err)
	}
	<-time.Tick(1 * time.Minute)
```

- 实现 deleteDeployment()函数
  - 关于PropagationPolicy属性，有3种可选特性
    - DeletePropagationOrphan 不考虑依赖资源
    - DeletePropagationBackground 后台删除依赖资源
    - DeletePropagationForeground 前台删除依赖资源
```golang
	func deleteDeployment(dpClient v1.DeploymentInterface) error {
		deletePolicy := metav1.DeletePropagationForeground

		return dpClient.Delete(
			context.TODO(), "kube-demoapp", metav1.DeleteOptions{
				PropagationPolicy: &deletePolicy,
			},
		)
	}

	// 函数调用
	log.Println("delete Deployment")
	if err := deleteDeployment(dpClient); err != nil {
		log.Fatal(err)
	}
	<-time.Tick(1 * time.Minute)
```

- import
```go
	import (
		appsv1 "k8s.io/api/apps/v1"
		coreV1 "k8s.io/api/core/v1"
		metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
		"k8s.io/client-go/kubernetes"
		v1 "k8s.io/client-go/kubernetes/typed/apps/v1"
		"k8s.io/client-go/tools/clientcmd"
		"k8s.io/client-go/util/homedir"
		"k8s.io/client-go/util/retry"
	)
```