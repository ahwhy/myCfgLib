# client-go Examples

<!-- This directory contains examples that cover various use cases and functionality for client-go. -->
为 client-go 提供各种用例及功能的 examples 

### Auth plugins

<!-- Client configuration is typically loaded from kubeconfig files containing server and credential configuration.
Several plugins for obtaining credentials from external sources are available, but are not loaded by default.
To enable these plugins in your program, import them in your main package. -->

Client 配置通常从包含 server 和凭证配置的 kubeconfig 文件中加载。有几个从外部来源获取凭证的插件是可用的，但默认情况下不会加载。

要在程序中启用这些插件，需要将它们导入主包中。

加载所有 auth plugins:
```go
import _ "k8s.io/client-go/plugin/pkg/client/auth"
```

加载特殊的 auth plugins:
```go
import _ "k8s.io/client-go/plugin/pkg/client/auth/azure"
import _ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
import _ "k8s.io/client-go/plugin/pkg/client/auth/oidc"
```

### Configuration

- [**Authenticate in cluster**](./in-cluster-client-configuration): 配置 client 在 Kubernetes 集群内部运行

- [**Authenticate out of cluster**](./out-of-cluster-client-configuration): 配置 client 从外部访问 Kubernetes 集群

### Basics

- [**Managing resources with API**](./create-update-delete-deployment): Create, get, update, delete a Deployment resource.

### Advanced Concepts

- [**Work queues**](./workqueue): Create a hotloop-free controller with the rate-limited workqueue and the [informer framework][informer].

- [**Custom Resource Definition (CRD)**](https://git.k8s.io/apiextensions-apiserver/examples/client-go):
  Register a custom resource type with the API, create/update/query this custom type, and write a controller that drives the cluster state based on the changes to the custom resources.

- [**Leader election**](./leader-election): 展示使用包 `tools/leaderelection`，该包可用于实现高可用的 controllers

[informer]: https://godoc.org/k8s.io/client-go/tools/cache#NewInformer

### Testing

- [**Fake Client**](./fake-client): Use a fake client in tests.