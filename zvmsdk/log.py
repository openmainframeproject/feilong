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


import logging

from zvmsdk import config


CONF = config.CONF


class Logger():
    def __init__(self, logger, path="/tmp/zvmsdk.log",
                 level=logging.INFO):
        # create a logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(level)

        # create a handler for the file
        fh = logging.FileHandler(path)
        fh.setLevel(level)

        # set the formate of the handler
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)

        # add handler in the logger
        self.logger.addHandler(fh)

    def getlog(self):
        return self.logger


log_level = CONF.logging.log_level.upper()
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


LOG = Logger(path=CONF.logging.log_file, logger='ZVMSDK',
             level=log_level).getlog()
