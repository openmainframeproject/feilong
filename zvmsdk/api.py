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


import netaddr

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
        action = "start guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_start(userid)

    @zvmutils.check_input_types(_TUSERID, valid_keys=['timeout',
                                                      'poll_interval'])
    def guest_stop(self, userid, **kwargs):
        """Power off a virtual machine.

        :param str userid: the id of the virtual machine to be power off
        :param dict kwargs:
               - timeout=<value>:
                 Integer, time to wait for vm to be deactivate, the
                 recommended value is 300
               - poll_interval=<value>
                 Integer, how often to signal guest while waiting for it
                 to be deactivate, the recommended value is 20

        :returns: None
        """

        action = "stop guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_stop(userid, **kwargs)

    @zvmutils.check_input_types(_TUSERID, valid_keys=['timeout',
                                                      'poll_interval'])
    def guest_softstop(self, userid, **kwargs):
        """Issue a shutdown command to shutdown the OS in a virtual
        machine and then log the virtual machine off z/VM..

        :param str userid: the id of the virtual machine to be power off
        :param dict kwargs:
               - timeout=<value>:
                 Integer, time to wait for vm to be deactivate, the
                 recommended value is 300
               - poll_interval=<value>
                 Integer, how often to signal guest while waiting for it
                 to be deactivate, the recommended value is 20

        :returns: None
        """

        action = "soft stop guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_softstop(userid, **kwargs)

    @zvmutils.check_input_types(_TUSERID)
    def guest_reboot(self, userid):
        """Reboot a virtual machine
        :param str userid: the id of the virtual machine to be reboot
        :returns: None
        """
        action = "reboot guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_reboot(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_reset(self, userid):
        """reset a virtual machine
        :param str userid: the id of the virtual machine to be reset
        :returns: None
        """
        action = "reset guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_reset(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_pause(self, userid):
        """Pause a virtual machine.

        :param str userid: the id of the virtual machine to be paused
        :returns: None
        """
        action = "pause guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_pause(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_unpause(self, userid):
        """Unpause a virtual machine.

        :param str userid: the id of the virtual machine to be unpaused
        :returns: None
        """
        action = "unpause guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_unpause(userid)

    @zvmutils.check_input_types(_TUSERID)
    def guest_get_power_state(self, userid):
        """Returns power state."""
        action = "get power state of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
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
        action = "get info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_info(userid)

    def guest_list(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        action = "list guests on host"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.guest_list()

    def host_get_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        action = "get host information"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.get_info()

    @zvmutils.check_input_types(_TSTR)
    def host_diskpool_get_info(self, disk_pool=CONF.zvm.disk_pool):
        """ Retrieve diskpool information.
        :param str disk_pool: the disk pool info. It use ':' to separate
        disk pool type and name, eg "ECKD:eckdpool" or "FBA:fbapool"
        :returns: Dictionary describing diskpool usage info
        """
        if ':' not in disk_pool:
            msg = ('Invalid input parameter disk_pool, expect ":" in'
                   'disk_pool, eg. ECKD:eckdpool')
            LOG.error(msg)
            raise exception.SDKInvalidInputFormat(msg)
        diskpool_type = disk_pool.split(':')[0].upper()
        diskpool_name = disk_pool.split(':')[1]
        if diskpool_type not in ('ECKD', 'FBA'):
            msg = ('Invalid disk pool type found in disk_pool, expect'
                   'disk_pool like ECKD:eckdpool or FBA:fbapool')
            LOG.error(msg)
            raise exception.SDKInvalidInputFormat(msg)

        action = "get information of disk pool: '%s'" % disk_pool
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.diskpool_get_info(diskpool_name)

    @zvmutils.check_input_types(_TSTR)
    def image_delete(self, image_name):
        """Delete image from image repository

        :param image_name: the name of the image to be deleted
        """
        try:
            self._imageops.image_delete(image_name)
        except exception.SDKBaseException:
            LOG.error("Failed to delete image '%s'" % image_name)
            raise

    @zvmutils.check_input_types(_TSTR)
    def image_get_root_disk_size(self, image_name):
        """Get the root disk size of the image

        :param image_name: the image name in image Repository
        :returns: the disk size in units CYL or BLK
        """
        try:
            return self._imageops.image_get_root_disk_size(image_name)
        except exception.SDKBaseException:
            LOG.error("Failed to get root disk size units of image '%s'" %
                      image_name)
            raise

    @zvmutils.check_input_types(_TSTR, _TSTR, dict, _TSTR_OR_NONE)
    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import image to zvmsdk image repository

        :param image_name: image name that can be uniquely identify an image
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
        """
        try:
            self._imageops.image_import(image_name, url, image_meta,
                                        remote_host=remote_host)
        except exception.SDKBaseException:
            LOG.error("Failed to import image '%s'" % image_name)
            raise

    @zvmutils.check_input_types(_TSTR_OR_NONE)
    def image_query(self, imagename=None):
        """Get the list of image info in image repository

        :param imagename:  Used to retrieve the specified image info,
               if not specified, all images info will be returned

        :returns: A list that contains the specified or all images info
        """
        try:
            return self._imageops.image_query(imagename)
        except exception.SDKBaseException:
            LOG.error("Failed to query image")
            raise

    @zvmutils.check_input_types(_TSTR, _TSTR, _TSTR_OR_NONE)
    def image_export(self, image_name, dest_url, remote_host=None):
        """Export the image to the specified location
        :param image_name: image name that can be uniquely identify an image
        :param dest_url: the location of exported image, eg.
        file:///opt/images/export.img, now only support export to remote server
        or local server's file system
        :param remote_host: the server that the image will be export to, if
        remote_host is None, the image will be stored in the dest_path in
        local server,  the format is username@IP eg. nova@9.x.x.x
        :returns a dictionary that contains the exported image info
        {
        'image_name': the image_name that exported
        'image_path': the image_path after exported
        'os_version': the os version of the exported image
        'md5sum': the md5sum of the original image
        }
        """
        try:
            return self._imageops.image_export(image_name, dest_url,
                                               remote_host)
        except exception.SDKBaseException:
            LOG.error("Failed to export image '%s'" % image_name)
            raise

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
        """
        action = ("deploy image '%(img)s' to guest '%(vm)s'" %
                  {'img': image_name, 'vm': userid})
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_deploy(userid, image_name,
                                     transportfiles, remotehost, vdev)

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6):
        """ Capture the guest to generate a image

        :param userid: (str) the user id of the vm
        :param image_name: (str) the unique image name after capture
        :param capture_type: (str) the type of capture, the value can be:
               rootonly: indicate just root device will be captured
               alldisks: indicate all the devices of the userid will be
               captured
        :param compress_level: the compression level of the image, default
               is 6
        """
        action = ("capture guest '%(vm)s' to generate image '%(img)s'" %
                  {'vm': userid, 'img': image_name})
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_capture(userid, image_name,
                                      capture_type=capture_type,
                                      compress_level=compress_level)

    @zvmutils.check_input_types(_TUSERID, _TSTR_OR_NONE, _TSTR_OR_NONE,
                       _TSTR_OR_NONE, _TSTR_OR_NONE, bool)
    def guest_create_nic(self, userid, vdev=None, nic_id=None,
                         mac_addr=None, active=False):
        """ Create the nic for the vm, add NICDEF record into the user direct.

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param str nic_id: nic identifier
        :param str mac_addr: mac address, it is only be used when changing
               the guest's user direct. Format should be xx:xx:xx:xx:xx:xx,
               and x is a hexadecimal digit
        :param bool active: whether add a nic on active guest system

        :returns: nic device number, 1- to 4- hexadecimal digits
        :rtype: str
        """
        if mac_addr is not None:
            if not zvmutils.valid_mac_addr(mac_addr):
                raise exception.SDKInvalidInputFormat(
                    msg=("Invalid mac address, format should be "
                         "xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit"))
        return self._networkops.create_nic(userid, vdev=vdev, nic_id=nic_id,
                                           mac_addr=mac_addr, active=active)

    @zvmutils.check_input_types(_TUSERID, _TSTR, bool)
    def guest_delete_nic(self, userid, vdev, active=False):
        """ delete the nic for the vm

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether delete a nic on active guest system
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
        action = "get the definition info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
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
               'is_boot_disk': For root disk, this key must be set to indicate
               the image that will be deployed on this disk.
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
        """
        if disk_list:
            for disk in disk_list:
                if not isinstance(disk, dict):
                    errmsg = ('Invalid "disk_list" input, it should be a '
                              'dictionary. Details could be found in doc.')
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
                # 'size' is required for each disk
                if 'size' not in disk.keys():
                    errmsg = ('Invalid "disk_list" input, "size" is required '
                              'for each disk.')
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
                # 'disk_pool' format check
                disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
                if ':' not in disk_pool or (disk_pool.split(':')[0].upper()
                    not in ['ECKD', 'FBA']):
                    errmsg = ("Invalid disk_pool input, it should be in format"
                              " ECKD:eckdpoolname or FBA:fbapoolname")
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
                # 'format' value check
                if ('format' in disk.keys()) and (disk['format'].lower() not in
                                                  ('ext2', 'ext3', 'ext4',
                                                   'xfs')):
                    errmsg = ("Invalid disk_pool input, supported 'format' "
                              "includes 'ext2', 'ext3', 'ext4', 'xfs'")
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

        action = "create guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.create_vm(userid, vcpus, memory, disk_list,
                                  user_profile)

    @zvmutils.check_input_types(_TUSERID, list)
    def guest_create_disks(self, userid, disk_list):
        """Add disks to an existing guest vm.

        :param userid: (str) the userid of the vm to be created
        :param disk_list: (list) a list of disks info for the guest.
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
               'format': optional, can be ext2, ext3, ext4, xfs, if not
               specified, the disk will not be formatted.
               'is_boot_disk': For root disk, this key must be set to indicate
               the image that will be deployed on this disk.
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
        """
        if disk_list == []:
            # nothing to do
            LOG.debug("No disk specified when calling guest_create_disks, "
                      "nothing happened")
            return

        action = "create disks '%s' for guest '%s'" % (str(disk_list), userid)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.create_disks(userid, disk_list)

    @zvmutils.check_input_types(_TUSERID, list)
    def guest_delete_disks(self, userid, disk_vdev_list):
        """Delete disks from an existing guest vm.

        :param userid: (str) the userid of the vm to be deleted
        :param disk_vdev_list: (list) the vdev list of disks to be deleted,
            for example: ['0101', '0102']
        """
        action = "delete disks '%s' from guest '%s'" % (str(disk_vdev_list),
                                                        userid)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.delete_disks(userid, disk_vdev_list)

    @zvmutils.check_input_types(_TUSERID, _TSTR, _TVSWNAME, bool)
    def guest_nic_couple_to_vswitch(self, userid, nic_vdev,
                                    vswitch_name, active=False):
        """ Couple nic device to specified vswitch.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param str vswitch_name: the name of the vswitch
        :param bool active: whether make the change on active guest system
        """
        self._networkops.couple_nic_to_vswitch(userid, nic_vdev,
                                               vswitch_name, active=active)

    @zvmutils.check_input_types(_TUSERID, _TSTR, bool)
    def guest_nic_uncouple_from_vswitch(self, userid, nic_vdev,
                                        active=False):
        """ Disonnect nic device with network.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether make the change on active guest system
        """
        self._networkops.uncouple_nic_from_vswitch(userid, nic_vdev,
                                                   active=active)

    def vswitch_get_list(self):
        """ Get the vswitch list.

        :returns: vswitch name list
        :rtype: list
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
        """
        if ((queue_mem < 1) or (queue_mem > 8)):
            errmsg = ('API vswitch_create: Invalid "queue_mem" input, '
                      'it should be 1-8')
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        if isinstance(vid, int) or vid.upper() != 'UNAWARE':
            if ((native_vid is not None) and
                ((native_vid < 1) or (native_vid > 4094))):
                errmsg = ('API vswitch_create: Invalid "native_vid" input, '
                          'it should be 1-4094 or None')
                raise exception.SDKInvalidInputFormat(msg=errmsg)

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
        action = "get the console output of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            output = self._vmops.get_console_output(userid)

        return output

    @zvmutils.check_input_types(_TUSERID)
    def guest_delete(self, userid):
        """Delete guest.

        :param userid: the user id of the vm
        """
        action = "delete guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.delete_vm(userid)

    @zvmutils.check_input_types(_TUSERID_OR_LIST)
    def guest_inspect_stats(self, userid_list):
        """Get the statistics including cpu and mem of the guests

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
                  'samples_cpu_delay': xx,
                  'used_mem_kb': xx,
                  'max_mem_kb': xx,
                  'min_mem_kb': xx,
                  'shared_mem_kb': xx
                  },
                  'UID2':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx,
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
        action = "get the statistics of guest '%s'" % str(userid_list)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._monitor.inspect_stats(userid_list)

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
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        action = "get the vnics statistics of guest '%s'" % str(userid_list)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._monitor.inspect_vnics(userid_list)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID)
    def vswitch_grant_user(self, vswitch_name, userid):
        """Set vswitch to grant user

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """

        self._networkops.grant_user_to_vswitch(vswitch_name, userid)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID)
    def vswitch_revoke_user(self, vswitch_name, userid):
        """Revoke user for vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """
        self._networkops.revoke_user_from_vswitch(vswitch_name, userid)

    @zvmutils.check_input_types(_TVSWNAME, _TUSERID, int)
    def vswitch_set_vlan_id_for_user(self, vswitch_name, userid, vlan_id):
        """Set vlan id for user when connecting to the vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        :param int vlan_id: the VLAN id
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
        action = "config disks for userid '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
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
        """
        for k in kwargs.keys():
            if k not in constants.SET_VSWITCH_KEYWORDS:
                errmsg = ('API vswitch_set: Invalid keyword %s' % k)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        self._networkops.set_vswitch(vswitch_name, **kwargs)

    @zvmutils.check_input_types(_TVSWNAME, bool)
    def vswitch_delete(self, vswitch_name, persist=True):
        """ Delete vswitch.

        :param str name: the vswitch name
        :param bool persist: whether delete the vswitch from the permanent
               configuration for the system
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
                    instance in database.
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
               database.
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
        """
        self._volumeop.detach_volume_from_instance(guest,
                                                   volume,
                                                   connection_info,
                                                   is_rollback_in_failure)

    @zvmutils.check_input_types(_TUSERID, _TSTR, list, bool)
    def guest_create_network_interface(self, userid, os_version,
                                       guest_networks, active=False):
        """ Create network interface(s) for the guest inux system. It will
            create the nic for the guest, add NICDEF record into the user
            direct. It will also construct network interface configuration
            files and punch the files to the guest. These files will take
            effect when initializing and configure guest.

        :param str userid: the user id of the guest
        :param str os_version: operating system version of the guest
        :param list guest_networks: a list of network info for the guest.
               It has one dictionary that contain some of the below keys for
               each network, the format is:
               {'ip_addr': (str) IP address or None,
               'dns_addr': (list) dns addresses or None,
               'gateway_addr': (str) gateway address or None,
               'cidr': (str) cidr format,
               'nic_vdev': (str)nic VDEV, 1- to 4- hexadecimal digits or None,
               'nic_id': (str) nic identifier or None,
               'mac_addr': (str) mac address or None, it is only be used when
               changing the guest's user direct. Format should be
               xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit}

               Example for guest_networks:
               [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mac_addr': '02:00:00:12:34:56'},
               {'ip_addr': '192.168.96.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003}]
        :param bool active: whether add a nic on active guest system
        :returns: guest_networks list, including nic_vdev for each network
        :rtype: list
        """
        if len(guest_networks) == 0:
            errmsg = ("API guest_create_network_interface: "
                      "Network information is required but not provided")
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        vdev = nic_id = mac_addr = ip_addr = None
        for network in guest_networks:
            if 'nic_vdev' in network.keys():
                vdev = network['nic_vdev']
            if 'nic_id' in network.keys():
                nic_id = network['nic_id']

            if (('mac_addr' in network.keys()) and
                (network['mac_addr'] is not None)):
                mac_addr = network['mac_addr']
                if not zvmutils.valid_mac_addr(mac_addr):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid mac address, format should be "
                              "xx:xx:xx:xx:xx:xx, and x is a hexadecimal "
                              "digit")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('ip_addr' in network.keys()) and
                (network['ip_addr'] is not None)):
                ip_addr = network['ip_addr']
                if not netaddr.valid_ipv4(ip_addr):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid management IP address, it should be "
                              "the value between 0.0.0.0 and 255.255.255.255")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('dns_addr' in network.keys()) and
                (network['dns_addr'] is not None)):
                if not isinstance(network['dns_addr'], list):
                    raise exception.SDKInvalidInputTypes(
                        'guest_config_network',
                        str(list), str(type(network['dns_addr'])))
                for dns in network['dns_addr']:
                    if not netaddr.valid_ipv4(dns):
                        errmsg = ("API guest_create_network_interface: "
                                  "Invalid dns IP address, it should be the "
                                  "value between 0.0.0.0 and 255.255.255.255")
                        raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('gateway_addr' in network.keys()) and
                (network['gateway_addr'] is not None)):
                if not netaddr.valid_ipv4(
                                    network['gateway_addr']):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid gateway IP address, it should be "
                              "the value between 0.0.0.0 and 255.255.255.255")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
            if (('cidr' in network.keys()) and
                (network['cidr'] is not None)):
                if not zvmutils.valid_cidr(network['cidr']):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid CIDR, format should be a.b.c.d/n, and "
                              "a.b.c.d is IP address, n is the value "
                              "between 0-32")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            try:
                used_vdev = self._networkops.create_nic(userid, vdev=vdev,
                                                        nic_id=nic_id,
                                                        mac_addr=mac_addr,
                                                        active=active)
                network['nic_vdev'] = used_vdev
            except exception.SDKBaseException:
                LOG.error(('Failed to create nic on vm %s') % userid)
                raise

        try:
            self._networkops.network_configuration(userid, os_version,
                                                   guest_networks,
                                                   active=active)
        except exception.SDKBaseException:
            LOG.error(('Failed to set network configuration file on vm %s') %
                      userid)
            raise
        return guest_networks

    @zvmutils.check_input_types(_TUSERID, _TSTR, _TSTR)
    def guests_get_nic_info(self, userid=None, nic_id=None, vswitch=None):
        """ Retrieve nic information in the network database according to
            the requirements, the nic information will include the guest
            name, nic device number, vswitch name that the nic is coupled
            to, nic identifier and the comments.

        :param str userid: the user id of the vm
        :param str nic_id: nic identifier
        :param str vswitch: the name of the vswitch

        :returns: list describing nic information, format is
                  [
                  (userid, interface, vswitch, nic_id, comments),
                  (userid, interface, vswitch, nic_id, comments)
                  ], such as
                  [
                  ('VM01', '1000', 'xcatvsw2', '1111-2222', None),
                  ('VM02', '2000', 'xcatvsw3', None, None)
                  ]
        :rtype: list
        """
        action = "get nic information"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._networkops.get_nic_info(userid=userid, nic_id=nic_id,
                                                 vswitch=vswitch)
