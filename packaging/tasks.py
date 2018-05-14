import os
import sys
import glob
import pkg_resources
import shutil

from invoke import task, call

DIST = 'dist'
NAME = 'gui'

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
def check_dependencies(ctx, build=False):
    if build and sys.prefix == sys.base_prefix:
        raise RuntimeError("Build should be done in a virtual env.")

    with open('../requirements.txt', 'r') as f:
        dependencies = f.readlines()

    if build:
        dependencies.append('pyinstaller>=3.3')

        if sys.platform.startswith('darwin'):
            dependencies.append('dmgbuild>=1.3')

    pkg_resources.require(dependencies)

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


@task(call(check_dependencies, build=True))
def build(ctx, clean=False):
    exe(ctx, clean)
    installer(ctx)

@task
def build_modules(ctx):
    if sys.platform.startswith('win'):
        packaging_dir = os.path.dirname(__file__)

        # Build cosine-cython extension
        path = os.path.join(packaging_dir, '..', 'cosine-cython')
        ctx.run(rf'cd /d {path} & python setup.py build_ext --inplace')
        dest = os.path.join(packaging_dir, '..', 'lib', 'workers', 'ext')
        if not os.path.exists(dest):
            os.makedirs(dest)
        for module in glob.glob(os.path.join(path, '*.pyd')):
            shutil.copy(module, dest)

        # Build force atlas 2 extension
        path = os.path.join(packaging_dir, '..', 'forceatlas2')
        dest = os.path.join(packaging_dir, '..', 'lib', 'workers', 'ext', 'fa2')
        if not os.path.exists(dest):
            os.makedirs(dest)
        ctx.run(rf'cd /d {path} & python setup.py build_ext --inplace')
        for module in glob.glob(os.path.join(path, 'fa2', '*.py*')):
            shutil.copy(module, dest)
    else:
        pass  # TODO: Allow packaging of dependencies on other platforms


@task(check_dependencies)
def icon(ctx):
    if sys.platform.startswith('win'):
        ctx.run("bin\ImageMagick\convert.exe -density 384 -background transparent ../lib/ui/images/main.svg -define icon:auto-resize -colors 256 main.ico")
    elif sys.platform.startswith('darwin'):
        ctx.run("./make_icns.sh ../lib/ui/images/main.svg")


@task(check_dependencies)
def rc(ctx):
    ctx.run("pyrcc5 ../lib/ui/ui.qrc -o ../lib/ui/ui_rc.py")


@task(call(check_dependencies, build=True))
def exe(ctx, clean=False):
    build_modules(ctx)
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

