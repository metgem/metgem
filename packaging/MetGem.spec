# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import glob

from distutils.core import run_setup

from PyInstaller.utils.hooks import qt_plugins_binaries, get_module_file_attribute

# On Anaconda distributions, qt_plugins_binaries can't be found because QLibraryInfo returns wrong path
import PyInstaller.utils.hooks.qt
location = PyInstaller.utils.hooks.qt.pyqt5_library_info.location
for k in location.keys():
    if not os.path.exists(location[k]) and "Library" in location[k]:
        s = location[k].split("Library")[1]
        location[k] = os.path.join(sys.prefix, "Library" + s)

# if --debug flag is passed, make a debug release
DEBUG = '--debug' in sys.argv
        
pathex = []
binaries = []
datas = []
hookspath = []
runtime_hooks = []
hiddenimports = ['metgem_app.ui.ui_rc']
excludes = []

# Get data from setup.py
distribution = run_setup(os.path.join(SPECPATH, "..", "setup.py"), stop_after="init") 
for f in distribution.package_data['metgem_app']:
    datas.append((os.path.join(SPECPATH, "..", "metgem_app", f), os.path.join("metgem_app", os.path.dirname(f))))
for d, files in distribution.data_files:
    for f in files:
        datas.append((os.path.join(SPECPATH, "..", f), d if d else "."))

# Encrypt files?
block_cipher = None

# Remove Tkinter: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-remove-tkinter-tcl
sys.modules['FixTk'] = None
excludes.extend(['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'matplotlib.backends._tkagg'])

# Remove lib2to3
excludes.extend(['lib2to3'])

# Try to locate Qt base directory
qt_base_dir = os.path.join(os.path.dirname(get_module_file_attribute('PyQt5')), 'Qt')
if not os.path.exists(qt_base_dir):
    qt_base_dir = os.path.join(sys.prefix, 'Library')

# Add some useful folders to path
if sys.platform.startswith('win'):
    pathex.append(os.path.join(sys.prefix, 'Lib', 'site-packages', 'scipy', 'extra-dll'))
    
# Get Qt styles dll
binaries.extend(qt_plugins_binaries('styles', namespace='PyQt5'))
binaries.extend(qt_plugins_binaries('platforms', namespace='PyQt5'))
binaries.extend(qt_plugins_binaries('iconengines', namespace='PyQt5'))
binaries.extend(qt_plugins_binaries('imageformats', namespace='PyQt5'))

# Adds Qt OpenGL
hiddenimports.extend(['PyQt5.QtOpenGL'])
if sys.platform.startswith('win'):
    binaries.extend([(os.path.join(qt_base_dir, 'bin', dll), r'PyQt5\Qt\bin')
                      for dll in ('libEGL.dll', 'libGLESv2.dll')])

# Add pybel
try:
    import pybel
except ImportError:
    pass
else:
    hiddenimports.extend(['pybel'])

# Add phate
try:
    import phate
except ImportError:
    pass
else:
    hiddenimports.extend(['phate'])

# Add umap
try:
    import umap
except ImportError:
    pass
else:
    hiddenimports.extend(['umap'])

# Define path for build hooks
hookspath.extend([os.path.join(SPECPATH, "hooks")])

# Define path for runtime hooks
runtime_hooks.extend(sorted(glob.glob(os.path.join(SPECPATH, "rthooks", "*_pyi_*.py"))))

a = Analysis([os.path.join(SPECPATH, '..', 'MetGem')],
             pathex=pathex,
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=hookspath,
             runtime_hooks=runtime_hooks,
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
             
# Remove unused IPython data files
a.datas = [dat for dat in a.datas if not dat[0].startswith('IPython')]
             
# Remove unused pytz data files
a.datas = [dat for dat in a.datas if not dat[0].startswith('pytz')]

# Remove matplotlib sample data
a.datas = [dat for dat in a.datas if not ('sample_data' in dat[0] and dat[0].startswith('mpl-data'))]
             
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MetGem',
          debug=DEBUG,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=DEBUG,
          icon=os.path.join(SPECPATH, 'main.ico') if sys.platform.startswith('win') else None)

coll_name = 'MetGem'
if DEBUG:
    coll_name += '_debug'
          
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name=coll_name)

if sys.platform.startswith('darwin') and not DEBUG:
    app = BUNDLE(coll,
                 name='MetGem.app',
                 icon=os.path.join(SPECPATH, 'main.icns'),
                 bundle_identifier=None)
