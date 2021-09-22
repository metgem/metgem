from typing import List, Any

from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel, QIdentityProxyModel
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QHeaderView

from ....models.link_item_selection_model import LinkItemSelectionModel


# Python port of KRearrangeColumnsProxyModel from KDAB
# with modifications to allow the proxy model to present only a subset of columns from the source model
class RearrangeColumnsProxymodel(QIdentityProxyModel):

    def __init__(self, parent):
        self._source_columns = []
        super().__init__(parent)

    def columnCount(self, parent=QModelIndex()):
        if self.sourceModel() is None:
            return 0
        return len(self._source_columns)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if self.sourceModel() is None:
            return 0

        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)
        return self.sourceModel().rowCount(source_parent)

    def setSourceColumns(self, columns: List[int]):
        # We could use layoutChanged() here, but we would have to map persistent
        # indexes from the old to the new location...
        self.beginResetModel()
        self._source_columns = columns
        self.endResetModel()

    # We derive from QIdentityProxyModel simply to be able to use
    # its mapFromSource method which has friend access to createIndex() in the source model.

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        # assert row >= 0
        # assert column >= 0

        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)

        # Find the child in the source model, we need its internal pointer
        source_index = self.sourceModel().index(row, self.sourceColumnForProxyColumn(column), source_parent)
        if not source_index.isValid():
            return QModelIndex()
        return self.createIndex(row, column, source_index.internalPointer())

    def parent(self, child: QModelIndex) -> QModelIndex:
        source_index = self.mapToSource(child)
        source_parent = source_index.parent()
        if not source_parent.isValid():
            return QModelIndex()
        return self.createIndex(source_parent.row(), 0, source_parent.internalPointer())

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            source_col = self.sourceColumnForProxyColumn(section)
            return self.sourceModel().headerData(source_col, orientation, role)
        else:
            return super().headerData(section, orientation, role)

    def sibling(self, row: int, column: int, idx: QModelIndex) -> QModelIndex:
        if column >= len(self._source_columns):
            return QModelIndex()
        return self.index(row, column, idx.parent())

    def mapFromSource(self, source_index: QModelIndex) -> QModelIndex:
        if not source_index.isValid():
            return QModelIndex()

        # assert source_index.model() == self.sourceModel()

        proxy_column = self.proxyColumnForSourceColumn(source_index.column())
        if proxy_column == -1:
            return super().mapFromSource(source_index)
        index = self.createIndex(source_index.row(), proxy_column, source_index.internalPointer())

        return index

    def mapToSource(self, proxy_index: QModelIndex) -> QModelIndex:
        if not proxy_index.isValid():
            return QModelIndex()

        # This is just an indirect way to call sourceModel.createIndex(row, sourceColumn, pointer)
        fake_index = self.createIndex(proxy_index.row(), self.sourceColumnForProxyColumn(proxy_index.column()),
                                      proxy_index.internalPointer())
        return super().mapToSource(fake_index)

    def proxyColumnForSourceColumn(self, source_column: int):
        try:
            # If this is too slow, we could add a second QVector with
            # index=logical_source_column value=desired_pos_in_proxy.
            return self._source_columns.index(source_column)
        except ValueError:
            return -1

    def sourceColumnForProxyColumn(self, proxy_column: int):
        if not self._source_columns:
            return -1
        # assert proxy_column >= 0
        # assert proxy_column < len(self._source_columns)
        try:
            return self._source_columns[proxy_column]
        except IndexError:
            return -1


