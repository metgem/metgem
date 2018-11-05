from .widgets import AutoToolTipItemDelegate
from ..workers import WorkerSet
from ..workers import (ListDatabasesWorker, DownloadDatabasesWorker,
                       GetGNPSDatabasesMtimeWorker, ConvertDatabasesWorker)
from .progress_dialog import ProgressDialog

import os
from datetime import datetime

from requests.exceptions import ConnectionError, RequestException
import ftplib

from PyQt5.QtWidgets import QListWidgetItem, QDialogButtonBox, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'download_databases_dialog.ui')

DownloadDatabasesDialogUI, DownloadDatabasesDialogBase = uic.loadUiType(UI_FILE,
                                                                        from_imports='lib.ui',
                                                                        import_from='lib.ui')


class DownloadDatabasesDialog(DownloadDatabasesDialogUI, DownloadDatabasesDialogBase):
    IdsRole = Qt.UserRole + 1
    DescRole = Qt.UserRole + 2
    OriginRole = Qt.UserRole + 3

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.lstDatabases.setIconSize(QSize(12, 12))
        self.lstDatabases.setFocus()
        self.lstDatabases.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lstDatabases.setItemDelegate(AutoToolTipItemDelegate())

        self._workers = WorkerSet(self, ProgressDialog(self))
        self._mtimes = {}

        # Add download button
        self.btDownload = self.buttonBox.addButton("&Download", QDialogButtonBox.ActionRole)
        self.btDownload.setIcon(QIcon(":/icons/images/download-package.svg"))
        self.btDownload.setEnabled(False)

        # Set Close button as default
        btClose = self.buttonBox.button(QDialogButtonBox.Close)
        if btClose is not None:
            btClose.setDefault(True)

        # Connect events
        self.btSelectAll.clicked.connect(lambda: self.select('all'))
        self.btSelectNone.clicked.connect(lambda: self.select('none'))
        self.btSelectInvert.clicked.connect(lambda: self.select('invert'))
        self.lstDatabases.currentItemChanged.connect(self.update_description)
        self.lstDatabases.itemChanged.connect(self.check_selection)
        self.lstDatabases.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked))
        self.btDownload.clicked.connect(self.download_databases)
        self.btRefresh.clicked.connect(self.refresh_list)

        self.refresh_list()

    def refresh_list(self):
        self.btRefresh.setEnabled(False)
        self.lstDatabases.clear()
        self.lstDatabases.setLoading(True)

        worker = self.prepare_populate_list_worker()
        self._workers.add(worker)

    def prepare_populate_list_worker(self):
        # Create worker to populate list and start it
        def update_list(dict_item):
            item = QListWidgetItem(dict_item['name'])
            item.setCheckState(Qt.Unchecked)
            item.setData(DownloadDatabasesDialog.IdsRole, dict_item['ids'])
            item.setData(DownloadDatabasesDialog.DescRole, dict_item['desc'])
            item.setData(DownloadDatabasesDialog.OriginRole, dict_item['origin'])
            self.lstDatabases.addItem(item)

        def process_finished():
            self.lstDatabases.setLoading(False)
            self.btRefresh.setEnabled(True)
            worker = self.prepare_get_mtimes_worker()
            self._workers.add(worker)

        worker = ListDatabasesWorker()
        worker.itemReady.connect(update_list)
        worker.error.connect(self.on_error)
        worker.finished.connect(process_finished)

        return worker

    def prepare_get_mtimes_worker(self):
        def process_finished():
            self._mtimes = worker.result()
            self.update_badges()

        ids = self.get_ids(origin=['GNPS'])
        worker = GetGNPSDatabasesMtimeWorker(ids)
        worker.finished.connect(process_finished)

        return worker

    def on_error(self, e):
        if isinstance(e, ConnectionError):
            self.close()
            QMessageBox.warning(self, None,
                                'Connection failed. Please check your network connection.')
        elif isinstance(e, ftplib.all_errors) or isinstance(e, RequestException):
            if hasattr(e.id) and e.id is not None:
                QMessageBox.warning(self, None,
                                    f'Connection failed while downloading {e.id} database.\n'
                                    f'Please check your network connection.\n{str(e)}')
            else:
                QMessageBox.warning(self, None,
                                    f'Connection failed. Please check your network connection.\n{str(e)}')
        else:
            QMessageBox.warning(self, None, str(e))

    def select(self, type_):
        for i in range(self.lstDatabases.count()):
            item = self.lstDatabases.item(i)
            if type_ == 'all':
                item.setCheckState(Qt.Checked)
            elif type_ == 'none':
                item.setCheckState(Qt.Unchecked)
            elif type_ == 'invert':
                item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)

    def get_ids(self, selected_only: bool=False, origin: list=[]):
        items = [self.lstDatabases.item(i) for i in range(self.lstDatabases.count())
                 if not selected_only or self.lstDatabases.item(i).checkState() == Qt.Checked]
        ids = [id_ for item in items for id_ in item.data(DownloadDatabasesDialog.IdsRole)
               if item.data(DownloadDatabasesDialog.IdsRole) is not None and
               (not origin or item.data(DownloadDatabasesDialog.OriginRole) in origin)]
        return ids

    def check_selection(self, item):
        if item.checkState():
            self.btDownload.setEnabled(True)
        else:
            enabled = False
            for i in range(self.lstDatabases.count()):
                if self.lstDatabases.item(i).checkState():
                    enabled = True
                    break
            self.btDownload.setEnabled(enabled)

    def update_description(self, current, previous):
        if current is not None:
            desc = current.data(DownloadDatabasesDialog.DescRole)
            self.labelDesc.setText(desc)

    def update_badges(self):
        if not self._mtimes:
            return False

        for i in range(self.lstDatabases.count()):
            item = self.lstDatabases.item(i)
            ids = item.data(DownloadDatabasesDialog.IdsRole)
            if ids is None:
                continue
            for id_ in ids:
                if id_ in self._mtimes:
                    path = os.path.join(self.base_path, f'{id_}.mgf')
                    if os.path.exists(path):
                        if datetime.fromtimestamp(os.path.getmtime(path)) < self._mtimes[id_]:
                            item.setIcon(QIcon(":/icons/images/update-available.svg"))
                        else:
                            item.setIcon(QIcon())
                    else:
                        item.setIcon(QIcon(":/icons/images/new.svg"))

    def setEnabled(self, enabled):
        self.lstDatabases.setEnabled(enabled)
        self.btDownload.setEnabled(enabled)
        self.btSelectAll.setEnabled(enabled)
        self.btSelectNone.setEnabled(enabled)
        self.btSelectInvert.setEnabled(enabled)

    def download_databases(self):
        self.setEnabled(False)

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        ids = self.get_ids(selected_only=True)
        if len(ids) == 0:
            QMessageBox.warning(self, None,
                                'Please select at least one database first.')
            return False

        worker = self.prepare_download_databases_worker(ids)
        if worker is not None:
            self._workers.add(worker)

    def prepare_download_databases_worker(self, ids):
        def clean_up():
            self.setEnabled(True)
            self.update_badges()

        def download_finished():
            nonlocal worker

            self.update_badges()
            downloaded_ids, unreachable_ids = worker.result()

            if unreachable_ids:
                QMessageBox.warning(self, None,
                                    "One or more databases were not accessible in the remote server:\n{}"
                                    .format(", ".join(unreachable_ids)))

            if downloaded_ids:
                worker = self.prepare_convert_databases_worker(downloaded_ids)
                if worker is not None:
                    self._workers.add(worker)

        worker = DownloadDatabasesWorker(ids, self.base_path)
        worker.error.connect(clean_up)
        worker.error.connect(self.on_error)
        worker.finished.connect(download_finished)
        worker.canceled.connect(clean_up)
        return worker

    def prepare_convert_databases_worker(self, ids):
        def clean_up():
            self.setEnabled(True)
            self.update_badges()

        def conversion_finished():
            nonlocal worker
            converted_ids = worker.result()

            clean_up()

            num_converted = len(converted_ids)
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
