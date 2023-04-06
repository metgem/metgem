from PySide6.QtCore import Qt, QTimer, QModelIndex
from PySide6.QtGui import QPalette

from ..delegates import StandardsResultsDelegate
from .freeze_table import FreezeTableMixin
from .metadata import MetadataTableView
from .header import HeaderView


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