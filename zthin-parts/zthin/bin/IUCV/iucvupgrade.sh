#!/bin/bash
#  SPDX-License-Identifier: Apache-2.0
#
#  Copyright 2025 Contributors to the Feilong Project.
#  Copyright 2017 IBM Corp.
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

# Get linux version
name=`cat /etc/*release|egrep -i 'Red Hat|Suse|Ubuntu'`
lnx_name=`echo ${name#*\"}|awk '{print $1}'`
version=`cat /etc/*release|egrep '^VERSION=|^VERSION =|Red Hat'`
lnx_version=`echo $version|grep -o '[0-9]\+'|head -1`

echo $lnx_name $lnx_version >>/var/log/messages

rollback_rhel_ubuntu(){
    echo "Enter rollback" >>/var/log/messages
    if [ -f /lib/systemd/system/iucvserd.service.old ]; then
        mv /lib/systemd/system/iucvserd.service.old /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    fi
    if [ -f /usr/bin/iucvserv.old ]; then
        mv /usr/bin/iucvserv.old /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    fi
    systemctl restart iucvserd >>/var/log/messages
}

rollback_sles(){
    if [ -f /usr/lib/systemd/system/iucvserd.service.old ]; then
        mv /usr/lib/systemd/system/iucvserd.service.old /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    fi
    if [ -f /usr/bin/iucvserv.old ]; then
        mv /usr/bin/iucvserv.old /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    fi
    systemctl restart iucvserd >>/var/log/messages
}

# Replace iucvserver files
# RHEL and Ubuntu
if [[ "$lnx_name" = "Red" ]] || [[ "$lnx_name" = "Ubuntu" ]]; then
    echo "target system: rhel or ubuntu" >>/var/log/messages
    pkill iucvserv >>/var/log/messages
    mv /lib/systemd/system/iucvserd.service /lib/systemd/system/iucvserd.service.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel_ubuntu
        exit 1
    fi
    mv /usr/bin/iucvserv /usr/bin/iucvserv.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel_ubuntu
        exit 1
    fi
    mv /usr/bin/iucvserv.new /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel_ubuntu
        exit 1
    fi
    mv /lib/systemd/system/iucvserd.service.new /lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_rhel_ubuntu
        exit 1
    fi
    systemctl daemon-reload >>/var/log/messages
    systemctl start iucvserd.service >>/var/log/messages

    # roll back
    ps_iucv=`ps -ef|grep -c iucvserv`
    if [[ $ps_iucv -lt 2 ]]; then
        rollback_rhel_ubuntu
        exit 1
    fi

# SLES
elif [[ "$lnx_name" = "SUSE" ]]; then
    echo "target system: sles" >>/var/log/messages
    pkill iucvserv >>/var/log/messages
    mv /usr/lib/systemd/system/iucvserd.service /usr/lib/systemd/system/iucvserd.service.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles
        exit 1
    fi
    mv /usr/bin/iucvserv /usr/bin/iucvserv.old 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles
        exit 1
    fi
    mv /usr/bin/iucvserv.new /usr/bin/iucvserv 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles
        exit 1
    fi
    mv /usr/lib/systemd/system/iucvserd.service.new /usr/lib/systemd/system/iucvserd.service 2>/dev/nul >>/var/log/messages
    if [ $? -ne 0 ]; then
        rollback_sles
        exit 1
    fi
    systemctl daemon-reload >>/var/log/messages
    systemctl start iucvserd.service >>/var/log/messages

    # roll back
    ps_iucv=`ps -ef|grep -c iucvserv`
    if [[ $ps_iucv -lt 2 ]]; then
        rollback_sles
        exit 1
    fi
fi
