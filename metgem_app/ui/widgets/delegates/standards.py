from qtpy.QtCore import Qt, QObject, QEvent, QModelIndex, Signal
from qtpy.QtGui import QStandardItemModel, QStandardItem, QIcon
from qtpy.QtWidgets import (QStyledItemDelegate, QComboBox, QTreeView,
                             QWidget, QHBoxLayout, QSizePolicy, QToolButton)

from ....models.metadata import StandardsRole, AnalogsRole, DbResultsRole

ANALOGS = 1


class StandardsResultsEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.combo = StandardsResultsComboBox(self)
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.combo)
        self.button = QToolButton(self)
        self.button.setIcon(QIcon(':/icons/images/library-more.svg'))
        self.button.setText('...')
        self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.button.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        self.setContentsMargins(0, 0, 0, 0)

    def model(self):
        return self.combo.view().model()

    def setModel(self, model):
        self.combo.setModel(model)

    def rootModelIndex(self):
        return self.combo.rootModelIndex()

    def setRootModelIndex(self, index: QModelIndex):
        self.combo.setRootModelIndex(index)

    def currentIndex(self):
        return self.combo.currentIndex()

    def setCurrentIndex(self, index: QModelIndex):
        self.combo.setCurrentIndex(index)

    def showPopup(self):
        self.combo.showPopup()

    def hidePopup(self):
        self.combo.hidePopup()


class StandardsResultsComboBox(QComboBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._skip_next_hide = False

        self.setStyleSheet("""QPushButton {
                              text-decoration:underline;
                              border: none;}""")

        view = QTreeView()
        view.setUniformRowHeights(True)
        view.setAlternatingRowColors(True)
        view.setHeaderHidden(True)
        view.viewport().installEventFilter(self)
        self.setView(view)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.MouseButtonPress and obj == self.view().viewport():
            # Prevent pop-up to close if user click in TreeView
            index = self.view().indexAt(event.pos())
            if not self.view().visualRect(index).contains(event.pos()):
                self._skip_next_hide = True
        return False

    def showPopup(self):
        self.view().expandAll()
        super().showPopup()

    def hidePopup(self):
        if self._skip_next_hide:
            self._skip_next_hide = False
            return

        super().hidePopup()


class StandardsResultsDelegate(QStyledItemDelegate):

    viewDetailsClicked = Signal(int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, widget, option, index):
        standards = index.model().data(index, StandardsRole)
        analogs = index.model().data(index, AnalogsRole)
        if standards or analogs:
            model = QStandardItemModel()
            editor = StandardsResultsEditor(widget)
            editor.setModel(model)
            for type_, items in enumerate((standards, analogs)):
                parent = QStandardItem()
                if type_ == ANALOGS:
                    parent.setText('Analogs')
                    parent.setIcon(QIcon(":/icons/images/library-query-analogs.svg"))
                else:
                    parent.setText('Standards')
                    parent.setIcon(QIcon(":/icons/images/library-query.svg"))
                parent.setData(type_)
                parent.setSelectable(False)
                model.appendRow(parent)
                if items and not isinstance(items, str):
                    for i, result in enumerate(items):
                        if not isinstance(result, str):
                            item = QStandardItem()
                            if type_ == ANALOGS:
                                item.setSelectable(False)
                            item.setText(result.text)
                            item.setData(result.id)
                            parent.appendRow(item)

            # Connect events
            editor.button.clicked.connect(lambda: self.on_view_details(index, editor))

            return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        standards = index.data(StandardsRole)
        if standards is not None and not isinstance(standards, str):
            parent = editor.model().index(0, 0)
            editor.setRootModelIndex(parent)
            editor.setCurrentIndex(value)
            editor.setRootModelIndex(QModelIndex())

    def setModelData(self, editor, model, index):
        if editor.currentIndex() > 0:
            model.setData(index, editor.currentIndex(), Qt.EditRole)

    def on_view_details(self, index, editor):
        self.closeEditor.emit(editor)
        item_ids = index.model().data(index, DbResultsRole)
        if item_ids:
            try:
                row = index.model().mapToSource(index).row()
            except AttributeError:
                row = index.row()
            self.viewDetailsClicked.emit(row, item_ids)
