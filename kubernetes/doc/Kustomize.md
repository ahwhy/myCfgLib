# 通过 Kustomize 的配置管理

## 一、了解 Kustomize

`Kustomize` 的代码库 [GitHub 地址](https://github.com/kubernetes-sigs/kustomize)。Kustomize 是 Kubernetes 原生配置管理工具，实现了类似 sed 的给资源配置文件"打补丁"的能力。Kubernetes 1.14.0 版本已经集成到了 kubectl 命令中，所以也可以通过 kubectl 的子命令来使用Kustomize.

### 1. Kustomize 的基本概念

- Kustomize 中的几个关键术语
    - kustomization 这个词指代的是一个 kustomization.yaml 文件
        - 或者更广义地理解为一个包含 kustomization.yaml 文件的目录以及这个 kustomization.yaml 文件中引用的所有其他文件
    - base 指的是被其他 kustomization 引用的一个 kustomization 
        - 换言之，任何一个 kustomization a 被另一个 kustomization b 引用时，a 是 b 的 base，
        - 这时如果新增一个 kustomization c 来引用 b，那么 b 也就是 c 的base
        - 即，base是一个相对的概念，而不是某种属性标识
    - overlay 与 base 相对应，依赖另一个 kustomization 的 kustomization 被称为 overlay
        - 如果 kustomization b 引用了 kustomization a，那么 b 是 a 的 overlay，a 是 b 的 base


## 二、Kustomize 的安装

Kustomize 提供了 Linux/Darwin 系统 *amd64/arm64 架构的二进制可执行文件(Windows等也支持，不过不建议在Windows上使用这些工具)。可以到Kustomize 项目的 [release](https://github.com/kubernetes-sigs/kustomize/releases)页面去下载对应的压缩包。
```shell
➜ wget https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.1.1/kustomize_v5.1.1_linux_amd64.tar.gz

➜ tar -xzvf kustomize_v5.1.1_linux_amd64.tar.gz
x kustomize

➜ sudo mv kustomize /usr/local/bin/

➜ kustomize version
```


## 三、使用 Kustomize 生成资源

在 Kubernetes 中通常使用 ConfigMap 和 Secret 来分别存储配置文件和敏感配置信息等，这些内容往往是在 Kubernetes 集群之外的。比如通过 Secret 来存储数据库连接信息，这些信息也许记录在特定机器的环境变量中，也许保存在某台机器的一个 TXT 文本文件中，总之这些信息和 Kubernetes 集群本身没有关联。但是应用以 Pod 的方式运行在一个 Kubernetes 集群之内时，就需要使用 ConfigMap 或者 Secret 资源对象来获取各种配置，下面看下如何通过 Kustomize 快速创建 ConfigMap 和 Secret。

### 1. ConfigMap生成器

一般通过 configMapGenerator 来自动管理 ConfigMap 资源文件的创建和引用等。

**a. 从配置文件生成 ConfigMap**
```shell
➜ mkdir Kustomize && cd Kustomize

➜ cat <<EOF >config.txt
key=value
EOF

➜ cat <<EOF >kustomization.yaml
configMapGenerator:
- name: app-config
  files:
  - config.txt
EOF

# 然后有两种方式来构建 ConfigMap
➜ kustomize build .
apiVersion: v1
data:
  config.txt: |
    key=value
kind: ConfigMap
metadata:
  name: app-config-gc6cm9fg4c

➜ kubectl kustomize .
apiVersion: v1
data:
  config.txt: |
    key=value
kind: ConfigMap
metadata:
  name: app-config-gc6cm9fg4c
```
可以看到 `kustomize build <kustomization_directory>` 和 `kubectl kustomize <kustomization_directory>` 都可以输出想要的资源配置。

**b. 通过环境变量创建 ConfigMap**
除了可以从文本文件生成ConfigMap之外，也可以使用环境变量中的配置内容
```shell
➜ cat <<EOF >golang_env.txt
GOVERSION=go1.20.4
GOARCH
EOF

➜ cat <<EOF >kustomization.yaml
configMapGenerator:
- name: app-config
  envs:
  - golang_env.txt
EOF

➜ kustomize build .
apiVersion: v1
data:
  golang_env.txt: |
    GOVERSION=go1.20.4
    GOARCH
kind: ConfigMap
metadata:
  name: app-config-ft5hk6c8gc
```
可以看到在 golang_env.txt 中存放的 key=value 格式的 GOVERSION 配置以及环境变量中的 GOARCH 都包含在这个 ConfigMap 中了。

**c. 通过键值对字面值直接创建 ConfigMap**
```shell
➜ cat <<EOF >kustomization.yaml
configMapGenerator:
- name: app-config
  literals:
  - Hello=World
EOF

➜ kustomize build .
apiVersion: v1
data:
  Hello: World
kind: ConfigMap
metadata:
  name: app-config-7b4b2hf646
```

**d. 使用 ConfigMap**
通过 Kustomize 生成的 ConfigMap 的名称默认带了一串后缀，在 Deployment 中引用这个 ConfigMap 的时候，Kustomize 会自动在 Deployment 配置中替换这个字段
```shell
➜ cat <<EOF >config.txt
key=value
EOF

➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: app-config
EOF

➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml
configMapGenerator:
- name: app-config
  files:
  - config.txt
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: v1
data:
  config.txt: |
    key=value
kind: ConfigMap
metadata:
  name: app-config-gc6cm9fg4c
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
        volumeMounts:
        - mountPath: /config
          name: config
      volumes:
      - configMap:
          name: app-config-gc6cm9fg4c
        name: config
```
可以看到生成的 ConfigMap 名为 app-config-gc6cm9fg4c，同时 Deployment 部分的 `Deployment.spec.template .spec.volumes[0].configMap.name` 也对应配置成了 app-config-gc6cm9fg4c


### 2. Secret 生成器

与 ConfigMap 类似，有好几种方式来生成 Secret 资源配置。

**a. 通过配置文件生成 Secret**
```shell
➜ cat <<EOF >passwd.txt
user=ahwhy
passwd=123456
EOF

➜ cat <<EOF >kustomization.yaml
secretGenerator:
- name: app-secret
  files:
  - passwd.txt
EOF

➜ kustomize build .
apiVersion: v1
data:
  passwd.txt: dXNlcj1haHdoeQpwYXNzd2Q9MTIzNDU2Cg==
kind: Secret
metadata:
  name: app-secret-6bk85dk4g8
type: Opaque

# 解码后查看，符合预期
➜ echo "dXNlcj1haHdoeQpwYXNzd2Q9MTIzNDU2Cg==" | base64 -d
user=ahwhy
passwd=123456
```

**b. 通过键值对字面值创建 Secret**
```shell
➜ cat <<EOF >kustomization.yaml
secretGenerator:
- name: app-secret
  literals:
  - user=ahwhy
  - passwd=123456
EOF

➜ kustomize build .
apiVersion: v1
data:
  passwd: MTIzNDU2
  user: YWh3aHk=
kind: Secret
metadata:
  name: app-secret-m5459t4tbd
type: Opaque

# 解码后查看，符合预期
➜ echo "MTIzNDU2" | base64 -d
123456%

➜ echo "YWh3aHk=" | base64 -d
ahwhy%
```
需要注意这里多出了一个 % 符号，这是自动加在没有换行符的字符串结尾的，然后自动强制换行，能够让下一个输出从新的一行开始

**c. 使用 Secret**
与ConfigMap的用法类似，同样可以在Deployment中使用带后缀的Secret
```shell
➜ cat <<EOF >passwd.txt
user=ahwhy
passwd=123456
EOF

➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
        volumeMounts:
        - name: passwd
          mountPath: /secrets
      volumes:
      - name: passwd
        secret:
          secretName: app-secret
EOF

➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml
secretGenerator:
- name: app-secret
  files:
  - passwd.txt
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: v1
data:
  passwd.txt: dXNlcj1haHdoeQpwYXNzd2Q9MTIzNDU2Cg==
kind: Secret
metadata:
  name: app-secret-6bk85dk4g8
type: Opaque
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
        volumeMounts:
        - mountPath: /secrets
          name: passwd
      volumes:
      - name: passwd
        secret:
          secretName: app-secret-6bk85dk4g8
```
可以看到生成的 Secret 名为 app-secret-6bk85dk4g8，同时 Deployment 部分的 `Deployment.spec.template. spec.volumes[0].secret.secretName` 也对应配置成 app-secret-6bk85dk4g8，和 ConfigMap 的处理方式基本一致。

### 3. 使用generatorOptions改变默认行为

前面使用 ConfigMap 和 Secret 生成器时，可以发现最终生成的资源配置名字上会有一串随机字符串，这个行为的意义是为了保证不同配置内容生成的资源名字会不一样，减少误用的概率。如果不需要这种默认行为，Kustomize也提供了开关，可以通过 generatorOptions 来改变这种行为。
```shell
➜ cat <<EOF >kustomization.yaml
configMapGenerator:
- name: app-config
  literals:
  - Hello=World
generatorOptions:
  disableNameSuffixHash: true
  labels:
    type: generated
  annotations:
    note: generated
EOF

➜ kustomize build .
apiVersion: v1
data:
  Hello: World
kind: ConfigMap
metadata:
  annotations:
    note: generated
  labels:
    type: generated
  name: app-config
```
可以看到这次得到的资源名字变成了没有后缀的 app-config，同时这里演示了 generatorOptions 可以给资源统一添加 labels 和 annotations


## 四、 使用Kustomize管理公共配置项

经常有需要在不同的资源配置文件中配置相同的字段，比如：

- 给所有的资源配置相同的 namespace
- 给多个资源的 name 字段加上相同的前缀或者后缀
- 给多个资源配置相同的 labels 或 annotations

这时，可以通过 Kustomize 统一管理这种公共配置项
```shell
➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
EOF

➜ cat <<EOF >kustomization.yaml
namespace: kustomize
namePrefix: test-
nameSuffix: -v1
commonLabels:
  version: v1
commonAnnotations:
  user: ahwhy
resources:
- deployment.yaml
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    user: ahwhy
  labels:
    app: demoapp
    version: v1
  name: test-demoapp-v1
  namespace: kustomize
spec:
  selector:
    matchLabels:
      app: demoapp
      version: v1
  template:
    metadata:
      annotations:
        user: ahwhy
      labels:
        app: demoapp
        version: v1
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
```
可以看到定义的 namespace、name前后缀、label 和 annotation 都生效了。使用这种方式就可以将多个资源的一些公共配置抽取出来，以便于管理。


## 五、 使用 Kustomize 组合资源

通过 Kustomize 可以灵活组合多个资源或者给多个资源"打补丁"从而拓展配置。

### 1. 多个资源的组合

很多时候在 Kubernetes 上部署一个应用时需要用到多个资源类型的配置，比如 Deployment 和Service，它们往往通过不同的文件来保存，比如 deployment.yaml 和 service.yaml
```shell
➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
EOF

➜ cat <<EOF >service.yaml
apiVersion: v1
kind: Service
metadata:
  name: demoapp-svc
spec:
  selector:
    app: demoapp
  ports:
  - name: http
    port: 80
    targetPort: 80
EOF

➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml
- service.yaml
EOF

# 最后构建出的资源模版
➜ kustomize build .
kind: Service
metadata:
  name: demoapp-svc
spec:
  ports:
  - name: http
    port: 80
    targetPort: 80
  selector:
    app: demoapp
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
```

### 2. 给资源配置打补丁

很多时候需要给同一个资源针对不同使用场景配置不同的配置项。比如同样一个 nginx 应用，可能在开发环境需要 100MB 的内存就可以，但是在生产环境则需要 1GB，这时如果分别使用两个配置文件来保存开发环境和生产环境的 nginx 配置，明显是不够优雅的。可以通过 Kustomize 给一个资源 "打不同的补丁" 来实现 "多环境配置灵活管理"。

**a. patchesStrategicMerge 方式自定义配置**
```shell
# 先准备一个普通的 Deployment 配置文件
➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
EOF

# 单独将内存配置放到一个新的文件中
➜ cat <<EOF >deployment-memory.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        resources:
          requests:
            cpu: 0.5
            memory: "64Mi"
          limits:
            cpu: 2 
            memory: "1024Mi"
EOF

# 接着编写 kustomization.yaml (老)
➜ cat <<EOF >kustomization.yaml 
resources:
- deployment.yaml
patchesStrategicMerge:
- deployment-memory.yaml
EOF

# 接着编写 kustomization.yaml
➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
patches:
- path: deployment-memory.yaml
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
        resources:
          requests:
            cpu: 0.5
            memory: "64Mi"
          limits:
            cpu: 2 
            memory: "1024Mi"
```
这种方式在 kustomization.yaml中 的 patchesStrategicMerge 部分列出的是补丁文件列表。需要注意的是，这些文件中描述的是同一个资源对象才行，一般实践是每个 patch 都实现一个明确的小功能，比如设置资源 QoS 是一个单独的补丁(patch)，设置亲和性策略是一个单独的补丁，设置副本数又是一个单独的补丁，等等。

**b. patchesJson6902 方式自定义配置**
```shell
# 先准备一个普通的 Deployment 配置文件
➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
EOF

# 创建一个 patch 配置文件
➜ cat  <<EOF >patch.yaml
- op: replace
  path: /spec/replicas
  value: 1
EOF

# 接着编写 kustomization.yaml (老)
➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml
patchesJson6902:
- target:
    group: apps
    version: v1
    kind: Deployment
    name: demoapp
  path: patch.yaml
EOF

# 接着编写 kustomization.yaml
➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
patches:
- target:
    group: apps
    version: v1
    kind: Deployment
    name: demoapp
  path: patch.yaml
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: demoapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
```
结果符合预期，replicas 字段更新了。这种方式需要注意的是，在 kustomization.yaml 中需要正确指定 target，也就是 group、version、kind、name 等字段需要和 patch 的资源完全匹配才行。

**c. 镜像的自定义**
```shell
# 先准备一个普通的 Deployment 配置文件
➜ cat <<EOF >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        ports:
        - containerPort: 80
          name: http
EOF

# 接着编写 kustomization.yaml
➜ cat <<EOF >kustomization.yaml
resources:
- deployment.yaml
images:
- name: demoapp
  newName: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp
  newTag: v1.1
EOF

# 最后构建出的资源模版
➜ kustomize build .
```

**d. 容器内使用其他资源对象的配置**
还存在一个场景，比如一个容器化应用启动时需要知道某个 Service 的名字，而这个 Service 是该应用依赖的一个上游服务，所以拿到 Service 名字才能访问这个上游服务。在使用 Kustomize 之前，也许 Service 名字会通过硬编码的方式配置在YAML文件中。

现在这个 Service 通过 Kustomize 来构建，它的名字也许会多出来一些前后缀，这时可以通过下面方式动态获取这里的 Service 名字用于配置 Deployment。
```shell
# 先准备一个普通的 Deployment 配置文件，注意其中的 command 部分相关配置
➜ cat <<'EOF' >deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demoapp
  labels:
    app: demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - name: demoapp
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        command: ["start", "--host", "$(SERVICE_NAME)"]
        ports:
        - containerPort: 80
          name: http
EOF

# 这里需要一个 SERVICE_NAME，然后看一下 Service 的配置文件
➜ cat <<EOF >service.yaml
apiVersion: v1
kind: Service
metadata:
  name: demoapp-svc
spec:
  selector:
    app: demoapp
  ports:
  - name: http
    port: 80
    targetPort: 80
EOF

# 接着编写 kustomization.yaml，默认配置下 Service 的名字是 demoapp-svc
➜ cat <<EOF >kustomization.yaml
namePrefix: dev-

resources:
- deployment.yaml
- service.yaml

vars:
- name: SERVICE_NAME
  objref:
    kind: Service
    name: demoapp-svc
    apiVersion: v1
EOF

# 最后构建出的资源模版
➜ kustomize build .
apiVersion: v1
kind: Service
metadata:
  name: dev-demoapp-svc
spec:
  ports:
  - name: http
    port: 80
    targetPort: 80
  selector:
    app: demoapp
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: demoapp
  name: dev-demoapp
spec:
  selector:
    matchLabels:
      app: demoapp
  template:
    metadata:
      labels:
        app: demoapp
    spec:
      containers:
      - command:
        - start
        - --host
        - dev-demoapp-svc
        image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        name: demoapp
        ports:
        - containerPort: 80
          name: http
```
这里给两个资源都加了一个 dev- 名字前缀，所以 Service 的名字就变成了 dev-demoapp-svc。然后通过 vars 来定义 SERVICE_NAME 变量，该变量通过下面的 objref 内的几个配置项和上面的 Service 关联，可以看到最后 command 中用到的SERVICE_NAME 变量被渲染成 dev-demoapp-svc，和预期一致。

## 六、Base 和 Overlay

前面已经介绍过 Base 和 Overlay 的概念，这里再补充一些信息。首先 Base 对 Overlay 的存在是无感的，Overlay 引用的 Base 也不一定是一个本地目录，远程代码库的目录也可以，一个 Overlay 也可以有多个 Base。
```shell
➜ tree .
.
├── base
│   ├── demoapp-deployment.yaml
│   ├── demoapp-svc.yaml
│   └── kustomization.yaml
├── dev
│   ├── kustomization.yaml
│   └── namespace.yaml
└── prod

# 指定目录给出资源模版
➜ kustomize build base

➜ kustomize build dev
```
这可以看到，给 `kustomize build` 命令传递不同的 kustomization 目录路径，就可以得到相对应的配置渲染输出。
