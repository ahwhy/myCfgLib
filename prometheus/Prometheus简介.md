# Prometheus

## 概念简介

### 1、时序数据
- 时序数据，是在一段时间内通过重复测量(measurement)而获得的观测值的集合
	- 将这些观测值绘制于图形之上，它会有一个数据轴和一个时间轴
	- As our world gets increasingly instrumented, sensors and systems are constantly emitting a relentless stream of time series data.
	- Weather records, economic indicators and patient health evolution metrics all are time series data.

- 服务器指标数据、应用程序性能监控数据、网络数据等也都是时序数据

### 2、Prometheus-Server
- Prometheus 是一款时序(time series)数据库；但它的功能却并非止步于TSDB(Time Series DB)，而是一款设计用于进行目标(Target)监控的关键组件

- 结合生态系统内的其它组件，例如Pushgateway、Altermanager和Grafana 等，可构成一个完整的 IT 监控系统

- Prometheus 支持通过三种类型的途径从目标上"抓取(Scrape)"指标数据
	- Instrumentation
		- The application will expose Prometheus compatible metrics on a given URL.
	- Exporters
		- Prometheus has an entire collection of exporters for existing technologies.
		- You can for example find prebuilt exporters for Linux machine monitoring (node exporter), for very established databases (SQL exporter or MongoDB exporter) and even for HTTP load balancers (such as the HAProxy exporter).
	- Pushgateway
		- Sometimes you have applications or jobs that do not expose metrics directly.
		- Those applications are either not designed for it (such as batch jobs for example), or you may have made the choice not to expose those metrics directly via your app.

- Instrumentation 程序仪表
	- 任何能够支持 Scrape 指标数据的应用程序都首先要具有一个测量系统
	- 在 Prometheus 的语境中， Instrumentation 是指附加到应用程序中的那些用于暴露程序指标数据的客户端库

- Exporters
	- 对于那些未内建 Instrumentation ，且也不便于自行添加该类组件以暴露指标数据的应用程序来说，常用的办法是于待监控的目标应用程序外部运行一个独立指标暴露程序，该类型的程序即统称为 Exporter
	- Exporter 负责从目标应用程序上采集和聚合原始格式的数据，并转换或聚合为 Prometheus 格式的指标向外暴露
	- Prometheus 站点上提供了大量的 Exporter

- Alerts
	- 抓取到异常值后， Prometheus 支持通过"告警(Alert)"机制向用户发送反馈或警示，以触发用户能够及时采取应对措施
	- Prometheus Server 仅负责生成告警指示，具体的告警行为由另一个独立的应用程序AlertManager 负责
		- 告警指示由 Prometheus Server 基于用户提供的"告警规则"周期性计算生成
		- Alertmanager 接收到 Prometheus Server发来的告警指示后，基于用户定义的告警路由(route)向告警接收人(receivers)发送告警信息

### 3、Pull and Push
- Prometheus 主动从各 Target 上"拉取(pull)"数据，而非等待被监控端的"推送(push)"
	- 基于 HTTP call，从配置文件中指定的网络端点(endpoint)上周期性获取指标数据

- 两个方式各有优劣，其中 Pull 模型的优势在于
	- 集中控制: 有利于将配置集在 Prometheus Server 上完成，包括指标及采取速率等
	- Prometheus 的根本目标在于收集在 Target 上预先完成聚合的聚合型数据，而非一款由事件驱动的存储系统

### 4、Prometheus的生态组件
- Prometheus 生态圈中包含了多个组件，其中部分组件可选
	- Prometheus Server: 收集和存储时间序列数据
	- Client Library: 客户端库，目的在于为那些期望原生提供 Instrumentation 功能的应用程序提供便捷的开发途径
	- Push Gateway: 接收那些通常由短期作业生成的指标数据的网关，并支持由 PrometheusServer 进行指标拉取操作
	- Exporters: 用于暴露现有应用程序或服务(不支持 Instrumentation)的指标给 Prometheus Server
	- Alertmanager: 从 Prometheus Server 接收到"告警通知"后，通过去重、分组、路由等预处理功能后以高效向用户完成告警信息发送
	- Data Visualization: Prometheus Web UI(Prometheus Server 内建)，及 Grafana 等；
	- Service Discovery: 动态发现待监控的 Target，从而完成监控配置的重要组件，在容器化环境中尤为有用；该组件目前由 Prometheus Server 内建支持；	

