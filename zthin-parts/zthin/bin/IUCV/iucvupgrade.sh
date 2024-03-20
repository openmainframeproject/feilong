#!/bin/bash
#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017 IBM Corp.
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
#
# Change Activity:
#

# Get linux version
name=`cat /etc/*release|egrep -i 'Red Hat|Suse|Ubuntu'`
lnx_name=`echo ${name#*\"}|awk '{print $1}'`
version=`cat /etc/*release|egrep '^VERSION=|^VERSION =|Red Hat'`
lnx_version=`echo $version|grep -o '[0-9]\+'|head -1`

echo $lnx_name $lnx_version >>/var/log/messages

rollback_rhel6_sles11(){
    echo "Enter rollback" >>/var/log/messages
    if [ -f /etc/init.d/iucvserd.old ]; then
        mv /etc/init.d/iucvserd.old /etc/init.d/iucvserd 2>/dev/nul >>/var/log/messages
    fi
    if [ -f /usr/bin/iucvserv.old ]; then
        mv /usr/bin/iucvserv.old /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    fi
    service iucvserd restart >>/var/log/messages
}

rollback_rhel7_ubuntu(){
    echo "Enter rollback" >>/var/log/messages
    if [ -f /lib/systemd/system/iucvserd.service.old ]; then
        mv /lib/systemd/system/iucvserd.service.old /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    fi
    if [ -f /usr/bin/iucvserv.old ]; then
        mv /usr/bin/iucvserv.old /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    fi
    systemctl restart iucvserd >>/var/log/messages
}

rollback_sles12(){
    if [ -f /usr/lib/systemd/system/iucvserd.service.old ]; then
        mv /usr/lib/systemd/system/iucvserd.service.old /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    fi
    if [ -f /usr/bin/iucvserv.old ]; then
        mv /usr/bin/iucvserv.old /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    fi
    systemctl restart iucvserd >>/var/log/messages
}

# Replace iucvserver files
# Rhel6 and Sles11
if [[ "$lnx_name" = "Red" && $lnx_version -lt 7 ]] || [[ "$lnx_name" = "SUSE" && $lnx_version -lt 12 ]]; then
    echo "target system: rhel6 or sles11" >>/var/log/messages
    service iucvserd stop >>/var/log/messages
    mv /etc/init.d/iucvserd /etc/init.d/iucvserd.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel6_sles11
        exit 1
    fi
    mv /usr/bin/iucvserv /usr/bin/iucvserv.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel6_sles11
        exit 1
    fi
    mv /usr/bin/iucvserv.new /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel6_sles11
        exit 1
    fi
    mv /etc/init.d/iucvserd.new /etc/init.d/iucvserd 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel6_sles11
        exit 1
    fi
    ps -ef|grep iucv >>/var/log/messages
    netstat -napo|grep iucvserv >>/var/log/messages
    service iucvserd restart >>/var/log/messages

    # roll back
    ps_iucv=`ps -ef|grep -c iucvserv`
    if [[ $ps_iucv -lt 2 ]]; then
        rollback_rhel6_sles11
        exit 1
    fi

# Above Rhel7 and Ubuntu
elif [[ "$lnx_name" = "Red" && $lnx_version -ge 7 ]] || [[ "$lnx_name" = "Ubuntu" ]]; then
    echo "target system: rhel7 or ubuntu" >>/var/log/messages
    pkill iucvserv >>/var/log/messages
    mv /lib/systemd/system/iucvserd.service /lib/systemd/system/iucvserd.service.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel7_ubuntu
        exit 1
    fi
    mv /usr/bin/iucvserv /usr/bin/iucvserv.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel7_ubuntu
        exit 1
    fi
    mv /usr/bin/iucvserv.new /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel7_ubuntu
        exit 1
    fi
    mv /lib/systemd/system/iucvserd.service.new /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel7_ubuntu
        exit 1
    fi
    systemctl daemon-reload >>/var/log/messages
    systemctl start iucvserd.service >>/var/log/messages

    # roll back
    ps_iucv=`ps -ef|grep -c iucvserv`
    if [[ $ps_iucv -lt 2 ]]; then
        rollback_rhel7_ubuntu
        exit 1
    fi

# Above Sles12
elif [[ "$lnx_name" = "SUSE" && $lnx_version -ge 12 ]]; then
    echo "target system: sles12" >>/var/log/messages
    pkill iucvserv >>/var/log/messages
    mv /usr/lib/systemd/system/iucvserd.service /usr/lib/systemd/system/iucvserd.service.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles12
        exit 1
    fi
    mv /usr/bin/iucvserv /usr/bin/iucvserv.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles12
        exit 1
    fi
    mv /usr/bin/iucvserv.new /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles12
        exit 1
    fi
    mv /usr/lib/systemd/system/iucvserd.service.new /usr/lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles12
        exit 1
    fi
    systemctl daemon-reload >>/var/log/messages
    systemctl start iucvserd.service >>/var/log/messages

    # roll back
    ps_iucv=`ps -ef|grep -c iucvserv`
    if [[ $ps_iucv -lt 2 ]]; then
        rollback_sles12
        exit 1
    fi
fi
