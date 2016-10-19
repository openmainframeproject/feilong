

from log import LOG
import utils as zvmutils


class VMOps(object):
    def __init__(self):
        self._xcat_url = zvmutils.get_xcat_url()

    def _power_state(self, instance_name, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + instance_name)
        return zvmutils.xcat_request(method, url, body)

    def get_power_state(self, instance_name):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % instance_name)
        res_dict = self._power_state(instance_name, "GET", "stat")

        @zvmutils.wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        power_stat = _get_power_string(res_dict)
        return power_stat
