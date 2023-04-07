import os
import sys
from typing import Dict, List

from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QCompleter, QFileSystemModel, QDialog, QFileDialog, QListWidget

from .progress_dialog import ProgressDialog
from ..workers.core import WorkerQueue
from .export_db_results_dialog_ui import Ui_Dialog


class ExportDBResultsDialog(QDialog, Ui_Dialog):

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self._dialog = None
        self._workers = WorkerQueue(self, ProgressDialog(self))

        self._dialog = None

        # Set completer for output files
        completer = QCompleter(self.editExportFile)
        if sys.platform.startswith('win'):
            completer.setCaseSensitivity(Qt.CaseInsensitive)
        model = QFileSystemModel(completer)
        model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        model.setRootPath(QDir.currentPath())
        completer.setModel(model)
        self.editExportFile.setCompleter(completer)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        self.cbFieldSeparator.setOtherEditWidget(self.editFieldSeparator)
        self.cbFieldSeparator.setCurrentText("Semicolon (;)")

        # Connect events
        self.btBrowseExportFile.clicked.connect(self.browse)
        self.btSelectAllStandards.clicked.connect(lambda: self.select(self.lstStandards, 'all'))
        self.btSelectNodeStandards.clicked.connect(lambda: self.select(self.lstStandards, 'none'))
        self.btInvertSelectionStandards.clicked.connect(lambda: self.select(self.lstStandards, 'invert'))
        self.btSelectAllAnalogs.clicked.connect(lambda: self.select(self.lstAnalogs, 'all'))
        self.btSelectNodeAnalogs.clicked.connect(lambda: self.select(self.lstAnalogs, 'none'))
        self.btInvertSelectionAnalogs.clicked.connect(lambda: self.select(self.lstAnalogs, 'invert'))
        self.editExportFile.textChanged.connect(self.validate_export_filename)
        self.editFieldSeparator.textChanged.connect(self.validate_separator)

    def validate_export_filename(self):
        output_file = self.editExportFile.text()
        if os.access(os.path.dirname(output_file), os.W_OK):
            self.editExportFile.setPalette(self.style().standardPalette())
            return True
        else:
            self.editExportFile.setPalette(self._error_palette)
            return False

    def validate_separator(self):
        if self.cbFieldSeparator.currentIndex() < self.cbFieldSeparator.count()\
                or len(self.editFieldSeparator.text()) == 1:
            self.editFieldSeparator.setPalette(self.style().standardPalette())
            return True
        else:
            self.editFieldSeparator.setPalette(self._error_palette)
            return False

    def done(self, r):
        if r == QDialog.DialogCode.Accepted:
            if self.validate_export_filename() and self.validate_separator():
                super().done(r)
        else:
            super().done(r)

    def browse(self):
        self._dialog = QFileDialog(self)
        self._dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self._dialog.setNameFilters(["Comma separated values (*.csv *.tsv *.txt)"])

        def set_filename(result):
            if result == QDialog.DialogCode.Accepted:
                filename = self._dialog.selectedFiles()[0]
                self.editExportFile.setText(filename)

        self._dialog.finished.connect(set_filename)
        self._dialog.open()

    def select(self, list_widget: QListWidget, type_: str):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if type_ == 'all':
                item.setCheckState(Qt.Checked)
            elif type_ == 'none':
                item.setCheckState(Qt.Unchecked)
            elif type_ == 'invert':
                item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)

    def getValues(self) -> (str, str, int, Dict[str, List[str]]):
        attributes = {'standards': [], 'analogs': []}
        for type_, list_widget in (('standards', self.lstStandards),
                                   ('analogs', self.lstAnalogs)):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    attributes[type_].append(item.data(Qt.DisplayRole))

        return self.editExportFile.text(), self.cbFieldSeparator.delimiter(), self.spinNumHits.value(), attributes
