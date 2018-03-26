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


import logging
import os

from zvmsdk import config


class Logger():

    def __init__(self, logger):
        # create a logger
        self.logger = logging.getLogger(logger)
        self.log_level = logging.INFO

    def getlog(self):
        return self.logger

    def setup(self, log_dir, log_level, log_file_name='zvmsdk.log'):
        # make sure target directory exists
        if not os.path.exists(log_dir):
            if os.access(log_dir, os.W_OK):
                os.makedirs(log_dir)
            else:
                log_dir = '/tmp/'

        # Setup log level
        self.updateloglevel(log_level)
        self.logger.setLevel(self.log_level)

        # create a handler for the file
        log_file = os.path.join(log_dir, log_file_name)
        fh = logging.FileHandler(log_file)
        fh.setLevel(self.log_level)

        # set the formate of the handler
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)

        # add handler in the logger
        self.logger.addHandler(fh)

    def updateloglevel(self, level):
        log_level = level.upper()
        if log_level in ('LOGGING.INFO', 'INFO'):
            log_level = logging.INFO
        elif log_level in ('LOGGING.DEBUG', 'DEBUG'):
            log_level = logging.DEBUG
        elif log_level in ('LOGGING.WARN', 'WARN'):
            log_level = logging.WARN
        elif log_level in ('LOGGING.ERROR', 'ERROR'):
            log_level = logging.ERROR
        elif log_level in ('LOGGING.CRITICAL', 'CRITICAL'):
            log_level = logging.CRITICAL
        else:
            # default to logging.INFO
            log_level = logging.INFO

        self.log_level = log_level

    def getloglevel(self):
        return self.log_level


def setup_log():
    global LOGGER
    LOGGER.setup(log_dir=config.CONF.logging.log_dir,
                 log_level=config.CONF.logging.log_level)


LOGGER = Logger('ZVMSDK')
LOG = LOGGER.getlog()
