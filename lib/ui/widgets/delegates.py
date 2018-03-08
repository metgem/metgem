from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QToolTip
from PyQt5.QtCore import QEvent, Qt

class AutoToolTipItemDelegateMixin():
    '''
    QItemDelegate subclass that shows tooltip based on item text and
    only if text is not fully visibile
    '''

    def __init__(self, parent=None):
        self._widths = {}
        super().__init__(parent)

    def helpEvent(self, event, view, option, index):
        if event is None or view is None:
            return False

        if event.type() == QEvent.ToolTip and index.isValid() and index in self._widths:
            if self._widths[index] < self.sizeHint(option, index).width():
                tooltip = self.displayText(index.data(Qt.DisplayRole),
                                           option.locale)

                # If text is elided, show tooltip
                if tooltip != '':
                    QToolTip.showText(event.globalPos(), tooltip, view)
                    return True

            if not super().helpEvent(event, view, option, index):
                QToolTip.hideText()
                return True

        return super().helpEvent(event, view, option, index)

    def paint(self, painter, option, index):
        # For some reason, option.rect in helpEvent has bad width in helpEvent but is ok in paint
        self._widths[index] = option.rect.width()
        super().paint(painter, option, index)


class AutoToolTipItemDelegate(AutoToolTipItemDelegateMixin, QStyledItemDelegate):
    pass


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QListView
    from PyQt5.QtGui import QStandardItemModel, QStandardItem

    app = QApplication(sys.argv)

    view = QListView()
    model = QStandardItemModel()
    view.setModel(model)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setItemDelegate(AutoToolTipItemDelegate())
    view.setMinimumWidth(200)

    for i in range(0, 20):
        item = QStandardItem(str(i) * (50 - i))
        model.appendRow(item)

    view.show()

    sys.exit(app.exec_())