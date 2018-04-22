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
    LOG_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\log')
    DATABASES_PATH = os.path.expandvars(r'%APPDATA%\tsne-network\databases')
elif sys.platform.startswith('darwin'):
    LOG_PATH = os.path.expanduser('~/Library/Logs/tsne-network/log')
    DATABASES_PATH = os.path.expanduser(r'~/Library/tsne-network/databases')
elif sys.platform.startswith('linux'):
    LOG_PATH = os.path.expanduser('~/.config/tsne-network/log')
    DATABASES_PATH = os.path.expanduser(r'~/.config/tsne-network/databases')
else:
    LOG_PATH = 'log'
    DATABASES_PATH = 'databases'