#!/bin/bash

set -e
if [ "migrate" = "rollback" ]; then
    exit 0
fi

# 获取eth0 IP
IP=$(/sbin/ifconfig eth0 | grep inet | grep -v 127.0.0.1 | grep -v inet6 | awk '{print $2}' | tr -d "addr:")
ENDPOINT="https://$IP:2379"

echo "ENDPOINT:  "$ENDPOINT
set +e
# 查询etcd endpoints status，判断该etcd是否为leader
ETCDCTL_API=3 /usr/bin/etcdctl --cacert=/var/lib/etcd/cert/ca.pem --cert=/var/lib/etcd/cert/etcd-server.pem --key=/var/lib/etcd/cert/etcd-server-key.pem --endpoints=$ENDPOINT endpoint status | grep true
if [ $? -ne 0 ]; then
    echo "不为etcd leader所在机器，退出。"
    exit 0
fi
set -e

yum install curl wget -y

if [ ! -f "/tmp/ossutil64" ]; then
    # wget ossutil，保存到/tmp/目录下
    wget -c -t 10 -O /tmp/ossutil64 https://oos-public-cn-north-2-gov-1.oss-cn-north-2-gov-1-internal.aliyuncs.com/x64/ossutil64
    if [ $? -ne 0 ]; then
        echo "下载ossutil工具，退出。"
        exit 1
    fi
    chmod +x /tmp/ossutil64
fi

if [ ! -f "/tmp/modify-prefix" ]; then
    echo "下载modify-prefix"
    wget -c -t 10 -O /tmp/modify-prefix https://aliacs-k8s-cn-north-2-gov-1.oss-cn-north-2-gov-1-internal.aliyuncs.com/public/pkg/etcd/modify-prefix
    if [ $? -ne 0 ]; then
        echo "下载修改prefix工具出错，退出。"
        exit 1
    fi
    chmod +x /tmp/modify-prefix
fi

# 为leader则做snapshot，将snapshot存在在/tmp/
TIMESTAMP=$(date "+%Y%m%d%H%M%S")
mkdir -p /tmp/etcdsnap
SNAP_NAME=etcd_$TIMESTAMP
echo "开始备份，备份名为/tmp/"$SNAP_NAME
DestPrefix="/"cac207bc56f584188914b6e5716ff9512
ETCDCTL_API=3 /usr/bin/etcdctl --cacert=/var/lib/etcd/cert/ca.pem --cert=/var/lib/etcd/cert/etcd-server.pem --key=/var/lib/etcd/cert/etcd-server-key.pem --endpoints=$ENDPOINT snapshot save /tmp/etcdsnap/$SNAP_NAME
/tmp/modify-prefix modify-prefix --db=/tmp/etcdsnap/$SNAP_NAME --src-prefix=/registry --dest-prefix=$DestPrefix --bucket=key
if [ $? -ne 0 ]; then
    echo "修改prefix出错，退出。"
    exit 1
fi

# 获取oss 相关地址，上传
ROLE=$(curl -s 100.100.100.200/latest/meta-data/ram/security-credentials/)
ROLERES=$(curl -s 100.100.100.200/latest/meta-data/ram/security-credentials/$ROLE)
AccessKeyId=$(echo $ROLERES | python -c "import sys, json; print json.load(sys.stdin)['AccessKeyId']")
AccessKeySecret=$(echo $ROLERES | python -c "import sys, json; print json.load(sys.stdin)['AccessKeySecret']")
SecurityToken=$(echo $ROLERES | python -c "import sys, json; print json.load(sys.stdin)['SecurityToken']")
# put object to oss
/tmp/ossutil64 -t $SecurityToken -i $AccessKeyId -k $AccessKeySecret -e oss-cn-north-2-gov-1-internal.aliyuncs.com cp /tmp/etcdsnap/$SNAP_NAME oss://xingshui-k8s/$SNAP_NAME

# sign
oss_url=$(/tmp/ossutil64 -t $SecurityToken -i $AccessKeyId -k $AccessKeySecret -e oss-cn-north-2-gov-1-internal.aliyuncs.com sign --timeout 2400 oss://xingshui-k8s/$SNAP_NAME | grep -v "elapsed" | tr -d '\n')
sakey=$(cat /etc/kubernetes/pki/sa.key | base64 -w0)
sapub=$(cat /etc/kubernetes/pki/sa.pub | base64 -w0)
frontcrt=$(cat /etc/kubernetes/pki/front-proxy-ca.crt | base64 -w0)
frontkey=$(cat /etc/kubernetes/pki/front-proxy-ca.key | base64 -w0)
echo "{\"sakey\":\"$sakey\",\"sapub\":\"$sapub\",\"frontcrt\":\"$frontcrt\",\"frontkey\":\"$frontkey\",\"oss_url\":\"$oss_url\"}" >/tmp/etcdsnap/sign