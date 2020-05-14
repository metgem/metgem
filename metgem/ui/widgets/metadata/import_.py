from PyQt5.QtCore import QStringListModel, QModelIndex, Qt, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QLineEdit


class CsvDelimiterModel(QStringListModel):
    seps = [',', ';', ' ', '\t', None]
    texts = ["Comma (,)", "Semicolon (;)", "Space", "Tabulation", "Other"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.texts)

    def data(self, index: QModelIndex, role=None):
        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.texts[index.row()]

    def itemData(self, index: QModelIndex):
        if not index.isValid():
            return None

        return self.seps[index.row()]


class CsvDelimiterCombo(QComboBox):
    delimiterChanged = pyqtSignal(str)

    def __init__(self, *args, other_edit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setModel(CsvDelimiterModel())

        self._other_edit = other_edit
        self.currentIndexChanged.connect(self.on_current_index_changed)

    def otherEditWidget(self):
        return self._other_edit

    def setOtherEditWidget(self, widget):
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.on_other_edit_text_changed)
            self._other_edit = widget

    def delimiter(self, index=None):
        model = self.model()
        if index is None:
            index = self.currentIndex()
        delimiter = model.itemData(model.index(index))
        if delimiter is None and self._other_edit is not None:
            delimiter = self._other_edit.text()
            if len(delimiter) != 1:
                delimiter = None
        return delimiter

    def setDelimiter(self, delimiter: str):
        model = self.model()
        if delimiter in model.seps:
            self.setCurrentIndex(model.seps.index(delimiter))
            self.delimiterChanged.emit(delimiter)
        elif self._other_edit is not None:  # Other
            self.setCurrentIndex(model.seps.index(None))
            self._other_edit.setText(delimiter)
            self.delimiterChanged.emit(delimiter)

    def on_current_index_changed(self, row):
        delimiter = self.delimiter(index=row)
        if self._other_edit is not None:
            self._other_edit.setEnabled(delimiter is None)
        self.delimiterChanged.emit(delimiter)

    def on_other_edit_text_changed(self, text):
        if len(text) == 1:
            self.delimiterChanged.emit(text)
