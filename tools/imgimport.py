'''
module -- imgimport

imgimport is a tool used to import image to xCAT

It defines osimage objects in xCAT, and upload image file to xCAT.

'''


import sys
import os
import shutil
import uuid
import datetime
import tarfile
import socket

sys.path.append('..')
import zvmsdk.utils as zvmutils
from zvmsdk import config

CONF = config.CONF

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter


__all__ = []
__version__ = 0.1

DEBUG = 1
TESTRUN = 0
PROFILE = 0


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_version_message = '%%(prog)s %s' % (program_version)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

USAGE
''' % (program_shortdesc)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license,
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--image-version", dest="image_version",
            help="version of image file which will be imported to xCAT."
             "\n[for example: rhel72[sles12]")
        parser.add_argument("-f", "--image-file", dest="image_file",
            help="image file which will be imported to xCAT."
             "\n[for example: /imagedir/imagename.img]")
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)

        # Process arguments
        del argv[0];
        args = parser.parse_args(argv)
        # Check argv 
        if len(argv) < 4:
            parser.print_help()
            os._exit(1)

        if not os.path.exists(args.image_file):
            print args.image_file + ": not exist,please check."
            os._exit(1)
        image_version = args.image_version
        image_file = args.image_file
        image_name = os.path.basename(image_file)
        print "Start import image_file :" + image_file + " to zvm xcat server:" + CONF.xcat.server

        image_file_name = os.path.basename(image_file)
        now = datetime.datetime.now()
        date_now = now.strftime("%Y-%m-%d")
        image_uuid = str(uuid.uuid1()).replace('-', '_')
        running_path = os.path.abspath('.')

        # generate manifest.xml
        manifest_template = running_path + "/manifest.xml.template"
        manifest_target = running_path + "/manifest.xml"
        shutil.copyfile(manifest_template, manifest_target)
        manifest = open("manifest.xml", 'rb+')
        lines = manifest.readlines()
        d=""

        for line in lines:
            c = line.replace("IMAGE_NAME", image_version + "-s390x-netboot-" + image_uuid).replace("ROOTIMGDIR", "/install/netboot/" + image_version + "/s390x/" + image_uuid).replace("PROFILE", image_uuid).replace("IMAGE_VERSION", image_version).replace("LASTUSEDATE", "auto:last_use_date:" + date_now).replace("IMAGE_FILE_NAME", image_file_name)
            d += c
            manifest.seek(0)
            manifest.truncate()
            manifest.write(d)
        manifest.close()

        # Get bundle file directory
        date_dir = now.strftime("%Y%m%d%H%M%S")
        image_package_path = os.path.dirname(os.path.abspath(image_file))
        image_bundle_path = image_package_path + '/' + date_dir
        os.makedirs(image_bundle_path)
        dist_path = image_bundle_path + "/" + "manifest.xml"
        shutil.copyfile(os.path.abspath('.') + "/" + "manifest.xml", dist_path)

        # Generate the image bundle which is used to import to xCAT MN's image repository.
        image_bundle_name = image_name + '.tar'
        tar_file = image_package_path + '/' + date_dir + '_' + image_bundle_name
        os.chdir(image_package_path)
        target_image_file = image_bundle_path + '/' + image_name
        print 'image_bundle__path is:' + image_bundle_path
        shutil.copyfile(image_file, target_image_file)
        tarFile = tarfile.open(tar_file, mode='w')
        tarFile.add(date_dir)
        tarFile.close()
        shutil.rmtree(image_bundle_path)
#         myhostname = socket.getfqdn(socket.gethostname(  ))
#         myaddrip = socket.gethostbyname(myhostname)
        remote_host_info = ''.join(['root', '@', CONF.network.my_ip])

        #Import the image bundle from compute node to xCAT MN's image repository.
        _xcat_url = zvmutils.get_xcat_url()

        body = ['osimage=%s' % tar_file,
                'profile=%s' % image_uuid,
                'remotehost=%s' % remote_host_info,
                'nozip']
        url = _xcat_url.imgimport()
        resp = zvmutils.xcat_request("POST", url, body)
        for ind in range(0,5):
            print resp['data'][ind][0]
        print "to zvm xcat server :" + CONF.xcat.server
        os.remove(tar_file)
        os.remove(manifest_target)
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__  == "__main__":
    if DEBUG:
        #sys.argv.append("-v rhel");
        print ""
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'module_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    main()

