#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2018 IBM Corp.
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
import os
import json
import tempfile

from zvmsdk.tests.fvt import base
from zvmsdk import config


CONF = config.CONF


class FileTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(FileTestCase, self).__init__(methodName)

    def _import_file(self, path):
        resp = self.client.file_import(path)
        return resp

    def _export_file(self, fpath):
        resp = self.client.file_export(fpath)
        return resp

    def test_import_file_not_exist(self):
        pass

    def test_export_file_not_exist(self):
        fpath = 'dummy'
        resp = self._export_file(fpath)
        results = json.loads(resp.content)
        self.assertEqual(300, results['overallRC'])

    def _prepare_files(self):
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        file_path = '/'.join([tempDir, 'file_to_import'])
        with open(file_path, 'wb') as f:
            f.write('123456abcdef')
        return file_path

    def _cleanup_files(self, fpath):
        if os.path.exists(fpath):
            os.remove(fpath)

    def test_import_export(self):
        file_to_import = self._prepare_files()
        self.addCleanup(self._cleanup_files, file_to_import)
        # import test
        resp = self._import_file(file_to_import)
        self.assertEqual(200, resp.status_code)
        content = json.loads(resp.content)
        dest_path = content['output']['dest_url'].replace('file://', '')
        file_name = dest_path.split('/')[-1]
        self.assertTrue(True, os.path.exists(dest_path))

        # export test
        fpath = CONF.file.file_repository + '/imported/' + file_name
        self.addCleanup(self._cleanup_files, fpath)
        resp = self._export_file(fpath)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('123456abcdef', resp.content)
