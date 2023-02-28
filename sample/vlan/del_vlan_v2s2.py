#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017 IBM Corp.

from zvmconnector import connector
import os

print("Setup client: client=connector.ZVMConnector('9.60.18.170', 8080)\n")
client=connector.ZVMConnector('9.60.18.170', 8080)

print("Test: send_request('vswitch_get_list')")
list = client.send_request('vswitch_get_list')
print("Result: %s\n" % list)

GUEST_USERID = 'DEMOV2S2'


print("Check generated image: send_request('guest_delete', '%s') % GUEST_USERID")
info = client.send_request('guest_delete', GUEST_USERID)
print('Result: %s\n' % info)

print("Check generated image: send_request('image_query', '%s') % GUEST_USERID")
info = client.send_request('guest_get_definition_info', GUEST_USERID)
print('Result: %s\n' % info)

print('Completed\n')
