

from log import LOG
import utils as zvmutils


VMOPS = None


def _get_vmops():
    if VMOPS is None:
        VMOPS = VMOps()
    return VMOPS


def run_instance(instance_name, image_id, cpu, memory,
                 login_password, ip_addr):
    """Deploy and provision a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :image_id:        Image ID
    :cpu:             vcpu
    :memory:          memory
    :login_password:  login password
    :ip_addr:         ip address
    """
    pass


def terminate_instance(instance_name):
    """Destroy a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    pass

def start_instance(instance_name):
    """Power on a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    _get_vmops()._power_state(instance_name, "PUT", "on")

def stop_instance(instance_name):
    """Shutdown a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    pass


def create_volume(volume_name, size):
    """Create a volume.

    Input parameters:
    :volume_name:     volume name
    :size:            size
    """
    pass


def delete_volume(volume_name):
    """Create a volume.

    Input parameters:
    :volume_name:     volume name
    """
    pass


def attach_volume(instance_name, volume_name):
    """Create a volume.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :volume_name:     volume name
    """
    pass


def capture_instance(instance_name, image_name):
    """Caputre a virtual machine image.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :image_name:      Image name
    """
    pass


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name
    """
    pass


def detach_volume(instance_name, volume_name):
    """Create a volume.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :volume_name:     volume name
    """
    pass


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