### 5、Prometheus数据模型
- Prometheus 仅用于以“键值”形式存储时序式的聚合数据，它并不支持存储文本
	- 其中的"键"称为指标(Metric)，它通常意味着 CPU 速率、内存使用率或分区空闲比例等
	- 同一指标可能会适配到多个目标或设备，因而它使用"标签"作为元数据，从而为 Metric 添加更多的信息描述纬度
	- 些标签还可以作为过滤器进行指标过滤及聚合运算

### 6、指标类型 Metric Types
- Prometheus 使用 4 种方法来描述监视的指标
	- Counter：计数器，用于保存单调递增型的数据，例如站点访问次数等
		- 不能为负值，也不支持减少，但可以重置回 0
	- Gauge：仪表盘，用于存储有着起伏特征的指标数据，例如内存空闲大小等
		- Gauge 是 Counter 的超集；但存在指标数据丢失的可能性时，Counter 能让用户确切了解指标随时间的变化状态，而 Gauge 则可能随时间流逝而精准度越来越低；
	- Histogram：直方图，它会在一段时间范围内对数据进行采样，并将其计入可配置的bucket 之中
		- Histogram 能够存储更多的信息，包括样本值分布在每个 bucket(bucket 自身的可配置) 中的数量、所有样本值之和以及总的样本数量，从而 Prometheus 能够使用内置的函数进行如下操作
			- 计算样本平均值: 以值的总和除以值的数量；
			- 计算样本分位值: 分位数有助于了解符合特定标准的数据个数；例如评估响应时长超过 1 秒钟的请求比例，若超过 20% 即发送告警等；
	- Summary：摘要 Histogram 的扩展类型，但它是直接由被监测端自行聚合计算出分位数，并将计算结果响应给 Prometheus Server 的样本采集请求
		- 因而，其分位数计算是由监控端完成

### 7、作业Job 和 实例Instance
- Instance: 能够接收 Prometheus Server 数据 Scrape 操作的每个网络端点(endpoint)，即为一个实例(Instance)

- 通常，具有类似功能的 Instance 的集合称为一个 Job ，例如一个 MySQL 主从复制集群中的所有 MySQL 进程

### 8、PromQL
- Prometheus 提供了内置的数据查询语言 PromQL(全称为 Prometheus Query Language)，支持用户进行实时的数据查询及聚合操作

- PromQL 支持处理两种向量，并内置提供了一组用于数据处理的函数
	- 即时向量: 最近一次的时间戳上跟踪的数据指标；
	- 时间范围向量: 指定时间范围内的所有时间戳上的数据指标；

### 9、Prometheus的局限性
- Prometheus 是一款指标监控系统，不适合存储事件及日志

- Prometheus 认为只有最近的监控数据才有查询的需要，其本地存储的设计初衷只是保存短期数据，因而不支持针对大量的历史数据进行存储
	- 若需要存储长期的历史数据，建议基于远端存储机制将数据保存于 InfluxDB 或 OpenTSDB 等系统中

- Prometheus 的集群机制成熟度不高，即便基于 Thanos 亦是如此


## Exporters

### 1、客户端库
- 应用程序自己并不会直接生成指标数据，这依赖于开发人员将相关的客户端库添加至应用程序中构建出的测量系统(instrumentation system)来完成
	- Prometheus 为包括 Go 、 Python 、 Java (或 Scala)和 Ruby 等主流的编程语言提供了各自适用的客户端库，另外还有适用于 Bash 、 C 、 C++ 、 C# 、 Node.js 、 Haskell 、 Erlang 、 Perl 、 PHP和 Rust 等多种编程语言的第三方库可用；
	- 通常，三两行代码即能将客户端库整合进应用程序中实现直接测量(direct instrumentation)机制；

- 客户端库主要负责处理所有的细节类问题，例如线程安全和记账，以及生成文本格式的指标以数据响应 HTTP 请求等

- 客户端库通常还会额外提供一些指标，例如 CPU 使用率和垃圾回收统计信息等，具体的实现则取决于库和相关的运行时环境

