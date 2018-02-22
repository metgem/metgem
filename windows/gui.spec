# -*- mode: python -*-

import os
import sys

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
             hiddenimports=['igraph.vendor.texttable',
                            'scipy._lib.messagestream',
                            'sklearn.neighbors.typedefs',
                            'sklearn.neighbors.quad_tree',
                            'sklearn.tree._utils',
                            'sklearn.tree._criterion',
                            'sklearn.tree._splitter',
                            'sklearn.tree._tree'
                            'sklearn.tree.tree',
                            'sklearn.tree.export',
                            'sklearn.tree.setup'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', #Remove Tkinter
                       'lib2to3'
                      ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
# Remove MKL binaries
a.binaries = [bin for bin in a.binaries if not bin[0].startswith('mkl_')]
a.binaries = [bin for bin in a.binaries if not bin[0].startswith('api-ms-win-')]
             
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
