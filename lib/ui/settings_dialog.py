import os
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QDialog

UI_FILE = os.path.join(os.path.dirname(__file__), 'settings_dialog.ui')

SettingsDialogUI, SettingsDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='lib.ui',
                                                      import_from='lib.ui')


class SettingsDialog(SettingsDialogUI, SettingsDialogBase):

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        settings = QSettings()
        value = settings.value('Metadata/neutral_tolerance')
        if value is not None:
            self.spinNeutralTolerance.setValue(value)

    def done(self, r):
        if r == QDialog.Accepted:
            settings = QSettings()
            settings.setValue('Metadata/neutral_tolerance', self.spinNeutralTolerance.value())
        super().done(r)

    def getValues(self):
        return None
