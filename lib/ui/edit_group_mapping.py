import os
from typing import Tuple, List
from keyword import iskeyword

import yaml

from PyQt5 import uic
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QMessageBox, QStyledItemDelegate

UI_FILE = os.path.join(os.path.dirname(__file__), 'edit_group_mappings.ui')

EditGroupMappingsDialogUI, EditGroupMappingsDialogBase = uic.loadUiType(UI_FILE,
                                                                        from_imports='lib.ui',
                                                                        import_from='lib.ui')

COLUMN_TITLE = 0
COLUMN_ALIAS = 1

COLUMN_NAME = 0
COLUMN_FORMULA = 1


class AliasValidator(QValidator):

    def validate(self, input: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if input.isidentifier() or not input:
            if iskeyword(input):
                return QValidator.Intermediate, input, pos
            else:
                return QValidator.Acceptable, input, pos
        else:
            return QValidator.Invalid, input, pos


class AliasDelegate(QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        editor.setValidator(AliasValidator())
        return editor


class ColumnNameValidator(QValidator):

    def __init__(self, columns: List[str] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._columns = columns

    def validate(self, input: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if input not in self._columns or not input:
            return QValidator.Acceptable, input, pos
        else:
            return QValidator.Intermediate, input, pos


class ColumnNameDelegate(QStyledItemDelegate):

    def __init__(self, columns: List[str] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._columns = columns

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        editor.setValidator(ColumnNameValidator(self._columns))
        return editor


class EditGroupMappingsDialog(EditGroupMappingsDialogUI, EditGroupMappingsDialogBase):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.tblAlias.setColumnCount(2)
        self.tblAlias.setRowCount(model.columnCount())
        self.tblAlias.setHorizontalHeaderLabels(['Column', 'Alias'])
        self.tblAlias.setItemDelegateForColumn(1, AliasDelegate())

        self.tblMappings.setColumnCount(2)
        self.tblMappings.setHorizontalHeaderLabels(['Name', 'Formula'])

        validator = AliasValidator()
        for i in range(model.columnCount()):
            title = model.headerData(i, Qt.Horizontal)
            item = QTableWidgetItem(title)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.tblAlias.setItem(i, COLUMN_TITLE, item)
            if validator.validate(title, 0)[0] == QValidator.Acceptable:
                item = QTableWidgetItem(title)
                self.tblAlias.setItem(i, COLUMN_ALIAS, item)

        self.btLoadMappings.clicked.connect(self.on_load_mappings)
        self.btAddMapping.clicked.connect(self.on_add_mapping)
        self.btRemoveMappings.clicked.connect(self.on_remove_mappings)

    def on_remove_mappings(self):
        for item in self.tblMappings.selectedItems():
            self.tblMappings.removeRow(item.row())

    def on_add_mapping(self):
        self.tblMappings.setRowCount(self.tblMappings.rowCount() + 1)

    def on_load_mappings(self):
        filter_ = ["Group mappings files (*.yaml)", "All files (*.*)"]
        filename, filter_ = QFileDialog.getOpenFileName(self, "Load group mappings",
                                                        filter=";;".join(filter_))
        if filename:
            try:
                with open(filename, 'r') as f:
                    ml = yaml.load(f, Loader=yaml.FullLoader)
                    alias = ml['alias']
                    mappings = ml['mappings']
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Load failed (I/O Error).")
            else:
                for i in range(self.tblAlias.rowCount()):
                    item = self.tblAlias.item(i, COLUMN_TITLE)
                    if item:
                        for name, title in alias.items():
                            if title == item.data(Qt.DisplayRole):
                                alias_item = QTableWidgetItem(name)
                                self.tblAlias.setItem(i, COLUMN_ALIAS, alias_item)

                self.tblMappings.setRowCount(len(mappings))
                columns = [self.tblAlias.item(i, COLUMN_TITLE).data(Qt.DisplayRole)
                           for i in range(self.tblAlias.rowCount())]
                self.tblMappings.setItemDelegateForColumn(0, ColumnNameDelegate(columns))
                for i, (name, formula) in enumerate(mappings.items()):
                    item = QTableWidgetItem(name)
                    self.tblMappings.setItem(i, COLUMN_NAME, item)
                    item = QTableWidgetItem(formula)
                    self.tblMappings.setItem(i, COLUMN_FORMULA, item)

    def getValues(self):
        alias = {}
        for i in range(self.tblAlias.rowCount()):
            item = self.tblAlias.item(i, COLUMN_ALIAS)
            if item:
                name = item.data(Qt.DisplayRole)
                if name:
                    item = self.tblAlias.item(i, COLUMN_TITLE)
                    if item:
                        title = item.data(Qt.DisplayRole)
                        alias[name] = title

        mappings = {}
        for i in range(self.tblMappings.rowCount()):
            item = self.tblMappings.item(i, COLUMN_NAME)
            if item:
                name = item.data(Qt.DisplayRole)
                if name:
                    item = self.tblMappings.item(i, COLUMN_FORMULA)
                    if item:
                        formula = item.data(Qt.DisplayRole)
                        mappings[name] = formula

        return alias, mappings
