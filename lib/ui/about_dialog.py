from PyQt5.QtWidgets import QTextBrowser

from ..config import LICENSE_TEXT

import os
import base64

from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication

UI_FILE = os.path.join(os.path.dirname(__file__), 'about_dialog.ui')
AboutDialogUI, AboutDialogDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')


class AboutDialog(AboutDialogDialogBase, AboutDialogUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        self.setWindowTitle(f"About {QCoreApplication.applicationName()}")
        self.setTitle(QCoreApplication.applicationName())
        self.setVersion(f"Version {QCoreApplication.applicationVersion()}")
        self.setAbout("<p>(c) 2018, CNRS/ICSN</p><p><a href='http://metgem.github.io'>http://metgem.github.io</a></p>")

        authors = f"<p><b>Active Development Team of {QCoreApplication.applicationName()}</b></p>"
        mail = base64.b64decode(b'bmljb2xhcy5lbGllQGNucnMuZnI=').decode()
        authors += f"""<p>Nicolas Elie <a href=\"mailto:{mail}\">{mail}</a><br />
                       <i>Developer and Original Author</i></p>"""
        mail = base64.b64decode(b'ZmxvcmVudC5vbGl2b25AY25ycy5mcg==').decode()
        authors += f"""<p>Florent Olivon <a href=\"mailto:{mail}\">{mail}</a><br />
                      <i>Original Author and Tester</i></p>"""
        mail = base64.b64decode(b'Z3dlbmRhbC5ncmVsaWVyQGNucnMuZnI=').decode()
        authors += f"""<p>Gwendal Grelier <a href=\"mailto:{mail}\">{mail}</a><br />
                      <i>Developer and Tester</i></p>"""
        mail = base64.b64decode(b'ZGF2aWQudG91Ym91bEBjbnJzLmZy=').decode()
        authors += f"""<p>David Touboul <a href=\"mailto:{mail}\">{mail}</a><br />
                      <i>Project Manager</i></p>"""
        authors += """<p><b>Credits</b></p>
            <p><i>Various Suggestions &amp; Testing:</i> Cyrille Santerre</p>"""
        self.setAuthors(authors)

        self.setData(
            """<p><b>Icons</b></p>
            <p>Some icons are taken or derived from <a href=\"http://tango.freedesktop.org/Tango_Desktop_Project">Tango Desktop Project</a>.
            These icons are released to the Public Domain.</p>
            <p>Some icons are taken or derived from <a href=\"https://commons.wikimedia.org/wiki/GNOME_Desktop_icons">Gnome Desktop Icons</a>.
            These icons can be used freely under the terms of the
            <a href=\"https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html\">GNU General Public License version 2</a>.</p>
            <p>Some icons are taken or derived from <a href=\"https://openclipart.org/\">OpenClipart</a>.
            These icons can be used freely under the terms of the
            <a href=\"http://creativecommons.org/publicdomain/zero/1.0/\">CC0 1.0 Universal</a> license.</p>
            """)
        self.setLicenseAgreement(LICENSE_TEXT)

    def _set_browser_text(self, browser: QTextBrowser, text: str):
        browser.setText(text)
        fmt = browser.document().rootFrame().frameFormat()
        fmt.setMargin(12)
        browser.document().rootFrame().setFrameFormat(fmt)

    def setVersion(self, text: str):
        self.lblVersion.setText(text)

    def setTitle(self, text: str):
        self.lblTitle.setText(text)

    def setAbout(self, text: str):
        self._set_browser_text(self.txtAbout, text)

    def setAuthors(self, text: str):
        self._set_browser_text(self.txtAuthors, text)

    def setData(self, text: str):
        self._set_browser_text(self.txtData, text)

    def setLicenseAgreement(self, text: str):
        self._set_browser_text(self.txtLicense, text)
