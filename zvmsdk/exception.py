import config
import log
import six

CONF = config.CONF
LOG = log.LOG


class BaseException(Exception):
    """
    Inherit from this class and define a 'msg_fmt' property.
    That msg_fmt will get printf'd with the keyword arguments
    provided to the constructor.
    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kw = kwargs
        if 'code' in self.kw:
            try:
                self.kw['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                LOG.exception('Exception in string format operation')
                for name, value in six.iteritems(kwargs):
                    LOG.error("%s: %s" % (name, value))

                message = self.msg_fmt

        self.message = message
        super(BaseException, self).__init__(message)

    def format_message(self):
        return self.args[0]


class ZVMDriverError(BaseException):
    msg_fmt = 'z/VM driver error: %(msg)s'


class ZVMXCATRequestFailed(BaseException):
    msg_fmt = 'Request to xCAT server %(xcatserver)s failed: %(msg)s'


class ZVMInvalidXCATResponseDataError(BaseException):
    msg_fmt = 'Invalid data returned from xCAT: %(msg)s'


class ZVMXCATInternalError(BaseException):
    msg_fmt = 'Error returned from xCAT: %(msg)s'


class ZVMVolumeError(BaseException):
    msg_fmt = 'Volume error: %(msg)s'


class ZVMImageError(BaseException):
    msg_fmt = "Image error: %(msg)s"


class ZVMGetImageFromXCATFailed(BaseException):
    msg_fmt = 'Get image from xCAT failed: %(msg)s'


class ZVMNetworkError(BaseException):
    msg_fmt = "z/VM network error: %(msg)s"


class ZVMXCATXdshFailed(BaseException):
    msg_fmt = 'Execute xCAT xdsh command failed: %(msg)s'


class ZVMXCATCreateNodeFailed(BaseException):
    msg_fmt = 'Create xCAT node %(node)s failed: %(msg)s'


class ZVMXCATCreateUserIdFailed(BaseException):
    msg_fmt = 'Create xCAT user id %(instance)s failed: %(msg)s'


class ZVMXCATUpdateNodeFailed(BaseException):
    msg_fmt = 'Update node %(node)s info failed: %(msg)s'


class ZVMXCATDeployNodeFailed(BaseException):
    msg_fmt = 'Deploy image on node %(node)s failed: %(msg)s'


class ZVMConfigDriveError(BaseException):
    msg_fmt = 'Create configure drive failed: %(msg)s'


class ZVMRetryException(BaseException):
    pass
