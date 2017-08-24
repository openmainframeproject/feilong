# Copyright 2017 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from zvmsdk import config
from zvmsdk import database
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG

_XCAT_CLIENT = None
_SMUT_CLIENT = None


def get_xcatclient():
    global _XCAT_CLIENT
    if _XCAT_CLIENT is None:
        try:
            _XCAT_CLIENT = zvmutils.import_object(
                'zvmsdk.xcatclient.XCATClient')
        except ImportError:
            LOG.error("Unable to get zvmclient")
            raise ImportError
    return _XCAT_CLIENT


def get_smutclient():
    global _SMUT_CLIENT
    if _SMUT_CLIENT is None:
        try:
            _SMUT_CLIENT = zvmutils.import_object(
                'zvmsdk.smutclient.SMUTClient')
        except ImportError:
            LOG.error("Unable to get zvmclient")
            raise ImportError
    return _SMUT_CLIENT


def get_zvmclient():
    if CONF.zvm.client_type == 'xcat':
        return get_xcatclient()
    elif CONF.zvm.client_type == 'smut':
        return get_smutclient()
    else:
        # TODO: raise Exception
        pass


class ZVMClient(object):

    def __init__(self):
        self._pathutils = zvmutils.PathUtils()
        self._DbOperator = database.get_DbOperator()

    def guest_start(self, userid):
        pass

    def guest_stop(self, userid):
        pass

    def get_power_state(self, userid):
        pass

    def image_import(self, image_name, url, image_meta, remote_host=None):
        pass

    def image_query(self, imagekeyword=None):
        pass

    def image_delete(self, image_name):
        pass

    def get_host_info(self):
        pass

    def get_diskpool_info(self, pool):
        pass

    def virtual_network_vswitch_query_iuo_stats(self):
        pass

    def get_vm_list(self):
        pass

    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='IP',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):
        pass

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False):
        pass

    def create_nic(self, userid, vdev=None, nic_id=None,
                   mac_addr=None, ip_addr=None, active=False):
        pass

    def delete_nic(self, userid, vdev, active=False):
        pass

    def delete_vswitch(self, switch_name, persist=True):
        pass

    def get_vm_nic_vswitch_info(self, vm_id):
        pass

    def get_vswitch_list(self):
        pass

    def grant_user_to_vswitch(self, vswitch_name, userid):
        pass

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        pass

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        pass

    def set_vswitch(self, switch_name, **kwargs):
        pass

    def uncouple_nic_from_vswitch(self, userid, nic_vdev,
                                  active=False):
        pass

    def get_guest_connection_status(self, userid):
        pass

    def guest_deploy(self, node, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        pass

    def process_additional_minidisks(self, userid, disk_info):
        pass

    def get_user_direct(self, userid):
        pass

    def create_vm(self, userid, cpu, memory, disk_list, profile):
        pass

    def delete_vm(self, userid):
        pass

    def _generate_vdev(self, base, offset):
        """Generate virtual device number based on base vdev
        :param base: base virtual device number, string of 4 bit hex.
        :param offset: offset to base, integer.
        """
        vdev = hex(int(base, 16) + offset)[2:]
        return vdev.rjust(4, '0')

    def generate_disk_vdev(self, start_vdev=None, offset=0):
        """Generate virtual device number for disks
        :param offset: offset of user_root_vdev.
        :return: virtual device number, string of 4 bit hex.
        """
        if not start_vdev:
            start_vdev = CONF.zvm.user_root_vdev
        vdev = self._generate_vdev(start_vdev, offset)
        if offset >= 0 and offset < 254:
            return vdev
        else:
            msg = "Invalid virtual device number for disk:%s" % vdev
            LOG.error(msg)
            raise

    def add_mdisks(self, userid, disk_list, start_vdev=None):
        """Add disks for the userid

        :disks: A list dictionary to describe disk info, for example:
                disk: [{'size': '1g',
                       'format': 'ext3',
                       'disk_pool': 'ECKD:eckdpool1'}]

        """

        for idx, disk in enumerate(disk_list):
            vdev = self.generate_disk_vdev(start_vdev=start_vdev, offset=idx)
            self._add_mdisk(userid, disk, vdev)

    def authorize_iucv_client(self, guest_userid, client_userid):
        pass

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        pass

    def get_image_performance_info(self, userid):
        """Get CPU and memory usage information.

        :userid: the zvm userid to be queried
        """
        pi_dict = self.image_performance_query([userid])
        return pi_dict.get(userid.upper(), None)

    def _parse_vswitch_inspect_data(self, rd_list):
        """ Parse the Virtual_Network_Vswitch_Query_IUO_Stats data to get
        inspect data. This is an internal function shared by both smut and
        xcat client.
        """
        def _parse_value(data_list, idx, keyword, offset):
            return idx + offset, data_list[idx].rpartition(keyword)[2].strip()

        vsw_dict = {}
        with zvmutils.expect_invalid_resp_data():
            # vswitch count
            idx = 0
            idx, vsw_count = _parse_value(rd_list, idx, 'vswitch count:', 2)
            vsw_dict['vswitch_count'] = int(vsw_count)

            # deal with each vswitch data
            vsw_dict['vswitches'] = []
            for i in range(vsw_dict['vswitch_count']):
                vsw_data = {}
                # skip vswitch number
                idx += 1
                # vswitch name
                idx, vsw_name = _parse_value(rd_list, idx, 'vswitch name:', 1)
                vsw_data['vswitch_name'] = vsw_name
                # uplink count
                idx, up_count = _parse_value(rd_list, idx, 'uplink count:', 1)
                # skip uplink data
                idx += int(up_count) * 9
                # skip bridge data
                idx += 8
                # nic count
                vsw_data['nics'] = []
                idx, nic_count = _parse_value(rd_list, idx, 'nic count:', 1)
                nic_count = int(nic_count)
                for j in range(nic_count):
                    nic_data = {}
                    idx, nic_id = _parse_value(rd_list, idx, 'nic_id:', 1)
                    userid, toss, vdev = nic_id.partition(' ')
                    nic_data['userid'] = userid
                    nic_data['vdev'] = vdev
                    idx, nic_data['nic_fr_rx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_rx:', 1
                                                              )
                    idx, nic_data['nic_fr_rx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_rx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_err:', 1
                                                            )
                    idx, nic_data['nic_fr_tx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_tx:', 1
                                                              )
                    idx, nic_data['nic_fr_tx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_tx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_err:', 1
                                                            )
                    idx, nic_data['nic_rx'] = _parse_value(rd_list, idx,
                                                           'nic_rx:', 1
                                                           )
                    idx, nic_data['nic_tx'] = _parse_value(rd_list, idx,
                                                           'nic_tx:', 1
                                                           )
                    vsw_data['nics'].append(nic_data)
                # vlan count
                idx, vlan_count = _parse_value(rd_list, idx, 'vlan count:', 1)
                # skip vlan data
                idx += int(vlan_count) * 3
                # skip the blank line
                idx += 1

                vsw_dict['vswitches'].append(vsw_data)

        return vsw_dict
