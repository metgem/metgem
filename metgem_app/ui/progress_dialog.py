import os

from PyQt5 import uic
from PyQt5.QtCore import Qt

try:
    # noinspection PyUnresolvedReferences
    from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
    HAS_WINEXTRAS = True
except ImportError:
    HAS_WINEXTRAS = False

UI_FILE = os.path.join(os.path.dirname(__file__), 'progress_dialog.ui')

ProgressDialogUI, ProgressDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='metgem_app.ui',
                                                      import_from='metgem_app.ui')


class ProgressDialog(ProgressDialogUI, ProgressDialogBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        if HAS_WINEXTRAS:
            self._button = QWinTaskbarButton(self)
            self._button.setWindow(self.windowHandle())
            self._button.setOverlayIcon(self.icon())

    def value(self):
        return self.progressBar.value()

    def setValue(self, value):
        self.progressBar.setValue(value)
        if HAS_WINEXTRAS:
            self._button.progress().setValue(value)

    def format(self):
        return self.windowTitle()

    def setFormat(self, value):
        self.setWindowTitle(value)

    def minimum(self):
        return self.progressBar.minimum()

    def setMinimum(self, minimum):
        self.progressBar.setMinimum(minimum)
        if HAS_WINEXTRAS:
            self._button.progress().setMinimum(minimum)

    def maximum(self):
        return self.progressBar.maximum()

    def setMaximum(self, maximum):
        self.progressBar.setMaximum(maximum)
        if HAS_WINEXTRAS:
            self._button.progress().setMaximum(maximum)

    def setRange(self, minimum, maximum):
        self.progresBar.setRange(minimum, maximum)
        if HAS_WINEXTRAS:
            self._button.progress().setRange(minimum, maximum)

    def reject(self):
        return super().reject()

    def done(self, r: int):
        return super().done(r)

    def show(self):
        super().show()
        if HAS_WINEXTRAS:
            self._button.progress().show()
