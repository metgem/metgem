import os
import sys

# Network visualisation
RADIUS = 30
NODE_BORDER_WIDTH = 5
FONT_SIZE = 14

# File format
FILE_EXTENSION = '.mnz'

DEBUG = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1')
EMBED_JUPYTER = os.getenv('EMBED_JUPYTER', 'false').lower() in ('true', '1')

if sys.platform.startswith('win'):
    LOG_PATH = os.path.expandvars(r'%APPDATA%\HDiSpeC\log')
    DATABASES_PATH = os.path.expandvars(r'%APPDATA%\HDiSpeC\databases')
elif sys.platform.startswith('darwin'):
    LOG_PATH = os.path.expanduser('~/Library/Logs/HDiSpeC/log')
    DATABASES_PATH = os.path.expanduser(r'~/Library/HDiSpeC/databases')
elif sys.platform.startswith('linux'):
    LOG_PATH = os.path.expanduser('~/.config/HDiSpeC/log')
    DATABASES_PATH = os.path.expanduser(r'~/.config/HDiSpeC/databases')
else:
    LOG_PATH = 'log'
    DATABASES_PATH = 'databases'
SQL_PATH = os.path.join(DATABASES_PATH, 'spectra.sqlite')
