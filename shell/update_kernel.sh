#!/bin/bash

cd `dirname $0`

GRUB_CFG=/boot/grub2/grub.cfg

if rpm -q kernel-4.14.49 &> /dev/null; then
  exit
fi

cp $GRUB_CFG{,.bak}
rpm -ivh kernel-4.14.49-1.x86_64.rpm
# rpm -ivh kernel-devel-4.14.49-1.x86_64.rpm
sed -i 's/GRUB_DEFAULT=.*/GRUB_DEFAULT=0/g' /etc/default/grub
grub2-mkconfig -o $GRUB_CFG
mv /boot/grub2/grubenv{,.bak}