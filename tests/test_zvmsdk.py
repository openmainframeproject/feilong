import config as CONF
# import configdrive
import mock
import unittest
import utils as zvmutils
import vmops as sdkapi


class SDKTestCase(unittest.TestCase):
    def setUp(self):
        self.vmops = sdkapi._get_vmops()
        self.volumeops = sdkapi._get_volumeops()
        '''
        return_value = {
                'os':'rhel7',
                'vcpus':1,
                'ip_addr':'192.168.114.6',
                'power_state':'off',
                'memory':'1024m',
                }
        '''

    def tearDown(self):
        pass

    def _fake_fun(self, value = None):
        return lambda *args, **kwargs: value


class SDKBasicAPITestCase(SDKTestCase):
    def setUp(self):
        super(SDKBasicAPITestCase, self).setUp()
        self.image_name =\
        "rhel7-s390x-netboot-testimage_dc410d84_86a0_4ac2_b841_1701bf065730"

    def test_run_instance(self):
        self.assertFalse('foo'.isupper())

    def test_terminate_instance(self):
        self.assertFalse('foo'.isupper())

    # TODO:version 1.0
    @mock.patch('vmops.VMOps.get_info')
    def test_describe_instance(self, getInfo):
        sdkapi.describe_instance('cbi00038')
        getInfo.assert_called_with('cbi00038')

    # TODO:version 1.0
    @mock.patch('vmops.VMOps._power_state')
    def test_start_instance(self, ChangePowerState):
        sdkapi.start_instance('cbi00038')
        ChangePowerState.assert_called_with('cbi00038', 'PUT', 'on')

    # TODO:version 1.0
    @mock.patch('vmops.VMOps._power_state')
    def test_stop_instance(self, ChangePowerState):
        sdkapi.stop_instance('cbi00038')
        ChangePowerState.assert_called_with('cbi00038', 'PUT', 'off')

    # TODO:version 1.0
    @mock.patch('vmops.VMOps.get_power_state')
    @mock.patch('vmops.VMOps.capture_instance')
    def test_capture_instance(self, snapshot, power_state):
        power_state.return_value = 'on'
        sdkapi.capture_instance('cbi00038')
        snapshot.assert_called_with('cbi00038')

    @mock.patch('vmops.VMOps.delete_image')
    def test_delete_image(self, deleteImage):
        sdkapi.delete_image(self.image_name)
        deleteImage.assert_called_with(self.image_name)

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch('vmops.VOLUMEOps.add_volume_info')
    @mock.patch('vmops.VOLUMEOps.get_free_mgr_vdev')
    def test_create_volume(self, gfmv, add_info, xrequest):
        # this url is made up
        url = "/xcatws/vms/volmgr?" + \
                "userName=admin&password=passowrd&format=json"
        body = ['--add9336 fbapool  1024 MR read write MULTI ext3']
        size = 1024
        gfmv.return_value = ''
        sdkapi.create_volume(size)

        xrequest.assert_called_with('PUT', url, body)
        add_info.assert_called_with(' free volmgr ')

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch('vmops.VOLUMEOps.delete_volume_info')
    @mock.patch('vmops.VOLUMEOps.get_volume_info')
    def test_delete_volume(self, get_info, delete_info, xrequest):
        # this url is made up
        uuid = 'asdf'
        url = "/xcatws/vms/volmgr?" + \
                "userName=admin&password=passowrd&format=json"
        body = ['--removedisk asdf']
        sdkapi.delete_volume(uuid)

        get_info.assert_called_with(uuid)
        xrequest.assert_called_with('PUT', url, body)
        delete_info.assert_called_with(uuid)

    # TODO
    def test_attach_volume(self):
        self.assertFalse('foo'.isupper())

    # TODO
    def test_detach_volume(self):
        self.assertFalse('foo'.isupper())


