import logging
import os
from functools import wraps
from PySide6.QtCore import QCoreApplication
from logging.handlers import RotatingFileHandler

import numpy as np

from .config import LOG_PATH, get_debug_flag

__all__ = ('logger', 'debug')

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
try:
    file_handler = RotatingFileHandler(
        os.path.join(LOG_PATH, f'{QCoreApplication.applicationName()}.log'), 'a', 1000000, 1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except FileNotFoundError:
    file_handler = None

if get_debug_flag():
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)
    if file_handler is not None:
        file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)
    if file_handler is not None:
        file_handler.setLevel(logging.WARNING)


def debug(func):
    np.set_string_function(lambda arr: '<array>')

    @wraps(func)
    def new_func(*args, **kwargs):
        if get_debug_flag():
            # noinspection PyShadowingNames
            logger = logging.getLogger()
            str_args = ', '.join([repr(a) for a in args])
            str_kwargs = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            logger.debug(f"Calling {func.__name__}({str_args}{', ' if str_kwargs else ''}{str_kwargs})")
            out = func(*args, **kwargs)
            logger.debug(f"Finished {func.__name__} -> {out}")
            return out
        else:
            return func(*args, **kwargs)

    return new_func
