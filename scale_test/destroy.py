"""
Sample code that invokes SDKAPI.
"""

import sys

from zvmconnector import connector


sdk_client = connector.ZVMConnector(connection_type='rest', port='8080')


def terminate_guest(userid):
    """Destroy a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    res = sdk_client.send_request('guest_delete', userid)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in delete user: %s" % res)


def main():
    if len(sys.argv) != 2:
        print('need param for guest name')
        exit(1)

    guest_id = sys.argv[1]
    print('destroy %s' % guest_id)
    terminate_guest(guest_id)


if __name__ == "__main__":
    main()
