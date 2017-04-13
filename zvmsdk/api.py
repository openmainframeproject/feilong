

from zvmsdk import vmops


class ComputeAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self.vmops = vmops._get_vmops()
