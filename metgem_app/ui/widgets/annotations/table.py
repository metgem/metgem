from typing import Any

from PySide6.QtCore import QModelIndex, Qt, QSortFilterProxyModel, QItemSelection, QAbstractTableModel
from PySide6.QtWidgets import QWidget, QGraphicsScene
from metgem_app.ui.widgets.annotations.table_ui import Ui_AnnotationsWidget


class AnnotationsModel(QAbstractTableModel):
    ItemRole = Qt.UserRole

    def __init__(self, scene: QGraphicsScene, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = scene

    def setScene(self, scene):
        self.beginResetModel()
        self._scene = scene
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._scene.annotationsLayer.childItems())

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return str(self._scene.annotationsLayer.childItems()[index.row()])
        elif role == AnnotationsModel.ItemRole:
            return self._scene.annotationsLayer.childItems()[index.row()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and section == 0:
            return 'Description'

        return super().headerData(section, orientation, role)


class AnnotationsWidget(QWidget, Ui_AnnotationsWidget):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.tvAnnotations.doubleClicked.connect(self.on_double_clicked)

    def on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        for index in selected.indexes():
            item = index.data(AnnotationsModel.ItemRole)
            item.setSelected(True)

        for index in deselected.indexes():
            item = index.data(AnnotationsModel.ItemRole)
            item.setSelected(False)

    def on_double_clicked(self, index: QModelIndex):
        item = index.data(AnnotationsModel.ItemRole)
        scene = item.scene()
        scene.requestEditAnnotationItem(item)

    def model(self) -> QAbstractTableModel:
        return self.tvAnnotations.model()

    def setModel(self, model: QAbstractTableModel):
        proxy = QSortFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.tvAnnotations.setModel(proxy)
        self.tvAnnotations.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def beginResetModel(self):
        if self.model() is not None:
            self.model().beginResetModel()

    def endResetModel(self):
        if self.model() is not None:
            self.model().endResetModel()
