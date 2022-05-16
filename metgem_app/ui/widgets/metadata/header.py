from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QHeaderView

from ....models.metadata import ColorMarkRole


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