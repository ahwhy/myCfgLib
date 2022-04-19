#!/bin/bash
#please Ready hostname && sshd-keygen && hosts && cpupower && disk

#set fileformat=unix
#set -o errexit

NVIDIA="NVIDIA-Linux-x86_64-418.87.00.run"
#NVIDIA="NVIDIA-Linux-x86_64-440.36.run"
CUDA="cuda_10.1.168_418.67_linux.run"
#CUDA="cuda_10.2.89_440.33.01_linux.run"

#NO.1 check Ntp
echo "start NO.1 check Ntp"
cat /etc/ntp.conf | egrep "255.254|255.255" &> /dev/null
if [ $? -eq 0 ];then
    ntpq -p | grep \*  &> /dev/null
    if [ $? -eq 0 ];then
        echo -e "\033[47;30m [----- NO.1 Ntp is Ready -----] \033[0m"
    else
        echo -e "\033[47;31;5m [----- NO.1 Ntp is Not Ready -----] \033[0m"
    fi
else
   echo -e "\033[47;31;5m [----- NO.1 Ntp IP is Not Exist -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.2 check Dns
echo "start NO.2 check Dns"
cat /etc/resolv.conf | egrep "255.254|255.255"  &> /dev/null
if [ $? -eq 0 ];then
    echo -e "\033[47;30m [----- NO.2 Dns is Ready -----] \033[0m"
else
    echo -e "\033[47;31;5m [----- NO.2 Dns is Not Ready -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.3 check Swap
echo "start NO.3 check Swap"
swap=`free |grep -i swap|awk '{print $2}'`
if [ "$swap" == "0" ];then
    echo -e "\033[47;30m [----- NO.3 Swap is Closed -----] \033[0m"
else
    echo -e "\033[47;31;5m [----- NO.3 Swap is Open -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.4 check Firewall
echo "start NO.4 check Firewall"
systemctl stop firewalld.service
systemctl disable firewalld.service
systemctl status firewalld.service &> /dev/null
if [ $? -eq 0 ];then
  echo -e "\033[47;31;5m [----- NO.4 Firewalld is Open -----] \033[0m"
else
  echo -e "\033[47;30m [----- NO.4 Firewalld is Closed -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.5 check SElinux
echo "start NO.5 check SElinux"
sed -i '/^SELINUX=/c\SELINUX=disabled' /etc/sysconfig/selinux
setenforce 0 &> /dev/null
selinux_status=`getenforce`
if [ "$selinux_status" == "Disabled" ] || [ "$selinux_status" == "Permissive" ];then
  echo -e "\033[47;30m [----- NO.5 SElinux is Closed -----] \033[0m"
else
  echo -e "\033[47;31;5m [----- NO.5 SElinux is Open -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.6 check NetworkManager
echo "start NO.6 check NetworkManager"
systemctl stop NetworkManager &> /dev/null
systemctl disable NetworkManager &> /dev/null
systemctl status NetworkManager &> /dev/null
if [ $? -eq 0 ];then
  echo -e "\033[47;31;5m [----- NO.6 NetworkManager is Open -----] \033[0m"
else
  echo -e "\033[47;30m [----- NO.6 NetworkManager is Closed -----] \033[0m"
fi
echo "****************************************"
sleep 1

#NO.7 ssh basic
echo "start NO.7 ssh basic"
sed -i "s/#UseDNS yes/UseDNS no/"  /etc/ssh/sshd_config
sed -i 's/^GSSAPIAuthentication yes$/GSSAPIAuthentication no/g' /etc/ssh/sshd_config
sed -i 's/#   StrictHostKeyChecking ask/StrictHostKeyChecking=no/' /etc/ssh/ssh_config
systemctl restart sshd.service &> /dev/null
echo -e "\033[47;30m [----- NO.7 Ssh Basic is Ready-----] \033[0m"
echo "****************************************"
sleep 1

#NO.8 Hugepage change
echo "start NO.8 Hugepage change"
rm -f /etc/rc.local
ln -s /etc/rc.d/rc.local /etc/rc.local
echo "echo '0' > /sys/kernel/mm/transparent_hugepage/khugepaged/defrag"  >>  /etc/rc.local
echo "echo never > /sys/kernel/mm/transparent_hugepage/defrag"  >>  /etc/rc.local
echo "echo never > /sys/kernel/mm/transparent_hugepage/enabled"  >>  /etc/rc.local
echo "nvidia-smi -pm 1"  >>  /etc/rc.local
chmod +x /etc/rc.local
chmod +x /etc/rc.d/rc.local
echo -e "\033[47;30m [----- NO.8 Hugepage is changed -----] \033[0m"
echo "****************************************"
sleep 

#NO.9 Ulimit change
echo "start NO.9 Ulimit change"
ulimit -SHn 655360
cat > /etc/security/limits.conf << FORMAT
* soft nofile 655350
* hard nofile 655350
@hadoop soft nproc 655350000
@hadoop hard nproc 655350000
@root soft nproc 655350000
@root hard nproc 655350000
FORMAT
#echo "* - nofile 655360" > /etc/security/limits.d/20-nproc.conf
echo -e "\033[47;30m [----- NO.9 Ulimit is changed -----] \033[0m"
echo "****************************************"
sleep 1

