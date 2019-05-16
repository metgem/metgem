import os
import sys
import shutil

from invoke import task

DIST = 'dist'
NAME = 'MetGem'

if sys.platform.startswith('win'):
    WINDOWS_BIN_URL = 'https://mycore.core-cloud.net/index.php/s/2z4z9phDvxplWiE/download'

    import urllib.request

    def download_file(url, file_name):
        """Download the file from `url` and save it locally under `file_name`:"""

        with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    def extract_zip(file_name, extract_path='.'):
        """Extract contents of the zip file `file_name` under the path `extract_path` using no external tools"""

        from win32com.client import gencache

        shell = gencache.EnsureDispatch('Shell.Application')             # Create scripting object
        files = shell.NameSpace(os.path.realpath(file_name)).Items()     # Get list of files in zip
        shell.NameSpace(os.path.realpath(extract_path)).CopyHere(files)  # Extract all files


@task
def check_dependencies(ctx):
    if sys.platform.startswith('win') and not os.path.exists('bin'):
        print('Download binaries needed for build...', end='\t')
        download_file(WINDOWS_BIN_URL, 'bin.zip')
        extract_zip('bin.zip')
        assert(os.path.exists('bin'))
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
def build(ctx, clean=False):
    exe(ctx, clean)
    installer(ctx)


@task(check_dependencies)
def icon(ctx):
    if sys.platform.startswith('win'):
        ctx.run("bin\ImageMagick\convert.exe -density 384 -background transparent ../lib/ui/images/main.svg -define icon:auto-resize -colors 256 main.ico")


@task(check_dependencies)
def rc(ctx):
    ctx.run("pyrcc5 ../lib/ui/ui.qrc -o ../lib/ui/ui_rc.py")


@task(check_dependencies)
def exe(ctx, clean=False):
    icon(ctx)
    rc(ctx)
    switchs = "--clean" if clean else ""
    result = ctx.run("pyinstaller gui.spec --noconfirm" + " " + switchs)
    if result:
        if sys.platform.startswith('win'):
            replace_icon(ctx)
            replace_manifest(ctx)


@task(check_dependencies)
def replace_icon(ctx):
    if sys.platform.startswith('win'):
        ctx.run("bin\ResHacker\ResourceHacker.exe -open {0}\{1}\{1}.exe -save {0}\{1}\{1}.exe -action delete -mask ICONGROUP,101, -log CONSOLE".format(DIST, NAME))
        ctx.run("bin\ResHacker\ResourceHacker.exe -open {0}\{1}\{1}.exe -save {0}\{1}\{1}.exe -resource main.ico -action addoverwrite -mask ICONGROUP,101, -log CONSOLE".format(DIST, NAME))


@task(check_dependencies)
def replace_manifest(ctx):
    if sys.platform.startswith('win'):
        ctx.run("bin\ResHacker\ResourceHacker.exe -open {0}\{1}\{1}.exe -save {0}\{1}\{1}.exe -resource {0}\{1}\{1}.exe.manifest -action add -mask MANIFEST,1, -log CONSOLE".format(DIST, NAME))
        ctx.run("del {0}\{1}\{1}.exe.manifest".format(DIST, NAME))


@task(check_dependencies)
def installer(ctx):
    if sys.platform.startswith('win'):
        ctx.run("bin\InnoSetup\ISCC.exe setup.iss")
    elif sys.platform.startswith('darwin'):
        ctx.run("dmgbuild -s dmgbuild_settings.py '' XXX.dmg")
    elif sys.platform.startswith('linux'):
        import tarfile
        with tarfile.open("dist/MetGem.tar.xz", "w:xz") as tar:
            tar.add("dist/MetGem", arcname="MetGem")
            tar.add("MetGem.sh", arcname="MetGem.sh")
