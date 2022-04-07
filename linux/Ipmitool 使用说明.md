# ipmitoolʹ�ñʼ�

## ipmitool��װ����

```shell
# ��װ
$ yum install ipmitool

# ����ģ��
$ modprobe ipmi_poweroff
$ modprobe ipmi_watchdog
$ modprobe ipmi_msghandler  
$ modprobe ipmi_devintf  
$ modprobe ipmi_si 

# ��������
$ service ipmi start

# lanplus�ǲ���Զ�̻��������Ҫ�������ػ�������Ҫ��lanplus���� open 
# ����pxe����
$ ipmitool -I lanplus -H {ipmi} -U {user} -P {passwd} chassis bootdev pxe
# ��������
$ ipmitool -I lanplus -H {ipmi} -U {user} -P {passwd} chassis power cycle

# ��������bmc
# warm��ʾ��������cold��ʾӲ����
$ ipmitool mc reset <warm|cold>

# ��������
$ ipmitool lan set 1 ipsrc static;
$ ipmitool lan set 1 ipaddr 192.168.7.60;
$ ipmitool lan set 1 netmask 255.255.255.0; 
$ ipmitool lan set 1 defgw ipaddr 192.168.7.1;
$ ipmitool lan set 1 access on

��������bmc
$ ipmitool mc reset <warm|cold>  warm��ʾ��������cold��ʾӲ����

# ����
# �鿴��ǰipmi ��ַ
$ ipmitool lan print
# �鿴��־
$ ipmitool sel list
# �������־
$ ipmitool sel clear 
```


## ipmitool����

### 1��������״̬����
- �鿴���ػ�״̬ 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) power status`

- ����:
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) power on`

- �ػ�
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) power off`

- ���� 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) power reset`

### 2��IP��������
[ChannelNo] �ֶ��ǿ�ѡ�ģ�ChannoNoΪ1(Share Nic����)����8(BMC������������)���������������������������IPΪ��̬��Ȼ���ٽ����������ã�

- �鿴������Ϣ: 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) lan print [ChannelNo]`

- �޸�IPΪ��̬����DHCPģʽ: 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) lan set <ChannelNo> ipsrc <static/dhcp>`

- �޸�IP��ַ: 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) lan set <ChannelNo> ipaddr <IPAddress>`

- �޸���������: 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) lan set <ChannelNo> netmask <NetMask>`

- �޸�Ĭ������: 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) lan set <ChannelNo> defgw ipaddr <Ĭ������>`

### 3��Ӳ����Ϣ
- �鿴FRU��Ϣ 
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) fru list`

- ������BMC
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) mc reset <warm/cold>`

- �鿴SDR Sensor��Ϣ
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) sdr`

- �鿴Sensor��Ϣ
	- `ipmitool -H (BMC�Ĺ���IP��ַ) -I lanplus -U (BMC��¼�û���) -P (BMC ��¼�û���������) sensor list`


## ����

- [ipmitoolʹ���ֲ�](https://blog.csdn.net/xinqidian_xiao/article/details/80924897)

- �����̷�����IPMIĬ���û�
	- ����IPMIĬ���û���: root ����: calvin
	- ���IPMIĬ���û���: admin ����: admin     
	- �˳�IPMIĬ���û���: admin ����: admin     
	- H3C IPMIĬ���û���: admin ����: Password@_
	- ��ΪIPMIĬ���û���: root ����: Huawei12#$