# -*- mode: python -*-

import os
import sys
import glob

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
hiddenimports = []
excludes = []

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

# Gather data files
datas = [('../splash.png', '.'),
         ('../styles/*.css', 'styles'),
         ('../LICENSE', '.'),
         ('../lib/ui/*_rc.py', 'lib/ui'),
         ('../lib/ui/*.ui', 'lib/ui'),
         ('../lib/ui/widgets/images/*', 'lib/ui/widgets/images'),
         ('../lib/ui/widgets/spectrum/images/*', 'lib/ui/widgets/spectrum/images'),
         ('../lib/ui/widgets/*.ui', 'lib/ui/widgets'),
         ('../lib/ui/widgets/databases/*.ui', 'lib/ui/widgets/databases')]
if not sys.platform.startswith('darwin'):
    datas.extend([('../examples/Codiaeum.csv', 'examples'),
                  ('../examples/Codiaeum.mgf', 'examples'),
                  ('../examples/Codiaeum.mnz', 'examples'),
                  ('../examples/Stillingia SFE.csv', 'examples'),
                  ('../examples/Stillingia SFE.mgf', 'examples'),
                  ('../examples/Stillingia SFE.mnz', 'examples'),
                  ('../examples/Stillingia group mapping.txt', 'examples')])
                   	
         
# Get Qt styles dll
binaries.extend(qt_plugins_binaries('styles', namespace='PyQt5'))

# Add pybel
try:
    import pybel
except ImportError:
    pass
else:
    hiddenimports.extend(['pybel'])

# Adds Qt OpenGL
hiddenimports.extend(['PyQt5.QtOpenGL'])
if sys.platform.startswith('win'):
    binaries.extend([(os.path.join(qt_base_dir, 'bin', dll), r'PyQt5\Qt\bin')
                      for dll in ('libEGL.dll', 'libGLESv2.dll')])
    
# Define path for build hooks
hookspath.extend(['hooks'])

# Define path for runtime hooks
runtime_hooks.extend(sorted(glob.glob('rthooks/*_pyi_*.py')))
    
a = Analysis(['../gui.py'],
             pathex=pathex,
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=hookspath,
             runtime_hooks=runtime_hooks,
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
# Remove MKL binaries
a.binaries = [bin for bin in a.binaries if not bin[0].startswith('mkl_') or bin[0].startswith('mkl_rt')
              or bin[0].startswith('mkl_intel_thread')]

# Remove unused IPython data files
a.datas = [dat for dat in a.datas if not dat[0].startswith('IPython')]
             
# Remove unused pytz data files
a.datas = [dat for dat in a.datas if not dat[0].startswith('pytz')]

# Remove matplotlib sample data
a.datas = [dat for dat in a.datas if not ('sample_data' in dat[0] and dat[0].startswith('mpl-data'))]
             
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
             
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MetGem',
          debug=DEBUG,
          strip=False,
          upx=False,
          console=DEBUG)
          
coll_name = 'MetGem'
if DEBUG:
    coll_name += '_debug'
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name=coll_name)
               
if sys.platform.startswith('darwin') and not DEBUG:
    app = BUNDLE(coll,
                 name='MetGem.app',
                 icon='main.icns',
                 bundle_identifier=None)