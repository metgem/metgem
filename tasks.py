import glob
import tqdm
import subprocess
import os
import sys
import shutil

from invoke import task

SOURCE_DIR = os.path.dirname(__file__)

# noinspection PyShadowingNames,PyUnusedLocal
@task
def uic(ctx, filename=''):
    if not filename:
        filename = '*'
        
    if shutil.which('pyside6-uic'):
        uic_cmd = [r'pyside6-uic']
    elif shutil.which('uic'):
        uic_cmd = [r'uic', '-g', 'python']
    else:
        raise RuntimeError("UIC executable not found, make sure Qt6 is installed in the current environment")

    files = glob.glob(os.path.join(SOURCE_DIR, 'metgem', 'ui', '**', filename + '.ui'),
                      recursive=True)
    for fn in tqdm.tqdm(files):
        fn = os.path.realpath(fn)
        out = fn[:-3] + '_ui.py'
        subprocess.run([*uic_cmd, fn, '-o', out],
                       shell=sys.platform == 'win32',
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)
    print(f'[UIC] {len(files)} UI file(s) updated.')


# noinspection PyShadowingNames,PyUnusedLocal
@task
def rc(ctx, force=False):
    if shutil.which('pyside6-rc'):
        rc_cmd = [r'pyside6-rc']
    elif shutil.which('rc'):
        rc_cmd = [r'rc', '-g', 'python']
    else:
        raise RuntimeError("UIC executable not found, make sure Qt6 is installed in the current environment")
    
    qrcs = [os.path.join(SOURCE_DIR, 'metgem', 'ui', 'ui.qrc')]
    rc = os.path.join(SOURCE_DIR, 'metgem', 'ui', 'ui_rc.py')
    skip = False
    if not force and os.path.exists(rc):
        rc_mtime = os.path.getmtime(rc)
        skip = not any([os.path.getmtime(qrc) > rc_mtime for qrc in qrcs])

    if skip:
        print('[RC] resource file is up-to-date, skipping build.')
    else:
        subprocess.run([*rc_cmd, '-o', rc, ' '.join(qrcs)],
                       shell=sys.platform == 'win32')
        print('[RC] Resource file updated.')
