from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem, QLineEdit


class EnsureStringItemDelegate(QStyledItemDelegate):

    def displayText(self, value, locale):
        return str(value)

    def createEditor(self, parent: QWidget, options: QStyleOptionViewItem, index: QModelIndex):
        return QLineEdit(parent)
