import os

from PyQt5.QtGui import QStandardItemModel, QIcon, QStandardItem
from PyQt5.QtWidgets import QAbstractItemView

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'view_standards_results_dialog.ui')

from ..database import SpectraLibrary, Spectrum, Base
from .widgets.delegates.quality import LibraryQualityDelegate

from sqlalchemy.orm import joinedload

ViewStandardsResultsDialogUI, ViewStandardsResultsDialogBase = uic.loadUiType(UI_FILE,
                                                                              from_imports='lib.ui',
                                                                              import_from='lib.ui')


class SpectraModel(QAbstractTableModel):
    TypeRole = Qt.UserRole + 1

    def __init__(self, base_path, selection: dict):
        columns = [col for col in Spectrum.__table__.columns]
        self._columns = {index: col for index, col in enumerate(columns)}
        self._rcolumns = {col.key: index for index, col in enumerate(columns)}

        super().__init__()

        self._data = {'standards': [], 'analogs': []}
        self.selection = selection
        self._analogs_start = len(selection['standards']) if 'standards' in selection else 0
        with SpectraLibrary(os.path.join(base_path, 'spectra')) as lib:
            for key in self._data:
                if key in selection:
                    for res in selection[key]:
                        query = lib.query(Spectrum).options(joinedload('*'))\
                            .filter(Spectrum.bank.has(name=res.bank), Spectrum.spectrumid == res.id)
                        self._data[key].append(query.first())

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data['standards']) + len(self._data['analogs'])

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._columns) + 1

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if (orientation == Qt.Horizontal and section > self.columnCount())\
                or (orientation == Qt.Vertical and section > self.rowCount()):
            return

        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return 'Score'
            col = self._columns[section-1]
            return col.comment if col.comment is not None else col.name.split('_id')[0]
        else:
            return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if row > self.rowCount() or column > self.columnCount():
            return

        if row >= self._analogs_start:
            key = 'analogs'
            row -= self._analogs_start
        else:
            key = 'standards'

        if role == SpectraModel.TypeRole:
            return key

        if column == 0:
            try:
                return f"{self.selection[key][row].score:.2f}"
            except IndexError:
                return

        try:
            obj = self._data[key][row]
        except IndexError:
            return

        if role in (Qt.DisplayRole, Qt.EditRole):
            attr = self._columns[column-1].name.split('_id')[0]
            attr = 'polarity' if attr == 'positive' else attr
            value = getattr(obj, attr, None)
            if isinstance(value, Base):
                value = getattr(value, 'name', None)
            return value

    def column_index(self, column):
        return self._rcolumns[column.key] + 1


class ViewStandardsResultsDialog(ViewStandardsResultsDialogUI, ViewStandardsResultsDialogBase):

    def __init__(self, *args, base_path=None, selection: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        model = SpectraModel(base_path, selection)

        for i in range(model.columnCount()):
            if model.headerData(i, Qt.Horizontal) == Spectrum.libraryquality.comment:
                self.tvSpectra.setItemDelegateForColumn(i, LibraryQualityDelegate())
                break

        forbidden_cols = (model.column_index(Spectrum.id),
                          model.column_index(Spectrum.bank_id),
                          model.column_index(Spectrum.peaks))
        tree_model = QStandardItemModel()
        tree_model.setColumnCount(model.columnCount()-len(forbidden_cols))
        tree_model.setHorizontalHeaderLabels([model.headerData(section) for section in range(model.columnCount())
                                              if section not in forbidden_cols])

        standards_item = QStandardItem(QIcon(":/icons/images/library-query.svg"), 'Standards')
        standards_item.setSelectable(False)
        tree_model.appendRow(standards_item)
        analogs_item = QStandardItem(QIcon(":/icons/images/library-query-analogs.svg"), 'Analogs')
        analogs_item.setSelectable(False)
        tree_model.appendRow(analogs_item)

        for row in range(model.rowCount()):
            values = []
            for column in range(model.columnCount()):
                if column in forbidden_cols:
                    continue
                index = model.index(row, column)
                values.append(QStandardItem(str(model.data(index))))
            if model.data(index, role=SpectraModel.TypeRole) == 'analogs':
                analogs_item.appendRow(values)
            else:
                standards_item.appendRow(values)

        self.tvSpectra.setModel(tree_model)
        self.widgetSpectrumDetails.setModel(model)

        # Connect events
        self.tvSpectra.selectionModel().currentChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, index):
        parent = index.parent()
        if parent.isValid():
            # Update description labels
            self.widgetSpectrumDetails.setCurrentIndex(index.row() + parent.row())

    def closeEvent(self, event):
        super().closeEvent(event)

    def showEvent(self, event):
        self.select_row(0)
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def select_row(self, row, scroll_hint: QAbstractItemView.ScrollHint = QAbstractItemView.EnsureVisible):
        return  # TODO
        if 0 <= row < self.tvSpectra.model().rowCount():
            index = self.tvSpectra.model().index(row, 0)
            self.tvSpectra.selectRow(row)
            self.tvSpectra.scrollTo(index, scroll_hint)

