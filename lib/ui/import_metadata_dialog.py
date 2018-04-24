import os
import sys
import csv

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDir, QItemSelectionModel, QItemSelection
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QCompleter, QFileSystemModel, QDialog, QFileDialog, QTableWidgetItem

from ..utils import SignalBlocker
from ..workers import WorkerSet, ReadMetadataWorker, ReadMetadataOptions
from .progress_dialog import ProgressDialog

UI_FILE = os.path.join(os.path.dirname(__file__), 'import_metadata_dialog.ui')

try:
    ImportMetadataDialogUI, ImportMetadataDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
except:
    ImportMetadataDialogUI, ImportMetadataDialogBase = uic.loadUiType(UI_FILE)


class ImportMetadataDialog(ImportMetadataDialogBase, ImportMetadataDialogUI):

    def __init__(self, *args, filename=None, delimiter=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self._workers = WorkerSet(self, ProgressDialog(self))

        # Set completer for input files
        completer = QCompleter(self.editMetadataFile)
        if sys.platform.startswith('win'):
            completer.setCaseSensitivity(Qt.CaseInsensitive)
        model = QFileSystemModel(completer)
        model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        model.setRootPath(QDir.currentPath())
        completer.setModel(model)
        self.editMetadataFile.setCompleter(completer)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        # Connect Delimiter ComboBox to delimiter LineEdit
        self.cbCsvDelimiter.setOtherEditWidget(self.editCsvDelimiter)

        # Connect events
        self.btBrowseMetadataFile.clicked.connect(self.browse)
        self.chkComment.clicked.connect(lambda: self.editComment.setEnabled(self.chkComment.isChecked()))
        self.editMetadataFile.textChanged.connect(self.on_metadata_file_changed)
        self.cbCsvDelimiter.delimiterChanged.connect(self.populate_table)
        self.chkUseFirstLineAsHeader.clicked.connect(self.populate_table)
        self.spinSkipRows.valueChanged.connect(self.populate_table)
        self.editComment.textChanged.connect(self.populate_table)
        self.chkComment.clicked.connect(self.populate_table)
        self.btRefresh.clicked.connect(self.populate_table)
        self.chkComment.clicked.connect(self.populate_table)
        self.btSelectAll.clicked.connect(self.twMetadata.selectAll)
        self.btSelectNone.clicked.connect(self.twMetadata.clearSelection)
        self.btSelectInvert.clicked.connect(self.invert_selection)

        if delimiter is not None:
            with SignalBlocker(self.cbCsvDelimiter):
                self.cbCsvDelimiter.setDelimiter(delimiter)

        if filename is not None:
            self.editMetadataFile.setText(filename)

    def done(self, r):
        if r == QDialog.Accepted:
            metadata_file = self.editMetadataFile.text()
            if os.path.exists(metadata_file) and os.path.isfile(metadata_file):
                super().done(r)
            else:
                self.editMetadataFile.setPalette(self._error_palette)
        else:
            super().done(r)

    def browse(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters(["Metadata File (*.csv; *.tsv; *.txt; *.xls; *.xlsx)", "All files (*.*)"])

        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            with SignalBlocker(self.editMetadataFile):
                self.editMetadataFile.setText(filename)
            self.editMetadataFile.setPalette(self.style().standardPalette())
            self.on_metadata_file_changed(filename)

    def selection(self):
        model = self.twMetadata.model()
        first = model.index(0, 0)
        last = model.index(self.twMetadata.model().rowCount() - 1, self.twMetadata.model().columnCount() - 1)
        return QItemSelection(first, last)

    def selected_columns(self):
        return [index.column() for index in self.twMetadata.selectionModel().selectedColumns()]

    def invert_selection(self):
        self.twMetadata.selectionModel().select(self.selection(), QItemSelectionModel.Toggle)

    def on_metadata_file_changed(self, text):
        self.twMetadata.clear()

        # Check that selected metadata file is a valid csv file and try to get delimiter
        try:
            with open(text, 'r') as f:
                line = f.read(2048)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(line).delimiter
            has_header = sniffer.has_header(line)
        except (OSError, FileNotFoundError, csv.Error, UnicodeDecodeError):
            return
        else:
            with SignalBlocker(self.cbCsvDelimiter, self.chkUseFirstLineAsHeader):
                self.cbCsvDelimiter.setDelimiter(delimiter)
                self.chkUseFirstLineAsHeader.setChecked(has_header)
        finally:
            self.populate_table()

    def populate_table(self):
        def file_read():
            nonlocal worker
            data = worker.result()
            self.twMetadata.clear()
            self.twMetadata.setRowCount(0)

            if data is None:
                self.twMetadata.setLoading(False)
                return

            if data.shape[0] == 0 or data.shape[1] == 0:
                self.twMetadata.setLoading(False)
                return

            try:
                self.twMetadata.setRowCount(data.shape[0])
                self.twMetadata.setColumnCount(data.shape[1])
                self.twMetadata.setHorizontalHeaderLabels(data.columns)
                for row in range(data.shape[0]):
                    for column in range(data.shape[1]):
                        item = QTableWidgetItem(str(data.loc[row][column]))
                        self.twMetadata.setItem(row, column, item)
            except KeyError:
                self.twMetadata.clear()
                self.twMetadata.setRowCount(0)
                self.twMetadata.setColumnCount(0)
            finally:
                self.twMetadata.setLoading(False)

        options = self.prepare_options(preview=True)
        if options is not None:
            worker = ReadMetadataWorker(self.editMetadataFile.text(), options, track_progress=False)
            if worker is not None:
                worker.finished.connect(file_read)
                worker.error.connect(lambda: self.twMetadata.setLoading(False))
                self.twMetadata.setLoading(True)
                self._workers.add(worker)

    def prepare_options(self, preview=True):
        delimiter = self.cbCsvDelimiter.delimiter()
        if delimiter is not None:
            options = ReadMetadataOptions()
            options.sep = delimiter
            options.header = 'infer' if self.chkUseFirstLineAsHeader.isChecked() else None
            options.comment = self.editComment.text() if self.chkComment.isChecked() else ''
            options.comment = options.comment if len(options.comment) == 1 else None
            options.skiprows = self.spinSkipRows.value() - 1

            if preview:
                options.nrows = 100
            else:
                selected_cols = self.selected_columns()
                options.usecols = selected_cols if len(selected_cols) > 0 else None
            return options

    def getValues(self):
        return self.editMetadataFile.text(), self.prepare_options(preview=False)
