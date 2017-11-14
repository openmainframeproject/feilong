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


import six

from smutLayer import msgs
from zvmsdk import returncode


def generate_errcode():
    _lines = []

    # add zvmsdk error codes and messages
    for k in returncode.errors.keys():
        _error = returncode.errors[k]
        _lines.append('**' + _error[2] + '**\n')
        if _error[1] == {}:
            # no reason code (rs) defined
            _line = ';'.join((
                six.text_type(_error[0]['overallRC']),
                six.text_type(_error[0]['rc']),
                '',
                _error[2],
                '\n',
                ))
            _lines.append(_line)
        else:
            for rs, errmsg in _error[1].items():
                _line = ';'.join((
                    six.text_type(_error[0]['overallRC']),
                    six.text_type(_error[0]['rc']),
                    six.text_type(rs),
                    errmsg,
                    '\n',
                    ))
                _lines.append(_line)

    # add smut error codes and messages
    _lines.append('**' + "smut errors" + '**\n')
    for _msg in msgs.msg.values():
        _orc = _msg[0].get('overallRC')
        _rc = _msg[0].get('rc', '')
        _rs = _msg[0].get('rs', '')
        _err = _msg[1]
        _line = ';'.join((
                six.text_type(_orc),
                six.text_type(_rc),
                six.text_type(_rs),
                six.text_type(_err),
                '\n',
                ))
        _lines.append(_line)

    return _lines


if __name__ == "__main__":
    csv_file = "./errcode.csv"
    err_codes = generate_errcode()
    with open(csv_file, 'w') as f:
        f.writelines(err_codes)
