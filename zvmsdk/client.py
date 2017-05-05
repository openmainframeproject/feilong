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


import os
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


class XCATClient(ZVMClient):

    def __init__(self):
        self._xcat_url = zvmutils.get_xcat_url()
        self._zhcp_info = {}

    def _power_state(self, userid, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + userid)
        with zvmutils.except_invalid_xcat_node_and_reraise(userid):
            return zvmutils.xcat_request(method, url, body)

    def power_on(self, userid):
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

    def get_diskpool_info(self, pool=CONF.zvm.diskpool):
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

    def _image_performance_query(self, uid_list):
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
            'used_memory': "Used memory:",
            'max_memory': " Max memory:",
        }

        pi_dict = {}
        with zvmutils.expect_invalid_xcat_resp_data():
            rpi_list = raw_data.split(": \n")
            for rpi in rpi_list:
                pi = zvmutils.translate_xcat_resp(rpi, ipq_kws)
                for k, v in pi.items():
                    pi[k] = v.strip('" ')
                if pi.get('userid') is not None:
                    pi_dict[pi['userid']] = pi

        return pi_dict

    def get_image_performance_info(self, userid):
        pi_dict = self._image_performance_query([userid])
        return pi_dict.get(userid.upper(), None)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsvm(self, userid):
        url = self._xcat_url.lsvm('/' + userid)
        with zvmutils.except_invalid_xcat_node_and_reraise(userid):
            resp_info = zvmutils.xcat_request("GET", url)['info'][0][0]
        return resp_info.split('\n')

    def get_user_direct(self, userid):
        resp_info = self._lsvm(userid)
        return resp_info

    # TODO:moving to vmops and change name to ''
    def get_node_status(self, userid):
        url = self._xcat_url.nodestat('/' + userid)
        res_dict = zvmutils.xcat_request("GET", url)
        return res_dict

    def validate_vm_id(self, userid):
        if len(userid) > 8:
            msg = ("Don't support spawn vm on zVM hypervisor with name:%s,"
                   "please make sure vm_id not longer than 8." % userid)
            raise exception.ZVMInvalidInput(msg)

    def make_vm(self, userid, kwprofile, cpu, memory, image_name):
        body = [kwprofile,
                'password=%s' % CONF.zvm.user_default_password,
                'cpu=%i' % cpu,
                'memory=%im' % memory,
                'privilege=%s' % const.ZVM_USER_DEFAULT_PRIVILEGE,
                'ipl=%s' % CONF.zvm.user_root_vdev,
                'imagename=%s' % image_name]

        url = zvmutils.get_xcat_url().mkvm('/' + userid)
        zvmutils.xcat_request("POST", url, body)

    # TODO:moving to vmops and change name to 'create_vm_node'
    def create_xcat_node(self, userid):
        """Create xCAT node for z/VM instance."""
        LOG.debug("Creating xCAT node for %s" % userid)
        body = ['userid=%s' % userid,
                'hcp=%s' % CONF.zhcp,
                'mgt=zvm',
                'groups=%s' % const.ZVM_XCAT_GROUP]
        url = self._xcat_url.mkdef('/' + userid)
        zvmutils.xcat_request("POST", url, body)

    def _delete_xcat_node(self, userid):
        """Remove xCAT node for z/VM instance."""
        url = self._xcat_url.rmdef('/' + userid)
        try:
            zvmutils.xcat_request("DELETE", url)
        except Exception as err:
            if err.format_message().__contains__("Could not find an object"):
                # The xCAT node not exist
                return
            else:
                raise err

    def _delete_userid(self, url):
        try:
            zvmutils.xcat_request("DELETE", url)
        except Exception as err:
            emsg = err.format_message()
            LOG.debug("error emsg in delete_userid: %s", emsg)
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 4")):
                # zVM user definition not found, delete xCAT node directly
                self._delete_xcat_node()
            else:
                raise err

    def remove_vm(self, userid):
        url = zvmutils.get_xcat_url().rmvm('/' + userid)
        self._delete_userid(url)

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

    def clean_network_resource(self, userid):
        """Clean node records in xCAT mac, host and switch table."""
        self._delete_mac(userid)
        self._delete_switch(userid)
        self._delete_host(userid)

    def _delete_mac(self, userid):
        """Remove node mac record from xcat mac table."""
        commands = "-d node=%s mac" % userid
        url = self._xcat_url.tabch("/mac")
        body = [commands]

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _delete_host(self, userid):
        """Remove xcat hosts table rows where node name is node_name."""
        commands = "-d node=%s hosts" % userid
        body = [commands]
        url = self._xcat_url.tabch("/hosts")

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _delete_switch(self, userid):
        """Remove node switch record from xcat switch table."""
        commands = "-d node=%s switch" % userid
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def create_port(self, userid, nic_id, mac_address, vdev):
        zhcpnode = self._get_hcp_info()['nodename']
        self._delete_mac(userid)
        self._add_mac_table_record(userid, vdev, mac_address, zhcpnode)
        self._add_switch_table_record(userid, nic_id, vdev, zhcpnode)

    def _add_mac_table_record(self, userid, interface, mac, zhcp=None):
        """Add node name, interface, mac address into xcat mac table."""
        commands = "mac.node=%s" % userid + " mac.mac=%s" % mac
        commands += " mac.interface=%s" % interface
        if zhcp is not None:
            commands += " mac.comments=%s" % zhcp
        url = self._xcat_url.tabch("/mac")
        body = [commands]

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return zvmutils.xcat_request("PUT", url, body)['data']

    def _add_switch_table_record(self, userid, nic_id, interface, zhcp=None):
        """Add node name and nic name address into xcat switch table."""
        commands = "switch.node=%s" % userid
        commands += " switch.port=%s" % nic_id
        commands += " switch.interface=%s" % interface
        if zhcp is not None:
            commands += " switch.comments=%s" % zhcp
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with zvmutils.except_xcat_call_failed_and_reraise(
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

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMXCATUpdateNodeFailed):
            zvmutils.xcat_request("PUT", url, body)

    def deploy_image_to_vm(self, node, image_name, transportfiles=None):
        """image_name format looks like:
        sles12-s390x-netboot-0a0c576a_157f_42c8_bde5_2a254d8b77fc"""
        # Update node info before deploy
        node_info = image_name.split('-')
        self._update_vm_info(node, node_info)

        # Deploy the image to node
        url = self._xcat_url.nodeset('/' + node)
        vdev = CONF.zvm.user_root_vdev
        body = ['netboot',
                'device=%s' % vdev,
                'osimage=%s' % image_name]

        if transportfiles:
            body.append('transport=%s' % transportfiles)

        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMXCATUpdateNodeFailed):
            zvmutils.xcat_request("PUT", url, body)

    def lsdef_image(self, image_uuid):
        parm = '&criteria=profile=~' + image_uuid
        url = self._xcat_url.lsdef_image(addp=parm)
        with zvmutils.except_xcat_call_failed_and_reraise(
                exception.ZVMImageError):
            res = zvmutils.xcat_request("GET", url)
        return res

    def check_space_imgimport_xcat(self, tar_file, xcat_free_space_threshold,
                                   zvm_xcat_master):
        pass

    def export_image(self, image_file_path):
        pass

    def import_image(self, image_bundle_package, image_profile):
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
