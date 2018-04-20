from PyQt5.QtGui import QPainter, QKeyEvent
from PyQt5.QtWidgets import QTableView, QAbstractButton, QHeaderView
from PyQt5.QtCore import Qt, QObject, QEvent, QRect, QItemSelectionModel

from .model import ProxyModel
from ..delegates import EnsureStringItemDelegate


class HeaderView(QHeaderView):
    """QHeaderView that can have a different color background for each section"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selection_state = False

        self._saved_sort_section = self.sortIndicatorSection()
        self._saved_sort_order = self.sortIndicatorOrder()

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int):
        bg = self.model().headerData(logical_index, Qt.Horizontal, Qt.BackgroundColorRole)

        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()

        if bg is not None and bg.isValid():
            painter.fillRect(rect, bg)


class MetadataTableView(QTableView):
    """ TableView to display metadata"""

    def __init__(self):
        super().__init__()

        self.setItemDelegate(EnsureStringItemDelegate())

        # Install event filter on top left button (usually used to select all rows and columns
        btn = self.findChild(QAbstractButton)
        if btn:
            btn.installEventFilter(self)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

        self.setSortingEnabled(True)

    def eventFilter(self, watched: QObject, event: QEvent):
        # If top-left button if right clicked, reset model's sorting order
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


class NodeTableView(MetadataTableView):
    def __init__(self):
        super().__init__()

        self._sort_allowed = True

        header = HeaderView(Qt.Horizontal, self)
        header.setSectionsClickable(True)
        header.setHighlightSections(True)
        self.setHorizontalHeader(header)

        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)


class EdgeTableView(MetadataTableView):

    def __init__(self):
        super().__init__()

        # Last column is virtual (content is generated on demand),
        # so we don't want to sort or resize column from content
        self.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        self.horizontalHeader().setStretchLastSection(True)

    def sizeHintForColumn(self, column: int):
        if column == self.model().columnCount() - 1:
            return 0
        return super().sizeHintForColumn(column)

    def on_sort_indicator_changed(self, index: int, order):
        if index == self.model().columnCount() - 1:
            self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
