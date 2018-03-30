from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel


class GraphTableModel(QAbstractTableModel):
    NodesModelType = 0
    EdgesModelType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attributes = None

    def rowCount(self, parent=QModelIndex()):
        if self._type == GraphTableModel.EdgesModelType:
            return self.parent().graph.ecount()
        else:
            return self.parent().graph.vcount()

    def columnCount(self, parent=QModelIndex()):
        return len(self.attributes)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        column = index.column()
        row = index.row()
        if column > self.columnCount() or row > self.rowCount():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            if self._type == GraphTableModel.EdgesModelType:
                return self.parent().graph.es[self.attributes[column]][row]
            else:
                return self.parent().graph.vs[self.attributes[column]][row]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.attributes[section]
        else:
            return super().headerData(section, orientation, role)

    def endResetModel(self):
        self._attributes = None
        super().endResetModel()

    @property
    def attributes(self):
        if self._attributes is None:
            if self._type == GraphTableModel.EdgesModelType:
                self._attributes = [x for x in self.parent().graph.es.attributes() if not x.startswith('__')]
            else:
                self._attributes = [x for x in self.parent().graph.vs.attributes() if not x.startswith('__')]
        return self._attributes


class NodesModel(GraphTableModel):
    _type = GraphTableModel.NodesModelType


class EdgesModel(GraphTableModel):
    _type = GraphTableModel.EdgesModelType


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        # self._filter = None
        self._selection = None

    def filterAcceptsRow(self, source_row, source_parent):
        if self._selection is not None:
            index = self.sourceModel().index(source_row, 0)
            # idx = self.sourceModel().data(index, IndexRole)
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