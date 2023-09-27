# 通过 Kustomize 的配置管理

## 一、了解 Kustomize

`Kustomize` 的代码库 [GitHub 地址](https://github.com/kubernetes-sigs/kustomize)。Kustomize 是 Kubernetes 原生配置管理工具，实现了类似 sed 的给资源配置文件"打补丁"的能力。Kubernetes 1.14.0 版本已经集成到了 kubectl 命令中，所以也可以通过 kubectl 的子命令来使用Kustomize.

### 1. Kustomize 的基本概念

- Kustomize 中的几个关键术语
    - kustomization 这个词指代的是一个 kustomization.yaml 文件
        - 或者更广义地理解为一个包含 kustomization.yaml 文件的目录以及这个 kustomization.yaml 文件中引用的所有其他文件
    - base 指的是被其他 kustomization 引用的一个 kustomization 
        - 换言之，任何一个kustomization a被另一个kustomization b引用时，a是b的base，
        - 这时如果新增一个kustomization c来引用b，那么b也就是c的base
        - 即，base是一个相对的概念，而不是某种属性标识
    - overlay 与base相对应，依赖另一个kustomization的kustomization被称为overlay
        - 如果kustomization b引用了kustomization a，那么b是a的overlay，a是b的base


## 二、Kustomize 的安装

Kustomize 提供了 Linux/Darwin 系统 *amd64/arm64 架构的二进制可执行文件(Windows等也支持，不过不建议在Windows上使用这些工具)。可以到Kustomize项目的 [release](https://github.com/kubernetes-sigs/kustomize/releases)页面去下载对应的压缩包。
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

**a. 1.从配置文件生成ConfigMap**
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

**b. 通过环境变量创建ConfigMap**
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

**c. 通过键值对字面值直接创建ConfigMap**
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

**d. 使用ConfigMap**
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
        image: ikubernetes/demoapp:v1.0
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
      - image: ikubernetes/demoapp:v1.0
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


### 2.  Secret 生成器

与ConfigMap类似，有好几种方式来生成Secret资源配置。

**a. 通过配置文件生成Secret**
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

**b. 通过键值对字面值创建Secret**
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

**c. 使用Secret**
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
        image: ikubernetes/demoapp:v1.0
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
      - image: ikubernetes/demoapp:v1.0
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
可以看到生成的Secret名为 app-secret-6bk85dk4g8，同时 Deployment 部分的 `Deployment.spec.template. spec.volumes[0].secret.secretName` 也对应配置成app-secret-6bk85dk4g8，和 ConfigMap 的处理方式基本一致。

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
