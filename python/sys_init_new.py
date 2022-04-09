#/bin/python
#coding:utf-8
#此脚本用于添加DNS、更新yum源、关闭防火墙、关闭SElinux、NTP、时间时区、测试网卡速率、双网卡Bond0、监控客户端安装、安装GPU驱动、网卡驱动

import os, shutil, subprocess, platform, tarfile, logging, re
sys = platform.dist()[0]
if (sys == "Ubuntu" or sys == "SuSE"):
        ver = int(platform.dist()[1][0] + platform.dist()[1][1])
elif (sys == "centos" or sys == "redhat"):
        ver = int(platform.dist()[1][0])
'''
以下为各安装模块开关，可根据实际情况更改需要安装的开关on or off，并添加各模块配置。
驱动安装包需放在/root/目录下，包名称可自己更改，必须跟实际包名称一致。
网卡驱动根据需求版本更改，如：i40e-2.4.6改成i40e-2.4.10
'''
#DNS配置,如果是on,配置dns地址
dns_status = "on"
dns = 'xx.xx.xx.xx'

#软件源配置
source_status = "on"
url = "http://xx.xx.xx.xx"

#ntp配置,如果是on,配置ntp地址
ntp_status = "on"
ntp = 'xx.xx.xx.xx'

#是否开启性能最大化
max_per_status = "on"

#是否关闭NetworkManager
NetworkManager_status = 'off'

#GPU_DRIVE安装
gpu_status = "on"
GPU_DRIVER_version = 'NVIDIA-Linux-x86_64-390.46.run'
cuda_status = "on"
CUDA_DRIVER_version = 'cuda_8.0.61_375.26_linux-run'
#如果已安装GPU驱动，是否卸载已安装的驱动,卸载后会重启服务器
gpu_uninstall = "off"

#万兆卡i40e驱动安装,默认版本为i40e-2.4.10
nic_status = "on"
if sys == "centos":
    if ver > 6:
        version = float(os.popen("cat /etc/redhat-release | awk '{print $4}'").read().strip()[0:3])
    else:
        version = float(os.popen("cat /etc/redhat-release | awk '{print $3}'").read().strip())
    if version > 7.4:
        Physical_NIC_DRIVER_version = 'i40e-2.7.26'
    else:
        Physical_NIC_DRIVER_version = 'i40e-2.4.10'
else:
    Physical_NIC_DRIVER_version = 'i40e-2.4.10'

#Bond0配置，暂提供mode4，如果是on需配置interface，bond0的ip,gateway,netmask,bond_dns,注意：目前脚本不配置ubuntu18.04及以上版本的bond0
bond0_status = "off"
mode = "4"
interface = "em1 em2"
ip = "192.168.0.100"
gateway = "192.168.0.1"
netmask = "255.255.255.0"
bond_dns = "192.168.0.1"

#安装prom_monitor
monitor_status = "on"
monitor_url = "http://xx.xx.xx.xx"

#url = "http://xx.xx.xx.xx"
GPU_DRIVER_filepath = 'Soft/GPU_Driver'
CUDA_DRIVER_filepath = 'Soft/CUDA_tools'
Physical_NIC_DRIVER_filepath = 'Sys_init'
Virtual_NIC_DRIVER_filepath = 'IAAS'
#Virtual_NIC_DRIVER_version = 'i40evf-3.5.6'

