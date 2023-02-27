#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2018 IBM Corp.
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

import json
import os
import six

from zvmsdk import log


LOG = log.LOG


class NotMatch(Exception):
    pass


def make_json(data):
    if not data:
        return {}
    # data = re.sub(r'(\: )%\((.+)\)s([^"])', r'\1"%(int:\2)s"\3', data)
    return json.loads(data)


class APITestBase(object):
    def _compare(self, expected, result):
        matched_value = None

        if expected is None:
            if result is None:
                pass
            elif result == u'':
                pass
            else:
                raise NotMatch('Expected None, got %(result)s.'
                        % {'result': result})
        elif isinstance(expected, dict):
            if not isinstance(result, dict):
                raise NotMatch('%(result)s is not a dict.'
                        % {'result': result})
            ex_keys = sorted(expected.keys())
            res_keys = sorted(result.keys())
            if ex_keys != res_keys:
                ex_delta = []
                res_delta = []
                for key in ex_keys:
                    if key not in res_keys:
                        ex_delta.append(key)
                for key in res_keys:
                    if key not in ex_keys:
                        res_delta.append(key)
                raise NotMatch(
                        'Dictionary key mismatch:\n'
                        'Extra key(s) in template:\n%(ex_delta)s\n'
                        'Extra key(s) in result:\n%(res_delta)s\n' %
                        {'ex_delta': ex_delta, 'res_delta': res_delta})
            for key in ex_keys:
                res = self._compare(expected[key], result[key])
                matched_value = res or matched_value
        elif isinstance(expected, list):
            pass
        elif isinstance(expected, (six.integer_types, float,
                                   six.string_types)):
            pass

        return matched_value

    def _read_template(self, name):
        dirname = os.path.dirname(os.path.abspath(__file__))
        dirname = os.path.normpath(os.path.join(dirname,
                                   './api_templates'))

        template = ''.join([dirname, '/', name, '.tpl'])
        with open(template) as inf:
            return inf.read().strip()

    def _verify_result(self, expected, result):

        try:
            expected_json = make_json(expected)
            result_json = make_json(result)

            self._compare(expected_json, result_json)
        except NotMatch:
            raise NotMatch("\nFailed to match Template to Response: \n"
                           "Template: %s\n"
                           "Result: %s\n" %
                           (expected_json, result_json))

    def verify_result(self, test_name, result):
        result = bytes.decode(result)
        expected = self._read_template(test_name)
        return self._verify_result(expected, result)
