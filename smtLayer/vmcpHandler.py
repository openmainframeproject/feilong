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

    def delete_nic_for_guest(self, userid, vdev):
        """
        Detach a NIC from the active configuration of a target guest.

        Equivalent command:
            vmcp "FOR <userid> CMD DETACH NIC <vdev>"

        Returns:
           dict with keys:
            response   - decoded stdout/stderr string
            overallRC   0  — NIC confirmed gone (success)
                        1  — FOR rejected (auth / guest-not-on)
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.delete_nic_for_guest, "
                       "userid: %s vdev: %s" % (userid, vdev))

        result = self._run_for(userid, "DETACH NIC %s" % vdev)

        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.delete_nic_for_guest failed for "
                       "userid: %s vdev: %s rc: %s response: %s"
                       % (userid, vdev, result['overallRC'],
                          result['response']))
            rh.updateResults(result)
            rh.printSysLog("Exit VMCPHandler.delete_nic_for_guest, rc: " +
                           str(result['overallRC']))
            return result

        rh.printSysLog("Exit VMCPHandler.delete_nic_for_guest, rc: " +
                    str(result['overallRC']))
        return result

    def uncouple_nic_for_guest(self, userid, vdev):
        """
        Uncouple a NIC from its vswitch on the active configuration of a
        target guest.

        Equivalent command:
            vmcp "FOR <userid> CMD UNCOUPLE <vdev>"

        Returns:
           dict with keys:
            overallRC   0  — NIC confirmed uncoupled (success)
                        1  — FOR rejected (auth / guest-not-on)
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.uncouple_nic_for_guest, "
                       "userid: %s vdev: %s" % (userid, vdev))

        result = self._run_for(userid, "UNCOUPLE %s" % vdev)

        if result['overallRC'] != 0:
            rh.printLn("ES",
                       "VMCPHandler.uncouple_nic_for_guest failed for "
                       "userid: %s vdev: %s rc: %s response: %s"
                       % (userid, vdev, result['overallRC'],
                          result['response']))
            rh.updateResults(result)
            rh.printSysLog("Exit VMCPHandler.uncouple_nic_for_guest, rc: " +
                           str(result['overallRC']))
            return result

        rh.printSysLog("Exit VMCPHandler.uncouple_nic_for_guest, rc: " +
                    str(result['overallRC']))
        return result
