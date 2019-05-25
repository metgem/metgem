import numpy as np
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QSettings
from PyQt5.QtGui import QIcon

try:
    import os
    import pandas as pd
    with open(os.path.join(os.path.dirname(__file__), 'neutral_losses.csv'), encoding='utf-8') as f:
        NEUTRAL_LOSSES = pd.read_csv(f, sep=';', comment='#')  # Workaround for Pandas's bug #15086
except (ImportError, FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError):
    NEUTRAL_LOSSES = None

FilterRole = Qt.UserRole + 1
LabelRole = Qt.UserRole + 2
StandardsRole = Qt.UserRole + 3
AnalogsRole = Qt.UserRole + 4
DbResultsRole = Qt.UserRole + 5
ColorMarkRole = Qt.UserRole + 6


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
        self.headers_colors = {}
        self.headers_bgcolors = {}
        self.headers_fonts = {}
        self.mappings = {}

    def rowCount(self, parent=QModelIndex()):
        return self.infos.shape[0] if self.infos is not None else len(self.mzs)

    def columnCount(self, parent=QModelIndex()):
        count = len(self.mappings) + 2
        if self.infos is not None:
            count += self.infos.shape[1]
        return count

    def endResetModel(self):
        network = self.parent().network
        infos = getattr(network, 'infos', None)
        mappings = getattr(network, 'mappings', {})
        if infos is not None:
            self.infos = infos.values
            self.headers = np.array(infos.columns.tolist() + list(mappings.keys()))
        else:
            self.infos = None
            self.headers = None

        # Convert column name's mappings to index mapping
        if self.headers is not None:
            header_to_column = {h: i for i, h in enumerate(self.headers)}
            index_mappings = {}
            first_mapping_column = infos.shape[1] if infos is not None else 0
            for index, (mapname, maplist) in enumerate(mappings.items()):
                l = [value for key, value in header_to_column.items() for colname in maplist if key.startswith(colname)]
                index_mappings[first_mapping_column+index] = l
            self.mappings = index_mappings
        else:
            self.mappings = {}

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
                    results = self.db_results[row]
                except KeyError:
                    if role == Qt.DisplayRole:
                        return 'N/A'
                    else:
                        return

                try:
                    if role == Qt.DisplayRole:
                        try:
                            current = results['current']
                        except KeyError:
                            current = 0
                        return results['standards'][current].text
                    elif role == DbResultsRole:
                        return results
                    elif role == StandardsRole:
                        return results['standards']
                    elif role == AnalogsRole:
                        return results['analogs']
                    elif role == Qt.EditRole:
                        return results['current']
                    else:
                        return
                except (TypeError, KeyError, IndexError):
                    if role == Qt.EditRole:
                        return 0
                    elif role == Qt.DisplayRole and 'analogs' in results and 'standards' not in results:
                        return 'Analogs results available'
                    return 'N/A'
            else:
                try:
                    data = self.infos[row, column - 2]
                    if isinstance(data, np.generic):
                        data = data.item()
                except IndexError:
                    mappped_columns = self.mappings[column - 2]
                    data = sum(self.infos[row, c] for c in mappped_columns)
                if isinstance(data, np.generic):
                    data = data.item()
                return str(data) if role in (FilterRole, LabelRole) else data

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if role == Qt.EditRole and column == 1:
            try:
                result = self.db_results[row]
            except KeyError:
                return False

            if ('current' not in result and value != 0) or \
                    ('current' in result and result['current'] != value):
                self.db_results[row]['current'] = value
                self.dataChanged.emit(index, index)
                return True
            return super().setData(index, value, role)
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
                    text = str(self.headers[section - 2])
                    if role == Qt.ToolTipRole and section - 2 in self.mappings:
                        text += " [" + "+".join(self.headers[x] for x in self.mappings[section-2]) + "]"
                    return text
            elif orientation == Qt.Vertical:
                return str(section+1)
        elif role == ColorMarkRole:
            if orientation == Qt.Horizontal and self.headers_colors is not None and section in self.headers_colors:
                return self.headers_colors[section]
        elif role == Qt.BackgroundRole:
            if orientation == Qt.Horizontal and self.headers_bgcolors is not None and section in self.headers_bgcolors:
                return self.headers_bgcolors[section]
        elif role == Qt.FontRole:
            if orientation == Qt.Horizontal and self.headers_fonts is not None and section in self.headers_fonts:
                return self.headers_fonts[section]
        elif role == Qt.DecorationRole:
            if orientation == Qt.Horizontal:
                if section == 1:
                    return QIcon(":/icons/images/library.svg")
                elif section - 2 in self.mappings:
                    return QIcon(":/icons/images/mapping.svg")
        else:
            super().headerData(section, orientation, role)

    def setHeaderData(self, section: int, orientation: int, value, role=Qt.EditRole):
        if role == ColorMarkRole:
            self.headers_colors[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        elif role == Qt.BackgroundRole:
            self.headers_bgcolors[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        elif role == Qt.FontRole:
            self.headers_fonts[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True

        return super().setHeaderData(section, orientation, value, role)

    def flags(self, index: QModelIndex):
        return super().flags(index) | Qt.ItemIsEditable


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
            return len(data[0]) + 1
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
            else:
                data = self.interactions[row][column]
                if column == 0 or column == 1:
                    data += 1
                if role in (FilterRole, LabelRole):
                    return str(data)
                else:
                    return data

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            if section == self.columnCount() - 1:
                return 'Possible interpretation'
            return self.interactions.dtype.names[section]
        elif orientation == Qt.Vertical:
            return str(section+1)
