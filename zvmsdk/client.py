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


import datetime
import os
import re
import shutil
import tarfile
import xml.dom.minidom as Dom

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG

_XCAT_CLIENT = None


def get_zvmclient():
    if CONF.zvm.client_type == 'xcat':
        global _XCAT_CLIENT
        if _XCAT_CLIENT is None:
            return XCATClient()
        else:
            return _XCAT_CLIENT
    else:
        # TODO: raise Exception
        pass


class ZVMClient(object):

    def power_on(self, userid):
        pass

    def get_power_state(self, userid):
        pass

    def prepare_for_spawn(self, userid):
        """
        Every kind of client can do someting special for themselves before
        spawn.Because some keywords can not appear in ops modules, so we can
        put them in this interface.
        eg. xcat client can create xcat node here.
        """
        pass


class XCATClient(ZVMClient):

    def __init__(self):
        self._xcat_url = zvmutils.get_xcat_url()
        self._zhcp_info = {}
        self._zhcp_userid = None
        self._xcat_node_name = None
        self._pathutils = zvmutils.PathUtils()

    def _power_state(self, userid, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + userid)
        with zvmutils.expect_invalid_xcat_node_and_reraise(userid):
            return zvmutils.xcat_request(method, url, body)

    def guest_start(self, userid):
        """"Power on VM."""
        try:
            self._power_state(userid, "PUT", "on")
        except exception.ZVMXCATInternalError as err:
            err_str = err.format_message()
            if ("Return Code: 200" in err_str and
                    "Reason Code: 8" in err_str):
                # VM already active
                LOG.warning("VM %s already active", userid)
                return
            else:
                raise

    def guest_stop(self, userid):
        self._power_state(userid, "PUT", "off")

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % userid)
        res_dict = self._power_state(userid, "GET", "stat")

        @zvmutils.wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        return _get_power_string(res_dict)

    def get_host_info(self):
        """ Retrive host information"""
        host = CONF.zvm.host
        url = self._xcat_url.rinv('/' + host)
        inv_info_raw = zvmutils.xcat_request("GET", url)['info'][0]
        inv_keys = const.XCAT_RINV_HOST_KEYWORDS
        inv_info = zvmutils.translate_xcat_resp(inv_info_raw[0], inv_keys)

        hcp_hostname = inv_info['zhcp']
        self._zhcp_info = self._construct_zhcp_info(hcp_hostname)

        return inv_info

    def get_diskpool_info(self, pool):
        """Retrive diskpool info"""
        host = CONF.zvm.host
        addp = '&field=--diskpoolspace&field=' + pool
        url = self._xcat_url.rinv('/' + host, addp)
        res_dict = zvmutils.xcat_request("GET", url)

        dp_info_raw = res_dict['info'][0]
        dp_keys = const.XCAT_DISKPOOL_KEYWORDS
        dp_info = zvmutils.translate_xcat_resp(dp_info_raw[0], dp_keys)

        return dp_info

    def _get_hcp_info(self, hcp_hostname=None):
        """ Return a Dictionary containing zhcp's hostname,
        nodename and userid
        """
        if self._zhcp_info != {}:
            return self._zhcp_info
        else:
            if hcp_hostname is not None:
                return self._construct_zhcp_info(hcp_hostname)
            else:
                self.get_host_info()
                return self._zhcp_info

    def _construct_zhcp_info(self, hcp_hostname):
        hcp_node = hcp_hostname.partition('.')[0]
        return {'hostname': hcp_hostname,
                'nodename': hcp_node,
                'userid': zvmutils.get_userid(hcp_node)}

    def get_vm_list(self):
        zvm_host = CONF.zvm.host
        hcp_base = self._get_hcp_info()['hostname']

        url = self._xcat_url.tabdump("/zvm")
        res_dict = zvmutils.xcat_request("GET", url)

        vms = []

        with zvmutils.expect_invalid_xcat_resp_data(res_dict):
            data_entries = res_dict['data'][0][1:]
            for data in data_entries:
                l = data.split(",")
                node, hcp = l[0].strip("\""), l[1].strip("\"")
                hcp_short = hcp_base.partition('.')[0]

                # exclude zvm host and zhcp node from the list
                if (hcp.upper() == hcp_base.upper() and
                        node.upper() not in (zvm_host.upper(),
                        hcp_short.upper(), CONF.xcat.master_node.upper())):
                    vms.append(node)

        return vms

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsdef(self, userid):
        url = self._xcat_url.lsdef_node('/' + userid)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0]
        return resp_info

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        if not isinstance(uid_list, list):
            uid_list = [uid_list]

        cmd = ('smcli Image_Performance_Query -T "%(uid_list)s" -c %(num)s' %
               {'uid_list': " ".join(uid_list), 'num': len(uid_list)})

        with zvmutils.expect_invalid_xcat_resp_data():
            resp = zvmutils.xdsh(CONF.xcat.zhcp_node, cmd)
            raw_data = resp["data"][0][0]

        ipq_kws = {
            'userid': "Guest name:",
            'guest_cpus': "Guest CPUs:",
            'used_cpu_time': "Used CPU time:",
            'elapsed_cpu_time': "Elapsed time:",
            'min_cpu_count': "Minimum CPU count:",
            'max_cpu_limit': "Max CPU limit:",
            'samples_cpu_in_use': "Samples CPU in use:",
            'samples_cpu_delay': ",Samples CPU delay:",
            'used_memory': "Used memory:",
            'max_memory': " Max memory:",
        }

        pi_dict = {}
        with zvmutils.expect_invalid_xcat_resp_data():
            rpi_list = raw_data.split(": \n")
            for rpi in rpi_list:
                try:
                    pi = zvmutils.translate_xcat_resp(rpi, ipq_kws)
                except exception.ZVMInvalidXCATResponseDataError as err:
                    emsg = err.format_message()
                    # when there is only one userid queried and this userid is
                    # in 'off'state, the smcli will only returns the queried
                    # userid number, no valid performance info returned.
                    if(emsg.__contains__("No value matched with keywords.")):
                        continue
                    else:
                        raise err
                for k, v in pi.items():
                    pi[k] = v.strip('" ')
                if pi.get('userid') is not None:
                    pi_dict[pi['userid']] = pi

        return pi_dict

    def get_image_performance_info(self, userid):
        pi_dict = self.image_performance_query([userid])
        return pi_dict.get(userid.upper(), None)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsvm(self, userid):
        url = self._xcat_url.lsvm('/' + userid)
        with zvmutils.expect_invalid_xcat_node_and_reraise(userid):
            resp_info = zvmutils.xcat_request("GET", url)['info'][0][0]
        return resp_info.split('\n')

    def get_user_direct(self, userid):
        raw_dict = self._lsvm(userid)
        return [ent.partition(': ')[2] for ent in raw_dict]

    # TODO:moving to vmops and change name to ''
    def get_node_status(self, userid):
        url = self._xcat_url.nodestat('/' + userid)
        res_dict = zvmutils.xcat_request("GET", url)
        return res_dict

    def create_vm(self, userid, cpu, memory, disk_list, profile):
        # Create node for the vm
        self.prepare_for_spawn(userid)
        profile = 'profile=%s' % profile or CONF.zvm.user_profile

        body = [profile,
                'cpu=%i' % cpu,
                'memory=%im' % memory,
                'privilege=%s' % const.ZVM_USER_DEFAULT_PRIVILEGE]

        if not CONF.zvm.zvm_default_admin_userid:
            body.append('password=LBYONLY')
        else:
            body.append('password=LBYONLY')
            body.append('logonby=%s' % CONF.zvm.zvm_default_admin_userid)

        ipl_disk = None
        if disk_list and 'is_boot_disk' in disk_list[0]:
            ipl_disk = CONF.zvm.user_root_vdev

        if ipl_disk:
            body.append('ipl=%s' % ipl_disk)

        url = self._xcat_url.mkvm('/' + userid)
        zvmutils.xcat_request("POST", url, body)

        if disk_list:
            # Add disks for vm
            self.add_mdisks(userid, disk_list)

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

    def _add_mdisk(self, userid, disk, vdev):
        """Create one disk for userid

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """

        size = disk['size']
        fmt = disk.get('format')

        disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool

        disk_type = disk_pool.split(':')[0].upper()
        diskpool_name = disk_pool.split(':')[1]

        if (disk_type == 'ECKD'):
            action = '--add3390'
        elif (disk_type == 'FBA'):
            action = '--add9336'
        else:
            errmsg = ("Disk type %s is not supported.") % disk_type
            LOG.error(errmsg)
            raise exception.ZVMException(msg=errmsg)

        if fmt:
            body = [" ".join([action, diskpool_name, vdev, size, "MR", "''",
                    "''", "''", fmt])]
        else:
            body = [" ".join([action, diskpool_name, vdev, size])]

        url = zvmutils.get_xcat_url().chvm('/' + userid)
        zvmutils.xcat_request("PUT", url, body)

    # TODO:moving to vmops and change name to 'create_vm_node'
    def create_xcat_node(self, userid):
        """Create xCAT node for z/VM instance."""
        LOG.debug("Creating xCAT node for %s" % userid)
        body = ['userid=%s' % userid,
                'hcp=%s' % CONF.xcat.zhcp,
                'mgt=zvm',
                'groups=%s' % const.ZVM_XCAT_GROUP]
        url = self._xcat_url.mkdef('/' + userid)
        zvmutils.xcat_request("POST", url, body)

    # xCAT client can something special for xCAT here
    def prepare_for_spawn(self, userid):
        self.create_xcat_node(userid)

    def remove_image_file(self, image_name):
        url = self._xcat_url.rmimage('/' + image_name)
        zvmutils.xcat_request("DELETE", url)

    def remove_image_definition(self, image_name):
        url = self._xcat_url.rmobject('/' + image_name)
        zvmutils.xcat_request("DELETE", url)

    def change_vm_ipl_state(self, userid, ipl_state):
        body = ["--setipl %s" % ipl_state]
        url = zvmutils.get_xcat_url().chvm('/' + userid)
        zvmutils.xcat_request("PUT", url, body)

    def change_vm_fmt(self, userid, fmt, action, diskpool, vdev, size):
        if fmt:
            body = [" ".join([action, diskpool, vdev, size, "MR", "''", "''",
                    "''", fmt])]
        else:
            body = [" ".join([action, diskpool, vdev, size])]
        url = zvmutils.get_xcat_url().chvm('/' + userid)
        zvmutils.xcat_request("PUT", url, body)

    def get_tabdump_info(self):
        url = self._xcat_url.tabdump("/zvm")
        res_dict = zvmutils.xcat_request("GET", url)
        return res_dict

    def do_capture(self, nodename, profile):
        url = self._xcat_url.capture()
        body = ['nodename=' + nodename,
                'profile=' + profile]
        res = zvmutils.xcat_request("POST", url, body)
        return res

    def _clean_network_resource(self, userid):
        """Clean node records in xCAT mac, host and switch table."""
        self._delete_mac(userid)
        self._delete_switch(userid)
        self._delete_host(userid)

    def _delete_mac(self, userid):
        """Remove node mac record from xcat mac table."""
        commands = "-d node=%s mac" % userid
        url = self._xcat_url.tabch("/mac")
        body = [commands]

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _delete_host(self, userid):
        """Remove xcat hosts table rows where node name is node_name."""
        commands = "-d node=%s hosts" % userid
        body = [commands]
        url = self._xcat_url.tabch("/hosts")

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _delete_switch(self, userid):
        """Remove node switch record from xcat switch table."""
        commands = "-d node=%s switch" % userid
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def create_nic(self, userid, nic_info, ip_addr=None):
        if ip_addr is None:
            raise exception.ZVMInvalidInput(
                msg=("IP address is required"))

        self._preset_vm_network(userid, ip_addr)
        nic_vdev = CONF.zvm.default_nic_vdev
        zhcpnode = self._get_hcp_info()['nodename']
        for nic_item in nic_info:
            nic_id = nic_item['nic_id']
            mac_addr = nic_item['mac_addr']
            LOG.debug('Nic attributes: '
                      'ID is %(id)s, address is %(address)s, '
                      'vdev is %(vdev)s',
                      {'id': nic_id, 'address': mac_addr,
                      'vdev': nic_vdev})
            self._create_nic(userid, nic_id, mac_addr,
                             nic_vdev, zhcpnode)
            nic_vdev = str(hex(int(nic_vdev, 16) + 3))[2:]

    def _create_nic(self, userid, nic_id, mac_address, vdev, zhcpnode):
        self._delete_mac(userid)
        self._add_mac_table_record(userid, vdev, mac_address, zhcpnode)
        self._add_switch_table_record(userid, nic_id, vdev, zhcpnode)

        mac = ''.join(mac_address.split(':'))[6:]
        url = self._xcat_url.chvm('/' + userid)
        commands = ' '.join((
            'Image_Definition_Update_DM -T %userid%',
            '-k \'NICDEF=VDEV=%s TYPE=QDIO' % vdev,
            'MACID=%s\'' % mac))
        body = ['--smcli', commands]

        with zvmutils.expect_invalid_xcat_resp_data():
            zvmutils.xcat_request("PUT", url, body)

    def _add_mac_table_record(self, userid, interface, mac, zhcp=None):
        """Add node name, interface, mac address into xcat mac table."""
        commands = ' '.join(("mac.node=%s" % userid,
                             "mac.mac=%s" % mac,
                             "mac.interface=%s" % interface))
        if zhcp is not None:
            commands += " mac.comments=%s" % zhcp
        url = self._xcat_url.tabch("/mac")
        body = [commands]

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _add_switch_table_record(self, userid, nic_id, interface, zhcp=None):
        """Add node name and nic name address into xcat switch table."""
        commands = ' '.join(("switch.node=%s" % userid,
                             "switch.port=%s" % nic_id,
                             "switch.interface=%s" % interface))
        if zhcp is not None:
            commands += " switch.comments=%s" % zhcp
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _update_vm_info(self, node, node_info):
        """node_info looks like : ['sles12', 's390x', 'netboot',
        '0a0c576a_157f_42c8_bde5_2a254d8b77f']
        """
        url = self._xcat_url.chtab('/' + node)
        body = ['noderes.netboot=%s' % const.HYPERVISOR_TYPE,
                'nodetype.os=%s' % node_info[0],
                'nodetype.arch=%s' % node_info[1],
                'nodetype.provmethod=%s' % node_info[2],
                'nodetype.profile=%s' % node_info[3]]

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMXCATUpdateNodeFailed):
            zvmutils.xcat_request("PUT", url, body)

    def guest_deploy(self, node, image_name, transportfiles=None, vdev=None):
        """image_name format looks like:
        sles12-s390x-netboot-0a0c576a_157f_42c8_bde5_2a254d8b77fc"""
        # Update node info before deploy
        node_info = image_name.split('-')
        self._update_vm_info(node, node_info)

        # Deploy the image to node
        url = self._xcat_url.nodeset('/' + node)
        vdev = vdev or CONF.zvm.user_root_vdev
        body = ['netboot',
                'device=%s' % vdev,
                'osimage=%s' % image_name]

        if transportfiles:
            body.append('transport=%s' % transportfiles)

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMXCATUpdateNodeFailed):
            zvmutils.xcat_request("PUT", url, body)

    def check_space_imgimport_xcat(self, tar_file, xcat_free_space_threshold,
                                   zvm_xcat_master):
        pass

    def export_image(self, image_file_path):
        pass

    def image_import(self, image_bundle_package, image_profile):
        """
        Import the image bundle from computenode to xCAT's image repository.
        :param image_bundle_package: image bundle file path
                eg,'/root/images/xxxx.img.tar'
        :param image_profile: mostly use image_uuid
                eg,'9c95464_2a53_11e7_87fd_020000012'
        """
        remote_host_info = zvmutils.get_host()
        body = ['osimage=%s' % image_bundle_package,
                'profile=%s' % image_profile,
                'remotehost=%s' % remote_host_info,
                'nozip']
        url = self._xcat_url.imgimport()

        try:
            resp = zvmutils.xcat_request("POST", url, body)
        except (exception.ZVMXCATRequestFailed,
                exception.ZVMInvalidXCATResponseDataError,
                exception.ZVMXCATInternalError) as err:
            msg = ("Import the image bundle to xCAT MN failed: %s" %
                   err.format_message())
            raise exception.ZVMImageError(msg=msg)
        finally:
            os.remove(image_bundle_package)
            return resp

    def get_vm_nic_switch_info(self, vm_id):
        """
        Get NIC and switch mapping for the specified virtual machine.
        """
        url = self._xcat_url.tabdump("/switch")
        with zvmutils.expect_invalid_xcat_resp_data():
            switch_info = zvmutils.xcat_request("GET", url)['data'][0]
            switch_info.pop(0)
            switch_dict = {}
            for item in switch_info:
                switch_list = item.split(',')
                if switch_list[0].strip('"') == vm_id:
                    switch_dict[switch_list[4].strip('"')] = \
                                            switch_list[1].strip('"')

            LOG.debug("Switch info the %(vm_id)s is %(switch_dict)s",
                      {"vm_id": vm_id, "switch_dict": switch_dict})
            return switch_dict

    def _config_xcat_mac(self, vm_id):
        """Hook xCat to prevent assign MAC for instance."""
        fake_mac_addr = "00:00:00:00:00:00"
        nic_name = "fake"
        self._add_mac_table_record(vm_id, nic_name, fake_mac_addr)

    def _add_host_table_record(self, vm_id, ip, host_name):
        """Add/Update hostname/ip bundle in xCAT MN nodes table."""
        commands = ' '.join(("node=%s" % vm_id,
                             "hosts.ip=%s" % ip,
                             "hosts.hostnames=%s" % host_name))
        body = [commands]
        url = self._xcat_url.tabch("/hosts")

        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            zvmutils.xcat_request("PUT", url, body)['data']

    def _makehost(self):
        """Update xCAT MN /etc/hosts file."""
        url = self._xcat_url.network("/makehosts")
        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            zvmutils.xcat_request("PUT", url)['data']

    def _preset_vm_network(self, vm_id, ip_addr):
        self._config_xcat_mac(vm_id)
        LOG.debug("Add ip/host name on xCAT MN for instance %s",
                  vm_id)

        self._add_host_table_record(vm_id, ip_addr, vm_id)
        self._makehost()

    def _get_nic_ids(self):
        addp = ''
        url = self._xcat_url.tabdump("/switch", addp)
        with zvmutils.expect_invalid_xcat_resp_data():
            nic_settings = zvmutils.xcat_request("GET", url)['data'][0]
        # remove table header
        nic_settings.pop(0)
        # it's possible to return empty array
        return nic_settings

    def _get_userid_from_node(self, vm_id):
        addp = '&col=node&value=%s&attribute=userid' % vm_id
        url = self._xcat_url.gettab("/zvm", addp)
        with zvmutils.expect_invalid_xcat_resp_data():
            return zvmutils.xcat_request("GET", url)['data'][0][0]

    def _get_nic_settings(self, port_id, field=None, get_node=False):
        """Get NIC information from xCat switch table."""
        LOG.debug("Get nic information for port: %s", port_id)
        addp = '&col=port&value=%s' % port_id + '&attribute=%s' % (
                                                field and field or 'node')
        url = self._xcat_url.gettab("/switch", addp)
        with zvmutils.expect_invalid_xcat_resp_data():
            ret_value = zvmutils.xcat_request("GET", url)['data'][0][0]
        if field is None and not get_node:
            ret_value = self._get_userid_from_node(ret_value)
        return ret_value

    def _get_node_from_port(self, port_id):
        return self._get_nic_settings(port_id, get_node=True)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        """Set vswitch to grant user."""
        zhcp = CONF.xcat.zhcp_node
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k grant_userid=%s" % userid,
            "-h persist=YES"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        zvmutils.xcat_request("PUT", url, body)

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        """Revoke user for vswitch."""
        zhcp = CONF.xcat.zhcp_node
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k revoke_userid=%s" % userid,
            "-h persist=YES"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        zvmutils.xcat_request("PUT", url, body)

    def _couple_nic(self, vswitch_name, userid, vdev, persist=True):
        """Couple NIC to vswitch by adding vswitch into user direct."""
        zhcp = CONF.xcat.zhcp_node
        url = self._xcat_url.xdsh("/%s" % zhcp)
        if persist:
            commands = ' '.join(('/opt/zhcp/bin/smcli',
                                 'Virtual_Network_Adapter_Connect_Vswitch_DM',
                                 "-T %s" % userid,
                                 "-v %s" % vdev,
                                 "-n %s" % vswitch_name))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]
            zvmutils.xcat_request("PUT", url, body)

        # the inst must be active, or this call will failed
        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Connect_Vswitch',
                             "-T %s" % userid,
                             "-v %s" % vdev,
                             "-n %s" % vswitch_name))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        zvmutils.xcat_request("PUT", url, body)

    def couple_nic_to_vswitch(self, vswitch_name, nic_vdev,
                              userid, persist=True):
        """Couple nic to vswitch."""
        LOG.debug("Connect nic to switch: %s", vswitch_name)
        self._couple_nic(vswitch_name, userid, nic_vdev, persist)

    def _uncouple_nic(self, userid, vdev, persist=True):
        """Uncouple NIC from vswitch"""
        zhcp = CONF.xcat.zhcp_node
        url = self._xcat_url.xdsh("/%s" % zhcp)
        if persist:
            commands = ' '.join(('/opt/zhcp/bin/smcli',
                                 'Virtual_Network_Adapter_Disconnect_DM',
                                 "-T %s" % userid,
                                 "-v %s" % vdev))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]
            zvmutils.xcat_request("PUT", url, body)

        # the inst must be active, or this call will failed
        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Disconnect',
                             "-T %s" % userid,
                             "-v %s" % vdev))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        zvmutils.xcat_request("PUT", url, body)

    def uncouple_nic_from_vswitch(self, vswitch_name, nic_vdev,
                                  userid, persist=True):
        """Uncouple nic from vswitch."""
        LOG.debug("Disconnect nic from switch: %s", vswitch_name)
        self._uncouple_nic(userid, nic_vdev, persist)

    def _get_xcat_node_ip(self):
        addp = '&col=key&value=master&attribute=value'
        url = self._xcat_url.gettab("/site", addp)
        with zvmutils.expect_invalid_xcat_resp_data():
            return zvmutils.xcat_request("GET", url)['data'][0][0]

    def _get_xcat_node_name(self):
        if self._xcat_node_name is not None:
            return self._xcat_node_name

        xcat_ip = self._get_xcat_node_ip()
        addp = '&col=ip&value=%s&attribute=node' % (xcat_ip)
        url = self._xcat_url.gettab("/hosts", addp)
        with zvmutils.expect_invalid_xcat_resp_data():
            self._xcat_node_name = zvmutils.xcat_request(
                "GET", url)['data'][0][0]
            return self._xcat_node_name

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def get_vswitch_list(self):
        zhcp = CONF.xcat.zhcp_node
        userid = self._get_zhcp_userid()
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query',
            "-T %s" % userid,
            "-s \'*\'"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        result = zvmutils.xcat_request("PUT", url, body)
        if (result['errorcode'][0][0] != '0' or not
                result['data'] or not result['data'][0]):
            return None
        else:
            data = '\n'.join([s for s in result['data'][0]
                              if isinstance(s, unicode)])
            output = re.findall('VSWITCH:  Name: (.*)', data)
            return output

    def _get_zhcp_userid(self):
        if not self._zhcp_userid:
            self._zhcp_userid = self._get_userid_from_node(CONF.xcat.zhcp_node)
        return self._zhcp_userid

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def add_vswitch(self, name, rdev,
                    controller, connection, queue_mem,
                    router, network_type, vid,
                    port_type, update, gvrp, native_vid):
        zhcp = CONF.xcat.zhcp_node
        vswitch_info = self._check_vswitch_status(name)
        if vswitch_info is not None:
            LOG.info('Vswitch %s already exists,check rdev info.' % name)
            if rdev is None:
                LOG.debug('vswitch %s is not changed', name)
                return
            else:
                # as currently zvm-agent can only set one rdev for vswitch
                # so as long one of rdev in vswitch env are same as rdevs
                # list in config file, we think the vswitch does not change.
                rdev_list = rdev.split(',')
                for i in vswitch_info:
                    for j in rdev_list:
                        if i.strip() == j.strip():
                            LOG.debug('vswitch %s is not changed', name)
                            return

                LOG.info('start changing vswitch %s ' % name)
                self._set_vswitch_rdev(name, rdev)
                return

        if ((vid < 0) or (vid > 4094)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid vlan id should be 0-4094'))
        if ((connection < 0) or (connection > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid connection value should be 0, 1, 2'))
        if ((queue_mem < 1) or (queue_mem > 8)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid query memory value should be 0-8'))
        if ((router < 0) or (router > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid router value should be 0, 1, 2'))
        if ((network_type < 0) or (network_type > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid network type value should be 0, 1, 2'))
        if ((port_type < 0) or (port_type > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid port type value should be 0, 1, 2'))
        if ((update < 0) or (update > 3)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid update indicator should be 0, 1, 2, 3'))
        if ((gvrp < 0) or (gvrp > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid GVRP value should be 0, 1, 2'))
        if (((native_vid < 1) or (native_vid > 4094)) and
            (native_vid != -1)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid native VLAN id should be -1 or 1-4094'))
        # if vid = 0, port_type, gvrp and native_vlanid are not
        # allowed to specified
        if int(vid) == 0:
            vid = 0
            port_type = 0
            gvrp = 0
            native_vid = -1

        userid = self._get_zhcp_userid()
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Create',
            '-T %s' % userid,
            '-n %s' % name))
        if rdev:
            commands += " -r %s" % rdev.replace(',', ' ')
        # commands += " -a %s" % osa_name
        if controller != '*':
            commands += " -i %s" % controller
        commands = ' '.join((commands,
                             "-c %s" % connection,
                             "-q %s" % queue_mem,
                             "-e %s" % router,
                             "-t %s" % network_type,
                             "-v %s" % vid,
                             "-p %s" % port_type,
                             "-u %s" % update,
                             "-G %s" % gvrp,
                             "-V %s" % native_vid))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        result = zvmutils.xcat_request("PUT", url, body)
        if ((result['errorcode'][0][0] != '0') or
            (self._check_vswitch_status(name) is None)):
            raise exception.ZVMException(
                msg=("switch: %s add failed, %s") %
                    (name, result['data']))

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _check_vswitch_status(self, vsw):
        '''
        check the vswitch exists or not,return rdev info
        return value:
        None: vswitch does not exist
        []: vswitch exists but does not connect to a rdev
        ['xxxx','xxxx']:vswitch exists and 'xxxx' is rdev value
        '''
        zhcp = CONF.xcat.zhcp_node
        userid = self._get_zhcp_userid()
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query',
            "-T %s" % userid,
            "-s %s" % vsw))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        result = zvmutils.xcat_request("PUT", url, body)
        if (result['errorcode'][0][0] != '0' or not
                result['data'] or not result['data'][0]):
            return None
        else:
            output = re.findall('Real device: (.*)\n', result['data'][0][0])
            return output

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _set_vswitch_rdev(self, vsw, rdev):
        """Set vswitch's rdev."""
        zhcp = CONF.xcat.zhcp_node
        userid = self._get_zhcp_userid()
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % userid,
            "-k switch_name=%s" % vsw))
        if rdev:
            commands += ' -k real_device_address=%s' % rdev.replace(',', ' ')
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        result = zvmutils.xcat_request("PUT", url, body)
        if (result['errorcode'][0][0] != '0'):
            raise exception.ZVMException(
                msg=("switch: %s changes failed, %s") %
                    (vsw, result['data']))
        LOG.info('change vswitch %s done.' % vsw)

    def image_query(self, imagekeyword=None):
        """List the images"""
        if imagekeyword:
            imagekeyword = imagekeyword.replace('-', '_')
            parm = '&criteria=profile=~' + imagekeyword
        else:
            parm = None
        url = self._xcat_url.lsdef_image(addp=parm)
        with zvmutils.expect_xcat_call_failed_and_reraise(
                exception.ZVMImageError):
            res = zvmutils.xcat_request("GET", url)
        image_list = []
        if res['info']:
            if imagekeyword:
                image_name = res['info'][0][0].strip().split(" ")[0]
                image_list.append(image_name)
            elif len(res['info'][0]) >= 2:
                for img in res['info'][0]:
                    image_name = img.strip().split(" ")[0]
                    image_list.append(image_name)

        return image_list

    def get_user_console_output(self, userid, log_size):
        """get console log."""
        url = self._xcat_url.rinv('/' + userid, '&field=--consoleoutput'
                                  '&field=%s') % log_size

        # Because we might have logs in the console, we need ignore the warning
        res_info = zvmutils.xcat_request("GET", url)

        with zvmutils.expect_invalid_xcat_resp_data(res_info):
            log_data = res_info['info'][0][0]

        raw_log_list = log_data.split('\n')
        return '\n'.join([rec.partition(': ')[2] for rec in raw_log_list])

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

    def _generate_eph_parmline(self, vdev, fmt, mntdir):
        parms = [
                'action=addMdisk',
                'vaddr=' + vdev,
                'filesys=' + fmt,
                'mntdir=' + mntdir
                ]
        parmline = ''.join(parms)
        return parmline

    def process_eph_disk(self, instance_name, vdev=None,
                         fmt=None, mntdir=None):
        if not fmt:
            fmt = CONF.zvm.default_ephemeral_format or\
                  const.DEFAULT_EPH_DISK_FMT
        vdev = vdev or CONF.zvm.user_adde_vdev
        mntdir = mntdir or CONF.zvm.default_ephemeral_mntdir
        eph_parms = self._generate_eph_parmline(vdev, fmt, mntdir)
        self.aemod_handler(instance_name, const.DISK_FUNC_NAME, eph_parms)

    def aemod_handler(self, instance_name, func_name, parms):
        url = self._xcat_url.chvm('/' + instance_name)
        body = [" ".join(['--aemod', func_name, parms])]
        try:
            zvmutils.xcat_request("PUT", url, body)
        except Exception as err:
            emsg = err.format_message()
            LOG.error('Invoke AE method function: %(func)s on %(node)s '
                      'failed with reason: %(msg)s',
                      {'func': func_name, 'node': instance_name, 'msg': emsg})
            raise exception.ZVMDriverError(msg=emsg)

    def delete_vm(self, userid):
        """Delete z/VM userid for the instance.This will remove xCAT node
        and network resource info at same time.
        """
        try:
            self._clean_network_resource(userid)
        except exception.ZVMNetworkError:
            LOG.warning("Clean MAC and VSWITCH failed in delete_userid")
        try:
            self.delete_userid(userid)
        except exception.ZVMXCATInternalError as err:
            emsg = err.format_message()
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 12")):
                # The vm was locked. Unlock before deleting
                self.unlock_userid(userid)
            elif (emsg.__contains__("Return Code: 408") and
                    emsg.__contains__("Reason Code: 12")):
                # The vm device was locked. Unlock the device before deleting
                self.unlock_devices(userid)
            else:
                LOG.debug("exception not able to handle in delete_userid "
                          "%s", self._name)
                raise err
            # delete the vm after unlock
            self.delete_userid(userid)
        except exception.ZVMXCATRequestFailed as err:
            emsg = err.format_message()
            if (emsg.__contains__("Invalid nodes and/or groups") and
                    emsg.__contains__("Forbidden")):
                # Assume neither zVM userid nor xCAT node exist in this case
                return
            else:
                raise err

    def delete_xcat_node(self, nodename):
        """Remove xCAT node for z/VM instance."""
        url = self._xcat_url.rmdef('/' + nodename)
        try:
            zvmutils.xcat_request("DELETE", url)
        except exception.ZVMXCATInternalError as err:
            if err.format_message().__contains__("Could not find an object"):
                # The xCAT node not exist
                return
            else:
                raise err

    def unlock_userid(self, userid):
        """Unlock the specified userid"""
        cmd = "/opt/zhcp/bin/smcli Image_Unlock_DM -T %s" % userid
        zhcp_node = CONF.xcat.zhcp_node
        zvmutils.xdsh(zhcp_node, cmd)

    def unlock_devices(self, userid):
        cmd = "/opt/zhcp/bin/smcli Image_Lock_Query_DM -T %s" % userid
        zhcp_node = CONF.xcat.zhcp_node
        resp = zvmutils.xdsh(zhcp_node, cmd)
        with zvmutils.expect_invalid_xcat_resp_data(resp):
            resp_str = resp['data'][0][0]

        if resp_str.__contains__("is Unlocked..."):
            # unlocked automatically, do nothing
            return

        def _unlock_device(vdev):
            cmd = ("/opt/zhcp/bin/smcli Image_Unlock_DM -T %(uid)s -v %(vdev)s"
                   % {'uid': userid, 'vdev': vdev})
            zvmutils.xdsh(zhcp_node, cmd)

        resp_list = resp_str.split('\n')
        for s in resp_list:
            if s.__contains__('Device address:'):
                vdev = s.rpartition(':')[2].strip()
                _unlock_device(vdev)

    def delete_userid(self, userid):
        url = self._xcat_url.rmvm('/' + userid)
        try:
            zvmutils.xcat_request("DELETE", url)
        except exception.ZVMXCATInternalError as err:
            emsg = err.format_message()
            LOG.debug("error emsg in delete_userid: %s", emsg)
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 4")):
                # zVM user definition not found, delete xCAT node directly
                self.delete_xcat_node(userid)
            else:
                raise

    def _rewr(self, manifest_path):
        f = open(manifest_path + '/manifest.xml', 'r')
        lines = f.read()
        f.close()

        lines = lines.replace('\n', '')
        lines = re.sub(r'>(\s*)<', r'>\n\1<', lines)
        lines = re.sub(r'>[ \t]*(\S+)[ \t]*<', r'>\1<', lines)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(lines)
        f.close()

    def generate_manifest_file(self, image_meta, image_name, disk_file_name,
                               manifest_path):
        """
        Generate the manifest.xml file from glance's image metadata
        as a part of the image bundle.
        """
        image_id = image_meta['id']
        image_type = image_meta['properties']['image_type_xcat']
        os_version = image_meta['properties']['os_version']
        os_name = image_meta['properties']['os_name']
        os_arch = image_meta['properties']['architecture']
        prov_method = image_meta['properties']['provision_method']

        image_profile = image_id.replace('-', '_')
        image_name_xcat = '-'.join((os_version, os_arch,
                               prov_method, image_profile))
        rootimgdir_str = ('/install', prov_method, os_version,
                          os_arch, image_profile)
        rootimgdir = '/'.join(rootimgdir_str)
        today_date = datetime.date.today()
        last_use_date_string = today_date.strftime("%Y-%m-%d")
        is_deletable = "auto:last_use_date:" + last_use_date_string

        doc = Dom.Document()
        xcatimage = doc.createElement('xcatimage')
        doc.appendChild(xcatimage)

        # Add linuximage section
        imagename = doc.createElement('imagename')
        imagename_value = doc.createTextNode(image_name_xcat)
        imagename.appendChild(imagename_value)
        rootimagedir = doc.createElement('rootimgdir')
        rootimagedir_value = doc.createTextNode(rootimgdir)
        rootimagedir.appendChild(rootimagedir_value)
        linuximage = doc.createElement('linuximage')
        linuximage.appendChild(imagename)
        linuximage.appendChild(rootimagedir)
        xcatimage.appendChild(linuximage)

        # Add osimage section
        osimage = doc.createElement('osimage')
        manifest = {'imagename': image_name_xcat,
                    'imagetype': image_type,
                    'isdeletable': is_deletable,
                    'osarch': os_arch,
                    'osname': os_name,
                    'osvers': os_version,
                    'profile': image_profile,
                    'provmethod': prov_method}

        if 'image_comments' in image_meta['properties']:
            manifest['comments'] = image_meta['properties']['image_comments']

        for item in list(manifest.keys()):
            itemkey = doc.createElement(item)
            itemvalue = doc.createTextNode(manifest[item])
            itemkey.appendChild(itemvalue)
            osimage.appendChild(itemkey)
            xcatimage.appendChild(osimage)
            f = open(manifest_path + '/manifest.xml', 'w')
            f.write(doc.toprettyxml(indent=''))
            f.close()

        # Add the rawimagefiles section
        rawimagefiles = doc.createElement('rawimagefiles')
        xcatimage.appendChild(rawimagefiles)

        files = doc.createElement('files')
        files_value = doc.createTextNode(rootimgdir + '/' + disk_file_name)
        files.appendChild(files_value)

        rawimagefiles.appendChild(files)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(doc.toprettyxml(indent='  '))
        f.close()

        self._rewr(manifest_path)

        return manifest_path + '/manifest.xml'

    def generate_image_bundle(self, spawn_path, time_stamp_dir,
                              image_name, image_file_path):
        """
        Generate the image bundle which is used to import to xCAT MN's
        image repository.
        """
        image_bundle_name = image_name + '.tar'
        tar_file = spawn_path + '/' + time_stamp_dir + '_' + image_bundle_name
        LOG.debug("The generate the image bundle file is %s", tar_file)

        # copy tmp image file to bundle path
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)
        image_file_copy = os.path.join(bundle_file_path, image_name)
        shutil.copyfile(image_file_path, image_file_copy)

        os.chdir(spawn_path)
        tarFile = tarfile.open(tar_file, mode='w')
        try:
            tarFile.add(time_stamp_dir)
            tarFile.close()
        except Exception as err:
            msg = ("Generate image bundle failed: %s" % err)
            LOG.error(msg)
            if os.path.isfile(tar_file):
                os.remove(tar_file)
            raise exception.ZVMImageError(msg=msg)
        finally:
            self._pathutils.clean_temp_folder(time_stamp_dir)

        return tar_file

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        zhcp = CONF.xcat.zhcp_node
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % userid,
            "-k grant_userid=%s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k user_vlan_id=%s" % vlan_id))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        zvmutils.xcat_request("PUT", url, body)

    def update_nic_definition(self, userid, nic_vdev, mac, switch_name):
        """add one NIC's info to user direct."""
        url = self._xcat_url.chvm('/' + userid)
        commands = ' '.join((
            'Image_Definition_Update_DM -T %userid%',
            '-k \'NICDEF=VDEV=%s TYPE=QDIO' % nic_vdev,
            'MACID=%s' % mac,
            'LAN=SYSTEM',
            'SWITCHNAME=%s\'' % switch_name))
        body = ['--smcli', commands]

        with zvmutils.expect_invalid_xcat_resp_data():
            zvmutils.xcat_request("PUT", url, body)
