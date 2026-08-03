import subprocess

from smtLayer import msgs

modId = 'VCP'


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
            msg = msgs.msg['0405'][1] % (modId, strCmd, strCmd, e.output)
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

    def query_fcp(self):
        """
        Query FCP devices and return raw CP output.

        Replaces: smcli System_WWPN_Query
        CP command: QUERY FCP WWPN
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_fcp, userid: " + rh.userid)
        result = self._run(['QUERY', 'FCP', 'WWPN'])
        if result['overallRC'] != 0:
            result['rc'] = 4
            result['rs'] = 28
        rh.printSysLog("Exit VMCPHandler.query_fcp, rc: " +
                       str(result['overallRC']))
        return result

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

            # line3: ATTACHED TO <userid>  -or-  FREE
            parts3 = line3.split()
            if parts3 and parts3[0].upper() == 'ATTACHED':
                # "ATTACHED TO <userid>"
                status = 'Active'
                owner = parts3[2] if len(parts3) > 2 else 'NONE'
            else:
                status = 'Free'
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
