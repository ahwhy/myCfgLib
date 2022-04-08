#!/bin/bash
#1、安装基础环境:添加DNS、更新yum源、修改主机名、NTP、关闭selinux、关闭防火墙、关闭重启CTtl+alt+delete组合键、修改最大文件描述符、修改最大文件描述符
function Initialization()  
{
    basePath=`pwd`
    echo $basePath
    platform=`python -c 'import platform;print platform.dist()[0].lower()'`
	#判断是否为Centos7系统
    if [[ $platform == 'centos' ]]; then
		#DNS
        [[ ! -e /etc/resolv.conf.bak ]] && cp /etc/resolv.conf{,.bak}
        grep "172.16.xx.xx" /etc/resolv.conf &> /dev/null || sed -i '1i\nameserver 172.16.xx.xx' /etc/resolv.conf
        
		#yum 源
        [[ ! -d /root/yumbak ]] && mkdir /root/yumbak
        mv /etc/yum.repos.d/*.repo /root/yumbak/
        wget -O /etc/yum.repos.d/CentOS-Base.repo http://172.16.xx.xx/source/centos/centos7.repo
        yum clean all && yum makecache

        #yum upgrade -y
        yum -y install net-tools git lrzsz rsync vim bind-utils openssh-clients tree wget ntp net-snmp net-snmp-utils net-snmp-devel net-snmp-libs net-snmp-perl mrtg nmap sysstat
		
		#性能最大化
		yum install -y cpupowerutils
		cpupower frequency-set --governor performance
		cpupower monitor

		#NTP
        sed -i "s/^server/#server/g" /etc/ntp.conf
        grep "^server 172.16.xx.xx" /etc/ntp.conf &> /dev/null || sed -i '21i\server 172.16.xx.xx' /etc/ntp.conf
        systemctl stop ntpd
        ntpdate 172.16.xx.xx;hwclock --systohc
        systemctl enable ntpd
        systemctl restart ntpd
	
		#关闭防火墙
        systemctl stop firewalld
        chkconfig firewalld off

		#关闭SElinux
        sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config 

		#关闭重启CTtl+alt+delete组合键
        [[ -e /usr/lib/systemd/system/ctrl-alt-del.target ]] && mv /usr/lib/systemd/system/ctrl-alt-del.target{,.bak}  
        init q
		# ln -s /usr/lib/systemd/system/reboot.target /usr/lib/systemd/system/ctrl-alt-del.target #开启重启CTtl+alt+delete组合键

    elif [[ $platform == 'ubuntu' ]]; then
		#DNS
    	[[ ! -e /etc/resolv.conf.bak ]] && cp /etc/resolv.conf{,.bak}
    	echo "nameserver 172.16.xx.xx" > /etc/resolvconf/resolv.conf.d/base && resolvconf -u

		#yum源
        [[ ! -d /root/apt ]] && mkdir /root/apt
        cp /etc/apt/* /root/apt
    	wget -O /etc/apt/sources.list http://172.16.59.33/source/ubuntu/sources.list-14.04
    	apt-get update -y
    	apt-get install net-tools git lrzsz rsync vim dnsutils openssh-server tree wget ntp snmp  mrtg nmap sysstat -y
		
		#性能最优
		apt-get install  -y  linux-tools-common linux-tools-4.4.0-31-generic  linux-cloud-tools-4.4.0-31-generic
		cpupower frequency-set --governor performance
		apt-get install -y cpufrequtils
		chmod u+s /usr/bin/cpufreq-set
		cpufreq-info 
        
		#NTP
        sed -i "s/^server/#server/g" /etc/ntp.conf
        grep "^server 172.16.xx.xx" /etc/ntp.conf &> /dev/null || sed -i '19i\server 172.16.xx.xx' /etc/ntp.conf
        /etc/init.d/ntp stop
        ntpdate 172.16.xx.xx;hwclock --systohc
        /etc/init.d/ntp restart
	
		#关闭防火墙
        ufw disable  
		
		#关闭SElinux
        [[ -e /etc/selinux/config ]] &&  sed -i "s/SELINUX=permissive/SELINUX=disabled/g" /etc/selinux/config 

		 #关闭重启CTtl+alt+delete组合键
        [[ -e /etc/init/control-alt-delete.conf ]] && cp /etc/init/control-alt-delete.conf{,.bak}
        sed -i 's/^exec/#exec/g' /etc/init/control-alt-delete.conf

        # [[ ! -e /etc/ssh/sshd_config.bak ]] && cp /etc/ssh/sshd_config{,.bak}
        # sed -i 's/^PermitRootLogin without-password/#PermitRootLogin without-password/g' /etc/ssh/sshd_config
        # grep "^PermitRootLogin yes" /etc/ssh/sshd_config &> /dev/null || sed -i "28i\PermitRootLogin yes" /etc/ssh/sshd_config
        # service ssh restart   

        # sed -i "s/#UseDNS yes/UseDNS no/"  /etc/ssh/sshd_config
        # sed -i 's/^GSSAPIAuthentication yes$/GSSAPIAuthentication no/g' /etc/ssh/sshd_config
        # sed -i 's/#   StrictHostKeyChecking ask/StrictHostKeyChecking=no/' /etc/ssh/ssh_config 
    fi
    
    #环境变量
    [[ ! -e /etc/profile.bak ]] && cp /etc/profile{,.bak}
    grep "LD_LIBRARY_PATH" /etc/profile &> /dev/null || printf "export LD_LIBRARY_PATH=./\n" >> /etc/profile
    grep "ulimit" /etc/profile &> /dev/null || printf "ulimit -SHn 65535\n" >> /etc/profile #修改最大文件描述符
    source /etc/profile

    cd $basePath
}

# 2、安装通用组件Salt-minion,pmc,pauto_client
function InstallOthers()  
{
    basePath=`pwd`
    [[ ! -e msp.tar.gz ]] && wget http://172.16.59.33/Standard/myli7/msp.tar.gz
    [[ -e msp.tar.gz ]] && tar -zxf msp.tar.gz -C /tmp/
    [[ -d /tmp/pmc ]] && rm -rf msp.tar.gz
    [[ ! -d /msp/platform/mmp/pmc ]] && mkdir -p /msp/platform/mmp/pmc
    [[ ! -d /msp/platform/tools/pauto_client ]] && mkdir -p /msp/platform/tools/pauto_client
    platform=`python -c 'import platform;print platform.dist()[0].lower()'`
    if [[ $platform == 'centos' ]]; then
        yum install salt-minion -y
        [[ ! -e /etc/salt/minion.bak ]] && cp /etc/salt/minion{,.bak}
        sed -i -e "/^#master: salt/s/#master: salt/master: 192.168.72.227/" /etc/salt/minion
        systemctl enable salt-minion
        systemctl restart salt-minion

        [[ ! -e /msp/platform/mmp/pmc/pmc ]] && cp -r /tmp/pmc/pmc_centos/pmc-7_hf/* /msp/platform/mmp/pmc
        cd /msp/platform/mmp/pmc
        chmod +x /msp/platform/mmp/pmc/pmc
        nohup ./pmc -d &

        [[ ! -e /msp/platform/tools/pauto_client/pauto_client ]] && cp -r /tmp/pauto_client_centos/* /msp/platform/tools/pauto_client
        cd /msp/platform/tools/pauto_client
        chmod +x /msp/platform/tools/pauto_client/pauto_client
        ./pauto_client

        cd $basePath

        [[ ! -e /etc/rc.local.bak ]]  && cp /etc/rc.local{,.bak}
        grep "LD_LIBRARY_PATH" /etc/rc.local &> /dev/null || cat > /etc/rc.local << EOF
#!/bin/bash
touch /var/lock/subsys/local
export LD_LIBRARY_PATH=./
ulimit -SHn 65535
cd /msp/platform/mmp/pmc
nohup ./pmc -d &
cd /msp/platform/tools/pauto_client
./pauto_client
exit 0
EOF
        chmod +x /etc/rc.d/rc.local
        yum install gcc cmake make -y
        systemctl status salt-minion

    elif [[ $platform == 'ubuntu' ]]; then
        apt-get install python-software-properties
        add-apt-repository  ppa:saltstack/salt
        apt-get update -y
    	apt-get install salt-minion -y
    	[[ ! -e /etc/salt/minion.bak ]] && cp /etc/salt/minion{,.bak}
    	sed -i -e "/^#master: salt/s/#master: salt/master: 192.168.72.227/" /etc/salt/minion
        /etc/init.d/salt-minion restart

        [[ ! -e /msp/platform/mmp/pmc/pmc ]] && cp -r /tmp/pmc/pmc_ubuntu/pmc_u_hf/* /msp/platform/mmp/pmc
        cd /msp/platform/mmp/pmc
        chmod +x /msp/platform/mmp/pmc/pmc
        nohup ./pmc -d &

        [[ ! -e /msp/platform/tools/pauto_client/pauto_client ]] && cp -r /tmp/pauto_client_Ubuntu/* /msp/platform/tools/pauto_client
        cd /msp/platform/tools/pauto_client
        chmod +x /msp/platform/tools/pauto_client/pauto_client
        ./pauto_client

        cd /etc/init.d/
        [[ ! -e /etc/init.d/test ]] && cat > /etc/init.d/test << EOF
#!/bin/bash
export LD_LIBRARY_PATH=./
ufw disable
/etc/init.d/salt-minion start
ulimit -SHn 65535
cd /msp/platform/mmp/pmc
nohup ./pmc -d &
cd /msp/platform/tools/pauto_client
./pauto_client -d &
exit 0
EOF
        chmod 755 /etc/init.d/test
        update-rc.d test defaults 90
        cd $basePath
        /etc/init.d/salt-minion status
    fi

	#安装监控
    [[ ! -e InstallAgent-2.2.8_Linux.py ]] && wget http://172.16.XX.XX/downloads/zabbix_scripts/scripts/InstallAgent-2.2.8_Linux.py
    [[ -e InstallAgent-2.2.8_Linux.py ]] && python InstallAgent-2.2.8_Linux.py
    ps -ef | grep pmc
    ps -ef | grep pauto_client
    service ntp  status
}

Initialization
InstallOthers