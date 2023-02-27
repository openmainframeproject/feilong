#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017 IBM Corp.
#
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

import sys

from zvmsdk import config


CONF = config.ConfigOpts()


def _print_one_line(f):
    f.write('\n')


def _print_with_comment(f, v, key):
    string = v.split('\n')
    for i in string:
        if key:
            f.write('#')
        else:
            f.write('# ')
        f.write(i)
        f.write('\n')


def _print_one_section(f, section, data):
    f.write('[')
    f.write(section)
    f.write(']')

    _print_one_line(f)

    for k,v in sorted(data.items()):
        
        _print_one_line(f)

        if 'help' in v and len(v['help']) != 0:
            _print_with_comment(f, v['help'], False)

        if 'required' in v:
            if v['required']:
                required = 'This param is required'
            else:
                required = 'This param is optional'
            _print_with_comment(f, required, False)

        if 'default' in v:
            setting = '%s=%s' % (k, v['default'])
        else:
            setting = '%s=' % k
        _print_with_comment(f, setting, True)
        _print_one_line(f)


def generate(f):
    dicts = CONF.get_config_dicts_default(config.zvm_opts)
    for data in sorted(dicts):
        # bypass test section on purpose
        if (data == 'tests'):
            continue

        # xcat is only used for internal test purpose
        if (data == 'xcat'):
            continue

        _print_one_section(f, data, dicts[data])
        _print_one_line(f)


def main(args=None):
    doc_file = './zvmsdk.conf.sample'
    with open(doc_file, 'w') as f:
        generate(f)

main()