# https://gist.githubusercontent.com/gdementen/21a78ac56258c07dbc1072b806a5097a/raw/add074825e16086845d200509c5eaef649c237ba/frozen.py
# https://objexx.com/labs.Efficient-Qt-Frozen-Columns-and-Rows.html
# noinspection PyTypeChecker,PyUnresolvedReferences,PyCallByClass
class FreezeTableMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._frozen_table = QTableView(self)
        self._frozen_table.verticalHeader().hide()
        self._frozen_table.setFocusPolicy(Qt.NoFocus)
        self._frozen_table.setStyleSheet('''
        QTableView, QHeaderView {
            border: none;
            background-color: palette(dark);
            alternate-background-color: palette(mid);
            color: palette(base);
        }''')
        self._frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_table.horizontalHeader().setStretchLastSection(True)

        self.viewport().stackUnder(self._frozen_table)

        self._frozen_table.verticalHeader().setDefaultSectionSize(self.verticalHeader().defaultSectionSize())
        self._frozen_table.hide()

        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # connect the headers and scrollbars of both tableviews together
        self.horizontalHeader().sectionResized.connect(self.updateFrozenSectionWidth)
        self._frozen_table.horizontalHeader().sectionResized.connect(self.updateTableSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self._frozen_table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self._frozen_table.verticalScrollBar().setValue)

    def frozenTable(self):
        return self._frozen_table

    def setHorizontalHeader(self, header: QHeaderView) -> None:
        header.sectionResized.connect(self.updateFrozenSectionWidth)
        super().setHorizontalHeader(header)
        header.stackUnder(self._frozen_table)

    def setFrozenTableHorizontalHeader(self, header: QHeaderView) -> None:
        header.sectionResized.connect(self.updateTableSectionWidth)
        self._frozen_table.setHorizontalHeader(header)

    def setVerticalHeader(self, header: QHeaderView) -> None:
        header.sectionResized.connect(self.updateSectionHeight)
        self._frozen_table.verticalHeader().setDefaultSectionSize(header.defaultSectionSize())
        super().setVerticalHeader(header)

    def setModel(self, model: QAbstractItemModel) -> None:
        super().setModel(model)

        # Derive a proxy model from the model to limit number of columns
        frozen_model = RearrangeColumnsProxymodel(self)
        frozen_model.setSourceModel(self.model())
        self._frozen_table.setModel(frozen_model)

        link_selection_model = LinkItemSelectionModel(frozen_model, QAbstractItemView.selectionModel(self), self)
        self._frozen_table.setSelectionModel(link_selection_model)

    # noinspection PyUnusedLocal
    def updateFrozenSectionWidth(self, logical_index: int, old_size: int, new_size: int):
        model = self._frozen_table.model()
        if model is None:
            return

        proxy_logical_index = model.proxyColumnForSourceColumn(logical_index)
        if proxy_logical_index > 0:
            self._frozen_table.horizontalHeader().blockSignals(True)
            self._frozen_table.horizontalHeader().resizeSection(proxy_logical_index, new_size)
            self._frozen_table.horizontalHeader().blockSignals(False)
            self.updateFrozenTableGeometry()

    # noinspection PyUnusedLocal
    def updateTableSectionWidth(self, logical_index: int, old_size: int, new_size: int):
        model = self._frozen_table.model()
        if model is None:
            return

        source_logical_index = model.sourceColumnForProxyColumn(logical_index)
        if source_logical_index > 0:
            self.setColumnWidth(source_logical_index, new_size)
            self.updateFrozenTableGeometry()

    # noinspection PyUnusedLocal
    def updateSectionHeight(self, logical_index: int, old_size: int, new_size: int):
        self._frozen_table.setRowHeight(logical_index, new_size)

    def resizeEvent(self, event):
        QTableView.resizeEvent(self, event)
        self.updateFrozenTableGeometry()

    def scrollTo(self, index: QModelIndex, hint: QAbstractItemView.ScrollHint = QAbstractItemView.EnsureVisible) -> None:
        if index.column() > 1:
            QTableView.scrollTo(self, index, hint)

    def setFrozenColumns(self, num_columns=None):
        if num_columns is not None:
            model = self._frozen_table.model()
            if model is None:
                return

            mapping = [self.horizontalHeader().logicalIndex(col) for col in range(num_columns)]
            mapping = [col for col in mapping if not self.isColumnHidden(col)]
            model.setSourceColumns(mapping)

            # Synchronize section sizes between table and frozen table
            hh = self._frozen_table.horizontalHeader()
            for col in range(num_columns):
                logical_index = model.sourceColumnForProxyColumn(col)
                hh.resizeSection(col, self.columnWidth(logical_index))

            self._frozen_table.show()
            self.updateFrozenTableGeometry()
        else:
            self._frozen_table.hide()

    def updateFrozenTableGeometry(self):
        model = self._frozen_table.model()
        if model is None:
            return

        ax = ay = self.frameWidth()
        aw = sum(self.columnWidth(model.sourceColumnForProxyColumn(i))
                 for i in range(model.columnCount()))
        ah = self.viewport().height() + self.horizontalHeader().height()
        if self.verticalHeader().isVisible():
            ax += self.verticalHeader().width()
        self._frozen_table.setGeometry(ax, ay, aw, ah)

    def moveCursor(self, cursorAction, modifiers):
        current = QTableView.moveCursor(self, cursorAction, modifiers)
        x = self.visualRect(current).topLeft().x()
        frozen_width = self._frozen_table.columnWidth(0) + self._frozen_table.columnWidth(1)
        if cursorAction == self.MoveLeft and current.column() > 1 and x < frozen_width:
            new_value = self.horizontalScrollBar().value() + x - frozen_width
            self.horizontalScrollBar().setValue(new_value)
        return current


class FreezeTableView(FreezeTableMixin, QTableView):
    pass
