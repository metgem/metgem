import os
from keyword import iskeyword
from typing import Tuple, List

import yaml
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QMessageBox, QStyledItemDelegate, QMenu, QTableWidget, \
    QTableView

UI_FILE = os.path.join(os.path.dirname(__file__), 'add_columns_by_formulae.ui')

AddColumnsByFormulaeDialogUI, AddColumnsByFormulaeDialogBase = uic.loadUiType(UI_FILE,
                                                                              from_imports='metgem_app.ui',
                                                                              import_from='metgem_app.ui')


# noinspection PyShadowingBuiltins
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


# noinspection PyShadowingBuiltins
class ColumnNameValidator(QValidator):

    def __init__(self, columns=List[str], *args, **kwargs):
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


class AddColumnsByFormulaeDialog(AddColumnsByFormulaeDialogUI, AddColumnsByFormulaeDialogBase):
    COLUMN_TITLE = 0
    COLUMN_ALIAS = 1

    COLUMN_NAME = 0
    COLUMN_FORMULA = 1

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

        # Allow re-ordering of rows in mappings table
        self.tblMappings.verticalHeader().setSectionsMovable(True)
        self.tblMappings.verticalHeader().setDragEnabled(True)
        self.tblMappings.verticalHeader().setDragDropMode(QTableView.InternalMove)

        validator = AliasValidator()
        for i in range(model.columnCount()):
            title = model.headerData(i, Qt.Horizontal)
            item = QTableWidgetItem(title)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.tblAlias.setItem(i, AddColumnsByFormulaeDialog.COLUMN_TITLE, item)
            if validator.validate(title, 0)[0] == QValidator.Acceptable:
                item = QTableWidgetItem(title)
                self.tblAlias.setItem(i, AddColumnsByFormulaeDialog.COLUMN_ALIAS, item)

        menu = QMenu()
        menu.addSection("Power and logarithmic functions")
        for func in sorted(['exp', 'expm1', 'log', 'log10', 'log1p', 'log2', 'sqrt']):
            action = menu.addAction(func)
            action.setData(func + '()')
            action.triggered.connect(self.add_text_to_mappings_editor)
        menu.addSection("Trigonometric functions")
        for func in sorted(['sin', 'cos', 'arcsin', 'arccos', 'arctan', 'arctan2']):
            action = menu.addAction(func)
            action.setData(func + '()')
            action.triggered.connect(self.add_text_to_mappings_editor)
        self.btAddFunction.setMenu(menu)
        menu.addSection("Hyperbolic functions")
        for func in sorted(['sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', 'arctanh']):
            action = menu.addAction(func)
            action.setData(func + '()')
            action.triggered.connect(self.add_text_to_mappings_editor)
        menu.addSection("Statistical Functions")
        for func in sorted(['mean', 'median', 'std', 'var', 'quantile', 'min', 'max']):
            action = menu.addAction(func)
            action.setData(func + '()')
            action.triggered.connect(self.add_text_to_mappings_editor)
        for func in sorted(['abs', 'sum', 'prod']):
            action = menu.addAction(func)
            action.setData(func + '()')
            action.triggered.connect(self.add_text_to_mappings_editor)
        self.btAddFunction.setMenu(menu)

        menu = QMenu()
        for text, const in sorted([('Pi', 'pi'), ('e Euler’s number', 'e')]):
            action = menu.addAction(const)
            action.setData(const)
            action.triggered.connect(self.add_text_to_mappings_editor)
        self.btAddConstant.setMenu(menu)

        menu = QMenu()
        menu.addSection("Arithmetic Operators")
        for text, operator in [('+ Addition', '+'), ('- Subtraction', '-'), ('* Multiplication', '*'),
                               ('/ Division', '/'), ('% Modulus', '%'), ('** Exponent', '**'),
                               ('// Floor Division', '//')]:
            action = menu.addAction(text)
            action.setData(operator)
            action.triggered.connect(self.add_text_to_mappings_editor)
        menu.addSection("Comparison Operators")
        for text, operator in [('== Equal', '=='), ('!= Different', '!='), ('> Greater', '>'), ('< Lower', '<'),
                               ('Greater or Equal', '>='), ('Lower of Equal', '<=')]:
            action = menu.addAction(text)
            action.setData(operator)
            action.triggered.connect(self.add_text_to_mappings_editor)
        menu.addSection("Logical Operators")
        for text, operator in [('and Logical AND', 'and'), ('OR Logical OR', 'or'), ('not Logical NOT', 'not')]:
            action = menu.addAction(text)
            action.setData(operator)
            action.triggered.connect(self.add_text_to_mappings_editor)
        menu.addSection("Bitwise Operators")
        for text, operator in [('&& Binary AND', '&'), ('| Binary OR', '|'), ('^ Binary XOR', '^'),
                               ('~ Binary Ones Complement', '~'), ('<< Binary Left Shift', '<<'),
                               ('>> Binary Right Shift', '>>')]:
            action = menu.addAction(text)
            action.setData(operator)
            action.triggered.connect(self.add_text_to_mappings_editor)

        self.btAddOperator.setMenu(menu)

        self.btLoadMappings.clicked.connect(self.on_load_mappings)
        self.btSaveMappings.clicked.connect(self.on_save_mappings)
        self.btAddMapping.clicked.connect(self.on_add_mapping)
        self.btRemoveMappings.clicked.connect(self.on_remove_mappings)

    def on_remove_mappings(self):
        for item in self.tblMappings.selectedItems():
            self.tblMappings.removeRow(item.row())

    def on_add_mapping(self):
        self.tblMappings.setRowCount(self.tblMappings.rowCount() + 1)

    def on_load_mappings(self):
        filter_ = ["Group mappings files (*.yaml)", "All files (*)"]
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
                    item = self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_TITLE)
                    if item:
                        for name, title in alias.items():
                            if title == item.data(Qt.DisplayRole):
                                alias_item = QTableWidgetItem(name)
                                self.tblAlias.setItem(i, AddColumnsByFormulaeDialog.COLUMN_ALIAS, alias_item)

                self.tblMappings.setRowCount(len(mappings))
                columns = [self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_TITLE).data(Qt.DisplayRole)
                           for i in range(self.tblAlias.rowCount())]
                self.tblMappings.setItemDelegateForColumn(0, ColumnNameDelegate(columns))
                for i, (name, formula) in enumerate(mappings.items()):
                    item = QTableWidgetItem(name)
                    self.tblMappings.setItem(i, AddColumnsByFormulaeDialog.COLUMN_NAME, item)
                    item = QTableWidgetItem(formula)
                    self.tblMappings.setItem(i, AddColumnsByFormulaeDialog.COLUMN_FORMULA, item)

    def on_save_mappings(self):
        filter_ = ["Group mappings files (*.yaml)", "All files (*)"]
        filename, filter_ = QFileDialog.getSaveFileName(self, "Load group mappings",
                                                        filter=";;".join(filter_))

        if filename:
            alias = {}
            for i in range(self.tblAlias.rowCount()):
                item = self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_TITLE)
                if not item:
                    continue
                title = item.data(Qt.DisplayRole)
                item = self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_ALIAS)
                if item:
                    name = item.data(Qt.DisplayRole)
                    alias[name] = title

            mappings = {}
            for i in range(self.tblMappings.rowCount()):
                item = self.tblMappings.item(i, AddColumnsByFormulaeDialog.COLUMN_NAME)
                if not item:
                    continue
                name = item.data(Qt.DisplayRole)
                item = self.tblMappings.item(i, AddColumnsByFormulaeDialog.COLUMN_FORMULA)
                if item:
                    formula = item.data(Qt.DisplayRole)
                    mappings[name] = formula

            ml = {'alias': alias}
            if mappings:
                ml['mappings'] = mappings

            try:
                with open(filename, 'w') as f:
                    yaml.dump(ml, f, sort_keys=False)
            except IOError:
                QMessageBox.warning(self, None, "Save failed (I/O Error).")

    def add_text_to_mappings_editor(self):
        if self.tblMappings.state() == QTableWidget.EditingState:
            index = self.tblMappings.currentIndex()
            if not index.isValid():
                return
            if index.column() == AddColumnsByFormulaeDialog.COLUMN_FORMULA:
                editor = self.tblMappings.indexWidget(index)
                item = self.sender()
                if item:
                    editor.insert(item.data())

    def getValues(self):
        alias = {}
        for i in range(self.tblAlias.rowCount()):
            item = self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_ALIAS)
            if item:
                name = item.data(Qt.DisplayRole)
                if name:
                    item = self.tblAlias.item(i, AddColumnsByFormulaeDialog.COLUMN_TITLE)
                    if item:
                        title = item.data(Qt.DisplayRole)
                        alias[name] = title

        mappings = {}
        for i in range(self.tblMappings.rowCount()):
            item = self.tblMappings.item(i, AddColumnsByFormulaeDialog.COLUMN_NAME)
            if item:
                name = item.data(Qt.DisplayRole)
                if name:
                    item = self.tblMappings.item(i, AddColumnsByFormulaeDialog.COLUMN_FORMULA)
                    if item:
                        formula = item.data(Qt.DisplayRole)
                        mappings[name] = formula

        return alias, mappings
