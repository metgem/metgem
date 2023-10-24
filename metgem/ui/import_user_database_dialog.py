import os

from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QCompleter, QFileSystemModel, QDialog, QFileDialog, QDialogButtonBox, QMessageBox

from metgem.ui.progress_dialog import ProgressDialog
from metgem.workers.databases import ConvertDatabasesWorker
from metgem.workers.core import WorkerQueue
from metgem.ui.import_user_database_dialog_ui import Ui_ImportUserDatabaseDialog


class ImportUserDatabaseDialog(QDialog, Ui_ImportUserDatabaseDialog):

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path

        self.setupUi(self)
        self.btBrowseInputFile.setFocus()

        self._dialog = None
        self._workers = WorkerQueue(self, ProgressDialog(self))

        # Add import button
        self.btImport = self.buttonBox.addButton("&Import", QDialogButtonBox.ActionRole)
        self.btImport.setIcon(QIcon(":/icons/images/import-database.svg"))
        self.btImport.setEnabled(False)

        # Set Close button as default
        bt_close = self.buttonBox.button(QDialogButtonBox.Close)
        if bt_close is not None:
            bt_close.setDefault(True)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        # Set completer for input files
        # TODO: completer makes the dialog freeze for seconds on show, disable it until fixed
        # completer = QCompleter(self.editInputFile)
        # if sys.platform.startswith('win'):
        #     completer.setCaseSensitivity(Qt.CaseInsensitive)
        # model = QFileSystemModel(completer)
        # model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        # model.setNameFilterDisables(False)
        # model.setNameFilters(['*.mgf', '*.msp'])
        # model.setRootPath(QDir.currentPath())
        # completer.setModel(model)
        self.editInputFile.setText(QDir.currentPath())
        # self.editInputFile.setCompleter(completer)

        # Connect events
        self.btBrowseInputFile.clicked.connect(self.browse)
        self.btImport.clicked.connect(self.import_database)
        self.editInputFile.textChanged.connect(self.check_import_possible)
        self.editDatabaseName.textChanged.connect(self.check_import_possible)

    def check_import_possible(self):
        self.btImport.setEnabled(len(self.editInputFile.text()) > 0 and len(self.editDatabaseName.text()) > 0)

    def browse(self):
        """Open a dialog to choose .mgf file"""

        self._dialog = QFileDialog(self)
        self._dialog.setFileMode(QFileDialog.ExistingFile)
        self._dialog.setNameFilters(["All supported formats (*.mgf *.msp)",
                               "Mascot Generic Format (*.mgf)",
                               "NIST Text Format of Individual Spectra (*.msp)",
                               "All files (*)"])

        def set_filename(result):
            if result == QDialog.Accepted:
                filename = self._dialog.selectedFiles()[0]
                self.editInputFile.setText(filename)
                self.editDatabaseName.setText(os.path.splitext(os.path.basename(filename))[0])
                self.editInputFile.setPalette(self.style().standardPalette())

        self._dialog.finished.connect(set_filename)
        self._dialog.open()

    def import_database(self):
        try:
            os.makedirs(self.base_path, exist_ok=True)
        except PermissionError:
            QMessageBox.critical(self, None,
                                'Unable to import database because the destination folder is not writable.')

        input_file = self.editInputFile.text()
        if len(input_file) == 0 or not os.path.exists(input_file) \
                or os.path.splitext(input_file)[1].lower() not in ('.mgf', '.msp'):
            self.editInputFile.setPalette(self._error_palette)

        name = self.editDatabaseName.text()
        if len(name) == 0:
            self.editDatabaseName.setPalette(self._error_palette)

        id_ = {'User': {name: [input_file]}}
        worker = self.prepare_convert_database_worker(id_)
        if worker is not None:
            self._workers.append(worker)
            self._workers.start()

    def prepare_convert_database_worker(self, id_):
        def error(e):
            if isinstance(e, NotImplementedError):
                QMessageBox.warning(self, None, "File format is not supported.")
            else:
                QMessageBox.warning(self, None, str(e))

        def finished():
            QMessageBox.information(self, None,
                                    "Database was successfully imported.")

        worker = ConvertDatabasesWorker(id_, output_path=self.base_path)
        worker.error.connect(error)
        worker.finished.connect(finished)
        return worker
