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

    def _power_state(self, userid, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + userid)
        return zvmutils.xcat_request(method, url, body)

    def power_on(self, userid):
        """"Power on VM."""
        try:
            self._power_state(userid, "PUT", "on")
        except exception.ZVMXCATInternalError as err:
            err_str = str(err)
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

    def get_host_info(self, host):
        """ Retrive host information"""
        url = self._xcat_url.rinv('/' + host)
        inv_info_raw = zvmutils.xcat_request("GET", url)['info'][0]
        inv_keys = const.XCAT_RINV_HOST_KEYWORDS
        inv_info = zvmutils.translate_xcat_resp(inv_info_raw[0], inv_keys)
        dp_info = self.get_diskpool_info(host)

        host_info = {}

        with zvmutils.expect_invalid_xcat_resp_data(inv_info):
            host_info['vcpus'] = int(inv_info['lpar_cpu_total'])
            host_info['vcpus_used'] = int(inv_info['lpar_cpu_used'])
            host_info['cpu_info'] = {}
            host_info['cpu_info'] = {'architecture': const.ARCHITECTURE,
                                     'cec_model': inv_info['cec_model'], }
            host_info['disk_total'] = dp_info['disk_total']
            host_info['disk_used'] = dp_info['disk_used']
            host_info['disk_available'] = dp_info['disk_available']
            mem_mb = zvmutils.convert_to_mb(inv_info['lpar_memory_total'])
            host_info['memory_mb'] = mem_mb
            mem_mb_used = zvmutils.convert_to_mb(inv_info['lpar_memory_used'])
            host_info['memory_mb_used'] = mem_mb_used
            host_info['hypervisor_type'] = const.HYPERVISOR_TYPE
            verl = inv_info['hypervisor_os'].split()[1].split('.')
            version = int(''.join(verl))
            host_info['hypervisor_version'] = version
            host_info['hypervisor_hostname'] = inv_info['hypervisor_name']
            host_info['zhcp'] = inv_info['zhcp']
            host_info['ipl_time'] = inv_info['ipl_time']

        return host_info

    def get_diskpool_info(self, host, pool=CONF.zvm.diskpool):
        """Retrive diskpool info"""
        addp = '&field=--diskpoolspace&field=' + pool
        url = self._xcat_url.rinv('/' + host, addp)
        res_dict = zvmutils.xcat_request("GET", url)

        dp_info_raw = res_dict['info'][0]
        dp_keys = const.XCAT_DISKPOOL_KEYWORDS
        dp_info = zvmutils.translate_xcat_resp(dp_info_raw[0], dp_keys)

        with zvmutils.expect_invalid_xcat_resp_data(dp_info):
            for k in list(dp_info.keys()):
                s = dp_info[k].strip().upper()
                if s.endswith('G'):
                    sl = s[:-1].split('.')
                    n1, n2 = int(sl[0]), int(sl[1])
                    if n2 >= 5:
                        n1 += 1
                    dp_info[k] = n1
                elif s.endswith('M'):
                    n_mb = int(s[:-1])
                    n_gb, n_ad = n_mb / 1024, n_mb % 1024
                    if n_ad >= 512:
                        n_gb += 1
                    dp_info[k] = n_gb
                else:
                    exp = "ending with a 'G' or 'M'"
                    errmsg = ("Invalid diskpool size format: %(invalid)s; "
                        "Expected: %(exp)s") % {'invalid': s, 'exp': exp}
                    LOG.error(errmsg)
                    raise exception.ZVMSDKInternalError(msg=errmsg)

        return dp_info

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsdef(self, userid):
        url = self._xcat_url.lsdef_node('/' + userid)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0]
        return resp_info

    def get_lsdef_info(self, userid):
        lsdef_info = self._lsdef(userid)
        return lsdef_info

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsvm(self, userid):
        url = self._xcat_url.lsvm('/' + userid)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0][0]
        return resp_info.split('\n')

    def get_lsvm_info(self, userid):
        resp_info = self._lsvm(userid)
        return resp_info

    def get_node_status(self, userid):
        url = self._xcat_url.nodestat('/' + userid)
        res_dict = zvmutils.xcat_request("GET", url)
        return res_dict

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

    def delete_xcat_node(self, userid):
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
                self.delete_xcat_node()
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