### 2、Exporter基础
- 对于那些非由用户可直接控制的应用代码来说，为其添加客户端库以进行直接测量很难实现
	- 操作系统内核就是一个典型的示例，它显然不大可能易于实现添加自定义代码通过 HTTP 协议输出 Prometheus 格式的指标
	- 但这一类的程序一般都会通常某种接口输出其内在的指标，只不过这些指标可能有着特殊的格式，例如 Linux 内核的特有指标格式，或者 SNMP 指标格式等
	- 这些指标需要对它进行适当的解析和处理以转换为合用的目标格式， Exporter (指标暴露器)是完成此类转换功能的应用程序

- Exporter 独立运行于要获取其测量指标的应用程序之外，负责接收来自于Prometheus Server 的指标获取请求，它通过目标应用程序(真正的目标)内置的指标接口获取指标数据，并将这些指标数据转换为合用的目标格式后响应给Prometheus
	- Exporter 更像是"一对一"的代理，它作为 Prometheus Server 的 target 存在，工作于应用程序的指标接口和 Prometheus 的文本指标格式之间转换数据格式
	- 但 Exporter 不存储也不缓存任何数据

### 3、Node Exporter
- Exporter Unit
```shell
$ vim /usr/lib/systemd/system/node_exporter.service
[Unit]
Description=node_exporter
Documentation=https://prometheus.io/
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/bin/node_exporter \
	--web.config=web config.yml \
	--collector.ntp \
	--collector.mountstats \
	--collector.systemd \
	--collector.ntp \
	--collector.tcpstat
ExecReload=/bin/kill -HUP $MAINPID
TimeoutStopSec=20s
Restart=always

[Install]
WantedBy=multi-user.target
```

