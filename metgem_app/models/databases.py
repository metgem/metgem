from typing import Any

from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, QAbstractTableModel

from metgem_app.database import Bank, Spectrum, Base


class BanksModel(QAbstractListModel):
    BankIdRole = Qt.UserRole + 1

    def __init__(self, session):
        super().__init__()

        self.session = session
        self._data = []

        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self._data = sorted([(b.name, b.id) for b in self.session.query(Bank.name, Bank.id)])
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        if row > self.rowCount():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._data[row][0]
        elif role == BanksModel.BankIdRole:
            return self._data[row][1]


class SpectraModel(QAbstractTableModel):
    ObjectRole = Qt.UserRole + 1

    BATCH_SIZE = 200

    def __init__(self, session, bank):
        columns = [col for col in Spectrum.__table__.columns]
        self._columns = {index: col for index, col in enumerate(columns)}
        self._rcolumns = {col.key: index for index, col in enumerate(columns)}

        super().__init__()

        self.session = session
        self._data = []
        self._bank_id = bank
        self._offset = 0
        self._max_results = 0

        self.query_db()

    def query_db(self):
        query = self.session.query(Spectrum).filter(Spectrum.bank_id == self._bank_id)
        self._max_results = query.count()
        self._data.extend([spec for spec in query.limit(self.BATCH_SIZE).offset(self._offset)])
        self._offset += self.BATCH_SIZE

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._max_results

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if (orientation == Qt.Horizontal and section > self.columnCount()) \
                or (orientation == Qt.Vertical and section > self.rowCount()):
            return None

        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            col = self._columns[section]
            return col.comment if col.comment is not None else col.name.split('_id')[0]
        else:
            return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        if row > self.rowCount() or column > self.columnCount():
            return None

        if row >= self._offset:
            self.query_db()

        try:
            obj = self._data[row]
        except IndexError:
            return None

        if role == SpectraModel.ObjectRole:
            return obj
        elif role in (Qt.DisplayRole, Qt.EditRole):
            attr = self._columns[column].name.split('_id')[0]
            attr = 'polarity' if attr == 'positive' else attr
            value = getattr(obj, attr, None)
            if isinstance(value, Base):
                value = getattr(value, 'name', None)
            return value

    def bank(self):
        return self._bank_id

    def set_bank(self, bank_id):
        self.beginResetModel()
        self._bank_id = bank_id
        self._data = []
        self._offset = 0
        self.query_db()
        self.endResetModel()

    def column_index(self, column):
        return self._rcolumns[column.key]
