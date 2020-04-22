# Copyright 2017 IBM Corp.
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


import setuptools

from zvmsdk import version as sdkversion


setuptools.setup(
    name='zVMCloudConnector',
    version=sdkversion.__version__,
    license='ASL 2.0',
    author='IBM',
    description='z/VM cloud management library in Python',
    long_description=open('README.md').read(),
    url='https://github.com/openmainframeproject/python-zvm-sdk',
    keywords='zvm cloud library',
    install_requires=open('requirements.txt').read(),
    packages=setuptools.find_packages(exclude=["zvmsdk.tests.fvt*"]),
    package_data={
        'zvmsdk': [
            'vmactions/templates/grow_root_volume.j2'
        ]
    },
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        'wsgi_scripts': [
            'sdk_api = zvmsdk.sdkwsgi.wsgi:init_application',
        ]
    },
    scripts=['scripts/sdkserver', 'zvmsdk/sdkwsgi/zvmsdk-wsgi',
             'scripts/zvmsdk-gentoken'],
    data_files=[('/lib/systemd/system', ['data/sdkserver.service']),
                ('/var/lib/zvmsdk', ['data/setupDisk']),
                ('/etc/sudoers.d', ['data/sudoers-zvmsdk']),
                ('/etc/zvmsdk', ['data/uwsgi-zvmsdk.conf']),
                ('/etc/zvmsdk', ['doc/source/zvmsdk.conf.sample'])],
)
