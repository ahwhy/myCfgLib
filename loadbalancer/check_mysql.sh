#!/bin/bash

. /etc/profile
. ~/.bash_profile
. ~/.bashrc

mysql_host_master='10.0.0.103'
mysql_port=3306

# Alive MYSQL_STATE=0,Down MYSQL_STATE=1
MYSQL_STATE=2
W_LOG()
{
  STR=$1
  echo "$DT $STR" >> $LOG 2>&1
}

procCnt=`ps -ef|grep "check_mysql.sh" |wc -l`

if [ ${procCnt} -gt 4 ] ; then 
    echo "检查脚本已经在运行[procs=${procCnt}],此次执行自动取消."
    exit 1; 

else

# Common
DD=$(date +%Y%m%d)
DT=$(date +'%Y-%m-%d %H:%M:%S')
LOG=/usr/local/keepalived/log/mysqlcheck.$DD.log
    
    mysql_state()
    {
      /usr/bin/mysql -S /data/mysql/$2/run/mysql.sock -umonitor -p'xxxxxxxxxxx' -e "select user() from dual;" >> /dev/null 2>&1
      res=$?
      if [ $res -eq 0 ]
      then
        # mysql is alived
        MYSQL_STATE=0
        W_LOG "`date +'%Y-%m-%d %H:%M:%S'` $1 $2 MySQL is alived."
      else
        MYSQL_STATE=1
        W_LOG "`date +'%Y-%m-%d %H:%M:%S'` $1  $2 MySQL is down, keepalived will be stopped!!!"
      fi
    }
    
    # check master state
    mysql_state $mysql_host_master $mysql_port
    
    i=1
    while [[ $MYSQL_STATE -eq 1 ]] && [[ $i -lt 2 ]] 
    do
      sleep 1
      echo $i $MYSQL_STATE
      mysql_state $mysql_host_master $mysql_port
      let i++
    done
    
    
    if [[ $MYSQL_STATE -ne 0 ]]
    then
      pkill keepalived
      exit 1
    fi
    sleep 1
fi