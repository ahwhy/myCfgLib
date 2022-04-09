#/bin/python
#coding:utf-8

import os, shutil, subprocess, platform, tarfile, logging
sys = platform.dist()[0]
if (sys == "Ubuntu" or sys == "SuSE"):
        ver = int(platform.dist()[1][0] + platform.dist()[1][1])
elif (sys == "centos" or sys == "redhat"):
        ver = int(platform.dist()[1][0])

#普通用户名，自定义
common_user = "demo"
common_password = "demo1234"

#选择是否配置umask，on or off?
umask = "off"

#源
url = 'http://172.16.xx.xx/Soft' 

#初始化logging
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("/var/log/security_reinforce.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console)

#查看系统版本及内核版本
logger.info(os.popen("uname -a").read())
logger.info(os.popen("cat /etc/*release").read())

def services_minimum():
    #关闭samba服务
    logger.info("---------------current listenning ports-----------------")
    logger.info(os.popen("netstat -pantul |grep LISTEN").read())
    logger.info(os.popen("systemctl list-unit-files |grep enabled").read())
    if (sys == "Ubuntu"):
        logger.info(os.popen("service nmbd stop 2>&1 && service smbd stop 2>&1").read())
        logger.info(os.popen("apt-get remove samba -y 2>&1").read())
    else:
        logger.info(os.popen("systemctl stop postfix 2>&1").read())
        logger.info(os.popen("service postfix stop 2>&1").read())
        logger.info(os.popen("yum remove postfix -y 2>&1").read())
    
    #添加普通用户
    logger.info(os.popen("useradd -m -s /bin/bash %s 2>&1" %(common_user)).read().strip())
    logger.info(os.popen("echo '%s:%s'|chpasswd 2>&1" %(common_user,common_password)).read().strip())
    with open("/etc/sudoers", "r") as s:
            c = s.read()
            if common_user not in c:
                subprocess.call(["echo '%s    ALL=(ALL:ALL) ALL' >> /etc/sudoers" %(common_user)], shell=True)

def base_upgrade():
    os.chdir('/root')
    if sys == "Ubuntu":
        logger.info(os.popen("apt-get install gcc g++ make wget -y 2>&1").read())
    else:
        logger.info(os.popen("yum install gcc gcc-c++ make wget -y 2>&1").read())
    
    if not os.path.exists("openssh-7.4p1.tar.gz"):
        logger.info(os.popen("wget %s/openssh-7.4p1.tar.gz 2>&1" %(url)).read().strip())
    if not os.path.exists("zlib-1.2.11.tar.gz"):
        logger.info(os.popen("wget %s/zlib-1.2.11.tar.gz 2>&1" %(url)).read().strip())
    if not os.path.exists("openssl-1.0.2k.tar.gz"):
        logger.info(os.popen("wget %s/openssl-1.0.2k.tar.gz 2>&1" %(url)).read().strip())

    tar = tarfile.open("openssh-7.4p1.tar.gz")
    tar.extractall()
    tar.close()
    tar = tarfile.open("zlib-1.2.11.tar.gz")
    tar.extractall()
    tar.close()
    tar = tarfile.open("openssl-1.0.2k.tar.gz")
    tar.extractall()
    tar.close()

    #安装zlib
    if not os.path.exists("/usr/local/zlib"):
        os.chdir("/root/zlib-1.2.11")
        logger.info(os.popen("./configure 2>&1").read().strip())
        logger.info(os.popen("make 2>&1 && make install 2>&1").read().strip())
        with open("/etc/ld.so.conf", "r") as f:
            con0 = f.read()
            if "/usr/local/lib" not in con0:
                logger.info(os.popen("echo '/usr/local/lib' >> /etc/ld.so.conf").read().strip())
                logger.info(os.popen("ldconfig").read().strip())
    
    #安装openssl
    if not os.path.exists("/usr/local/ssl"):
        os.chdir("/root/openssl-1.0.2k")
        logger.info(os.popen("./config shared -fPIC 2>&1").read().strip())
        logger.info(os.popen("make  2>&1 && make install 2>&1").read().strip())
        with open("/etc/ld.so.conf", "r") as r:
            con1 = r.read()
            if "/usr/local/lib/ssl" not in con1:
                subprocess.call(["echo '/usr/local/ssl/lib' >> /etc/ld.so.conf"], shell=True)
                subprocess.call(["ldconfig"], shell=True)
                subprocess.call(["rm -f /usr/bin/openssl"], shell=True)
                subprocess.call(["ln -s /usr/local/ssl/bin/openssl /usr/bin/openssl"], shell=True)
                a = os.popen("openssl version")
                logger.info("---------------The openssl version is " + a.read().strip() + "-----------------")
    
def ubuntu_openssh_upgrade():
    #openssh升级
    base_upgrade()
    #安装telnet服务，脚本执行后若ssh升级失败，可用telnet连接服务器
    logger.info(os.popen("apt-get install -y openbsd-inetd telnetd screen auditd 2>&1").read().strip())
    logger.info(os.popen("service openbsd-inetd start 2>&1").read().strip())

    os.chdir("/root/openssh-7.4p1")
    logger.info(os.popen("apt-get install libpam0g-dev -y 2>&1").read().strip())
    subprocess.call(["rm -rf /etc/ssh /usr/bin/scp /usr/bin/sftp /usr/bin/ssh* /usr/sbin/sshd /lib/x86_64-linux-gnu/libssl.so.1.0.0 /lib/x86_64-linux-gnu/libcrypto.so.1.0.0"], shell=True)
    subprocess.call(["cp /usr/local/ssl/lib/libssl.so.1.0.0 /lib/x86_64-linux-gnu/"], shell=True)
    subprocess.call(["cp /usr/local/ssl/lib/libcrypto.so.1.0.0 /lib/x86_64-linux-gnu/"], shell=True)

    logger.info(os.popen("./configure --prefix=/usr/local/ssh --sysconfdir=/etc/ssh --with-md5-passwords --with-pam --with-ssl-dir=/usr/local/ssl --mandir=/usr/share/man --with-zlib=/usr/local/zlib --with-privsep-path=/var/empty --with-privsep-user=sshd --with-ssl-engine 2>&1").read().strip())
    logger.info(os.popen("make 2>&1 && make install 2>&1").read().strip())

    subprocess.call(["service sshd stop 2>&1"], shell=True)
    cmd = ["ln -s /usr/local/ssh/bin/ssh /usr/bin/ssh", "ln -s /usr/local/ssh/bin/scp /usr/bin/scp", "ln -s /usr/local/ssh/bin/sftp /usr/bin/sftp", "ln -s /usr/local/ssh/bin/ssh-add /usr/bin/ssh-add", "ln -s /usr/local/ssh/bin/ssh-agent /usr/bin/ssh-agent", "ln -s /usr/local/ssh/bin/ssh-keygen /usr/bin/ssh-keygen", "ln -s /usr/local/ssh/bin/ssh-keyscan /usr/bin/ssh-keyscan", "ln -s /usr/local/ssh/sbin/sshd /usr/sbin/sshd"]
    for i in cmd:
        subprocess.call(["%s" %(i)], shell=True)
    with open("/etc/ssh/sshd_config", "r") as l:
        con2 = l.read()
        if "PermitRootLogin yes" not in con2:
            subprocess.call(["sed -i '/PermitRootLogin\ prohibit/a\PermitRootLogin\ yes' /etc/ssh/sshd_config"], shell=True)
    logger.info(os.popen("service sshd start 2>&1"))
    logger.info(os.popen("service sshd status 2>&1"))
    b = os.popen("ssh -V 2>&1")
    logger.info("---------------The openssh version is " + b.read().strip() + "-----------------")
    #telnetd服务卸载
    ssh_status = logger.info(os.popen("ps aux|grep 'sshd -D' |grep -v grep").read().strip())
    if ssh_status:
        logger.info(os.popen("service openbsd-inetd stop 2>&1").read().strip())
        logger.info(os.popen("apt-get remove telnetd openbsd-inetd --purge -y 2>&1").read().strip())

def centos_openssh_upgrade():
    base_upgrade()
    logger.info(os.popen("yum install -y telnet-server audit 2>&1").read().strip())
    subprocess.call(["sed -i '/disable/c\\tdisable = no' /etc/xinetd.d/telnet"], shell=True)
    logger.info(os.popen("service xinetd restart 2>&1").read().strip())
    with open("/etc/securetty", "r") as f:
        con2 = f.read()
        if "pts/1" not in con2:
            subprocess.call(["echo 'pts/1\npts/2\npts/3' >> /etc/securetty"], shell=True)
    
    os.chdir("/root/openssh-7.4p1")
    logger.info(os.popen("yum install -y pam-devel screen 2>&1").read().strip())
    logger.info(os.popen("service sshd stop 2>&1").read().strip())
    logger.info(os.popen("rm -rf /etc/init.d/sshd /etc/ssh /usr/bin/scp /usr/bin/sftp /usr/bin/ssh* /usr/sbin/sshd").read().strip())
    logger.info(os.popen("./configure --prefix=/usr/local/ssh --sysconfdir=/etc/ssh --with-md5-passwords --with-pam --with-ssl-dir=/usr/local/ssl --mandir=/usr/share/man --with-zlib=/usr/local/zlib --with-privsep-path=/var/empty --with-privsep-user=sshd --with-ssl-engine 2>&1").read().strip())
    logger.info(os.popen("make 2>&1 && make install 2>&1").read().strip())
    
    cmd = ["ln -s /usr/local/ssh/bin/ssh /usr/bin/ssh", "ln -s /usr/local/ssh/bin/scp /usr/bin/scp", "ln -s /usr/local/ssh/bin/sftp /usr/bin/sftp", "ln -s /usr/local/ssh/bin/ssh-add /usr/bin/ssh-add", "ln -s /usr/local/ssh/bin/ssh-agent /usr/bin/ssh-agent", "ln -s /usr/local/ssh/bin/ssh-keygen /usr/bin/ssh-keygen", "ln -s /usr/local/ssh/bin/ssh-keyscan /usr/bin/ssh-keyscan", "ln -s /usr/local/ssh/sbin/sshd /usr/sbin/sshd", "touch /etc/ssh/ssh_host_key.pub", "cp contrib/redhat/sshd.init /etc/init.d/sshd", "chmod u+x /etc/init.d/sshd", "chkconfig --add sshd", "chkconfig sshd on"]
    for i in cmd:
        logger.info(os.popen("%s" %(i)).read().strip())
    with open("/etc/ssh/sshd_config", "r") as l:
        con2 = l.read()
        if "PermitRootLogin yes" not in con2:
            logger.info(os.popen("sed -i '/PermitRootLogin\ prohibit/a\PermitRootLogin\ yes' /etc/ssh/sshd_config").read().strip())
    logger.info(os.popen("/etc/init.d/sshd start 2>&1").read().strip())
    logger.info(os.popen("service sshd status 2>&1").read().strip())
    b = os.popen("ssh -V 2>&1").read().strip()
    logger.info("---------------The openssh version is " + b.read().strip() + "-----------------")
    #telnet服务卸载
    ssh_status = logger.info(os.popen("ps aux|grep 'sshd -D' |grep -v grep").read().strip())
    if ssh_status:
        logger.info(os.popen("service xinetd stop 2>&1").read().strip())
        logger.info(os.popen("rm -rf /etc/xinetd.d/telnet").read().strip())
        logger.info(os.popen("rpm -e -nodeps telnet-server 2>&1").read().strip())
    
def system_security():
    #禁用无用账号
    if not os.popen("awk -F: '($2==\"\")' /etc/passwd").read().strip():
        logger.info("---------------There is no empty account---------------")
    acc = os.popen("awk -F: '($3==0)' /etc/passwd |cut -d ':' -f 1").read().strip()
    for i in acc.split("\n"):
        if i != "root":
            subprocess.call(["passwd -l %s" %(i)], shell=True)
    if not os.popen("awk -F: '($3==0)' /etc/passwd | grep -v root").read().strip():
        logger.info("---------------There is no UID:0 account---------------")
    cmd = "adm lp shutdown uucp operator  games gopher"
    for i in cmd.split():
        os.popen("userdel %s" %(i))
    
    #账号异常锁定
    if sys == "Ubuntu":
        logger.info(os.popen("apt-get install libpam-cracklib -y 2>&1").read().strip())
    with open("/etc/pam.d/sshd", "r") as f:
        if "pam_tally2.so onerr=fail deny=6" not in f.read():
            subprocess.call(["echo 'auth required pam_tally2.so onerr=fail deny=6 unlock_time=300' >> /etc/pam.d/sshd"], shell=True)
    logger.info("---------------Account lock complete---------------")

    #口令周期策略
    subprocess.call(["sed -i '/^PASS_MAX_DAYS/cPASS_MAX_DAYS 90' /etc/login.defs"], shell=True)
    subprocess.call(["sed -i '/^PASS_MIN_DAYS/cPASS_MIN_DAYS 0' /etc/login.defs"], shell=True)
    #subprocess.call(["sed -i '/PASS_MIN_LEN/d' /etc/login.defs"], shell=True)
    #subprocess.call(["sed -i '/PASS_MIN_DAYS\ 0/aPASS_MIN_LEN 8' /etc/login.defs"], shell=True)
    subprocess.call(["sed -i '/^PASS_WARN_AGE/cPASS_WARN_AGE 7' /etc/login.defs"], shell=True)
    logger.info(os.popen("chage -M 90 -m 0 -W 7 %s" %(common_user)).read().strip())
    logger.info("---------------Password Cycle Strategy complete---------------")

    #口令复杂度要求
    if sys == "Ubuntu":
        subprocess.call(["sed -i '/pam_cracklib.so/cpassword required pam_cracklib.so enforce_for_root debug difok=3 minlen=8 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1 maxsequence=2 maxrepeat=2 gecoscheck' /etc/pam.d/common-password"], shell=True)
        subprocess.call(["sed -i '/try_first_pass retry=3/d' /etc/pam.d/common-password"], shell=True)
        subprocess.call(["sed -i '/enforce_for_root/apassword required pam_cracklib.so try_first_pass retry=3 type=' /etc/pam.d/common-password"], shell=True)
    else:
        content01 = "password required pam_cracklib.so enforce_for_root debug difok=3 minlen=8 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1 maxsequence=2 maxrepeat=2 gecoscheck"
        content02 =  "password required pam_cracklib.so try_first_pass retry=3 type="
        with open("/etc/pam.d/system-auth", "r") as l:
            cnt = l.read()
            if content01 not in cnt:
                subprocess.call(["echo '%s' >> /etc/pam.d/system-auth" %(content01)], shell=True)
            if content02 not in cnt:
                subprocess.call(["echo '%s' >> /etc/pam.d/system-auth" %(content02)], shell=True)
    logger.info("---------------Password Complexity Requirements complete---------------")

    #Bash历史命令
    #subprocess.call(["sed -i '/^HISTSIZE=/cHISTSIZE=5' /etc/profile"], shell=True)
    #subprocess.call(["source /etc/profile"], shell=True)
    #logger.info("---------------History bash command complete---------------")
    
    #登陆超时
    subprocess.call(["sed -i '/^TMOUT=/cTMOUT=900' /etc/profile"], shell=True)
    fp = open("/etc/profile", "r+")
    if "TMOUT=900" not in fp.read():
        subprocess.call(["echo 'TMOUT=900' >> /etc/profile"], shell=True)
    fp.close()
    subprocess.call(["source /etc/profile"], shell=True)
    logger.info("---------------Landing timeout complete---------------")
    
    #umask值配置
    if umask == "on":
        subprocess.call(["sed -i '/umask 022/c\ \ \ \ umask 027' /etc/profile"], shell=True)
        subprocess.call(["source /etc/profile"], shell=True)
    logger.info("---------------Umask config complete---------------")
    
    if sys == "Ubuntu":
        log_path = "/etc/rsyslog.d/50-default.conf"
    else:
        log_path = "/etc/rsyslog.conf"
    
    #开启日志服务器
    audit_rules = "-D\n-b 1024\n\n# Feel free to add below this line. See auditctl man page\n\n-a exit,always -F arch=b64 -S umask -S chown -S chmod\n-a exit,always -F arch=b64 -S unlink -S rmdir\n-a exit,always -F arch=b64 -S setrlimit\n\n-a exit,always -F arch=b64 -S setuid -S setreuid\n-a exit,always -F arch=b64 -S setgid -S setregid\n\n-a exit,always -F arch=b64 -S sethostname -S setdomainname\n-a exit,always -F arch=b64 -S adjtimex -S settimeofday\n\n-a exit,always -F arch=b64 -S mount -S _sysctl\n\n-w /etc/group -p wa\n-w /etc/passwd -p wa\n-w /etc/shadow -p wa\n-w /etc/sudoers -p wa\n\n-w /etc/ssh/sshd_config\n\n-w /etc/bashrc -p wa\n-w /etc/profile -p wa\n-w /etc/profile.d/\n-w /etc/aliases -p wa\n-w /etc/sysctl.conf -p wa\n\n-w /var/log/lastlog\n"

    f = open("/etc/audit/audit.rules", "w")
    f.write(audit_rules)
    f.close()
    logger.info(os.popen("service auditd restart 2>&1").read().strip())
    if os.popen("ps aux|grep audit|grep -v grep").read().strip():
        print "-----------------Audit log complete-------------------"
    
    #rsyslog 认证相关记录
    a = os.popen("cat %s |grep authpriv |grep -v messages |grep -v '#'" %(log_path)).read().strip()
    if not a:
        subprocess.call(["echo 'auth,authpriv.*                 /var/log/auth.log' >> /etc/rsyslog.d/50-default.conf"], shell=True)
    
    #rsyslog 日志设置
    b = os.popen("cat %s|grep messages |grep -v '#'" %(log_path)).read().strip()
    if not b:
        subprocess.call(["echo 'mail,news.none          -/var/log/messages' >> /etc/rsyslog.d/50-default.conf"], shell=True)
    c = os.popen("cat %s|grep cron |grep -v messages |grep -v '#'" %(log_path)).read().strip()
    if not c:
        subprocess.call(["echo 'cron.*                         /var/log/cron.log' >> /etc/rsyslog.d/50-default.conf"], shell=True)
    
    logger.info("---------------Rsyslog config complete---------------")
    logger.info("---------------System security complete---------------")

services_minimum()
sshver=os.popen("ssh -V 2>&1 |awk '{print $1}'|cut -d '_' -f 2").read().strip()
b_ver = int(sshver[0])
s_ver = int(sshver[2])
if not (b_ver >= 7 and s_ver >= 4):
    if (sys == "Ubuntu"):
        ubuntu_openssh_upgrade()
    else:
        centos_openssh_upgrade()
else:
    logger.info("--------------The openssh version is " + sshver + " ---------------")

system_security()
    
    
    
    
    