- [node_exporter 常用的各指标](https://github.com/prometheus/node_exporter)


### 4、Mysql Exporter
- Exporter Unit
```shell
$ vim /usr/lib/systemd/system/mysqld_exporter.service
[Unit]
Description=node_exporter
Documentation=https://prometheus.io/
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/mysqld_exporter/mysqld_exporter --config.my-cnf=my.cnf
Restart=on-failure

[Install]
WantedBy=multi-user.target

$ vim /usr/lib/systemd/system/my.cnf
[client]
host=127.0.0.1
user=exporter
password=password

# 授权 exporter 用户
mysql> GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'
```

### 5、适用于主机监控的USE方法
- USE 是使用率(Utilization)、饱和度(Saturation)和错误(Error)的缩写，由Netflix 的内核和性能工程师 Brendan Gregg 开发

- USE 方法可以概括为: 针对每个资源，检查使用率、饱和度和错误
	- 资源: 系统的一个组件，在 USE 中，它指的是一个传统意义上的物理服务器组件，如 CPU 、内存和磁盘等；
	- 使用率: 资源忙于工作的平均时间，它通常用随时间变化的百分比进行表示；
	- 饱和度: 资源排队工作的指标，无法再处理额外的工作；通常用队列长度表示；
	- 错误: 资源错误事件的计数；

- 对 CPU 来说，USE 通常意味着如下概念
	- CPU 使用率随时间的百分比；
	- CPU 饱和度，等待 CPU 的进程数；
	- 错误，通常对 CPU 不太有影响；

- 对内存来说，USE 的意义相似
	- 内存使用率随时间的百分比；
	- 内存饱和度，可通过监控 swap 进行测量；
	- 错误，通常不太关键；


## PromQL

### 1、Prometheus时间序列
- 时间序列数据: 按照时间顺序记录系统、设备状态变化的数据，每个数据称为一个样本
	- 数据采集以特定的时间周期进行，随着时间流逝，将这些样本数据记录下来，将生成一个离散的样本数据序列；
	- 该序列也称为向量(Vector)，将多个序列放在同一个坐标系内(以时间为横轴，以序列为纵轴)，将形成一个由数据点组成的矩阵；

### 2、PromQL简介
- Prometheus 基于指标名称(metrics name)以及附属的标签集(labelset)唯一定义一条时间序列
	- 指标名称代表着监控目标上某类可测量属性的基本特征标识
	- 标签则是这个基本特征上再次细分的多个可测量维度

- 基于 PromQL 表达式，用户可以针对指定的特征及其细分的纬度进行过滤、聚合、统计等运算从而产生期望的计算结果

- PromQL (Prometheus Query Language) 是 Prometheus Server 内置数据查询语言
	- PromQL 使用表达式(expression)来表述查询需求
	- 根据其使用的指标和标签，以及时间范围，表达式的查询请求可灵活地覆盖在一个或多个时间序列的一定范围内的样本之上，甚至是只包含单个时间序列的单个样本

### 3、Prometheus数据类型
- Prometheus 中，每个时间序列都由指标名称(Metric Name)和标签(Label)来唯一标识，格式为 `<metric name>{<label name>=<label value>,...}`
	- 指标名称：通常用于描述系统上要测定的某个特征
		- 例如，http_requests_total 表示接收到的 HTTP 请求总数；
		- 支持使用字母、数字、下划线和冒号，且必须能匹配 RE2 规范的正则表达式；
	- 标签：键值型数据，附加在指标名称之上，从而让指标能够支持多纬度特征；可选项
		- 例如，`http_requests_total{method=GET}` 和 `http_requests_total{method=POST}` 代表着两个不同的时间序列；
		- 标签名称可使用字母、数字和下划线，且必须能匹配 RE2 规范的正则表达式；
		- 以 "_ _" 为前缀的名称为 Prometheus 系统预留使用；

- Metric Name 的表示方式有两种
	- `http_requests_total{status="200",method="GET"}`
	- `{__name__="http_requests_total",status="200",method="GET"}` 通常用于 Prometheus 内部

### 4、PromQL的数据类型
- PromQL 的表达式中支持 4 种数据类型
	- 即时向量(Instant Vector): 特定或全部的时间序列集合上，具有相同时间戳的一组样本值称为即时向量
	- 范围向量(Range Vector): 特定或全部的时间序列集合上，在指定的同一时间范围内的所有样本值
	- 标量(Scalar): 一个浮点型的数据值
	- 字符串(String): 支持使用单引号、双引号或反引号进行引用，但反引号中不会对转义字符进行转义

### 5、时间序列选择器 Time series Selectors
- PromQL 的查询操需要针对有限个时间序列上的样本数据进行，挑选出目标时间序列是构建表达式时最为关键的一步
	- 用户可使用向量选择器表达式来挑选出给定指标名称下的所有时间序列或部分时间序列的即时(当前)样本值或至过去某个时间范围内的样本值
	- 前者称为即时向量选择器，后者称为范围向量选择器

- 即时向量选择器 Instant Vector Selectors
	- 返回 0 个、 1 个或多个时间序列上在给定时间戳(instant)上的各自的一个样本，该样本也可称为即时样本

- 范围向量选择器 Range Vector Selectors
	- 返回 0 个、 1 个或多个时间序列上在给定时间范围内的各自的一组样本

### 6、指标
- 样本数据格式
	- Prometheus 的每个数据样本由两部分组成
		- float64 格式的数据
		- 毫秒精度的时间戳

- 指标名称及标签使用注意事项
	- 指标名称和标签的特定组合代表着一个时间序列
		- 指标名称相同，但标签不同的组合分别代表着不同的时间序列；
		- 不同的指标名称自然更是代表着不同的时间序列；
	- PromQL 支持 基于定义的指标维度进行过滤和聚合
		- 更改任何标签值，包括添加或删除标签，都会创建一个新的时间序列
		- 应该尽可能地保持标签的稳定性，否则，则很可能创建新的时间序列，更甚者会生成一个动态的数据环境，并使得监控的数据源难以跟踪，从而导致建立在该指标之上的图形、告警及记录规则变得无效

### 7、PromQL的指标类型
- PromQL 有四个指标类型，主要由 Prometheus 的客户端库使用
	- Counter: 计数器，单调递增，除非重置(例如服务器或进程重启)
	- Gauge: 仪表盘，可增可减的数据
	- Histogram: 直方图，将时间范围内的数据划分成不同的时间段，并各自评估其样本个数及样本值之和，因而可计算出分位数
		- 可用于分析因异常值而引起的平均值过大的问题；
		- 分位数计算要使用专用的 histogram_quantile 函数；
	- Summary: 类似于 Histogram ，但客户端会直接计算并上报分位数

- Prometheus Server 并不使用类型信息，而是将所有数据展平为时间序列


## Service Discovery

