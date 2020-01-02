#!/bin/bash
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
#------------------------------------------------------------------------------
# Install and configure IUCV server daemon
#
# This bash script will:
#    -Install the IUCV server daemon, and configure the authorized user id
#     that the IUCV daemon will be talked to.
#
# Example: sh iucvseverinstaller.sh

INSTALL_CONFIG_SCRIPT_VERSION=1.0.0
AUTHORIZED_CLIENT_USERID=opncloud

function getOsVersion {
  # @Description:
  #   Returns the Linux distro version in an easy to parse format.
  # @Input:
  #   None
  # @Output:
  #   os - Variable set with OS and version information.  For example:
  #        "rhel62" or "sles11sp2"
  # @Code:
  if [[ -e "/etc/os-release" ]]; then
    os=`cat /etc/os-release | grep "^ID=" | sed \
      -e 's/ID=//' \
      -e 's/"//g'`
    version=`cat /etc/os-release | grep "^VERSION_ID=" | sed \
      -e 's/VERSION_ID=//' \
      -e 's/"//g' \
      -e 's/\.//'`
    os=$os$version

  #The /etc/SuSE-release file will be deprecated in sles11.4 and later release
  elif [[ -e "/etc/SuSE-release" ]]; then
    os='sles'
    version=`cat /etc/SuSE-release | grep "VERSION =" | sed \
      -e 's/^.*VERSION =//' \
      -e 's/\s*$//' \
      -e 's/.//' \
      -e 's/[^0-9]*([0-9]+).*/$1/'`
    os=$os$version

    # Append service level
    level=`echo "/etc/SuSE-release" | grep "LEVEL =" | sed \
      -e 's/^.*LEVEL =//' \
      -e 's/\s*$//' \
      -e 's/.//' \
      -e 's/[^0-9]*([0-9]+).*/$1/'`
    os=$os'sp'$level

  #The /etc/redhat-release file will be deprecated in rhel7 and later release
  elif [[ -e "/etc/redhat-release" ]]; then
    os='rhel'
    version=`cat /etc/redhat-release | grep -i "Red Hat Enterprise Linux Server" | sed \
      -e 's/[A-Za-z\/\.\(\)]//g' \
      -e 's/^ *//g' \
      -e 's/ *$//g' \
      -e 's/\s.*$//'`
    os=$os$version
  fi
  #echo "Detect the running os version is: "$os
  return
}


installer_Usage()
{
    echo "Usage: $0 [params]"
    echo "params can be one or more of the following:"
    echo "    --authorized-client | -a    : Input the userid of authorized client that can be communicate with iucv server daemon"
    echo "    --version | -v              : Print out iucv server daemon install and configure script version number and exit"
    echo "    --help | -h                 : Print out this help message"
    exit 1
}


function installIucvserver {
  # @Description:
  #   Install iucvserver according to os distro
  # @Input:
  #   None
  # @Output:
  #   None
  # @Code:
  if [[ ! -e "iucvserv" || ! -e "iucvserd" || ! -e "iucvserd.service" ]]; then
    echo "Error: Failed to find the install file to install iucv server daemon!"
    return 1
  fi

  # Put iucvserv to /usr/bin/iucvserv for all distros
  if [[ -e '/usr/bin/iucvserv' ]]; then
    rm -rf '/usr/bin/iucvserv'
  fi
  cp iucvserv /usr/bin/iucvserv

  # Install the service file according to linux distro
  if [[ $os == sles11* || $os == rhel6* ]]; then
    COPY_SERVICE_CMD="cp iucvserd /etc/init.d/"
    REGISTER_SERVICE_CMD="chkconfig --add iucvserd"
    START_SERVICE_CMD="service iucvserd start"
  elif [[ $os == ubuntu* || $os == rhel7* || $os == rhel8* ]]; then
    COPY_SERVICE_CMD="cp iucvserd.service /lib/systemd/system/"
    REGISTER_SERVICE_CMD="systemctl enable iucvserd.service"
    START_SERVICE_CMD="systemctl start iucvserd.service"
  elif [[ $os == sles12* ]]; then
    COPY_SERVICE_CMD="cp iucvserd.service /usr/lib/systemd/system/"
    REGISTER_SERVICE_CMD="systemctl enable iucvserd.service"
    START_SERVICE_CMD="systemctl start iucvserd.service"
  else
    echo "Error: Unknown linux distribution, fail to install iucvserver daemon!"
    exit 1
  fi

  eval $COPY_SERVICE_CMD 2>&1

  out=`eval $REGISTER_SERVICE_CMD 2>&1`
  rc=$?
  if (( rc != 0 )); then
    echo "Error: Failed to register iucvserver service on $os system due to $out"
    exit 1
  fi

  out=`eval $START_SERVICE_CMD 2>&1`
  rc=$?
  if (( rc != 0 )); then
    echo "Error: Failed to start iucvserver service on $os system due to $out"
    exit 1
  fi

  # On rhel7, install selinux policy module to enable iucv communication if selinux is enforcing
  # TODO: Similar resolution has a bug on sles and ubuntu waiting for further verify.
  if [[ $os == rhel7* && $(getenforce) == 'Enforcing' ]]; then
    out=`semodule -i iucvselx_running.pp`
    rc=$?
    if (( rc != 0 )); then
      echo "Error: Failed to install selinux policy module to allow iucv communication under enforcing state due to $out"
      exit 1
    fi
  fi
  echo "IUCV server daemon is configured and started successfully"
}


function setAuthorizedClient {
  echo "Setting the authorized client userid to be: $AUTHORIZED_CLIENT_USERID"
  echo -n $AUTHORIZED_CLIENT_USERID >/etc/iucv_authorized_userid 2>&1
}


while true
do
    case "$1" in
    -v | --version)
    echo iucvserverdaemoninstallconfig version $INSTALL_CONFIG_SCRIPT_VERSION
    exit 0
    ;;
     -h | --help)
    installer_Usage
    ;;
    -a | --authorized-client)
    AUTHORIZED_CLIENT_USERID=$2
    if test -z $AUTHORIZED_CLIENT_USERID; then
        echo "ERROR: Please input a valid authorized client userid" >&2
        exit 1
    fi
    if [[ `expr length $AUTHORIZED_CLIENT_USERID` -gt 8 ]]; then
        echo "ERROR: The length of authorized userid should not exceed 8 characters!" >&2
        exit 1
    fi
    break
    ;;
    -*)
    echo Unrecognized flag : "$1"
    installer_Usage
    ;;
    *)
    break
    ;;
    esac
done

getOsVersion
setAuthorizedClient
installIucvserver

