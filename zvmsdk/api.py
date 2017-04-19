

from zvmsdk import vmops


class ComputeAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self.vmops = vmops._get_vmops()

    def power_on(self, vm_id):
        self.vmops.power_on(vm_id)

    def get_power_state(self, vm_id):
        return self.vmops.get_power_state(vm_id)
