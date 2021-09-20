import os

from PyQt5 import uic
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo

UI_FILE = os.path.join(os.path.dirname(__file__), 'in_silico_db_dialog.ui')
InSilicoDBDialogUI, InSilicoDBDialogDialogBase = uic.loadUiType(UI_FILE,
                                                                from_imports='metgem_app.ui',
                                                                import_from='metgem_app.ui')


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


class InSilicoDBDialog(InSilicoDBDialogDialogBase, InSilicoDBDialogUI):
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
        self.browser.setPage(WebEnginePage(self.profile, self.browser))
        if self.url is not None:
            self.browser.load(self.url)
        self.browser.loadFinished.connect(self.on_load_finished)

    def page(self):
        return self.browser.page()

    def on_load_finished(self, ok):
        raise NotImplementedError

    def ready(self, returnValue):
        print(returnValue)

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)

        # QWebEnginePage should be deleted before QWebEngineProfile
        # or 'Release of profile requested but WebEnginePage still not deleted. Expect troubles !' error occurs
        self.browser.page().deleteLater()


class MetFragDialog(InSilicoDBDialog):
    url = QUrl('https://msbi.ipb-halle.de/MetFrag/')
    title = 'MetFrag'
    icon = QIcon(':/icons/images/metfrag.png')

    def on_load_finished(self, ok):
        if not ok:
            return

        self.page().runJavaScript(f"""
            document.getElementById('mainForm:mainAccordion:inputNeutralMonoisotopicMass').value = '';
            document.getElementById('mainForm:mainAccordion:inputMeasuredMass').value = '{self.mz}';
            document.getElementById('mainForm:mainAccordion:peakListInput').value = '{self.spectrum}';
            """)

        self.page().runJavaScript(f"""
            document.getElementById('footer').hidden = true;
            document.getElementsByClassName('ui-dialog-user')[0].remove();
            """)


class CFMIDDialog(InSilicoDBDialog):
    url = QUrl('http://cfmid4.wishartlab.com/identify')
    title = 'CFM-ID'
    icon = QIcon(':/icons/images/cfm-id.png')

    def on_load_finished(self, ok):
        if not ok:
            return

        self.page().runJavaScript(f"""
            document.getElementById('identify_query_parent_ion_mass').value = '{self.mz}';
            document.getElementById('medium_spectra').value = '{self.spectrum}';
            """)

        self.page().runJavaScript("""
            document.getElementById('submit-candidates-toggle').parentNode.hidden = true;
            document.querySelectorAll("label[for='identify_query_candidates_input']")[0].hidden = true;
            document.getElementsByClassName("example-loader-esi-1")[0].parentNode.hidden = true;
            document.getElementsByClassName("example-loader-esi-2")[0].parentNode.hidden = true;
            document.getElementsByClassName("example-loader-esi-1")[0].parentNode.previousElementSibling.hidden = true;
            document.getElementById('spectra-file-toggle').parentNode.hidden = true;
            """)
