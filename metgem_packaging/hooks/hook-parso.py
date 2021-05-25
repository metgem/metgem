import os.path
import sys

from PyInstaller.utils.hooks import collect_data_files

datas = []

# Collect grammar filtering out grammar files which does not correspond to the Python version used for metgem_packaging
version = str(sys.version_info.major) + str(sys.version_info.minor)
for data in collect_data_files('parso'):
    bname = os.path.basename(data[0])
    if bname.endswith('.txt') and bname.startswith('grammar'):
        if bname == 'grammar%s%s.txt' % (sys.version_info.major, sys.version_info.minor):
            datas.append(data)
    else:
        datas.append(data)
