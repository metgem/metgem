import os
import shutil
import sys

from invoke import task
from PyQt5.pyrcc_main import processResourceFile

PACKAGING_DIR = os.path.dirname(__file__)
DIST = os.path.join(PACKAGING_DIR, 'dist')
BUILD = os.path.join(PACKAGING_DIR, 'build')
NAME = 'MetGem'

if sys.platform.startswith('win'):
    WINDOWS_BIN_URL = 'https://mycore.core-cloud.net/index.php/s/2z4z9phDvxplWiE/download'

    import urllib.request

    def download_file(url, file_name):
        """Download the file from `url` and save it locally under `file_name`:"""

        with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    def extract_zip(file_name, extract_path=PACKAGING_DIR):
        """Extract contents of the zip file `file_name` under the path `extract_path` using no external tools"""

        from win32com.client import gencache

        shell = gencache.EnsureDispatch('Shell.Application')             # Create scripting object
        files = shell.NameSpace(os.path.realpath(file_name)).Items()     # Get list of files in zip
        shell.NameSpace(os.path.realpath(extract_path)).CopyHere(files, 16)  # Extract all files (16=Click "Yes to All" in any dialog box displayed)


@task
def check_dependencies(ctx):
    if sys.platform.startswith('win') and not os.path.exists('bin'):
        print('Download binaries needed for build...', end='\t')
        download_file(WINDOWS_BIN_URL, 'bin.zip')
        extract_zip('bin.zip')
        assert os.path.exists(os.path.join(PACKAGING_DIR, 'bin'))
        os.remove('bin.zip')
        print('Done')


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


@task(check_dependencies)
def build(ctx, clean=False, validate_appstream=True):
    exe(ctx, clean)
    installer(ctx, validate_appstream)


@task(check_dependencies)
def icon(ctx):
    if sys.platform.startswith('win'):
        convert = os.path.join(PACKAGING_DIR, 'bin', 'ImageMagick', 'convert.exe')
        ctx.run("{} -density 384 -background transparent {} -define icon:auto-resize -colors 256 main.ico".format(convert, os.path.join(PACKAGING_DIR, '..', 'metgem', 'ui', 'images', 'main.svg')))


@task(check_dependencies)
def rc(ctx):
    qrcs = [os.path.join(PACKAGING_DIR, '..', 'metgem', 'ui', 'ui.qrc')]
    rc = os.path.join(PACKAGING_DIR, '..', 'metgem', 'ui', 'ui_rc.py')
    skip = False
    if os.path.exists(rc):
        rc_mtime = os.path.getmtime(rc)
        skip = not any([os.path.getmtime(qrc) > rc_mtime for qrc in qrcs])

    if skip:
        print('[RC] resource file is up-to-date, skipping build.')
    else:
        processResourceFile(qrcs, rc, False)


@task(check_dependencies)
def exe(ctx, clean=False, debug=False):
    icon(ctx)
    rc(ctx)

    switchs = ["--clean"] if clean else []
    if debug:
        switchs.append("--debug all")
    result = ctx.run("pyinstaller {0} --noconfirm {1} --distpath {2} --workpath {3}".format(os.path.join(PACKAGING_DIR, 'MetGem.spec'), " ".join(switchs), DIST, BUILD))
    if result:
        if sys.platform.startswith('win'):
            replace_icon(ctx)
            replace_manifest(ctx)


@task(check_dependencies)
def replace_icon(ctx):
    if sys.platform.startswith('win'):
        res_hack = os.path.join(PACKAGING_DIR, 'bin', 'ResHacker', 'ResourceHacker.exe')
        ctx.run("{0} -open {1}\{2}\{2}.exe -save {1}\{2}\{2}.exe -action delete -mask ICONGROUP,101, -log CONSOLE".format(res_hack, DIST, NAME))
        ctx.run("{0} -open {1}\{2}\{2}.exe -save {1}\{2}\{2}.exe -resource main.ico -action addoverwrite -mask ICONGROUP,101, -log CONSOLE".format(res_hack, DIST, NAME))


@task(check_dependencies)
def replace_manifest(ctx):
    if sys.platform.startswith('win'):
        res_hack = os.path.join(PACKAGING_DIR, 'bin', 'ResHacker', 'ResourceHacker.exe')
        ctx.run("{0} -open {1}\{2}\{2}.exe -save {1}\{2}\{2}.exe -resource {1}\{2}\{2}.exe.manifest -action add -mask MANIFEST,1, -log CONSOLE".format(res_hack, DIST, NAME))
        ctx.run("del {0}\{1}\{1}.exe.manifest".format(DIST, NAME))


@task(check_dependencies)
def installer(ctx, validate_appstream=True):
    if sys.platform.startswith('win'):
        iscc = os.path.join(PACKAGING_DIR, 'bin', 'InnoSetup', 'ISCC.exe')
        iss = os.path.join(PACKAGING_DIR, 'setup.iss')
        ctx.run("{} {}".format(iscc, iss))
    elif sys.platform.startswith('darwin'):
        settings = os.path.join(PACKAGING_DIR, 'dmgbuild_settings.py')
        ctx.run("dmgbuild -s {} '' XXX.dmg".format(settings))
    elif sys.platform.startswith('linux'):
        if not os.path.exists('{}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR)):
            ctx.run('wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -P {}'.format(PACKAGING_DIR))
            ctx.run('chmod u+x {}/appimagetool-x86_64.AppImage'.format(PACKAGING_DIR))
        ctx.run('cp -r {0}/{1}/* {2}/AppDir/usr/lib/'.format(DIST, NAME, PACKAGING_DIR))
        switch = '-n' if not validate_appstream else ''
        ctx.run('cd {0} && ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir {1}'.format(PACKAGING_DIR, switch))
        ctx.run('rm -r {}/AppDir/usr/lib/*'.format(PACKAGING_DIR))
