# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import glob

from distutils.core import run_setup

# noinspection PyUnresolvedReferences
sys.path.insert(0, os.path.join(SPECPATH, '..'))
# noinspection PyUnresolvedReferences
sys.path.insert(0, os.path.join(SPECPATH, 'build', 'lib'))

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
# noinspection PyUnresolvedReferences
distribution = run_setup(os.path.join(SPECPATH, "..", "setup.py"), stop_after="init")
for f in distribution.package_data['metgem_app']:
    # noinspection PyUnresolvedReferences
    path = os.path.join(SPECPATH, "build", "lib", "metgem_app", f)
    alt_path = os.path.join(SPECPATH, "..", "metgem_app", f)
    dest_path = os.path.join("metgem_app", os.path.dirname(f))
    print(f)
    if os.path.exists(path):
        datas.append((path, dest_path))
    else:
        datas.append((alt_path, dest_path))
        
for d, files in distribution.data_files:
    for f in files:
        # noinspection PyUnresolvedReferences
        datas.append((os.path.join(SPECPATH, "..", f), d if d else "."))
            
version = distribution.get_version()

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
    pathex.append(os.path.join(sys.prefix, 'Library', 'bin'))
    pathex.append(os.path.join('C:', 'Program Files', 'OpenSSL', 'bin'))

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

# Add Qt Dbus on macOS
if sys.platform.startswith('darwin'):
    hiddenimports.extend(['PyQt5.QtDBus'])

# Add pybel
try:
    # noinspection PyPackageRequirements
    import pybel
except ImportError:
    pass
else:
    hiddenimports.extend(['pybel'])

# Add phate
try:
    # noinspection PyPackageRequirements
    import phate
except ImportError:
    pass
else:
    hiddenimports.extend(['phate'])

# Add umap
try:
    # noinspection PyPackageRequirements
    import umap
except ImportError:
    pass
else:
    hiddenimports.extend(['umap'])

# Define path for build hooks
# noinspection PyUnresolvedReferences
hookspath.extend([os.path.join(SPECPATH, "hooks")])

# Define path for runtime hooks
# noinspection PyUnresolvedReferences
runtime_hooks.extend(sorted(glob.glob(os.path.join(SPECPATH, "rthooks", "*_pyi_*.py"))))

# noinspection PyUnresolvedReferences
a = Analysis([os.path.join(SPECPATH, 'build', 'scripts', 'MetGem')],
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

# noinspection PyUnresolvedReferences
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform.startswith('win'):
    # noinspection PyUnresolvedReferences
    icon = os.path.join(SPECPATH, 'main.ico')

    # Write file_version_info.txt to use it in EXE
    import re

    v = re.match("(\d)\.(\d)\.(\d)\w*(\d?)", version)
    v = ", ".join(a if a else '0' for a in v.groups())
    # noinspection PyUnresolvedReferences
    version_file = os.path.join(SPECPATH, 'file_version_info.txt')
    with open(version_file, 'w') as f:
        f.write("# UTF-8\n")
        f.write("#\n")
        f.write("# For more details about fixed file info 'ffi' see:\n")
        f.write("#http://msdn.microsoft.com/en-us/library/ms646997.aspx\n")
        f.write("VSVersionInfo(\n")
        f.write("    ffi=FixedFileInfo(\n")
        f.write("        # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)\n")
        f.write("        # Set not needed items to zero 0.\n")
        f.write("        filevers=({}),\n".format(v))
        f.write("        prodvers=({}),\n".format(v))
        f.write("        # Contains a bitmask that specifies the valid bits 'flags'r\n")
        f.write("        mask=0x17,\n")
        f.write("        # Contains a bitmask that specifies the Boolean attributes of the file.\n")
        f.write("        flags=0x0,\n")
        f.write("        # The operating system for which this file was designed.\n")
        f.write("        # 0x4 - NT and there is no need to change it.\n")
        f.write("        OS=0x4,\n")
        f.write("        # The general type of file.\n")
        f.write("        # 0x1 - the file is an application.\n")
        f.write("        fileType=0x1,\n")
        f.write("        # The function of the file.\n")
        f.write("        # 0x0 - the function is not defined for this fileType\n")
        f.write("        subtype=0x0,\n")
        f.write("        # Creation date and time stamp.\n")
        f.write("        date=(0, 0)\n")
        f.write("    ),\n")
        f.write("    kids=[\n")
        f.write("        StringFileInfo(\n")
        f.write("            [\n")
        f.write("                StringTable(\n")
        f.write("                    u'000004b0',\n")
        f.write("                    [StringStruct(u'Comments', u'Version {}'),\n".format(version))
        f.write("                     StringStruct(u'CompanyName', u'CNRS/ICSN'),\n")
        f.write("                     StringStruct(u'FileDescription', u'MetGem'),\n")
        f.write("                     StringStruct(u'FileVersion', u'{}'),\n".format(version))
        f.write("                     StringStruct(u'InternalName', u'MetGem'),\n")
        f.write("                     StringStruct(u'LegalCopyright', u'Copyright (C) 2018-2020'),\n")
        f.write("                     StringStruct(u'OriginalFilename', u'MetGem.exe'),\n")
        f.write("                     StringStruct(u'ProductName', u'MetGem'),\n")
        f.write("                     StringStruct(u'ProductVersion', u'{}')])\n".format(version))
        f.write("            ]),\n")
        f.write("        VarFileInfo([VarStruct(u'Translation', [0, 1200])])\n")
        f.write("    ]\n")
        f.write(")\n")
elif sys.platform.startswith('darwin'):
    # noinspection PyUnresolvedReferences
    icon = os.path.join(SPECPATH, 'main.icns')
    version_file = None
else:
    icon = None
    version_file = None

# noinspection PyUnresolvedReferences
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          append_pkg=False,
          name='MetGem',
          debug=DEBUG,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=DEBUG,
          version=version_file,
          icon=icon)

coll_name = 'MetGem'
if DEBUG:
    coll_name += '_debug'

# noinspection PyUnresolvedReferences
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name=coll_name)

if sys.platform.startswith('darwin') and not DEBUG:
    # noinspection PyUnresolvedReferences
    app = BUNDLE(coll,
                 name='MetGem.app',
                 icon=icon,
                 bundle_identifier=None,
                 version=version)
