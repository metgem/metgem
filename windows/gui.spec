# -*- mode: python -*-

import os
import sys
import glob

DEBUG = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1')

# Encrypt files?
block_cipher = None

# Remove Tkinter: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-remove-tkinter-tcl
sys.modules['FixTk'] = None

a = Analysis(['../gui.py'],
             pathex=[r'Lib\site-packages\scipy\extra-dll'],
             binaries=[],
             datas=[('../LICENSE', ''),
                    ('../examples/*', 'examples'),
                    ('../lib/ui/*_rc.py', 'lib/ui'),
                    ('../lib/ui/*.ui', 'lib/ui'),
                    ('../lib/ui/images/*', 'lib/ui/images'),
                    ('../lib/ui/widgets/*.ui', 'lib/ui/widgets')],
             hiddenimports=[],
             hookspath=['hooks'],
             runtime_hooks=sorted(glob.glob('rthooks/*_pyi_*.py')),
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', #Remove Tkinter
                       'lib2to3'
                      ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
# Remove MKL binaries
a.binaries = [bin for bin in a.binaries if not bin[0].startswith('mkl_')]
a.binaries = [bin for bin in a.binaries if not bin[0].startswith('api-ms-win-')]

# Remove unused IPthon data files
a.datas = [dat for dat in a.datas if not dat[0].startswith('IPython')]
             
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
             
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='gui',
          debug=DEBUG,
          strip=False,
          upx=False,
          console=DEBUG)
          
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='gui')
