import os

import typing
from PyQt5 import uic
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QItemSelection, QSortFilterProxyModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QLabel, QHeaderView, QMessageBox, QDialogButtonBox

from . import ProgressDialog
from ..config import PLUGINS_PATH
from ..plugins import get_loaded_plugins, reload_plugins
from ..workers import WorkerQueue, CheckPluginsVersionsWorker, DownloadPluginsWorker


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


class PluginsManagerDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'plugins_manager_dialog.ui'), self)

        self.tabWidget.setCurrentIndex(0)

        self.tvAvailable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        model = QSortFilterProxyModel()
        model.setSourceModel(AvailablePluginsModel())
        self.tvAvailable.setModel(model)
        self.tvAvailable.selectionModel().selectionChanged.connect(
            lambda selected, _: self.update_description(self.lblADescription, selected))

        self.tvUpdates.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        model = QSortFilterProxyModel()
        model.setSourceModel(UpdatesPluginsModel())
        self.tvUpdates.setModel(model)
        self.tvUpdates.selectionModel().selectionChanged.connect(
            lambda selected, _: self.update_description(self.lblUDescription, selected))

        self.tvInstalled.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        model = QSortFilterProxyModel()
        model.setSourceModel(InstalledPluginsModel())
        self.tvInstalled.setModel(model)
        self.tvInstalled.selectionModel().selectionChanged.connect(
            lambda selected, _: self.update_description(self.lblIDescription, selected))

        for edit in (self.leASearch, self.leUSearch, self.leISearch):
            edit.textChanged.connect(self.on_do_search)
            edit.returnPressed.connect(self.on_do_search)
        for button in (self.btASearch, self.btUSearch, self.btISearch):
            button.clicked.connect(self.on_do_search)

        self.btReloadPlugins = self.buttonBox.addButton("Reload Plugins", QDialogButtonBox.ActionRole)
        self.btReloadPlugins.setIcon(QIcon(":/icons/images/refresh.svg"))
        self.btReloadPlugins.clicked.connect(self.reload_plugins)

        self.btInstall.clicked.connect(self.on_install_clicked)
        self.btUpdate.clicked.connect(self.on_update_clicked)
        self.btUninstall.clicked.connect(self.on_uninstall_clicked)

        self._workers = WorkerQueue(self, ProgressDialog(self))

        self.update_plugins_lists()

    def on_do_search(self):
        sender = self.sender()
        if sender in (self.leASearch, self.btASearch):
            table = self.tvAvailable
            edit = self.leASearch
        elif sender in (self.leUSearch, self.btUSearch):
            table = self.tvUpdates
            edit = self.leUSearch
        elif sender in (self.leISearch, self.btISearch):
            table = self.tvInstalled
            edit = self.leISearch
        else:
            return

        table.model().setFilterRegExp(str(edit.text()))

    def install_plugins(self, plugins):
        def plugins_installed():
            nonlocal worker
            downloaded, unreachable = worker.result()

            if any(unreachable):
                msg = ["{}: {}".format(origin, ", ".join(names)) for origin, names in unreachable.items()]
                QMessageBox.warning(self, None,
                                    "One or more plugins were not accessible on the remote server(s):\n{}"
                                    .format("\n".join(msg)))

            if any(downloaded):
                num_installed = len(downloaded)
                QMessageBox.information(self, None, f"{num_installed} plugin"
                                                    f"{'s' if num_installed>1 else ''}"
                                                    " successfully installed.")

            self.reload_plugins()

        worker = DownloadPluginsWorker(PLUGINS_PATH, plugins)
        worker.finished.connect(plugins_installed)
        self._workers.append(worker)
        self._workers.start()

    def uninstall_plugins(self, plugins):
        for plugin in plugins:
            try:
                os.remove(plugin.__file__)
            except (FileNotFoundError, AttributeError):
                pass
        self.reload_plugins()

    def get_checked_items_plugins(self, model):
        plugins = []
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            if index.data(Qt.CheckStateRole) == Qt.Checked:
                plugin = index.data(PluginsModel.PluginRole)
                plugins.append(plugin)

        return plugins

    def on_install_clicked(self):
        model = self.tvAvailable.model().sourceModel()
        plugins = self.get_checked_items_plugins(model)

        self.install_plugins(plugins)

    def on_update_clicked(self):
        model = self.tvUpdates.model().sourceModel()
        plugins = self.get_checked_items_plugins(model)

        self.install_plugins(plugins)

    def on_uninstall_clicked(self):
        model = self.tvInstalled.model().sourceModel()
        plugins = self.get_checked_items_plugins(model)

        self.uninstall_plugins(plugins)

    def update_description(self, desc_label: QLabel, selected: QItemSelection):
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            plugin = index.data(InstalledPluginsModel.PluginRole)
            if plugin:
                try:
                    desc_label.setText(plugin.__description__)
                except AttributeError:
                    try:
                        desc_label.setText(plugin['description'])
                    except KeyError:
                        desc_label.setText("")

    def reload_plugins(self):
        reload_plugins()
        self.update_plugins_lists()

    def update_plugins_lists(self):
        def finished():
            nonlocal worker, loaded_plugins
            plugins = worker.result()
            if plugins:
                if loaded_plugins:
                    available_plugins = {k: v for k, v in plugins.items() if k not in loaded_plugins}
                else:
                    available_plugins = plugins
                self.tvAvailable.model().sourceModel().update(sorted(tuple(available_plugins.items())))

                if loaded_plugins:
                    plugins_to_update = []
                    for name, plugin in loaded_plugins.items():
                        if name in plugins:
                            version = getattr(plugin, '__version__', '')
                            if plugins[name]['version'] > version:
                                plugins_to_update.append((name, plugin, plugins[name]))
                    self.tvUpdates.model().sourceModel().update(sorted(plugins_to_update))

        loaded_plugins = get_loaded_plugins()
        if loaded_plugins:
            self.tvInstalled.model().sourceModel().update(sorted(tuple(loaded_plugins.items())))

        worker = CheckPluginsVersionsWorker()
        worker.finished.connect(finished)
        self._workers.append(worker)
        self._workers.start()
