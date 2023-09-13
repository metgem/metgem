from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import QTableView, QAbstractButton

from metgem_app.ui.widgets.delegates import EnsureStringItemDelegate


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
        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.model().sort(-1)

    def sourceModel(self):
        model = self.model()
        while hasattr(model, 'sourceModel'):
            model = model.sourceModel()
        return model