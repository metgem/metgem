import base64
import os

from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QTextBrowser

from ..config import LICENSE_TEXT

UI_FILE = os.path.join(os.path.dirname(__file__), 'about_dialog.ui')
AboutDialogUI, AboutDialogDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='metgem_app.ui',
                                                      import_from='metgem_app.ui')


class AboutDialog(AboutDialogDialogBase, AboutDialogUI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)

        appname = QCoreApplication.applicationName()
        self.setWindowTitle(f"About {appname}")
        self.setTitle(appname)
        self.setVersion(f"Version {QCoreApplication.applicationVersion()}")
        self.setAbout("<p>(C) 2018-2021, CNRS/ICSN</p>"
                      f"<p><a href='https://metgem.github.io/'>{appname}</a></p>"
                      "<p><a href='https://github.com/metgem'>Source Code</a></p>")

        authors = f"<p><b>Active Development Team</b></p>"
        mail = base64.b64decode(b'bmljb2xhcy5lbGllQGNucnMuZnI=').decode()
        authors += f"""<p>Nicolas Elie <a href=\"mailto:{mail}\">{mail}</a><br />
                       <i>Main Developer and Original Author</i></p>"""
        mail = base64.b64decode(b'ZGF2aWQudG91Ym91bEBjbnJzLmZy=').decode()
        authors += f"""<p>David Touboul <a href=\"mailto:{mail}\">{mail}</a><br />
                      <i>Project Manager and Tester</i></p>"""
        authors += f"<p><b>Former Development Team</b></p>"
        mail = base64.b64decode(b'ZmxvcmVudC5vbGl2b25AY25ycy5mcg==').decode()
        authors += f"""<p>Florent Olivon <a href=\"mailto:{mail}\">{mail}</a><br />
                              <i>Original Author and Tester</i></p>"""
        mail = base64.b64decode(b'Z3dlbmRhbC5ncmVsaWVyQGNucnMuZnI=').decode()
        authors += f"""<p>Gwendal Grelier <a href=\"mailto:{mail}\">{mail}</a><br />
                              <i>Developer and Tester</i></p>"""
        authors += """<p><b>Credits</b></p>
            <p><i>Various Suggestions &amp; Testing:</i> Cyrille Santerre, Simon Remy, Florence Mondeguer, Orianne Brel,
            Morgane Barthélémy, Téo Hebra</p>"""
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
            "<li><a href=\"https://www.riverbankcomputing.com/software/pyqt/download5\">PyQt</a>: GPLv3</li>"
            "<li><a href=\"https://www.riverbankcomputing.com/software/sip/download\">sip</a>: SIP License + GPLv2 + GPLv3</li>"
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
            "<li><a href=\"http://www.rdkit.org//\">rdKIT</a>: 3-clause BSD</li>"
            "<li><a href=\"https://numexpr.readthedocs.io/\">NumExpr</a>: MIT</li>"
            "<li><a href=\"https://github.com/python-excel/xlrd/\">xlrd</a>: 3-clause BSD</li>"
            "<li><a href=\"https://github.com/eea/odfpy/\">odfpy</a>: Apache v2</li>"
            "<li><a href=\"https://github.com/kurtmckee/feedparser/\">xlrd</a>: MIT</li>"
            "<li><a href=\"https://mplcursors.readthedocs.io/\">mplcursors</a>: MIT</li>"
            "<li><a href=\"https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System/\">"
            "Qt-Advanced-Docking-System</a>: LGPL v2.1</li>"
            "<li><a href=\"https://github.com/metgem/pyemf/\">pyemf</a>: GPL v2</li>"
            "<li><a href=\"https://github.com/metgem/PyQtNetworkView/\">PyQtNetworkView</a>: GPL v3</li>"
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
