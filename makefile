all: icon rc

icon:
	convert -density 384 -background transparent lib/ui/images/main.svg -define icon:auto-resize -colors 256 lib/ui/images/main.ico

rc:
	pyrcc5 lib/ui/ui.qrc -o lib/ui/ui_rc.py

clean:
	rm lib/ui/images/main.ico
	rm lib/ui/ui_rc.py
