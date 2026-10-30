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

# CP messages indicating that a virtual NIC does not exist on the target guest.
NIC_NOT_FOUND_PATTERN = r'HCP(NIC2836E|NIC040E|DTV040E)'


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

    def is_nic_coupled(self, userid, vdev):
        """
        Check whether a virtual NIC is coupled to a VSWITCH for a target guest.

        Equivalent command:
            vmcp "QUERY VSWITCH ALL DETAILS USERID <userid>"

        Input:
           userid - target virtual machine userid (str)
           vdev   - virtual device address, e.g. "1000" or "0600" (str)

        Output:
           dict with keys:
             coupled   - True if NIC is connected to a VSWITCH, False otherwise
             response  - decoded stdout string
             overallRC - 0 on success, non-zero on failure
             rc        - 0 on success, non-zero on failure
             rs        - 0
             errno     - 0
             strError  - error string if any
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.is_nic_coupled, userid: %s vdev: %s"
                       % (userid, vdev))
        vdev_norm = '%04X' % int(vdev, 16)
        result = self._run(
            ["QUERY", "VSWITCH", "ALL", "DETAILS", "USERID", userid])
        if result['overallRC'] != 0:
            return {
                'coupled': False,
                'response': result.get('response', ''),
                'overallRC': result['overallRC'],
                'rc': result['overallRC'],
                'rs': 0,
                'errno': 0,
                'strError': result.get('response', '')
            }
        response = result.get('response', '')
        # In 'QUERY VSWITCH ALL DETAILS USERID <userid>', coupled NICs appear as:
        # "Adapter Owner: <userid> NIC: <vdev>.P00 Name: ... Type: QDIO"
        pattern = r'Adapter\s+Owner:\s+%s\s+NIC:\s+%s(?:\.P\d\d|\s|$)' % (
            re.escape(userid.upper()),
            re.escape(vdev_norm))
        coupled = bool(re.search(pattern, response, re.IGNORECASE))
        rh.printSysLog("Exit VMCPHandler.is_nic_coupled, coupled: %s"
                       % coupled)
        return {
            'coupled': coupled,
            'response': response,
            'overallRC': 0,
            'rc': 0,
            'rs': 0,
            'errno': 0,
            'strError': ''
        }

    def delete_nic_for_guest(self, userid, vdev):
        """
        Detach a NIC from the active configuration of a target guest.
        First verifies whether the NIC exists using
        'QUERY NIC USERID <userid> <vdev>'.

        Equivalent command:
            vmcp "FOR <userid> CMD DETACH NIC <vdev>"

        Input:
           userid - target virtual machine userid (str)
           vdev   - virtual device address, e.g. "1000" or "0600" (str)

        Output:
           dict with keys:
             overallRC     - 0 on success, non-zero on failure
             rc            - 0 on success, non-zero on failure
             rs            - 0
             errno         - 0
             nic_not_found - True if NIC was absent before DETACH (overallRC=0)
             response      - command output string
             strError      - error output string
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.delete_nic_for_guest, "
                       "userid: %s vdev: %s" % (userid, vdev))

        vdev_norm = '%04X' % int(vdev, 16)
        # Check if NIC exists on the guest
        verify = self._run(
            ['QUERY', 'NIC', 'USERID', userid, vdev_norm],
            tolerated=NIC_NOT_FOUND_PATTERN)
        if verify['overallRC'] != 0:
            # Query failed for an unexpected reason (e.g. privilege error)
            return {
                'overallRC': verify['overallRC'],
                'rc': verify['overallRC'],
                'rs': 0,
                'errno': 0,
                'strError': verify.get('response', ''),
                'response': verify.get('response', '')
            }

        if re.search(NIC_NOT_FOUND_PATTERN, verify['response']):
            rh.printSysLog(
                "VMCPHandler.delete_nic_for_guest verify: "
                "NIC %s absent for %s before DETACH"
                % (vdev_norm, userid))
            return {
                'overallRC': 0,
                'rc': 0,
                'rs': 0,
                'errno': 0,
                'strError': verify['response'],
                'response': verify['response'],
                'nic_not_found': True
            }

        result = self._run_for(userid, "DETACH NIC %s" % vdev_norm)
        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.delete_nic_for_guest failed for "
                       "userid: %s vdev: %s rc: %s response: %s"
                       % (userid, vdev_norm, result['overallRC'],
                          result['response']))
            rh.updateResults(result)

        rh.printSysLog("Exit VMCPHandler.delete_nic_for_guest, rc: %s"
                       % result['overallRC'])
        return result

    def uncouple_nic_for_guest(self, userid, vdev):
        """
        Uncouple a NIC from its vswitch on the active configuration of a
        target guest.
        First verifies:
          1. Whether the NIC exists ('QUERY NIC USERID <userid> <vdev>').
          2. Whether the NIC is coupled ('QUERY VSWITCH ALL DETAILS USERID ...').

        Equivalent command:
            vmcp "FOR <userid> CMD UNCOUPLE <vdev>"

        Input:
           userid - target virtual machine userid (str)
           vdev   - virtual device address, e.g. "1000" or "0600" (str)

        Output:
           dict with keys:
             overallRC          - 0 on success, non-zero on failure
             rc                 - 0 on success, non-zero on failure
             rs                 - 0
             errno              - 0
             nic_not_found      - True if NIC absent before UNCOUPLE (overallRC=1)
             already_uncoupled  - True if NIC already uncoupled (overallRC=0)
             response           - command output string
             strError           - error output string
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.uncouple_nic_for_guest, "
                       "userid: %s vdev: %s" % (userid, vdev))

        vdev_norm = '%04X' % int(vdev, 16)
        # Step 1: Check if NIC exists on the guest
        verify = self._run(
            ['QUERY', 'NIC', 'USERID', userid, vdev_norm],
            tolerated=NIC_NOT_FOUND_PATTERN)
        if verify['overallRC'] != 0:
            # Query failed for an unexpected reason (e.g. privilege error)
            return {
                'overallRC': verify['overallRC'],
                'rc': verify['overallRC'],
                'rs': 0,
                'errno': 0,
                'strError': verify.get('response', ''),
                'response': verify.get('response', '')
            }

        if re.search(NIC_NOT_FOUND_PATTERN, verify['response']):
            rh.printSysLog(
                "VMCPHandler.uncouple_nic_for_guest verify: "
                "NIC %s absent for %s before UNCOUPLE"
                % (vdev_norm, userid))
            result = {
                'overallRC': 1,
                'rc': 1,
                'rs': 0,
                'errno': 0,
                'strError': verify['response'],
                'response': verify['response'],
                'nic_not_found': True
            }
            rh.updateResults(result)
            return result

        # Step 2: Check if NIC is coupled to any VSWITCH
        couple_info = self.is_nic_coupled(userid, vdev_norm)
        if couple_info['overallRC'] != 0:
            rh.printSysLog(
                "VMCPHandler.uncouple_nic_for_guest: QUERY VSWITCH failed")
            return couple_info

        if not couple_info['coupled']:
            rh.printSysLog("VMCPHandler.uncouple_nic_for_guest: "
                           "NIC %s for %s is already uncoupled"
                           % (vdev_norm, userid))
            return {
                'overallRC': 0,
                'rc': 0,
                'rs': 0,
                'errno': 0,
                'strError': '',
                'response': couple_info['response'],
                'already_uncoupled': True
            }

        # Step 3: Execute UNCOUPLE
        result = self._run_for(userid, "UNCOUPLE %s" % vdev_norm)
        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.uncouple_nic_for_guest failed for "
                       "userid: %s vdev: %s rc: %s response: %s"
                       % (userid, vdev_norm, result['overallRC'],
                          result['response']))
            rh.updateResults(result)

        rh.printSysLog("Exit VMCPHandler.uncouple_nic_for_guest, rc: %s"
                       % result['overallRC'])
        return result
