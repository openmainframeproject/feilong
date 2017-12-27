#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from zvmsdk import config
import zvmsdk.utils as zvmutils
from zvmsdk.tests.unit import base


CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class ZVMUtilsTestCases(base.SDKTestCase):
    def test_convert_to_mb(self):
        self.assertEqual(2355.2, zvmutils.convert_to_mb('2.3G'))
        self.assertEqual(20, zvmutils.convert_to_mb('20M'))
        self.assertEqual(1153433.6, zvmutils.convert_to_mb('1.1T'))

    def test_validate_option_sdkserver_connect_type(self):
        set_conf("sdkserver", "connect_type", "dummy")
        self.assertEqual(False, zvmutils.validate_options())

        set_conf("sdkserver", "connect_type", "rest")
        self.assertEqual(True, zvmutils.validate_options())

    def test_validate_option_zvm_disk_pool(self):
        set_conf("zvm", "disk_pool", "dummy")
        self.assertEqual(False, zvmutils.validate_options())

        set_conf("zvm", "disk_pool", "a:b")
        self.assertEqual(True, zvmutils.validate_options())
