#!/usr/bin/env python
# Command line processor for Systems Management Ultra Thin Layer
#
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

from smut import SMUT
from ReqHandle import ReqHandle

version = '1.0.0'         # Version of this script

"""
******************************************************************************
 main routine
******************************************************************************
"""
useSMUT = True
if useSMUT:
    results = SMUT(cmdName=sys.argv[0]).request(sys.argv[1:], captureLogs=True)
else:
    reqHandle = ReqHandle(cmdName=sys.argv[0], captureLogs=True)
    results = reqHandle.parseCmdline(sys.argv[1:])

    if results['overallRC'] == 0:
        results = reqHandle.driveFunction()

# On error, show the result codes (overall rc, rc, rs, ...)
if results['overallRC'] != 0:
    print("overall rc: " + str(results['overallRC']))
    print("        rc: " + str(results['rc']))
    print("        rs: " + str(results['rs']))
    print("     errno: " + str(results['errno']))
    print("  strError: " + str(results['strError']))
    print("")
    print("Response:")

# Show the response lines
if len(results['response']) != 0:
    for line in results['response']:
        print(line)
elif results['overallRC'] == 0:
    print("Command succeeded.")

# On error, show the trace log.
if results['overallRC'] != 0:
    print("")
    print("Trace Log:")
    for line in results['logEntries']:
        print(line)

if results['overallRC'] != 0:
    exit(results['overallRC'])
