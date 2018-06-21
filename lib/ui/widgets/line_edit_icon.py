from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPaintEvent, QPainter, QColor
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidget


class LineEditIcon(QLineEdit):

    def __init__(self, icon: QIcon, parent: QWidget):
        super().__init__(parent)
        self.setIcon(icon)

    def setIcon(self, icon: QIcon):
        self._icon = icon
        if icon.isNull():
            self.setTextMargins(1, 1, 1, 1)
        else:
            self.setTextMargins(24, 1, 1, 1)

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)

        if not self._icon.isNull():
            painter = QPainter(self)
            pixmap = self._icon.pixmap(self.height() - 6, self.height() - 6)
            cx = pixmap.width()

            painter.drawPixmap(2, 3, pixmap)
            painter.setPen(QColor(Qt.lightGray))
            painter.drawLine(cx + 2, 3, cx + 2, self.height() - 4)
