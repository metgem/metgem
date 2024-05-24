import base64
import platform

from PySide6.QtCore import QCoreApplication, qVersion, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QTextBrowser, QDialog, QApplication, QWidget, QGraphicsOpacityEffect
from PySide6 import __version__ as PYSIDE_VERSION

from metgem.config import LICENSE_TEXT, BUILD_VERSION
from metgem.ui.about_dialog_ui import Ui_AboutDialog


def copy_version_info(debug=False):
    info = f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}"
    if BUILD_VERSION:
        info += f" (build {BUILD_VERSION})"

    if debug:
        info += "\n\n"
        info += f"\tPython version:\t{platform.python_version()} ({platform.python_implementation()})\n"
        info += f"\tQt version:\t{qVersion()}\n"
        info += f"\tPySide version:\t{PYSIDE_VERSION}\n"
        info += "\n"
        info += f"\tOS Version:\t{platform.platform()}\n"

    cb = QApplication.clipboard()
    cb.clear()
    cb.setText(info)


class AboutDialog(QDialog, Ui_AboutDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self.effect = None
        self.animation = None

        self.btCopyVersion.clicked.connect(self.copyVersionToClipboard)
        self.btCopyDebugInfo.clicked.connect(self.copyDebugInfoToClipboard)

        self.tabWidget.setCurrentIndex(0)

        appname = QCoreApplication.applicationName()
        self.setWindowTitle(f"About {appname}")
        self.setTitle(appname)
        self.setVersion(f"Version {QCoreApplication.applicationVersion()}")
        self.setBuildVersion(BUILD_VERSION if BUILD_VERSION else None)
        self.setAbout("<p>(C) 2018-2024, CNRS/ICSN</p>"
                      f"<p><a href='https://metgem.github.io/'>{appname}</a></p>"
                      "<p><a href='https://github.com/metgem'>Source Code</a></p>")

        authors = f"<p><b>Active Development Team</b></p>"
        mail = base64.b64decode(b'bmljb2xhcy5lbGllQGNucnMuZnI=').decode()
        authors += f"""<p>Nicolas Elie <a href=\"mailto:{mail}\">{mail}</a><br />
                       <i>Main Developer and Original Author</i></p>"""

        authors += """<p><b>Credits</b></p>
                    <p><i>Various Suggestions &amp; Testing:</i> Cyrille Santerre, Simon Remy, Florence Mondeguer, Orianne Brel,
                    Morgane Barthélémy, Téo Hebra, Marceau Levasseur, Cécile Apel, Marie Valmori</p>"""

        authors += f"<p><b>Former Development Team</b></p>"
        mail = base64.b64decode(b'ZGF2aWQudG91Ym91bEBjbnJzLmZy=').decode()
        authors += f"""<p>David Touboul <a href=\"mailto:{mail}\">{mail}</a><br />
                              <i>Project Manager and Tester</i></p>"""
        mail = base64.b64decode(b'ZmxvcmVudC5vbGl2b25AY25ycy5mcg==').decode()
        authors += f"""<p>Florent Olivon <a href=\"mailto:{mail}\">{mail}</a><br />
                              <i>Original Author and Tester</i></p>"""
        mail = base64.b64decode(b'Z3dlbmRhbC5ncmVsaWVyQGNucnMuZnI=').decode()
        authors += f"""<p>Gwendal Grelier <a href=\"mailto:{mail}\">{mail}</a><br />
                              <i>Developer and Tester</i></p>"""
        self.setAuthors(authors)

        # noinspection PyPep8
        self.setData(
            """<p><b>Icons</b></p>
            <p>MetGem Logo can be used freely under the terms of the <a href=\"http://creativecommons.org/publicdomain/zero/1.0/\">CC0 1.0 Universal</a> license.</p>
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
        # noinspection PyPep8
        self.setLibraries(
            f"<p><b>Third-party libraries used by {appname}</b></p>"
            f"<p>{appname} is built on the following free software libraries:</p>"
            "<p><ul>"
            "<li><a href=\"https://www.python.org/\">Python</a>: Python Software Foundation License v2</li>"
            "<li><a href=\"https://www.numpy.org/\">Numpy</a>: 3-clause BSD</li>"
            "<li><a href=\"https://www.scipy.org/\">Scipy</a>: 3-clause BSD</li>"
            "<li><a href=\"http://cython.org/\">Cython</a>: Apache v2</li>"
            "<li><a href=\"https://www.openmp.org/\">OpenMP</a>: MIT</li>"
            "<li><a href=\"https://www.qt.io/\">Qt</a>: GPLv2 + GPLv3 + LGPLv2.1 + LGPLv3</li>"
            "<li><a href=\"http://www.pyside.org/\">PySide6</a>: LGPLv2.1</li>"
            "<li><a href=\"https://www.pyside.org\">Shiboken6</a>: LGPLv3</li>"
            "<li><a href=\"https://pandas.pydata.org/\">Pandas</a>: 3-clause BSD</li>"
            "<li><a href=\"https://arrow.apache.org/\">PyArrow</a>: Apache v2</li>"
            "<li><a href=\"http://scikit-learn.org/\">Scikit-learn</a>: 3-clause BSD</li>"
            "<li><a href=\"http://lxml.de/\">lxml</a>: BSD</li>"
            "<li><a href=\"http://pyteomics.readthedocs.io/\">Pyteomics</a>: Apache v2</li>"
            "<li><a href=\"http://igraph.org/\">igraph</a>: GPLv2</li>"        
            "<li><a href=\"http://jupyter.org/\">Jupyter</a>: 3-clause BSD</li>"
            "<li><a href=\"https://matplotlib.org/\">Matplotlib</a>: BSD-like</li>"
            "<li><a href=\"http://docs.python-requests.org\">Requests</a>: Apache v2</li>"
            "<li><a href=\"http://www.sqlalchemy.org/\">SQLAlchemy</a>: MIT</li>"
            "<li><a href=\"https://www.sqlite.org\">SQLite</a>: Public Domain</li>"
            "<li><a href=\"https://github.com/cytoscape/py2cytoscape\">py2cytoscape</a>: MIT</li>"
            "<li><a href=\"https://github.com/mhammond/pywin32\">pywin32</a>: Python Software Foundation License</li>"
            "<li><a href=\"https://github.com/bhargavchippada/forceatlas2\">Gephi's ForceAtlas2</a>: GPLv3</li>"
            "<li><a href=\"https://qtconsole.readthedocs.io/en/stable\">qtconsole</a>: 3-clause BSD</li>"
            "<li><a href=\"http://pluginbase.pocoo.org/\">pluginbase</a>: 3-clause BSD</li>"
            "<li><a href=\"https://pyyaml.org/\">PyYAML</a>: MIT</li>"
            "<li><a href=\"http://www.rdkit.org//\">RDKit</a>: 3-clause BSD</li>"
            "<li><a href=\"https://numexpr.readthedocs.io/\">NumExpr</a>: MIT</li>"
            "<li><a href=\"https://github.com/python-excel/xlrd/\">xlrd</a>: 3-clause BSD</li>"
            "<li><a href=\"https://github.com/eea/odfpy/\">odfpy</a>: Apache v2</li>"
            "<li><a href=\"https://github.com/kurtmckee/feedparser/\">xlrd</a>: MIT</li>"
            "<li><a href=\"https://mplcursors.readthedocs.io/\">mplcursors</a>: MIT</li>"
            "<li><a href=\"https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System/\">"
            "Qt-Advanced-Docking-System</a>: LGPL v2.1</li>"
            "<li><a href=\"https://github.com/mborgerson/pyside6_qtads/\">PySide6QtAds</a>: LGPL v2.1</li>"
            "<li><a href=\"https://github.com/jeremysanders/pyemf3/\">pyemf3</a>: GPL v2</li>"
            "<li><a href=\"https://github.com/metgem/QtMolecularNetwork/\">QtMolecularNetwork</a>: GPLv3</li>"
            "<li><a href=\"https://github.com/metgem/libmetgem/\">libmetgem</a>: GPL v3</li>"
            "<li><a href=\"http://numba.pydata.org/\">numba</a>: 2-clause BSD</li>"
            "<li><a href=\"https://umap-learn.readthedocs.io/\">umap-learn</a>: 3-clause BSD</li>"
            "<li><a href=\"http://phate.readthedocs.io/\">PHATE</a>: GPL v2</li>"
            "<li><a href=\"https://hdbscan.readthedocs.io/\">hdbscan</a>: 3-clause BSD</li>"
            "</ul></p>"
        )

    def _set_browser_text(self, browser: QTextBrowser, text: str):
        browser.document().setDefaultStyleSheet("a { text-decoration: underline; color: palette(window-text); }")
        browser.setText(text)
        fmt = browser.document().rootFrame().frameFormat()
        fmt.setMargin(12)
        browser.document().rootFrame().setFrameFormat(fmt)

    def setVersion(self, text: str):
        self.lblVersion.setText(text)

    def setBuildVersion(self, text: str):
        self.lblBuildVersion.setText(f"<i>Build {text}</i>" if text is not None else "")

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

    def setLibraries(self, text: str):
        self._set_browser_text(self.txtLibraries, text)

    def copyVersionToClipboard(self):
        copy_version_info()
        self.show_info("Version copied to clipboard!")

    def copyDebugInfoToClipboard(self):
        copy_version_info(debug=True)
        self.show_info("Debug info copied to clipboard!")

    def show_info(self, text: str):
        self.lblCopy.setText(text)

        self.effect = QGraphicsOpacityEffect(self.lblCopy)
        self.lblCopy.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.effect.setOpacity(.0)
        self.animation.setDuration(1000)
        self.animation.setStartValue(.0)
        self.animation.setEndValue(.7)
        self.animation.setEasingCurve(QEasingCurve.InQuad)
        self.animation.finished.connect(lambda: QTimer.singleShot(1000, fadeout))
        self.animation.start()

        def fadeout():
            self.effect = QGraphicsOpacityEffect(self.lblCopy)
            self.lblCopy.setGraphicsEffect(self.effect)
            self.animation = QPropertyAnimation(self.effect, b"opacity")
            self.effect.setOpacity(.7)
            self.animation.setDuration(1000)
            self.animation.setStartValue(.7)
            self.animation.setEndValue(.0)
            self.animation.setEasingCurve(QEasingCurve.OutQuad)
            self.animation.finished.connect(lambda: self.lblCopy.setText(""))
            self.animation.start()
