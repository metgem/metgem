import os

from PySide6.QtCore import Qt, QItemSelection, QSortFilterProxyModel
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QLabel, QHeaderView, QMessageBox, QDialogButtonBox

from . import ProgressDialog
from ..config import PLUGINS_PATH
from ..models.plugins import PluginsModel, AvailablePluginsModel, InstalledPluginsModel, UpdatesPluginsModel
from ..plugins import get_loaded_plugins, reload_plugins
from ..workers.net import CheckPluginsVersionsWorker, DownloadPluginsWorker
from ..workers.core import WorkerQueue
from .plugins_manager_dialog_ui import Ui_PluginsManager


class PluginsManagerDialog(QDialog, Ui_PluginsManager):

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.setupUi(self)

        self.tabWidget.setCurrentIndex(0)

        self.tvAvailable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        model = QSortFilterProxyModel()
        model.setSourceModel(AvailablePluginsModel())
        self.tvAvailable.setModel(model)
        self.tvAvailable.selectionModel().selectionChanged.connect(
            lambda selected, _: self.update_description(self.lblADescription, selected))

        self.tvUpdates.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        model = QSortFilterProxyModel()
        model.setSourceModel(UpdatesPluginsModel())
        self.tvUpdates.setModel(model)
        self.tvUpdates.selectionModel().selectionChanged.connect(
            lambda selected, _: self.update_description(self.lblUDescription, selected))

        self.tvInstalled.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
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

        self.btReloadPlugins = self.buttonBox.addButton("Reload Plugins", QDialogButtonBox.ButtonRole.ActionRole)
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
        try:
            os.makedirs(PLUGINS_PATH, exist_ok=True)
        except PermissionError:
            QMessageBox.critical(self, None,
                                'Unable to download plugins because the destination folder is not writable.')

        def plugins_installed():
            nonlocal worker
            downloaded, unreachable = worker.result()

            if any(unreachable):
                msg = ["{}: {}".format(origin, ", ".join(names)) for origin, names in unreachable]
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
                filename = os.path.realpath(plugin.__file__)

                # Remove the plugin if it's located in the user's plugins folder
                if os.path.commonpath([PLUGINS_PATH, filename]) == PLUGINS_PATH:
                    os.remove(filename)
            except (FileNotFoundError, AttributeError, ValueError):
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
