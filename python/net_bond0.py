#/bin/python
#coding:utf-8

import os, shutil, subprocess, platform, tarfile, logging
import sys, getopt

sys_type = platform.dist()[0]
if (sys_type == "Ubuntu" or sys_type == "SuSE"):
        ver = int(platform.dist()[1][0] + platform.dist()[1][1])
elif (sys_type == "centos" or sys_type == "redhat"):
        ver = int(platform.dist()[1][0])

# Bond0配置，暂提供mode4，如果是on需配置interface，bond0的ip,gateway,netmask,bond_dns,注意: 目前脚本不配置ubuntu18.04及以上版本的bond0
#mode = "4"
#interface = "em1 em2"
#ip = "192.168.0.10"
#gateway = "192.168.0.1"
#netmask = "255.255.255.0"
#bond_dns = "192.168.0.1"

# 初始化logging
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("/var/log/bond0.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console)

argv = sys.argv[1:]

if len(argv) < 6:
    print "please input args!"
    exit()
try:
    options, args = getopt.getopt(argv, "hp:i:", ["help","bond=", "via=", "ip=", "gw=", "mode=", "dns="])
except getopt.GetoptError:
    sys.exit()

help = "please input correct information\n--ip               ip address for example:192.168.1.23/24 the '24' is netmask\n--via               two interfaces\n--gw               gateway\n--mode               bond mode\n--dns               bond0 dns"
for option, value in options:
    if option in ("--help"):
        logger.info(help)
        exit()
    if option in ("--bond"):
        bond_name = "{0}".format(value)
    if option in ("--via"):
        inters = "{0}".format(value)
    if option in ("--ip"):
        ip_mask = "{0}".format(value)
    if option in ("--gw"):
        gateway = "{0}".format(value)
    if option in ("--mode"):
        mode = "{0}".format(value)
    if option in ("--dns"):
        bond_dns = "{0}".format(value)
logger.info("error args: {0}".format(args))

ip = ip_mask.split("/")[0]
if ip.split(".")[-1] == "1" or ip.split(".")[-1] == "254":
    logger.info("-------------------IP ERROR-------------------")
    logger.info("-------------------This IP is maybe GATEWAY-----------------")
    exit()

if mode != "4" and mode != "1" and mode != "6":
    logger.info("-------------------MODE ERROR-------------------")
    exit()

prefix = ip_mask.split("/")[1]
if prefix == "24":
    netmask = "255.255.255.0"
if prefix == "16":
    netmask = "255.255.0.0"
if prefix == "25":
    netmask = "255.255.255.128"
if prefix == "8":
    netmask = "255.0.0.0"


def bond0_config():
    inter = inters.split()
    if (sys_type == "centos" or sys_type == "redhat"):
        data = "MASTER=%s\nSLAVE=yes" %(bond_name)
        if mode == "4":
            if gateway:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"xmit_hash_policy=layer2+3 mode=%s mimmon=80\"\nIPADDR=%s\nPREFIX=%s\nGATEWAY=%s\nDNS1=%s" %(bond_name, mode, ip, prefix, gateway, bond_dns)
            else:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"xmit_hash_policy=layer2+3 mode=%s mimmon=80\"\nIPADDR=%s\nPREFIX=%s" %(bond_name, mode, ip, prefix)
        if mode == "1":
            if gateway:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"mode=%s\"\nIPADDR=%s\nPREFIX=%s\nGATEWAY=%s\nDNS1=%s" %(bond_name, mode, ip, prefix, gateway, bond_dns)
            else:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"mode=%s\"\nIPADDR=%s\nPREFIX=%s\n" %(bond_name, mode, ip, prefix)
        if mode == "6":
            if gateway:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"miimon=100 mode=%s\"\nIPADDR=%s\nPREFIX=%s\nGATEWAY=%s\nDNS1=%s" %(bond_name, mode, ip, prefix, gateway, bond_dns)
            else:
                net = "TYPE=Bond\nDEVICE=%s\nBOOTPROTO=none\nONBOOT=yes\nBONDING_MASTER=yes\nBONDING_OPTS=\"miimon=100 mode=%s\"\nIPADDR=%s\nPREFIX=%s" %(bond_name, mode, ip, prefix)
        for i in inter:
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
        bond_path = "/etc/sysconfig/network-scripts/ifcfg-%s" %(bond_name)
        with open(bond_path, 'w') as fp:
            fp.write(net)
        
        for i in inter:
            logger.info(os.popen("cat /etc/sysconfig/network-scripts/ifcfg-%s" %(i)).read().strip())
            logger.info("---------------------------------------------------------------")
        logger.info(os.popen("cat /etc/sysconfig/network-scripts/ifcfg-bond0").read().strip())

    elif (sys_type == "Ubuntu" and ver <= 16):
        net = "auto bond0\niface bond0 inet static\naddress %s\ngateway %s\nnetmask %s\nbond-salves all\nbond-mode 802.3ad\nbond-miimon 100\nup ifenslave bond0 %s\ndown ifenslave -d bond0 %s" %(ip, gateway, netmask, inters, inters)
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
    if (sys_type == "centos" and ver>= 7):
        logger.info(os.popen("systemctl restart network 2>&1").read().strip())
    if (sys_type == "Ubuntu"):
        logger.info(os.popen("/etc/init.d/networking restart 2>&1").read().strip())
    else:
        logger.info(os.popen("service network restart 2>&1").read().strip())

    subprocess.call(["sleep 3"], shell=True)
    bond_sts = os.popen("cat /proc/net/bonding/%s" %(bond_name)).read().strip()
    if not bond_sts:
        logger.info("------------------------The BOND config error----------------------")
        exit()
    b_mode = os.popen("cat /proc/net/bonding/%s |grep 'Bonding Mode'" %(bond_name)).read().strip()
    if mode == "4":
        if "802.3ad" not in b_mode:
            logger.info("------------------------The bond mode config error----------------------")
            exit()
    elif mode == "1":
        if "Active-backup policy" not in b_mode:
            logger.info("------------------------The bond mode config error----------------------")
            exit()
    
    if "down" in os.popen("cat /proc/net/bonding/%s |grep 'MII Status'| awk '{print $3}'" %(bond_name)).read().strip():
        logger.info("------------------------There is a interface down,  error----------------------")
        exit()
    
    for i in inter:
        logger.info("------------------This is " + i + os.popen("ethtool %s | grep Speed" %(i)).read().strip() + "------------------")
    subprocess.call(["sleep 3"], shell=True)
    logger.info("------------------This is %s " %(bond_name) + os.popen("ethtool %s | grep Speed" %(bond_name)).read().strip() + "-------------------")

bond0_config()