#NO.10 Kernel change
echo "start NO.10 Kernel change"
cat > /etc/sysctl.conf << FORMAT
net.ipv4.ip_forward = 1
vm.max_map_count = 655360
vm.swappiness = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 0            
net.ipv4.tcp_fin_timeout = 30
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 262144
net.ipv4.tcp_max_orphans = 262144
net.ipv4.tcp_max_syn_backlog = 262144
net.ipv4.tcp_synack_retries = 1
net.ipv4.tcp_syn_retries = 1
net.ipv4.tcp_keepalive_time = 300
FORMAT
sysctl -p  &> /dev/null
echo -e "\033[47;30m [----- NO.10 Kernel is changed -----] \033[0m"
echo "****************************************"
sleep 1

#NO.11 TMOUT change
echo "start NO.11 TMOUT change"
sed -i 's/TMOUT/\#TMOUT/g'  /etc/profile
source /etc/profile
echo -e "\033[47;30m [----- NO.11 TMOUT is changed -----] \033[0m"
echo "****************************************"
sleep 1

#NO.12 Make Yum change
echo "start NO.12  Make Yum change"
if [ ! -d /etc/yum.repos.d/bak ]; then
    mkdir /etc/yum.repos.d/bak
    echo "Create /etc/yum.repos.d/bak"
fi
mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/bak/
touch /etc/yum.repos.d/centos-vault.repo
cat > /etc/yum.repos.d/centos-vault.repo < FORMAT
[base]
name=base
baseurl=https://mirrors.tuna.tsinghua.edu.cn/centos-vault/7.4.1708/os/x86_64/
enabled=1
gpgcheck=0

[extras]
name=extras
baseurl=https://mirrors.tuna.tsinghua.edu.cn/centos-vault/7.4.1708/extras/x86_64/
enabled=1
gpgcheck=0

[updates]
name=updates
baseurl=https://mirrors.tuna.tsinghua.edu.cn/centos-vault/7.4.1708/updates/x86_64/
enabled=1
gpgcheck=0

[epel]
name=epel
baseurl=https://mirrors.tuna.tsinghua.edu.cn/epel/7/x86_64/
enabled=1
gpgcheck=0
FORMAT
yum clean all >> /dev/null 2>&1
yum makecache >> /dev/null 2>&1
echo -e "\033[47;30m [----- NO.12 Make Yum Is Done-----] \033[0m"
echo "****************************************"
sleep 1

#NO.13 Install Soreware
echo "start NO.13 Install Soreware"
yum install -y vim redhat-lsb-core lshw mariadb ipmitool sox unzip redhat-lsb-core portaudio protaudio-devel compat-openmpi16-1.6.4-10.5.el7 rsync ntp kernel-devel-`uname -r` wget openssh-clients environment-modules net-tools MySQL-python dmidecode leveldb-devel snappy-devel hdf5-devel nfs-utils rpcbind lspci expect tcl gcc-gfortran tk pciutils bc perl sg3_utils libXp* libXmu.so* expect openssl-devel gtk2 atk cairo libxml2-python tcsh libnl lsof numactl tk mesa-libGLU* infinipath-psm libpapi libgflags* lapack lapack-devel blas atlas-* openblas
yum remove -y NetworkManager* firefox
ln -s /usr/lib64/libgflags.so.2.1 /usr/lib64/libgflags.so.2
echo -e "\033[47;30m [----- NO.13 Install Soreware Is Done -----] \033[0m"
echo "****************************************"
sleep 1

#NO.14 Install Nvidia
echo "start NO.14 Install Nvidia and Cuda"
yum install -y pclutils wget dkms
if [ ! -f /etc/modprobe.d/blacklist.conf ]; then
    touch /etc/modprobe.d/blacklist.conf
    echo "Create /etc/modprobe.d/blacklist.conf"
fi
cat > /etc/modprobe.d/blacklist.conf << FORMAT
blacklist nouveau
options nouveau modeset=0
FORMAT
rmmod nouveau
rmmod nv_peer_mem
rmmod nvidia_uvm
rmmod nvidia_drm
rmmod nvidia_modeset
rmmod nvidia
wget -N http://172.16.0.2/Soft/GPU_Driver/$NVIDIA -P /root/  &> /dev/null
wget -N http://172.16.0.2/Soft/CUDA_tools/$CUDA -P /root/  &> /dev/null
sh /root/$NVIDIA --kernel-source-path=/usr/src/kernels/$(uname -r) -k $(uname -r) --dkms -s 
mv /boot/initramfs-$(uname -r).img /root/initramfs-$(uname -r).img.bak
dracut /boot/initramfs-$(uname -r).img $(uname -r)
nvidia-smi -pm 1
echo -e "\033[47;30m [----- NO.14 Install Nvidia Is Done -----] \033[0m"
echo "****************************************"
sleep 1

date=`date`
echo "Check Done IN $date"

#sh cuda_10.2.89_440.33.01_linux.run
#cd /usr/local/cuda-10.2/samples/0_Simple/clock
#make
#./clock
#mknod -m 660 /dev/nvidia-modeset c 195 254
#ls /dev/nv*
