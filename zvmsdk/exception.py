import config
import log
import six
from i18n import _

CONF = config.CONF
LOG = log.LOG


class BaseException(Exception):
    msg_fmt = _("An unknown exception occurred.")
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
    msg_fmt = _('z/VM driver error: %(msg)s')


class ZVMXCATRequestFailed(BaseException):
    msg_fmt = _('Request to xCAT server %(xcatserver)s failed: %(msg)s')


class ZVMInvalidXCATResponseDataError(BaseException):
    msg_fmt = _('Invalid data returned from xCAT: %(msg)s')


class ZVMXCATInternalError(BaseException):
    msg_fmt = _('Error returned from xCAT: %(msg)s')


class ZVMVolumeError(BaseException):
    msg_fmt = _('Volume error: %(msg)s')


class ZVMImageError(BaseException):
    msg_fmt = _("Image error: %(msg)s")


class ZVMGetImageFromXCATFailed(BaseException):
    msg_fmt = _('Get image from xCAT failed: %(msg)s')


class ZVMNetworkError(BaseException):
    msg_fmt = _("z/VM network error: %(msg)s")


class ZVMXCATXdshFailed(BaseException):
    msg_fmt = _('Execute xCAT xdsh command failed: %(msg)s')


class ZVMXCATCreateNodeFailed(BaseException):
    msg_fmt = _('Create xCAT node %(node)s failed: %(msg)s')


class ZVMXCATCreateUserIdFailed(BaseException):
    msg_fmt = _('Create xCAT user id %(instance)s failed: %(msg)s')


class ZVMXCATUpdateNodeFailed(BaseException):
    msg_fmt = _('Update node %(node)s info failed: %(msg)s')


class ZVMXCATDeployNodeFailed(BaseException):
    msg_fmt = _('Deploy image on node %(node)s failed: %(msg)s')


class ZVMConfigDriveError(BaseException):
    msg_fmt = _('Create configure drive failed: %(msg)s')


class ZVMRetryException(BaseException):
    pass
