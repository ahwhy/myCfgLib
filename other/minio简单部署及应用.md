# Minio简单部署及应用

## Minio 简介

Minio 是基于Apache License v2.0开源协议的对象存储服务。
它兼容亚马逊S3云存储服务接口，非常适合于存储大容量非结构化的数据，例如图片、视频、日志文件、备份数据和容器/虚拟机镜像等，而一个对象文件可以是任意大小，从几kb到最大5T不等。
Minio是一个非常轻量的服务，可以很简单的和其他应用的结合，类似 NodeJS、Redis 或者 MySQL。


## Minio的存储结构

- 单主机，单磁盘
 
- 单主机，多块磁盘

- 分布式部署→多主机，多块磁盘
  
  
## 基于docker的单主机多硬盘模式部署

###	1、镜像下载
```shell
# 服务器端
$ docker pull minio/minio

# 客户端
$ docker pull minio/mc
```

###	2、在Docker中运行Minio容器

```shell
$ docker run -d -p 9000-9009:9000-9009 --name minio1 --restart=always  \
	-e MINIO_ACCESS_KEY=admin -e MINIO_SECRET_KEY=12345678  \
	-v /disk9/minio/data:/disk9/data -v /disk10/minio/data:/disk10/data  \
	-v /disk11/minio/data:/disk11/data -v /disk12/minio/data:/disk12/data  \
	-v /disk9/minio/config:/root/.minio  \
	minio/minio server /disk9/data /disk10/data /disk11/data /disk12/data
```

- -d: 后台运行容器，并返回容器ID；
- -p：指定端口映射，这里打开多个端口为后续多用户做准备；
- --name：为容器指定一个名称；
- -e: 设置环境变量，ACCESS表示用户名，SECRET表示密码；
- -v：绑定一个卷，将容器内部的文件夹绑定到物理卷上；
- server /*：指定容器内部的存放文件的位置。
- 该模式下，Minio在一台服务器上搭建服务，但数据分散在多块(大于4块)磁盘上，提供了数据上的安全保障。

### 3、其他用户的添加
- 单硬盘存储模式的用户添加
```shell
$ docker exec -it minio1 /bin/sh
$ export MINIO_ACCESS_KEY=usr1 
$ export MINIO_SECRET_KEY=12345678

$ minio --config-dir ~/usr1 server --address :9001 /disk9/data/usr1  &
```

- 多硬盘存储模式的用户添加
```shell
# 将 用户目录 置于已存在用户的 数据目录 之下 的用户创建
$ docker exec -it minio1 /bin/sh
$ export MINIO_ACCESS_KEY=usr2 
$ export MINIO_SECRET_KEY=12345678

$ minio --config-dir ~/usr2 server --address :9002 /disk9/data/usr2   \
	/disk10/data/usr2 /disk11/data/usr2 /disk12/data/usr2  &
WARNING: Host local has more than 2 drives of set. A host failure will result in data becoming unavailable.Attempting encryption of all config, IAM users and policies on MinIO backend
# 警告: 主机本地有2个以上的驱动器。主机故障将导致数据不可用。尝试对MinIO后端上的所有配置、IAM用户和策略进行加密
# 由于usr2的数据目录在 admin 的路径之下(/disk*/data)，所以会导致admin用户可以对usr2用户下所有数据进行访问修改
```

- 数据目录不重叠的用户创建：
```shell
$ docker exec -it minio1 /bin/sh
$ export MINIO_ACCESS_KEY=usr3 
$ export MINIO_SECRET_KEY=12345678

# 这里由于用户目录不在开始绑定到物理卷文件夹上，所以物理数据盘上，就不存在该用户的数据目录
$ minio --config-dir ~/usr3 server --address :9003 /disk9/usr3   \
	/disk10/usr3 /disk11/usr3 /disk12/usr3  &
```

### 4、基于docker的minio-client的部署
- Minio拥有网页端的配置管理，官网还是给我们提供了基于命令行的客户端Minio Client(简称mc)

- 在Docker容器中运行mc
```shell
$ docker run --restart=always --name minio1-client -it --entrypoint=/bin/sh minio/mc

# 运行完成后需要进行配置，将MinIO服务配置到客户端上去，配置的格式如下
$ mc config host add <ALIAS> <YOUR-S3-ENDPOINT> <YOUR-ACCESS-KEY> <YOUR-SECRET-KEY> <API-SIGNATURE>
$ mc config host add minio http://172.16.61.207:9000 admin 12345678 S3v4
```

- 常用命令
```
ls       列出文件和文件夹。
mb       创建一个存储桶或一个文件夹。
cat      显示文件和对象内容。
pipe     将一个STDIN重定向到一个对象或者文件或者STDOUT。
share    生成用于共享的URL。
cp       拷贝文件和对象。
mirror   给存储桶和文件夹做镜像。
find     基于参数查找文件。
diff     对两个文件夹或者存储桶比较差异。
rm       删除文件和对象。
events   管理对象通知。
watch    监视文件和对象的事件。
policy   管理访问策略。
session  为cp命令管理保存的会话。
config   管理mc配置文件。
update   检查软件更新。
version  输出版本信息。
```

### 4、举例
```shell
# 查看存储桶和查看存储桶中存在的文件
# 查看存储桶
$ mc ls minio
# 查看存储桶中存在的文件
$ mc ls minio/test1

# 创建一个名为test2的存储桶：
$ mc mb minio/test2

# 共享test1.txt文件的下载路径：
$ mc share download minio/test1/test-excel-1.xlsx

# 查找test1存储桶中的txt文件：
$ mc find minio/test1 --name "*.txt"

# 设置test1存储桶的访问权限为只读：
# 目前可以设置这四种权限：none, download, upload, public
$ mc policy set download minio/test1/

# 查看存储桶当前权限
$ mc policy list minio/test/
```