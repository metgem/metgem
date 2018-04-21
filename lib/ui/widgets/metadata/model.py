import numpy as np
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QSettings

try:
    import os
    import pandas as pd
    NEUTRAL_LOSSES = pd.read_csv(os.path.join(os.path.dirname(__file__), 'neutral_losses.csv'), sep=';', comment='#')
except (ImportError, FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError):
    NEUTRAL_LOSSES = None

FilterRole = Qt.UserRole + 1
LabelRole = Qt.UserRole + 2


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFilterRole(FilterRole)
        self._selection = None

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        l = left.data()
        r = right.data()

        if type(l).__module__ == type(r).__module__ == 'numpy':
            return l.item() < r.item()
        return super().lessThan(left, right)

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
    """Model based on a pandas DataFrame"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = None
        self.list = []
        self.headers = None
        self.headers_colors = None

    def rowCount(self, parent=QModelIndex()):
        return self.table.shape[0] if self.table is not None else len(self.list)

    def columnCount(self, parent=QModelIndex()):
        return self.table.shape[1] + 1 if self.table is not None else 1

    def endResetModel(self):
        table = getattr(self.parent().network, 'infos', None)
        if table is not None:
            self.table = table.values
            self.headers = np.array(table.columns)
        else:
            self.table = None
            self.headers = None
        self.headers_colors = [None] * self.columnCount()
        self.list = getattr(self.parent().network, 'spectra', [])
        super().endResetModel()

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole, FilterRole, LabelRole):
            if column == 0:
                try:
                    return self.list[row].mz_parent
                except IndexError:
                    return
            elif role in (FilterRole, LabelRole):
                return str(self.table[row, column - 1])
            else:
                return self.table[row, column - 1]

    def headerData(self, section: int, orientation: int, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "m/z parent"
                elif self.headers is not None:
                    return self.headers[section-1]
            elif orientation == Qt.Vertical:
                return str(section+1)
        elif role == Qt.BackgroundColorRole:
            if orientation == Qt.Horizontal and self.headers_colors is not None and section < len(self.headers_colors):
                return self.headers_colors[section]
        else:
            super().headerData(section, orientation, role)

    def setHeaderData(self, section: int, orientation: int, value, role=Qt.EditRole):
        if role == Qt.BackgroundColorRole:
            if self.headers_colors is not None:
                self.headers_colors[section] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
        else:
            super().setHeaderData(section, orientation, value, role)


class EdgesModel(QAbstractTableModel):
    """Model based on a numpy record array"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = None

        self.settings = QSettings()

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

    def endResetModel(self):
        self.table = getattr(self.parent().network, 'interactions', None)
        super().endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        column = index.column()
        row = index.row()
        if role in (Qt.DisplayRole, Qt.EditRole, FilterRole, LabelRole):
            if column == self.columnCount()-1:
                if role in (FilterRole, LabelRole):
                    return
                d_exp = abs(self.table[row]['Delta MZ'])
                interpretations = []
                if NEUTRAL_LOSSES is not None:
                    for _, r in NEUTRAL_LOSSES.iterrows():
                        d_th = r['Mass difference']
                        if abs((d_exp - d_th) / d_th) * 10**6 < self.settings.value('Metadata/neutral_tolerance', 50):
                            interpretations.append(r['Origin'])
                    return ' ; '.join(interpretations)
                else:
                    return
            elif role in (FilterRole, LabelRole):
                return str(self.table[row][column])
            else:
                return self.table[row][column]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            if section == self.columnCount()-1:
                return 'Possible interpretation'
            return self.table.dtype.names[section]
        elif orientation == Qt.Vertical:
            return str(section+1)
