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


__all__ = ['__version__']
__version__ = '0.3.0'


# Check supported Python versions
_PYTHON_M = sys.version_info[0]
_PYTHON_N = sys.version_info[1]
if _PYTHON_M == 2 and _PYTHON_N < 7:
    raise RuntimeError('On Python 2, zvm sdk requires Python 2.7')
elif _PYTHON_M == 3:
    raise RuntimeError('On Python 3, zhm sdk does not support now')
