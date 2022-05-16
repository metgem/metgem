import os
import tempfile
from typing import Iterable

import pandas as pd
from qtpy.QtCore import QUrl, Qt
from qtpy.QtGui import QCloseEvent, QIcon
from qtpy.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile
from PySide2.QtWebEngineWidgets import QWebEngineDownloadItem, QWebEngineScript
from qtpy.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from qtpy.QtWidgets import QDialog
from .in_silico_db_dialog_ui import Ui_InSilicoDBDialog


class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)


class WebEngineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):

    def __init__(self, url: QUrl):
        super().__init__()
        self.url = url

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if info.navigationType() == QWebEngineUrlRequestInfo.NavigationTypeLink:
            if info.requestUrl().url() in info.firstPartyUrl().url():
                info.redirect(self.url)


class InSilicoDBDialog(QDialog, Ui_InSilicoDBDialog):
    url = None
    title = None
    icon = None

    def __init__(self, parent, mz, spectrum):
        super().__init__(parent)

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        if self.title is not None:
            self.setWindowTitle(self.title)
        if self.icon is not None:
            self.setWindowIcon(self.icon)

        self.mz = mz
        self.spectrum = '\\n'.join(" ".join(f'{x:.4f}' for x in peak) for peak in spectrum)

        self.interceptor = WebEngineUrlRequestInterceptor(self.url)
        self.profile = QWebEngineProfile()
        self.profile.setRequestInterceptor(self.interceptor)
        self.profile.downloadRequested.connect(self.on_download_requested)
        self.browser.setPage(WebEnginePage(self.profile, self.browser))

        for script in self.create_scripts():
            self.page().scripts().insert(script)

        if self.url is not None:
            self.browser.load(self.url)

        self._result = None

    def page(self):
        return self.browser.page()

    def create_scripts(self) -> Iterable[QWebEngineScript]:
        yield

    def on_download_requested(self, download: QWebEngineDownloadItem):
        path = ''
        tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(tmpdir.name, 'metgem.csv')
        download.setPath(path)

        def download_finished():
            self._result = self.read_results_file(path)
            tmpdir.cleanup()
            self.accept()

        download.finished.connect(download_finished)
        download.accept()

    def done(self, r):
        if r == QDialog.Accepted and self._result is None:
            self.start_download()
        super().done(r)

    def start_download(self):
        raise NotImplementedError

    def read_results_file(self, path: str):
        raise NotImplementedError

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)

        # QWebEnginePage should be deleted before QWebEngineProfile
        # or 'Release of profile requested but WebEnginePage still not deleted. Expect troubles !' error occurs
        self.browser.page().deleteLater()

    def getValues(self):
        return self._result


class MetFragDialog(InSilicoDBDialog):
    url = QUrl('https://msbi.ipb-halle.de/MetFrag/')
    title = 'MetFrag'
    icon = QIcon(':/icons/images/metfrag.png')

    def create_scripts(self) -> Iterable[QWebEngineScript]:
        script = QWebEngineScript()
        script.setInjectionPoint(QWebEngineScript.DocumentReady)
        script.setSourceCode(f"""
            document.getElementById('mainForm:mainAccordion:inputNeutralMonoisotopicMass').value = '';
            document.getElementById('mainForm:mainAccordion:inputMeasuredMass').value = '{self.mz}';
            document.getElementById('mainForm:mainAccordion:peakListInput').value = '{self.spectrum}';
            document.getElementById('footer').hidden = true;
            document.getElementsByClassName('ui-dialog-user')[0].remove();
            """)
        yield script

    def start_download(self):
        self.browser.page().runJavaScript(
            """document.querySelector("form[name='downloadResultsFormCSV'] a").click();""")

    def read_results_file(self, path: str):
        return pd.read_csv(path, sep=',')

    def done(self, r):
        if r == QDialog.Accepted and self._result is None:
            self.start_download()
        super().done(r)


class CFMIDDialog(InSilicoDBDialog):
    url = QUrl('http://cfmid4.wishartlab.com/identify')
    title = 'CFM-ID'
    icon = QIcon(':/icons/images/cfm-id.png')

    def create_scripts(self) -> Iterable[QWebEngineScript]:
        script = QWebEngineScript()
        script.setInjectionPoint(QWebEngineScript.DocumentReady)
        script.setSourceCode(f"""
            document.getElementById('identify_query_parent_ion_mass').value = '{self.mz}';
            document.getElementById('medium_spectra').value = '{self.spectrum}';
            
            document.getElementById('submit-candidates-toggle').parentNode.hidden = true;
            document.querySelectorAll("label[for='identify_query_candidates_input']")[0].hidden = true;
            document.getElementsByClassName("example-loader-esi-1")[0].parentNode.hidden = true;
            document.getElementsByClassName("example-loader-esi-2")[0].parentNode.hidden = true;
            document.getElementsByClassName("example-loader-esi-1")[0].parentNode.previousElementSibling.hidden = true;
            document.getElementById('spectra-file-toggle').parentNode.hidden = true;
            """)
        yield script

    def start_download(self):
        self.browser.page().runJavaScript(
            """document.querySelector('div#results a.btn-download').click();""")

    def read_results_file(self, path: str):
        with open(path, 'r') as f:
            return f.read()
