import os

from .config import LOG_PATH, DEBUG

import logging
from logging.handlers import RotatingFileHandler

# Create logger
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler(os.path.join(LOG_PATH, f'{os.path.basename(__file__)}.log'), 'a', 1000000, 1)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if DEBUG:
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARN)
    file_handler.setLevel(logging.WARN)
