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

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsdef(self, userid):
        url = self._xcat_url.lsdef_node('/' + userid)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0]
        return resp_info

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_current_memory(self, rec_list):
        """Return the max memory can be used."""
        _mem = None

        for rec in rec_list:
            if rec.__contains__("Total Memory: "):
                tmp_list = rec.split()
                _mem = tmp_list[3]
                break

        _mem = self._modify_storage_format(_mem)
        return _mem

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_cpu_used_time(self, rec_list):
        """Return the cpu used time in."""
        cpu_time = 0

        for rec in rec_list:
            if rec.__contains__("CPU Used Time: "):
                tmp_list = rec.split()
                cpu_time = tmp_list[4]
                break

        return float(cpu_time)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_guest_cpus(self, rec_list):
        """Return the processer count, used by cpumempowerstat"""
        guest_cpus = 0

        for rec in rec_list:
            if rec.__contains__("Guest CPUs: "):
                tmp_list = rec.split()
                guest_cpus = tmp_list[3]
                break

        return int(guest_cpus)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_power_stat(self, rec_list):
        """Return the power stat, used by cpumempowerstat"""
        power_stat = None

        for rec in rec_list:
            if rec.__contains__("Power state: "):
                tmp_list = rec.split()
                power_stat = tmp_list[3]
                break

        return power_stat

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
            rpi_list = raw_data.split("".join((CONF.xcat.zhcp_node, ": \n")))
            for rpi in rpi_list:
                pi = zvmutils.translate_xcat_resp(rpi, ipq_kws)
                for k, v in pi.items():
                    pi[k] = v.strip('"')
                if pi.get('userid') is not None:
                    pi_dict[pi['userid']] = pi

        return pi_dict

    def get_image_performance_info(self, userid):
        pi_dict = self._image_performance_query([userid])
        return pi_dict[userid.upper()]

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
