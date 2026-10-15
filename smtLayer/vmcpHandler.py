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
        """
        Query OSA for rh.userid.

        Returns a standard results dict.
        """
        OSA_info = {}

        result = self._run(['QUERY', 'OSA'])
        if result['overallRC'] != 0:
            return OSA_info

        output = result.get('response', '')
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 3 or parts[0] != 'OSA':
                continue

            osa_addr = parts[1]
            status_word = parts[2]

            osa_type = 'OSA'
            if 'DEVTYPE' in parts:
                dt_idx = parts.index('DEVTYPE')
                if dt_idx + 1 < len(parts):
                    osa_type = parts[dt_idx + 1]

            if osa_type not in OSA_info:
                OSA_info[osa_type] = {
                    'FREE': [], 'BOXED': [], 'OFFLINE': [], 'ATTACHED': []}

            if status_word == 'ATTACHED':
                attached_id = parts[4] if len(parts) > 4 else 'UNKNOWN'
                OSA_info[osa_type]['ATTACHED'].append((attached_id, osa_addr))
            elif status_word in OSA_info[osa_type]:
                OSA_info[osa_type][status_word].append(osa_addr)

        return OSA_info
