from typing import List, Union

import numpy as np
import pandas as pd
from PySide6.QtCore import (QStringListModel, QModelIndex, Qt, QSortFilterProxyModel, QAbstractTableModel, QSettings,
                         QAbstractItemModel)
from PySide6.QtGui import QIcon

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
LabelRole = Qt.UserRole + 1
StandardsRole = Qt.UserRole + 2
AnalogsRole = Qt.UserRole + 3
DbResultsRole = Qt.UserRole + 4
ColorMarkRole = Qt.UserRole + 5
ColumnDataRole = Qt.UserRole + 6


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


class NodesSortProxyModel(QSortFilterProxyModel):

    def __init__(self, parent: QModelIndex = None):
        super().__init__(parent)
        self._index = pd.Index([])

    def setSourceModel(self, source_model: QAbstractItemModel) -> None:
        super().setSourceModel(source_model)
        self._index = source_model.mzs.index

    def mapToSource(self, proxy_index: QModelIndex) -> QModelIndex:
        if self._index.size > 0 and proxy_index.isValid():
            return self.sourceModel().index(self._index[proxy_index.row()], proxy_index.column())
        return super().mapToSource(proxy_index)

    def mapFromSource(self, source_index: QModelIndex) -> QModelIndex:
        if self._index.size > 0 and source_index.isValid():
            return self.index(self._index.get_loc(source_index.row()), source_index.column())
        return super().mapFromSource(source_index)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()

        source = self.sourceModel()
        if column == -1:  # Reset sorting
            self._index = pd.Index([])
        elif column == NodesModel.MZCol:
            df = source.mzs.copy()
            df.index = pd.RangeIndex(0, df.shape[0])
            df = df.sort_values(ascending=(order == Qt.AscendingOrder))
            self._index = df.index
        elif column == NodesModel.DBResultsCol:
            db_results = self.sourceModel().db_results
            df = pd.DataFrame.from_dict({x: db_results.get(x, {})
                                        .get('standards', db_results.get(x, {}).get('analogs', ['N/A']))
                                        [db_results.get(x, {}).get('current', 0)]
                                        for x in range(self.sourceModel().infos.shape[0])}).transpose()
            df = df.sort_values(df.columns[-1], ascending=(order == Qt.AscendingOrder))
            self._index = df.index
        elif column >= self.sourceModel().infos.shape[1] + 2:  # Column Mappings
            if source.infos is not None and source.mappings:
                mapped_columns = [c-2 for c in source.mappings[column]]
                df = source.infos[source.infos.columns[mapped_columns]]
                s = df.sum(axis=1)
                s.index = pd.RangeIndex(0, s.shape[0])
                s = s.sort_values(ascending=(order == Qt.AscendingOrder))
                self._index = s.index
        else:
            if source.infos is not None:
                col = source.infos.columns[column-2]
                df = source.infos[col].copy()
                df.index = pd.RangeIndex(0, df.shape[0])
                df = df.sort_values(ascending=(order == Qt.AscendingOrder))
                self._index = df.index

        self.layoutChanged.emit()


class EdgesSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QModelIndex = None):
        super().__init__(parent)
        self._index = pd.Index([])

    def setSourceModel(self, source_model: QAbstractItemModel) -> None:
        super().setSourceModel(source_model)
        self._index = source_model.interactions.index

    def mapToSource(self, proxy_index: QModelIndex) -> QModelIndex:
        if self._index.size > 0 and proxy_index.isValid():
            return self.sourceModel().index(self._index[proxy_index.row()], proxy_index.column())
        return super().mapToSource(proxy_index)

    def mapFromSource(self, source_index: QModelIndex) -> QModelIndex:
        if self._index.size > 0 and source_index.isValid():
            return self.index(self._index.get_loc(source_index.row()), source_index.column())
        return super().mapFromSource(source_index)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        # The last column is virtual so we don't want to sort on this column
        if column == self.columnCount() - 1:
            return

        self.layoutAboutToBeChanged.emit()
        if column == -1:  # Reset sorting
            self._index = pd.Index([])
        else:
            source = self.sourceModel()
            col = source.interactions.columns[column]
            data = source.interactions[col]
            if col == 'Delta MZ':
                data = data.abs()
            idx = data.argsort()[::1 if order == Qt.AscendingOrder else -1]
            self._index = pd.Index(idx)
        self.layoutChanged.emit()


class SelectionProxyModel(QSortFilterProxyModel):
    _selection = None

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if self._selection is not None:
            index = super().sourceModel().index(source_row, 0, source_parent)
            index = super().sourceModel().mapToSource(index)
            if index.isValid() and index.row() in self._selection:
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


