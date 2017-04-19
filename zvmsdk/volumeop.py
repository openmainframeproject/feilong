class VolumeOperatorAPI(object):
    """Volume operation APIs oriented towards SDK driver.

    The reason to design these APIs is to facilitate the SDK driver
    issuing a volume related request without knowing details. The
    details among different distributions, different instance status,
    different volume types and so on are all hidden behind these APIs.
    The only thing the issuer need to know is what it want to do on
    which targets.

    In fact, that's an ideal case. In the real world, something like
    connection_info still depends on different complex and the issuer
    needs to know how to deal with its case. Even so, these APIs can
    still make things much easier.
    """

    def attach_volume_to_instance(self, instance, volume, connection_info,
                                  is_rollback_on_failure=False):
        raise NotImplementedError

    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_on_failure=False):
        raise NotImplementedError


class VolumeConfiguratorAPI(object):
    """Volume configure APIs to implement volume config jobs on the
    target instance, like: attach, detach, and so on.

    The reason to design these APIs is to hide the details among
    different Linux distributions and releases.
    """

    def config_attach(self, volume, connection_info,
                      is_rollback_on_failure=False):
        raise NotImplementedError

    def config_detach(self, volume, connection_info,
                      is_rollback_on_failure=False):
        raise NotImplementedError


class VolumeTools(object):
    """Tool functions for volume operations."""

    @staticmethod
    def get_volume_configurator(instance):
        pass

    @staticmethod
    def get_volume_parameter_parser(volume):
        pass
