from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel


class NodesModel(QAbstractTableModel):

    def rowCount(self, parent=QModelIndex()):
        data = self.table
        return data.size if data is not None else len(getattr(self.parent().network, 'spectra', []))

    def columnCount(self, parent=QModelIndex()):
        data = self.table
        return len(data[0]) + 1 if data is not None else 1

    @property
    def table(self):
        return getattr(self.parent().network, 'infos', None)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        column = index.column()
        row = index.row()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == 0:
                spectra = getattr(self.parent().network, 'spectra', None)
                if spectra is not None:
                    return spectra[row].mz_parent
            else:
                return self.table[row][column - 1].item()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "m/z parent"
            else:
                return self.table.dtype.names[section-1]
        else:
            return super().headerData(section, orientation, role)


class EdgesModel(QAbstractTableModel):

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
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.table[row][column].item()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.table.dtype.names[section]
        else:
            return super().headerData(section, orientation, role)


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

    def setSelection(self, idx):
        """Display only selected items from the scene"""

        if len(idx) == 0:
            self._selection = None
        else:
            self._selection = idx
        self.invalidateFilter()
