import typing

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex


class PluginsModel(QAbstractTableModel):
    PluginRole = Qt.UserRole

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._plugins = []
        self._selected_indexes = set()

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return None

        if role == Qt.CheckStateRole:
            if index.column() == 0:
                return Qt.Checked if index.row() in self._selected_indexes else Qt.Unchecked

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False

        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self._selected_indexes.add(index.row())
                self.dataChanged.emit(index, index)
            else:
                try:
                    self._selected_indexes.remove(index.row())
                except KeyError:
                    pass
                else:
                    self.dataChanged.emit(index, index)
            return True

        return super().setData(index, value, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.isValid():
            if index.column() == 0:
                return flags | Qt.ItemIsUserCheckable
            else:
                return flags
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Plugin"
            elif section == 1:
                return "Version"

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._plugins)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return 2

    def update(self, plugins):
        self.beginResetModel()
        self._plugins = plugins
        self.endResetModel()


class AvailablePluginsModel(PluginsModel):
    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()

            if column == 0:
                return self._plugins[row][0]
            elif column == 1:
                return self._plugins[row][1]['version']
        elif role == PluginsModel.PluginRole:
            return self._plugins[index.row()][1]
        return super().data(index, role)


class InstalledPluginsModel(PluginsModel):
    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()

            if column == 0:
                return self._plugins[row][0]
            elif column == 1:
                try:
                    return self._plugins[row][1].__version__
                except AttributeError:
                    return
        elif role == PluginsModel.PluginRole:
            return self._plugins[index.row()][1]

        return super().data(index, role)


class UpdatesPluginsModel(PluginsModel):
    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()

            if column == 0:
                return self._plugins[row][0]
            elif column == 1:
                return self._plugins[row][1].__version__
            elif column == 2:
                return self._plugins[row][2]['version']
        elif role == PluginsModel.PluginRole:
            return self._plugins[index.row()][2]
        return super().data(index, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Plugin"
            elif section == 1:
                return "Installed Version"
            elif section == 2:
                return "Available Version"

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return 3
