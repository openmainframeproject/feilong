
import logging


# <Logging>
LOG_FILE = 'zvmsdk.log'
LOG_LEVEL = logging.INFO

# The IP address that running python zvm sdk
my_ip = "192.168.0.1"

# <xCAT>
zvm_xcat_server = "192.168.0.1"
zvm_xcat_username = "admin"
zvm_xcat_password = "passowrd"
zvm_xcat_master = 'xcat'
zvm_zhcp_node = "zhcp"
zhcp = 'zhcp.ibm.com'

# <zVM>
zvm_host = "zvmhost1"
zvm_default_nic_vdev = '1000'
zvm_user_default_password = 'password'
zvm_diskpool = 'xcateckd'
zvm_user_root_vdev = '0100'
root_disk_units = '3338'
zvm_diskpool_type = 'ECKD'

# <instance>
instances_path = '/home/user/'
tempdir = '/home/user/tmp/'
zvm_reachable_timeout = 10000

# <network>
device = 'enccw0.0.1000'
broadcast_v4 = '192.168.0.2'
gateway_v4 = '192.168.0.1'
netmask_v4 = '255.255.255.0'
subchannels = '0.0.1000,0.0.1001,0.0.1002'
nic_name = 'a2ca1e29-88ac-44f3-85eb-cc1f637366ef'

# <Volume>
volume_mgr_userid = "volmgr"
volume_mgr_node = "volmgr"
volume_diskpool = "fbapool"
volume_filesystem = "ext3"
volume_vdev_start = '2000'
