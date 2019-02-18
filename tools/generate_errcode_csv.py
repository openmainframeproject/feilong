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
from zvmconnector import restclient
from zvmconnector import socketclient
from zvmsdk import returncode


SDK_ERR_KEYS = (
    'input',
    'guest',
    'network',
    'volume',
    'image',
    'monitor',
    'RESTAPI',
    'notExist',
    'conflict',
    'deleted',
    'internal',
    'serviceUnavail',
)


def generate_errcode():
    _lines = []

    # add zvmsdk error codes and messages
    for k in SDK_ERR_KEYS:
        _error = returncode.errors[k]
        _lines.append('**' + _error[2] + '**\n')
        if _error[1] == {}:
            # no reason code (rs) defined
            _line = ';'.join((
                six.text_type(_error[0]['overallRC']),
                six.text_type(_error[0]['modID']),
                six.text_type(_error[0]['rc']),
                '',
                _error[2],
                ))
            _line += '\n'
            _lines.append(_line)
        else:
            for rs, errmsg in _error[1].items():
                _line = ';'.join((
                    six.text_type(_error[0]['overallRC']),
                    six.text_type(_error[0]['modID']),
                    six.text_type(_error[0]['rc']),
                    six.text_type(rs),
                    errmsg,
                    ))
                _line += '\n'
                _lines.append(_line)

    # add smut error codes and messages
    _lines.append('**' + "smut errors" + '**\n')
    _smut_orcs = {}
    _smut_errkeys = msgs.msg.keys()
    for k in sorted(_smut_errkeys):
        _orcs = msgs.msg[k]
        _orrc = _orcs[0].get('overallRC')
        if _smut_orcs.get(_orrc) is not None:
            _smut_orcs[_orrc].append(_orcs)
        else:
            _smut_orcs[_orrc] = [_orcs]

    orcs = _smut_orcs.keys()
    for orc in sorted(orcs):
        for _msg in _smut_orcs[orc]:
            _orc = _msg[0].get('overallRC')
            _mid = '1'
            _rc = _msg[0].get('rc')
            _rs = _msg[0].get('rs')
            _err = _msg[1].replace('%i', '%s') % _msg[2]
            _line = ';'.join((
                    six.text_type(_orc),
                    six.text_type(_mid),
                    six.text_type(_rc),
                    six.text_type(_rs),
                    six.text_type(_err),
                    ))
            _line += '\n'
            _lines.append(_line)

    # add client error codes and messages
    _lines.append('**' + "client errors" + '**\n')
    # add restclient errors
    for rs, errmsg in restclient.REST_REQUEST_ERROR[1].items():
        _line = ';'.join((
            six.text_type(restclient.REST_REQUEST_ERROR[0]['overallRC']),
            six.text_type(restclient.REST_REQUEST_ERROR[0]['modID']),
            six.text_type(restclient.REST_REQUEST_ERROR[0]['rc']),
            six.text_type(rs),
            errmsg,
            ))
        _line += '\n'
        _lines.append(_line)
    # add socketclient errors
    for rs, errmsg in socketclient.SOCKET_ERROR[1].items():
        _line = ';'.join((
            six.text_type(socketclient.SOCKET_ERROR[0]['overallRC']),
            six.text_type(socketclient.SOCKET_ERROR[0]['modID']),
            six.text_type(socketclient.SOCKET_ERROR[0]['rc']),
            six.text_type(rs),
            errmsg,
            ))
        _line += '\n'
        _lines.append(_line)
    # add invalid api client errors
    _lines.append(';'.join((
        six.text_type(restclient.INVALID_API_ERROR[0]['overallRC']),
        six.text_type(restclient.INVALID_API_ERROR[0]['modID']),
        six.text_type(restclient.INVALID_API_ERROR[0]['rc']),
        '1',
        six.text_type(restclient.INVALID_API_ERROR[1][1]),
        )) + '\n')
    # add service unavailable error
    _lines.append(';'.join((
        six.text_type(restclient.SERVICE_UNAVAILABLE_ERROR[0]['overallRC']),
        six.text_type(restclient.SERVICE_UNAVAILABLE_ERROR[0]['modID']),
        six.text_type(restclient.SERVICE_UNAVAILABLE_ERROR[0]['rc']),
        '2',
        six.text_type(restclient.SERVICE_UNAVAILABLE_ERROR[1][2]),
        )) + '\n')

    return _lines


if __name__ == "__main__":
    csv_file = "./errcode.csv"
    err_codes = generate_errcode()
    with open(csv_file, 'w') as f:
        f.writelines(err_codes)
