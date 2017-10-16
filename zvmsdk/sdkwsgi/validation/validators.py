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

import netaddr
import re

import jsonschema

from zvmsdk.sdkwsgi.validation import parameter_types


@jsonschema.FormatChecker.cls_checks('name', Exception)
def _validate_name(instance):
    regex = parameter_types.valid_name_regex
    try:
        if re.search(regex.regex, instance):
            return True
    except TypeError:
        # The name must be string type. If instance isn't string type, the
        # TypeError will be raised at here.
        pass

    raise Exception


def validate_release(os_version, distro, remain):
    supported = {'rhel': ['6', '7'],
                 'sles': ['11', '12'],
                 'ubuntu': ['16']}
    releases = supported[distro]
    for r in releases:
        if remain.startswith(r):
            return True
    return False


@jsonschema.FormatChecker.cls_checks('os_version')
def _validate_os_version(os_version):
    """Separate os and version from os_version.

    Possible return value are only:
    ('rhel', x.y) and ('sles', x.y) where x.y may not be digits
    """
    supported = {'rhel': ['rhel', 'redhat', 'red hat'],
                 'sles': ['suse', 'sles'],
                 'ubuntu': ['ubuntu']}
    os_version = os_version.lower()
    for distro, patterns in supported.items():
        for i in patterns:
            if os_version.startswith(i):
                # Not guarrentee the version is digital
                remain = os_version.split(i, 2)[1]
                release = validate_release(os_version, distro, remain)
                if release:
                    return True
                else:
                    return False
    return False


@jsonschema.FormatChecker.cls_checks('cidr')
def _validate_cidr_format(cidr):
    try:
        netaddr.IPNetwork(cidr)
    except netaddr.AddrFormatError:
        return False
    if '/' not in cidr:
        return False
    if re.search('\s', cidr):
        return False
    return True
