
import logging

import config as cfg


LOG = logging.getLogger('ZVMSDK')
LOG.setLevel(cfg.LOG_LEVEL)

formatter = logging.Formatter('%(name)-6s %(asctime)s %(levelname)-8s '
                              '%(message)s', '%a, %d %b %Y %H:%M:%S',)

file_handler = logging.FileHandler(cfg.LOG_FILE)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

LOG.addHandler(file_handler)
LOG.addHandler(stream_handler)
