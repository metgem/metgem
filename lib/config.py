import os
import sys

# Network visualisation
RADIUS = 30

# File format
FILE_EXTENSION = '.mnz'

DEBUG = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1')
EMBED_JUPYTER = os.getenv('EMBED_JUPYTER', 'false').lower() in ('true', '1')

if sys.platform.startswith('win'):
    USER_PATH = os.path.join(os.path.expandvars(r'%APPDATA%'), 'MetGem')
elif sys.platform.startswith('darwin'):
    USER_PATH = os.path.join(os.path.expanduser('~'), 'Library', 'Logs', 'MetGem')
elif sys.platform.startswith('linux'):
    USER_PATH = os.path.join(os.path.expanduser('~'), '.config', 'MetGem')
else:
    USER_PATH = os.path.realpath('.')

DATABASES_PATH = os.path.join(USER_PATH, 'databases')
SQL_PATH = os.path.join(DATABASES_PATH, 'spectra.sqlite')
LOG_PATH = os.path.join(USER_PATH, 'log')
STYLES_PATH = os.path.join(USER_PATH, 'styles')

if not os.path.exists(DATABASES_PATH):
    os.makedirs(DATABASES_PATH)

if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

if not os.path.exists(STYLES_PATH):
    os.makedirs(STYLES_PATH)
