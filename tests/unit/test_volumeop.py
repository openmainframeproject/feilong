import unittest

from zvmsdk import volumeop
from zvmsdk.exception import ZVMVolumeError as err


class VolumeOpTestCase(unittest.TestCase):

    def setUp(self):
        self._vol_op = volumeop.VolumeOperator()

    def test_attach_volume_to_instance(self):
        pass

    def test_detach_volume_from_instance(self):
        pass

    def test_validate_instance(self):
        self.assertRaises(err, self._vol_op._validate_instance, None)
        inst = ['inst1', 'sles12']
        self.assertRaises(err, self._vol_op._validate_instance, inst)
        inst = {'name': 'inst1'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)
        inst = {'os_type': 'sles12'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)
        inst = {'name': 'inst1', 'os_type': 'centos'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)
        inst = {'name': 'inst1', 'os_type': 'sles12'}
        self.assertEqual(self._vol_op._validate_instance(inst), None)

    def test_get_configurator(self):
        pass
