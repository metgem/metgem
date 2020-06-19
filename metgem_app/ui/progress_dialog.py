import os

from PyQt5 import uic
from PyQt5.QtCore import Qt

UI_FILE = os.path.join(os.path.dirname(__file__), 'progress_dialog.ui')

ProgressDialogUI, ProgressDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='metgem_app.ui',
                                                      import_from='metgem_app.ui')


class ProgressDialog(ProgressDialogUI, ProgressDialogBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

    def value(self):
        return self.progressBar.value()

    def setValue(self, value):
        self.progressBar.setValue(value)

    def format(self):
        return self.windowTitle()

    def setFormat(self, value):
        self.setWindowTitle(value)

    def minimum(self):
        return self.progressBar.minimum()

    def setMinimum(self, value):
        self.progressBar.setMinimum(value)

    def maximum(self):
        return self.progressBar.maximum()

    def setMaximum(self, value):
        self.progressBar.setMaximum(value)

    def reject(self):
        return super().reject()

    def done(self, r: int):
        return super().done(r)
