from PyQt5.QtWidgets import QStyledItemDelegate


class EnsureStringItemDelegate(QStyledItemDelegate):

    def displayText(self, value, locale):
        return str(value)