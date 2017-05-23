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
"""Deployment handling for sdk API."""

from zvmsdk.sdkwsgi import handler
from zvmsdk.sdkwsgi import microversion
from zvmsdk.sdkwsgi import requestlog


NAME = "sdk"


def deploy(project_name):
    """Assemble the middleware pipeline leading to the placement app."""
    microversion_middleware = microversion.MicroversionMiddleware
    request_log = requestlog.RequestLog

    application = handler.SdkHandler()

    for middleware in (microversion_middleware,
                       request_log,
                       ):
        if middleware:
            application = middleware(application)

    return application


def loadapp(project_name=NAME):
    application = deploy(project_name)
    return application
