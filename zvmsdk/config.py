
import logging


# <Logging>
LOG_FILE = 'zvmsdk.log'
LOG_LEVEL = logging.DEBUG

# The IP address that running python zvm sdk
my_ip = "9.115.112.124"

# <xCAT>
zvm_xcat_server = "9.60.29.166"
zvm_xcat_username = "admin"
zvm_xcat_password = "admin"
zvm_xcat_master = 'ZSHUOCTR'
zhcp = 'zhcp.ibm.com'

# <zVM>
zvm_host = "opnstk1"
zvm_default_nic_vdev = '1000'
zvm_user_default_password = 'dfltpass'
zvm_diskpool = 'xcateckd'
zvm_user_root_vdev = '0100'
root_disk_units = '3338'
zvm_diskpool_type = 'ECKD'

# <instance>
instances_path = '/home/shuozhang/'
tempdir = '/home/shuozhang/tmp/'
zvm_reachable_timeout = 10000

# <network>
device = 'enccw0.0.1000'
broadcast_v4 = '192.168.166.255'
gateway_v4 = '192.168.166.1'
netmask_v4 = '255.255.255.0'
subchannels = '0.0.1000,0.0.1001,0.0.1002'
nic_name = 'a2ca1e29-88ac-44f3-85eb-cc1f637366ef'