#初始化logging
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("/var/log/sys_init_log.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console)

def base_init():
    #查看系统版本
    logger.info("-----------os edition------------")
    logger.info(os.popen("uname -a 2>&1").read().strip())
    #检查系统分区
    logger.info("-----------system partition------------")
    logger.info(os.popen("lsblk 2>&1").read().strip())
    #检查系统时区
    logger.info("-----------system timezone-------------")
    logger.info(os.popen("date -R 2>&1").read().strip())
    #查看当前CPU频率
    logger.info("-----------current cpu frequency--------------")
    logger.info(os.popen("cat /proc/cpuinfo |grep M 2>&1").read().strip())
    #查看cpu主频
    logger.info("-----------The CPU reality frequency--------------")
    logger.info(os.popen("cat /proc/cpuinfo |grep G 2>&1").read().strip())

def dns_init():
    #DNS
    if not os.path.isfile(r'/etc/resolv.conf.bak'):
        shutil.copy('/etc/resolv.conf', '/etc/resolv.conf.bak')
    with open('/etc/resolv.conf','r') as r:
        lines = r.readlines()
    with open('/etc/resolv.conf', 'w') as w:
        for l in lines:
            if dns not in l:
                w.write(l)
    with open('/etc/resolv.conf', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('nameserver %s\n' % (dns) + content)
    logger.info(os.popen("cat /etc/resolv.conf | grep nameserver").read().strip())
    if os.popen("cat /etc/resolv.conf | grep 'nameserver %s'" %(dns)).read().strip():
        logger.info("--------------dns config complete success---------------")
    else:
        logger.info("--------------dns config complete error---------------")

def ntp_init():
    with open('/etc/ntp.conf', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('server', '#server'))
    with open('/etc/ntp.conf','r') as r:
        lines=r.readlines()
    with open('/etc/ntp.conf', 'w') as w:
        for l in lines:
            if ntp not in l:
                w.write(l)
    with open('/etc/ntp.conf', "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write('server %s\n' % (ntp) + content)
    logger.info(os.popen("cat /etc/ntp.conf |grep server |grep -v '#'").read().strip())
    if (sys == "centos" or sys == "redhat"):
        if (ver == 7):
            logger.info(os.popen("systemctl stop ntpd 2>&1").read().strip())
            logger.info(os.popen("ntpdate %s 2>&1;hwclock -w --systohc 2>&1" % (ntp)).read().strip())
            logger.info(os.popen("systemctl enable ntpd").read().strip())
            logger.info(os.popen("systemctl restart ntpd 2>&1").read().strip())
        else:
            logger.info(os.popen("service ntpd stop 2>&1").read().strip())
            logger.info(os.popen("ntpdate %s 2>&1;hwclock -w --systohc 2>&1" % (ntp)).read().strip())
            logger.info(os.popen("chkconfig ntpd on").read().strip())
            logger.info(os.popen("service ntpd restart 2>&1").read().strip())
    elif (sys == "Ubuntu"):
        logger.info(os.popen("/etc/init.d/ntp stop 2>&1").read().strip())
        logger.info(os.popen("ntpdate %s 2>&1;hwclock -w --systohc 2>&1" % (ntp)).read().strip())
        logger.info(os.popen("/etc/init.d/ntp restart 2>&1").read().strip())
    elif (sys == "Suse"):
        logger.info(os.popen("systemctl stop ntpd 2>&1").read().strip())
        logger.info(os.popen("ntpdate %s 2>&1;hwclock -w --systohc 2>&1" % (ntp)).read().strip())
        logger.info(os.popen("systemctl restart ntpd 2>&1").read().strip())

    logger.info(os.popen("date").read().strip())
    if os.popen("cat /etc/ntp.conf |grep 'server %s'|grep -v '#'" %(ntp)).read().strip():
        logger.info("--------------ntp config complete success---------------")
    else:
        logger.info("--------------ntp config complete error---------------")

def source_init():
    if (sys == "Ubuntu"):
        if not (os.path.isdir('/root/apt')):
            os.makedirs('/root/apt')
        logger.info(os.popen("mv /etc/apt/sources.list /root/apt/").read().strip())
        logger.info(os.popen("wget -O /etc/apt/sources.list %s/source/ubuntu/sources.list-%s.04 2>&1" % (url, ver)).read().strip())
        logger.info(os.popen("apt-get update -y > /dev/null").read().strip())
    elif sys == "centos":
        logger.info(os.popen("yum install wget -y 2>&1").read().strip())
        if not (os.path.isdir('/root/yumbak/')):
            os.makedirs('/root/yumbak/')
        if os.listdir("/root/yumbak"):
            logger.info(os.popen("mv /root/yumbak/CentOS-Base.repo /root/yumbak/CentOS-Base.repo.bak").read().strip())     
        x = [item for item in os.walk('/etc/yum.repos.d')]
        for path, dirs, files in x:
            for file in files:
                if file.endswith('.repo'):
                    shutil.move(path + os.sep + file, '/root/yumbak/')

        if ver == 7:
            version = os.popen("cat /etc/redhat-release | awk '{print $4}'").read().strip()
            logger.info(os.popen("wget -O /etc/yum.repos.d/CentOS-Base.repo %s/source/centos/Centos%s.repo" % (url,version)).read().strip())
        else:
            logger.info(os.popen("wget -O /etc/yum.repos.d/CentOS-Base.repo %s/source/centos/centos%s.repo 2>&1" % (url,ver)).read().strip())
        logger.info(os.popen("yum clean all").read().strip())
        subprocess.call(["sleep 3"], shell=True)
        subprocess.call(["rm -rf /var/cache/yum"], shell=True)
        subprocess.call(["yum makecache"], shell=True)
    elif sys == "redhat":
        if not (os.path.isdir('/root/yumbak/')):
            os.makedirs('/root/yumbak/')
        if os.listdir("/root/yumbak"):
            logger.info(os.popen("mv /root/yumbak/CentOS-Base.repo /root/yumbak/CentOS-Base.repo.bak").read().strip())
        x = [item for item in os.walk('/etc/yum.repos.d')]
        for path, dirs, files in x:
            for file in files:
                if file.endswith('.repo'):
                    shutil.move(path + os.sep + file, '/root/yumbak/')
        logger.info(os.popen("wget -O /etc/yum.repos.d/CentOS-Base.repo %s/source/epel/centos%s.repo" % (url,ver)).read().strip())
        logger.info(os.popen("yum clean all").read().strip())
        subprocess.call(["sleep 3"], shell=True)
        subprocess.call(["rm -rf /var/cache/yum"], shell=True)
        subprocess.call(["yum makecache"], shell=True)
    logger.info("-----------source config complete-------------")

def NIC_speed():
    #网卡速率
    out = os.popen("ls /sys/class/net")
    inter = out.read().split()
    for i in inter:
        a = os.popen("ethtool %s|grep baseT|awk '{print $1}' |grep Full" % (i))
        sup_speed = a.read().split('\n')[0]
        logger.info("------------The %s supported speed is " % (i) + sup_speed + "---------------")
        inter_speed = os.popen("ethtool %s|grep Speed" % (i))
        logger.info("------------The %s reality speed is " %(i) + inter_speed.read().strip() + "---------------")

def bond0_config():
    if ip.split(".")[-1] == "1" or ip.split(".")[-1] == "254":
        logger.info("-------------------IP ERROR-------------------")
        logger.info("-------------------This IP is maybe GATEWAY-----------------")
        exit()

    if mode != "4" and mode != "1":
        logger.info("-------------------MODE ERROR-------------------")
        exit()
    inter = interface.split()
    if (sys == "centos" or sys == "redhat"):
        data = "MASTER=bond0\nSLAVE=yes"
        if mode == "4":
            net = "TYPE=Bond\nDEVICE=bond0\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"xmit_hash_policy=layer2+3 mode=%s mimmon=80\"\nIPADDR=%s\nPREFIX=24\nGATEWAY=%s\nDNS1=%s" %(mode, ip, gateway, bond_dns)
        if mode == "1":
            net = "TYPE=Bond\nDEVICE=bond0\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"mode=%s\"\nIPADDR=%s\nPREFIX=24\nGATEWAY=%s\nDNS1=%s" %(mode, ip, gateway, bond_dns)
        for i in inter:
            subprocess.call(["mkdir /root/net_conf"], shell=True)
            subprocess.call(["cp /etc/sysconfig/network-scripts/ifcfg-%s /root/net_conf/" %(i)], shell=True)
            subprocess.call(["sed -i '/IPADDR=/d' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/NETMASK=/d' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/GATEWAY=/d' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/PREFIX=/d' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/DNS1=/d' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/ONBOOT=/cONBOOT=yes' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            subprocess.call(["sed -i '/BOOTPROTO=/cBOOTPROTO=none' /etc/sysconfig/network-scripts/ifcfg-%s" %(i)], shell=True)
            with open('/etc/sysconfig/network-scripts/ifcfg-%s' %(i),'r') as r:
                content = r.read()
                if data not in content:
                    with open('/etc/sysconfig/network-scripts/ifcfg-%s' %(i), 'a') as f:
                        f.write(data)
                        logger.info("---------------This is " + i + "config------------------")
                        logger.info(os.popen("cat /etc/sysconfig/network-scripts/ifcfg-%s" %(i)).read().strip())
        with open('/etc/sysconfig/network-scripts/ifcfg-bond0', 'w') as fp:
            fp.write(net)
            logger.info(os.popen("cat /etc/sysconfig/network-scripts/ifcfg-bond0").read().strip())
    elif (sys == "Ubuntu" and ver <= 16):
        net = "auto bond0\niface bond0 inet static\naddress %s\ngateway %s\nnetmask %s\nbond-salves all\nbond-mode 802.3ad\nbond-miimon 100\nup ifenslave bond0 %s\ndown ifenslave -d bond0 %s" %(ip, gateway, netmask, interface, interface)
        subprocess.call(["mkdir /root/net_conf"], shell=True)
        subprocess.call(["cp /etc/network/interfaces /root/net_conf/"], shell=True)
        with open('/etc/network/interfaces','r') as r:
            content = r.read()
            if "bond-master" not in content:
                for i in inter:
                    subprocess.call(["sed -i '/address\ /d' /etc/network/interfaces"], shell=True)
                    subprocess.call(["sed -i '/netmask\ /d' /etc/network/interfaces"], shell=True)
                    subprocess.call(["sed -i '/gateway\ /d' /etc/network/interfaces"], shell=True)
                    subprocess.call(["sed -i '/network\ /d' /etc/network/interfaces"], shell=True)
                    subprocess.call(["sed -i '/broadcast\ /d' /etc/network/interfaces"], shell=True)
                    subprocess.call(["sed -i '/dns-nameserver\ /d' /etc/network/interfaces"], shell=True)
                    logger.info(os.popen("sed -i '/iface\ %s/a\\bond-master\ bond0' /etc/network/interfaces" %(i)).read().strip())
            if "auto bond0" not in content:
                with open('/etc/network/interfaces', 'a') as f:
                    f.write(net)
        logger.info(os.popen("cat /etc/network/interfaces").read().strip())

    #重启网卡
    if (sys == "centos" and ver>= 7):
        logger.info(os.popen("systemctl restart network 2>&1").read().strip())
    if (sys == "Ubuntu"):
        logger.info(os.popen("/etc/init.d/networking restart 2>&1").read().strip())
    else:
        logger.info(os.popen("service network restart 2>&1").read().strip())
    
    subprocess.call(["sleep 3"], shell=True)
    bond_sts = os.popen("cat /proc/net/bonding/bond0").read().strip()
    if not bond_sts:
        logger.info("------------------------The BOND config error----------------------")
        exit()
    b_mode = os.popen("cat /proc/net/bonding/bond0 |grep 'Bonding Mode'").read().strip()
    if mode == "4":
        if "802.3ad" not in b_mode:
            logger.info("------------------------The bond mode config error----------------------")
            exit()
    elif mode == "1":
        if "Active-backup policy" not in b_mode:
            logger.info("------------------------The bond mode config error----------------------")
            exit()
    
    if "down" in os.popen("cat /proc/net/bonding/bond0 |grep 'MII Status'| awk '{print $3}'").read().strip():
        logger.info("------------------------There is a interface down,  error----------------------")
        exit()
    
    for i in interface:
        logger.info("------------------This is " + i + os.popen("ethtool %s | grep Speed" %(i)).read().strip() + "------------------")
    subprocess.call(["sleep 1"], shell=True)
    logger.info("------------------This is Bond0 " + os.popen("ethtool bond0 | grep Speed").read().strip() + "-------------------")

def CentOS_init():
    #YUM
    logger.info("------------------------Install Basic dependency packages------------------------")
    logger.info("------------------------Please waiting minites------------------------")
    subprocess.call(["yum install wget gcc gcc-c++ make kernel-devel -y > /dev/null"], shell=True)
    #安装依赖
    subprocess.call(["yum install pciutils -y > /dev/null"], shell=True)
    subprocess.call(["yum install ntpdate -y > /dev/null"], shell=True)
    subprocess.call(["yum -y install ethtool net-tools vim tree ntp curl rsync curl-devel > /dev/null"], shell=True)
    #时区配置
    logger.info(os.popen("mv /etc/localtime /etc/localtime.bak").read().strip())
    logger.info(os.popen("ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime").read().strip())
    logger.info("-------------timezone complete--------------")
    logger.info(os.popen("date").read().strip())
    #关闭防火墙
    if (ver == 7):
        logger.info(os.popen("sudo systemctl stop firewalld").read().strip())
        logger.info(os.popen("sudo chkconfig firewalld off").read().strip())
        out = os.popen("firewall-cmd --state 2>&1")
        logger.info(" ----------The firewall is " + out.read().strip() + "----------")
    else:
        logger.info(os.popen("service iptables stop 2>&1").read().strip())
        logger.info(os.popen("sudo chkconfig iptables off").read().strip())
        out = os.popen("service iptables status 2>&1")
        logger.info(" ----------The firewall is " + out.read().strip() + "----------")
    #关闭SElinux
    with open('/etc/selinux/config', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('SELINUX=enforcing','SELINUX=disabled'))
        logger.info("-----------------Selinux off success------------------")
    
    #打开ip_forward
    ip_forward = os.popen("cat /etc/sysctl.conf |grep 'net.ipv4.ip_forward = 1'|grep -v '#'").read().strip()
    if not ip_forward:
        subprocess.call(["echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf"], shell=True)
        logger.info(os.popen("sysctl -p 2>&1").read().strip())
    logger.info("----------------IP_forward on success--------------------")

    #关闭swap分区
    #subprocess.call(["swapoff -a"], shell=True)
    #subprocess.call(["sed -ri 's/.*swap.*/#&/' /etc/fstab"], shell=True)
    #logger.info("----------------SWAP off success--------------------")
    
    #关闭大页内存
    subprocess.call(["echo never > /sys/kernel/mm/transparent_hugepage/enabled"], shell=True)
    subprocess.call(["echo never > /sys/kernel/mm/transparent_hugepage/defrag"], shell=True)

    subprocess.call(["sed -i '/echo never/d' /etc/rc.local"], shell=True)
    subprocess.call(["sed -i '/touch/iecho never > /sys/kernel/mm/transparent_hugepage/enable' /etc/rc.local"], shell=True)
    subprocess.call(["sed -i '/touch/iecho never > /sys/kernel/mm/transparent_hugepage/defrag' /etc/rc.local"], shell=True)
    logger.info(os.popen("grep Huge /proc/meminfo 2>&1").read().strip())
    logger.info("----------------Hugepages off success--------------------")

def Ubuntu_init():
    logger.info("------------------------Install Basic dependency packages------------------------")
    logger.info("------------------------Please waiting minites------------------------")
    #安装依赖
    subprocess.call(["apt-get -y install libsnmp-dev > /dev/null"], shell=True)
    subprocess.call(["apt-get -y install gcc g++ > /dev/null"], shell=True)
    subprocess.call(["apt-get -y install pciutils > /dev/null"], shell=True)
    subprocess.call(["apt-get -y install ntpdate python > /dev/null"], shell=True)
    subprocess.call(["apt-get -y install ethtool make net-tools rsync vim tree openssh-client ntp > /dev/null"], shell=True)
    logger.info(os.popen("mv /etc/localtime /etc/localtime.bak").read().strip())
    logger.info(os.popen("ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime").read().strip())
    logger.info("-------------timezone complete--------------")
    logger.info(os.popen("date").read().strip())
    #关闭防火墙
    logger.info(os.popen("ufw disable").read().strip())
    #关闭SElinux
    if os.path.isfile('/etc/selinux/config'):
        with open('/etc/selinux/config', "r+") as f:
            read_data = f.read()
            f.seek(0)
            f.truncate()
            f.write(read_data.replace('SELINUX=permissive','SELINUX=disabled'))
    out = os.popen("ufw status 2>&1")
    logger.info("----------The firewall is " + out.read().strip() + "----------")
    #打开ip_forward
    ip_forward = os.popen("cat /etc/sysctl.conf |grep 'net.ipv4.ip_forward = 1'|grep -v '#'").read().strip()
    if not ip_forward:
        subprocess.call(["echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf"], shell=True)
        logger.info(os.popen("sysctl -p 2>&1").read().strip())
    logger.info("----------------IP_forward on success--------------------")

    #关闭swap分区
    subprocess.call(["swapoff -a"], shell=True)
    subprocess.call(["sed -ri 's/.*swap.*/#&/' /etc/fstab"], shell=True)
    logger.info("----------------SWAP off success--------------------")
    
    #关闭大页内存
    subprocess.call(["echo never > /sys/kernel/mm/transparent_hugepage/enabled"], shell=True)
    subprocess.call(["echo never > /sys/kernel/mm/transparent_hugepage/defrag"], shell=True)

    subprocess.call(["sed -i '/echo never/d' /etc/rc.local"], shell=True)
    subprocess.call(["sed -i '/touch/iecho never > /sys/kernel/mm/transparent_hugepage/enable' /etc/rc.local"], shell=True)
    subprocess.call(["sed -i '/touch/iecho never > /sys/kernel/mm/transparent_hugepage/defrag' /etc/rc.local"], shell=True)
    logger.info(os.popen("grep Huge /proc/meminfo 2>&1").read().strip())
    logger.info("----------------Hugepages off success--------------------")

def SuSE_init():
    #SuSE使用zypper进行软件下载
    #关闭防火墙
    if (ver == 12):
        logger.info(os.popen("/usr/bin/systemctl stop SuSEfirewall2.service").read().strip())
    else:
        logger.info(os.popen("service SuSEfirewall2_setup stop").read().strip())
    #SELinux
    #SuSE无SElinux
    #NTP
    logger.info(os.popen("zypper install ntp wget gcc gcc-c++ make 2>&1").read().strip())
    logger.info(os.popen("mv /etc/localtime /etc/localtime.bak").read().strip())
    logger.info(os.popen("ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime").read().strip())
    logger.info("-------------timezone complete--------------")
    logger.info(os.popen("date").read().strip())

def System_initialization():
    if (sys == "Ubuntu"):
        Ubuntu_init()
    elif (sys == "centos" or sys == "redhat"):
        CentOS_init()
    elif (sys == "SuSE"):
        SuSE_init()

def GPU_DRIVE():
    #如果之前已经安装了驱动，并且驱动有问题需要先卸载
    if (gpu_uninstall == "on"):
        st = logger.info(os.popen("nvidia-uninstall").read().strip())
        if (st == 0):
            logger.info(os.popen("reboot now -h").read().strip())

    #显卡驱动安装
    logger.info("--------------NVIDA Driver install-------------------")
    os.chdir('/root')
    if not os.path.exists(GPU_DRIVER_version):
        logger.info("-------Try to download package on " + url + "----------")
        logger.info(os.popen("wget %s/%s/%s" % (url,GPU_DRIVER_filepath,GPU_DRIVER_version)).read().strip())
        if not os.path.exists(GPU_DRIVER_version):
            logger.info("-----------The driver installation package is not exist------------")
            exit()
    
    with open('/etc/modprobe.d/blacklist.conf', 'a') as f:
        f.write('blacklist nouveau\n')
        f.write('options nouveau modeset = 0\n')
    logger.info(os.popen("rmmod nouveau").read().strip())
    logger.info(os.popen("chmod a+x %s" % (GPU_DRIVER_version)).read().strip())
    logger.info(os.popen("./%s --accept-license --silent --no-nouveau-check --disable-nouveau --no-opengl-files 2>&1" % (GPU_DRIVER_version)).read().strip())
    a = os.popen("nvidia-smi -L | cut -d ':' -f 3 | cut -d ')' -f 1").read().strip()
    nvida_id = a.split("\n")
    for l in nvida_id:
        logger.info(os.popen("nvidia-smi -i %s -pm ENABLED" %(l)).read().strip())
        logger.info(os.popen("sed -i '/touch/invidia-smi -i %s -pm ENABLED' /etc/rc.local" %(l)).read().strip())
    if os.popen("nvidia-smi").read().strip():
        logger.info("---------------GPU_DRIVER have complete success--------------------")
    else:
        logger.info("---------------GPU_DRIVER have complete error--------------------")

def cuda_driver():
    #cuda环境安装
    logger.info("---------------cuda install--------------------")
    if not os.path.exists(CUDA_DRIVER_version):
        logger.info("-------Try to download package on " + url + "----------")
        logger.info(os.popen("wget %s/%s/%s" % (url,CUDA_DRIVER_filepath,CUDA_DRIVER_version)).read().strip())
        if not os.path.exists(CUDA_DRIVER_version):
            logger.info("-----------The driver installation package is not exist------------")
            exit()

    a = CUDA_DRIVER_version.split("_")
    version = a[1][0] + a[1][1] + a[1][2]
    logger.info(os.popen("chmod a+x %s" % (CUDA_DRIVER_version)).read().strip())
    logger.info(os.popen("./%s --silent --toolkit --toolkitpath=/usr/local/cuda-%s --samples --samplespath=/usr/local --no-opengl-libs 2>&1" % (CUDA_DRIVER_version, version)).read().strip())
    #查看dev设备目录
    os.chdir("/usr/local/cuda-%s/samples/0_Simple/clock" %(version))
    logger.info(os.popen("make").read().strip())
    logger.info(os.popen("sleep 3").read().strip())
    logger.info(os.popen("chmod +x ./clock").read().strip())
    logger.info(os.popen("./clock").read().strip())
    if os.popen("ls /dev/nvidia-uvm*").read().strip():
        logger.info("---------------CUDA_DRIVER have complete success--------------------")
    else:
        logger.info("---------------CUDA_DRIVER have complete error--------------------")

#网卡驱动
def NIC_DRIVE():
    uname = os.popen('uname --r')
    u = uname.read().strip()
    #物理网卡安装驱动
    os.chdir('/root')
#    logger.info(os.popen("rm -rf /root/i40e*").read().strip())
    if not os.path.exists("%s.tar.gz" %(Physical_NIC_DRIVER_version)):
        logger.info("-------Try to download package on " + url + "----------")
        logger.info(os.popen("wget %s/%s/%s.tar.gz" % (url,Physical_NIC_DRIVER_filepath,Physical_NIC_DRIVER_version)).read().strip())
        if not os.path.exists("%s.tar.gz" %(Physical_NIC_DRIVER_version)):
            logger.info("-----------The driver installation package is not exist------------")
            exit()
    tar = tarfile.open("%s.tar.gz" % (Physical_NIC_DRIVER_version))
    tar.extractall()
    tar.close()
    os.chdir('%s/src/' % (Physical_NIC_DRIVER_version))
    logger.info(os.popen("make && make install 2>&1").read().strip())
    if not (sys == 'centos' and ver >= 7):
        shutil.copy('i40e.ko', '/lib/modules/%s/kernel/drivers/net' % (u))
        os.chdir('/lib/modules/%s/kernel/drivers/net' % (u))
        logger.info(os.popen("rmmod i40e &").read().strip())
        logger.info(os.popen("modprobe i40e &").read().strip())
        logger.info(os.popen("lsmod").read())
    logger.info(os.popen("rmmod i40e  && modprobe i40e &").read().strip())
    logger.info(os.popen("lsmod").read())
    #重启网卡
    if (sys == "centos" and ver>= 7):
        logger.info(os.popen("systemctl restart network").read().strip())
    if (sys == "Ubuntu"):
        logger.info(os.popen("/etc/init.d/networking restart").read().strip())
    else:
        logger.info(os.popen("service network restart").read().strip())
    inters = os.popen("ls /sys/class/net").read().strip().split()
    b = ""
    for i in inters:
        a = os.popen("ethtool -i %s" %(i)).read().strip()
        b = b + a
    nic_ver = Physical_NIC_DRIVER_version.split("-")
    if nic_ver[1] in b:
        logger.info("---------------NIC_DRIVE complete success------------------")
    else:
        logger.info("---------------NIC_DRIVE complete error------------------")

def max_performance():
    if sys == "Ubuntu":
        ker_ver = os.popen("uname -r").read().strip()
        logger.info(os.popen("apt-get install linux-tools-common linux-tools-%s  linux-cloud-tools-%s cpufrequtils  > /dev/null" %(ker_ver, ker_ver)).read())
        logger.info(os.popen("cpupower frequency-set --governor performance 2>&1 &").read().strip())
    else:
        logger.info(os.popen("yum install tuned -y  > /dev/null").read().strip())
        logger.info(os.popen("service tuned restart 2>&1").read().strip())
        if ver == 7:
            logger.info(os.popen("systemctl enable tuned.service 2>&1 &").read().strip())
        else:
            logger.info(os.popen("chkconfig tuned on 2>&1 &").read().strip())
        subprocess.call(["sleep 3"], shell=True)
        subprocess.call(["tuned-adm profile latency-performance 2>&1 &"], shell=True)
    logger.info("---------------Max_performance complete success------------------")

def NetworkManager():
    logger.info("-----------------------Close NetworkManager---------------------")
    logger.info(os.popen("service NetworkManager stop").read())
    subprocess.call(["systemctl disable NetworkManager"], shell=True)
    if ver == 6:
        subprocess.call(["chkconfig NetworkManager off"], shell=True)

    if not os.popen("ps aux|grep NetworkManager |grep -v grep").read().strip():
        logger.info("-----------------------NetworkManager Close success---------------------")

def prom_monitor():
    logger.info(os.popen("wget %s 2>&1" %(monitor_url)).read().strip())
    mon = monitor_url.split("/")[-1]
    logger.info(os.popen("bash %s" %(mon)).read().strip())
    logger.info(os.popen("ps -ef | grep prom-monitor").read().strip())
    logger.info(os.popen("grep 'hostname' /iflymonitor/prom-monitor/cfg.json").read().strip())
    if os.popen("ps aux|grep prom |grep -v grep").read().strip():
        logger.info("--------------prom-monitor complete success-----------------------")
    else:
        logger.info("--------------prom-monitor complete error-----------------------")

def check_network_info():
    #获取有IP的网络接口
    interfaces = os.popen("ls /sys/class/net").read().strip().split()
    inter = []
    for i in interfaces:
        if os.popen("ip addr|grep inet |grep %s" %(i)).read().strip():
            inter.append(i)
    inter.remove('lo')
    if not inter:
        logger.info("---------------There is no Available network Interfaces-----------------")
        exit()
    if sys == "Ubuntu":
        #校验netmask、gateway关键词
        file = '/etc/network/interfaces'
        f = open(file, 'r')
        content = f.read()
        netmask = re.findall(r'\w+\s255\.\d+\.\d+\.\d+', content)
        gateway = re.findall(r'gateway\s\d+\.\d+\.\d+\.\d+', content)

        for l in netmask:
            if l.split()[0] != "netmask":
                logger.info("---------------The netmask key words is error-----------------")
                logger.info("---------------" + l + "-----------------")

        if not gateway:
            logger.info("---------------The gateway key words is error-----------------")
            logger.info("---------------Please check the config file-----------------")
        f.close()

    if sys == "centos" or sys == "redhat":
        #校验NETMASK、GATEWAY、ONBOOT、PREFIX，有bond0则校验BONDING_OPTS和mode4
        for s in inter:
            file = "/etc/sysconfig/network-scripts/ifcfg-%s" %(s)
            f = open(file, 'r')
            content = f.read()
            if "NETMASK" not in content:
                if "PREFIX" not in content:
                    logger.info("---------------The interface " + s + " NETMASK config is error-----------------")
            if "GATEWAY" not in content:
                logger.info("---------------The interface " + s + " GATEWAY config is error-----------------")
            if "ONBOOT=\"yes\"" not in content and "ONBOOT=yes" not in content:
                logger.info("---------------The interface " + s + " ONBOOT config is error-----------------")
            f.close()
    
        is_bond0 = os.popen("ls /etc/sysconfig/network-scripts/|grep bond0").read().strip()
        if is_bond0:
            path = "/etc/sysconfig/network-scripts/ifcfg-bond0"
            fp = open(path, 'r')
            content2 = fp.read()
            if "BONDING_OPTS" not in content2:
                logger.info("---------------The interface bond0 BONDING_OPTS config is error-----------------")
            else:
                co = os.popen("cat %s |grep 'BONDING_OPTS'" %(path)).read().strip()
                if "mode=4" not in co:
                    logger.info("---------------The mode4 config is error-----------------")
                logger.info("---------------" + co + "-----------------")
            f.close()

    #校验nameserver
    file = "/etc/resolv.conf"
    f = open(file, 'r')
    content = f.read()
    dns_server = re.findall(r'[a-z]+\s\d+.\d+.\d+.\d+', content)
    for d in dns_server:
        if d.split()[0] != "nameserver":
            logger.info("---------------The nameserver key words is error-----------------")
            logger.info("---------------" + d + "-----------------")
    f.close()
    logger.info("---------------The Key words check complete success-----------------")

if (bond0_status == 'on'):
    bond0_config()

base_init()

if (dns_status == 'on'):
    dns_init()

if (source_status == 'on'):
    source_init()

System_initialization()
NIC_speed()

if (ntp_status == 'on'):
    ntp_init()

if os.popen("lspci |grep NVIDIA").read().strip():
    if (gpu_status == 'on'):
        GPU_DRIVE()
    if (cuda_status == 'on'):
        cuda_driver()

nic_inters = os.popen("ls /sys/class/net").read().strip().split()
tmp = ""
for i in nic_inters:
    tmp0 = os.popen("ethtool -i %s" %(i)).read().strip()
    tmp = tmp + tmp0
if "i40e" in tmp:
    if (nic_status == 'on'):
        NIC_DRIVE()
if not os.popen("ps aux|grep prom |grep -v grep").read().strip():
    if (monitor_status == 'on'):
        prom_monitor()

if (max_per_status == 'on'):
    max_performance()

check_network_info()

if (NetworkManager_status == 'on'):
    NetworkManager()

subprocess.call(["cat /var/log/sys_init_log.log |grep success"], shell=True)
subprocess.call(["cat /var/log/sys_init_log.log |grep error"], shell=True)