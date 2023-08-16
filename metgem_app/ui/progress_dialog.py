from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

# TODO: Qt6 has no equivalent for QWinTaskbarProgress
# try:
#     # noinspection PyUnresolvedReferences
#     from PySide6.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
#     HAS_WINEXTRAS = True
# except ImportError:
#     HAS_WINEXTRAS = False

from .progress_dialog_ui import Ui_Dialog


class ProgressDialog(QDialog, Ui_Dialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        # if HAS_WINEXTRAS:
        #     self._button = QWinTaskbarButton(self)
        #     self._button.setWindow(self.windowHandle())
        #     self._button.setOverlayIcon(self.windowIcon())

    def value(self):
        return self.progressBar.value()

    def setValue(self, value):
        val = min(value, self.progressBar.maximum())
        self.progressBar.setValue(val)
        # if HAS_WINEXTRAS:
        #     self._button.progress().setValue(val)

    def format(self):
        return self.windowTitle()

    def setFormat(self, value):
        self.setWindowTitle(value)

    def minimum(self):
        return self.progressBar.minimum()

    def setMinimum(self, minimum):
        self.progressBar.setMinimum(minimum)
        # if HAS_WINEXTRAS:
        #     self._button.progress().setMinimum(minimum)

    def maximum(self):
        return self.progressBar.maximum()

    def setMaximum(self, maximum):
        self.progressBar.setMaximum(maximum)
        # if HAS_WINEXTRAS:
        #     self._button.progress().setMaximum(maximum)

    def setRange(self, minimum, maximum):
        self.progressBar.setRange(minimum, maximum)
        # if HAS_WINEXTRAS:
        #     self._button.progress().setRange(minimum, maximum)

    # def show(self):
    #     super().show()
        # if HAS_WINEXTRAS:
        #     self._button.progress().show()
