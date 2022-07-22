#!/usr/libexec/platform-python


import json
import sys

from zvmconnector import connector


client = connector.ZVMConnector(connection_type = 'socket', port = 2000)


def image_query():
    print("\nQuerying image ...")
    res = client.send_request('image_query')

    if res['overallRC']:
        raise RuntimeError("Failed to list image!")

    return res


def printhelp():
    print("\nCurrnt support params")
    print("\nimage_query: list all the images")
    print("\n")


def main():
    if len(sys.argv) <= 1:
        print("no parm given, nothing to do")
        return 0

    if sys.argv[1] == 'help':
        printhelp()
        exit(0)

    if sys.argv[1] == 'image_query':
        re = image_query()
        print("Image Result are:\n")
        print(json.dumps(re['output'], indent=4, sort_keys=True))
    else:
        print("param %s is invalid, use %s help to get all supported params" % (sys.argv[1], sys.argv[0]))


if __name__ == "__main__":
    sys.exit(main())
