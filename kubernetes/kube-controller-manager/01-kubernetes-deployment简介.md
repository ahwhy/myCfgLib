# Kubernetes Deployment 简介

## 一、Kubernetes Deployment

Deployment 是常用的 Kubernetes 原生工作负载资源之一，刚开始尝试使用 Kubernetes 时大概率就是从运行一个 Deployment 类型的工作负载开始的。

本文也就不赘述 Deployment 的基础功能了，下面会介绍下 Deployment 的字段含义，以及滚动更新等特性。

### 1. Deployment 字段含义

Deployment 的 YAML 文件模版
```yaml
apiVersion: apps/v1  # API群组及版本
kind: Deployment  # 资源类型特有标识
metadata:
  name <string>  # 资源名称，在作用域中要唯一
  namespace <string>  # 名称空间；Deployment隶属名称空间级别
spec:
  minReadySeconds <integer>  # Pod就绪后多少秒内任一容器无crash方可视为"就绪"
  replicas <integer> # 期望的Pod副本数，默认为1
  selector <object> # 标签选择器，必须匹配template字段中Pod模板中的标签
  template <object>  # Pod模板对象
  revisionHistoryLimit <integer> # 滚动更新历史记录数量，默认为10
  strategy <Object> # 滚动更新策略
    type <string>  # 滚动更新类型，可用值有Recreate和RollingUpdate；
    rollingUpdate <Object>  # 滚动更新参数，专用于RollingUpdate类型
      maxSurge <string>  # 更新期间可比期望的Pod数量多出的数量或比例；
      maxUnavailable <string>  # 更新期间可比期望的Pod数量缺少的数量或比例，10， 
  progressDeadlineSeconds <integer> # 滚动更新故障超时时长，默认为600秒
  paused <boolean>  # 是否暂停部署过程
```

- Deployment 类型 spec 的属性
	- minReadySeconds: 默认值为0，表示一个Pod就绪之后多长时间可以提供服务；换句话说，配置成1就是 Pod 就绪之后1秒才对外提供服务
	- replicas: 副本数
	- selector: 标签选择器
	- template: Pod模板
	- revisionHistoryLimit: 默认是10，表示保留的历史版本数量
	- strategy: 表示 Deployment 更新 Pod 时的替换策略
		- type: Type 的可选值是 "Recreate" 和 "RollingUpdate"，默认为 "RollingUpdate"
		- rollingUpdate: 
			- maxSurge: 表示滚动更新的时候最多可以比期望副本数多几个，数字或者百分比配置都行，比如1表示更新过程中最多同时新增1个副本，然后等一个旧副本删掉之后才能继续增加1个新副本，百分比计算的结果要向上取整
			- maxUnavailable: 表示滚动更新的时候可以有多少副本不可用，同样是数字或者百分比配置，比如期望副本数是3，1表示最多删除副本到剩下2，然后要等新副本创建才能继续删除，百分比计算的结果要向下取整
	- progressDeadlineSeconds: 默认值为600，表示处理一个Deployment任务的超时时间，比如10分钟到了还没有升级成功，则标记为failed(失败)状态
	- paused: 挂起

### 2. 通过 Deployment 实现的简单版本管理

