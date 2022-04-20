# -*- coding: UTF-8 -*-
# !/usr/bin/env python
import commands
import os
import time
from operator import methodcaller

repo_path = "/root/repo"
tag_file = "/root/install_tag"
base_url = "http://172.16.0.2/index/resources"

sources = ['hfa-hadoop_check_centos7-22.sh', 'intel.tgz', 'jdk1.8.0_121.tar.gz', 'cm5.5.0.tar.gz', 'parcels.tar.gz',
           'hadoop.tar.gz', 'sentry-hdfs-1.8.0.jar', 'avro-1.7.6-kf-cdh5.2.0.jar', 'hosts', 'hostname.ip']

steps = ["download_sources", "mount_disk_cat_fstab", "mount_disk_mount", "modify_hostname", "sys_init", "mkl",
         "install_jdk", "install_cm", "parcels", "hadoop", "distribute_sentry", "distribute_avro", "check_jps",
         "restart_cm_agent", "ln"]


class HfCentOSUpdate:
    def __init__(self):
        pass

    @staticmethod
    def print_info(info):
        print('----------------------- ' + info + ' -------------------------P')
        echo = "echo \"---------------------- " + info + " ----------------------E\""
        status, output = commands.getstatusoutput(echo)
        print('----------------------- ' + info + ' -------------------------')

    def write_tag_file_and_exit(self, tag):
        self.print_info(tag + " [FAILURE]")
        echo = "echo " + tag + " > " + tag_file
        status, output = commands.getstatusoutput(echo)
        retries = 3
        while status != 0 and retries > 0:
            retries = retries - 1  # 如果tag写入不成功，则尝试3次
            status, output = commands.getstatusoutput(echo)
        os._exit(0)

    def check_exist(self, path):
        if path not in sources:
            self.print_info("file is incorrect, pls check")
            return False
        else:
            return True

    def download_sources(self):
        print('--------------------------------------------------------------------------------')
        print('--------------------------------begin downloading-------------------------------')
        if not os.path.exists(repo_path):
            os.popen('mkdir -p ' + repo_path)
        for i in sources:
            self.print_info("begin download " + i)
            status, output = commands.getstatusoutput("wget -N -P " + repo_path + " " + base_url + "/" + i)
            if status == 0:
                self.print_info(i + " download [SUCCESS]")
            else:
                self.write_tag_file_and_exit("download_sources")
                self.write_tag_file_and_exit("all sources have downloaded")
                self.write_tag_file_and_exit("---------------------------")
        print('--------------------------------download [SUCCESS]------------------------------')
        print('--------------------------------------------------------------------------------')

    def mount_disk_cat_fstab(self):
        self.print_info("mount_disk_cat_fstab")
        mkdir = "mkdir -p /disk1 /disk2 /disk3 /disk4  /disk5 /disk6 /disk7 /disk8 /disk9 /disk10 /disk11 /disk12"
        status, output = commands.getstatusoutput(mkdir)
        partition = "/dev/sdb1       /disk1  ext4    defaults        0 0 \n" \
                    "/dev/sdc1       /disk2  ext4    defaults        0 0 \n" \
                    "/dev/sdd1       /disk3  ext4    defaults        0 0 \n" \
                    "/dev/sde1       /disk4  ext4    defaults        0 0 \n" \
                    "/dev/sdf1       /disk5  ext4    defaults        0 0 \n" \
                    "/dev/sdg1       /disk6  ext4    defaults        0 0 \n" \
                    "/dev/sdh1       /disk7  ext4    defaults        0 0 \n" \
                    "/dev/sdi1       /disk8  ext4    defaults        0 0 \n" \
                    "/dev/sdj1       /disk9  ext4    defaults        0 0 \n" \
                    "/dev/sdk1       /disk10  ext4    defaults        0 0 \n" \
                    "/dev/sdl1       /disk11  ext4    defaults        0 0 \n" \
                    "/dev/sdm1       /disk12  ext4    defaults        0 0 \n"
        f = open('/etc/fstab', 'a')
        data = f.write(partition)
        print('data-->' + str(data))
        self.print_info("mount_disk_cat_fstab")

    def mount_disk_mount(self):
        self.print_info("mount_disk_mount")
        mount = "mount -a"
        status, output = commands.getstatusoutput(mount)
        if not status == 0:
            self.write_tag_file_and_exit("mount_disk_mount")
        self.print_info("mount_disk_mount")

    def modify_hostname(self):
        self.print_info("modify_hostname")
        cp_etc_hosts = "\\cp " + repo_path + "/hosts" + " /etc"
        status, output = commands.getstatusoutput(cp_etc_hosts)
        status, output = commands.getstatusoutput("ifconfig | grep 172.16 | awk '{print $2}'")
        print('status,output=[' + str(status) + ", " + output + ']')
        if status == 0 and output != '':
            hostname_ip = repo_path + "/" + "hostname.ip"
            if not os.path.exists(hostname_ip):
                print (hostname_ip + " is not found.")
                self.write_tag_file_and_exit("modify_hostname")
            cat_cmd = "cat " + hostname_ip + " | grep " + output + " | awk '{print $2}'"
            status, output = commands.getstatusoutput(cat_cmd)  # //TODO 绝对路径
            hostname = output
            print('hostname----------->' + hostname)
            if hostname == '':
                self.write_tag_file_and_exit('modify_hostname')
            status, output = commands.getstatusoutput("echo " + hostname + " > /etc/hostname")
            if not status == 0:
                self.write_tag_file_and_exit('modify_hostname')
            status, output = commands.getstatusoutput("sysctl kernel.hostname=" + hostname)
            if not status == 0:
                self.write_tag_file_and_exit('modify_hostname')
            chk_status, chk_output = commands.getstatusoutput(
                "hostname")  # 对kernel.hostnamecheck；(?)对/etc/hostname是否需要check
            if chk_status == 0 and chk_output == hostname:
                self.print_info("modify_hostname [SUCCESS]")
            else:
                self.write_tag_file_and_exit('modify_hostname')
        else:
            self.write_tag_file_and_exit('modify_hostname')

    def modify_hostname0(self):
        self.print_info("modify_hostname")
        status, output = commands.getstatusoutput("ifconfig | grep 10.10 | awk '{print $2}'")
        print('status,output=[' + str(status) + ", " + output + ']')
        if status == 0 and output != '':
            status, output = commands.getstatusoutput(
                "cat hosts | grep " + output + " | awk '{print $2}'")  # //TODO 绝对路径
            hostname = output
            print('hostname----------->' + hostname)
            if hostname != '':
                status, output = commands.getstatusoutput("echo " + hostname + " > /etc/hostname")
                if status == 0:
                    status, output = commands.getstatusoutput("sysctl kernel.hostname=" + hostname)
                    if status == 0:  # hostname修改成功
                        chk_status, chk_output = commands.getstatusoutput(
                            "hostname")  # 对kernel.hostnamecheck；(?)对/etc/hostname是否需要check
                        if chk_status == 0 and chk_output == hostname:
                            self.print_info("modify_hostname [SUCCESS]")
        else:
            self.write_tag_file_and_exit("modify_hostname")

    def ping(self, ip):
        status, output = commands.getstatusoutput("ping -c 3 " + ip)
        if status != 0:
            self.print_info("PING " + ip + " FAILURE.")
            return False
            self.write_tag_file_and_exit('sys_init')
        else:
            print (status)
            self.print_info("PING " + ip + " SUCCESS.")
            return True

    def sys_init(self):
        self.print_info("system init")
        script_file = "hfa-hadoop_check_centos7-22.sh"
        if not self.check_exist(script_file):
            self.write_tag_file_and_exit("sys_init")
        src_path = repo_path + "/" + script_file
        dst_path = '/root'
        dst_path_file = dst_path + "/" + script_file
        copy_cmd = '\cp ' + src_path + " " + dst_path
        commands.getstatusoutput(copy_cmd)
        chmod = 'chmod u+x ' + dst_path_file
        commands.getstatusoutput(chmod)
        check_centos = "sh " + dst_path_file  # //TODO 合并
        commands.getstatusoutput(check_centos)
        commands.getstatusoutput("yum install lzo-devel -y")
        status, output = commands.getstatusoutput(check_centos)
        status, output = commands.getstatusoutput(
            "systemctl stop NetworkManager; systemctl disable NetworkManager; systemctl restart network; route -n")

        ip_list = ["10.10.10.247", "10.10.12.247", "10.10.11.247", "10.10.22.53",
                   "10.10.21.95", "172.21.21.20", "172.21.13.18", "172.21.12.22",
                   "172.21.14.22", "172.21.17.22", "172.21.191.1", "172.21.192.11",
                   "172.23.21.1", "172.21.212.1"
                   ]  # //TODO 从函数拿到公共变量区
        for ip in ip_list:
            if not self.ping(ip):
                self.write_tag_file_and_exit("sys_init")
        self.print_info("sys_init [SUCCESS]")

    def mkl(self):
        self.print_info("mkl")
        mkl_file = "intel.tgz"
        if not self.check_exist(mkl_file):
            self.write_tag_file_and_exit("mkl")

        mkdir = "mkdir -p /opt/hadoopsys/thirdparty"
        status, output = commands.getstatusoutput(mkdir)
        utar = "tar -zxvf " + repo_path + "/intel.tgz -C /opt/hadoopsys/thirdparty/"  # //has changed
        status, output = commands.getstatusoutput(utar)
        if not status == 0:
            self.write_tag_file_and_exit("mkl")
        self.print_info("mkl [SUCCESS]")

    def install_jdk(self):
        self.print_info("install jdk8")
        jdk_file = "jdk1.8.0_121.tar.gz"
        jdk_version = "jdk1.8.0_121"
        if not self.check_exist(jdk_file):
            self.write_tag_file_and_exit("install_jdk")
        jdk_file = repo_path + "/" + jdk_file
        tar_dst_path = '/usr/local/' + jdk_version
        sym_dst_path = '/usr/local/jdk8'
        if not os.path.exists(tar_dst_path):
            status, output = commands.getstatusoutput("tar -zxvf " + jdk_file + " -C /usr/local/")
            if status != 0:
                self.write_tag_file_and_exit("install_jdk")
        if os.path.exists(sym_dst_path):
            sym_rm = 'rm -rf ' + sym_dst_path
            print ('-------' + sym_rm)
            status, output = commands.getstatusoutput(sym_rm)
        status, output = commands.getstatusoutput(
            "chown -R root:root /usr/local/" + jdk_version + "; ln -s /usr/local/" + jdk_version + " /usr/local/jdk8")  # //has changed
        if status != 0:
            self.write_tag_file_and_exit("install_jdk")
        self.print_info("install_jdk [SUCCESS]")

    def install_cm(self):
        self.print_info("install_cm [BEGIN]")
        cm_version = "cm5.5.0"
        cm_file = cm_version + ".tar.gz"
        if not self.check_exist(cm_file):
            self.write_tag_file_and_exit("install_cm")
        cm_file = repo_path + "/" + cm_file
        status, output = commands.getstatusoutput("tar -zxvf " + cm_file + " -C /root")
        if status != 0:
            self.write_tag_file_and_exit("install_cm")
        status, output = commands.getstatusoutput(
            "cd /root/" + cm_version + "/RPMS/x86_64; yum localinstall -y --nogpgcheck *.rpm;sed -i \"s/^server_host\\=localhost/server_host\\=10.10.12.17/g\" /etc/cloudera-scm-agent/config.ini")
        print('status,output:[' + str(status) + ", " + output + "]")
        if status != 0:
            self.write_tag_file_and_exit("install_cm")
        self.print_info("install_cm [SUCCESS]")

    def parcels(self):
        self.print_info("parcels")

        parcels_target_dir = "/opt/cloudera"
        if not os.path.exists(parcels_target_dir):
            status, output = commands.getstatusoutput("mkdir -p " + parcels_target_dir)

        parcels = "parcels.tar.gz"
        hadoop = "hadoop.tar.gz"
        if not self.check_exist(parcels) and not self.check_exist(hadoop):
            self.write_tag_file_and_exit("parcels")
        parcels_src_path = repo_path + "/" + parcels
        cmd = "tar -zxvf " + parcels_src_path + " -C " + parcels_target_dir
        status, output = commands.getstatusoutput(cmd)

        if not status == 0:
            self.write_tag_file_and_exit("parcels")
        self.print_info("parcels [SUCCESS]")

    def hadoop(self):
        self.print_info("hadoop")

        parcels_target_dir = "/opt/cloudera"
        if not os.path.exists(parcels_target_dir):
            status, output = commands.getstatusoutput("mkdir -p " + parcels_target_dir)

        hadoop = "hadoop.tar.gz"
        hadoop_target_dir = "/etc"
        if not self.check_exist(hadoop):
            self.write_tag_file_and_exit("hadoop")
        hadoop_src_path = repo_path + "/" + hadoop
        cmd = "tar -zxvf " + hadoop_src_path + " -C " + hadoop_target_dir
        cmd = cmd + "; update-alternatives --install /etc/hadoop/conf hadoop-conf /etc/hadoop/conf.cloudera.yarn 50"
        status, output = commands.getstatusoutput(cmd)

        # check
        check_cmd = "ls -la /etc/alternatives/hadoop-conf | awk '{print $11}'"
        tag = "/etc/hadoop/conf.cloudera.yarn"
        status, output = commands.getstatusoutput(check_cmd)
        if not status == 0:
            self.write_tag_file_and_exit("hadoop")
        if tag != output:
            self.write_tag_file_and_exit("hadoop")
        self.print_info("hadoop [SUCCESS]")

    def distribute_sentry(self):
        self.print_info("distribute_sentry")
        sentry = "sentry-hdfs-1.8.0.jar"
        if not self.check_exist(sentry):
            self.write_tag_file_and_exit("parcels_and_hadoop")

        # config sentry
        src_path = repo_path + "/" + sentry
        dst_path = "/opt/cloudera/parcels/CDH/lib/hadoop-hdfs/"
        cmd = "\\cp " + src_path + " " + dst_path  # //TODO \cp
        status, output = commands.getstatusoutput(cmd)
        if not status == 0:
            self.write_tag_file_and_exit("distribute_sentry")

        self.print_info("distribute_sentry [SUCCESS]")

    def distribute_avro(self):
        self.print_info("distribute_avro")
        avro = "avro-1.7.6-kf-cdh5.2.0.jar"
        old_avro = "avro-1.7.6-cdh5.5.0.jar"
        if not self.check_exist(avro):
            self.write_tag_file_and_exit("parcels_and_hadoop")

        # config avro
        src_path = repo_path + "/" + avro
        dst_path = "/opt/cloudera/parcels/CDH/jars"
        cmd = "\\cp " + src_path + " " + dst_path  # //TODO \cp
        status, output = commands.getstatusoutput(cmd)
        if not status == 0:
            self.write_tag_file_and_exit("distribute_avro")
        old_avro_file = dst_path + "/" + old_avro
        if os.path.exists(old_avro_file):
            bak = 'mv ' + old_avro_file + ' ' + old_avro_file + ".bak"
            commands.getstatusoutput(bak)
        ln_cmd = "ln -s " + dst_path + '/' + avro + " " + dst_path + '/' + old_avro
        print('ln_cmd-->' + ln_cmd)
        status, output = commands.getstatusoutput(ln_cmd)
        if not status == 0:
            self.write_tag_file_and_exit("distribute_avro")
        self.print_info("distribute_avro [SUCCESS]")

    def check_jps(self):
        self.print_info("check_jps")
        # check_cmd = "which jps | grep jdk | wc -l"
        check_cmd = 'jps'
        status, output = commands.getstatusoutput(check_cmd)
        print('status,output:[' + str(status) + ", " + output + "]")
        #        if not status == 0:
        #            self.write_tag_file_and_exit("check_jps")
        if output == "command not found":
            #        if int(output) == 0:
            update = "update-alternatives --install /usr/bin/jps jps /usr/java/jdk1.7.0_67-cloudera/bin/jps 300"
            status, output = commands.getstatusoutput(update)
            if not status == 0:
                self.write_tag_file_and_exit("check_jps")
            # re-check
            status, output = commands.getstatusoutput(check_cmd)
            if not status == 0:
                self.write_tag_file_and_exit("check_jps")

            if int(output) == 0:
                self.write_tag_file_and_exit("check_jps")
        self.print_info("check_jps [SUCCESS]")

    def restart_cm_agent(self):
        self.print_info("restart_cm_agent")
        cmd = "systemctl start cloudera-scm-agent"
        status, output = commands.getstatusoutput(cmd)
        if not status == 0:
            self.write_tag_file_and_exit("restart_cm_agent")
        chk_cmd = "systemctl status cloudera-scm-agent  | grep 'Active: active' | wc -l"
        status, output = commands.getstatusoutput(chk_cmd)
        print('status,output:[' + str(status) + ", " + output + "]")
        if not status == 0:
            self.write_tag_file_and_exit("restart_cm_agent")
        if int(output) == 0:
            self.write_tag_file_and_exit("restart_cm_agent")
        self.print_info("restart_cm_agent [SUCCESS]")

    def ln(self):
        self.print_info("ln")
        if not os.path.exists('/opt/cloudera/parcels/Anaconda'):
            status, output = commands.getstatusoutput(
                "cd /opt/cloudera/parcels;"
                "ln -s /opt/cloudera/parcels/Anaconda-4.3.1 /opt/cloudera/parcels/Anaconda")
            if not status == 0:
                self.write_tag_file_and_exit("ln")
            if not os.path.exists('/opt/cloudera/parcels/CDH'):
                status, output = commands.getstatusoutput(
                    "cd /opt/cloudera/parcels;"
                    "ln -s /opt/cloudera/parcels/CDH-5.5.0-1.cdh5.5.0.p0.8 /opt/cloudera/parcels/CDH")
                if not status == 0:
                    self.write_tag_file_and_exit("ln")
        self.print_info('ln [SUCCESS]')

    def install_cmdb(self):
        self.print_info("install_cmdb")
        cmdb = "curl -s http://172.16.59.94:8666/scripts/cmdb.sh | bash"
        status, output = commands.getstatusoutput(cmdb)
        if not status == 0:
            self.write_tag_file_and_exit("install_cmdb")
        self.print_info("install_cmdb [SUCCESS]")


if __name__ == "__main__":
    work = HfCentOSUpdate()
    step_tag = ""
    if not os.path.exists(tag_file):  # 首次运行，断点(tag_file)文件不存在，从头开始执行
        for step in steps:
            methodcaller(step)(work)
    else:  # 前次中断退出，再次则从断点位置开始执行
        f = open(tag_file, 'r')
        step_tag = f.readlines()[-1].strip()  # 读取断点位置
        fr = steps.index(step_tag)
        to = len(steps)
        for step in steps[fr: to]:  # 从断点位置开始执行
            methodcaller(step)(work)
