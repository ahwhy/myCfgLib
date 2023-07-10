#/bin/python
#coding:utf-8

import os, shutil, subprocess, platform
def CentOS():
    #DNS
    if not os.path.isfile(r'/etc/resolv.conf.bak'):
        shutil.copy('/etc/resolv.conf', '/etc/resolv.conf.bak')
    with open('/etc/resolv.conf.bak','r') as r:
        lines = r.readlines()
    with open('/etc/resolv.conf.bak', 'w') as w:
        for l in lines:
            if '172.16.xx.xx' not in l:
                w.write(l)
    with open('/etc/resolv.conf.bak', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('nameserver 172.16.xx.xx\n'+content)
    #YUM,此处以Centos6为例，具体下载版本根据实际系统版本决定，如centos7.repo
    if not (os.path.isdir('/root/yumbak/')):
        os.makedirs('/root/yumbak/')
    x = [item for item in os.walk('/etc/yum.repos.d')]
    for path, dirs, files in x:
        for file in files:
            if file.endswith('.repo'):
                shutil.move(path + os.sep + file, '/root/yumbak/')
    subprocess.call(["wget -O /etc/yum.repos.d/CentOS-Base.repo http://xxx.xxx.com/source/centos/centos6.repo"], shell=True)
    subprocess.call(["yum clean all && yum makecache"], shell=True)
    #关闭防火墙
    if(int(float(platform.dist()[1])) == 7):
        subprocess.call(["sudo systemctl stop firewalld"], shell=True)
        subprocess.call(["sudo chkconfig firewalld off"], shell=True)
    else:
        subprocess.call(["sudo chkconfig iptables off"], shell=True)
    #关闭SElinux
    with open('/etc/selinux/config', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('SELINUX=enforcing','SELINUX=disabled'))
    #NTP
    with open('/etc/ntp.conf', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('^server', '#server'))
    with open('/etc/ntp.conf','r') as r:
        lines=r.readlines()
    with open('/etc/ntp.conf', 'w') as w:
        for l in lines:
            if 'ntp1.test.com' not in l:
                w.write(l)
    with open('/etc/ntp.conf', "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write('server ntp1.test.com\n'+content)
    if(int(float(platform.dist()[1])) == 7):
        subprocess.call(["systemctl stop ntpd"], shell=True)
        subprocess.call(["ntpdate ntp1.test.com;hwclock - -systohc"], shell=True)
        subprocess.call(["systemctl enable ntpd"], shell=True)
        subprocess.call(["systemctl restart ntpd"], shell=True)
    else:
        subprocess.call(["service ntpd stop"], shell=True)
        subprocess.call(["ntpdate 172.16.xx.xx;hwclock --systohc"], shell=True)
        subprocess.call(["chkconfig ntpd on"], shell=True)
        subprocess.call(["service ntpd restart"], shell=True)

def Ubuntu():
    #DNS
    if not os.path.isfile(r'/etc/resolv.conf.bak'):
        shutil.copy('/etc/resolv.conf', '/etc/resolv.conf.bak')
    with open('/etc/resolvconf/resolv.conf.d/base', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('nameserver 172.16.xx.xx\n' + content)
    subprocess.call(["resolvconf -u"], shell=True)
    #YUM，此处以Ubuntu14为例，具体下载版本根据实际系统版本决定，如sources.list-16.04
    shutil.copytree('/etc/apt/','/root/apt/')
    subprocess.call(["wget -O /etc/apt/sources.list http://xxx.xxx.com/source/ubuntu/sources.list-14.04"], shell=True)
    subprocess.call(["apt-get update -y"], shell=True)
    #关闭防火墙
    subprocess.call(["ufw disable"], shell=True)
    #关闭SElinux
    if os.path.isfile('/etc/selinux/config'):
        with open('/etc/selinux/config', "r+") as f:
            read_data = f.read()
            f.seek(0)
            f.truncate()
            f.write(read_data.replace('SELINUX=permissive','SELINUX=disabled'))
    #NTP
    with open('/etc/ntp.conf', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('server', '#server'))
    with open('/etc/ntp.conf','r') as r:
        lines=r.readlines()
    with open('/etc/ntp.conf', 'w') as w:
        for l in lines:
            if 'ntp1.test.com' not in l:
                w.write(l)
    with open('/etc/ntp.conf', "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write('server ntp1.test.com\n'+content)
    subprocess.call(["/etc/init.d/ntp stop"], shell=True)
    subprocess.call(["ntpdate ntp1.test.com;hwclock --systohc"], shell=True)
    subprocess.call(["/etc/init.d/ntp restart"], shell=True)

def Redhat():
    #DNS
    if not os.path.isfile(r'/etc/resolv.conf.bak'):
        shutil.copy('/etc/resolv.conf', '/etc/resolv.conf.bak')
    with open('/etc/resolv.conf.bak','r') as r:
        lines = r.readlines()
    with open('/etc/resolv.conf.bak', 'w') as w:
        for l in lines:
            if '172.16.xx.xx' not in l:
                w.write(l)
    with open('/etc/resolv.conf.bak', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('nameserver 172.16.xx.xx\n'+content)
    #YUM，此处以Redhat6为例，具体下载版本根据实际系统版本决定，如rhel7.1.repo
    if not (os.path.isdir('/root/rhel/')):
        os.makedirs('/root/rhel/')
    x = [item for item in os.walk('/etc/yum.repos.d')]
    for path, dirs, files in x:
        for file in files:
            if file.endswith('.repo'):
                shutil.move(path + os.sep + file, '/root/rhel/')
    subprocess.call(["wget -O /etc/yum.repos.d/rhel6.repo http://xxx.xxx.com/source/rhel/rhel6.repo"], shell=True)
    subprocess.call(["yum clean all && yum makecache"], shell=True)
    #关闭防火墙
    subprocess.call(["chkconfig iptables off"], shell=True)
    #关闭SElinux
    with open('/etc/selinux/config', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('SELINUX=enforcing','SELINUX=disabled'))
    #NTP
    with open('/etc/ntp.conf', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('^server', '#server'))
    with open('/etc/ntp.conf', 'r') as r:
        lines = r.readlines()
    with open('/etc/ntp.conf', 'w') as w:
        for l in lines:
            if 'ntp1.test.com' not in l:
                w.write(l)
    with open('/etc/ntp.conf', "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write('server ntp1.test.com\n' + content)
    subprocess.call(["service ntpd stop"], shell=True)
    subprocess.call(["ntpdate ntp1.test.com;hwclock - -systohc"], shell=True)
    subprocess.call(["chkconfig ntpd on"], shell=True)
    subprocess.call(["service ntpd restart"], shell=True)

def SuSE():
    #DNS
    if not os.path.isfile(r'/etc/resolv.conf.bak'):
        shutil.copy('/etc/resolv.conf', '/etc/resolv.conf.bak')
    with open('/etc/resolv.conf.bak','r') as r:
        lines = r.readlines()
    with open('/etc/resolv.conf.bak', 'w') as w:
        for l in lines:
            if '172.16.xx.xx' not in l:
                w.write(l)
    with open('/etc/resolv.conf.bak', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('nameserver 172.16.xx.xx\n'+content)
    #YUM
    #SuSE使用zypper进行软件下载
    #关闭防火墙
    if (int(float(platform.dist()[1])) == 12):
        subprocess.call(["/sbin/systemctl stop SuSEfirewall2.service"], shell=True)
    else:
        subprocess.call(["/sbin/service SuSEfirewall2_setup stop"], shell=True)
    #SELinux
    #SuSE无SElinux
    #NTP
    with open('/etc/ntp.conf', "r+") as f:
        read_data = f.read()
        f.seek(0)
        f.truncate()
        f.write(read_data.replace('server', '#server'))
    with open('/etc/ntp.conf','r') as r:
        lines=r.readlines()
    with open('/etc/ntp.conf', 'w') as w:
        for l in lines:
            if 'ntp1.test.com' not in l:
                w.write(l)
    with open('/etc/ntp.conf', "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write('server ntp1.test.com\n'+content)
    subprocess.call(["/etc/init.d/ntp stop"], shell=True)
    subprocess.call(["ntpdate ntp1.test.com;hwclock --systohc"], shell=True)
    subprocess.call(["/etc/init.d/ntp restart"], shell=True)

def UsePlatform():
    system = platform.dist()
    if (system[0] == "Ubuntu"):
        Ubuntu()
    elif (system[0] == "centos"):
        CentOS()
    elif (system[0] == "redhat"):
        Redhat()
    elif (system[0] == "SuSE"):
        SuSE()

UsePlatform()