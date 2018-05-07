# Copyright 2017,2018 IBM Corp.
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

import json

from zvmsdk import config
from zvmsdk import log
from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import base
from zvmsdk.tests.sdkwsgi import test_utils


LOG = log.LOG
CONF = config.CONF


class VSwitchTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(VSwitchTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        # test change bind_port
        self.set_conf('sdkserver', 'bind_port', 3000)
        self.client = test_utils.TestzCCClient()

        # make sure test vswitch does not exist
        self._cleanup()

    def _cleanup(self):
        self._vswitch_delete()

    def setUp(self):
        super(VSwitchTestCase, self).setUp()
        self.record_logfile_position()

    def _vswitch_list(self):
        resp = self.client.api_request(url='/vswitches', method='GET')
        self.assertEqual(200, resp.status_code)

        return resp

    def test_vswitch_list(self):
        resp = self._vswitch_list()
        self.apibase.verify_result('test_vswitch_get', resp.content)

    def _vswitch_create(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        if resp.status_code in (200, 409):
            self.addCleanup(self._cleanup)

        return resp

    def _vswitch_create_aware(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00", "vid": 1}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        return resp

    def _vswitch_delete(self):
        resp = self.client.api_request(url='/vswitches/restvsw1',
                                       method='DELETE')
        return resp

    def _vswitch_query(self):
        resp = self.client.api_request(url='/vswitches/restvsw1',
                                       method='GET')
        return resp

    def test_vswitch_create_query_delete(self):
        resp = self._vswitch_create()
        self.assertEqual(200, resp.status_code)

        # Try to create another vswitch, this should fail
        resp = self._vswitch_create()
        self.assertEqual(409, resp.status_code)

        try:
            resp = self._vswitch_list()
            vswlist = json.loads(resp.content)['output']
            inlist = 'RESTVSW1' in vswlist
            self.assertTrue(inlist)

            resp = self._vswitch_query()
            vswinfo = json.loads(resp.content)['output']
            switch_name = vswinfo['switch_name']
            self.assertEqual(switch_name, 'RESTVSW1')
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

            # Try to delete again, currently ignore not exist error
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_list()
            vswlist = json.loads(resp.content)['output']
            inlist = 'RESTVSW1' in vswlist
            self.assertFalse(inlist)

            resp = self._vswitch_query()
            self.assertEqual(404, resp.status_code)

    def test_vswitch_grant_revoke(self):
        resp = self._vswitch_create()
        self.assertEqual(200, resp.status_code)

        body = '{"vswitch": {"grant_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                       method='PUT', body=body)
        self.assertEqual(200, resp.status_code)

        resp = self._vswitch_query()
        self.assertEqual(200, resp.status_code)

        vswinfo = json.loads(resp.content)['output']
        inlist = 'FVTUSER1' in vswinfo['authorized_users']
        self.assertTrue(inlist)

        body = '{"vswitch": {"revoke_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                       method='PUT', body=body)
        self.assertEqual(200, resp.status_code)

        resp = self._vswitch_query()
        self.assertEqual(200, resp.status_code)
        vswinfo = json.loads(resp.content)['output']
        inlist = 'FVTUSER1' in vswinfo['authorized_users']
        self.assertFalse(inlist)

    def test_vswitch_delete_update_query_not_exist(self):
        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

        # Test update the vswitch not found
        body = '{"vswitch": {"grant_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='PUT', body=body)
        self.assertEqual(404, resp.status_code)

        body = '{"vswitch": {"revoke_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='PUT', body=body)
        self.assertEqual(404, resp.status_code)

        content = {"vswitch": {"user_vlan_id":
                                 {"userid": "FVTUSER1", "vlanid": 10}}}
        body = json.dumps(content)
        resp = self.client.api_request(url='/vswitches/notexist',
                                           method='PUT', body=body)
        self.assertEqual(404, resp.status_code)

        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='GET')
        self.assertEqual(404, resp.status_code)

    def test_vswitch_create_invalid_body(self):
        body = '{"vswitch": {"v1": "v1"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_vswitch_create_nobody(self):
        resp = self.client.api_request(url='/vswitches', method='POST')
        self.assertEqual(400, resp.status_code)

    def test_vswitch_set_port_vlanid(self):
        resp = self._vswitch_create_aware()
        self.assertEqual(200, resp.status_code)

        try:
            content = {"vswitch": {"user_vlan_id":
                               {"userid": "FVTUSER1", "vlanid": 10}}}
            body = json.dumps(content)
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_query()
            self.assertEqual(200, resp.status_code)
            vswinfo = json.loads(resp.content)['output']
            inlist = 'FVTUSER1' in vswinfo['authorized_users']
            self.assertTrue(inlist)
            self.assertEqual('1',
                        vswinfo['authorized_users']['FVTUSER1']['vlan_count'])
            self.assertListEqual(['10'],
                        vswinfo['authorized_users']['FVTUSER1']['vlan_ids'])
        except Exception:
            raise
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

    def test_vswitch_set_port_invalid_vlanid(self):
        resp = self._vswitch_create_aware()
        self.assertEqual(200, resp.status_code)
        try:
            content = {"vswitch": {"user_vlan_id":
                               {"userid": "FVTUSER1", "vlanid": 0}}}
            body = json.dumps(content)
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(400, resp.status_code)

            content = {"vswitch": {"user_vlan_id":
                               {"userid": "FVTUSER1", "vlanid": 4095}}}
            body = json.dumps(content)
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(400, resp.status_code)

            content = {"vswitch": {"user_vlan_id":
                               {"userid": "FVTUSER1", "vlanid": "BADAWARE"}}}
            body = json.dumps(content)
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(400, resp.status_code)
        except Exception:
            raise
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

    def test_vswitch_set_port_vlanid_vswitch_unaware(self):
        resp = self._vswitch_create()
        self.assertEqual(200, resp.status_code)
        try:
            content = {"vswitch": {"user_vlan_id":
                               {"userid": "FVTUSER1", "vlanid": 1}}}
            body = json.dumps(content)
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                       method='PUT',
                                       body=body)
            self.assertEqual(409, resp.status_code)
        except Exception:
            raise
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

    def test_vswitch_create_vlan_unaware(self):
        content = {"vswitch": {"name": "RESTVSW1", "rdev": "FF00",
                               "controller": "FAKEVMID",
                               "connection": "CONnect",
                               "network_type": "IP", "router": "NONrouter",
                               "vid": "UNAWARE", "port_type": "ACCESS",
                               "gvrp": "NOGVRP", "queue_mem": 3,
                               "native_vid": 1, "persist": False}}
        body = json.dumps(content)
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self._cleanup)
        try:
            resp = self._vswitch_query()
            self.assertEqual(200, resp.status_code)
            vswinfo = json.loads(resp.content)['output']
            switch_name = vswinfo['switch_name']
            self.assertEqual('RESTVSW1', switch_name)
            self.assertEqual('IP', vswinfo['transport_type'])
            self.assertEqual('NONE', vswinfo['port_type'])
            self.assertEqual('3', vswinfo['queue_memory_limit'])
            self.assertEqual('UNAWARE', vswinfo['vlan_awareness'])
            self.assertEqual('NONROUTER', vswinfo['routing_value'])
            self.assertEqual('NOGVRP', vswinfo['gvrp_request_attribute'])
            self.assertEqual('USERBASED', vswinfo['user_port_based'])
            self.assertDictEqual({}, vswinfo['authorized_users'])
            self.assertTrue('FF00' in vswinfo['real_devices'])
        except Exception:
            raise
        finally:
            self.assertEqual(200, resp.status_code)

    def test_vswitch_create_vlan_aware(self):
        content = {"vswitch": {"name": "RESTVSW1", "rdev": "1111 2222",
                               "controller": "FAKEVMID",
                               "connection": "DISCONnect",
                               "network_type": "ETHernet",
                               "router": "PRIrouter",
                               "vid": 1000, "port_type": "TRUNK",
                               "gvrp": "GVRP", "queue_mem": 5,
                               "native_vid": 10, "persist": True}}
        body = json.dumps(content)
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self._cleanup)

        resp = self._vswitch_query()
        self.assertEqual(200, resp.status_code)
        vswinfo = json.loads(resp.content)['output']
        switch_name = vswinfo['switch_name']
        self.assertEqual('RESTVSW1', switch_name)
        self.assertEqual('ETHERNET', vswinfo['transport_type'])
        self.assertEqual('TRUNK', vswinfo['port_type'])
        self.assertEqual('5', vswinfo['queue_memory_limit'])
        self.assertEqual('AWARE', vswinfo['vlan_awareness'])
        self.assertEqual('GVRP', vswinfo['gvrp_request_attribute'])
        self.assertEqual('USERBASED', vswinfo['user_port_based'])
        self.assertDictEqual({}, vswinfo['authorized_users'])
        self.assertEqual('1000', vswinfo['vlan_id'])
        self.assertEqual('10', vswinfo['native_vlan_id'])
        self.assertEqual('NA', vswinfo['routing_value'])
        self.assertEqual(sorted(['1111', '2222']),
                         sorted(vswinfo['real_devices'].keys()))

    def test_vswitch_create_long_name(self):
        body = '{"vswitch": {"name": "LONGVSWITCHNAME", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_vswitch_create_invalid_rdev(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "11 22 33 44"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)
