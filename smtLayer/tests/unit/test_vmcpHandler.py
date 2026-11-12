#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2026 IBM Corp.
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

import re
import subprocess
from unittest import mock

from smtLayer import msgs
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import (
    ALREADY_LOGGED_ON_PATTERN,
    NOT_ATTACHED_PATTERN,
    NOT_LOGGED_ON_PATTERN,
    VMCPHandler)
from zvmsdk import exception

# Output of "sudo vmcp QUERY FRAMES" (rc=0) captured on a real z/VM host.
# Layout is exactly as CP printed it, including the trailing blank (\x20)
# after some lines.
QUERY_FRAMES_REAL = """\
All Frames:
   Configured=134217728  Real=134217728  Usable=134217728  Offline=0
   Pageable=132798942  NotInitialized=0  GlobalClearedAvail=17
   LocalClearedAvail=64  LocalUnclearedAvail=60
   LockedPageable=0% LockedWarning=50% LockedFail=90%
   IOATSize=262144 IOATUsed=0% IOATMaxused=0% IOATWarning=50%
   Permanent=134217728 Reconfigurable=0 Vacating=0\x20

Frames < 2G:
   GlobalUnclearedAvail=308081  Pageable=509992  LogicalFreeStorage=1140
   RealFreeStorage=4  LockedRS=29  LockedCmd=0
   MinidiskCache=0  Nucleus/Prefix=3803  Trace=3100  Other=6220\x20

Frames > 2G:
   GlobalUnclearedAvail=97473280  Pageable=132288950  LogicalFreeStorage=1483
   RealFreeStorage=7033  LockedRS=3202  LockedCmd=0
   MinidiskCache=0  Other=1392772\x20
"""

# Output of "sudo vmcp QUERY SSI" (rc=0) captured on a real z/VM host that is
# not a member of an SSI cluster.
QUERY_SSI_NOT_IN_CLUSTER_REAL = """\
This system is not a member of an SSI cluster.
"""

