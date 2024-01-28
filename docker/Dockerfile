################https://docs.docker.com/engine/reference/builder/
################第一阶段镜像构建
################构建容器的基础信息
# FROM 定义基础镜像，后面的本地有效的镜像名，如果本地没有会从远处仓库下载;
# as 定义别名为 base
ARG VERSION
FROM ubuntu:${VERSION} as base

################具体执行的命令
RUN apt-get update && apt-get install -y git gcc
# WORKDIR 指定工作目录
WORKDIR /data/workspace
# ADD 自动解压压缩包
ADD demo.tar /data/workspace
RUN go build -o demo


################################################################################################################
################第二阶段镜像构建
# FROM 定义基础镜像，后面的本地有效的镜像名，如果本地没有会从远处仓库下载
FROM centos
# MAINTAINER 镜像维护者信息
MAINTAINER ahwhya@outlook.com

################其他可选参数
# USER 指定该容器运行时的用户名和UID，后续的RUN命令也会使用这里指定的用户执行
USER 1001
# WORKDIR 指定工作目录
WORKDIR /data/workspace
# VOLUME 设置容器挂载主机目录
VOLUME ["/data/dir_1","/data/dir_2"]
# ENV 设置容器变量，常用于容器内传递用户密码、运行参数等
ENV PATH /root/miniconda3/bin:/root/miniconda3/condabin:$PATH

################具体执行的命令
RUN rm -rf /etc/localtime && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN ln -sf /root/log/log.txt /dev/stdout &&  ln -sf /root/log/log.txt /dev/stderr 
RUN yum install -y epel-release && yum install -y unzip vim wget tree lrzsz gcc gcc-c++ automake pcre pcre-devel zlib zlib-devel openssl openssl-devel iproute net-tools iotop# ADD 自动解压压缩包
RUN yum clean all && rm -rf ~/.cache/pip/
ADD target/demo.war /usr/local/tomcat/webapps/demo.war

# 分阶段构建镜像，从第一阶段构建的镜像中拷贝产物
COPY --from=base /data/workspace/demo /opt/demo
ADD start.sh /opt/start.sh

# EXPOSE 向外开发的端口，多个端口做空格间隔
# 启动容器的时候，使用-p参数指定对应的端口对外映射，如：-p 8081:80，则 80 就是这里的 80
EXPOSE 80 443

# ENTRYPOINT 用于定义容器启动以后的执行体，这个是容器的“入口”
# 如果docker run命令后面有东西，那么后面的全部都会作为 ENTRYPOINT 的参数
# 如果run后面没有额外的东西，但是CMD有，那么cmd的全部内容会作为 ENTRYPOINT 的参数
ENTRYPOINT ["/opt/start.sh"]

# CMD 容器启动运行的命令，每个Dockerfile只能有一条，如果有多条则只有最后一条被执行
# 如果在从该镜像启动容器的时候也指定了启动命令，那么指定的命令会覆盖Dockerfile构建的镜像里面的CMD命令
# 即 指定的命令优先级 比 Dockerfile中添加命令的优先级更高
# CMD ["/bin/bash", "-ce", "tail -f /dev/null"]
CMD ["-f", "demo"]