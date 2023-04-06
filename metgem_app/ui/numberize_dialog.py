from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from ..workers.options import NumberizeOptions
from .numberize_dialog_ui import Ui_Dialog


class NumberizeDialog(QDialog, Ui_Dialog):

    def __init__(self, *args, views, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        for key, name in views.items():
            self.cbView.addItem(name, key)

    def getValues(self):
        options = NumberizeOptions()
        options.column_name = self.btColumnName.text()

        return self.cbView.currentData(), options
