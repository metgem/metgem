from PyQt5.QtWidgets import QItemDelegate, QToolTip
from PyQt5.QtCore import QEvent, Qt


class AutoToolTipItemDelegateMixin:
    """
    QItemDelegate subclass that shows tooltip based on item text and
    only if text is not fully visible
    """

    def helpEvent(self, event, view, option, index):
        if event is None or view is None:
            return False

        if event.type() == QEvent.ToolTip and index.isValid():
            if option.rect.width() <= self.sizeHint(option, index).width():
                tooltip = index.data(Qt.DisplayRole)

                # If text is elided, show tooltip
                if tooltip != '':
                    QToolTip.showText(event.globalPos(), tooltip, view)
                    return True

            if not super().helpEvent(event, view, option, index):
                QToolTip.hideText()
                return True

        return super().helpEvent(event, view, option, index)


class AutoToolTipItemDelegate(AutoToolTipItemDelegateMixin, QItemDelegate):
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
