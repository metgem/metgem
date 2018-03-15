from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt


class NumberDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        value = index.data(Qt.DisplayRole)
        self.drawDisplay(painter, option, option.rect, str(value))
        self.drawFocus(painter, option, option.rect)