class FilterProxyModel(SelectionProxyModel):
    _sort_proxy = QSortFilterProxyModel()

    def setSourceModel(self, source_model: QAbstractItemModel) -> None:
        self._sort_proxy.setSourceModel(source_model)
        super().setSourceModel(self._sort_proxy)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self._sort_proxy.sort(column, order)

    def sortColumn(self):
        return self._sort_proxy.sortColumn()

    def sortOrder(self):
        return self._sort_proxy.sortOrder()

    def sortCaseSensitivity(self):
        return self._sort_proxy.sortCaseSensitivity()

    def sortRole(self):
        return self._sort_proxy.sortRole()

    def setSortRole(self, role):
        self._sort_proxy.setSortRole(role)

    def setSortCaseSensitivity(self, cs):
        self._sort_proxy.setSortCaseSensitivity(cs)

    def setSortLocaleAware(self, on):
        self._sort_proxy.setSortLocaleAware(on)

    def setDynamicSortFilter(self, enable):
        self._sort_proxy.setDynamicSortFilter(enable)

    def mapSelectionToSource(self, proxy_selection):
        return super().sourceModel().mapSelectionToSource(super().mapSelectionToSource(proxy_selection))

    def mapSelectionFromSource(self, source_selection):
        return super().mapSelectionFromSource(super().sourceModel().mapSelectionToSource(source_selection))


class NodesSortFilterProxyModel(FilterProxyModel):
    _sort_proxy = NodesSortProxyModel()


class EdgesSortFilterProxyModel(FilterProxyModel):
    _sort_proxy = EdgesSortProxyModel()


class NodesModel(QAbstractTableModel):
    """Model based on a pandas DataFrame"""

    MZCol = 0
    DBResultsCol = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.infos = None
        self.mzs = pd.Series(dtype='float64')
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

        self.mzs = getattr(network, 'mzs', pd.Series(dtype='float64'))
        self.db_results = getattr(network, 'db_results', None)

        super().endResetModel()

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole, LabelRole, StandardsRole, AnalogsRole, DbResultsRole):
            if column == NodesModel.MZCol:
                try:
                    return str(round(self.mzs.iloc[row], QSettings().value('Metadata/float_precision', 4, type=int)))
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
                    data = self.infos.loc[self.mzs.index[row]].iloc[column - 2]
                except IndexError:
                    try:
                        mappped_columns = self.mappings[column]
                        data = sum(self.infos.loc[self.mzs.index[row]].iloc[c-2] for c in mappped_columns)
                    except (IndexError, KeyError):
                        return None
                except KeyError:
                    return None

                if isinstance(data, np.generic):
                    data = data.item()
                if isinstance(data, float):
                    data = round(data, QSettings().value('Metadata/float_precision', 4, type=int))
                return str(data) if role == LabelRole else data

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

    def headerKeysToIndices(self, keys: List[Union[str, int]]) -> int:
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
                return str(self.mzs.index[section])
        elif role == KeyRole:
            return self.headers[section]
        elif role == ColumnDataRole:
            if section == NodesModel.MZCol:
                return self.mzs
            elif section == NodesModel.DBResultsCol:
                return
            else:
                try:
                    return self.infos.iloc[:, section - 2]
                except IndexError:
                    try:
                        mappped_columns = self.mappings[section]
                        return self.infos.iloc[:, [c-2 for c in mappped_columns]].sum(axis=1)
                    except KeyError:
                        return
                except KeyError:
                    return
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
        self.interactions = pd.DataFrame()
        self.mzs = pd.Series(dtype='float64')

        self.settings = QSettings()

    def rowCount(self, parent=QModelIndex()):
        return self.interactions.shape[0]

    def columnCount(self, parent=QModelIndex()):
        if self.interactions.size > 0:
            return self.interactions.shape[1] + 1
        else:
            return 0

    def endResetModel(self):
        widget = self.parent().current_network_widget
        self.interactions = getattr(widget, 'interactions', pd.DataFrame())

        network = self.parent().network
        self.mzs = getattr(network, 'mzs', pd.Series(dtype='float64'))

        super().endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        column = index.column()
        row = index.row()
        if role in (Qt.DisplayRole, Qt.EditRole, LabelRole, ColumnDataRole):
            if column == self.columnCount()-1:
                if role == LabelRole:
                    return
                d_exp = abs(self.interactions.iloc[row]['Delta MZ'])
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
                data = self.interactions.iloc[row, column]
                if column <= 1:  # First two columns (source and target)
                    data = self.mzs.index[data]
                if role in (Qt.DisplayRole, LabelRole):
                    return str(data)
                else:
                    return data

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            if section == self.columnCount() - 1:
                return 'Possible interpretation'
            return self.interactions.columns[section]
        elif orientation == Qt.Vertical:
            return str(self.interactions.index[section]+1)
