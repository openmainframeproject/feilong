

from zvmsdk import config
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG


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
        """"Power on z/VM instance."""
        self._power_state(userid, "PUT", "on")

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % userid)
        res_dict = self._power_state(userid, "GET", "stat")

        @zvmutils.wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        return _get_power_string(res_dict)


def get_zvmclient():
    if CONF.client_type == 'xcat':
        return XCATClient()
    else:
        # TODO: raise Exception
        pass
