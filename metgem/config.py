import os
import sys

RADIUS = 30

# File format
FILE_EXTENSION = '.mnz'

try:
    # noinspection PyProtectedMember
    APP_PATH = sys._MEIPASS
except AttributeError:
    APP_PATH = os.path.dirname(os.path.dirname(__file__))

try:
    path = os.path.join(APP_PATH, 'LICENSE') if getattr(sys, 'frozen', False) else 'LICENSE'
    with open(path, 'r', encoding='UTF-8') as f:
        LICENSE_TEXT = "".join(f.readlines())
except (FileNotFoundError, IOError):
    LICENSE_TEXT = ""

DEBUG = False
EMBED_JUPYTER = False
USE_OPENGL = True
USE_PYTHON_RENDERING = False

# Make app portable if `application folder`/data folder exists
IS_PORTABLE = os.path.exists(os.path.join('.', 'data'))

if IS_PORTABLE:
    USER_PATH = os.path.join(APP_PATH, 'data')
    try:
        # Network visualisation
        from PySide6.QtCore import QSettings
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, USER_PATH)
    except ImportError:
        pass
elif sys.platform.startswith('win'):
    USER_PATH = os.path.join(os.path.expandvars(r'%APPDATA%'), "MetGem")
elif sys.platform.startswith('darwin'):
    USER_PATH = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', "MetGem")
elif sys.platform.startswith('linux'):
    USER_PATH = os.path.join(os.path.expanduser('~'), '.config', "MetGem")
else:
    USER_PATH = os.path.realpath('.')

DATABASES_PATH = os.path.join(USER_PATH, 'databases')
SQL_PATH = os.path.join(DATABASES_PATH, 'spectra.sqlite')
if sys.platform.startswith('darwin'):
    LOG_PATH = os.path.join(os.path.expanduser('~'), 'Library', 'Logs', "MetGem")
else:
    LOG_PATH = os.path.join(USER_PATH, 'log')
STYLES_PATH = os.path.join(USER_PATH, 'styles')
PLUGINS_PATH = os.path.join(USER_PATH, 'plugins')


def makedirs(path):
    try:
        os.makedirs(path, exist_ok=True)
    except (OSError, PermissionError):
        pass


makedirs(DATABASES_PATH)
makedirs(LOG_PATH)
makedirs(STYLES_PATH)
makedirs(PLUGINS_PATH)


def get_debug_flag() -> bool:
    return DEBUG


def set_debug_flag(val: bool):
    global DEBUG
    DEBUG = val


def get_jupyter_flag() -> bool:
    return EMBED_JUPYTER


def set_jupyter_flag(val: bool):
    global EMBED_JUPYTER
    EMBED_JUPYTER = val


def get_use_opengl_flag() -> bool:
    return USE_OPENGL


def set_use_opengl_flag(val: bool):
    global USE_OPENGL
    USE_OPENGL = val


def set_python_rendering_flag(val: bool):
    global USE_PYTHON_RENDERING
    USE_PYTHON_RENDERING = val


def get_python_rendering_flag() -> bool:
    return USE_PYTHON_RENDERING
