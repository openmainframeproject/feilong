
import unittest

from zvmsdk import api


class ComputeAPITestCase(unittest.TestCase):
    """Testcases for compute APIs."""
    def setUp(self):
        super(ComputeAPITestCase, self).setUp()
        self.api = api.ComputeAPI()

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.api, api.ComputeAPI))
