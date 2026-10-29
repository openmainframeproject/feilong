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

import re
import subprocess

from smtLayer import msgs
from smtLayer import vmUtils
from zvmsdk import exception

modId = 'VCP'
version = "1.0.0"

# CP messages meaning the guest is not logged on (same set that
# vmUtils.isLoggedOn uses).  For a logoff this is the desired end state.
NOT_LOGGED_ON_PATTERN = r'^HCP\w\w\w(045E|361E)'


class VMCPHandler:

    def __init__(self, rh):
        """
        Initialise the handler with a Request Handle.

        Input:
           rh - smtLayer ReqHandle instance
        """
        self._rh = rh

    def _run(self, vmcp_args, tolerated=None):
        """
        Execute one vmcp sub-command.

        Builds the full command as:
            sudo /sbin/vmcp <vmcp_args[0]> <vmcp_args[1]> ...

        Input:
           vmcp_args - list of str tokens that follow '/sbin/vmcp',
                       e.g. ["query", "userid"]
           tolerated - optional regex (str).  If the command fails and its
                       output matches, the failure is tolerated: nothing is
                       recorded in the request results and overallRC is 0.

        Output:
           dict with keys:
             response   - decoded stdout string; empty string on failure
                          (the command output for a tolerated failure)
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
            if tolerated and e.output and re.search(
                    tolerated, bytes.decode(e.output), re.MULTILINE):
                rh.printSysLog("Tolerated failure of: " + strCmd)
                return {"response": bytes.decode(e.output), "overallRC": 0}
            msg = msgs.msg['0405'][1] % (
                modId, strCmd, strCmd, e.output.decode(errors='replace'))
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
           Raises exception.SDKSMTRequestFailed when the vmcp command
           fails, or when it exits with rc=0 but CP reports
           "A PCI function was not found.", i.e. the host has no PCI
           function.
        """
        rh = self._rh
        log_tag = "VMCPHandler.query_pcif"

        args = ["query", "pcif"]
        result = self._run(args)

        if result["overallRC"] != 0:
            # _run() already recorded the failure in rh.results.
            results = rh.results
            results.pop('logEntries', None)
            msg = ("Failed to query PCIF list via vmcp. Results: %s"
                   % str(results))
            rh.printSysLog("%s: %s" % (log_tag, msg))
            raise exception.SDKSMTRequestFailed(results, msg)

        # vmcp exits rc=0 but prints "A PCI function was not found." when the
        # host has no PCI function hardware at all.
        if "A PCI function was not found." in result["response"]:
            msg = msgs.msg['0405'][1] % (
                modId, "PCIF list", "vmcp query pcif", result["response"])
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0405'][0])
            rh.printSysLog("%s: no PCIF hardware on host, recorded as failure"
                           % log_tag)
            raise exception.SDKSMTRequestFailed(rh.results, msg)

        pcif_list = []
        for line in result["response"].splitlines():
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

    def query_storage(self):
        """
        Query total and standby storage of the z/VM LPAR.

        Output:
           dict with keys:
             'lparMemTotal'   - e.g. "65536M";  "no info" on error
             'lparMemStandby' - e.g. "0";        "no info" on error
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_storage")

        lparMemTotal = "no info"
        lparMemStandby = "no info"

        result = self._run(["query", "storage"])
        output = result["response"]
        if result["overallRC"] == 0:
            # Normalise:  "STORAGE = 65536M  STANDBY = 0  REMAINDER = 0"
            #         →   ["STORAGE", "65536M", "STANDBY", "0", ...]
            parts = output.upper().replace('=', ' ').split()
            try:
                if 'STORAGE' in parts:
                    lparMemTotal = parts[parts.index('STORAGE') + 1]
                if 'STANDBY' in parts:
                    lparMemStandby = parts[parts.index('STANDBY') + 1]
            except (ValueError, IndexError):
                rh.printSysLog(
                    "VMCPHandler.query_storage: unexpected output: " + output)

        rh.printSysLog(
            "Exit VMCPHandler.query_storage, total: %s standby: %s"
            % (lparMemTotal, lparMemStandby))
        return {"lparMemTotal": lparMemTotal, "lparMemStandby": lparMemStandby}

    def query_cplevel(self):
        """
        Query the z/VM CP level and IPL date/time.
        Output:
           ipl - the IPL line as a string,
                 e.g. "IPL at 01/15/24 08:30:00 EST"; "" on error / not found
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_cplevel")

        ipl = ""
        result = self._run(["query", "cplevel"])
        output = result["response"]
        if result["overallRC"] == 0:
            for line in output.splitlines():
                if "IPL" in line:
                    ipl = line.strip()
                    break

        rh.printSysLog("Exit VMCPHandler.query_cplevel, ipl: " + ipl)
        return ipl

    def deactivate(self, userid, force=False):
        """
        Deactivate (log off) a virtual machine via vmcp.
        Input:
           userid - target virtual machine userid (str)
           force  - True → append IMMED to the vmcp force logoff command
                    (default False)

        Output:
           dict with keys:
             response   - decoded stdout string; empty string on failure
             overallRC  - 0 on success, non-zero on failure
        """
        rh = self._rh

        rh.printSysLog(
            "Enter VMCPHandler.deactivate, userid: %s force: %s"
            % (userid, str(force)))

        # Step 1: Check whether the guest is logged on.
        results = vmUtils.isLoggedOn(rh, userid)
        if results['overallRC'] != 0:
            # Cannot determine the log on/off state.
            # Message already included.  Act as if it is 'on'.
            pass
        elif results['rs'] == 0:
            # State is powered on.
            pass
        else:
            # Reset values for rest of subfunction
            results['overallRC'] = 0
            results['rc'] = 0
            results['rs'] = 0
            rh.updateResults(results)
            return {"response": "", "overallRC": 0}

        rh.printSysLog(
            "VMCPHandler.deactivate: %s is logged on" % userid)

        # Step 2: Force logoff — with IMMED if -f IMMED was requested.
        # The guest may log off between the status check and the FORCE
        # (HCP045E); that is the desired end state, so it is tolerated, as
        # the SMAPI path tolerates rc 200 / rs 12 or 16.
        args = ["force", userid, "logoff"]
        if force:
            args.append("IMMED")

        response = self._run(args, tolerated=NOT_LOGGED_ON_PATTERN)
        rh.printSysLog("Exit VMCPHandler.deactivate, rc: " +
                       str(response['overallRC']))
        return response