```shell
# UP-TO-DATE: 已经更新到期望状态的副本数。
# AVAILABLE: 已经可以提供服务的副本数。
# READY: 可以提供服务的副本数/期望副本数。

➜ kubectl get deployment,replicaset,pod
NAME                                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/appdemo                                  2/2     2            2           34h

NAME                                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/appdemo-6954b8cbd8                                  2         2         2       34h

NAME                                                          READY   STATUS    RESTARTS   AGE
pod/appdemo-6954b8cbd8-l7w2m                                  1/1     Running   0          34h
pod/appdemo-6954b8cbd8-r88vr                                  1/1     Running   0          34h

# 第一次更新版本
➜ kubectl set image deployment/appdemo demoapp=registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.1
deployment.apps/appdemo image updated


➜ kubectl get deployment,replicaset,pod
NAME                                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/appdemo                                  2/2     2            2           34h

NAME                                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/appdemo-6954b8cbd8                                  0         0         0       34h
replicaset.apps/appdemo-967cdffb7                                   2         2         2       34s

NAME                                                          READY   STATUS    RESTARTS   AGE
pod/appdemo-967cdffb7-89xbc                                   1/1     Running       0          34s
pod/appdemo-967cdffb7-vhgbt                                   1/1     Running       0          31s

➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

# 给第二个版本添加说明 
➜ kubectl annotate deployment/appdemo kubernetes.io/change-cause="appdemo image update to v1.1"
deployment.apps/appdemo annotate

# 查看版本说明效果
➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         <none>
2         appdemo image update to v1.1

# 通过给 rs 添加注解，给第一个版本添加说明 
➜ kubectl annotate replicaset.apps/appdemo-6954b8cbd8 kubernetes.io/change-cause="created deployment/appdemo for v1.0" 
replicaset.apps/appdemo-6954b8cbd8 annotate

# 查看版本说明效果
➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         created deployment/appdemo for v1.0
2         appdemo image update to v1.1

# 第二次更新版本
➜ kubectl set image deployment/appdemo demoapp=registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.2
deployment.apps/appdemo image updated

➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         created deployment/appdemo for v1.0
2         appdemo image update to v1.1
3         appdemo image update to v1.1

# 给第三个版本添加说明 
➜ kubectl annotate deployment/appdemo kubernetes.io/change-cause="appdemo image update to v1.2"
deployment.apps/appdemo annotate

➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         created deployment/appdemo for v1.0
2         appdemo image update to v1.1
3         appdemo image update to v1.2

# 第三次更新版本 - 设置一个不存在的镜像版本，模拟错误发布情况
➜ kubectl set image deployment/appdemo demoapp=registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.3
deployment.apps/appdemo image updated

➜  kubectl get pod
NAME                                                      READY   STATUS             RESTARTS   AGE
appdemo-7cbd5cbb6-j5bm7                                   1/1     Running            0          4m19s
appdemo-7cbd5cbb6-jdf8h                                   1/1     Running            0          4m21s
appdemo-b6b6d6f9c-8twpg                                   0/1     ImagePullBackOff   0          80s

# 给第四个版本添加失败说明 
➜  kubectl annotate deployment/appdemo kubernetes.io/change-cause="appdemo image update to v1.3 --> failed" 
deployment.apps/appdemo annotate

# 查看整体效果
➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         created deployment/appdemo for v1.0
2         appdemo image update to v1.1
3         appdemo image update to v1.2
4         appdemo image update to v1.3 --> failed

# 通过 kubectl rollout undo 回滚到上一个版本
➜ kubectl rollout undo deployment/appdemo
deployment.apps/appdemo rolled back

# 原第三个版本，已经变为第五个(当前)版本
➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
1         created deployment/appdemo for v1.0
2         appdemo image update to v1.1
4         appdemo image update to v1.3 --> failed
5         appdemo image update to v1.2

# 通过 --revision 参数，查看某一版本的详细配置
➜ kubectl rollout history deployment/appdemo --revision=1
deployment.apps/appdemo with revision #1
Pod Template:
  Labels:	app=demoapp
	pod-template-hash=6954b8cbd8
  Annotations:	kubernetes.io/change-cause: created deployment/appdemo for v1.0
  Containers:
   demoapp:
    Image:	registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
    Port:	80/TCP
    Host Port:	0/TCP
    Environment:	<none>
    Mounts:	<none>
  Volumes:	<none>

# 通过 --to-revision=1 参数，回滚至第一个版本
➜ kubectl rollout undo deployment/appdemo --to-revision=1
deployment.apps/appdemo rolled back

# 原第一个版本，已经变为第六个(当前)版本
➜ kubectl rollout history deployment/appdemo
deployment.apps/appdemo
REVISION  CHANGE-CAUSE
2         appdemo image update to v1.1
4         appdemo image update to v1.3 --> failed
5         appdemo image update to v1.2
6         created deployment/appdemo for v1.0
```

最后附上案例中 deployment/appdemo 最后的完整 yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "6"
    kubernetes.io/change-cause: created deployment/appdemo for v1.0
  creationTimestamp: "2023-09-17T17:19:00Z"
  generation: 9
  labels:
    app: demoapp
  name: appdemo
  namespace: default
  resourceVersion: "40232035"
  uid: 5086784d-0cbc-44c3-8707-aa87cb2bde54
spec:
  progressDeadlineSeconds: 600
  replicas: 2
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: demoapp
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: demoapp
    spec:
      containers:
      - image: registry.cn-hangzhou.aliyuncs.com/opensf/demoapp:v1.0
        imagePullPolicy: IfNotPresent
        name: demoapp
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        resources: {}
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      terminationGracePeriodSeconds: 30
status:
  availableReplicas: 2
  conditions:
  - lastTransitionTime: "2023-09-17T17:19:01Z"
    lastUpdateTime: "2023-09-17T17:19:01Z"
    message: Deployment has minimum availability.
    reason: MinimumReplicasAvailable
    status: "True"
    type: Available
  - lastTransitionTime: "2023-09-17T17:19:00Z"
    lastUpdateTime: "2023-09-19T04:28:18Z"
    message: ReplicaSet "appdemo-6954b8cbd8" has successfully progressed.
    reason: NewReplicaSetAvailable
```