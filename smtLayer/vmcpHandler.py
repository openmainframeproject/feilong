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
        output, rc = result["response"], result["overallRC"]
        if rc == 0:
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
        output, rc = result["response"], result["overallRC"]
        if rc == 0:
            for line in output.splitlines():
                if "IPL" in line:
                    ipl = line.strip()
                    break

        rh.printSysLog("Exit VMCPHandler.query_cplevel, ipl: " + ipl)
        return ipl
    
    def query_user(self, userid):
        """
        Query whether a specific virtual machine is logged on to z/VM.
        Input:
           userid - target virtual machine userid (str)

        Output:
           (logged_on, output)
             logged_on - True if the guest is currently logged on
             output    - raw decoded stdout; empty string on error
        """
        rh = self._rh
        rh.printSysLog("Enter VMCPHandler.query_user, userid: " + userid)

        result = self._run(["query", userid])
        output, rc = result["response"], result["overallRC"]
        logged_on = (rc == 0)

        rh.printSysLog(
            "Exit VMCPHandler.query_user, logged_on: " + str(logged_on))
        return logged_on, output

    def deactivate(self, userid, force=False):
        """
        Deactivate (log off) a virtual machine via vmcp.
        Input:
           userid - target virtual machine userid (str)
           force  - True → append IMMED to the vmcp force logoff command
                    (default False)

        Output:
           rc - 0 on success, non-zero on failure
        """
        rh = self._rh

        rh.printSysLog(
            "Enter VMCPHandler.deactivate, userid: %s force: %s"
            % (userid, str(force)))

        # Step 1: Check whether the guest is logged on.
        logged_on, _ = self.query_user(userid)
        if not logged_on:
            rh.printSysLog(
                "VMCPHandler.deactivate: %s is not logged on; "
                "nothing to do" % userid)
            rh.printSysLog(
                "Exit VMCPHandler.deactivate (already off), rc: 0")
            return 0

        rh.printSysLog(
            "VMCPHandler.deactivate: %s is logged on" % userid)

        # Step 2: Force logoff — with IMMED if -f IMMED was requested.
        args = ["force", userid, "logoff"]
        if force:
            args.append("IMMED")

        rc = self._run(args)["overallRC"]

        rh.printSysLog("Exit VMCPHandler.deactivate, rc: " + str(rc))
        return rc