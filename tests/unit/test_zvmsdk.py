
import mock
import unittest

from zvmsdk.config import CONF
import zvmsdk.utils as zvmutils
import zvmsdk.vmops as sdkapi
from zvmsdk import networkops


class SDKTestCase(unittest.TestCase):
    def setUp(self):
        self.vmops = sdkapi._get_vmops()
        self.volumeops = sdkapi._get_volumeops()
        self.networkops = networkops._get_networkops()

    def _fake_fun(self, value = None):
        return lambda *args, **kwargs: value


class SDKVMOpsTestCase(SDKTestCase):
    def setUp(self):
        super(SDKVMOpsTestCase, self).setUp()
        self.xcat_url = zvmutils.get_xcat_url()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_power_state(self, xrequest):
        url = "/xcatws/nodes/cbi00063/power?" + \
                "userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        body = ['stat']
        self.vmops.get_power_state('cbi00063')
        xrequest.assert_called_with('GET', url, body)

    @mock.patch('zvmsdk.client.XCATClient._lsvm')
    @mock.patch('zvmsdk.client.XCATClient._lsdef')
    @mock.patch('zvmsdk.client.XCATClient._power_state')
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

    @mock.patch('zvmsdk.client.XCATClient._power_state')
    def test_power_on(self, power_state, ):
        self.vmops.power_on('cbi00063')
        power_state.assert_called_once_with('cbi00063', 'PUT', 'on')

    @mock.patch('zvmsdk.vmops.VMOps.set_ipl')
    @mock.patch('zvmsdk.vmops.VMOps.add_mdisk')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_create_userid(self, xrequest, add_mdisk, set_ipl):
        url = "/xcatws/vms/cbi00063?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password +\
                "&format=json"
        body = ['profile=QCDFLT',
                'password=password',
                'cpu=1', 'memory=1024m',
                'privilege=G', 'ipl=0100',
                'imagename=test-image-name']
        self.vmops.create_userid('cbi00063', 1, 1024, 'test-image-name')
        xrequest.assert_called_once_with('POST', url, body)
        add_mdisk.assert_called_once_with('cbi00063', CONF.zvm.diskpool,
                                          CONF.zvm.user_root_vdev,
                                          CONF.zvm.root_disk_units)
        set_ipl.assert_called_once_with('cbi00063', CONF.zvm.user_root_vdev)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_userid(self, xrequest):
        url = "/xcatws/vms/cbi00038?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        self.vmops.delete_userid('cbi00038', 'zhcp2')

        xrequest.assert_called_once_with('DELETE', url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mdisk(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?" + \
                "userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        body_str = '--add3390 ' + CONF.zvm.diskpool + ' 0100 3338'
        body = []
        body.append(body_str)
        self.vmops.add_mdisk('cbi00063', CONF.zvm.diskpool,
                                          CONF.zvm.user_root_vdev,
                                          CONF.zvm.root_disk_units)
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_ipl(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        # TODO
        body = ['--setipl 0100']
        self.vmops.set_ipl('cbi00063', CONF.zvm.user_root_vdev)
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_list_instances(self, xrequest):
        res_dict = {
                'info': [],
                'node': [],
                'errorcode': [],
                'data': [],
                'error': []}
        items = []
        test_item1 = '#table header...'
        test_item2 = '"cbi00021","' + CONF.xcat.zhcp + '","cbi00021",,,,,,'
        test_item3 = '"cbi00038","' + CONF.xcat.zhcp + '","cbi00038",,,,,,'
        items.append(test_item1)
        items.append(test_item2)
        items.append(test_item3)
        res_dict['data'].append(items)
        xrequest.return_value = res_dict
        instances = [u'cbi00021', u'cbi00038']
        ret = self.vmops.list_instances()
        self.assertEqual(ret, instances)

    @mock.patch('zvmsdk.client.XCATClient.get_power_state')
    def test_is_powered_off(self, check_stat):
        check_stat.return_value = 'off'
        ret = self.vmops.is_powered_off('cbi00063')
        self.assertEqual(True, ret)

    @mock.patch('zvmsdk.vmops.VMOps.list_instances')
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
        url = "/xcatws/objects/osimage/test-image-name?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        self.vmops.delete_image('test-image-name')

        xrequest.assert_called_with('DELETE', url)


class SDKVolumeOpsTestCase(SDKTestCase):
    def test_temp(self):
        pass


class SDKNetworkOpsTestCase(SDKTestCase):
    def test_temp(self):
        pass


if __name__ == '__main__':
    unittest.main()
