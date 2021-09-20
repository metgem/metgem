from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QTableView, QAbstractButton, QHeaderView, QWidget, QMenu
from PyQt5.QtCore import Qt, QObject, QEvent, QRect, QTimer, QModelIndex
from PyQt5 import uic

from .freeze_table import FreezeTableMixin
from ....models.metadata import ColorMarkRole
from ..delegates import EnsureStringItemDelegate, StandardsResultsDelegate
from ....utils import SignalBlocker

import os


class HeaderView(QHeaderView):
    """QHeaderView that can have a different color background and or color mark for each section"""

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int):
        bg = self.model().headerData(logical_index, Qt.Horizontal, Qt.BackgroundColorRole)
        cm = self.model().headerData(logical_index, Qt.Horizontal, ColorMarkRole)

        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()

        if bg is not None and bg.isValid():
            bg.setAlpha(100)
            painter.fillRect(rect, bg)

        if cm is not None and cm.isValid():
            painter.fillRect(rect.adjusted(0, 0, 0, -int(7 * rect.height() / 8)), cm)


class MetadataTableView(QTableView):
    """ TableView to display metadata"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setItemDelegate(EnsureStringItemDelegate())

        # Install event filter on top left button (usually used to select all rows and columns)
        btn = self.findChild(QAbstractButton)
        if btn:
            btn.installEventFilter(self)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

    def eventFilter(self, watched: QObject, event: QEvent):
        # If top-left button is right clicked, reset model's sorting order
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.RightButton:
                self.resetSorting()
        return False

    def resetSorting(self):
        self.model().sort(-1)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)


class NodeTableView(FreezeTableMixin, MetadataTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.timers = {}

        for table in (self, self.frozenTable()):
            header = HeaderView(Qt.Horizontal, table)
            header.setHighlightSections(True)
            header.setSectionsClickable(True)
            header.setStretchLastSection(True)
            if table == self:
                self.setHorizontalHeader(header)
            else:
                self.setFrozenTableHorizontalHeader(header)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(True)
        self.frozenTable().setAlternatingRowColors(True)

        delegate = StandardsResultsDelegate()
        self.viewDetailsClicked = delegate.viewDetailsClicked
        self.setItemDelegateForColumn(1, delegate)

    def setColumnBlinking(self, section: int, blink: bool):
        if section in self.timers:
            self.timers[section].stop()
            del self.timers[section]
            self.model().setHeaderData(section, Qt.Horizontal, None, role=Qt.BackgroundColorRole)

        if blink:
            timer = self.timers[section] = QTimer()
            colored = True

            def update():
                nonlocal colored
                color = self.palette().color(QPalette.Highlight) if colored else None
                self.model().setHeaderData(section, Qt.Horizontal, color, role=Qt.BackgroundColorRole)
                colored = not colored

            timer.timeout.connect(update)
            timer.start(500)

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        self.setColumnBlinking(current.column(), False)
        return super().currentChanged(current, previous)


class EdgeTableView(MetadataTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.horizontalHeader().setStretchLastSection(True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setAlternatingRowColors(True)

    def sizeHintForColumn(self, column: int):
        if column == self.model().columnCount() - 1:
            return 0
        return super().sizeHintForColumn(column)


class NodesWidget(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'nodes.ui'), self)

        hh = self.tvNodes.horizontalHeader()
        self._sort_indicator_section = -1
        self._sort_indicator_order = Qt.AscendingOrder
        hh.setSortIndicator(-1, Qt.AscendingOrder)

        menu = QMenu()
        menu.addAction(self.actionUseColumnForLabels)
        menu.addAction(self.actionResetLabelMapping)
        self.btUseColumnForLabels.setMenu(menu)
        self.btUseColumnForLabels.setDefaultAction(self.actionUseColumnForLabels)

        menu = QMenu()
        menu.addAction(self.actionUseColumnsForPieCharts)
        menu.addAction(self.actionResetPieColorMapping)
        self.btUseColumnsForPieCharts.setMenu(menu)
        self.btUseColumnsForPieCharts.setDefaultAction(self.actionUseColumnsForPieCharts)

        menu = QMenu()
        menu.addAction(self.actionUseColumnForNodesSizes)
        menu.addAction(self.actionResetSizeMapping)
        self.btUseColumnForNodesSizes.setMenu(menu)
        self.btUseColumnForNodesSizes.setDefaultAction(self.actionUseColumnForNodesSizes)

        menu = QMenu()
        menu.addAction(self.actionUseColumnForNodesColors)
        menu.addAction(self.actionResetColorMapping)
        self.btUseColumnForNodesColors.setMenu(menu)
        self.btUseColumnForNodesColors.setDefaultAction(self.actionUseColumnForNodesColors)

        menu = QMenu()
        menu.addAction(self.actionUseColumnForNodesPixmaps)
        menu.addAction(self.actionResetPixmapMapping)
        self.btUseColumnForNodesPixmaps.setMenu(menu)
        self.btUseColumnForNodesPixmaps.setDefaultAction(self.actionUseColumnForNodesPixmaps)

        self.btHighlightSelectedNodes.setDefaultAction(self.actionHighlightSelectedNodes)
        self.btAddColumnsByFormulae.setDefaultAction(self.actionAddColumnsByFormulae)
        self.btClusterize.setDefaultAction(self.actionClusterize)
        self.btDeleteColumns.setDefaultAction(self.actionDeleteColumns)
        self.btSetAlternatingRowColors.setDefaultAction(self.actionSetAlternatingRowColors)
        self.btEnableOrdering.setDefaultAction(self.actionEnableOrdering)
        self.btSetColumnsMovable.setDefaultAction(self.actionSetColumnsMovable)
        self.btFreezeFirstColumn.setDefaultAction(self.actionFreezeFirstColumn)
        self.btFreezeColumns.setDefaultAction(self.actionFreezeColumns)

        menu = QMenu()
        menu.addAction(self.actionViewSpectrum)
        menu.addAction(self.actionViewCompareSpectrum)
        self.btShowSpectrum.setMenu(menu)
        self.btShowSpectrum.setDefaultAction(self.actionViewSpectrum)

        menu = QMenu()
        menu.addAction(self.actionFindStandards)
        menu.addAction(self.actionFindAnalogs)
        menu.addSeparator()
        menu.addAction(self.actionMetFrag)
        menu.addAction(self.actionCFMID)
        self.btFindStandards.setMenu(menu)
        self.btFindStandards.setDefaultAction(self.actionFindStandards)

        self.actionFreezeColumns.triggered.connect(self.on_freeze_columns)
        self.actionFreezeFirstColumn.triggered.connect(self.on_freeze_first_column)
        self.actionSetAlternatingRowColors.triggered.connect(self.on_set_alternating_row_colors)
        self.actionEnableOrdering.triggered.connect(self.on_enable_sorting)
        self.actionSetColumnsMovable.triggered.connect(
            lambda: self.tvNodes.horizontalHeader().setSectionsMovable(self.actionSetColumnsMovable.isChecked()))
        hh.sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        self.tvNodes.frozenTable().horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)

    def on_set_alternating_row_colors(self):
        checked = self.actionSetAlternatingRowColors.isChecked()
        self.tvNodes.setAlternatingRowColors(checked)
        self.tvNodes.frozenTable().setAlternatingRowColors(checked)

    def on_sort_indicator_changed(self, logical_index: int, order: int):
        # Store sort indicator if sorting is enabled, restore the last saved if sorting is disabled
        # We need to do this because if sort indicator is shown but sorting disabled, the sort indicator
        # can still be changed
        if self.tvNodes.isSortingEnabled():
            self._sort_indicator_section = logical_index
            self._sort_indicator_order = order
            hh = self.tvNodes.frozenTable().horizontalHeader() if self.sender() == self.tvNodes.horizontalHeader() \
                else self.tvNodes.horizontalHeader()
            with SignalBlocker(hh):
                hh.setSortIndicator(logical_index, order)
        else:
            for hh in (self.tvNodes.horizontalHeader(), self.tvNodes.frozenTable().horizontalHeader()):
                with SignalBlocker(hh):
                    hh.setSortIndicator(self._sort_indicator_section, self._sort_indicator_order)

    def on_enable_sorting(self):
        if self.actionEnableOrdering.isChecked():
            self.tvNodes.setSortingEnabled(True)
            self.tvNodes.frozenTable().setSortingEnabled(True)
        else:
            self.tvNodes.setSortingEnabled(False)
            self.tvNodes.frozenTable().setSortingEnabled(False)
            self.tvNodes.horizontalHeader().setSortIndicatorShown(True)
            self.tvNodes.frozenTable().horizontalHeader().setSortIndicatorShown(True)

    def on_freeze_columns(self):
        if self.actionFreezeColumns.isChecked():
            selected_columns = self.tvNodes.selectionModel().selectedColumns()
            if not selected_columns:
                with SignalBlocker(self.actionFreezeColumns):
                    self.actionFreezeColumns.setChecked(False)
                return

            with SignalBlocker(self.actionFreezeFirstColumn):
                self.actionFreezeFirstColumn.setChecked(False)
            self.tvNodes.setFrozenColumns(
                self.tvNodes.horizontalHeader().visualIndex(selected_columns[-1].column()) + 1)
        else:
            self.tvNodes.setFrozenColumns(None)

    def on_freeze_first_column(self):
        if self.actionFreezeFirstColumn.isChecked():
            with SignalBlocker(self.actionFreezeColumns):
                self.actionFreezeColumns.setChecked(False)
            self.tvNodes.setFrozenColumns(1)
        else:
            self.tvNodes.setFrozenColumns(None)


class EdgesWidget(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'edges.ui'), self)

        hh = self.tvEdges.horizontalHeader()
        self._sort_indicator_section = -1
        self._sort_indicator_order = Qt.AscendingOrder
        hh.setSortIndicator(-1, Qt.AscendingOrder)

        self.btHighlightSelectedEdges.setDefaultAction(self.actionHighlightSelectedEdges)
        self.btHighlightNodesFromSelectedEdges.setDefaultAction(self.actionHighlightNodesFromSelectedEdges)
        self.btSetAlternatingRowColors.setDefaultAction(self.actionSetAlternatingRowColors)
        self.btEnableOrdering.setDefaultAction(self.actionEnableOrdering)
        self.btSetColumnsMovable.setDefaultAction(self.actionSetColumnsMovable)

        self.actionSetAlternatingRowColors.triggered.connect(
            lambda: self.tvEdges.setAlternatingRowColors(self.actionSetAlternatingRowColors.isChecked()))
        self.actionEnableOrdering.triggered.connect(self.on_enable_sorting)
        self.actionSetColumnsMovable.triggered.connect(
            lambda: self.tvEdges.horizontalHeader().setSectionsMovable(self.actionSetColumnsMovable.isChecked()))
        self.tvEdges.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)

    def on_sort_indicator_changed(self, logical_index: int, order: int):
        # Store sort indicator if sorting is enabled, restore the last saved if sorting is disabled
        # We need to do this because if sort indicator is shown but sorting disabled, the sort indicator
        # can still be changed
        hh = self.tvEdges.horizontalHeader()

        # Sorting is disabled in proxy model for last column because it's content is generated on demand
        if self.tvEdges.isSortingEnabled() and logical_index != self.tvEdges.model().columnCount() - 1:
            self._sort_indicator_section = logical_index
            self._sort_indicator_order = order

            with SignalBlocker(hh):
                hh.setSortIndicator(logical_index, order)
        else:
            with SignalBlocker(hh):
                hh.setSortIndicator(self._sort_indicator_section, self._sort_indicator_order)

    def on_enable_sorting(self):
        if self.actionEnableOrdering.isChecked():
            self.tvEdges.setSortingEnabled(True)
        else:
            self.tvEdges.setSortingEnabled(False)
            self.tvEdges.horizontalHeader().setSortIndicatorShown(True)

