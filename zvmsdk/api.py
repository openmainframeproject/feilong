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


import functools
import types

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import hostops
from zvmsdk import imageops
from zvmsdk import log
from zvmsdk import monitor
from zvmsdk import networkops
from zvmsdk import vmops


CONF = config.CONF
LOG = log.LOG

_TSTR = types.StringTypes
_TNONE = types.NoneType
_TUSERID = types.TypeType


def check_input_types(*types, **validkeys):
    """This is a function decorator to check all input parameters given to
    decorated function are in expected types.

    The checks can be skipped by specify skip_input_checks=True in decorated
    function.

    :param tuple types: expected types of input parameters to the decorated
                        function
    :param validkeys: valid keywords(str) in a list.
                      e.g. validkeys=['key1', 'key2']
    """
    def decorator(function):
        @functools.wraps(function)
        def wrap_func(*args, **kwargs):
            if args[0]._skip_input_check:
                # skip input check
                return function(*args, **kwargs)
            # drop class object self
            inputs = args[1:]
            argtypes = tuple(map(type, inputs))
            match_types = types[0:len(argtypes)]

            def _valid_userid(userid):
                if type(userid) not in _TSTR:
                    return False
                if ((userid == '') or
                    (userid.find(' ') != -1)):
                    return False
                return True

            invalid_type = False
            invalid_userid_idx = -1
            for idx in range(len(argtypes)):
                _mtypes = match_types[idx]
                if isinstance(_mtypes, tuple):
                    if tuple in map(type, _mtypes):
                        _tmtypes = ()
                        for typ in _mtypes:
                            if isinstance(typ, tuple):
                                _tmtypes += typ
                            else:
                                _tmtypes += (typ,)
                    else:
                        _tmtypes = _mtypes
                    argtype = argtypes[idx]
                    if _TUSERID in _tmtypes:
                        userid_type = True
                        for _tmtype in _tmtypes:
                            if ((argtype == _tmtype) and
                                (_tmtype != _TUSERID)):
                                userid_type = False
                        if (userid_type and
                            (not _valid_userid(inputs[idx]))):
                            invalid_userid_idx = idx
                            break
                    elif argtype not in _tmtypes:
                        invalid_type = True
                        break
                else:
                    if (_mtypes == _TUSERID):
                        if (not _valid_userid(inputs[idx])):
                            invalid_userid_idx = idx
                            break
                    elif argtypes[idx] != _mtypes:
                        invalid_type = True
                        break

            if invalid_userid_idx != -1:
                msg = ("Invalid userid found, userid should be string type and"
                       " should not be null or contain spaces.")
                LOG.info(msg)
                raise exception.ZVMInvalidInput(msg=msg)

            if invalid_type:
                msg = ("Invalid input types: %(argtypes)s; "
                       "Expected types: %(types)s" %
                       {'argtypes': str(argtypes), 'types': str(types)})
                LOG.info(msg)
                raise exception.ZVMInvalidInput(msg=msg)

            valid_keys = validkeys.get('valid_keys')
            if valid_keys:
                for k in kwargs.keys():
                    if k not in valid_keys:
                        msg = ("Invalid keyword: %(key)s; "
                               "Expected keywords are: %(keys)s" %
                               {'key': k, 'keys': str(valid_keys)})
                        LOG.info(msg)
                        raise exception.ZVMInvalidInput(msg=msg)
            return function(*args, **kwargs)
        return wrap_func
    return decorator


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self, **kwargs):
        self._vmops = vmops.get_vmops()
        self._hostops = hostops.get_hostops()
        self._networkops = networkops.get_networkops()
        self._imageops = imageops.get_imageops()
        self._monitor = monitor.get_monitor()
        self._skip_input_check = kwargs.get('skip_input_check')

    @check_input_types(_TUSERID)
    def guest_start(self, userid):
        """Power on a virtual machine.

        :param str userid: the id of the virtual machine to be power on

        :returns: None
        """
        self._vmops.guest_start(userid)

    @check_input_types(_TUSERID, int, int)
    def guest_stop(self, userid, timeout=0, retry_interval=10):
        """Power off a virtual machine.

        :param str userid: the id of the virtual machine to be power off
        :param int timeout: time to wait for GuestOS to shutdown
        :param int retry_interval: How often to signal guest while
                                   waiting for it to shutdown

        :returns: None
        """
        if retry_interval < 0:
            LOG.error('Invalid input parameter - retry_interval, '
                      'expect an integer > 0')
            raise exception.ZVMInvalidInput('retry_interval')

        self._vmops.guest_stop(userid, timeout, retry_interval)

    @check_input_types(_TUSERID)
    def guest_get_power_state(self, userid):
        """Returns power state."""
        return self._vmops.get_power_state(userid)

    @check_input_types(_TUSERID)
    def guest_get_info(self, userid):
        """Get the status of a virtual machine.

        :param str userid: the id of the virtual machine

        :returns: Dictionary contains:
                  power_state: (str) the running state, one of on | off
                  max_mem_kb: (int) the maximum memory in KBytes allowed
                  mem_kb: (int) the memory in KBytes used by the instance
                  num_cpu: (int) the number of virtual CPUs for the instance
                  cpu_time_us: (int) the CPU time used in microseconds
        """
        return self._vmops.get_info(userid)

    def host_get_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        return self._hostops.get_info()

    @check_input_types(_TSTR)
    def host_diskpool_get_info(self, disk_pool=CONF.zvm.disk_pool):
        """ Retrieve diskpool information.
        :param str disk_pool: the disk pool info. It use ':' to separate
        disk pool type and name, eg "ECKD:eckdpool" or "FBA:fbapool"
        :returns: Dictionary describing diskpool usage info
        """
        if ':' not in disk_pool:
            LOG.error('Invalid input parameter disk_pool, expect ":" in'
                      'disk_pool, eg. ECKD:eckdpool')
            raise exception.ZVMInvalidInput('disk_pool')
        diskpool_type = disk_pool.split(':')[0].upper()
        diskpool_name = disk_pool.split(':')[1]
        if diskpool_type not in ('ECKD', 'FBA'):
            LOG.error('Invalid disk pool type found in disk_pool, expect'
                      'disk_pool like ECKD:eckdpool or FBA:fbapool')
            raise exception.ZVMInvalidInput('disk_pool')

        return self._hostops.diskpool_get_info(diskpool_name)

    def host_list_guests(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        return self._hostops.list_guests()

    @check_input_types(_TUSERID, _TSTR, (_TSTR, _TNONE), (_TSTR, _TNONE))
    def guest_deploy(self, userid, image_name, transportfiles=None,
                     vdev=None):
        """ Deploy the image to vm.

        :param userid: the user id of the vm
        :param image_name: the name of image that used to deploy the vm
        :param transportfiles: the files that used to customize the vm
        :param vdev: the device that image will be deploy to

        """
        return self._vmops.guest_deploy(userid, image_name,
                                        transportfiles, vdev)

    @check_input_types(_TUSERID, list, (_TSTR, _TNONE))
    def guest_create_nic(self, userid, nic_info, ip_addr=None):
        """ Create the nic for the vm, add NICDEF record into the user direct.

        :param vm_id: the user id of the vm
        :param nic_info: the list used to contain nic info,
               including nic id and mac address
               format sample: [{'nic_id': XXX, 'mac_addr': YYY}]
        :param ip_addr: IP address of the vm

        """
        if len(nic_info) == 0:
            msg = ("no nic info is provided to create nic")
            raise exception.ZVMInvalidInput(msg)

        self._networkops.create_nic(userid, nic_info, ip_addr=ip_addr)

    @check_input_types(_TUSERID)
    def guest_get_nic_switch_info(self, userid):
        """ Return the nic and switch pair for the specified vm.

        :param userid: the user id of the vm

        :returns: Dictionary describing nic and switch info
        """
        return self._networkops.get_vm_nic_switch_info(userid)

    @check_input_types(_TUSERID, valid_keys=['nic_coupled'])
    def guest_get_definition_info(self, userid, **kwargs):
        """Get definition info for the specified guest vm, also could be used
        to check specific info.

        :param str userid: the user id of the guest vm
        :param dict kwargs: Dictionary used to check specific info in user
                            direct. Valid keywords for kwargs:
                            nic_coupled=<vdev>, where <vdev> is the virtual
                            device number of the nic to be checked the couple
                            status.
        :returns: Dictionary describing user direct and check info result
        :rtype: dict
        """
        return self._vmops.get_definition_info(userid, **kwargs)

    @check_input_types(_TSTR, _TSTR)
    def image_import(self, image_file_path, os_version):
        """import image to z/VM according to the file path and os_version

        :param image_file_path:the absolute path for image file
        :param os_version:the os version of the image

        """
        self._imageops.image_import(image_file_path, os_version)

    @check_input_types(_TUSERID, int, int, list, _TSTR)
    def guest_create(self, userid, vcpus, memory, disk_list=[],
                     user_profile=CONF.zvm.user_profile):
        """create a vm in z/VM

        :param userid: (str) the userid of the vm to be created
        :param vcpus: (int) amount of vcpus
        :param memory: (int) size of memory
        :param disk_list: (dict) a list of disks info for the guest, it has
               one dictionary that contain some of the below keys for each
               disk, the root disk should be the first element in the list.
               {'size': str,
               'format': str,
               'is_boot_disk': bool,
               'disk_pool': str}

               For example:
               [{'size': '1g',
               'is_boot_disk': True,
               'disk_pool': 'ECKD:eckdpool1'},
               {'size': '200000',
               'disk_pool': 'FBA:fbapool1',
               'format': 'ext3'}]
               In this case it will create one disk 0100(in case the vdev
               for root disk is 0100) with size 1g from ECKD disk pool
               eckdpool1 for guest , then set IPL 0100 in guest's user
               directory, and it will create 0101 with 200000 blocks from
               FBA disk pool fbapool1, and formated with ext3.
        :param user_profile: the profile for the guest
        """
        self._vmops.create_vm(userid, vcpus, memory, disk_list, user_profile)

    @check_input_types(_TSTR)
    def image_get_root_disk_size(self, image_file_name):
        """Get the root disk size of the image

        :param image_file_name: the image file name in image Repository
        :returns: the disk size in units CYL or BLK
        """
        return self._imageops.image_get_root_disk_size(image_file_name)

    @check_input_types(_TSTR, _TSTR, _TUSERID, bool)
    def guest_nic_couple_to_vswitch(self, vswitch_name, nic_vdev,
                                    userid, persist=True):
        """ Couple nic device to specified vswitch.

        :param vswitch_name: the name of the vswitch
        :param nic_vdev: nic device number
        :param userid: the user's name who owns the port
        :param persist: whether keep the change in the permanent
               configuration for the system

        """
        self._networkops.couple_nic_to_vswitch(vswitch_name, nic_vdev,
                                               userid, persist)

    @check_input_types(_TSTR, _TSTR, _TUSERID, bool)
    def guest_nic_uncouple_from_vswitch(self, vswitch_name, nic_vdev,
                                        userid, persist=True):
        """ Couple nic device to specified vswitch.

        :param vswitch_name: the name of the vswitch
        :param nic_vdev: nic device number
        :param userid: the user's name who owns the port
        :param persist: whether keep the change in the permanent
               configuration for the system

        """
        self._networkops.uncouple_nic_from_vswitch(vswitch_name,
                                                   nic_vdev,
                                                   userid, persist)

    def vswitch_get_list(self):
        """ Get the vswitch list.

        :returns: vswitch name list
        """
        return self._networkops.get_vswitch_list()

    @check_input_types(_TSTR, _TSTR, _TSTR, int, int, int, int, int, int, int,
                       int, int)
    def vswitch_create(self, name, rdev,
                       controller='*', connection=1,
                       queue_mem=8, router=0, network_type=2, vid=0,
                       port_type=1, update=1, gvrp=2, native_vid=1):
        """ Create vswitch.

        :param str name: the vswitch name
        :param str rdev: the real device number
        :param str controller: the vswitch's controller
        :param int connection: 0-unspecified 1-Actice 2-non-Active
        :param int queue_mem: the max number of megabytes on a single port
        :param int router: 0-unspecified 1-nonrouter 2-prirouter
        :param int network_type: 0-unspecified 1-IP 2-ethernet
        :param int vid: 1-4094 for access port defaut vlan
        :param int port_type: 0-unspecified 1-access 2-trunk
        :param int update: 0-unspecified 1-create 2-create and add to system
               configuration file 3-add to system configuration
        :param int gvrp: 0-unspecified 1-gvrp 2-nogvrp
        :param int native_vid: the native vlan id

        """
        if ((vid < 0) or (vid > 4094)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid vlan id should be 0-4094'))
        if ((connection < 0) or (connection > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid connection value should be 0, 1, 2'))
        if ((queue_mem < 1) or (queue_mem > 8)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid query memory value should be 0-8'))
        if ((router < 0) or (router > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid router value should be 0, 1, 2'))
        if ((network_type < 0) or (network_type > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid network type value should be 0, 1, 2'))
        if ((port_type < 0) or (port_type > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid port type value should be 0, 1, 2'))
        if ((update < 0) or (update > 3)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid update indicator should be 0, 1, 2, 3'))
        if ((gvrp < 0) or (gvrp > 2)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid GVRP value should be 0, 1, 2'))
        if (((native_vid < 1) or (native_vid > 4094)) and
            (native_vid != -1)):
            raise exception.ZVMInvalidInput(
                msg=("switch: %s add failed, %s") %
                    (name, 'valid native VLAN id should be -1 or 1-4094'))
        # if vid = 0, port_type, gvrp and native_vlanid are not
        # allowed to specified
        if int(vid) == 0:
            vid = 0
            port_type = 0
            gvrp = 0
            native_vid = -1

        self._networkops.add_vswitch(name, rdev,
                                     controller, connection, queue_mem,
                                     router, network_type, vid,
                                     port_type, update, gvrp, native_vid)

    @check_input_types((_TSTR, _TNONE))
    def image_query(self, imagekeyword=None):
        """Get the list of image names in image repository

        :param imagekeyword: The key strings that can be used to uniquely
               retrieve an image, if not specified, all image names will be
               listed

        :returns: A list that contains image names
        """
        return self._imageops.image_query(imagekeyword)

    @check_input_types(_TUSERID)
    def guest_get_console_output(self, userid):
        """Get the console output of the guest virtual machine.

        :param str userid: the user id of the vm
        :returns: console log string
        :rtype: str
        """
        return self._vmops.get_console_output(userid)

    @check_input_types(_TUSERID)
    def guest_delete(self, userid):
        """Delete guest
        :param userid: the user id of the vm

        """
        return self._vmops.delete_vm(userid)

    @check_input_types((_TUSERID, list))
    def guest_inspect_cpus(self, userid_list):
        """Get the cpu statistics of the guest virtual machines

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the cpu statistics of the vm
                  in the form {'UID1':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx
                  },
                  'UID2':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx
                  }
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_cpus(userid_list)

    @check_input_types((_TUSERID, list))
    def guest_inspect_mem(self, userid_list):
        """Get the mem usage statistics of the guest virtual machines

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the mem statistics of the vm
                  in the form {'UID1':
                  {
                  'used_mem_kb': xx,
                  'max_mem_kb': xx,
                  'min_mem_kb': xx,
                  'shared_mem_kb': xx
                  },
                  'UID2':
                  {
                  'used_mem_kb': xx,
                  'max_mem_kb': xx,
                  'min_mem_kb': xx,
                  'shared_mem_kb': xx
                  }
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_mem(userid_list)

    @check_input_types((_TUSERID, list))
    def guest_inspect_vnics(self, userid_list):
        """Get the vnics statistics of the guest virtual machines

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the vnics statistics of the vm
                  in the form
                  {'UID1':
                  [{
                  'vswitch_name': xx,
                  'nic_vdev': xx,
                  'nic_fr_rx': xx,
                  'nic_fr_tx': xx,
                  'nic_fr_rx_dsc': xx,
                  'nic_fr_tx_dsc': xx,
                  'nic_fr_rx_err': xx,
                  'nic_fr_tx_err': xx,
                  'nic_rx': xx,
                  'nic_tx': xx
                  },
                  ],
                  'UID2':
                  [{
                  'vswitch_name': xx,
                  'nic_vdev': xx,
                  'nic_fr_rx': xx,
                  'nic_fr_tx': xx,
                  'nic_fr_rx_dsc': xx,
                  'nic_fr_tx_dsc': xx,
                  'nic_fr_rx_err': xx,
                  'nic_fr_tx_err': xx,
                  'nic_rx': xx,
                  'nic_tx': xx
                  },
                  ]
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_vnics(userid_list)

    @check_input_types(_TSTR, _TUSERID)
    def vswitch_grant_user(self, vswitch_name, userid):
        """Set vswitch to grant user

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """

        self._networkops.grant_user_to_vswitch(vswitch_name, userid)

    @check_input_types(_TSTR, _TUSERID)
    def vswitch_revoke_user(self, vswitch_name, userid):
        """Revoke user for vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """
        self._networkops.revoke_user_from_vswitch(vswitch_name, userid)

    @check_input_types(_TSTR, _TUSERID, _TSTR)
    def vswitch_set_vlan_id_for_user(self, vswitch_name, userid, vlan_id):
        """Set vlan id for user when connecting to the vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        :param str vlan_id: the VLAN id
        """
        self._networkops.set_vswitch_port_vlan_id(vswitch_name,
                                                  userid, vlan_id)

    @check_input_types(_TUSERID, _TSTR, _TSTR, _TSTR)
    def guest_update_nic_definition(self, userid, nic_vdev, mac,
                                    switch_name):
        """ add nic and coupled network info into the user direct.
        :param str userid: the user id of the vm
        :param str nic_vdev: nic device number
        :param str mac: mac address
        :param str switch_name: the network name
        """
        self._networkops.update_nic_definition(userid, nic_vdev, mac,
                                               switch_name)

    @check_input_types(_TUSERID, list)
    def guest_config_minidisks(self, userid, disk_info):
        """Punch the script that used to process additional disks to vm

        :param str userid: the user id of the vm
        :param dict disk_info: a list contains disks info for the guest. It
               has one dictionary that describes the disk info for each disk.
               For example,
               [{'vdev': '0101',
               'format': 'ext3',
               'mntdir': '/mnt/0101'}]

        """
        self._vmops.guest_config_minidisks(userid, disk_info)

    @check_input_types(_TSTR)
    def image_delete(self, image_name):
        """Delete image from image repository

        :param image_name: the name of the image to be deleted

        """
        self._imageops.image_delete(image_name)

    @check_input_types(_TSTR, valid_keys=['grant_userid', 'user_vlan_id',
        'revoke_userid', 'real_device_address', 'port_name', 'controller_name',
        'connection_value', 'queue_memory_limit', 'routing_value', 'port_type',
        'persist', 'gvrp_value', 'mac_id', 'uplink', 'nic_userid', 'nic_vdev',
        'lacp', 'Interval', 'group_rdev', 'iptimeout', 'port_isolation',
        'promiscuous', 'MAC_protect', 'VLAN_counters'])
    def set_vswitch(self, vswitch_name, **kwargs):
        """Change the configuration of an existing virtual switch

        :param str vswitch_name: the name of the virtual switch
        :param dict kwargs: Dictionary used to change specific configuration.
               Valid keywords for kwargs:
               - grant_userid=<value>: A userid to be added to the access list
               - user_vlan_id=<value> : user VLAN ID. Support following ways:
               1. As single values between 1 and 4094. A maximum of four
               values may be specified, separated by blanks.
               Example: 1010 2020 3030 4040
               2. As a range of two numbers, separated by a dash (-).
               A maximum of two ranges may be specified.
               Example: 10-12 20-22
               - revoke_userid=<value>: A userid to be removed from the
               access list
               - real_device_address=<value>: The real device address or the
               real device address and OSA Express port number of a QDIO OSA
               Express device to be used to create the switch to the virtual
               adapter. If using a real device and an OSA Express port number,
               specify the real device number followed by a period(.),
               the letter 'P' (or 'p'), followed by the port number as a
               hexadecimal number. A maximum of three device addresses,
               all 1-7 characters in length, may be specified, delimited by
               blanks. 'None' may also be specified
               - port_name=<value>:  The name used to identify the OSA Expanded
               adapter. A maximum of three port names, all 1-8 characters in
               length, may be specified, delimited by blanks.
               - controller_name=<value>: One of the following:
               1. The userid controlling the real device. A maximum of eight
               userids, all 1-8 characters in length, may be specified,
               delimited by blanks.
               2. '*': Specifies that any available controller may be used
               - connection_value=<value>: One of the following values:
               CONnect: Activate the real device connection.
               DISCONnect: Do not activate the real device connection.
               - queue_memory_limit=<value>: A number between 1 and 8
               specifying the QDIO buffer size in megabytes.
               - routing_value=<value>: Specifies whether the OSA-Express QDIO
               device will act as a router to the virtual switch, as follows:
               NONrouter: The OSA-Express device identified in
               real_device_address= will not act as a router to the vswitch
               PRIrouter: The OSA-Express device identified in
               real_device_address= will act as a primary router to the vswitch
               - port_type=<value>: Specifies the port type, ACCESS or TRUNK
               - persist=<value>: one of the following values:
               NO: The vswitch is updated on the active system, but is not
               updated in the permanent configuration for the system.
               YES: The vswitch is updated on the active system and also in
               the permanent configuration for the system.
               If not specified, the default is NO.
               - gvrp_value=<value>: GVRP or NOGVRP
               - mac_id=<value>: The MAC identifier
               - uplink=<value>: One of the following:
               NO: The port being enabled is not the vswitch's UPLINK port.
               YES: The port being enabled is the vswitch's UPLINK port.
               - nic_userid=<value>: One of the following:
               1. The userid of the port to/from which the UPLINK port will
               be connected or disconnected. If a userid is specified,
               then nic_vdev= must also be specified
               2. '*': Disconnect the currently connected guest port to/from
               the special virtual switch UPLINK port. (This is equivalent
               to specifying NIC NONE on CP SET VSWITCH).
               - nic_vdev=<value>: The virtual device to/from which the the
               UPLINK port will be connected/disconnected. If this value is
               specified, nic_userid= must also be specified, with a userid.
               - lacp=<value>: One of the following values:
               ACTIVE: Indicates that the virtual switch will initiate
               negotiations with the physical switch via the link aggregation
               control protocol (LACP) and will respond to LACP packets sent
               by the physical switch.
               INACTIVE: Indicates that aggregation is to be performed,
               but without LACP.
               - Interval=<value>: The interval to be used by the control
               program (CP) when doing load balancing of conversations across
               multiple links in the group. This can be any of the following
               values:
               1 - 9990: Indicates the number of seconds between load balancing
               operations across the link aggregation group.
               OFF: Indicates that no load balancing is done.
               - group_rdev=<value>: The real device address or the real device
               address and OSA Express port number of a QDIO OSA Express device
               to be affected within the link aggregation group associated with
               this vswitch. If using a real device and an OSA Express port
               number, specify the real device number followed by a period (.),
               the letter 'P' (or 'p'), followed by the port number as a
               hexadecimal number. A maximum of eight device addresses,
               all 1-7 characters in length, may be specified, delimited by
               blanks.
               Note: If a real device address is specified, this device will be
               added to the link aggregation group associated with this
               vswitch. (The link aggregation group will be created if it does
               not already exist.)
               - iptimeout=<value>: A number between 1 and 240 specifying the
               length of time in minutes that a remote IP address table entry
               remains in the IP address table for the virtual switch.
               - port_isolation=<value> ON or OFF
               - promiscuous=<value>: One of the following:
               NO: The userid or port on the grant is not authorized to use
               the vswitch in promiscuous mode
               YES: The userid or port on the grant is authorized to use the
               vswitch in promiscuous mode.
               - MAC_protect=<value>: ON, OFF or UNSPECified
               - VLAN_counters=<value>: ON or OFF

        """
        self._networkops.set_vswitch(vswitch_name, **kwargs)
