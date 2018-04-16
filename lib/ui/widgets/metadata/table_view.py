from PyQt5.QtWidgets import QTableView, QAbstractButton
from PyQt5.QtCore import Qt, QObject, QEvent


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
    pass
