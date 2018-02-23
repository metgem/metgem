# Build instructions for Windows (Python 3.6, 64 bits)
Tools can be downloaded from [here](https://mycore.core-cloud.net/index.php/s/2z4z9phDvxplWiE/download)

```
> python -m venv packaging
> cd packaging
> Scripts\activate.bat
> pip install whl\python_igraph-0.7.1.post7-cp36-cp36m-win_amd64.whl
> pip install -r ..\requirements.txt
> pip install pyinstaller
> bin\ImageMagick\convert.exe -density 384 -background transparent ../lib/ui/images/main.svg -define icon:auto-resize -colors 256 main.ico
> pyrcc5 ../lib/ui/ui.qrc -o ../lib/ui/ui_rc.py
> pyinstaller gui.spec
> bin\ResHacker\ResourceHacker.exe -open dist\gui\gui.exe -save dist\gui\gui.exe -action delete -mask ICONGROUP,101, -log CONSOLE
> bin\ResHacker\ResourceHacker.exe -open dist\gui\gui.exe -save dist\gui\gui.exe -resource main.ico -action addoverwrite -mask ICONGROUP,101, -log CONSOLE
> bin\ResHacker\ResourceHacker.exe -open dist\gui\gui.exe -save dist\gui\gui.exe -resource dist\gui\gui.exe.manifest -action add -mask MANIFEST,1, -log CONSOLE
> del dist\gui\gui.exe.manifest
> bin\InnoSetup\ISCC.exe setup.iss
```

# Build instructions for Mac OS (Python 3.6, 64 bits)
First install brew and Python 3, using [these instructions](http://docs.python-guide.org/en/latest/starting/install3/osx/)

```bash
$ cd packaging
$ pip3 install -r ../requirements.txt
$ pip3 install pyinstaller
$ pip3 install dmgbuild
$ brew install imagemagick
$ ./make_icns.sh ../lib/ui/images/main.svg
$ pyrcc5 ../lib/ui/ui.qrc -o ../lib/ui/ui_rc.py
$ pyinstaller gui.spec
$ dmgbuild -s dmgbuild_settings.py '' XXX.dmg
```