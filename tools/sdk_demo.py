#!/usr/bin/env python
import sys
from zvmsdk import vmops

sys.path.append(..)


def boot_instance():
	instance_name = "zli00038"
	image_name = "rhel7-s390x-netboot-iucvmage_1aee879d_edf9_4d27_8ddf_b1464cd96cc9"
	cpu = 1
	memory = 1024
	login_passwd = ""
	ip_addr = "192.168.114.5"
	
	ret = vmops.run_instance(instance_name, image_name, cpu,
					   memory, login_passwd, ip_addr)
	return ret


name = boot_instance()

if name is not None:
	print "name is:%s" % name
else:
	print "boot failed?"
