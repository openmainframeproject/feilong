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
"""Extend functionality from webob.dec.wsgify for sdk API."""

import json
import six
import webob

from webob.dec import wsgify

from zvmsdk import log
from zvmsdk.sdkwsgi import util


LOG = log.LOG
SDKWSGI_MODID = 120


class SdkWsgify(wsgify):

    def call_func(self, req, *args, **kwargs):
        """Add json_error_formatter to any webob HTTPExceptions."""
        try:
            super(SdkWsgify, self).call_func(req, *args, **kwargs)
        except webob.exc.HTTPException as exc:
            msg = ('encounter %(error)s error') % {'error': exc}
            LOG.debug(msg)
            exc.json_formatter = util.json_error_formatter
            code = exc.status_int
            explanation = six.text_type(exc)

            fault_data = {
                'overallRC': 400,
                'rc': 400,
                'rs': code,
                'modID': SDKWSGI_MODID,
                'output': '',
                'errmsg': explanation}
            exc.text = six.text_type(json.dumps(fault_data))
            return exc
