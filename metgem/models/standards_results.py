import os

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from sqlalchemy.orm import joinedload

from metgem.database import Spectrum, SpectraLibrary, Base


class SpectraModel(QAbstractTableModel):
    TypeRole = Qt.UserRole + 1
    RowRole = Qt.UserRole + 2

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
                            .filter(Spectrum.id == res.id)
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