#!/bin/bash

# 修改文件中对应配置

flag_cfg="/root/replace.conf"          # aaa bbb 将aaa修改为bbb
flag_cfg2="/root/file.conf"            # 修改文件路径
count=`cat $flag_cfg2|wc -l`
symbol='/'
i=1

cat $flag_cfg2|while read replace_file;do

echo "${i}${symbol}${count}----start replace  ${replace_file}  `date` ---------------"
 
cat $flag_cfg|while read replace_source replace_desc;do

  echo -e  "\033[36;41m $replace_source-->$replace_desc \033[0m" 

  echo `cat $replace_file|grep $replace_source`|sed  -e "s/$replace_source/[**$replace_source**]/g"    
   
  sed -i "s/$replace_source/$replace_desc/g" ${replace_file}      

  echo "--------->>"
   
  echo  `cat $replace_file|grep $replace_desc`|sed  -e "s/$replace_desc/[**$replace_desc**]/g"    
      
  done
   
  echo "${i}${symbol}${count}----end replace  $replace_file  `date` ---------------"
 
  let i++
 
done