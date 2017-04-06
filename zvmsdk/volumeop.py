class VolumeOpAPI(object):
    """Volume operator APIs oriented towards SDK driver."""

    def attach_volume_to_instance(self, instance, volume, connection_info,
                                  is_rollback_on_failure=False):
        raise NotImplementedError

    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_on_failure=False):
        raise NotImplementedError


class VolumeAPI(object):
    """Volume APIs oriented towards volume_op."""

    def attach_to(self, instance, connection_info,
                  is_rollback_on_failure=False):
        """Config and establish a connection to the instance."""
        raise NotImplementedError

    def detach_from(self, instance, connection_info,
                    is_rollback_on_failure=False):
        """Config and release the connection from the instance."""
        raise NotImplementedError
