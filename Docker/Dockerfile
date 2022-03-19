FROM tomcat

ENV PATH /root/miniconda3/bin:/root/miniconda3/condabin:$PATH

RUN rm -rf /etc/localtime && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN ln -sf /root/log/log.txt /dev/stdout &&  ln -sf /root/log/log.txt /dev/stderr 
RUN yum install -y epel-release && yum install -y unzip vim wget tree lrzsz gcc gcc-c++ automake pcre pcre-devel zlib zlib-devel openssl openssl-devel iproute net-tools iotop

ADD target/demo.war /usr/local/tomcat/webapps/demo.war

CMD ["/bin/bash", "-ce", "tail -f /dev/null"]