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
NOT_LOGGED_ON_PATTERN = r'HCP\w*(045E|361E)'
ALREADY_LOGGED_ON_PATTERN = r'HCP\w*054E'
NOT_ATTACHED_PATTERN = r'HCP\w*040E'


class VMCPHandler:

    def __init__(self, rh):
        """
        Initialise the handler with a Request Handle.

        Input:
           rh - smtLayer ReqHandle instance
        """
        self._rh = rh

    def _run(self, vmcp_args, tolerated=None, output=False):
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
           output    - if True, a (non-tolerated) failure also returns the
                       decoded CP output under 'output', so the caller can
                       look at the CP messages (HCP...).  Default False, so
                       the result stays safe to pass to updateResults.

        Output:
           dict with keys:
             response   - decoded stdout string; empty string on failure
                          (the command output for a tolerated failure)
             overallRC  - 0 on success, non-zero on failure
             output     - only if output=True and the command failed
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
            result = {"response": "", "overallRC": e.returncode}
            if output:
                result["output"] = bytes.decode(e.output) if e.output else ""
            return result
        except Exception as e:
            rh.printLn("ES", msgs.msg['0421'][1] % (
                modId, strCmd, type(e).__name__, str(e)))
            rh.updateResults(msgs.msg['0421'][0])
            return {"response": "", "overallRC": 1}

    def _run_for(self, userid, cp_cmd):
        """
        Execute a vmcp "FOR <userid> CMD <cp_cmd>" call.

        Equivalent command:
            sudo /sbin/vmcp "FOR <userid> CMD <cp_cmd>"

        Input:
           userid  - target z/VM guest userid, e.g. "KUNA0006"
           cp_cmd  - CP command string, e.g. "DEFINE NIC 0600 TYPE QDIO"

        Output:
           dict with keys:
             response   - decoded stdout/stderr string
             overallRC  - 0 on success, non-zero on failure
        """
        rh = self._rh
        vmcp_args = "FOR %s CMD %s" % (userid, cp_cmd)
        strCmd = 'sudo /sbin/vmcp "%s"' % vmcp_args
        rh.printSysLog("Invoking: " + strCmd)
        try:
            raw = subprocess.check_output(
                ['sudo', '/sbin/vmcp', vmcp_args],
                close_fds=True,
                stderr=subprocess.STDOUT)
            return {
                'response': bytes.decode(raw),
                'overallRC': 0,
                'rc': 0, 'rs': 0, 'errno': 0,
                'strError': ''
            }
        except subprocess.CalledProcessError as e:
            err_out = (bytes.decode(e.output)
                       if isinstance(e.output, bytes) else (e.output or ''))
            msg = msgs.msg['0405'][1] % (
                modId, strCmd, strCmd, e.output.decode(errors='replace'))
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0405'][0])
            return {
                'response': err_out,
                'overallRC': e.returncode,
                'rc': e.returncode, 'rs': 0, 'errno': 0,
                'strError': err_out
            }
        except Exception as e:
            rh.printLn("ES", msgs.msg['0421'][1] % (
                modId, strCmd, type(e).__name__, str(e)))
            rh.updateResults(msgs.msg['0421'][0])
            return {
                'response': '',
                'overallRC': 1,
                'rc': 1, 'rs': 0, 'errno': 0,
                'strError': str(e)
            }

    def activate(self, userid):
        """
        Activate (log on) a virtual machine via vmcp.
        Input:
           userid - target virtual machine userid (str)

        Output:
           dict with keys:
             response   - vmcp output
             overallRC  - 0 on success or already logged on,
                          non-zero on failure
        """
        rh = self._rh

        rh.printSysLog("Enter VMCPHandler.activate, userid: " + userid)

        # Step 1: Check whether the guest is already logged on.
        results = vmUtils.isLoggedOn(rh, userid)
        if results['overallRC'] != 0:
            # Cannot determine the log on/off state.
            # Message already included.  Act as if it is 'off'.
            pass
        elif results['rs'] == 1:
            # State is logged off.
            pass
        else:
            # Already logged on.  Reset values for rest of subfunction
            results['overallRC'] = 0
            results['rc'] = 0
            results['rs'] = 0
            rh.updateResults(results)
            rh.printSysLog(
                "Exit VMCPHandler.activate, %s is already logged on" % userid)
            return {"response": "", "overallRC": 0}

        rh.printSysLog(
            "VMCPHandler.activate: %s is logged off" % userid)

        # Step 2: XAUTOLOG the guest.
        # The guest may log on between the status check and the XAUTOLOG
        # (HCP054E); that is the desired end state, so it is tolerated, as
        # the SMAPI path tolerates rc 200 / rs 8.
        args = ["xautolog", userid]

        result = self._run(args, tolerated=ALREADY_LOGGED_ON_PATTERN)
        rc = result["overallRC"]
        if rc == 0:
            # If xautolog succeeded or HCP054E was tolerated, clear any failure from isLoggedOn
            if rh.results['overallRC'] != 0:
                rh.updateResults({}, reset=1)
        else:
            if rh.results['overallRC'] == 0:
                # Make sure a failed logon is always visible to callers that
                # inspect rh.results, even if _run did not record it.
                rh.updateResults(msgs.msg['0405'][0])
        rh.printSysLog("Exit VMCPHandler.activate, rc: " + str(rc))
        return result

    def query_image_performance(self, rh):
        """
        Collect MEMORY_IN_USE using VMCP QUERY FRAMES.
        Only MEMORY_IN_USE is consumed by the caller (getHost.getGeneralInfo).

        Input:
            rh - request handle containing the request information (RequestHandle object)

        Output:
            overallRC - return code (0 for success, 1 for failure)
            response  - string containing "MEMORY_IN_USE=<pages>" on success,
                        or an error message on failure
        """
        rh.printSysLog("Enter VMCPHandler.query_image_performance, userid: " + rh.userid)

        frames_output = self._run(["query", "frames"])
        rc = frames_output["overallRC"]
        if rc != 0:
            rh.printSysLog("Exit VMCPHandler.query_image_performance, rc: " + str(rc))
            return {"overallRC": rc, "response": frames_output["response"]}

        frames_out = frames_output["response"]

        configured = 0
        output = re.search(r"Configured=(\d+)", frames_out)
        if output:
            configured = int(output.group(1))

        free_frames = 0
        output = re.search(r"GlobalClearedAvail=(\d+)", frames_out)
        if output:
            free_frames += int(output.group(1))

        output = re.search(r"LocalClearedAvail=(\d+)", frames_out)
        if output:
            free_frames += int(output.group(1))

        output = re.search(r"GlobalUnclearedAvail=(\d+)", frames_out)
        if output:
            free_frames += int(output.group(1))

        output = re.search(r"LocalUnclearedAvail=(\d+)", frames_out)
        if output:
            free_frames += int(output.group(1))

        memory_in_use = configured - free_frames
        rh.printSysLog("Exit VMCPHandler.query_image_performance, rc: " + str(rc))

        return {"overallRC": rc, "response": "MEMORY_IN_USE=%d" % memory_in_use}

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

    def ssi_info(self):
        """
        Query and collect z/VM SSI cluster information using VMCP.

        Input:
           None - uses the request handle associated with the VMCPHandler.

        Output:
           Dictionary containing:
              response - list of formatted SSI information
              rc  - return code from the VMCP QUERY SSI command
        """

        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.ssi_info")

        args = ['QUERY', 'SSI']

        results = self._run(args)

        vmcp_response = results["response"]
        rc = results["overallRC"]

        # Host is not a member of an SSI cluster
        if "This system is not a member of an SSI cluster." in vmcp_response:
            rh.printSysLog(
                "Exit VMCPHandler.ssi_info - Host is not a member of an SSI cluster."
            )
            return {"response": [], "rc": rc}

        response = []

        # Parse SSI information
        ssi_name = re.search(r"SSI Name:\s*(.+)", vmcp_response)
        ssi_mode = re.search(r"SSI Mode:\s*(.+)", vmcp_response)
        cst = re.search(r"Cross-System Timeouts:\s*(.+)", vmcp_response)
        pdr = re.search(
            r"SSI Persistent Data Record \(PDR\) device:\s*(\S+)\s+on\s+(\S+)",
            vmcp_response
        )

        if ssi_name:
            response.append("ssi_name = %s" % ssi_name.group(1))
        if ssi_mode:
            response.append("ssi_mode = %s" % ssi_mode.group(1))
        if pdr:
            response.append("ssi_pdr = %s_on_%s" % (pdr.group(1), pdr.group(2)))
        if cst:
            response.append("cross_system_timeouts = %s" % cst.group(1))

        # Parse member information
        member_pattern = re.compile(
            r"^\s*(\d+)\s+(\S+)\s+(\S+)"
            r"(?:\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})"
            r"\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2}))?$",
            re.MULTILINE
        )

        member_matches = list(member_pattern.finditer(vmcp_response))

        response.append("output.ssiInfoCount = %d" % len(member_matches))
        response.append("")

        for match in member_matches:
            (
                slot,
                system_id,
                state,
                pdr_date,
                pdr_time,
                recv_date,
                recv_time,
            ) = match.groups()

            if system_id == "--------":
                system_id = "N/A"

            pdr_hb = (
                "%s_%s" % (pdr_date, pdr_time)
                if pdr_date and pdr_time else "N/A"
            )

            recv_hb = (
                "%s_%s" % (recv_date, recv_time)
                if recv_date and recv_time else "N/A"
            )

            response.extend([
                "member_slot = %s" % slot,
                "member_system_id = %s" % system_id,
                "member_state = %s" % state,
                "member_pdr_heartbeat = %s" % pdr_hb,
                "member_received_heartbeat = %s" % recv_hb,
                ""
            ])

        rh.printSysLog("Exit VMCPHandler.ssi_info, rc: " + str(rc))

        return {"response": response, "rc": rc}

    def query_attach(self, rh):
        """
        Attach a virtual device to a z/VM guest using the VMCP ATTACH command.

        Input:
           rh - request handle containing:
                parms['vaddr'] - virtual device address
                parms['raddr'] - real device address
                parms['mode']  - device access mode
                               (0 = read-write, 1 = read-only)
                userid          - target guest userid

        Output:
         overallRC - return code (0 for success, 1 for failure)
         response  - VMCP command output
        """

        rh.printSysLog("Enter VMCPHandler.query_attach, userid: " + rh.userid)

        args = ["ATTACH", rh.parms['vaddr'], "TO", rh.userid,
                "AS", rh.parms['raddr']]
        # Add read-only option if requested.
        # rh.parms['mode'] is 0 (read-write) or 1 (read-only).
        # z/VM CP ATTACH uses the keyword READONLY — not "RO" or "1".
        if str(rh.parms.get('mode', 0)) == '1':
            args.append("READONLY")

        response = self._run(args)
        rc = response["overallRC"]

        rh.printSysLog("Exit VMCPHandler.query_attach, rc: " + str(rc))
        return response

    def query_detach(self, rh):
        """
        Detach a virtual device from a z/VM guest using the VMCP DETACH command.

        Input:
           rh - request handle containing:
                parms['vaddr'] - virtual device address to be detached
                userid          - guest userid used for logging

            Output:
             overallRC - return code (0 for success or already detached, non-zero for failure)
             response  - VMCP command output
        """

        rh.printSysLog("Enter VMCPHandler.query_detach, userid: " + rh.userid)
        args = ["DETACH", rh.parms['vaddr'], "FROM", rh.userid]

        response = self._run(args, tolerated=NOT_ATTACHED_PATTERN)
        rc = response["overallRC"]

        rh.printSysLog("Exit VMCPHandler.query_detach, rc: " + str(rc))
        return response

    def query_relocate(self, rh):
        """
        Execute VMRELOCATE MOVE synchronously using VMCP.
        Waits for completion to validate the final relocation outcome.
        """

        rh.printSysLog("Enter VMCPHandler.query_relocate")

        args = ["VMRELOCATE", "MOVE", rh.userid]

        # Destination
        if 'dest' in rh.parms:
            args.extend([
                "TO",
                rh.parms['dest']
            ])

        # Force options
        forceOption = ''

        if 'forcearch' in rh.parms:
            forceOption = "ARCHITECTURE "

        if 'forcedomain' in rh.parms:
            forceOption = forceOption + "DOMAIN "

        if 'forcestorage' in rh.parms:
            forceOption = forceOption + "STORAGE "

        if forceOption != '':
            args.extend([
                "FORCE"
            ])
            args.extend(forceOption.split())

        # Immediate
        if 'immediate' in rh.parms:
            args.append("IMMEDIATE")

        # Max Total
        if 'maxTotal' in rh.parms:
            if rh.parms['maxTotal'] == -1:
                args.extend([
                    "MAXTotal",
                    "NOLIMIT"
                ])
            else:
                args.extend([
                    "MAXTotal",
                    str(rh.parms['maxTotal']),
                    "SEC"
                ])

        # Max Quiesce
        if 'maxQuiesce' in rh.parms:
            if rh.parms['maxQuiesce'] == -1:
                args.extend([
                    "MAXQuiesce",
                    "NOLIMIT"
                ])
            else:
                args.extend([
                    "MAXQuiesce",
                    str(rh.parms['maxQuiesce']),
                    "SEC"
                ])

        # Synchronous execution to wait for completion and validate final outcome
        args.append("SYNCHRONOUS")

        rh.printSysLog(
            "VMCP VMRELOCATE params: " + str(args)
        )

        response = self._run(args, output=True)

        rh.printSysLog(
            "Exit VMCPHandler.query_relocate, rc: " +
            str(response["overallRC"])
        )

        return response

    def query_vswitch_details(self):
        """
        Query per-NIC byte statistics for one or all VSwitches using VMCP.
        Runs: sudo /sbin/vmcp QUERY VSWITCH DETAILS

        Output:
           dict containing:
             response - parsed dictionary with keys:
                          'vswitch_count': int
                          'vswitches': list of dicts with 'vswitch_name' and
                                       'nics' (per-NIC statistics dicts)
             rc       - 0 on success, non-zero on failure
        """

        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_vswitch_details")

        results = self._run(["QUERY", "VSWITCH", "DETAILS"])
        rc = results["overallRC"]

        if rc != 0 or not results["response"]:
            rh.printSysLog(
                "Exit VMCPHandler.query_vswitch_details, rc: " + str(rc))
            return {
                "vswitch_count": 0,
                "vswitches": [],
                "rc": rc
            }

        raw_lines = results["response"].splitlines()

        vswitches = []
        current_vsw = None
        current_nic = None
        in_nic_section = False

        for line in raw_lines:
            stripped = line.strip()

            # VSWITCH SYSTEM VSICIC Type: QDIO Connected: 38 ...
            vsw_match = re.match(
                r'^VSWITCH\s+\S+\s+(\S+)',
                stripped,
                re.IGNORECASE)

            if vsw_match:
                # Save previous NIC
                if current_nic is not None and current_vsw is not None:
                    current_vsw['nics'].append(current_nic)
                    current_nic = None

                # Save previous VSwitch
                if current_vsw is not None:
                    vswitches.append(current_vsw)

                current_vsw = {
                    'vswitch_name': vsw_match.group(1),
                    'nics': []
                }

                in_nic_section = False
                continue

            if current_vsw is None:
                continue

            # NIC information starts after this section.
            if re.match(
                    r'^Adapter Connections:',
                    stripped,
                    re.IGNORECASE):
                in_nic_section = True
                continue

            # Adapter Owner: IAAS0151 NIC: 1000.P00 Name: HYD1G1
            if in_nic_section:
                adp_match = re.match(
                    r'^Adapter Owner:\s+(\S+)\s+NIC:\s+([0-9A-Fa-f]+)',
                    stripped,
                    re.IGNORECASE)

                if adp_match:
                    # Save previous NIC
                    if current_nic is not None:
                        current_vsw['nics'].append(current_nic)

                    current_nic = {
                        'userid': adp_match.group(1),
                        'vdev': adp_match.group(2),
                        'nic_fr_rx': '0',
                        'nic_fr_rx_dsc': '0',
                        'nic_fr_rx_err': '0',
                        'nic_fr_tx': '0',
                        'nic_fr_tx_dsc': '0',
                        'nic_fr_tx_err': '0',
                        'nic_rx': '0',
                        'nic_tx': '0'
                    }
                    continue

            # RX Packets
            rx_pkt = re.match(
                r'^RX Packets:\s+(\d+)\s+Discarded:\s+(\d+)\s+Errors:\s+(\d+)',
                stripped,
                re.IGNORECASE)

            if rx_pkt and current_nic is not None:
                current_nic['nic_fr_rx'] = rx_pkt.group(1)
                current_nic['nic_fr_rx_dsc'] = rx_pkt.group(2)
                current_nic['nic_fr_rx_err'] = rx_pkt.group(3)
                continue

            # TX Packets
            tx_pkt = re.match(
                r'^TX Packets:\s+(\d+)\s+Discarded:\s+(\d+)\s+Errors:\s+(\d+)',
                stripped,
                re.IGNORECASE)

            if tx_pkt and current_nic is not None:
                current_nic['nic_fr_tx'] = tx_pkt.group(1)
                current_nic['nic_fr_tx_dsc'] = tx_pkt.group(2)
                current_nic['nic_fr_tx_err'] = tx_pkt.group(3)
                continue

            # RX/TX Bytes
            bytes_match = re.match(
                r'^RX Bytes:\s+(\d+)\s+TX Bytes:\s+(\d+)',
                stripped,
                re.IGNORECASE)

            if bytes_match and current_nic is not None:
                current_nic['nic_rx'] = bytes_match.group(1)
                current_nic['nic_tx'] = bytes_match.group(2)
                continue

        if current_nic is not None and current_vsw is not None:
            current_vsw['nics'].append(current_nic)

        if current_vsw is not None:
            vswitches.append(current_vsw)

        response = {
            'vswitch_count': len(vswitches),
            'vswitches': vswitches
        }

        rh.printSysLog(
            "Exit VMCPHandler.query_vswitch_details, rc: " + str(rc))

        return {"response": response, "rc": rc}

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

    def get_cpu_count(self):
        """
        To get LPAR total cpu and cpu in use

        Returns cpu_total and cpu_use.
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.get_cpu_count")

        cpu_total = 0
        cpu_use = 0

        result = self._run(['QUERY', 'PROCESSORS', 'EXPANDED'])
        if result['overallRC'] != 0:
            rh.printSysLog(
                "Exit VMCPHandler.get_cpu_count, vmcp failed, returning (0,0)")
            return cpu_total, cpu_use

        for line in result['response'].splitlines():
            parts = line.split()
            if len(parts) < 4 or parts[0] != 'PROCESSOR':
                continue
            status_row = parts[2]
            type_row = parts[3]
            if (status_row.find('MASTER') != -1 or
                    status_row == 'ALTERNATE' or
                    status_row == 'PARKED'):
                cpu_use += 1
            if type_row in ('CP', 'IFL'):
                cpu_total += 1

        rh.printSysLog("Exit VMCPHandler.get_cpu_count, "
                       "total: %d use: %d" % (cpu_total, cpu_use))

        return cpu_total, cpu_use

    def purge_reader(self):
        """
        Purge all reader files for rh.userid

        Returns a standard results dict.
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.purge_reader, userid: " + rh.userid)
        result = self._run(['PURGE', rh.userid, 'RDR', 'ALL'])
        rh.printSysLog("Exit VMCPHandler.purge_reader, rc: " +
                       str(result['overallRC']))
        return result

    def create_nic_for_guest(self, userid, vdev):
        """
        Create a QDIO NIC at virtual device address <vdev> for rh.userid.

        Returns a standard results dict.
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.create_nic_for_guest, "
                       "userid: %s vdev: %s" % (userid, vdev))

        result = self._run_for(userid, "DEFINE NIC %s TYPE QDIO" % vdev)

        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.create_nic_for_guest failed for "
                       "userid: %s vdev: %s rc: %s response: %s"
                       % (userid, vdev, result['overallRC'],
                          result['response']))
            rh.updateResults(result)
            rh.printSysLog("Exit VMCPHandler.create_nic_for_guest, rc: " +
                           str(result['overallRC']))
            return result

        verify = self._run(['QUERY', 'NIC', 'USERID', userid, vdev])
        if verify['overallRC'] == 0:
            rh.printSysLog("VMCPHandler.create_nic_for_guest verify: "
                           "NIC %s for %s confirmed created (QUERY NIC rc=0)"
                           % (vdev, userid))
        else:
            rh.printLn("ES",
                       "VMCPHandler.create_nic_for_guest verify: "
                       "NIC %s absent for %s after DEFINE "
                       "(QUERY NIC rc=%s response: %s)"
                       % (vdev, userid, verify['overallRC'],
                          verify['response']))
            result = {'overallRC': 2, 'rc': 2, 'rs': 0, 'errno': 0,
                      'strError': verify['response'],
                      'response': verify['response'],
                      'nic_not_created': True}
            rh.updateResults(result)

        rh.printSysLog("Exit VMCPHandler.create_nic_for_guest, rc: " +
                       str(result['overallRC']))
        return result

    def query_osa(self):
        """Query OSA devices and their status."""
        DEVTYPE_MAP = {'OSH': 'OSA'}
        OSA_info = {}

        result = self._run(['QUERY', 'OSA'])
        if result['overallRC'] != 0:
            return OSA_info

        for line in result.get('response', '').splitlines():
            parts = line.split()
            if len(parts) < 3 or parts[0] != 'OSA':
                continue
            osa_addr = parts[1]
            if parts[2] != 'ATTACHED':
                continue
            devtype = 'OSA'
            if 'DEVTYPE' in parts:
                dt_idx = parts.index('DEVTYPE')
                if dt_idx + 1 < len(parts):
                    devtype = parts[dt_idx + 1]
            osa_type = DEVTYPE_MAP.get(devtype, devtype)
            OSA_info.setdefault(osa_type, {'FREE': [], 'BOXED': [],
                                           'OFFLINE': [], 'ATTACHED': []})
            attached_id = parts[4] if len(parts) > 4 else 'UNKNOWN'
            OSA_info[osa_type]['ATTACHED'].append((attached_id, osa_addr))

        free_result = self._run(['QUERY', 'OSA', 'FREE'])
        if free_result['overallRC'] == 0:
            for token in free_result.get('response', '').split(','):
                token_parts = token.split()
                if (len(token_parts) >= 3 and token_parts[0] == 'OSA' and
                        'FREE' in token_parts):
                    OSA_info.setdefault(
                        'OSA', {'FREE': [], 'BOXED': [],
                                'OFFLINE': [], 'ATTACHED': []})
                    OSA_info['OSA']['FREE'].append(token_parts[1])

        return OSA_info

    def query_fcp_formatted(self):
        """
        Query FCP devices and return formatted output compatible with
        smcli System_WWPN_Query (6 lines per device).

        Replaces: smcli System_WWPN_Query -k OWNER=YES
        CP command: QUERY FCP WWPN
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_fcp_formatted, userid: " +
                       rh.userid)

        raw = self._run(['QUERY', 'FCP', 'WWPN'])

        if raw['overallRC'] != 0:
            raw['rc'] = 4
            raw['rs'] = 28
            raw['errno'] = 0
            raw['strError'] = ''
            rh.printSysLog(
                "Exit VMCPHandler.query_fcp_formatted, rc: " +
                str(raw['overallRC']))
            return raw

        raw_lines = [line for line in raw['response'].splitlines() if line.strip()]

        out_lines = []
        i = 0
        while i + 2 < len(raw_lines):
            line1 = raw_lines[i]
            line2 = raw_lines[i + 1]
            line3 = raw_lines[i + 2]
            parts1 = line1.split()

            # line1 must start with 'FCP' to mark the start of a new block
            if not parts1 or parts1[0].upper() != 'FCP':
                i += 1
                continue

            # line1: FCP  <addr>  NPIV WWPN <npiv_wwpn>
            addr = parts1[1]
            npiv_wwpn = 'NONE'
            if 'WWPN' in parts1:
                wi = parts1.index('WWPN')
                npiv_wwpn = parts1[wi + 1] if wi + 1 < len(parts1) else 'NONE'

            # line2: CHPID <nn>  PERM WWPN <phys_wwpn>
            parts2 = line2.split()
            chpid = 'NONE'
            phys_wwpn = 'NONE'
            if 'CHPID' in parts2:
                ci = parts2.index('CHPID')
                chpid = parts2[ci + 1] if ci + 1 < len(parts2) else 'NONE'
            if 'WWPN' in parts2:
                wi = parts2.index('WWPN')
                phys_wwpn = parts2[wi + 1] if wi + 1 < len(parts2) else 'NONE'

            # line3: ATTACHED TO <userid>  -or-  FREE  -or-  OFFLINE (or other)
            parts3 = line3.split()
            if parts3 and parts3[0].upper() == 'ATTACHED':
                # "ATTACHED TO <userid>"
                status = 'Active'
                owner = parts3[2] if len(parts3) > 2 else 'NONE'
            elif parts3 and parts3[0].upper() == 'FREE':
                status = 'Free'
                owner = 'NONE'
            else:
                # OFFLINE, or a state not known here: never report the
                # device as free, so that it is not offered for allocation.
                status = 'Offline'
                owner = 'NONE'

            out_lines.append('FCP device number: %s' % addr)
            out_lines.append('  Status: %s' % status)
            out_lines.append('  NPIV world wide port number: %s' % npiv_wwpn)
            out_lines.append('  Channel path ID: %s' % chpid)
            out_lines.append('  Physical world wide port number: %s' % phys_wwpn)
            out_lines.append('  Owner: %s' % owner)

            i += 3

        result = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0,
            'errno': 0,
            'strError': '',
            'response': '\n'.join(out_lines),
        }
        rh.printSysLog("Exit VMCPHandler.query_fcp_formatted, rc: 0, "
                       "devices: %d" % (len(out_lines) // 6))
        return result

    def add_disk(self, vdev, mode):
        """
        Add a disk to the active configuration.

        Replaces: smcli Image_Disk_Create
        CP command: FOR <userid> CMD LINK * <vdev> <vdev> <mode>
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.add_disk, userid: %s vdev: %s "
                       "mode: %s" % (rh.userid, vdev, mode))

        # FOR <userid> CMD LINK * <vdev> <vdev> <mode>
        result = self._run_for(rh.userid, "LINK * %s %s %s" % (vdev, vdev, mode))
        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.add_disk failed for "
                       "userid: %s vdev: %s mode: %s rc: %s response: %s"
                       % (rh.userid, vdev, mode, result['overallRC'],
                          result['response']))
            rh.updateResults(result)
            rh.printSysLog("Exit VMCPHandler.add_disk, rc: " +
                           str(result['overallRC']))
            return result

        # Post-action verification (Privilege Class B)
        verify = self._run(['QUERY', 'MDISK', 'USERID', rh.userid, vdev, 'DETAILS'])
        if verify['overallRC'] == 0:
            rh.printSysLog("VMCPHandler.add_disk verify: "
                           "MDISK %s for %s is linked"
                           % (vdev, rh.userid))
            result['response'] = verify['response']
        else:
            rh.printLn("ES",
                       "VMCPHandler.add_disk verify: "
                       "MDISK %s not linked for %s after LINK "
                       "(QUERY MDISK rc=%s response: %s)"
                       % (vdev, rh.userid, verify['overallRC'], verify.get('response', '')))
            result = {
                'overallRC': 2,
                'rc': 2,
                'rs': 0,
                'errno': 0,
                'strError': verify.get('response', ''),
                'response': verify.get('response', ''),
                'disk_not_linked': True,
            }
            rh.updateResults(result)

        rh.printSysLog("Exit VMCPHandler.add_disk, rc: " +
                       str(result['overallRC']))
        return result
