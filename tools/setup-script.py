'''
module -- setup-script

This script creates QCDFLT profile and volmgr image, volmgr xcat node.

'''
import sys

sys.path.append('..')
from zvmsdk.log import LOG
import zvmsdk.utils as zvmutils
import zvmsdk.config as CONF

# Create profile - QCDFLT
_xcat_url = zvmutils.get_xcat_url()
url = _xcat_url.lsdef_node(''.join(['/', CONF.zvm_host]))
info = zvmutils.xcat_request('GET', url)
for s in info['info'][0]:
    if s.__contains__('hcp='):
        zhcp_url = s.strip().rpartition('=')[2]
        zhcp_info = zhcp_url.split('.')[0]

cmd = ("echo \"PROFILE QCDFLT\nCOMMAND SET RUN ON\n"
       "COMMAND SET RUN ON\nCOMMAND SET VSWITCH XCATVSW2 GRANT &USERID\n"
       "COMMAND DEFINE NIC 1000 TYPE QDIO\nCOMMAND COUPLE 1000 TO SYSTEM XCATVSW2\n"
       "MACHINE ESA\nOPTION APPL CHPIDV ONE\nCONSOLE 0009 3215 T\n"
       "SPOOL 000C 2540 READER *\nSPOOL 000D 2540 PUNCH A\nSPOOL 000E 1403 A\" > /tmp/profile_tmp")
Ccmd = "smcli Profile_Create_DM -T qcdflt -f /tmp/profile_tmp"
zvmutils.xdsh(zhcp_info, 'rm -rf /tmp/profile_tmp')
zvmutils.xdsh(zhcp_info, cmd)
out = zvmutils.xdsh(zhcp_info, Ccmd)['data'][0][0]
print out

# Create userid - VOLMGR
cmd = "echo \"USER VOLMGR NOLOG 256M 256M G\" > /tmp/volmgr_userid"
Ccmd = "smcli Image_Create_DM -T volmgr -f /tmp/volmgr_userid"
zvmutils.xdsh(zhcp_info, 'rm -rf /tmp/volmgr_userid')
zvmutils.xdsh(zhcp_info, cmd)
out = zvmutils.xdsh(zhcp_info, Ccmd)['data'][0][0]
print out

# Create xcat node - volmgr
url = _xcat_url.lsdef_node('/volmgr')
try:
    zvmutils.xcat_request("GET", url)['info'][0]
    print "xcat node - volmgr already defined"
except zvmutils.ZVMException:
    print "Create xcat node - volmgr successfully"
    #LOG.info("Create xcat node - volmgr")
    url = _xcat_url.mkdef('/volmgr')
    body = ['userid=volmgr',
            'hcp=%s' % zhcp_url,
            'mgt=zvm',
            'groups=all']
    zvmutils.xcat_request("POST", url, body)
