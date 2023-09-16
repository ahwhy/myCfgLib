# Kubernetes Webhook

## 一、Kubernetes Webhook

### 1. Kubernetes API 访问控制

Kubernetes API 有好几种方式，比如使用 kubectl 命令、使用 client-go 之类的开发库、直接通过 REST 请求等。不管是一个使用kubectl的真人用户，还是一个ServiceAccount，都可以通过API访问认证，这个过程 k8s 社区官网有张很直观的[图片](https://kubernetes.io/docs/concepts/security/controlling-access/)

![access-control-overview](../images/access-control-overview.svg)

当一个访问请求发送到 API Server 的时候，会依次经过认证、鉴权、准入控制三个主要的过程。下面介绍的 `Admission Webhook` 就是这里提到的"准入控制"的范畴

准入控制（Admission Control）模块，能够实现更改一个请求的内容或者决定是否拒绝一个请求的功能。准入控制主要是在一个对象发生变更时生效，变更包括创建、更新、删除等动作，也就是不包含查询动作。如果配置了多个准入控制模块，那么这些模块是按顺序工作的。

关于拒绝请求这个能力，一个请求在多个准入控制模块中有一个模块拒绝，这个请求就会被拒绝，这和认证或者鉴权模块明显不一样。而更改一个请求内容的能力，主要用于给一些请求字段设置默认值。

准入控制器基本都是在 kube-apiserver 中实现的，所以它们的启用也是通过在 kube-apiserver 的启动参数上添加相应配置，比如：

    kube-apiserver --enable-admission-plugins=NamespaceLifecycle,LimitRanger,NodeRestriction,PodSecurityPolicy,PodSecurity ...

可以在 k8s 社区官网找到这部分的[描述](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#what-does-each-admission-controller-do)中看到目前有哪些准入控制器以及它们的作用。

这里的多数准入控制器只能决定它们的启用或者禁用，除了这类在 kube-apiserver 内部实现的准入控制器外，还有两个特殊的准入控制器: `ValidatingAdmissionWebhook` 和 `MutatingAdmissionWebhook`。

这是Kubernetes提供的一种拓展机制，让用户能够通过 Webhook 的方式独立于 kube-apiserver 运行自己的准入控制逻辑。


### 2. Admission Webhook介绍

顾名思义，`Admission Webhook` 是一个 HTTP 回调钩子，可以用来接收"准入请求"，然后对这个请求做相应的逻辑处理。

- Admission Webhook 有两种
	- ValidatingAdmissionWebhook。
	- MutatingAdmissionWebhook。

先执行的是 `MutatingAdmissionWebhook`，这个准入控制器可以修改请求对象，主要用来注入自定义字段；当这个对象被 API Server 校验时，就会回调 `ValidatingAdmissionWebhook`，然后相应的自定义校验策略就会被执行，以决定这个请求能否被通过。


### 3. Admission Webhook的实现

可以通过 Kubebuilder 的 create webhook 命令来生成实现 Admission Webhook 的代码脚手架
```shell
# 添加webhook
➜ kubebuilder create webhook --group apps --version v1 --kind Application --defaulting --programmatic-validation
Writing kustomize manifests for you to edit...
Writing scaffold for you to edit...
api/v1/application_webhook.go
api/v1/webhook_suite_test.go
Update dependencies:
$ go mod tidy
Running make:
$ make generate
test -s /Users/workspace/MyOperatorProjects/clusterops-operator/bin/controller-gen && /Users/workspace/MyOperatorProjects/clusterops-operator/bin/controller-gen --version | grep -q v0.12.0 || \
	GOBIN=/Users/workspace/MyOperatorProjects/clusterops-operator/bin go install sigs.k8s.io/controller-tools/cmd/controller-gen@v0.12.0
/Users/workspace/MyOperatorProjects/clusterops-operator/bin/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./..."
Next: implement your new Webhook and generate the manifests with:
$ make manifests
```
这个命令执行完成后，可以看到项目内多了文件。

打开 `api/v1/application_webhook.go` 源文件，可以看到里面有一个 `Default()` 方法。在 `Default()` 方法中就可以完成 `MutatingAdmissionWebhook` 的相关逻辑。

**a. 实现MutatingAdmissionWebhook**

以 Replicas 默认值注入为例，比如用户提交的 Application 配置中没有给出 Replicas 的大小，那么注入一个默认值3，代码如下：
```golang
	// Default implements webhook.Defaulter so a webhook will be registered for the type
	func (r *Application) Default() {
		applicationlog.Info("default", "name", r.Name)

		if r.Spec.Deployment.Replicas == nil {
			r.Spec.Deployment.Replicas = new(int32)
			*r.Spec.Deployment.Replicas = 3
		}
	}
```

**b. 实现ValidatingAdmissionWebhook**

在 `application_webhook.go` 源文件中继续往后看，可以发现有3个 Validate 方法，分别是 `ValidateCreate`、`ValidateUpdate`和`ValidateDelete`。顾名思义，这几个Validate方法的触发条件分别是相应对象在创建、更新、删除的时候。

这里简单定义一个针对 Replicas 数量的 Admission
```golang
	var _ webhook.Validator = &Application{}

	// ValidateCreate implements webhook.Validator so a webhook will be registered for the type
	func (r *Application) ValidateCreate() (admission.Warnings, error) {
		applicationlog.Info("validate create", "name", r.Name)

		return r.vaildateApplication()
	}

	// ValidateUpdate implements webhook.Validator so a webhook will be registered for the type
	func (r *Application) ValidateUpdate(old runtime.Object) (admission.Warnings, error) {
		applicationlog.Info("validate update", "name", r.Name)

		return r.vaildateApplication()
	}

	// ValidateDelete implements webhook.Validator so a webhook will be registered for the type
	func (r *Application) ValidateDelete() (admission.Warnings, error) {
		applicationlog.Info("validate delete", "name", r.Name)

		return nil, nil
	}

	func (r *Application) vaildateApplication() (admission.Warnings, error) {
		if *r.Spec.Deployment.Replicas > 10 {
			return []string{"Replicas Warning"}, fmt.Errorf("replicas too many error")
		}

		return []string{}, nil
	}
```

这时如果想在本地运行测试Webhook，默认需要准备证书，放到 `/tmp/k8s-webhook-server/serving-certs/tls.{crt,key}` 中，然后执行 `make run` 命令。


### 4. cert-manager部署