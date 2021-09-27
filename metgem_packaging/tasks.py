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

# noinspection PyShadowingNames
@task
def buildpy(ctx):
    ctx.run("cd {0}/.. && python setup.py build -b {0}/build --build-scripts {0}/build/scripts".format(PACKAGING_DIR))

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


# noinspection PyShadowingNames,PyUnusedLocal
@task
def exe(ctx, clean=False, debug=False, build_py=True):
    if build_py:
        buildpy(ctx)

    switchs = ["--clean"] if clean else []
    if debug:
        switchs.append("--debug all")
    result = ctx.run("pyinstaller {0} --noconfirm {1} --distpath {2} --workpath {3}"
                     .format(os.path.join(PACKAGING_DIR, 'MetGem.spec'), " ".join(switchs), DIST, BUILD))

    if result:
        if sys.platform.startswith('win'):
            embed_manifest(ctx, debug)
            if not debug:
                com(ctx)
        elif sys.platform.startswith('darwin'):
            add_rpath(ctx, debug)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def add_rpath(ctx, debug):
    folder = NAME + "_debug" if debug else NAME
    webengine_process = "{0}/{1}/{2}".format(DIST, folder, 'WebEngineProcess')
    ctx.run('install_name_tool -add_rpath @executable_path/. {}'.format(webengine_process))


# noinspection PyShadowingNames,PyUnusedLocal
@task
def embed_manifest(ctx, debug):
    from PyInstaller.utils.win32 import winmanifest
    folder = NAME + "_debug" if debug else NAME
    exe = "{0}\{1}\{2}.exe".format(DIST, folder, NAME)

    # Embed manifest in exe
    manifest = exe + '.manifest'
    winmanifest.UpdateManifestResourcesFromXMLFile(exe, manifest)
    os.remove(manifest)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def com(ctx):
    # Copy generated exe to .com and change it to a console application
    # See https://www.nirsoft.net/vb/appmodechange.html
    import struct
    import winnt

    exe = "{0}\{1}\{2}.exe".format(DIST, NAME, NAME)
    com = exe.replace('.exe', '.com')
    exe = "{0}\{1}\{2}.exe".format(DIST, NAME, NAME)
    shutil.copy2(exe, com)

    with open(com, 'r+b') as f:
        assert f.read(2) == b'MZ'
        f.seek(0x3C)
        pe_location = struct.unpack('L', f.read(4))[0]
        f.seek(pe_location)
        assert f.read(2) == b'PE'
        f.seek(pe_location + 0x5C)
        subsystem = struct.unpack('B', f.read(1))[0]
        assert subsystem == winnt.IMAGE_SUBSYSTEM_WINDOWS_GUI
        f.seek(pe_location + 0x5C)
        f.write(struct.pack('B', winnt.IMAGE_SUBSYSTEM_WINDOWS_CUI))


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
