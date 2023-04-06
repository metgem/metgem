import webbrowser

from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from .updates_dialog_ui import Ui_UpdateDialog


class UpdatesDialog(QDialog, Ui_UpdateDialog):

    def __init__(self, parent, version, release_notes, url):
        super().__init__(parent)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self._url = url
        self._version = version

        self.setupUi(self)

        self.lblNewversion.setText(f"<b>{QCoreApplication.applicationName()} {version}</b> is now available.")
        if release_notes:
            self.lblReleaseNotesText.setText(release_notes)
        else:
            self.lblReleaseNotes.setVisible(False)
            self.lblReleaseNotesText.setVisible(False)
        self.lblCurrentVersion.setText(QCoreApplication.applicationVersion())
        self.lblNewVersion.setText(version)

        self.buttonBox.setStandardButtons(QDialogButtonBox.NoButton)
        self.btDownload = self.buttonBox.addButton("Download Now", QDialogButtonBox.AcceptRole) if self._url else None
        self.btIgnoreUpdate = self.buttonBox.addButton("Ignore This Update", QDialogButtonBox.AcceptRole)
        self.btRemindMeLater = self.buttonBox.addButton("Remind Me Later", QDialogButtonBox.AcceptRole)
        self.btRemindMeLater.setDefault(True)
        self.buttonBox.clicked.connect(self.handle_button_click)

    def handle_button_click(self, button):
        if button == self.btDownload:
            webbrowser.open(self._url)
        elif button == self.btIgnoreUpdate:
            QSettings().setValue('Updates/ignore', self._version)
        elif button == self.btRemindMeLater:
            QSettings().setValue('Updates/ignore', None)
