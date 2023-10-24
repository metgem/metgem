import glob
import tqdm
import subprocess
import os
import sys

from invoke import task

SOURCE_DIR = os.path.dirname(__file__)

# noinspection PyShadowingNames,PyUnusedLocal
@task
def uic(ctx, filename=''):
    if not filename:
        filename = '*'

    files = glob.glob(os.path.join(SOURCE_DIR, 'metgem', 'ui', '**', filename + '.ui'),
                      recursive=True)
    for fn in tqdm.tqdm(files):
        fn = os.path.realpath(fn)
        out = fn[:-3] + '_ui.py'
        subprocess.run([r'uic', '-g', 'python', fn, '-o', out],
                       shell=sys.platform == 'win32',
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)
    print(f'[UIC] {len(files)} UI file(s) updated.')


# noinspection PyShadowingNames,PyUnusedLocal
@task
def rc(ctx, force=False):
    qrcs = [os.path.join(SOURCE_DIR, 'metgem', 'ui', 'ui.qrc')]
    rc = os.path.join(SOURCE_DIR, 'metgem', 'ui', 'ui_rc.py')
    skip = False
    if not force and os.path.exists(rc):
        rc_mtime = os.path.getmtime(rc)
        skip = not any([os.path.getmtime(qrc) > rc_mtime for qrc in qrcs])

    if skip:
        print('[RC] resource file is up-to-date, skipping build.')
    else:
        subprocess.run([r'rcc', '-g', 'python', '-o', rc, ' '.join(qrcs)],
                       shell=sys.platform == 'win32')
        print('[RC] Resource file updated.')
