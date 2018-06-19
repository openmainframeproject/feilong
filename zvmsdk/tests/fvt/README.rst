How to add functional testcases and run tests
---------------------------------------------

Configure functional test enviroment
====================================

First of all, you should have a zCC installed, configured and works correctlly.

Test options should be set in '[tests]' section in zvmsdk.conf. Required test
options:

- restapi_url: REST API URL. Sample value: 'http://127.0.0.1:8888'

- images: Test image file path plus operating system version. Sample value:
  "/var/lib/zvmsdk/images/netboot/rhel6.7/46a4aea3_54b6_4b1c_8a49_01f302e70c60:rhel6.7"

- vswitch: The vswitch that test guests connect to.

- ip_addr_list: A list of test ip addresses. Sample value:
  '192.168.0.2 192.168.0.3 192.168.0.4 192.168.0.5 192.168.0.6'
  You may need to add a new nic to your zCC node and make sure your zCC is able
  to connect to the guest that deployed with these ip addresses.

- gateway_v4: gateway that used to configure guest network interface.

- cidr: CIDR of guest network for tests.


Optional test options that better to set:

- userid_prefix: Prefix for test guest userid. Set this to make sure your test
  guests have different prefix with other test environment.


Creating new testcases
======================

Add new functional testcases when:

- For every new feature, functional testcases should be created.

- If submitting a bug fix that had no functional testcases to cover the change,
  a new functional testcase should be created.

Test modules overview:

- base.py: base testcase class for all fvt testcase classes. Implement common
  init steps in this module.

- test_utils.py: Implemented a simple zCC client, which is used to send zCC
  REST request. And implementd test utils, which includes methods to implement
  complex helper functions, for example, deploy_guest invokes several zCC calls
  to deploy a guest in one test utils method. 

- test_suites.py: Define test suites, e.g. bvt test suites.

- other test modules: Adding testcases to test modules accordingly. e.g.
  test_guest.py is for guest actions tests, test_image is for image related
  tests.

Please **NOTE**:

- All common utils methods should be added into test utils, instead of
  individual test modules.

- All zCC REST request should be sent through zCC client in test_utils.py.


Run function tests
==================

Run one testcase:
``python -m unittest -v zvmsdk.tests.fvt.test_guest.GuestHandlerTestCaseWithMultipleDeployedGuest.test_guest_get_console_output``

Run one test class:
``python -m unittest -v zvmsdk.tests.fvt.test_guest.GuestHandlerTestCaseWithMultipleDeployedGuest``

Run bvt:
``python -m unittest zvmsdk.tests.fvt.test_suites.bvt``

Run full round of fvt:
``python -m unittest discover -v -s zvmsdk.tests.fvt``