# Output of "sudo /sbin/vmcp --buffer=1M QUERY VSWITCH DETAILS" (rc=0)
# captured on a real z/VM host with 4 vswitches: VSICIC has 21 guest NICs
# (one without any RX/TX lines), VSICICA has none, and the uplink ports of
# VMTCPIP/VSICIC/VSICICA print their own "RX Packets" lines before the
# "Adapter Connections:" section. The single blank (\x20) line between the
# vswitches is exactly as CP printed it.
QUERY_VSWITCH_DETAILS_REAL = """\
VSWITCH SYSTEM DTCSMAPI   Type: QDIO    Connected: 2    Maxconn: INFINITE
  PERSISTENT  RESTRICTED    ETHERNET                  Accounting: OFF
  USERBASED LOCAL
  VLAN Unaware
  MAC address: 02-01-78-00-00-06    MAC Protection: Unspecified
  IPTimeout: 5   QueueStorage Range: 8-256M     Current: None
  Isolation Status: OFF        VEPA Status: OFF
  Unicast IP address count: 2
 Uplink Port:
  State: Defined                       PriQueuing: OFF
  PMTUD setting: EXTERNAL   PMTUD value: 65535    Trace Pages: 8
  LOG: Off
 Adapter Connections:                            Connected: 2
    Adapter Owner: DTCSMAPI NIC: 0100.P00 Name: UNASSIGNED  Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 5993       Discarded: 0          Errors: 0
      TX Packets: 6904       Discarded: 0          Errors: 0
      RX Bytes: 481691               TX Bytes: 1251132
      Device: 0100  Unit: 000   Role: DATA       Port: 2176
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-00-00-0F IP: 10.60.100.100
        Multicast MAC Addresses:
          01-00-5E-00-00-01
    Adapter Owner: LOHCOST  NIC: F000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 10310      Discarded: 0          Errors: 0
      TX Packets: 8820       Discarded: 979        Errors: 0
      RX Bytes: 2126094              TX Bytes: 750529
      Device: F002  Unit: 002   Role: DATA       Port: 2177
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-00-00-08 IP: 10.70.100.100
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-00-00-08
\x20
VSWITCH SYSTEM VMTCPIP    Type: QDIO    Connected: 1    Maxconn: INFINITE
  PERSISTENT  RESTRICTED    ETHERNET                  Accounting: OFF
  USERBASED LOCAL
  VLAN Unaware
  MAC address: 02-01-78-00-00-01    MAC Protection: Unspecified
  IPTimeout: 5   QueueStorage Range: 8-256M     Current: 8M
  Isolation Status: OFF        VEPA Status: OFF
  Unicast IP address count: 1
 Uplink Port:
  State: Ready                         PriQueuing: OFF
  PMTUD setting: EXTERNAL   PMTUD value: 9000     Trace Pages: 8
  LOG: Off
  RDEV: 3000.P00 VDEV: 3000 Controller: SYSTEM   ACTIVE
        Adapter ID: 9175000C5BA8.0174
    Uplink Port Connection:
      RX Packets: 296203011  Discarded: 0          Errors: 0
      TX Packets: 38151      Discarded: 0          Errors: 0
      RX Bytes: 27058622185          TX Bytes: 14939428
      Device: 3000  Unit: 000   Interface: Activated   Port: 2049
      Options: Ethernet
      Partner Switch Capabilities: No_Reflective_Relay
  RDEV: 3100.P00 VDEV: 3100 Controller: SYSTEM   BACKUP
        Adapter ID: 9175000C5BA8.0288
    Uplink Port Connection:
      RX Packets: 0          Discarded: 0          Errors: 0
      TX Packets: 0          Discarded: 0          Errors: 0
      RX Bytes: 0                    TX Bytes: 0
      Device: 3100  Unit: 000   Interface: Inactive    Port: 2050
      Options: Ethernet
 Adapter Connections:                            Connected: 1
    Adapter Owner: TCPIP    NIC: BD00.P00 Name: UNASSIGNED  Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 296203586  Discarded: 0          Errors: 0
      TX Packets: 38150      Discarded: 0          Errors: 0
      RX Bytes: 27058702105          TX Bytes: 14939368
      Device: BD00  Unit: 000   Role: DATA       Port: 2176
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-00-00-04 IP: 172.26.1.120
        Multicast MAC Addresses:
          01-00-5E-00-00-01
\x20
VSWITCH SYSTEM VSICIC     Type: QDIO    Connected: 21   Maxconn: INFINITE
  PERSISTENT  RESTRICTED    ETHERNET                  Accounting: OFF
  USERBASED LOCAL
  VLAN Unaware
  MAC address: 02-01-78-00-00-02    MAC Protection: Unspecified
  IPTimeout: 5   QueueStorage Range: 8-256M     Current: 8M
  Isolation Status: OFF        VEPA Status: OFF
  Unicast IP address count: 20
 Uplink Port:
  State: Ready                         PriQueuing: OFF
  PMTUD setting: EXTERNAL   PMTUD value: 9000     Trace Pages: 8
  LOG: Off
  RDEV: 3001.P00 VDEV: 3001 Controller: SYSTEM   ACTIVE
        Adapter ID: 9175000C5BA8.0174
    Uplink Port Connection:
      RX Packets: 685601513  Discarded: 0          Errors: 0
      TX Packets: 236207705  Discarded: 0          Errors: 0
      RX Bytes: 358052229239         TX Bytes: 85249751597
      Device: 3001  Unit: 000   Interface: Activated   Port: 2049
      Options: Ethernet
      Partner Switch Capabilities: No_Reflective_Relay
  RDEV: 3101.P00 VDEV: 3101 Controller: SYSTEM   BACKUP
        Adapter ID: 9175000C5BA8.0288
    Uplink Port Connection:
      RX Packets: 0          Discarded: 0          Errors: 0
      TX Packets: 0          Discarded: 0          Errors: 0
      RX Bytes: 0                    TX Bytes: 0
      Device: 3101  Unit: 000   Interface: Inactive    Port: 2050
      Options: Ethernet
 Adapter Connections:                            Connected: 21
    Adapter Owner: B4904CPT NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 314253570  Discarded: 0          Errors: 0
      TX Packets: 13838885   Discarded: 0          Errors: 0
      RX Bytes: 39837695192          TX Bytes: 6827275465
      Device: 1002  Unit: 002   Role: DATA       Port: 2176
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-00-00-05 IP: 172.26.1.233
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          01-00-5E-00-00-FB
          33-33-00-00-00-01
          33-33-00-00-00-FB
          33-33-FF-00-00-05
    Adapter Owner: IIMD00BC NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 321346817  Discarded: 11         Errors: 0
      TX Packets: 24386487   Discarded: 0          Errors: 0
      RX Bytes: 52355419358          TX Bytes: 22867222781
      Device: 1002  Unit: 002   Role: DATA       Port: 2219
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-B8-86-64 IP: 172.26.11.139
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-B8-86-64
    Adapter Owner: IIMD00BD NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 296171003  Discarded: 0          Errors: 0
      TX Packets: 13222      Discarded: 0          Errors: 0
      RX Bytes: 27059637629          TX Bytes: 1290460
      Device: 1002  Unit: 002   Role: DATA       Port: 2220
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-81-93-97 IP: 172.26.11.155
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-81-93-97
    Adapter Owner: IIMD00B3 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 338005268  Discarded: 5          Errors: 0
      TX Packets: 34415411   Discarded: 0          Errors: 0
      RX Bytes: 47746983789          TX Bytes: 10806676192
      Device: 1002  Unit: 002   Role: DATA       Port: 2203
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-AA-9D-E2 IP: 172.26.11.196
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-AA-9D-E2
    Adapter Owner: IIMD00B5 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 309746245  Discarded: 9          Errors: 0
      TX Packets: 11844574   Discarded: 0          Errors: 0
      RX Bytes: 32936451153          TX Bytes: 4066469281
      Device: 1002  Unit: 002   Role: DATA       Port: 2208
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-F0-65-F4 IP: 172.26.11.130
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-F0-65-F4
    Adapter Owner: IIMD00FC NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 201423310  Discarded: 5          Errors: 0
      TX Packets: 14789078   Discarded: 0          Errors: 0
      RX Bytes: 25476027104          TX Bytes: 4839954153
      Device: 1002  Unit: 002   Role: DATA       Port: 2225
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-F9-7F-FA IP: 172.26.11.152
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-F9-7F-FA
    Adapter Owner: IIMD001D NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 308303407  Discarded: 5          Errors: 0
      TX Packets: 9103208    Discarded: 0          Errors: 0
      RX Bytes: 34857787254          TX Bytes: 3054925557
      Device: 1002  Unit: 002   Role: DATA       Port: 2182
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-87-38-CD IP: 172.26.11.50
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-87-38-CD
    Adapter Owner: IIMD0018 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 301339872  Discarded: 0          Errors: 0
      TX Packets: 6832653    Discarded: 0          Errors: 0
      RX Bytes: 27824032795          TX Bytes: 823270536
      Device: 1002  Unit: 002   Role: DATA       Port: 2180
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-97-7E-03 IP: 172.26.11.118
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-97-7E-03
    Adapter Owner: IIMD0019 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 386042486  Discarded: 185        Errors: 0
      TX Packets: 29587725   Discarded: 0          Errors: 0
      RX Bytes: 132064004557         TX Bytes: 10150833862
      Device: 1002  Unit: 002   Role: DATA       Port: 2181
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-1E-EC-C9 IP: 172.26.11.61
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-1E-EC-C9
    Adapter Owner: IIMD002B NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 296201385  Discarded: 0          Errors: 0
      TX Packets: 47032      Discarded: 0          Errors: 0
      RX Bytes: 27059345012          TX Bytes: 3056856
      Device: 1002  Unit: 002   Role: DATA       Port: 2186
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-9C-C5-A4 IP: 172.26.11.216
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-9C-C5-A4
    Adapter Owner: IIMD002C NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 297562908  Discarded: 0          Errors: 0
      TX Packets: 1401434    Discarded: 0          Errors: 0
      RX Bytes: 27342187495          TX Bytes: 247598850
      Device: 1002  Unit: 002   Role: DATA       Port: 2187
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-EC-59-8A IP: 172.26.11.254
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-EC-59-8A
    Adapter Owner: IIMD002D NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 297187074  Discarded: 4          Errors: 0
      TX Packets: 1111077    Discarded: 0          Errors: 0
      RX Bytes: 27525805652          TX Bytes: 135779852
      Device: 1002  Unit: 002   Role: DATA       Port: 2188
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-8F-9D-86 IP: 172.26.11.93
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-8F-9D-86
    Adapter Owner: IIMD002E NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 296435407  Discarded: 6          Errors: 0
      TX Packets: 284691     Discarded: 0          Errors: 0
      RX Bytes: 27086065783          TX Bytes: 16683304
      Device: 1002  Unit: 002   Role: DATA       Port: 2189
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-47-CC-DB IP: 172.26.11.58
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-47-CC-DB
    Adapter Owner: IIMD0024 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 297160896  Discarded: 1          Errors: 0
      TX Packets: 1609997    Discarded: 0          Errors: 0
      RX Bytes: 28145784570          TX Bytes: 2089093153
      Device: 1002  Unit: 002   Role: DATA       Port: 2185
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-54-63-01 IP: 172.26.11.16
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-54-63-01
    Adapter Owner: MALR000A NIC: 1000.P00 Name: UNASSIGNED  Type: QDIO
      PQUplinkTX: Normal
      Port: 2234
    Adapter Owner: MALR002E NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 112642709  Discarded: 0          Errors: 0
      TX Packets: 28232      Discarded: 0          Errors: 0
      RX Bytes: 10654819525          TX Bytes: 1909155
      Device: 1002  Unit: 002   Role: DATA       Port: 2256
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-6B-EA-01 IP: 172.26.40.119
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-6B-EA-01
    Adapter Owner: MALR0031 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 112258530  Discarded: 0          Errors: 0
      TX Packets: 18335      Discarded: 0          Errors: 0
      RX Bytes: 10619568163          TX Bytes: 1217439
      Device: 1002  Unit: 002   Role: DATA       Port: 2258
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-28-94-52 IP: 172.26.40.118
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-28-94-52
    Adapter Owner: RACH0013 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 94789234   Discarded: 0          Errors: 0
      TX Packets: 16714      Discarded: 0          Errors: 0
      RX Bytes: 9001901313           TX Bytes: 1091995
      Device: 1002  Unit: 002   Role: DATA       Port: 2272
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-FF-4D-B2 IP: 172.26.33.200
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-FF-4D-B2
    Adapter Owner: RAJA0023 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 191255088  Discarded: 0          Errors: 0
      TX Packets: 45872      Discarded: 0          Errors: 0
      RX Bytes: 17846965024          TX Bytes: 3063700
      Device: 1002  Unit: 002   Role: DATA       Port: 2237
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-AA-8B-1C IP: 172.26.59.230
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-AA-8B-1C
    Adapter Owner: SSAN0061 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 296158905  Discarded: 0          Errors: 0
      TX Packets: 13058      Discarded: 0          Errors: 0
      RX Bytes: 27053730489          TX Bytes: 1064424
      Device: 1002  Unit: 002   Role: DATA       Port: 2224
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-AE-84-75 IP: 172.26.55.136
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-AE-84-75
    Adapter Owner: SSAN0077 NIC: 1000.P00 Name: HYD1G1      Type: QDIO
      PQUplinkTX: Normal
      RX Packets: 62393168   Discarded: 0          Errors: 0
      TX Packets: 17268      Discarded: 0          Errors: 0
      RX Bytes: 5984543616           TX Bytes: 1217983
      Device: 1002  Unit: 002   Role: DATA       Port: 2273
      Options: Ethernet Broadcast
        Unicast MAC Addresses:
          02-01-78-53-74-EB IP: 172.26.55.131
        Multicast MAC Addresses:
          01-00-5E-00-00-01
          33-33-00-00-00-01
          33-33-FF-53-74-EB
\x20
VSWITCH SYSTEM VSICICA    Type: QDIO    Connected: 0    Maxconn: INFINITE
  PERSISTENT  RESTRICTED    ETHERNET                  Accounting: OFF
  USERBASED LOCAL
  VLAN Aware  Default VLAN: NONE    Default Porttype: Access  GVRP: Disabled
              Native  VLAN: 0001    VLAN Counters: OFF
  MAC address: 02-01-78-00-00-03    MAC Protection: Unspecified
  IPTimeout: 5   QueueStorage Range: 8-256M     Current: 8M
  Isolation Status: OFF        VEPA Status: OFF
  Unicast IP address count: 0
 Uplink Port:
  State: Ready                         PriQueuing: OFF
  PMTUD setting: EXTERNAL   PMTUD value: 9000     Trace Pages: 8
  LOG: Off
  RDEV: 7200.P00 VDEV: 7200 Controller: SYSTEM   ACTIVE
        Adapter ID: 9175000C5BA8.0284
    Uplink Port Connection:
      RX Packets: 0          Discarded: 0          Errors: 0
      TX Packets: 0          Discarded: 0          Errors: 0
      RX Bytes: 0                    TX Bytes: 0
      Device: 7200  Unit: 000   Interface: Activated   Port: 2049
      Options: Ethernet
      Partner Switch Capabilities: No_Reflective_Relay
"""