class SDKVMOpsTestCase(SDKTestCase):
    def setUp(self):
        super(SDKVMOpsTestCase, self).setUp()
        self.xcat_url = zvmutils.get_xcat_url()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_power_state(self, xrequest):
        url = "/xcatws/nodes/cbi00063/power?" + \
                "userName=admin&password=passowrd&format=json"
        body = ['stat']
        self.vmops._power_state('cbi00063', 'GET', 'stat')

        xrequest.assert_called_with("GET", url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_power_state(self, xrequest):
        url = "/xcatws/nodes/cbi00063/power?" + \
                "userName=admin&password=passowrd&format=json"
        body = ['stat']
        self.vmops.get_power_state('cbi00063')
        xrequest.assert_called_with('GET', url, body)

    '''
    example output of get_info:
    {
    'os': u'rhel7',
    'vcpus': 1,
    'ip_addr': u'192.168.114.3',
    'power_state': u'on',
    'memory': u'1024m'
    }
    '''
    @mock.patch('vmops.VMOps._lsvm')
    @mock.patch('vmops.VMOps._lsdef')
    @mock.patch('vmops.VMOps._power_state')
    def test_get_info(self, power_state, lsdef, lsvm):
        power_state.return_value = {'info': [[u'cbi00063: on\n']],
                'node': [], 'errorcode': [], 'data': [], 'error': []}
        lsdef.return_value = [
                'Object name: cbi00063',
                'arch=s390x', 'groups=all', 'hcp=zhcp2.ibm.com',
                'hostnames=cbi00063', 'interface=1000', 'ip=192.168.114.3',
                'mac=02:00:00:0e:02:fc', 'mgt=zvm', 'netboot=zvm',
                'os=rhel7', 'postbootscripts=otherpkgs',
                'postscripts=syslog, remoteshell,syncfiles',
                'profile=sdkimage_b9bbd236_547b_49d7_9282_d4443e9f9334',
                'provmethod=netboot', 'switch=xcatvsw2',
                'switchinterface=1000',
                'switchport=3c793024-13c9-4056-a2ef-569704ed1bd5',
                'switchvlan=-1', 'userid=cbi00063']
        lsvm.return_value = [u'cbi00064: USER CBI00063 DFLTPASS 1024m 1024m G',
                u'cbi00063: INCLUDE OSDFLT', u'cbi00063: CPU 00 BASE',
                u'cbi00063: ',
                u'cbi00063: ',
                u'cbi00063: ', u'']
        info = self.vmops.get_info('cbi00063')
        self.assertEqual(info['power_state'], 'on')
        self.assertEqual(info['vcpus'], 1)
        power_state.assert_called_once_with('cbi00063', 'GET', 'stat')
        lsdef.assert_called_once_with('cbi00063')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_is_reachable(self, xrequest):
        xrequest.return_value = {
                'info': [],
                'node': [[{u'data': [u'sshd'], u'name': [u'cbi00063']}]],
                'errorcode': [], 'data': [], 'error': []}
        ret = self.vmops.is_reachable('cbi00063')

        self.assertEqual(ret, True)

    @mock.patch('vmops.VMOps._power_state')
    def test_power_on(self, power_state, ):
        self.vmops.power_on('cbi00063')
        power_state.assert_called_once_with('cbi00063', 'PUT', 'on')

    @mock.patch('vmops.VMOps.set_ipl')
    @mock.patch('vmops.VMOps.add_mdisk')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_create_userid(self, xrequest, add_mdisk, set_ipl):
        url = "/xcatws/vms/cbi00063?" + \
                "userName=admin&password=passowrd&format=json"
        body = ['profile=QCDFLT',
                'password=password',
                'cpu=1', 'memory=1024m',
                'privilege=G', 'ipl=0100',
                'imagename=test-image-name']
        self.vmops.create_userid('cbi00063', 1, 1024, 'test-image-name')
        xrequest.assert_called_once_with('POST', url, body)
        add_mdisk.assert_called_once_with('cbi00063', CONF.zvm_diskpool,
                                          CONF.zvm_user_root_vdev,
                                          CONF.root_disk_units)
        set_ipl.assert_called_once_with('cbi00063', CONF.zvm_user_root_vdev)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_userid(self, xrequest):
        url = "/xcatws/vms/cbi00038?" + \
                "userName=admin&password=passowrd&format=json"
        self.vmops.delete_userid('cbi00038', 'zhcp2')

        xrequest.assert_called_once_with('DELETE', url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mdisk(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?" + \
                "userName=admin&password=passowrd&format=json"
        # TODO
        body = ['--add3390 xcateckd 0100 3338']
        self.vmops.add_mdisk('cbi00063', CONF.zvm_diskpool,
                                          CONF.zvm_user_root_vdev,
                                          CONF.root_disk_units)
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_ipl(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?" + \
                "userName=admin&password=passowrd&format=json"
        # TODO
        body = ['--setipl 0100']
        self.vmops.set_ipl('cbi00063', CONF.zvm_user_root_vdev)
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_list_instances(self, xrequest):
        res_dict = {'info': [], 'node': [], 'errorcode': [],
        'data': [
            [u'#table head',
            u'"opnstk2","zhcp2.ibm.com",,"zvm",,,,,',
            u'"cbi00021","zhcp2.ibm.com","cbi00021",,,,,,',
            u'"cbi00038","zhcp2.ibm.com","cbi00038",,,,,,',
            u'"zli00038","zhcp2.ibm.com","zli00038",,,,,,',
            u'"cmacbiao","zhcp2.ibm.com","CMACBIAO","vm","opnstk2",,,,',
            u'"zhcp2","zhcp2.ibm.com","CMACBIAO","vm","opnstk2",,,,',
            u'"cbi00063","zhcp2.ibm.com","cbi00063",,,,,,"IUCV=1"',
            u'"cbi00039","zhcp2.ibm.com","cbi00039",,,,,,"IUCV=1"',
            u'"zli00039","zhcp2.ibm.com","zli00039",,,,,,']
            ], 'error': []}
        xrequest.return_value = res_dict
        instances = [
                u'cbi00021', u'cbi00038', u'zli00038',
                u'cbi00063', u'cbi00039', u'zli00039']
        ret = self.vmops.list_instances()
        self.assertEqual(ret, instances)

    @mock.patch('vmops.VMOps._check_power_stat')
    def test_is_powered_off(self, check_stat):
        check_stat.return_value = 'off'
        ret = self.vmops.is_powered_off('cbi00063')
        self.assertEqual(True, ret)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_xcat_node(self, xrequest):
        url = "/xcatws/nodes/cbi00063" + \
                "?userName=admin&password=passowrd&format=json"
        self.vmops.delete_xcat_node('cbi00063')
        xrequest.assert_called_once_with('DELETE', url)

    @mock.patch('vmops.VMOps.list_instances')
    def test_instance_exists(self, list_instances):
        list_instances.return_value = ['cbi00063', 'cbi00064']
        ret = self.vmops.instance_exists('cbi00063')
        self.assertEqual(True, ret)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_capture_instance(self, xrequest):
        res = {
            'info': [
                [u'cbi00063: Capturing the image using zHCP node'],
                [u'cbi00063: creatediskimage start time'],
                [u'cbi00063: Moving the image files to the directory:xxxx'],
                [u'cbi00063: Completed capturing the image(test-image-name)']],
            'node': [],
            'errorcode': [],
            'data': [],
            'error': []}

        xrequest.return_value = res
        image_name = self.vmops.capture_instance('cbi00063')
        self.assertEqual(image_name, 'test-image-name')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_image(self, xrequest):
        url = "/xcatws/objects/osimage/test-image-name?" + \
                "userName=admin&password=passowrd&format=json"
        self.vmops.delete_image('test-image-name')

        xrequest.assert_called_with('DELETE', url)


class SDKVolumeOpsTestCase(SDKTestCase):
    def test_temp(self):
        self.assertFalse('foo'.isupper())


if __name__ == '__main__':
    unittest.main()
