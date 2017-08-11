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
    f.write('\n\n')


def _print_one_section(f, section, data):
    f.write('[')
    f.write(section)
    f.write(']')

    _print_one_line(f)

    f.write(str(data))


def generate(f):
    dicts = CONF.get_config_dicts_default(config.zvm_opts)
    for data in sorted(dicts):
        _print_one_section(f, data, dicts[data])
        _print_one_line(f)


def main(args=None):
    generate(sys.stdout)

main()
