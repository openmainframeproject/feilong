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
"""Deployment handling for Placmenent API."""

from api import handler
from api import microversion
from api import requestlog


# TODO(cdent): NAME points to the config project being used, so for
# now this is "nova" but we probably want "placement" eventually.
NAME = "sdk"


def deploy( project_name):
    """Assemble the middleware pipeline leading to the placement app."""
    microversion_middleware = microversion.MicroversionMiddleware
    request_log = requestlog.RequestLog

    application = handler.SdkHandler()

    # The ordering here is important. The list is ordered
    # from the inside out. For a single request req_id_middleware is called
    # first and microversion_middleware last. Then the request is finally
    # passed to the application (the PlacementHandler). At that point
    # the response ascends the middleware in the reverse of the
    # order the request went in. This order ensures that log messages
    # all see the same contextual information including request id and
    # authentication information.
    for middleware in (microversion_middleware,
                       request_log,
                       ):
        if middleware:
            application = middleware(application)

    return application


def loadapp(project_name=NAME):
    application = deploy(project_name)
    return application
