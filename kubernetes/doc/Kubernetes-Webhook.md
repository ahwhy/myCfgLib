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


### 4. cert-manager 部署

在部署 Webhook 之前需要先安装 cert-manager，用来实现证书签发功能。关于cert-manager的详细介绍可以参考[官方文档](https://cert-manager.io/docs/)。

cert-manager 提供了 helm Chart 包方式部署
```shell
➜ helm repo add jetstack https://charts.jetstack.io
"jetstack" has been added to your repositories

➜ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "jetstack" chart repository
Update Complete. ⎈Happy Helming!⎈

➜ helm search repo jetstack
NAME                                   	CHART VERSION	APP VERSION	DESCRIPTION
jetstack/cert-manager                  	v1.13.0      	v1.13.0    	A Helm chart for cert-manager
jetstack/cert-manager-approver-policy  	v0.7.0       	v0.7.0     	A Helm chart for cert-manager-approver-policy
jetstack/cert-manager-csi-driver       	v0.5.0       	v0.5.0     	A Helm chart for cert-manager-csi-driver
jetstack/cert-manager-csi-driver-spiffe	v0.4.0       	v0.4.0     	cert-manager csi-driver-spiffe is a CSI plugin ...
jetstack/cert-manager-google-cas-issuer	v0.7.1       	v0.7.1     	A Helm chart for jetstack/google-cas-issuer
jetstack/cert-manager-istio-csr        	v0.7.0       	v0.7.0     	istio-csr enables the use of cert-manager for i...
jetstack/cert-manager-trust            	v0.2.1       	v0.2.0     	DEPRECATED: The old name for trust-manager. Use...
jetstack/trust-manager                 	v0.6.0       	v0.6.0     	trust-manager is the easiest way to manage TLS ...
jetstack/version-checker               	v0.2.6       	v0.2.6     	A Helm chart for version-checker

# 可以看到 cert-manager 对应的 Chart 名字是 jetstack/cert-manager，直接安装就好
➜ helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.0 \
  --set installCRDs=true 
NAME: cert-manager
LAST DEPLOYED: Sat Sep 16 21:16:22 2023
NAMESPACE: cert-manager
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
cert-manager v1.13.0 has been deployed successfully!

In order to begin issuing certificates, you will need to set up a ClusterIssuer
or Issuer resource (for example, by creating a 'letsencrypt-staging' issuer).

More information on the different types of issuers and how to configure them
can be found in our documentation:

https://cert-manager.io/docs/configuration/

For information on how to configure cert-manager to automatically provision
Certificates for Ingress resources, take a look at the `ingress-shim`
documentation:

https://cert-manager.io/docs/usage/ingress/

# 确认组件状态
➜ kubectl -n cert-manager get all
NAME                                           READY   STATUS    RESTARTS   AGE
pod/cert-manager-64d969474b-dlsqj              1/1     Running   0          5m38s
pod/cert-manager-cainjector-646d9649d9-wxfpd   1/1     Running   0          5m38s
pod/cert-manager-webhook-5995b68bf7-npjqb      1/1     Running   0          5m38s

NAME                           TYPE        CLUSTER-IP        EXTERNAL-IP   PORT(S)    AGE
service/cert-manager           ClusterIP   192.168.57.154    <none>        9402/TCP   5m38s
service/cert-manager-webhook   ClusterIP   192.168.249.184   <none>        443/TCP    5m38s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/cert-manager              1/1     1            1           5m39s
deployment.apps/cert-manager-cainjector   1/1     1            1           5m39s
deployment.apps/cert-manager-webhook      1/1     1            1           5m39s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/cert-manager-64d969474b              1         1         1       5m39s
replicaset.apps/cert-manager-cainjector-646d9649d9   1         1         1       5m39s
replicaset.apps/cert-manager-webhook-5995b68bf7      1         1         1       5m39s

NAME                             ALBID                    DNSNAME                                              PORT&PROTOCOL   CERTID   AGE
albconfig.alibabacloud.com/alb   alb-jfbc0gfao3ox1oezcj   alb-jfbc0gfao3ox1oezcj.cn-beijing.alb.aliyuncs.com                            17d

NAME                                                                                             AGE
containernetworkfilesystem.storage.alibabacloud.com/cnfs-nas-c4b76f485f21d4e769e0a2ffed67dcd2b   51d
```


### 5. Webhook部署运行

已经准备好了 [Webhook 代码](https://github.com/ahwhy/clusterops-operator)，接着就部署到环境中来看一下运行结果。

**a. 构建并推送镜像**

执行以下两行命令来构建镜像，并把镜像上传到之前准备好的仓库中：
```shell
➜ make docker-build IMG=registry.cn-hangzhou.aliyuncs.com/ahwhya/clusterops-operator:v0.0.1

➜ docker push registry.cn-hangzhou.aliyuncs.com/ahwhya/clusterops-operator:v0.0.1
```

**b. 部署CRD**

CRD的部署很简单，执行以下命令
```shell
➜ make install
```

**c. 证书相关配置**

在前面的步骤中部署了 cert-manager，但是要使用 cert-manager 还需要做一些配置。

首先 `config/default/kustomization.yaml` 文件需要做一些调整，打开几行注释内容，最后看起来应该是这样的：
```yaml

namespace: clusterops-operator-system

namePrefix: clusterops-operator-

resources:
- ../crd
- ../rbac
- ../manager
- ../webhook
- ../certmanager

patchesStrategicMerge:
- manager_auth_proxy_patch.yaml
- manager_webhook_patch.yaml
- webhookcainjection_patch.yaml

replacements:
 - source: # Add cert-manager annotation to ValidatingWebhookConfiguration, MutatingWebhookConfiguration and CRDs
     kind: Certificate
     group: cert-manager.io
     version: v1
     name: serving-cert # this name should match the one in certificate.yaml
     fieldPath: .metadata.namespace # namespace of the certificate CR
   targets:
     - select:
         kind: ValidatingWebhookConfiguration
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 0
         create: true
     - select:
         kind: MutatingWebhookConfiguration
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 0
         create: true
     - select:
         kind: CustomResourceDefinition
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 0
         create: true
 - source:
     kind: Certificate
     group: cert-manager.io
     version: v1
     name: serving-cert # this name should match the one in certificate.yaml
     fieldPath: .metadata.name
   targets:
     - select:
         kind: ValidatingWebhookConfiguration
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 1
         create: true
     - select:
         kind: MutatingWebhookConfiguration
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 1
         create: true
     - select:
         kind: CustomResourceDefinition
       fieldPaths:
         - .metadata.annotations.[cert-manager.io/inject-ca-from]
       options:
         delimiter: '/'
         index: 1
         create: true
 - source: # Add cert-manager annotation to the webhook Service
     kind: Service
     version: v1
     name: webhook-service
     fieldPath: .metadata.name # namespace of the service
   targets:
     - select:
         kind: Certificate
         group: cert-manager.io
         version: v1
       fieldPaths:
         - .spec.dnsNames.0
         - .spec.dnsNames.1
       options:
         delimiter: '.'
         index: 0
         create: true
 - source:
     kind: Service
     version: v1
     name: webhook-service
     fieldPath: .metadata.namespace # namespace of the service
   targets:
     - select:
         kind: Certificate
         group: cert-manager.io
         version: v1
       fieldPaths:
         - .spec.dnsNames.0
         - .spec.dnsNames.1
       options:
         delimiter: '.'
         index: 1
         create: true
```

接着还需要调整 `config/crd/kustomization.yaml` 文件
```yaml
resources:
- bases/apps.clusterops.io_applications.yaml
#+kubebuilder:scaffold:crdkustomizeresource

patches:
- path: patches/webhook_in_applications.yaml
#+kubebuilder:scaffold:crdkustomizewebhookpatch

- path: patches/cainjection_in_applications.yaml
#+kubebuilder:scaffold:crdkustomizecainjectionpatch

configurations:
- kustomizeconfig.yaml
```

**b. 部署控制器**

接下来可以部署控制器
```shell
➜ make deploy
```

**e. 查看结果**
最后查看Pod是否正常运行
```shell
➜ kubectl -n clusterops-operator-system get deployment,pod
NAME                                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/clusterops-operator-controller-manager   2/2     2            2           11h

NAME                                                          READY   STATUS    RESTARTS   AGE
pod/clusterops-operator-controller-manager-86d548cb6f-pptkz   2/2     Running   0          11h
pod/clusterops-operator-controller-manager-86d548cb6f-th5hh   2/2     Running   0          11h
```


### 6. Webhook测试

准备一个yaml，这里的replicas给了12，然后 appky 一下看看 Validator 是否生效
```shell
➜ cat application/appdemo.yaml | grep replicas
    replicas: 12
➜ kubectl apply -f application/appdemo.yaml
Warning: Replicas Warning
Error from server (Forbidden): error when creating "application/appdemo.yaml": admission webhook "vapplication.kb.io" denied the request: replicas too many error
```
符合预期，得到了一个 replicas too many error 错误

接着将 replicas 字段删除，使用同样的方式可以验证 Defaulter 能否正常工作
```shell
➜ cat application/appdemo.yaml | grep replica

➜ kubectl apply -f application/appdemo.yaml
application.apps.clusterops.io/appdemo created

➜ kubectl get pod -l app=demoapp
NAME                       READY   STATUS    RESTARTS   AGE
appdemo-6954b8cbd8-4ts7m   1/1     Running   0          51s
appdemo-6954b8cbd8-bzw4t   1/1     Running   0          51s
appdemo-6954b8cbd8-tx98r   1/1     Running   0          51s
```
结果是在不设置Replicas的情况下，Replicas默认值会变成3


### 7. 文档案例

- [准入控制器：ValidatingAdmissionWebhook 实现](https://andblog.cn/3061)
