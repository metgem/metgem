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
StandardsRole = Qt.UserRole + 3
AnalogsRole = Qt.UserRole + 4
DbResultsRole = Qt.UserRole + 5


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
        self.infos = None
        self.mzs = []
        self.db_results = None
        self.headers = None
        self.headers_colors = None

    def rowCount(self, parent=QModelIndex()):
        return self.infos.shape[0] if self.infos is not None else len(self.mzs)

    def columnCount(self, parent=QModelIndex()):
        count = self.infos.shape[1] + 2 if self.infos is not None else 2
        return count

    def endResetModel(self):
        network = self.parent().network
        infos = getattr(network, 'infos', None)
        if infos is not None:
            self.infos = infos.values
            self.headers = np.array(infos.columns)
        else:
            self.infos = None
            self.headers = None
        self.headers_colors = [None] * self.columnCount()

        self.mzs = getattr(network, 'mzs', [])

        self.db_results = getattr(network, 'db_results', None)
        super().endResetModel()

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole, FilterRole, LabelRole, StandardsRole, AnalogsRole, DbResultsRole):
            if column == 0:
                try:
                    return self.mzs[row]
                except IndexError:
                    return
            elif column == 1:
                try:
                    if role == Qt.DisplayRole:
                        results = self.db_results[row]
                        try:
                            current = results['current']
                        except KeyError:
                            current = 0
                        return self.db_results[row]['standards'][current].text
                    elif role == DbResultsRole:
                        return self.db_results[row]
                    elif role == StandardsRole:
                        return self.db_results[row]['standards']
                    elif role == AnalogsRole:
                        return self.db_results[row]['analogs']
                    elif role == Qt.EditRole:
                        return self.db_results[row]['current']
                    else:
                        return
                except (TypeError, KeyError, IndexError):
                    if role == Qt.EditRole:
                        return 0
                    return
            else:
                if role in (FilterRole, LabelRole):
                    return str(self.infos[row, column - 2])
                else:
                    return self.infos[row, column - 2]

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if role == Qt.EditRole and column == 1:
            self.db_results[row]['current'] = value
            return True
        else:
            return super().setData(index, value, role)

    def headerData(self, section: int, orientation: int, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "m/z parent"
                elif section == 1:
                    return "Database search results"
                elif self.headers is not None:
                    return self.headers[section - 2]
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

    def flags(self, index: QModelIndex):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags


class EdgesModel(QAbstractTableModel):
    """Model based on a numpy record array"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interactions = None

        self.settings = QSettings()

    def rowCount(self, parent=QModelIndex()):
        data = self.interactions
        return data.size if data is not None else 0

    def columnCount(self, parent=QModelIndex()):
        data = self.interactions
        if data is not None:
            if NEUTRAL_LOSSES is not None:
                return len(data[0]) + 1
            else:
                return len(data[0])
        else:
            return 0

    def endResetModel(self):
        self.interactions = getattr(self.parent().network, 'interactions', None)
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
                d_exp = abs(self.interactions[row]['Delta MZ'])
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
                return str(self.interactions[row][column])
            else:
                return self.interactions[row][column]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            if section == self.columnCount()-1:
                return 'Possible interpretation'
            return self.interactions.dtype.names[section]
        elif orientation == Qt.Vertical:
            return str(section+1)
