import numpy as np
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel

try:
    import os
    import pandas as pd
    NEUTRAL_LOSSES = pd.read_csv(os.path.join(os.path.dirname(__file__), 'neutral_losses.csv'), sep=';', comment='#')
except (ImportError, FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError):
    NEUTRAL_LOSSES = None


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selection = None

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if self._selection is not None:
            if source_row in self._selection:
                return True
            return False

        return super().filterAcceptsRow(source_row, source_parent)

    def setSelection(self, idx):
        """Display only selected items from the scene"""
        if len(idx) == 0:
            self._selection = None
        else:
            self._selection = idx
        self.invalidateFilter()


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

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
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
            return str(section+1)


class NodesProxyModel(ProxyModel):

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        return left.row() < right.row()

    def sort(self, column_id, order=Qt.AscendingOrder):
        model = self.sourceModel()
        if column_id == 0:
            l = model.list
            indexes = sorted(range(len(l)), key=lambda k: l[k].mz_parent, reverse=bool(order))
            model.table = model.table.reindex(indexes, copy=False)
        elif column_id == -1:
            model.table.sort_index(ascending=not bool(order), inplace=True)
        else:
            column = model.table.columns[column_id - 1]
            model.table.sort_values(column, ascending=not bool(order), inplace=True)
        super().sort(column_id, order)


class EdgesModel(QAbstractTableModel):
    """Model with sort functionality based on a numpy record array"""

    def rowCount(self, parent=QModelIndex()):
        data = self.table
        return data.size if data is not None else 0

    def columnCount(self, parent=QModelIndex()):
        data = self.table
        if data is not None:
            if NEUTRAL_LOSSES is not None:
                return len(data[0]) + 1
            else:
                return len(data[0])
        else:
            return 0

    @property
    def table(self):
        return getattr(self.parent().network, 'interactions', None)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        column = index.column()
        row = index.row()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == self.columnCount()-1:
                d_exp = self.table[row]['Delta MZ']
                interpretations = []
                if NEUTRAL_LOSSES is not None:
                    for _, r in NEUTRAL_LOSSES.iterrows():
                        d_th = r['Mass difference']
                        if abs((d_exp - d_th) / d_th) * 10**6 < 200:  # 200 ppm
                            interpretations.append(r['Origin'])
                    return ','.join(interpretations)
                else:
                    return None
            return str(self.table[row][column])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == self.columnCount()-1:
                return 'Possible interpretation'
            return self.table.dtype.names[section]
        elif orientation == Qt.Vertical:
            return str(section+1)


class EdgesProxyModel(ProxyModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sort = None

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        if self._sort is not None:
            return self._sort[left.row()] < self._sort[right.row()]
        return super().lessThan(left, right)

    def index(self, row: int, column: int, parent:QModelIndex=QModelIndex()):
        index = super().index(row, column, parent)
        if self._sort is not None:
            index = index.sibling(self._row[row], column)
        return index

    def sort(self, column_id, order=Qt.AscendingOrder):
        model = self.sourceModel()
        if column_id == -1:
            model._sort = None
        elif column_id == model.columnCount()-1:
            return
        else:
            column = model.table.dtype.names[column_id]
            model._sort = np.argsort(model.table, order=column)
            if order == Qt.DescendingOrder:
                model._sort = model._sort[::-1]
        super().sort(column_id, order)
