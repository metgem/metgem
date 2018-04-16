from PyQt5.QtWidgets import QTableView, QAbstractButton, QHeaderView
from PyQt5.QtCore import Qt, QObject, QEvent, QSize


class MetadataTableView(QTableView):
    """ TableView to display metadata"""

    def __init__(self):
        super().__init__()

        # Install event filter on top left button (usually used to select all rows and columns
        btn = self.findChild(QAbstractButton)
        if btn:
            btn.installEventFilter(self)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

    def eventFilter(self, watched: QObject, event: QEvent):
        # If top-left button if right clicked, reset model's sorting order
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.RightButton:
                self.resetSorting()
        return False

    def resetSorting(self):
        self.model().sort(-1)
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)


class NodeTableView(MetadataTableView):
    def __init__(self):
        super().__init__()

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
