from PySide6.QtCore import Qt

from metgem_app.ui.widgets.metadata.metadata import MetadataTableView


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