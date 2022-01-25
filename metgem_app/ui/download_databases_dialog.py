import ftplib
import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTreeWidgetItem, QDialogButtonBox, QMessageBox
from requests.exceptions import ConnectionError, RequestException

from .progress_dialog import ProgressDialog
from .widgets import AutoToolTipItemDelegate
from ..workers.databases import (ListDatabasesWorker, DownloadDatabasesWorker,
                                 ConvertDatabasesWorker)
from ..workers.core import WorkerQueue
from ..plugins import get_db_sources


UI_FILE = os.path.join(os.path.dirname(__file__), 'download_databases_dialog.ui')

DownloadDatabasesDialogUI, DownloadDatabasesDialogBase = uic.loadUiType(UI_FILE,
                                                                        from_imports='metgem_app.ui',
                                                                        import_from='metgem_app.ui')


class DownloadDatabasesDialog(DownloadDatabasesDialogUI, DownloadDatabasesDialogBase):
    IdsRole = Qt.UserRole + 1
    DescRole = Qt.UserRole + 2
    OriginRole = Qt.UserRole + 3

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.treeDatabases.setIconSize(QSize(12, 12))
        self.treeDatabases.setFocus()
        self.treeDatabases.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.treeDatabases.setItemDelegate(AutoToolTipItemDelegate())

        self._workers = WorkerQueue(self, ProgressDialog(self))

        # Add download button
        self.btDownload = self.buttonBox.addButton("&Download", QDialogButtonBox.ActionRole)
        self.btDownload.setIcon(QIcon(":/icons/images/download-package.svg"))
        self.btDownload.setEnabled(False)

        # Set Close button as default
        bt_close = self.buttonBox.button(QDialogButtonBox.Close)
        if bt_close is not None:
            bt_close.setDefault(True)

        # Connect events
        self.btSelectAll.clicked.connect(lambda: self.select('all'))
        self.btSelectNone.clicked.connect(lambda: self.select('none'))
        self.btSelectInvert.clicked.connect(lambda: self.select('invert'))
        self.treeDatabases.currentItemChanged.connect(self.update_description)
        self.treeDatabases.itemChanged.connect(self.check_selection)
        self.treeDatabases.itemDoubleClicked.connect(
            lambda item: item.setCheckState(0, Qt.Checked if item.checkState(0) == Qt.Unchecked else Qt.Unchecked))
        self.btDownload.clicked.connect(self.download_databases)
        self.btRefresh.clicked.connect(self.refresh_list)

        self.refresh_list()

    def refresh_list(self):
        self.btRefresh.setEnabled(False)
        self.treeDatabases.clear()
        self.treeDatabases.setLoading(True)

        self._workers.append(self.prepare_populate_list_worker())

        self._workers.start()

    def prepare_populate_list_worker(self):
        # Create worker to populate list and start it
        def update_list(dict_item):
            items = self.treeDatabases.findItems(dict_item['origin'], Qt.MatchExactly)
            if len(items) == 0:
                parent = QTreeWidgetItem(self.treeDatabases, [dict_item['origin']])
                self.treeDatabases.addTopLevelItem(parent)
            else:
                parent = items[0]
                del items

            item = QTreeWidgetItem(parent, [dict_item['name']])
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, DownloadDatabasesDialog.IdsRole, dict_item['ids'])
            item.setData(0, DownloadDatabasesDialog.DescRole, dict_item['desc'])
            item.setData(0, DownloadDatabasesDialog.OriginRole, dict_item['origin'])
            self.treeDatabases.addTopLevelItem(item)

        def clean_up():
            self.treeDatabases.setLoading(False)
            self.btRefresh.setEnabled(True)

        worker = ListDatabasesWorker(get_db_sources())
        worker.itemReady.connect(update_list)
        worker.error.connect(clean_up)
        worker.error.connect(self.on_error)
        worker.finished.connect(clean_up)

        return worker

    def on_error(self, e):
        if isinstance(e, ConnectionError):
            self.close()
            QMessageBox.warning(self, None,
                                'Connection failed. Please check your network connection.')
        elif isinstance(e, ftplib.all_errors) or isinstance(e, RequestException):
            if hasattr(e, 'name') and e.name is not None:
                QMessageBox.warning(self, None,
                                    f'Connection failed while downloading {e.name} database.\n'
                                    f'Please check your network connection.\n{str(e)}')
            else:
                QMessageBox.warning(self, None,
                                    f'Connection failed. Please check your network connection.\n{str(e)}')
        elif isinstance(e, NotImplementedError):
            QMessageBox.warning(self, None, "File format is not supported.")
        else:
            QMessageBox.warning(self, None, str(e))

    def select(self, type_):
        for i in range(self.treeDatabases.topLevelItemCount()):
            parent = self.treeDatabases.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if type_ == 'all':
                    child.setCheckState(0, Qt.Checked)
                elif type_ == 'none':
                    child.setCheckState(0, Qt.Unchecked)
                elif type_ == 'invert':
                    child.setCheckState(0, Qt.Checked if child.checkState(0) == Qt.Unchecked else Qt.Unchecked)

    def get_ids(self, selected_only: bool = False, origin: list = []):
        ids = {}
        for i in range(self.treeDatabases.topLevelItemCount()):
            parent = self.treeDatabases.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if not selected_only or child.checkState(0) == Qt.Checked:
                    orig = child.data(0, DownloadDatabasesDialog.OriginRole)
                    name = child.data(0, Qt.DisplayRole)
                    for id_ in child.data(0, DownloadDatabasesDialog.IdsRole):
                        if id_ is not None and (not origin or orig in origin):
                            if orig not in ids:
                                ids[orig] = {}
                            if name not in ids[orig]:
                                ids[orig][name] = []
                            ids[orig][name].append(id_)

        return ids

    def check_selection(self, item):
        if item.checkState(0):
            self.btDownload.setEnabled(True)
        else:
            enabled = False
            for i in range(self.treeDatabases.topLevelItemCount()):
                parent = self.treeDatabases.topLevelItem(i)
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    if child.checkState(0):
                        enabled = True
                        break
            self.btDownload.setEnabled(enabled)

    # noinspection PyUnusedLocal
    def update_description(self, current, previous):
        if current is not None:
            desc = current.data(0, DownloadDatabasesDialog.DescRole)
            self.labelDesc.setText(desc)

    def setEnabled(self, enabled):
        self.treeDatabases.setEnabled(enabled)
        self.btDownload.setEnabled(enabled)
        self.btSelectAll.setEnabled(enabled)
        self.btSelectNone.setEnabled(enabled)
        self.btSelectInvert.setEnabled(enabled)

    def download_databases(self):
        self.setEnabled(False)

        try:
            os.makedirs(self.base_path, exist_ok=True)
        except PermissionError:
            QMessageBox.critical(self, None,
                                'Unable to download databases because the destination folder is not writable.')
            return False

        ids = self.get_ids(selected_only=True)
        if len(ids) == 0:
            QMessageBox.warning(self, None,
                                'Please select at least one database first.')
            return False

        # noinspection PyShadowingNames
        def create_convert_databases_worker(worker: DownloadDatabasesWorker, ids):
            downloaded, unreachable = worker.result()

            if any(unreachable.values()):
                msg = ["{}: {}".format(origin, ", ".join(names)) for origin, names in unreachable.items()]
                QMessageBox.warning(self, None,
                                    "One or more databases were not accessible on the remote server(s):\n{}"
                                    .format("\n".join(msg)))

            if any(downloaded.values()):
                to_be_converted = {}
                for origin, values in ids.items():
                    for name, ids in values.items():
                        if name in downloaded[origin]:
                            if origin in to_be_converted:
                                to_be_converted[origin][name] = ids
                            else:
                                to_be_converted[origin] = {name: ids}

                return self.prepare_convert_databases_worker(to_be_converted)

        worker = self.prepare_download_databases_worker(ids)
        self._workers.append(worker)
        # noinspection PyShadowingNames
        self._workers.append(lambda worker, ids=ids: create_convert_databases_worker(worker, ids))
        self._workers.start()

    def prepare_download_databases_worker(self, ids):
        def clean_up():
            self.setEnabled(True)

        worker = DownloadDatabasesWorker(ids, self.base_path, get_db_sources())
        worker.error.connect(clean_up)
        worker.error.connect(self.on_error)
        worker.canceled.connect(clean_up)
        return worker

    def prepare_convert_databases_worker(self, ids):
        def clean_up():
            self.setEnabled(True)

        def conversion_finished():
            nonlocal worker
            converted_ids = worker.result()

            clean_up()

            # noinspection PyShadowingNames
            num_converted = sum(len(ids) for origin, ids in converted_ids.items())
            if num_converted > 0:
                QMessageBox.information(self, None,
                                        f"{num_converted} librar{'y' if num_converted == 1 else 'ies'} "
                                        "successfully downloaded.")
            else:
                QMessageBox.warning(self, None, "No library downloaded.")

        worker = ConvertDatabasesWorker(ids, output_path=self.base_path)
        worker.error.connect(clean_up)
        worker.error.connect(self.on_error)
        worker.canceled.connect(clean_up)
        worker.finished.connect(conversion_finished)
        return worker

    def getValues(self):
        return
