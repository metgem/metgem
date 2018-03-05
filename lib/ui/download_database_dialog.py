import os
from datetime import datetime

from requests.exceptions import ConnectionError
import ftplib

from PyQt5.QtWidgets import QListWidgetItem, QDialogButtonBox, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSignalMapper, QSize
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'download_database_dialog.ui')

from ..database import DataBaseBuilder
from ..utils import WorkerSet
from ..workers import ListGNPSDatabasesWorker, DownloadGNPSDatabasesWorker, GetGNPSDatabasesMtimeWorker

DownloadDatabaseDialogUI, DownloadDatabaseDialogBase = uic.loadUiType(UI_FILE,
                                                                      from_imports='lib.ui',
                                                                      import_from='lib.ui')


class DownloadDatabaseDialog(DownloadDatabaseDialogUI, DownloadDatabaseDialogBase):
    IDS_ROLE = Qt.UserRole + 1
    DESC_ROLE = Qt.UserRole + 2

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path

        self.setupUi(self)
        self.widgetProgress.setVisible(False)

        self.lstDatabases.setIconSize(QSize(12, 12))

        self._workers = WorkerSet(self)
        self._mtimes = None

        # Add download button
        self.btDownload = self.buttonBox.addButton("&Download", QDialogButtonBox.ActionRole)

        # Create worker to populate list and start it
        def update_list(dict_item):
            item = QListWidgetItem(dict_item['name'])
            item.setToolTip(dict_item['name'])
            item.setCheckState(Qt.Unchecked)
            item.setData(DownloadDatabaseDialog.IDS_ROLE, dict_item['ids'])
            item.setData(DownloadDatabaseDialog.DESC_ROLE, dict_item['desc'])
            self.lstDatabases.addItem(item)

        def process_finished():
            worker = self.prepare_get_mtimes_worker()
            self._workers.add(worker)

        worker = ListGNPSDatabasesWorker()
        worker.updated.connect(update_list)
        worker.error.connect(self.on_error)
        worker.finished.connect(process_finished)
        self._workers.add(worker)

        # Connect events
        self._mapper = QSignalMapper(self)
        self.btSelectAll.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btSelectAll, 'all')
        self.btSelectNone.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btSelectNone, 'none')
        self.btSelectInvert.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btSelectInvert, 'invert')
        self._mapper.mapped[str].connect(self.select)

        self.lstDatabases.currentItemChanged.connect(self.update_description)
        self.btDownload.clicked.connect(self.download_databases)

    def prepare_get_mtimes_worker(self):
        def process_finished():
            self._mtimes = worker.result()
            self.update_badges()

        ids = self.get_ids()
        worker = GetGNPSDatabasesMtimeWorker(ids)
        worker.finished.connect(process_finished)

        return worker

    def on_error(self, e):
        if isinstance(e, ConnectionError):
            self.close()
            dialog = QMessageBox()
            dialog.warning(self, None,
                           'Connection failed. Please check your network connection.')
        elif isinstance(e, ftplib.all_errors):
            dialog = QMessageBox()
            dialog.warning(self, None,
                           f'Connection failed. Please check your network connection.\n{str(e)}')

    def select(self, type_):
        for i in range(self.lstDatabases.count()):
            item = self.lstDatabases.item(i)
            if type_ == 'all':
                item.setCheckState(Qt.Checked)
            elif type_ == 'none':
                item.setCheckState(Qt.Unchecked)
            elif type_ == 'invert':
                item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)

    def get_ids(self, selected_only=False):
        items = [self.lstDatabases.item(i) for i in range(self.lstDatabases.count())
                 if not selected_only or self.lstDatabases.item(i).checkState() == Qt.Checked]
        ids = [id_ for item in items for id_ in item.data(DownloadDatabaseDialog.IDS_ROLE)
                 if item.data(DownloadDatabaseDialog.IDS_ROLE) is not None]
        return ids

    def update_description(self, current, previous):
        desc = current.data(DownloadDatabaseDialog.DESC_ROLE)
        self.labelDesc.setText(desc)

    def update_badges(self):
        if self._mtimes is None:
            return False

        for i in range(self.lstDatabases.count()):
            item = self.lstDatabases.item(i)
            ids = item.data(DownloadDatabaseDialog.IDS_ROLE)
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

    def download_databases(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        ids = self.get_ids(selected_only=True)
        if len(ids) == 0:
            dialog = QMessageBox()
            dialog.warning(self, None,
                           'Please select at least one database first.')
            return False

        def update_filesizes(dict_sizes):
            self.progressBar.setMaximum(sum(dict_sizes.values()))

        def update_progress(i):
            self.progressBar.setValue(self.progressBar.value() + i)

        self.progressBar.setValue(0)
        worker = DownloadGNPSDatabasesWorker(ids, self.base_path)
        worker.filesizes_ready.connect(update_filesizes)
        worker.updated.connect(update_progress)
        worker.error.connect(self.on_error)
        worker.finished.connect(self.update_badges)
        self._workers.add(worker)

        # self.convert_databases()

    def convert_databases(self):
        with DataBaseBuilder(os.path.join(self.base_path, 'spectra')) as db:
            items = [self.lstDatabases.item(i) for i in range(self.lstDatabases.count())
                     if self.lstDatabases.item(i).checkState() == Qt.Checked]
            ids = [id_ for item in items for id_ in item.data(DownloadDatabaseDialog.IDS_ROLE)
                   if item.data(DownloadDatabaseDialog.IDS_ROLE) is not None]
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(ids))
            self.progressBar.setValue(0)

            for i, id_ in enumerate(ids):
                path = f'databases/{id_}.mgf'
                if os.path.exists(path):
                    db.add_bank(path)
                self.progressBar.setFormat(f'Converting: {id_}')
                self.progressBar.setValue(i)

    def getValues(self):
        return None
