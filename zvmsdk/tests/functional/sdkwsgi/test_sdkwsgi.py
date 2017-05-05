#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

import wsgi_intercept
from gabbi import driver

from zvmsdk.sdkwsgi import deploy

wsgi_intercept.STRICT_RESPONSE_HEADERS = True
TESTS_DIR = 'gabbits'


def setup_app():
    return deploy.loadapp()


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    # These inner fixtures provide per test request output and log
    # capture, for cleaner results reporting.
    return driver.build_tests(test_dir, loader, host=None,
                              intercept=setup_app,
                              test_loader_name=__name__)
