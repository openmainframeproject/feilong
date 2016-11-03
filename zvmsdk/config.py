
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

zvm_host = "opnstk1"


# <instance>
os_version = 'rhel72'
os_type = 'rhel7.2'
instances_path = '/home/shuozhang/'
zvm_diskpool = 'xcateckd'
zvm_user_root_vdev = '0100'
root_disk_units = '3338'
zvm_diskpool_type = 'ECKD'
tempdir = '/install/instance'
zvm_default_nic_vdev = '1000'
zvm_user_default_password = 'dfltpass'
zvm_reachable_timeout = 10000
nic_name = 'a2ca1e29-88ac-44f3-85eb-cc1f637366ef'
image_id = 'afecb046-8acc-4b68-b535-00cf2ea944c2'
image_name = 'eckdrh72'