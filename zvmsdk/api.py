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


from zvmsdk import config
from zvmsdk import constants
from zvmsdk import exception
from zvmsdk import hostops
from zvmsdk import imageops
from zvmsdk import log
from zvmsdk import monitor
from zvmsdk import networkops
from zvmsdk import vmops
from zvmsdk import volumeop
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG


_TSTR = constants._TSTR
_TNONE = constants._TNONE
_TSTR_OR_NONE = constants._TSTR_OR_NONE
_INT_OR_NONE = constants._INT_OR_NONE
_INT_OR_TSTR = constants._INT_OR_TSTR
_TUSERID = constants._TUSERID
# Vswitch name has same rule with userid
_TVSWNAME = constants._TVSWNAME
_TUSERID_OR_LIST = constants._TUSERID_OR_LIST


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self, **kwargs):
        self._vmops = vmops.get_vmops()
        self._hostops = hostops.get_hostops()
        self._networkops = networkops.get_networkops()
        self._imageops = imageops.get_imageops()
        self._monitor = monitor.get_monitor()
        self._volumeop = volumeop.get_volumeop()
        self._skip_input_check = kwargs.get('skip_input_check')

    @zvmutils.check_input_types(_TUSERID)
    def guest_start(self, userid):
        """Power on a virtual machine.

        :param str userid: the id of the virtual machine to be power on

        :returns: None
        """
        self._vmops.guest_start(userid)

    @zvmutils.check_input_types(_TUSERID, int, int)
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

    @zvmutils.check_input_types(_TUSERID)
    def guest_restart(self, userid):
        """Soft restart estart a virtual machine
        :param str userid: the id of the virtual machine to be reboot
        :returns: None
        """
        self._vmops.guest_restart(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_reset(self, userid):
        """reset a virtual machine
        :param str userid: the id of the virtual machine to be reset
        :returns: None
        """
        self._vmops.guest_reset(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_get_power_state(self, userid):
        """Returns power state."""
        return self._vmops.get_power_state(userid)

    @zvmutils.check_input_types(_TUSERID)
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

    def guest_list(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        return self._vmops.guest_list()

    def host_get_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        return self._hostops.get_info()

    @zvmutils.check_input_types(_TSTR)
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

    @zvmutils.check_input_types(_TSTR)
    def image_delete(self, image_name):
        """Delete image from image repository

        :param image_name: the name of the image to be deleted
        :raises: none

        """
        self._imageops.image_delete(image_name)

    @zvmutils.check_input_types(_TSTR)
    def image_get_root_disk_size(self, image_file_name):
        """Get the root disk size of the image

        :param image_file_name: the image file name in image Repository
        :returns: the disk size in units CYL or BLK
        """
        return self._imageops.image_get_root_disk_size(image_file_name)

    @zvmutils.check_input_types(_TSTR, dict, _TSTR_OR_NONE)
    def image_import(self, url, image_meta={}, remote_host=None):
        """Import image to zvmsdk image repository

        :param str url: image url to specify the location of image such as
               http://netloc/path/to/file.tar.gz.0
               https://netloc/path/to/file.tar.gz.0
               file:///path/to/file.tar.gz.0
        :param dict image_meta:
               a dictionary to describe the image info. such as md5sum,
               os_version. For example:
               {'os_version': 'rhel6.2',
               'md5sum': ' 46f199c336eab1e35a72fa6b5f6f11f5'}
        :param string remote_host:
                if the image url schema is file, the remote_host is used to
                indicate where the image comes from, the format is username@IP
                eg. nova@192.168.99.1, the default value is None, it indicate
                the image is from a local file system. If the image url schema
                is http/https, this value will be useless
        :raises ZVMImageError if:
                - All kinds of xCAT call failure
                - xCAT MN's root user is not authorized by the user of
                  the source image server
                - Free space is not enough in image repository
        """

        self._imageops.image_import(url, image_meta=image_meta,
                                    remote_host=remote_host)

    @zvmutils.check_input_types(_TSTR_OR_NONE)
    def image_query(self, imagekeyword=None):
        """Get the list of image names in image repository

        :param imagekeyword: The key strings that can be used to retrieve
               images, if CONF.zvm.client_type=='xcat', the images will be
               stored in xCAT's image repository, the imagekeyword should be
               the string from image's profile field, Otherwise, the
               imagekeyword should be the string from image name, if not
               specified, all image names will be listed

        :returns: A list that contains image names
        :raises: ZVMImageError if:
                 - All kinds of xCAT call failure
        """
        return self._imageops.image_query(imagekeyword)

    @zvmutils.check_input_types(_TUSERID, _TSTR, _TSTR_OR_NONE, _TSTR_OR_NONE,
                       _TSTR_OR_NONE)
    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        """ Deploy the image to vm.

        :param userid: (str) the user id of the vm
        :param image_name: (str) the name of image that used to deploy the vm
        :param transportfiles: (str) the files that used to customize the vm
        :param remotehost: the server where the transportfiles located, the
               format is username@IP, eg nova@192.168.99.1
        :param vdev: (str) the device that image will be deploy to

        :raises ZVMXCATDeployNodeFailed if:
                - Failed to deploy image to guest, refer to the error message
                  for details

        """
        return self._vmops.guest_deploy(userid, image_name,
                                        transportfiles, remotehost, vdev)

    @zvmutils.check_input_types(_TUSERID, _TSTR_OR_NONE, _TSTR_OR_NONE,
                       _TSTR_OR_NONE, _TSTR_OR_NONE, bool)
    def guest_create_nic(self, userid, vdev=None, nic_id=None,
                         mac_addr=None, ip_addr=None, active=False):
        """ Create the nic for the vm, add NICDEF record into the user direct.

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param str nic_id: nic identifier
        :param str mac_addr: mac address, it is only be used when changing
               the guest's user direct. Format should be xx:xx:xx:xx:xx:xx,
               and x is a hexadecimal digit
        :param str ip_addr: the management IP address of the guest, it should
               be the value between 0.0.0.0-255.255.255.255
        :param bool active: whether add a nic on active guest system

        :returns: nic device number, 1- to 4- hexadecimal digits
        :rtype: str

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
                - Invalid mac address or IP address format is provided
                - The specified virtual device number has already been used
        :raises ZVMNetworkError if:
                - The virtual device number is out of the range
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        if mac_addr is not None:
            if not zvmutils.valid_mac_addr(mac_addr):
                raise exception.ZVMInvalidInput(
                    msg=("Invalid mac address, format should be "
                         "xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit"))
        if ip_addr is not None:
            if not zvmutils.valid_IP(ip_addr):
                raise exception.ZVMInvalidInput(
                    msg=("Invalid management IP address, it should be the "
                         "value between 0.0.0.0 and 255.255.255.255"))
        return self._networkops.create_nic(userid, vdev=vdev, nic_id=nic_id,
                                           mac_addr=mac_addr, ip_addr=ip_addr,
                                           active=active)

    @zvmutils.check_input_types(_TUSERID, _TSTR, bool)
    def guest_delete_nic(self, userid, vdev, active=False):
        """ delete the nic for the vm

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether delete a nic on active guest system

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail

        """
        self._networkops.delete_nic(userid, vdev, active=active)

    @zvmutils.check_input_types(_TUSERID)
    def guest_get_nic_vswitch_info(self, userid):
        """ Return the nic and switch pair for the specified vm.

        :param str userid: the user id of the vm

        :returns: Dictionary describing nic and switch info, format is
                  {'vdev': 'vswitch'}, such as
                  {'1000': 'VSWITCH1', '1003': 'VSWITCH2'}
        :rtype: dict

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        """
        return self._networkops.get_vm_nic_vswitch_info(userid)

    @zvmutils.check_input_types(_TUSERID, valid_keys=['nic_coupled'])
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

    @zvmutils.check_input_types(_TUSERID, int, int, list, _TSTR)
    def guest_create(self, userid, vcpus, memory, disk_list=[],
                     user_profile=CONF.zvm.user_profile):
        """create a vm in z/VM

        :param userid: (str) the userid of the vm to be created
        :param vcpus: (int) amount of vcpus
        :param memory: (int) size of memory in MB
        :param disk_list: (dict) a list of disks info for the guest.
               It has one dictionary that contain some of the below keys for
               each disk, the root disk should be the first element in the
               list, the format is:
               {'size': str,
               'format': str,
               'is_boot_disk': bool,
               'disk_pool': str}

               In which, 'size': case insensitive, the unit can be in
               Megabytes (M), Gigabytes (G), or number of cylinders/blocks, eg
               512M, 1g or just 2000.
               'format': can be ext2, ext3, ext4, xfs.
               'is_boot_disk': only root disk need to set this key.
               'disk_pool': optional, if not specified, the disk will be
               created by using the value from configure file,the format is
               ECKD:eckdpoolname or FBA:fbapoolname.

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

        :raises ZVMInvalidInput if:
                - Input parameters are not proper
        :raises ZVMCreateVMFailed if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        if disk_list:
            for disk in disk_list:
                if not isinstance(disk, dict):
                    errmsg = ('Invalid "disk_list" input, it should be a '
                              'dictionary. Details could be found in doc.')
                    raise exception.ZVMInvalidInput(msg=errmsg)

                if 'size' not in disk.keys():
                    errmsg = ('Invalid "disk_list" input, "size" is required '
                              'for each disk.')
                    raise exception.ZVMInvalidInput(msg=errmsg)

                disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
                if ':' not in disk_pool or (disk_pool.split(':')[0].upper()
                    not in ['ECKD', 'FBA']):
                    errmsg = ("Invalid disk_pool input, it should be in format"
                              " ECKD:eckdpoolname or FBA:fbapoolname")
                    raise exception.ZVMInvalidInput(msg=errmsg)

        self._vmops.create_vm(userid, vcpus, memory, disk_list, user_profile)

    @zvmutils.check_input_types(_TUSERID, _TSTR, _TVSWNAME, bool)
    def guest_nic_couple_to_vswitch(self, userid, nic_vdev,
                                    vswitch_name, active=False):
        """ Couple nic device to specified vswitch.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param str vswitch_name: the name of the vswitch
        :param bool active: whether make the change on active guest system

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail

        """
        self._networkops.couple_nic_to_vswitch(userid, nic_vdev,
                                               vswitch_name, active=active)

    @zvmutils.check_input_types(_TUSERID, _TSTR, bool)
    def guest_nic_uncouple_from_vswitch(self, userid, nic_vdev,
                                        active=False):
        """ Couple nic device to specified vswitch.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether make the change on active guest system

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        self._networkops.uncouple_nic_from_vswitch(userid, nic_vdev,
                                                   active=active)

    def vswitch_get_list(self):
        """ Get the vswitch list.

        :returns: vswitch name list
        :rtype: list

        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
        """
        return self._networkops.get_vswitch_list()

    @zvmutils.check_input_types(_TVSWNAME, _TSTR_OR_NONE, _TUSERID, _TSTR,
                                _TSTR, _TSTR, _INT_OR_TSTR, _TSTR, _TSTR,
                                int, _INT_OR_NONE, bool)
    def vswitch_create(self, name, rdev=None, controller='*',
                       connection='CONNECT', network_type='IP',
                       router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                       gvrp='GVRP', queue_mem=8, native_vid=1,
                       persist=True):
        """ Create vswitch.

        :param str name: the vswitch name
        :param str rdev: the real device number, a maximum of three devices,
               all 1-4 characters in length, delimited by blanks. 'NONE'
               may also be specified
        :param str controller: the vswitch's controller, it could be the userid
               controlling the real device, or '*' to specifies that any
               available controller may be used
        :param str connection:
            - CONnect:
                Activate the real device connection.
            - DISCONnect:
                Do not activate the real device connection.
            - NOUPLINK:
                The vswitch will never have connectivity through
                the UPLINK port
        :param str network_type: Specifies the transport mechanism to be used
               for the vswitch, as follows: IP, ETHERNET
        :param str router:
            - NONrouter:
                The OSA-Express device identified in
                real_device_address= will not act as a router to the
                vswitch
            - PRIrouter:
                The OSA-Express device identified in
                real_device_address= will act as a primary router to the
                vswitch
            - Note: If the network_type is ETHERNET, this value must be
                unspecified, otherwise, if this value is unspecified, default
                is NONROUTER
        :param str/int vid: the VLAN ID. This can be any of the following
               values: UNAWARE, AWARE or 1-4094
        :param str port_type:
            - ACCESS:
                The default porttype attribute for
                guests authorized for the virtual switch.
                The guest is unaware of VLAN IDs and sends and
                receives only untagged traffic
            - TRUNK:
                The default porttype attribute for
                guests authorized for the virtual switch.
                The guest is VLAN aware and sends and receives tagged
                traffic for those VLANs to which the guest is authorized.
                If the guest is also authorized to the natvid, untagged
                traffic sent or received by the guest is associated with
                the native VLAN ID (natvid) of the virtual switch.
        :param str gvrp:
            - GVRP:
                Indicates that the VLAN IDs in use on the virtual
                switch should be registered with GVRP-aware switches on the
                LAN. This provides dynamic VLAN registration and VLAN
                registration removal for networking switches. This
                eliminates the need to manually configure the individual
                port VLAN assignments.
            - NOGVRP:
                Do not register VLAN IDs with GVRP-aware switches on
                the LAN. When NOGVRP is specified VLAN port assignments
                must be configured manually
        :param int queue_mem: A number between 1 and 8, specifying the QDIO
               buffer size in megabytes.
        :param int native_vid: the native vlan id, 1-4094 or None
        :param bool persist: whether create the vswitch in the permanent
               configuration for the system

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
                - The value of queue_mem or native_vid is out of the range
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail

        """
        if ((queue_mem < 1) or (queue_mem > 8)):
            raise exception.ZVMInvalidInput(
                msg=("Failed to create vswitch %s: %s") %
                    (name, 'valid query memory value should be 1-8'))

        if network_type.upper() == 'ETHERNET':
            router = None

        self._networkops.add_vswitch(name, rdev=rdev, controller=controller,
                                     connection=connection,
                                     network_type=network_type,
                                     router=router, vid=vid,
                                     port_type=port_type, gvrp=gvrp,
                                     queue_mem=queue_mem,
                                     native_vid=native_vid,
                                     persist=persist)

    @zvmutils.check_input_types(_TUSERID)
    def guest_get_console_output(self, userid):
        """Get the console output of the guest virtual machine.

        :param str userid: the user id of the vm
        :returns: console log string
        :rtype: str
        """
        return self._vmops.get_console_output(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_delete(self, userid):
        """Delete guest.

        :param userid: the user id of the vm

        :raises ZVMDeleteVMFailed if:
                - All kinds of xCAT call failure, refer to the message for
                  details

        """
        return self._vmops.delete_vm(userid)

    @zvmutils.check_input_types(_TUSERID_OR_LIST)
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

        :raises: None
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_cpus(userid_list)

    @zvmutils.check_input_types(_TUSERID_OR_LIST)
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
        :raises: None
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_mem(userid_list)

    @zvmutils.check_input_types(_TUSERID_OR_LIST)
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

        :raises: None
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        return self._monitor.inspect_vnics(userid_list)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID)
    def vswitch_grant_user(self, vswitch_name, userid):
        """Set vswitch to grant user

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail

        """

        self._networkops.grant_user_to_vswitch(vswitch_name, userid)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID)
    def vswitch_revoke_user(self, vswitch_name, userid):
        """Revoke user for vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm

        :raises ZVMInvalidInput:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        self._networkops.revoke_user_from_vswitch(vswitch_name, userid)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID, int)
    def vswitch_set_vlan_id_for_user(self, vswitch_name, userid, vlan_id):
        """Set vlan id for user when connecting to the vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        :param int vlan_id: the VLAN id

        :raises ZVMInvalidInput:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        self._networkops.set_vswitch_port_vlan_id(vswitch_name,
                                                  userid, vlan_id)

    @zvmutils.check_input_types(_TUSERID, list)
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

    @zvmutils.check_input_types(_TVSWNAME, valid_keys=['grant_userid',
        'user_vlan_id', 'revoke_userid', 'real_device_address',
        'port_name', 'controller_name', 'connection_value',
        'queue_memory_limit', 'routing_value', 'port_type',
        'persist', 'gvrp_value', 'mac_id', 'uplink', 'nic_userid', 'nic_vdev',
        'lacp', 'Interval', 'group_rdev', 'iptimeout', 'port_isolation',
        'promiscuous', 'MAC_protect', 'VLAN_counters'])
    def vswitch_set(self, vswitch_name, **kwargs):
        """Change the configuration of an existing virtual switch

        :param str vswitch_name: the name of the virtual switch
        :param dict kwargs:
            - grant_userid=<value>:
                A userid to be added to the access list
            - user_vlan_id=<value>:
                user VLAN ID. Support following ways:
                1. As single values between 1 and 4094. A maximum of four
                values may be specified, separated by blanks.
                Example: 1010 2020 3030 4040
                2. As a range of two numbers, separated by a dash (-).
                A maximum of two ranges may be specified.
                Example: 10-12 20-22
            - revoke_userid=<value>:
                A userid to be removed from the access list
            - real_device_address=<value>:
                The real device address or the real device address and
                OSA Express port number of a QDIO OSA
                Express device to be used to create the switch to the virtual
                adapter. If using a real device and an OSA Express port number,
                specify the real device number followed by a period(.),
                the letter 'P' (or 'p'), followed by the port number as a
                hexadecimal number. A maximum of three device addresses,
                all 1-7 characters in length, may be specified, delimited by
                blanks. 'None' may also be specified
            - port_name=<value>:
                The name used to identify the OSA Expanded
                adapter. A maximum of three port names, all 1-8 characters in
                length, may be specified, delimited by blanks.
            - controller_name=<value>:
                One of the following:
                1. The userid controlling the real device. A maximum of eight
                userids, all 1-8 characters in length, may be specified,
                delimited by blanks.
                2. '*': Specifies that any available controller may be used
            - connection_value=<value>:
                One of the following values:
                CONnect: Activate the real device connection.
                DISCONnect: Do not activate the real device connection.
            - queue_memory_limit=<value>:
                A number between 1 and 8
                specifying the QDIO buffer size in megabytes.
            - routing_value=<value>:
                Specifies whether the OSA-Express QDIO
                device will act as a router to the virtual switch, as follows:
                NONrouter: The OSA-Express device identified in
                real_device_address= will not act as a router to the vswitch
                PRIrouter: The OSA-Express device identified in
                real_device_address= will act as a primary router to the
                vswitch
            - port_type=<value>:
                Specifies the port type, ACCESS or TRUNK
            - persist=<value>:
                one of the following values:
                NO: The vswitch is updated on the active system, but is not
                updated in the permanent configuration for the system.
                YES: The vswitch is updated on the active system and also in
                the permanent configuration for the system.
                If not specified, the default is NO.
            - gvrp_value=<value>:
                GVRP or NOGVRP
            - mac_id=<value>:
                A unique identifier (up to six hexadecimal
                digits) used as part of the vswitch MAC address
            - uplink=<value>:
                One of the following:
                NO: The port being enabled is not the vswitch's UPLINK port.
                YES: The port being enabled is the vswitch's UPLINK port.
            - nic_userid=<value>:
                One of the following:
                1. The userid of the port to/from which the UPLINK port will
                be connected or disconnected. If a userid is specified,
                then nic_vdev= must also be specified
                2. '*': Disconnect the currently connected guest port to/from
                the special virtual switch UPLINK port. (This is equivalent
                to specifying NIC NONE on CP SET VSWITCH).
            - nic_vdev=<value>:
                The virtual device to/from which the the
                UPLINK port will be connected/disconnected. If this value is
                specified, nic_userid= must also be specified, with a userid.
            - lacp=<value>:
                One of the following values:
                ACTIVE: Indicates that the virtual switch will initiate
                negotiations with the physical switch via the link aggregation
                control protocol (LACP) and will respond to LACP packets sent
                by the physical switch.
                INACTIVE: Indicates that aggregation is to be performed,
                but without LACP.
            - Interval=<value>:
                The interval to be used by the control
                program (CP) when doing load balancing of conversations across
                multiple links in the group. This can be any of the following
                values:
                1 - 9990: Indicates the number of seconds between load
                balancing operations across the link aggregation group.
                OFF: Indicates that no load balancing is done.
            - group_rdev=<value>:
                The real device address or the real device
                address and OSA Express port number of a QDIO OSA Express
                devcie to be affected within the link aggregation group
                associated with this vswitch. If using a real device and an OSA
                Express port number, specify the real device number followed
                by a period (.), the letter 'P' (or 'p'), followed by the port
                number as a hexadecimal number. A maximum of eight device
                addresses all 1-7 characters in length, may be specified,
                delimited by blanks.
                Note: If a real device address is specified, this device will
                be added to the link aggregation group associated with this
                vswitch. (The link aggregation group will be created if it does
                not already exist.)
            - iptimeout=<value>:
                A number between 1 and 240 specifying the
                length of time in minutes that a remote IP address table entry
                remains in the IP address table for the virtual switch.
            - port_isolation=<value>:
                ON or OFF
            - promiscuous=<value>:
                One of the following:
                NO: The userid or port on the grant is not authorized to use
                the vswitch in promiscuous mode
                YES: The userid or port on the grant is authorized to use the
                vswitch in promiscuous mode.
            - MAC_protect=<value>:
                ON, OFF or UNSPECified
            - VLAN_counters=<value>:
                ON or OFF

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
                - Invalid keyword in the input dictionary
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail

        """
        self._networkops.set_vswitch(vswitch_name, **kwargs)

    @zvmutils.check_input_types(_TVSWNAME, bool)
    def vswitch_delete(self, vswitch_name, persist=True):
        """ Delete vswitch.

        :param str name: the vswitch name
        :param bool persist: whether delete the vswitch from the permanent
               configuration for the system

        :raises ZVMInvalidInput if:
                - Input parameter is invalid, refer to the error message for
                  detail
        :raises ZVMNetworkError if:
                - All kinds of xCAT call failure
                - Smcli call failure, refer to the error message for detail
        """
        self._networkops.delete_vswitch(vswitch_name, persist)

    @zvmutils.check_input_types(dict, dict, dict, bool)
    def volume_attach(self, guest, volume, connection_info,
                      is_rollback_in_failure=False):
        """ Attach a volume to a guest. It's prerequisite to active multipath
            feature on the guest before utilizing persistent volumes.

        :param dict guest:
                - name:
                    The type is string, it's the node name of the guest
                    instance in xCAT database.
                - os_type:
                    The type is string, it's the OS running on the guest.
                    Currently supported are RHEL7, SLES12 and their
                    sub-versions, i.e. 'rhel7', 'rhel7.2', 'sles12',
                    'sles12sp1'.
        :param dict volume:
                - size: of type string. The capacity size of the volume, in
                    unit of Megabytes or Gigabytes.
                - type: of type string. The device type of the volume. The only
                    one supported now is 'fc' which implies FibreChannel.
                - lun: of type string. The LUN value of the volume, excluding
                    prefixing '0x'. It's required if the type is 'fc' which
                    implies FibreChannel.
        :param dict connection_info:
                - alias: of type string. A constant valid alias of the volume
                    after it being attached onto the guest, i.e. '/dev/vda'.
                    Because the system generating device name could change
                    after each rebooting, it's necessary to have a constant
                    name to represent the volume in its life time.
                - protocol: of type string. The protocol by which the volume is
                    connected to the guest. The only one supported now is 'fc'
                    which implies FibreChannel.
                - fcps: of type list. The address of the FCP devices used by
                    the guest to connect to the volume. They should belong to
                    different channel path IDs in order to work properly.
                - wwpns: of type list. The WWPN values through which the volume
                    can be accessed, excluding prefixing '0x'.
                - dedicate: of type list. The address of the FCP devices which
                    will be dedicated to the guest before accessing the volume.
                    They should belong to different channel path IDs in order
                    to work properly.
        :param bool is_rollback_in_failure:
                Whether to roll back in failure.
                It's not guaranteed that the roll back operation must be
                successful.

        :raises ZVMVolumeError if:
               - Multipath feature is not active on the guest.
               - The volume is unaccessible.
               - The FCP devices can not be dedicated when protocol 'fc' is
                   specified.
               - The FCP devices belong to a same CHPID when protocol 'fc' is
                   specified.
        """
        self._volumeop.attach_volume_to_instance(guest,
                                                 volume,
                                                 connection_info,
                                                 is_rollback_in_failure)

    @zvmutils.check_input_types(dict, dict, dict, bool)
    def volume_detach(self, guest, volume, connection_info,
                      is_rollback_in_failure=False):
        """ Detach a volume from a guest. It's prerequisite to active multipath
            feature on the guest before utilizing persistent volumes.

        :param dict guest: A dict comprised of a list of properties of a guest,
               including:
               - name: of type string. The node name of the guest instance in
               xCAT database.
               - os_type: of type string. The OS running on the guest.
               Currently supported are RHEL7, SLES12 and their sub-versions,
               i.e. 'rhel7', 'rhel7.2', 'sles12', 'sles12sp1'.
        :param dict volume: A dict comprised of a list of properties of a
               volume, including:
               - type: of type string. The device type of the volume. The only
               one supported now is 'fc' which implies FibreChannel.
               - lun: of type string. The LUN value of the volume, excluding
               prefixing '0x'. It's required if the type is 'fc' which implies
               FibreChannel.
        :param dict connection_info: A dict comprised of a list of information
               used to establish host-volume connection, including:
               - alias: of type string. A constant valid alias of the volume
               after it being attached onto the guest, i.e. '/dev/vda'. Because
               the system generating device name could change after each
               rebooting, it's necessary to have a constant name to represent
               the volume in its life time.
               - protocol: of type string. The protocol by which the volume is
               connected to the guest. The only one supported now is 'fc' which
               implies FibreChannel.
               - fcps: of type list. The address of the FCP devices used by the
               guest to connect to the volume.
               - wwpns: of type list. The WWPN values through which the volume
               can be accessed, excluding prefixing '0x'.
               - dedicate: of type list. The address of the FCP devices which
               will be undedicated from the guest after removing the volume.
        :param bool is_rollback_in_failure: Whether to roll back in failure.
               It's not guaranteed that the roll back operation must be
               successful.

        :raises ZVMVolumeError if:
                - Multipath feature is not active on the guest.
                - The volume is not found on the guest.
        """
        self._volumeop.detach_volume_from_instance(guest,
                                                   volume,
                                                   connection_info,
                                                   is_rollback_in_failure)
