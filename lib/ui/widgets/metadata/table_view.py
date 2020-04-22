from PyQt5.QtGui import QPainter, QMouseEvent, QPalette
from PyQt5.QtWidgets import QTableView, QAbstractButton, QHeaderView, QWidget, QMenu
from PyQt5.QtCore import Qt, QObject, QEvent, QRect, QItemSelectionModel, pyqtSignal, QTimer, QModelIndex
from PyQt5 import uic

from .freeze_table import FreezeTableMixin
from .model import ProxyModel, ColorMarkRole
from ..delegates import EnsureStringItemDelegate, StandardsResultsDelegate
from ....utils import SignalBlocker

import os


class HeaderView(QHeaderView):
    """QHeaderView that can have a different color background and or color mark for each section and selection
    of columns with right mouse button."""

    sectionPressedRight = pyqtSignal(int)
    sectionEnteredRight = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._right_selection_active = False
        self._selection_running = False
        self._right_pressed_section = -1

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

    def allowRightMouseSelection(self):
        return self._right_selection_active

    def setAllowRightMouseSelection(self, value):
        self._right_selection_active = bool(value)

    def mousePressEvent(self, event: QMouseEvent):
        if not self._right_selection_active or event.buttons() != Qt.RightButton:
            return super().mousePressEvent(event)

        if self._selection_running:
            return

        pos = event.x() if self.orientation() == Qt.Horizontal else event.y()
        self._right_pressed_section = self.logicalIndexAt(pos)
        if self.sectionsClickable():
            self.sectionPressedRight.emit(self._right_pressed_section)
            if self._right_pressed_section != -1:
                self.updateSection(self._right_pressed_section)
                self._selection_running = True

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._right_selection_active or event.buttons() != Qt.RightButton:
            return super().mouseMoveEvent(event)

        pos = event.x() if self.orientation() == Qt.Horizontal else event.y()

        if pos < 0:
            return

        if self._selection_running:
            logical = self.logicalIndexAt(pos)
            if logical == self._right_pressed_section:
                return  # Nothing to do
            elif self._right_pressed_section != -1:
                self.updateSection(self._right_pressed_section)
            self._right_pressed_section = logical
            if self.sectionsClickable() and logical != -1:
                self.sectionEnteredRight.emit(self._right_pressed_section)
                self.updateSection(self._right_pressed_section)
            return

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)

        pos = event.x() if self.orientation() == Qt.Horizontal else event.y()

        if self._selection_running and self.sectionsClickable():
            section = self.logicalIndex(pos)
            self.updateSection(section)

        self._selection_running = False
        self._right_pressed_section = -1


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

        self.setSortingEnabled(True)

    def eventFilter(self, watched: QObject, event: QEvent):
        # If top-left button is right clicked, reset model's sorting order
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.RightButton:
                self.resetSorting()
        return False

    def resetSorting(self):
        self.model().sort(-1)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

    def setModel(self, model):
        proxy = ProxyModel()
        proxy.setSourceModel(model)
        super().setModel(proxy)


class NodeTableView(FreezeTableMixin, MetadataTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.timers = {}

        for table in (self, self.frozenTable()):
            header = HeaderView(Qt.Horizontal, table)
            header.setHighlightSections(True)
            header.setSectionsClickable(True)
            header.setSectionsMovable(True)
            header.setAllowRightMouseSelection(True)
            header.sectionPressedRight.connect(self.selectColumn)
            header.sectionEnteredRight.connect(self.on_section_entered)
            table.setHorizontalHeader(header)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        delegate = StandardsResultsDelegate()
        self.viewDetailsClicked = delegate.viewDetailsClicked
        self.setItemDelegateForColumn(1, delegate)

    def on_section_entered(self, logical_index):
        index = self.model().index(0, logical_index)
        model = self.selectionModel()
        selection = model.selection()
        selection.select(index, index)
        model.select(selection, QItemSelectionModel.Select | QItemSelectionModel.Columns)

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

        # Last column is virtual (content is generated on demand),
        # so we don't want to sort or resize column from content
        self.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionsMovable(True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def sizeHintForColumn(self, column: int):
        if column == self.model().columnCount() - 1:
            return 0
        return super().sizeHintForColumn(column)

    # noinspection PyUnusedLocal
    def on_sort_indicator_changed(self, index: int, order: int):
        if index == self.model().columnCount() - 1:
            with SignalBlocker(self.horizontalHeader()):
                self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)


class NodesWidget(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'nodes.ui'), self)

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

        self.btHighlightSelectedNodes.setDefaultAction(self.actionHighlightSelectedNodes)
        self.btAddColumnsByFormulae.setDefaultAction(self.actionAddColumnsByFormulae)
        self.btClusterize.setDefaultAction(self.actionClusterize)
        self.btDeleteColumns.setDefaultAction(self.actionDeleteColumns)

        menu = QMenu()
        menu.addAction(self.actionViewSpectrum)
        menu.addAction(self.actionViewCompareSpectrum)
        self.btShowSpectrum.setMenu(menu)
        self.btShowSpectrum.setDefaultAction(self.actionViewSpectrum)

        menu = QMenu()
        menu.addAction(self.actionFindStandards)
        menu.addAction(self.actionFindAnalogs)
        self.btFindStandards.setMenu(menu)
        self.btFindStandards.setDefaultAction(self.actionFindStandards)

        menu = QMenu()
        menu.addAction(self.actionFreezeColumns)
        menu.addAction(self.actionFreezeFirstColumn)
        self.btFreezeColumns.setMenu(menu)
        self.btFreezeColumns.setDefaultAction(self.actionFreezeFirstColumn)


class EdgesWidget(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'edges.ui'), self)

        self.btHighlightSelectedEdges.setDefaultAction(self.actionHighlightSelectedEdges)
        self.btHighlightNodesFromSelectedEdges.setDefaultAction(self.actionHighlightNodesFromSelectedEdges)
