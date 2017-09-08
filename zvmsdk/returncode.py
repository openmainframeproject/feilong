# Return code definition for zVM SDK
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


"""
Each error corresponds to a dictionary contains: 'overallRC', 'rc', 'rs',
'strError'.
--'overallRC' is used to indicate the overall return code, all the errors are
    classified into group with different overallRC value.

-- 'rc' is used to indicate which module this error happens in. The available
    Module and their RC value to use is listed in the following:
    ModID    ModName    RC
    ------   ------     --
    GST      GUEST      10
    NET      NETWORK    20
    VLM      VOLUME     30
    IMG      IMAGE      40
    MNT      MONITOR    50
    SDB      DATABASE   60
    SMC      SMUTCLIENT 70
    SVR      SDKSERVER  100
    CLT      SDKCLIENT  110

-- 'rs' is used to indicate the specific error. It is defined specificly by
    each module. Different error inside a module should use different 'rs'
    value.

-- 'strError' is used to return the detail error despcription.

-------------------------------------------------------------------------------
ErrorCode General Classification
-------------------------------------------------------------------------------
ErrorClass          overallRC  rc     rs    Description

SMUT                  1-99     --     --     Used by SMUT, refer to
                                             smutlayer/msgs.py

Invalid input         100     100      1     SDK API parameter number error
                      100     100      2     SDK API input type error
                      100     100      3     SDK API parameter format error (
                                              value not in expected format or
                                              range)

Object Not Exist      104     MODRC    x     The operated object does not
                                             exist, eg, the guest/vswitch/
                                             image/volume.

Conflict              109     MODRC    x     The status of the to-be-updated
                                             object is conflict with the
                                             update request.

Object Deleted        110     MODRC    x     The operated object has been
                                             deleted and not exist any more.
                                             This can be used for some module
                                             that support deleted=1 in DB.

Invalid API name      200     SVRRC    x     The SDK server received a invalid
                                             API name.

Socket Error          210     MODRC    x     The SDK server or client socket
                                             error.

Other Module Error    300     MODRC    x     The module-specific error during
                                             SDK API handling that not belongs
                                             to other general module-shared
                                             error.

Internal error        400     MODRC    x     The SDK module got unexpected
                                             error, eg, typeerror, keyerror,
                                             etc. SDK  server would take all
                                             the exceptions not belonging to
                                             SDKBaseexception as InternalError
                                             .Such error generally means
                                             bug report, SDK code should avoid
                                             using this return code.

"""
# -----------------------------------------------------------------------------
# Detail Code definition of each error
# -----------------------------------------------------------------------------

ModRCs = {
    'guest': 10,
    'network': 20,
    'volume': 30,
    'image': 40,
    'monitor': 50,
    'database': 60,
    'smutclient': 70,
    'sdkserver': 100,
    'sdkclient': 110,
    'zvmsdk': 400
    }

errors = {
    # 0001-0499 is reserved for SMUT, so start from 0500 here
    # Each entry defined here corresponds to a kind of error indicated by the
    # following list of info:
    # 1. the dict of 'overallRC', 'rc'
    # 2. the dict containing all the possible rs and its error message
    # 3. The general error description. This should be used for doc generation

# Invalid input error
    '0500': [{'overallRC': 100, 'rc': 100},
             {1: ("API: '%(api)s', %(expected)d expected while %(provided)d"
                   "provided."),
              2: ("API: '%(api)s', expected types：'%(expected)s'"
                  "input types: '%(inputtypes)s'"),
              3: ("API: '%(api)s', parameter format error: %(msg)s")
              },
             "Invalid API Input",
             ],
# Internal error
# Module Internal error, rc is not defined here, it will be set when raising
# exception. when module id is not specified, the 'zvmsdk' module rc will be
# used.
    '0600': [{'overallRC': 400, 'rc': None},
             {1: "Unexpected internal error in ZVM SDK, error: %(msg)s"},
             "ZVM SDK Internal Error"
             ],
# General Errors for each module, same overallRC = 300
# Guest Operation failed
    '0700': [{'overallRC': 300, 'rc': ModRCs['guest']},
             {1: "Failed to add mdisks when creating guest, error: %(msg)s"},
             "Operation on Guest failed"
             ],
    }
