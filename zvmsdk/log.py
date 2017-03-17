
import logging

# import config.CONF as cfg

from config import CONF as cfg
LOG = logging.getLogger('ZVMSDK')
# LOG.setLevel(cfg.LOG_LEVEL)
LOG.setLevel(logging.INFO)

formatter = logging.Formatter('%(name)-6s %(asctime)s %(levelname)-8s '
                              '%(message)s', '%a, %d %b %Y %H:%M:%S',)

# file_handler = logging.FileHandler(cfg.LOG_FILE)
file_handler = logging.FileHandler("zvmsdk.log")
# 
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

LOG.addHandler(file_handler)
LOG.addHandler(stream_handler)
