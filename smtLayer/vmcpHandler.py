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
import re
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

    def activate(self, userid):
        """
        Activate (autolog) a specific virtual machine on z/VM.

        Input:
           userid - target virtual machine userid (str)

        Output:
           rc - return code from the VMCP XAUTOLOG command
                0 indicates successful activation; non-zero indicates an error.
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.activate, userid: " + userid)

        args = ["xautolog", userid]
        result = self._run(args)
        rc = result["overallRC"]

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

        output = re.search(r"LocalUnclearedAvail=(\d+)", frames_out)
        if output:
            free_frames += int(output.group(1))

        for value in re.findall(r"GlobalUnclearedAvail=(\d+)", frames_out):
            free_frames += int(value)

        memory_in_use = configured - free_frames
        rh.printSysLog("Exit VMCPHandler.query_image_performance, rc: " + str(rc))

        return {"overallRC": rc, "response": "MEMORY_IN_USE=%d" % memory_in_use}

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

        args = ['QUERY SSI']

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
            response.append(f"ssi_name = {ssi_name.group(1)}")
        if ssi_mode:
            response.append(f"ssi_mode = {ssi_mode.group(1)}")
        if pdr:
            response.append(f"ssi_pdr = {pdr.group(1)}_on_{pdr.group(2)}")
        if cst:
            response.append(f"cross_system_timeouts = {cst.group(1)}")

        # Parse member information
        member_pattern = re.compile(
            r"^\s*(\d+)\s+(\S+)\s+(\S+)"
            r"(?:\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})"
            r"\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2}))?$",
            re.MULTILINE
        )

        member_matches = list(member_pattern.finditer(vmcp_response))

        response.append(f"output.ssiInfoCount = {len(member_matches)}")
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
                f"{pdr_date}_{pdr_time}"
                if pdr_date and pdr_time else "N/A"
            )

            recv_hb = (
                f"{recv_date}_{recv_time}"
                if recv_date and recv_time else "N/A"
            )

            response.extend([
                f"member_slot = {slot}",
                f"member_system_id = {system_id}",
                f"member_state = {state}",
                f"member_pdr_heartbeat = {pdr_hb}",
                f"member_received_heartbeat = {recv_hb}",
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
             overallRC - return code (0 for success, 1 for failure)
             response  - VMCP command output
        """

        rh.printSysLog("Enter VMCPHandler.query_detach, userid: " + rh.userid)
        args = ["DETACH", rh.parms['vaddr'], "FROM", rh.userid]

        response = self._run(args)
        rc = response["overallRC"]

        rh.printSysLog("Exit VMCPHandler.query_detach, rc: " + str(rc))
        return response

    def query_relocate(self, rh):
        """
        Execute VMRELOCATE MOVE using VMCP.
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

        # Asynchronous
        args.append("ASYNCHRONOUS")

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

        rh.printSysLog(
            "VMCP VMRELOCATE params: " + str(args)
        )

        response = self._run(args)

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
             response - list of lines understood by _parse_vswitch_inspect_data
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
