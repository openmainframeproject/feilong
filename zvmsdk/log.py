#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from config import CONF


class Logger():
    def __init__(self, logger, path="/var/log/nova/zvmsdk.log",
                    Clevel=logging.DEBUG, Flevel = logging.DEBUG):
        # create a logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.INFO)

        # create a handler for the file
        fh = logging.FileHandler(path)
        fh.setLevel(Flevel)

        # create a hander for the console
        ch = logging.StreamHandler()
        ch.setLevel(Clevel)

        # set the formate of the handler
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # add handler in the logger
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def getlog(self):
        return self.logger


log_level = CONF.LOG_LEVEL
if log_level is "logging.INFO" or "logging.info":
    log_level = logging.INFO
elif log_level is "logging.DEBUG" or "logging.debug":
    log_level = logging.DEBUG
elif log_level is "logging.WARN" or "logging.warn":
    log_level = logging.WARN
elif log_level is "logging.ERROR" or "logging.error":
    log_level = logging.ERROR
elif log_level is "logging.CRITICAL" or "logging.critical":
    log_level = logging.CRITICAL

LOG = Logger(
        path=CONF.LOG_FILE, logger='ZVMSDK',
        Clevel = log_level, Flevel = log_level).getlog()
