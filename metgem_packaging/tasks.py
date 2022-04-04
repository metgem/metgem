import glob
import json
import os
import shutil
import sys
import tempfile
import subprocess


from invoke import task

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
        subprocess.run(['pyside2-rcc', '-o', rc, ' '.join(qrcs)],
                       shell=True)
        print('[RC] Resource file updated.')

# noinspection PyShadowingNames,PyUnusedLocal
@task
def uic(ctx, filename=''):
    if not filename:
        filename = '*'

    for fn in glob.glob(os.path.join(PACKAGING_DIR, '..', 'metgem_app', 'ui', '**', filename + '.ui'), recursive=True):
        fn = os.path.realpath(fn)
        out = fn[:-3] + '_ui.py'
        subprocess.run(['pyside2-uic', fn, '-o', out],
                       shell=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)
    print(f'[UIC] {len(files)} UI file(s) updated.')


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
            add_rpath(ctx)


# noinspection PyShadowingNames,PyUnusedLocal
@task
def add_rpath(ctx):
    webengine_process = "{0}/{1}.app/Contents/MacOS/QtWebEngineProcess".format(DIST, NAME)
    ctx.run('install_name_tool -add_rpath @executable_path/. {}'.format(webengine_process))


# noinspection PyShadowingNames,PyUnusedLocal
@task
def embed_manifest(ctx, debug):
    from PyInstaller.utils.win32 import winmanifest
    folder = NAME + "_debug" if debug else NAME
    exe = "{0}\{1}\{2}.exe".format(DIST, folder, NAME)

    # Embed manifest in exe
    manifest = exe + '.manifest'
    if os.path.exists(manifest):
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
        ctx.run(f"{iscc} {iss}")
    elif sys.platform.startswith('darwin'):
        output = os.path.join(PACKAGING_DIR, NAME + '.dmg')
        if os.path.exists(output):
            os.unlink(output)

        with tempfile.TemporaryDirectory() as tmp_dir:
            application = os.path.join(PACKAGING_DIR, 'dist', NAME + '.app')
            icon = os.path.join(PACKAGING_DIR, 'main.icns')
            source_folder = os.path.join(tmp_dir, NAME)
            tmp_application = os.path.join(source_folder, NAME + '.app')

            os.makedirs(source_folder)
            subprocess.run([os.path.join(PACKAGING_DIR, 'set_folder_icon.sh'), icon, tmp_dir, NAME], shell=True)

            shutil.copytree(application, tmp_application)
            shutil.copytree(os.path.join(PACKAGING_DIR, '..', 'examples'),
                            os.path.join(source_folder, 'examples'))

            appdmg_json = {'title': NAME,
                           'icon': icon,
                           'icon-size': 150,
                           'background': os.path.join(PACKAGING_DIR, 'installer_background.png'),
                           'window': {'size': {'width': 800, 'height': 400}},
                           'contents': [{'x': 525, 'y': 125, 'type': 'link', 'path': '/Applications'},
                                        {'x': 125, 'y': 125, 'type': 'file', 'path': source_folder}]}
            appdmg_json_fn = os.path.join(PACKAGING_DIR, 'appdmg.json')
            with open(appdmg_json_fn, 'w') as f:
                json.dump(appdmg_json, f)

            subprocess.run(['appdmg', appdmg_json_fn, output], shell=True)
    elif sys.platform.startswith('linux'):
        if not os.path.exists('{}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR)):
            ctx.run('wget {} -P {}'.format(APPIMAGE_TOOL_URL, PACKAGING_DIR))
            ctx.run('chmod u+x {}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR))
        ctx.run('cp -r {0}/{1}/* {2}/AppDir/usr/lib/'.format(DIST, NAME, PACKAGING_DIR))
        switch = '-n' if not validate_appstream else ''
        ctx.run('cd {0} && ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir {1}'.format(PACKAGING_DIR, switch))
        ctx.run('rm -r {}/AppDir/usr/lib/*'.format(PACKAGING_DIR))
