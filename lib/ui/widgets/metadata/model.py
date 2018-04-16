import numpy as np
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel


class NodesModel(QAbstractTableModel):
    """Model with sort functionality based on a pandas DataFrame"""

    def rowCount(self, parent=QModelIndex()):
        data = self.table
        return len(data.index) if data is not None else len(self.list)

    def columnCount(self, parent=QModelIndex()):
        data = self.table
        return len(data.columns) + 1 if data is not None else 1

    @property
    def table(self):
        return getattr(self.parent().network, 'infos', None)

    @table.setter
    def table(self, value):
        self.parent().network.infos = value

    @property
    def list(self):
        return getattr(self.parent().network, 'spectra', [])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        table = self.table
        row = index.row()
        if table is not None:
            row = self.table.index[row]
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == 0:
                try:
                    return self.list[row].mz_parent
                except IndexError:
                    return
            else:
                return str(self.table.loc[row][column - 1])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "m/z parent"
            else:
                return self.table.columns[section-1]
        elif orientation == Qt.Vertical:
            table = self.table
            if table is not None:
                return str(self.table.index[section])
            else:
                return section

    def sort(self, column_id, order=Qt.AscendingOrder):
        self.beginResetModel()
        if column_id == 0:
            l = self.list
            indexes = sorted(range(len(l)), key=lambda k: l[k].mz_parent, reverse=bool(order))
            self.table = self.table.reindex(indexes, copy=False)
        elif column_id == -1:
            self.table.sort_index(ascending=not bool(order), inplace=True)
        else:
            column = self.table.columns[column_id - 1]
            self.table.sort_values(column, ascending=not bool(order), inplace=True)
        self.endResetModel()


class EdgesModel(QAbstractTableModel):
    """Model with sort functionality based on a numpy record array"""

    def __init__(self, parent):
        super().__init__(parent)
        self._sort = None

    def rowCount(self, parent=QModelIndex()):
        data = self.table
        return data.size if data is not None else 0

    def columnCount(self, parent=QModelIndex()):
        data = self.table
        return len(data[0]) if data is not None else 0

    @property
    def table(self):
        return getattr(self.parent().network, 'interactions', None)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        column = index.column()
        row = index.row()
        if self._sort is not None:
            row = self._sort[row]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return str(self.table[row][column])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.table.dtype.names[section]
        elif orientation == Qt.Vertical:
            if self._sort is not None:
                return str(self._sort[section]+1)
            else:
                return str(section+1)

    def sort(self, column_id, order=Qt.AscendingOrder):
        self.beginResetModel()
        if column_id == -1:
            self._sort = None
        else:
            column = self.table.dtype.names[column_id]
            self._sort = np.argsort(self.table, order=column)
            if order == Qt.DescendingOrder:
                self._sort = self._sort[::-1]
        self.endResetModel()


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selection = None

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if self._selection is not None:
            index = self.sourceModel().index(source_row, 0)
            if index.row() in self._selection:
                return True
            return False

        return super().filterAcceptsRow(source_row, source_parent)

    def sort(self, column_id, order=Qt.AscendingOrder):
        self.sourceModel().sort(column_id, order)

    def setSelection(self, idx):
        """Display only selected items from the scene"""

        if len(idx) == 0:
            self._selection = None
        else:
            self._selection = idx
        self.invalidateFilter()
