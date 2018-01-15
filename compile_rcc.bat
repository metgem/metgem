@echo off

REM COnvert SVG icon to icon format
convert -density 384 -background transparent lib/ui/images/main.svg -define icon:auto-resize -colors 256 lib/ui/images/main.ico

REM Compile resources
pyrcc5.exe lib\ui\ui.qrc -o lib\ui\ui_rc.py