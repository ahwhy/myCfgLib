#/bin/bash

# 批量修改主机密码
# 192.168.50.118   root      
# 172.21.191.111   sunflower

for((i=1;i<=50;i++)) 
do
        IP=$(cat accounts.txt |sed -n $i'p' |awk '{print $1}')
        ACCOUNT=$(cat accounts.txt |sed -n $i'p'|awk '{print $2}')
        ssh root@$IP "echo '78gxtw23.ysq!@#'|passwd --stdin $ACCOUNT;exit"
done
