import os
import shutil
import sys

from invoke import task
from PyQt5.pyrcc_main import processResourceFile

PACKAGING_DIR = os.path.dirname(__file__)
DIST = os.path.join(PACKAGING_DIR, 'dist')
BUILD = os.path.join(PACKAGING_DIR, 'build')
NAME = 'MetGem'
APPIMAGE_TOOL_URL = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"


@task
def clean(ctx, dist=False, bytecode=False, extra=''):
    patterns = ['build']
    if dist:
        patterns.append('dist')
    if bytecode:
        patterns.append('*.pyc')
    if extra:
        patterns.append(extra)
    for pattern in patterns:
        if sys.platform.startswith('win'):
            ctx.run("del /s /q {}".format(pattern))
        else:
            ctx.run("rm -rf {}".format(pattern))


# noinspection PyShadowingNames
@task
def build(ctx, clean=False, validate_appstream=True):
    exe(ctx, clean)
    installer(ctx, validate_appstream)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def rc(ctx):
    qrcs = [os.path.join(PACKAGING_DIR, '..', 'metgem_app', 'ui', 'ui.qrc')]
    rc = os.path.join(PACKAGING_DIR, '..', 'metgem_app', 'ui', 'ui_rc.py')
    skip = False
    if os.path.exists(rc):
        rc_mtime = os.path.getmtime(rc)
        skip = not any([os.path.getmtime(qrc) > rc_mtime for qrc in qrcs])

    if skip:
        print('[RC] resource file is up-to-date, skipping build.')
    else:
        processResourceFile(qrcs, rc, False)


# noinspection PyShadowingNames
@task
def exe(ctx, clean=False, debug=False):
    rc(ctx)

    switchs = ["--clean"] if clean else []
    if debug:
        switchs.append("--debug all")
    result = ctx.run("pyinstaller {0} --noconfirm {1} --distpath {2} --workpath {3}"
                     .format(os.path.join(PACKAGING_DIR, 'MetGem.spec'), " ".join(switchs), DIST, BUILD))
    if result and sys.platform.startswith('win'):
        from PyInstaller.utils.win32 import winmanifest
        exe = "{0}\{1}\{1}.exe".format(DIST, NAME)
        manifest = exe + '.manifest'
        winmanifest.UpdateManifestResourcesFromXMLFile(exe, manifest)
        os.remove(manifest)


@task
def installer(ctx, validate_appstream=True):
    if sys.platform.startswith('win'):
        iscc = shutil.which("ISCC")
        iss = os.path.join(PACKAGING_DIR, 'setup.iss')
        ctx.run("{} {}".format(iscc, iss))
    elif sys.platform.startswith('darwin'):
        settings = os.path.join(PACKAGING_DIR, 'dmgbuild_settings.py')
        ctx.run("dmgbuild -s {} '' XXX.dmg -Dpackaging_dir={}".format(settings, PACKAGING_DIR))
    elif sys.platform.startswith('linux'):
        if not os.path.exists('{}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR)):
            ctx.run('wget {} -P {}'.format(APPIMAGE_TOOL_URL, PACKAGING_DIR))
            ctx.run('chmod u+x {}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR))
        ctx.run('cp -r {0}/{1}/* {2}/AppDir/usr/lib/'.format(DIST, NAME, PACKAGING_DIR))
        switch = '-n' if not validate_appstream else ''
        ctx.run('cd {0} && ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir {1}'.format(PACKAGING_DIR, switch))
        ctx.run('rm -r {}/AppDir/usr/lib/*'.format(PACKAGING_DIR))
