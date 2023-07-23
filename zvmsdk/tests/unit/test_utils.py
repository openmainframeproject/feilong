#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017, 2022 IBM Corp.
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

import mock
import subprocess
import time
import threading
from mock import Mock, call

import zvmsdk.utils as zvmutils
from zvmsdk.tests.unit import base
from zvmsdk import exception


class ZVMUtilsTestCases(base.SDKTestCase):
    def test_convert_to_mb(self):
        self.assertEqual(2355.2, zvmutils.convert_to_mb('2.3G'))
        self.assertEqual(20, zvmutils.convert_to_mb('20M'))
        self.assertEqual(1153433.6, zvmutils.convert_to_mb('1.1T'))

    @mock.patch.object(zvmutils, 'get_smt_userid')
    def test_get_namelist(self, gsu):
        gsu.return_value = 'TUID'
        self.assertEqual('TSTNLIST', zvmutils.get_namelist())

        base.set_conf('zvm', 'namelist', None)
        gsu.return_value = 'TUID'
        self.assertEqual('NL00TUID', zvmutils.get_namelist())

        gsu.return_value = 'TESTUSER'
        self.assertEqual('NLSTUSER', zvmutils.get_namelist())
        base.set_conf('zvm', 'namelist', 'TSTNLIST')

    @mock.patch.object(subprocess, 'check_output')
    def test_get_lpar_name(self, vmcp_query):
        vmcp_query.return_value = b"IAAS01EF AT BOEM5401"
        self.assertEqual("BOEM5401", zvmutils.get_lpar_name())

    def test_expand_fcp_list_normal(self):
        fcp_list = "1f10;1f11;1f12;1f13;1f14"
        expected = {0: set(['1f10']),
                    1: set(['1f11']),
                    2: set(['1f12']),
                    3: set(['1f13']),
                    4: set(['1f14'])}

        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_dash(self):
        fcp_list = "1f10-1f14"
        expected = {0: set(['1f10', '1f11', '1f12', '1f13', '1f14'])}
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_dash(self):
        fcp_list = "1f10;1f11-1f13;1f17"
        expected = {0: set(['1f10']),
                    1: set(['1f11', '1f12', '1f13']),
                    2: set(['1f17'])}
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_2dash(self):
        fcp_list = "1f10;1f11-1f13;1f17-1f1a;1f02"
        expected = {0: set(['1f10']),
                    1: set(['1f11', '1f12', '1f13']),
                    2: set(['1f17', '1f18', '1f19', '1f1a']),
                    3: set(['1f02'])}
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_uncontinuous_equal_count(self):
        fcp_list = "5c70-5c71,5c73-5c74;5d70-5d71,5d73-5d74"
        expected = {0: set(['5c70', '5c71', '5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74'])}
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_4_uncontinuous_equal_count(self):
        fcp_list = "5c70-5c71,5c73-5c74;5d70-5d71,\
            5d73-5d74;1111-1112,1113-1114;2211-2212,2213-2214"
        expected = {0: set(['5c70', '5c71', '5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74']),
                    2: set(['1111', '1112', '1113', '1114']),
                    3: set(['2211', '2212', '2213', '2214']),
                   }
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_uncontinuous_not_equal_count(self):
        fcp_list = "5c73-5c74;5d70-5d71,5d73-5d74"
        expected = {0: set(['5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74'])}
        fcp_info = zvmutils.expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    @mock.patch("zvmsdk.utils.verify_fcp_list_in_hex_format", Mock())
    def test_shrink_fcp_list(self):
        """Test shrink_fcp_list"""

        # Case1: only one FCP in the list.
        fcp_list = ['1A01']
        expected_fcp_str = '1A01'
        result = zvmutils.shrink_fcp_list(fcp_list)
        self.assertEqual(expected_fcp_str, result)

        # Case 2: all the FCPs are continuous.
        expected_fcp_str = [
            '1A01 - 1A0E',      # continuous in last 1 digit
            '1A0E - 1A2E',      # continuous in last 2 digits
            '1AEF - 1B1F']      # continuous in last 3 digits
        expected_fcp_count = [
            14,       # continuous in last 1 digit
            33,       # continuous in last 2 digits
            49]       # continuous in last 3 digits
        for idx, efs in enumerate(expected_fcp_str):
            fcp_list = list(
                zvmutils.expand_fcp_list(efs)[0])
            result = zvmutils.shrink_fcp_list(fcp_list.copy())
            self.assertEqual(efs, result)
            self.assertEqual(expected_fcp_count[idx], len(fcp_list))

        # Case 3: not all the FCPs are continuous.
        expected_fcp_str = [
            '1A01, 1A0E - 1A2E',    # case 3.1
            '1A0E - 1A2E, 1B01',    # case 3.2
            '1A05, 1A0E - 1A2E, 1A4A, 1AEF - 1B1F',  # case 3.3
            '1A0E - 1A2E, 1A4A, 1A5B, 1AEF - 1B1F']  # case 3.4
        expected_fcp_count = [
            34,     # case 3.1
            34,     # case 3.2
            84,     # case 3.3
            84      # case 3.4
        ]
        for idx, efs in enumerate(expected_fcp_str):
            fcp_list = list(
                zvmutils.expand_fcp_list(efs)[0])
            result = zvmutils.shrink_fcp_list(fcp_list.copy())
            self.assertEqual(efs, result)
            self.assertEqual(expected_fcp_count[idx], len(fcp_list))

        # Case 4: an empty list.
        fcp_list = []
        expected_fcp_str = ''
        result = zvmutils.shrink_fcp_list(fcp_list)
        self.assertEqual(expected_fcp_str, result)

    def test_verify_fcp_list_in_hex_format(self):
        """Test verify_fcp_list_in_hex_format(fcp_list)"""
        # case1: not a list object
        fcp_list = '1A00 - 1A03'
        self.assertRaisesRegex(exception.SDKInvalidInputFormat,
                               "not a list object",
                               zvmutils.verify_fcp_list_in_hex_format,
                               fcp_list)
        # case2: FCP(1A0) length != 4
        fcp_list = ['1A00', '1A0']
        self.assertRaisesRegex(exception.SDKInvalidInputFormat,
                               "non-hex value",
                               zvmutils.verify_fcp_list_in_hex_format,
                               fcp_list)
        # case3: FCP(1A0G) not a 4-digit hex
        fcp_list = ['1A00', '1a0G']
        self.assertRaisesRegex(exception.SDKInvalidInputFormat,
                               "non-hex value",
                               zvmutils.verify_fcp_list_in_hex_format,
                               fcp_list)
        # case4: FCP(1A0R) not a 4-digit hex
        fcp_list = ['1a00', '1A0F']
        zvmutils.verify_fcp_list_in_hex_format(fcp_list)

    @mock.patch("zvmsdk.log.LOG.info")
    def test_synchronized(self, mock_info):
        """Test synchronized()"""

        @zvmutils.synchronized('fakeAction-{fakeObject[fakeKey]}')
        def fake_func1(fakeObject, sleep, *args, **kwargs):
            time.sleep(sleep)

        @zvmutils.synchronized('fakeAction-{fakeObject[fakeKey]}')
        def fake_func2(fakeObject, sleep, *args, **kwargs):
            time.sleep(sleep)

        @zvmutils.synchronized('fakeAction-{fakeObject[fakeKey2]}')
        def fake_func3(fakeObject, sleep, *args, **kwargs):
            time.sleep(sleep)

        # case1: test on @ decoration
        isinstance(zvmutils.synchronized._meta_lock, type(threading.RLock()))
        self.assertEqual(vars(zvmutils.synchronized).get('_lock_pool'), dict())
        concurrent_thread_count = vars(zvmutils.synchronized).get('_concurrent_thread_count')
        self.assertEqual(concurrent_thread_count, dict())

        # common variables
        fakeObj = {'fakeKey': 'fakeVal', 'fakeKey2': 'fakeVal2'}
        formatted_name = 'fakeAction-fakeVal'
        second_formatted_name = 'fakeAction-fakeVal2'

        # case2:
        # 2 concurrent threads on one decorated function
        th1 = threading.Thread(target=fake_func1, args=(fakeObj, 1))
        th2 = threading.Thread(target=fake_func1, args=(fakeObj, 0))
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        th1_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 1, th1.name)
        th2_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 2, th2.name)
        th1_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 1, th1.name)
        th2_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 0, th2.name)
        expected_calls = [call(th1_acquire_msg),
                          call(th2_acquire_msg),
                          call(th1_release_msg),
                          call(th2_release_msg)]
        expected_calls_order = [mock_info.mock_calls.index(c) for c in expected_calls]
        self.assertEqual(expected_calls_order, sorted(expected_calls_order))
        mock_info.reset_mock()

        # case3:
        # 2 concurrent threads on two decorated functions
        # with the same formatted lock name
        th1 = threading.Thread(target=fake_func1, args=(fakeObj, 1))
        th2 = threading.Thread(target=fake_func2, args=(fakeObj, 0))
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        th1_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 1, th1.name)
        th2_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 2, th2.name)
        th1_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 1, th1.name)
        th2_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 0, th2.name)
        expected_calls = [call(th1_acquire_msg),
                          call(th2_acquire_msg),
                          call(th1_release_msg),
                          call(th2_release_msg)]
        expected_calls_order = [mock_info.mock_calls.index(c) for c in expected_calls]
        self.assertEqual(expected_calls_order, sorted(expected_calls_order))
        mock_info.reset_mock()

        # case4:
        # 2 concurrent threads on two decorated functions
        # with different formatted lock names
        th1 = threading.Thread(target=fake_func1, args=(fakeObj, 1))
        th2 = threading.Thread(target=fake_func3, args=(fakeObj, 0))
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        th1_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 1, th1.name)
        th2_acquire_msg = ('synchronized: '
                           'acquiring lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            second_formatted_name, 1, th2.name)
        th1_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            formatted_name, 0, th1.name)
        th2_release_msg = ('synchronized: '
                           'after releasing lock {}, '
                           'concurrent thread count {}, '
                           'current thread: {}').format(
            second_formatted_name, 0, th2.name)
        expected_calls = [call(th1_acquire_msg),
                          call(th2_acquire_msg),
                          call(th2_release_msg),
                          call(th1_release_msg)]
        expected_calls_order = [mock_info.mock_calls.index(c) for c in expected_calls]
        self.assertEqual(expected_calls_order, sorted(expected_calls_order))
        mock_info.reset_mock()

    def test_translate_disk_pool_info_to_dict(self):
        # test only one diskpool
        poolname = 'pool1'
        diskpool_info = 'T60300 3390-A 220346 14420 POOL1 T60300\n' \
            'T60300 3390-A 627987 14563 POOL1 T60300'
        expect = {'POOL1': [{'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '220346',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'},
                            {'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '627987',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'}]}
        results = zvmutils.translate_disk_pool_info_to_dict(poolname, diskpool_info)
        self.assertDictEqual(expect, results)
        # test diskpool list
        poolname = ['pool1', 'pool2']
        diskpool_info = 'T60300 3390-A 220346 14420 POOL1 T60300\n' \
            'T60300 3390-A 627987 14563 POOL1 T60300\n' \
            'T60301 3390-A 320346 14563 POOL2 T60301\n' \
            'T60301 3390-A 727987 14563 POOL2 T60301'
        expect = {'POOL1': [{'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '220346',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'},
                            {'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '627987',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'}],
                  'POOL2': [{'volume_name': 'T60301',
                             'device_type': '3390-A',
                             'start_cylinder': '320346',
                             'free_size': 10,
                             'dasd_group': 'POOL2',
                             'region_name': 'T60301'},
                            {'volume_name': 'T60301',
                             'device_type': '3390-A',
                             'start_cylinder': '727987',
                             'free_size': 10,
                             'dasd_group': 'POOL2',
                             'region_name': 'T60301'}]}
        results = zvmutils.translate_disk_pool_info_to_dict(poolname, diskpool_info)
        self.assertDictEqual(expect, results)
        # Test match one diskpool name with multiple diskpool of the results
        poolname = 'pool1'
        diskpool_info = 'T60300 3390-A 220346 14420 POOL1 T60300\n' \
                        'T60300 3390-A 627987 14563 POOL1 T60300\n' \
                        'T60301 3390-A 320346 14563 POOL2 T60301\n' \
                        'T60301 3390-A 727987 14563 POOL2 T60301'
        expect = {'POOL1': [{'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '220346',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'},
                            {'volume_name': 'T60300',
                             'device_type': '3390-A',
                             'start_cylinder': '627987',
                             'free_size': 10,
                             'dasd_group': 'POOL1',
                             'region_name': 'T60300'}]}
        results = zvmutils.translate_disk_pool_info_to_dict(poolname, diskpool_info)
        self.assertDictEqual(expect, results)

    @mock.patch.object(subprocess, 'check_output')
    def test_get_pchid_by_chpid(self, lschp):
        lschp.return_value = (b'CHPID  Vary  Cfg.  Type  Cmg  Shared  PCHID\n============================'
                                   b'===============\n0.27   1     1     25    -    -       02e4 \n')
        chpid = '27'
        pchid = zvmutils.get_pchid_by_chpid(chpid)
        self.assertEqual('02e4', pchid)

    @mock.patch.object(subprocess, 'check_output')
    @mock.patch("zvmsdk.log.LOG.info")
    def test_print_all_pchids(self, mock_info, lschp_output):
        lschp_output.return_value = (b'CHPID  Vary  Cfg.  Type  Cmg  Shared  PCHID\n============================'
                              b'===============\n0.00   1     1     11    -    -      (ff00)\n0.01   1    '
                              b' 1     01    -    -      (ff01)\n0.10   1     1     25    -    -       02'
                              b'40 \n0.11   1     1     25    -    -       0260 \n0.12   1     1     25   '
                              b' -    -       0244 \n0.13   1     1     25    -    -       0264 \n0.14   1'
                              b'     1     25    -    -       0248 \n0.15   1     1     25    -    -     '
                              b'  0268 \n0.16   1     1     25    -    -       024c \n0.17   1     1     2'
                              b'5    -    -       026c \n0.30   1     1     1b    -    -       0280 \n0.31'
                              b'   1     1     1b    -    -       02a0 \n0.32   1     1     1b    -    - '
                              b'      0284 \n0.33   1     1     1b    -    -       02a4 \n0.34   1     1  '
                              b'   1b    -    -       0288 \n0.35   1     1     1b    -    -       02a8 \n'
                              b'0.36   1     1     1b    -    -       028c \n0.37   1     1     1b    -  '
                              b'  -       02ac \n0.70   1     1     11    -    -       01c0 \n0.71   1    '
                              b' 1     11    -    -       01e0 \n0.72   1     1     11    -    -       01'
                              b'c4 \n0.73   1     1     11    -    -       01c8 \n0.74   1     1     11   '
                              b' -    -       01e8 \n0.75   1     1     11    -    -       01e4 \n0.76   1'
                              b'     1     11    -    -       01cc \n0.77   1     1     11    -    -     '
                              b'  01ec \n0.80   1     1     24    -    -      (07c0)\n0.81   1     1     2'
                              b'4    -    -      (07c1)\n0.82   1     1     24    -    -      (07c2)\n0.83'
                              b'   1     1     24    -    -      (07c3)\n')
        zvmutils.print_all_pchids()
        mock_info.assert_called_with('CHPID  Vary  Cfg.  Type  Cmg  Shared  PCHID\n'
                                     '===========================================\n'
                                     '0.00   1     1     11    -    -      (ff00)\n'
                                     '0.01   1     1     01    -    -      (ff01)\n'
                                     '0.10   1     1     25    -    -       0240 \n'
                                     '0.11   1     1     25    -    -       0260 \n'
                                     '0.12   1     1     25    -    -       0244 \n'
                                     '0.13   1     1     25    -    -       0264 \n'
                                     '0.14   1     1     25    -    -       0248 \n'
                                     '0.15   1     1     25    -    -       0268 \n'
                                     '0.16   1     1     25    -    -       024c \n'
                                     '0.17   1     1     25    -    -       026c \n'
                                     '0.30   1     1     1b    -    -       0280 \n'
                                     '0.31   1     1     1b    -    -       02a0 \n'
                                     '0.32   1     1     1b    -    -       0284 \n'
                                     '0.33   1     1     1b    -    -       02a4 \n'
                                     '0.34   1     1     1b    -    -       0288 \n'
                                     '0.35   1     1     1b    -    -       02a8 \n'
                                     '0.36   1     1     1b    -    -       028c \n'
                                     '0.37   1     1     1b    -    -       02ac \n'
                                     '0.70   1     1     11    -    -       01c0 \n'
                                     '0.71   1     1     11    -    -       01e0 \n'
                                     '0.72   1     1     11    -    -       01c4 \n'
                                     '0.73   1     1     11    -    -       01c8 \n'
                                     '0.74   1     1     11    -    -       01e8 \n'
                                     '0.75   1     1     11    -    -       01e4 \n'
                                     '0.76   1     1     11    -    -       01cc \n'
                                     '0.77   1     1     11    -    -       01ec \n'
                                     '0.80   1     1     24    -    -      (07c0)\n'
                                     '0.81   1     1     24    -    -      (07c1)\n'
                                     '0.82   1     1     24    -    -      (07c2)\n'
                                     '0.83   1     1     24    -    -      (07c3)\n')
