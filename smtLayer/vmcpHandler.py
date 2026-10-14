#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# VMCP command handler for Systems Management Ultra Thin Layer
#
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

import subprocess

from smtLayer import msgs

modId = 'VCP'
version = "1.0.0"


class VMCPHandler:

    def __init__(self, rh):
        """
        Initialise the handler with a Request Handle.

        Input:
           rh - smtLayer ReqHandle instance
        """
        self._rh = rh

    def _run(self, vmcp_args):
        """
        Execute one vmcp sub-command.

        Builds the full command as:
            sudo /sbin/vmcp <vmcp_args[0]> <vmcp_args[1]> ...

        Input:
           vmcp_args - list of str tokens that follow '/sbin/vmcp',
                       e.g. ["query", "userid"]

        Output:
           dict with keys:
             response   - decoded stdout string; empty string on failure
             overallRC  - 0 on success, non-zero on failure
        """
        rh = self._rh
        cmd = ["sudo", "/sbin/vmcp"] + vmcp_args
        strCmd = ' '.join(cmd)
        rh.printSysLog("Invoking: " + strCmd)
        try:
            raw = subprocess.check_output(
                cmd, close_fds=True, stderr=subprocess.STDOUT)
            return {"response": bytes.decode(raw), "overallRC": 0}
        except subprocess.CalledProcessError as e:
            msg = msgs.msg['0405'][1] % (modId, strCmd, strCmd, e.output)
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0405'][0])
            return {"response": "", "overallRC": e.returncode}
        except Exception as e:
            rh.printLn("ES", msgs.msg['0421'][1] % (
                modId, strCmd, type(e).__name__, str(e)))
            rh.updateResults(msgs.msg['0421'][0])
            return {"response": "", "overallRC": 1}

    def query_pcif(self):
        """
        Query PCI function (PCIF) information via 'vmcp q pcif'.
        Output:
           list of dicts, one per PCIF line.  Each dict contains:
             'pcif'   - PCI function device number, e.g. "00000110"
             'status' - "ATTACHED" or "FREE"
             'userid' - owning virtual machine (ATTACHED only), e.g. "MALR003F";
                        empty string when FREE
             'state'  - "ENABLED" or "DISABLED"
             'type'   - network type, e.g. "NETH"
           Returns an empty list when no PCIFs are found or on error.
        """
        rh = self._rh
        log_tag = "VMCPHandler.query_pcif"

        args = ["query", "pcif"]
        result = self._run(args)
        output, rc = result["response"], result["overallRC"]

        pcif_list = []
        if rc == 0:
            for line in output.splitlines():
                # Parse by token semantics rather than fixed positions so the
                # parser stays correct across z/VM releases and PCI states.
                #
                # Known formats (tokens shown individually):
                #   ATTACHED: PCIF <dev> ATTACHED TO <userid> <dev> ENABLED|DISABLED <type>
                #   FREE:     PCIF <dev> FREE ENABLED|DISABLED <type>
                #
                # Strategy:
                #   - Require "PCIF" token; the token that follows is the device number.
                #   - "ATTACHED" or "FREE" token determines status.
                #   - When ATTACHED, the token after "TO" is the owning userid.
                #   - "ENABLED" or "DISABLED" token is the state; everything after
                #     it on the line is the type.
                pcif_info = line.upper().split()
                if "PCIF" not in pcif_info:
                    continue
                pcif_idx = pcif_info.index("PCIF")
                if pcif_idx + 1 >= len(pcif_info):
                    rh.printSysLog(
                        "%s: skipping malformed line (no token after PCIF): %r"
                        % (log_tag, line))
                    continue
                pcif_id = pcif_info[pcif_idx + 1]

                if "ATTACHED" in pcif_info:
                    status = "ATTACHED"
                    to_idx = pcif_info.index("TO") if "TO" in pcif_info else -1
                    userid = pcif_info[to_idx + 1] if to_idx >= 0 and to_idx + 1 < len(pcif_info) else ""
                elif "FREE" in pcif_info:
                    status = "FREE"
                    userid = ""
                else:
                    rh.printSysLog(
                        "%s: skipping line with unknown status: %r"
                        % (log_tag, line))
                    continue

                if "ENABLED" in pcif_info:
                    state = "ENABLED"
                    state_idx = pcif_info.index("ENABLED")
                elif "DISABLED" in pcif_info:
                    state = "DISABLED"
                    state_idx = pcif_info.index("DISABLED")
                else:
                    rh.printSysLog(
                        "%s: skipping line with no ENABLED/DISABLED token: %r"
                        % (log_tag, line))
                    continue

                # Everything after the state token is the type string.
                pcif_type = " ".join(pcif_info[state_idx + 1:])
                if not pcif_type:
                    rh.printSysLog(
                        "%s: skipping line with no type after state: %r"
                        % (log_tag, line))
                    continue
                pcif_list.append({
                    "pcif": pcif_id,
                    "status": status,
                    "userid": userid,
                    "state": state,
                    "type": pcif_type,
                })

        rh.printSysLog(
            "Exit %s, entries found: %d" % (log_tag, len(pcif_list)))
        return pcif_list