def _make_rh():
    """Return a lightweight mock ReqHandle."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.userid = "TESTUSER"
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': []}
    return rh


class VMCPHandlerTest(base.SMTTestCase):

    def test_init_stores_rh(self):
        rh = _make_rh()
        handler = VMCPHandler(rh)
        self.assertIs(rh, handler._rh)

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('subprocess.check_output', return_value=b"OK OUTPUT\n")
    def test_run_success_rc_0(self, _mock):
        result = self.handler._run(["query", "userid"])
        self.assertEqual(0, result["overallRC"])
        self.assertEqual("OK OUTPUT\n", result["response"])

    @mock.patch('subprocess.check_output', return_value=b"")
    def test_run_builds_correct_command(self, mock_check):
        self.handler._run(["query", "pcif"])
        mock_check.assert_called_once_with(
            ["sudo", "/sbin/vmcp", "query", "pcif"],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_returns_nonzero_rc(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=8, cmd="vmcp", output=b"error")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(8, result["overallRC"])
        self.assertEqual("", result["response"])

    @mock.patch('subprocess.check_output', return_value=b"OK \xff DONE\n")
    def test_run_success_survives_invalid_utf8(self, _mock):
        result = self.handler._run(["query", "userid"])
        self.assertEqual(0, result["overallRC"])
        self.assertIn("OK", result["response"])
        self.assertIn("DONE", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_tolerated_survives_invalid_utf8(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b"HCP040E \xff not attached")
        result = self.handler._run(
            ["FOR", "TESTUSER", "CMD", "DETACH", "0100"],
            tolerated=NOT_ATTACHED_PATTERN)
        self.assertEqual(0, result["overallRC"])
        self.assertIn("HCP040E", result["response"])
        self.rh.updateResults.assert_not_called()

    @mock.patch('subprocess.check_output')
    def test_run_output_true_survives_invalid_utf8(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b"HCP045E \xff not logged on")
        result = self.handler._run(["query", "userid"], output=True)
        self.assertEqual(1, result["overallRC"])
        self.assertIn("HCP045E", result["output"])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_updates_results(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"err")
        self.handler._run(["query", "pcif"])
        self.rh.updateResults.assert_called_once_with(msgs.msg['0405'][0])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_message_is_decoded(self, mock_check):
        # Invalid UTF-8 byte must not break decoding.
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"HCP err \xff")
        self.handler._run(["query", "pcif"])
        printed = self.rh.printLn.call_args[0][1]
        self.assertIn("HCP err", printed)
        self.assertNotIn("b'", printed)

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception_returns_rc_1(self, mock_check):
        mock_check.side_effect = OSError("not found")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(1, result["overallRC"])
        self.assertEqual("", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception_updates_results(self, mock_check):
        mock_check.side_effect = RuntimeError("boom")
        self.handler._run(["query", "pcif"])
        self.rh.updateResults.assert_called_once_with(msgs.msg['0421'][0])

    def _patch_run(self, response, rc=0):
        return mock.patch.object(
            self.handler, '_run',
            return_value={"response": response, "overallRC": rc},
        )

    def test_attached_enabled_line(self):
        output = "PCIF 00000110 ATTACHED TO MALR003F 00000110 ENABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(1, len(result))
        self.assertEqual({"pcif": "00000110", "status": "ATTACHED",
                          "userid": "MALR003F", "state": "ENABLED",
                          "type": "NETH"}, result[0])

    def test_free_enabled_line(self):
        output = "PCIF 00000120 FREE ENABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(1, len(result))
        self.assertEqual({"pcif": "00000120", "status": "FREE",
                          "userid": "", "state": "ENABLED",
                          "type": "NETH"}, result[0])

    def test_attached_disabled_line(self):
        output = "PCIF 00000130 ATTACHED TO TESTVM 00000130 DISABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        entry = result[0]
        self.assertEqual("DISABLED", entry["state"])
        self.assertEqual("TESTVM", entry["userid"])

    def test_multiple_lines_all_returned(self):
        output = (
            "PCIF 00000110 ATTACHED TO VM001 00000110 ENABLED NETH\n"
            "PCIF 00000120 FREE ENABLED NETH\n"
            "PCIF 00000130 FREE DISABLED NETH\n"
        )
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(3, len(result))

    def test_calls_run_with_query_pcif_args(self):
        with self._patch_run("") as mock_run:
            self.handler.query_pcif()
        mock_run.assert_called_once_with(["query", "pcif"])

    def test_run_failure_raises(self):
        # _run() records the failure in rh.results; query_pcif raises.
        with self._patch_run("", rc=8):
            with self.assertRaises(exception.SDKSMTRequestFailed) as cm:
                self.handler.query_pcif()
        self.assertIs(self.rh.results, cm.exception.results)

    def test_returns_empty_list_on_empty_output(self):
        with self._patch_run(""):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_pci_function_not_found_raises(self):
        with self._patch_run("A PCI function was not found.\n"):
            with self.assertRaises(exception.SDKSMTRequestFailed) as cm:
                self.handler.query_pcif()
        self.assertIs(self.rh.results, cm.exception.results)
        self.rh.updateResults.assert_called_once_with(msgs.msg['0405'][0])

    def test_pci_function_not_found_with_rc_nonzero_is_run_failure(self):
        # A failing vmcp raises as a run failure; the "not found" handling
        # (which records msg 0405 itself) is not applied.
        with self._patch_run("A PCI function was not found.\n", rc=8):
            with self.assertRaises(exception.SDKSMTRequestFailed):
                self.handler.query_pcif()
        self.rh.updateResults.assert_not_called()

    def test_pcif_at_end_of_line_skipped(self):
        # no device number after PCIF
        output = "SOMETHING PCIF\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_missing_state_token_skipped(self):
        # no ENABLED / DISABLED
        output = "PCIF 00000110 FREE NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_no_type_after_state_skipped(self):
        # ENABLED is the last token
        output = "PCIF 00000110 FREE ENABLED\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_query_storage_success(self):
        output = "STORAGE = 65536M  STANDBY = 0  REMAINDER = 0"
        with self._patch_run(output, rc=0) as mock_run:
            result = self.handler.query_storage()
            mock_run.assert_called_once_with(["query", "storage"])
            self.assertEqual("65536M", result["lparMemTotal"])
            self.assertEqual("0", result["lparMemStandby"])

    def test_query_storage_missing_standby(self):
        output = "STORAGE = 32G"
        with self._patch_run(output, rc=0):
            result = self.handler.query_storage()
            self.assertEqual("32G", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_storage_malformed_output(self):
        output = "STORAGE"
        with self._patch_run(output, rc=0):
            result = self.handler.query_storage()
            self.assertEqual("no info", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_storage_error_rc(self):
        with self._patch_run("", rc=1):
            result = self.handler.query_storage()
            self.assertEqual("no info", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_cplevel_success(self):
        output = "z/VM Version 7 Release 2.0 00/00/00 (64-bit)\nIPL at 01/15/24 08:30:00 EST\n"
        with self._patch_run(output, rc=0) as mock_run:
            ipl = self.handler.query_cplevel()
            mock_run.assert_called_once_with(["query", "cplevel"])
            self.assertEqual("IPL at 01/15/24 08:30:00 EST", ipl)

    def test_query_cplevel_no_ipl_line(self):
        output = "z/VM Version 7 Release 2.0 00/00/00 (64-bit)\n"
        with self._patch_run(output, rc=0):
            ipl = self.handler.query_cplevel()
            self.assertEqual("", ipl)

    def test_query_cplevel_error_rc(self):
        with self._patch_run("", rc=1):
            ipl = self.handler.query_cplevel()
            self.assertEqual("", ipl)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_not_logged_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_not_called()
            self.rh.updateResults.assert_called_once_with(
                {'overallRC': 0, 'rc': 0, 'rs': 0})
            self.assertEqual({"response": "", "overallRC": 0}, result)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_no_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER", force=False)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_with_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER", force=True)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff", "IMMED"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_is_logged_on_failed_acts_as_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 1, 'rc': 1, 'rs': 1}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_uses_userid_arg_not_rh_userid(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        self.assertEqual("TESTUSER", self.rh.userid)
        with self._patch_run("", rc=0) as mock_run:
            self.handler.deactivate("OTHERUSR", force=True)
            mock_is_logged_on.assert_called_once_with(self.rh, "OTHERUSR")
            mock_run.assert_called_once_with(
                ["force", "OTHERUSR", "logoff", "IMMED"],
                tolerated=mock.ANY)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_run_returns_failure_rc(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=8) as mock_run:
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(8, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_tolerates_not_logged_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.deactivate("TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=NOT_LOGGED_ON_PATTERN)

    def test_not_logged_on_pattern_matches_expected_messages(self):
        # HCP045E / HCP361E mean the guest is already logged off.
        for msg in ("HCPCMD045E TESTUSER not logged on",
                    "HCPUSR361E TESTUSER not logged on",
                    "HCPFRC045E TESTUSER not logged on"):
            self.assertTrue(re.search(NOT_LOGGED_ON_PATTERN, msg), msg)
        self.assertIsNone(re.search(NOT_LOGGED_ON_PATTERN,
                                    "HCPCMD054E TESTUSER already logged on"))

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_failure_already_recorded_not_overwritten(
            self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        self.rh.results['overallRC'] = 99
        with self._patch_run("", rc=1):
            result = self.handler.deactivate("TESTUSER")
            self.assertEqual(1, result['overallRC'])
            self.rh.updateResults.assert_not_called()


class VMCPHandlerRunForTestCase(base.SMTTestCase):
    """Tests for VMCPHandler._run_for()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('subprocess.check_output')
    def test_run_for_success(self, mock_co):
        mock_co.return_value = b'NIC 0600 TYPE QDIO\n'
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(0, result['overallRC'])
        self.assertEqual(0, result['rc'])
        self.assertIn('NIC', result['response'])
        mock_co.assert_called_once_with(
            ['sudo', '/sbin/vmcp',
             'FOR TESTUSER CMD DEFINE NIC 0600 TYPE QDIO'],
            close_fds=True, stderr=subprocess.STDOUT)

    @mock.patch('subprocess.check_output')
    def test_run_for_calledprocesserror(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b'HCP045E')
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(1, result['overallRC'])
        self.assertEqual(1, result['rc'])
        self.assertEqual('HCP045E', result['strError'])

    @mock.patch('subprocess.check_output')
    def test_run_for_survives_invalid_utf8(self, mock_co):
        mock_co.return_value = b'OK \xff DONE\n'
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(0, result['overallRC'])
        self.assertIn('DONE', result['response'])

    @mock.patch('subprocess.check_output')
    def test_run_for_error_survives_invalid_utf8(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b'HCP045E \xff')
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(1, result['overallRC'])
        self.assertIn('HCP045E', result['strError'])

    @mock.patch('subprocess.check_output')
    def test_run_for_generic_exception(self, mock_co):
        mock_co.side_effect = OSError('vmcp not found')
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('vmcp not found', result['strError'])


class VMCPHandlerGetCPUCountTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.get_cpu_count()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_success(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': (
                'PROCESSOR 0000 MASTER IFL  CORE 0000\n'
                'PROCESSOR 0001 ALTERNATE IFL  CORE 0000\n'
                'PROCESSOR 0002 PARKED IFL  CORE 0001\n'
                'PROCESSOR 0003 STANDBY IFL  CORE 0001\n'
                'PARTITION MODE LINUX-ONLY\n'
            )
        }
        total, used = self.handler.get_cpu_count()
        self.assertEqual(4, total)
        self.assertEqual(3, used)
        mock_run.assert_called_once_with(['QUERY', 'PROCESSORS', 'EXPANDED'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_vmcp_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        total, used = self.handler.get_cpu_count()
        self.assertEqual(0, total)
        self.assertEqual(0, used)

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_no_processors(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': 'PARTITION MODE: Z/VM\n'
        }
        total, used = self.handler.get_cpu_count()
        self.assertEqual(0, total)
        self.assertEqual(0, used)


class VMCPHandlerPurgeReaderTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.purge_reader()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_purge_reader_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': ''}
        result = self.handler.purge_reader()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['PURGE', 'TESTUSER', 'RDR', 'ALL'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_purge_reader_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.purge_reader()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerCreateNICTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.create_nic_for_guest()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_success(self, mock_run_for, mock_run):
        mock_run_for.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': 'NIC 0600 DEFINED'
        }
        mock_run.return_value = {'overallRC': 0, 'response': 'NIC 0600 TYPE QDIO'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(0, result['overallRC'])
        mock_run_for.assert_called_once_with(
            'TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        mock_run.assert_called_once_with(
            ['QUERY', 'NIC', 'USERID', 'TESTUSER', '0600'])

    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_define_fails(self, mock_run_for):
        mock_run_for.return_value = {
            'overallRC': 1, 'rc': 1, 'rs': 0, 'errno': 0,
            'strError': 'HCP045E', 'response': 'HCP045E'
        }
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(1, result['overallRC'])

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_verify_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': ''
        }
        mock_run.return_value = {'overallRC': 1, 'response': 'NIC not found'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(2, result['overallRC'])
        self.assertTrue(result.get('nic_not_created'))


class VMCPHandlerQueryOSATestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_osa()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_attached_and_free(self, mock_run):
        mock_run.side_effect = [
            {
                'overallRC': 0,
                'response': (
                    'OSA  3000 ATTACHED TO SYSTEM   3000 DEVTYPE OSH         CHPID 70 OSH TRACESIZE 0008\n'
                    'OSA  3001 ATTACHED TO SYSTEM   3001 DEVTYPE OSH         CHPID 70 OSH TRACESIZE 0008\n'
                )
            },
            {
                'overallRC': 0,
                'response': 'OSA   3002 FREE    , OSA   3003 FREE    , OSA   3004 FREE\n'
            }
        ]
        result = self.handler.query_osa()
        self.assertIn('OSA', result)
        self.assertEqual(2, len(result['OSA']['ATTACHED']))
        self.assertIn(('SYSTEM', '3000'), result['OSA']['ATTACHED'])
        self.assertIn(('SYSTEM', '3001'), result['OSA']['ATTACHED'])
        self.assertIn('3002', result['OSA']['FREE'])
        self.assertIn('3003', result['OSA']['FREE'])
        self.assertIn('3004', result['OSA']['FREE'])
        mock_run.assert_any_call(['QUERY', 'OSA'])
        mock_run.assert_any_call(['QUERY', 'OSA', 'FREE'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_query_osa_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        result = self.handler.query_osa()
        self.assertEqual({}, result)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_no_osa(self, mock_run):
        mock_run.side_effect = [
            {'overallRC': 0, 'response': ''},
            {'overallRC': 0, 'response': ''}
        ]
        result = self.handler.query_osa()
        self.assertEqual({}, result)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_free_fails_gracefully(self, mock_run):
        mock_run.side_effect = [
            {
                'overallRC': 0,
                'response': 'OSA  3000 ATTACHED TO SYSTEM   3000 DEVTYPE OSH CHPID 70\n'
            },
            {'overallRC': 1, 'response': ''}
        ]
        result = self.handler.query_osa()
        self.assertIn('OSA', result)
        self.assertEqual(1, len(result['OSA']['ATTACHED']))
        self.assertEqual([], result['OSA']['FREE'])


class VMCPHandlerQueryAttachTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.attach_device()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {'vaddr': '1A00', 'raddr': '2B00', 'mode': '0'}
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_read_write(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 2B00 attached to TESTUSER as 1A00'}
        result = self.handler.attach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(['ATTACH', '2B00', 'TO', 'TESTUSER', 'AS', '1A00'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_read_only(self, mock_run):
        self.rh.parms['mode'] = '1'
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 2B00 attached to TESTUSER as 1A00'}
        result = self.handler.attach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(['ATTACH', '2B00', 'TO', 'TESTUSER', 'AS', '1A00', 'READONLY'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP022E Device 2B00 does not exist'}
        result = self.handler.attach_device()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryDetachTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.detach_device()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {'vaddr': '1A00'}
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 1A00 detached'}
        result = self.handler.detach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['FOR', 'TESTUSER', 'CMD', 'DETACH', '1A00'],
            tolerated=NOT_ATTACHED_PATTERN
        )

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_tolerated_already_detached(self, mock_run):
        # Tolerated failure returns overallRC=0
        mock_run.return_value = {'overallRC': 0, 'response': 'HCP040E Device 1A00 does not exist'}
        result = self.handler.detach_device()
        self.assertEqual(0, result['overallRC'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP003E Invalid option'}
        result = self.handler.detach_device()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryImagePerformanceTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_image_performance()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_real_output(self, mock_run):
        # In real CP output Configured= and the Global/Local Cleared and
        # LocalUncleared fields appear only in the "All Frames" section.
        # GlobalUnclearedAvail appears only in the "Frames < 2G" and
        # "Frames > 2G" sections, so summing every field counts each value
        # once.  Using "All Frames" alone would report 134217587 in use.
        mock_run.return_value = {'overallRC': 0,
                                 'response': QUERY_FRAMES_REAL}
        result = self.handler.query_image_performance()
        self.assertEqual(0, result['overallRC'])
        # Computed by hand from QUERY_FRAMES_REAL:
        #   Configured = 134217728
        #   free = 17 + 64 + 60 (All Frames) + 308081 (< 2G)
        #          + 97473280 (> 2G) = 97781502
        #   in use = 134217728 - 97781502 = 36436226
        self.assertEqual("MEMORY_IN_USE=36436226", result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_not_double_counted(self, mock_run):
        # "All Frames" already carries every value, and the per-range
        # sections repeat some of them: each must be counted once.
        mock_run.return_value = {
            'overallRC': 0,
            'response': (
                "All Frames:\n"
                "   Configured=1000  GlobalClearedAvail=10\n"
                "   GlobalUnclearedAvail=100  LocalClearedAvail=5\n"
                "   LocalUnclearedAvail=5\n"
                "\n"
                "Frames < 2G:\n"
                "   Configured=400  GlobalUnclearedAvail=40\n"
                "\n"
                "Frames > 2G:\n"
                "   Configured=600  GlobalUnclearedAvail=60\n")}
        result = self.handler.query_image_performance()
        # in use = 1000 - (10 + 100 + 5 + 5)
        self.assertEqual("MEMORY_IN_USE=880", result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.query_image_performance()
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('HCP error', result['response'])


class VMCPHandlerSSIInfoTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.ssi_info()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_not_in_cluster_real_output(self, mock_run):
        mock_run.return_value = {'overallRC': 0,
                                 'response': QUERY_SSI_NOT_IN_CLUSTER_REAL}
        result = self.handler.ssi_info()
        self.assertEqual({'response': [], 'rc': 0}, result)

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_joined_cluster(self, mock_run):
        output = (
            "SSI Name: ICIC2SSI\n"
            "SSI Mode: Stable\n"
            "Cross-System Timeouts: Enabled\n"
            "SSI Persistent Data Record (PDR) device: IAS7CM on 139E\n"
            "Slot  System    State      PDR Heartbeat        Received Heartbeat\n"
            " 1    BOEIAAS7  Joined     12/28/21 05:10:21    12/28/21 05:10:21\n"
            " 2    BOEIAAS8  Joined     12/28/21 05:10:36    12/28/21 05:10:36\n"
            " 3    --------  Down\n"
            " 4    --------  Down\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.ssi_info()
        self.assertEqual(0, result['rc'])
        expected = [
            'ssi_name = ICIC2SSI',
            'ssi_mode = Stable',
            'ssi_pdr = IAS7CM_on_139E',
            'cross_system_timeouts = Enabled',
            'output.ssiInfoCount = 4',
            '',
            'member_slot = 1',
            'member_system_id = BOEIAAS7',
            'member_state = Joined',
            'member_pdr_heartbeat = 12/28/21_05:10:21',
            'member_received_heartbeat = 12/28/21_05:10:21',
            '',
            'member_slot = 2',
            'member_system_id = BOEIAAS8',
            'member_state = Joined',
            'member_pdr_heartbeat = 12/28/21_05:10:36',
            'member_received_heartbeat = 12/28/21_05:10:36',
            '',
            'member_slot = 3',
            'member_system_id = N/A',
            'member_state = Down',
            'member_pdr_heartbeat = N/A',
            'member_received_heartbeat = N/A',
            '',
            'member_slot = 4',
            'member_system_id = N/A',
            'member_state = Down',
            'member_pdr_heartbeat = N/A',
            'member_received_heartbeat = N/A',
            ''
        ]
        self.assertEqual(expected, result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.ssi_info()
        self.assertEqual(1, result['rc'])


class VMCPHandlerQueryRelocateTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.relocate_vm()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {
            'dest': 'TARGETSYS',
            'forcearch': True,
            'forcedomain': True,
            'forcestorage': True,
            'immediate': True,
            'maxTotal': 100,
            'maxQuiesce': 10
        }
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Relocation complete', 'output': ''}
        result = self.handler.relocate_vm()
        self.assertEqual(0, result['overallRC'])
        expected_args = [
            'VMRELOCATE', 'MOVE', 'TESTUSER',
            'TO', 'TARGETSYS',
            'FORCE', 'ARCHITECTURE', 'DOMAIN', 'STORAGE',
            'IMMEDIATE',
            'MAXTotal', '100', 'SEC',
            'MAXQuiesce', '10', 'SEC'
        ]
        mock_run.assert_called_once_with(expected_args, output=True)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_nolimit(self, mock_run):
        self.rh.parms = {
            'dest': 'TARGETSYS',
            'maxTotal': -1,
            'maxQuiesce': -1
        }
        mock_run.return_value = {'overallRC': 0, 'response': 'Relocation complete', 'output': ''}
        result = self.handler.relocate_vm()
        self.assertEqual(0, result['overallRC'])
        expected_args = [
            'VMRELOCATE', 'MOVE', 'TESTUSER',
            'TO', 'TARGETSYS',
            'MAXTotal', 'NOLIMIT',
            'MAXQuiesce', 'NOLIMIT'
        ]
        mock_run.assert_called_once_with(expected_args, output=True)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_fails(self, mock_run):
        mock_run.return_value = {
            'overallRC': 1,
            'response': 'HCP045E TESTUSER not logged on',
            'output': 'HCP045E TESTUSER not logged on'
        }
        result = self.handler.relocate_vm()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerActivateTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.activate()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_already_logged_on(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])
        self.assertEqual("", result['response'])
        mock_run.assert_not_called()

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_logged_off_xautolog_success(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 0, 'response': 'Command accepted'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['xautolog', 'TESTUSER'],
            tolerated=ALREADY_LOGGED_ON_PATTERN
        )

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_tolerated_already_logged_on(self, mock_run, mock_is_logged_on):
        # When XAUTOLOG returns HCP054E, tolerated failure returns overallRC=0
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 0, 'response': 'HCP054E Already logged on'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_fails(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP022E User does not exist'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryVSwitchDetailsTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_vswitch_details()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0,
                                 'response': QUERY_VSWITCH_DETAILS_REAL}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        response = result['response']
        self.assertEqual(4, response['vswitch_count'])
        vswitches = response['vswitches']
        self.assertEqual(['DTCSMAPI', 'VMTCPIP', 'VSICIC', 'VSICICA'],
                         [v['vswitch_name'] for v in vswitches])
        # Uplink port connections are not guest NICs and must not be
        # counted; VSICICA has only an uplink port.
        self.assertEqual([2, 1, 21, 0],
                         [len(v['nics']) for v in vswitches])

        # Two NICs on the same vswitch, the second with discarded TX frames.
        dtcsmapi = vswitches[0]['nics']
        self.assertEqual({
            'userid': 'DTCSMAPI', 'vdev': '0100',
            'nic_fr_rx': '5993', 'nic_fr_rx_dsc': '0',
            'nic_fr_rx_err': '0',
            'nic_fr_tx': '6904', 'nic_fr_tx_dsc': '0',
            'nic_fr_tx_err': '0',
            'nic_rx': '481691', 'nic_tx': '1251132'}, dtcsmapi[0])
        self.assertEqual({
            'userid': 'LOHCOST', 'vdev': 'F000',
            'nic_fr_rx': '10310', 'nic_fr_rx_dsc': '0',
            'nic_fr_rx_err': '0',
            'nic_fr_tx': '8820', 'nic_fr_tx_dsc': '979',
            'nic_fr_tx_err': '0',
            'nic_rx': '2126094', 'nic_tx': '750529'}, dtcsmapi[1])

        # The guest NIC counters, not the 296203011 / 27058622185 of the
        # uplink port connection printed just before them.
        tcpip = vswitches[1]['nics']
        self.assertEqual({
            'userid': 'TCPIP', 'vdev': 'BD00',
            'nic_fr_rx': '296203586', 'nic_fr_rx_dsc': '0',
            'nic_fr_rx_err': '0',
            'nic_fr_tx': '38150', 'nic_fr_tx_dsc': '0',
            'nic_fr_tx_err': '0',
            'nic_rx': '27058702105', 'nic_tx': '14939368'}, tcpip[0])

        # Many NICs on one vswitch, in the order CP printed them.
        vsicic = vswitches[2]['nics']
        self.assertEqual('B4904CPT', vsicic[0]['userid'])
        self.assertEqual('6827275465', vsicic[0]['nic_tx'])
        self.assertEqual('IIMD00BC', vsicic[1]['userid'])
        self.assertEqual('11', vsicic[1]['nic_fr_rx_dsc'])
        self.assertEqual('SSAN0077', vsicic[-1]['userid'])
        self.assertEqual('5984543616', vsicic[-1]['nic_rx'])
        self.assertEqual('1217983', vsicic[-1]['nic_tx'])
        self.assertEqual(['1000'] * 21, [n['vdev'] for n in vsicic])

        # A NIC without any RX/TX lines keeps the zero defaults.
        malr000a = [n for n in vsicic if n['userid'] == 'MALR000A'][0]
        self.assertEqual({
            'userid': 'MALR000A', 'vdev': '1000',
            'nic_fr_rx': '0', 'nic_fr_rx_dsc': '0', 'nic_fr_rx_err': '0',
            'nic_fr_tx': '0', 'nic_fr_tx_dsc': '0', 'nic_fr_tx_err': '0',
            'nic_rx': '0', 'nic_tx': '0'}, malr000a)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_multiple_vswitches(self, mock_run):
        output = (
            "VSWITCH SYSTEM VSW1 Type: QDIO Connected: 1\n"
            "Adapter Connections:\n"
            "  Adapter Owner: USER01 NIC: 0600\n"
            "    RX Packets: 10 Discarded: 0 Errors: 0\n"
            "    TX Packets: 20 Discarded: 0 Errors: 0\n"
            "    RX Bytes: 100 TX Bytes: 200\n"
            "VSWITCH SYSTEM VSW2 Type: QDIO Connected: 1\n"
            "Adapter Connections:\n"
            "  Adapter Owner: USER02 NIC: 0700\n"
            "    RX Packets: 30 Discarded: 1 Errors: 0\n"
            "    TX Packets: 40 Discarded: 2 Errors: 0\n"
            "    RX Bytes: 300 TX Bytes: 400\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        response = result['response']
        self.assertEqual(2, response['vswitch_count'])
        self.assertEqual('VSW1', response['vswitches'][0]['vswitch_name'])
        self.assertEqual('VSW2', response['vswitches'][1]['vswitch_name'])

    @mock.patch('subprocess.check_output', return_value=b"")
    def test_query_vswitch_details_command_has_buffer_option(
            self, mock_check):
        self.handler.query_vswitch_details()
        mock_check.assert_called_once_with(
            ["sudo", "/sbin/vmcp", "--buffer=1M",
             "QUERY", "VSWITCH", "DETAILS"],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_no_vswitches(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': ''}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        self.assertEqual({'vswitch_count': 0, 'vswitches': []},
                         result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        result = self.handler.query_vswitch_details()
        self.assertEqual(1, result['rc'])
        self.assertEqual(0, result['response']['vswitch_count'])
        self.assertEqual([], result['response']['vswitches'])
