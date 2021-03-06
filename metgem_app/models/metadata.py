from typing import List

import numpy as np
import pandas as pd
from PyQt5.QtCore import QStringListModel, QModelIndex, Qt, QSortFilterProxyModel, QAbstractTableModel, QSettings
from PyQt5.QtGui import QIcon

try:
    import os
    import pandas as pd
    with open(os.path.join(os.path.dirname(__file__), 'neutral_losses.csv'), encoding='utf-8') as f:
        NEUTRAL_LOSSES = pd.read_csv(f, sep=';', comment='#')  # Workaround for Pandas's bug #15086
except (ImportError, FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError):
    NEUTRAL_LOSSES = None


# Each column has a unique key: it's title except for the first two columns which use an integer as key
# Because data is loaded from csv or spreadsheet, the loaded titles are always strings
# It ensure that the reserved columns can't have the same key of a loaded column
KeyRole = Qt.UserRole
FilterRole = Qt.UserRole + 1
LabelRole = Qt.UserRole + 2
StandardsRole = Qt.UserRole + 3
AnalogsRole = Qt.UserRole + 4
DbResultsRole = Qt.UserRole + 5
ColorMarkRole = Qt.UserRole + 6
ColumnDataRole = Qt.UserRole + 7


class CsvDelimiterModel(QStringListModel):
    seps = [',', ';', ' ', '\t', None]
    texts = ["Comma (,)", "Semicolon (;)", "Space", "Tabulation", "Other"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.texts)

    def data(self, index: QModelIndex, role=None):
        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.texts[index.row()]

    def itemData(self, index: QModelIndex):
        if not index.isValid():
            return None

        return self.seps[index.row()]


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFilterRole(FilterRole)
        self._selection = None

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        ldata = left.data()
        rdata = right.data()

        if type(ldata).__module__ == type(rdata).__module__ == 'numpy':
            return ldata.item() < rdata.item()
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


NodesProxyModel = ProxyModel


class EdgesProxyModel(ProxyModel):
    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        # The last column is virtual so we don't want to sort on this column
        if column == self.columnCount() - 1:
            return
        else:
            super().sort(column, order)


class NodesModel(QAbstractTableModel):
    """Model based on a pandas DataFrame"""

    MZCol = 0
    DBResultsCol = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.infos = None
        self.mzs = []
        self.db_results = None
        self.headers = pd.Index([])
        self.headers_colors = {}
        self.headers_bgcolors = {}
        self.headers_fonts = {}
        self.mappings = {}

    def rowCount(self, parent=QModelIndex()):
        return len(self.mzs)

    def columnCount(self, parent=QModelIndex()):
        return self.headers.shape[0]

    def endResetModel(self):
        network = self.parent().network
        infos = getattr(network, 'infos', None)
        mappings = getattr(network, 'mappings', {})
        if infos is not None:
            self.infos = infos
            self.headers = pd.Index(list(range(2)) + infos.columns.tolist() + list(mappings.keys()))
        else:
            self.infos = None
            self.headers = pd.Index(list(range(2)))

        # Convert column name's mappings to index mapping
        if self.headers is not None:
            header_to_column = {h: i for i, h in enumerate(self.headers)}
            index_mappings = {}
            first_mapping_column = infos.shape[1] + 2 if infos is not None else 2
            for index, (mapname, maplist) in enumerate(mappings.items()):
                l = [value for key, value in header_to_column.items()
                     for colname in maplist if str(key).startswith(colname)]
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
            if column == NodesModel.MZCol:
                try:
                    return round(self.mzs[row], QSettings().value('Metadata/float_precision', 4, type=int))
                except IndexError:
                    return
            elif column == NodesModel.DBResultsCol:
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
                    data = self.infos.loc[row, self.infos.columns[column - 2]]
                except IndexError:
                    try:
                        mappped_columns = self.mappings[column]
                        data = sum(self.infos.loc[row, self.infos.columns[c-2]] for c in mappped_columns)
                    except KeyError:
                        return None
                except KeyError:
                    return None

                if isinstance(data, np.generic):
                    data = data.item()
                if isinstance(data, float):
                    data = round(data, QSettings().value('Metadata/float_precision', 4, type=int))
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

    def headerKeysToIndices(self, keys: List[str]) -> int:
        """Return column indices from column keys"""
        return np.where(self.headers.isin(keys))[0]

    def headerData(self, section: int, orientation: int, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if orientation == Qt.Horizontal:
                if section == NodesModel.MZCol:
                    return "m/z parent"
                elif section == NodesModel.DBResultsCol:
                    return "Database search results"
                else:
                    text = str(self.headers[section])
                    if role == Qt.ToolTipRole and section in self.mappings:
                        text += " [" + "+".join(self.headers[x] for x in self.mappings[section]) + "]"
                    return text
            elif orientation == Qt.Vertical:
                return str(section+1)
        elif role == KeyRole:
            return self.headers[section]
        elif role == ColumnDataRole:
            if section == NodesModel.MZCol:
                return self.mzs
            elif section == NodesModel.DBResultsCol:
                return
            else:
                return self.infos[self.infos.columns[section - 2]]
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
                if section == NodesModel.DBResultsCol:
                    return QIcon(":/icons/images/library.svg")
                elif section in self.mappings:
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
        if data is not None and data.size > 0:
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
                        tol = self.settings.value('Metadata/neutral_tolerance', 50, type=int)
                        if abs((d_exp - d_th) / d_th) * 10**6 < tol:
                            interpretations.append(r['Origin'])
                    return ' ; '.join(interpretations)
                else:
                    return
            else:
                data = self.interactions[row][column]
                if column in (NodesModel.MZCol, NodesModel.DBResultsCol):
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
