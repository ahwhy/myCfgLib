# 基于Vsftp的FTP服务器搭建

## Vsftp简介

VSFTP是一个基于GPL发布的类Unix系统上使用的FTP服务器软件，它的全称是Very Secure FTP。


## Vsftp部署
```shell
# 安装服务及依赖
$ yum install vsftpd pam* db4* -y

# 修改配置文件
$ vim /etc/vsftpd/vsftpd.conf
---conifg---
anonymous_enable=NO         #是否允许匿名用户登陆FTP
local_enable=YES            #是否本地用户登陆FTP
write_enable=YES            #是否本地用户上传
local_umask=022             #本地用户上传文件umask值，默认权限
dirmessage_enable=YES       #用户进入目录时，显示.message文件中信息
xferlog_enable=YES          #激活记录日志
connect_from_port_20=YES    #主动模式数据传输接口  
xferlog_std_format=YES      #使用标准的FTP日志格式
#ftpd_banner=Welcome to blah FTP service.    #登陆提示信息
listen=YES                  #是否运行被监听
listen_ipv6=NO                                 
pam_service_name=vsftpd     #设置PAM外挂模块提供的认证服务所使用的配置文件名，即/etc/pam.d/svftpd文件 
userlist_enable=YES         #用户登陆限制
tcp_wrappers=YES            #是否使用tcp_wrappers作为主机访问控制方式
listen_port=10021           #更改Ftp服务端口

# 修改/etc/services文件
$ vim /etc/service
---conifg---
ftp             10021/tcp                         #将端口修改为自己想要的端口    
ftp             10021/udp    fsp fspd             #将端口修改为自己想要的端口    
```


## 用户的创建

```shell
# 创建用户并且禁止其登陆所有服务
$ useradd -s /bin/false junding4            

# 给本地账户设置密码 
$ echo 'XXXXXXX' | passwd --stdin junding4

$ vim /etc/shells
---config---
/bin/false    #追加一行，开放ftp服务权限   
```


## 客户端登陆

```shell
# 使用ftp登陆（更改完端口后暂不能使用）
$ ftp 172.31.160.196 10021

# 使用lftp登陆
$ lftp -u 'junding4,XXXXXXX' 172.31.160.196:10021

# 修改存储路径
# 上传的文件存放在用户的家目录下: /home/junding4/
# 若要更改存放路径，则修改用户的家目录: 
$ usermod  -d  /data/home/junding4  -u 1002  junding4

# 赋予用户家目录权限
$ setfacl -m u:junding4:rwx /data/home/junding4 

# 若要限制用户登陆，修改下列文件
/etc/vsftpd/ftpusers   #该文件用来指定那些用户不能访问ftp服务器
/etc/vsftpd/user_list  #该文件用来指示的默认账户在默认情况下也不能访问ftp
```
