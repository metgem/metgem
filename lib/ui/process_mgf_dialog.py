import os
import sys
import csv

from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox, QCompleter, QFileSystemModel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QDir, QSignalMapper
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'process_mgf_dialog.ui')

ProcessMgfDialogUI, ProcessMgfDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
from .widgets import TSNEOptionsWidget, NetworkOptionsWidget, CosineOptionsWidget
from ..ui.import_metadata_dialog import ImportMetadataDialog
from ..workers.read_metadata import ReadMetadataOptions


class ProcessMgfDialog(ProcessMgfDialogBase, ProcessMgfDialogUI):
    """Create and open a dialog to process a new .mgf file.

    Creates a dialog containing 4 widgets:
        -file opening widget: to select a .mgf file to process and a .txt meta data file
        -CosineComputationOptions containing widget: to modify the cosine computation parameters
        -NetworkVisualizationOptions containing widget: to modify the Network visualization parameters
        -TSNEVisualizationOptions containing widget: to modify the TSNE visualization parameters

    If validated:   - the entered parameters are selected as default values for the next actions.
                    - the cosine score computing is started
                    - upon cosine score computation validation, Network and TSNE vilsualizations are created

    """

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._metadata_options = ReadMetadataOptions()

        self.setupUi(self)
        self.btBrowseProcessFile.setFocus()
        self.gbMetadata.setChecked(False)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        # Set completer for input files
        for edit in (self.editProcessFile, self.editMetadataFile):
            completer = QCompleter(edit)
            if sys.platform.startswith('win'):
                completer.setCaseSensitivity(Qt.CaseInsensitive)
            model = QFileSystemModel(completer)
            model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
            if edit == self.editProcessFile:
                model.setNameFilterDisables(False)
                model.setNameFilters(['*.mgf'])
            model.setRootPath(QDir.currentPath())
            completer.setModel(model)
            edit.setText(QDir.currentPath())
            edit.setCompleter(completer)

        # Add options widgets
        self.cosine_widget = CosineOptionsWidget()
        self.tsne_widget = TSNEOptionsWidget()
        self.network_widget = NetworkOptionsWidget()

        self.layout().addWidget(self.cosine_widget, self.layout().count()-1, 0)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.network_widget)
        layout.addWidget(self.tsne_widget)

        if options:
            self.cosine_widget.setValues(options.cosine)
            self.tsne_widget.setValues(options.tsne)
            self.network_widget.setValues(options.network)

        self.wgAdvancedOptions.setLayout(layout)

        # Add advanced option button
        self.btMore = self.buttonBox.addButton("&More >>", QDialogButtonBox.DestructiveRole)

        # Connect events
        self._mapper = QSignalMapper(self)
        self.btBrowseProcessFile.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btBrowseProcessFile, 'process')
        self.btBrowseMetadataFile.clicked.connect(self._mapper.map)
        self._mapper.setMapping(self.btBrowseMetadataFile, 'metadata')
        self._mapper.mapped[str].connect(self.browse)
        self.editMetadataFile.textChanged.connect(self.on_metadata_file_changed)
        self.btMore.clicked.connect(self.toggle_advanced_options)
        self.btOptions.clicked.connect(self.on_show_options_dialog)
        self.cbCsvDelimiter.delimiterChanged.connect(self.on_delimiter_changed)

    def on_delimiter_changed(self, delimiter):
        self._metadata_options.sep = delimiter

    def on_show_options_dialog(self):
        delimiter = self.cbCsvDelimiter.delimiter()
        dialog = ImportMetadataDialog(self, filename=self.editMetadataFile.text(), delimiter=delimiter)
        if dialog.exec_() == QDialog.Accepted:
            filename, options = dialog.getValues()
            self.editMetadataFile.setText(filename)
            self.cbCsvDelimiter.setDelimiter(options.sep)
            self._metadata_options = options

    def on_metadata_file_changed(self, text):
        # Check that selected metadata file is a valid csv file and try to get delimiter
        try:
            with open(text, 'r') as f:
                line = f.readline()
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(line).delimiter
        except (OSError, FileNotFoundError, csv.Error, UnicodeDecodeError):
            return
        else:
            self.cbCsvDelimiter.setDelimiter(delimiter)

    def done(self, r):
        if r == QDialog.Accepted:
            process_file = self.editProcessFile.text()
            metadata_file = self.editMetadataFile.text()
            if len(process_file) > 0 and os.path.exists(process_file) and os.path.splitext(process_file)[1] == '.mgf':
                if not self.gbMetadata.isChecked() or (os.path.exists(metadata_file) and os.path.isfile(metadata_file)):
                    super().done(r)
                else:
                    self.editMetadataFile.setPalette(self._error_palette)
            else:
                self.editProcessFile.setPalette(self._error_palette)
        else:
            super().done(r)

    def showEvent(self, event):
        self.wgAdvancedOptions.hide()
        self.adjustSize()
        super().showEvent(event)

    def toggle_advanced_options(self):
        """Toggle the Network and t-SNE parameters widgets"""

        if self.wgAdvancedOptions.isVisible():
            self.wgAdvancedOptions.hide()
            self.btMore.setText("&More >>")
        else:
            self.wgAdvancedOptions.show()
            self.btMore.setText("<< &Less")

        self.adjustSize()

    def browse(self, type_='process'):
        """Open a dialog to file either .mgf or metadata.txt file"""

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)

        if type_ == 'process':
            dialog.setNameFilters(["MGF Files (*.mgf)", "All files (*.*)"])
        elif type_ == 'metadata':
            dialog.setNameFilters(["Metadata File (*.csv; *.tsv; *.txt)", "All files (*.*)"])

        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            if type_ == 'process':
                self.editProcessFile.setText(filename)
                self.editProcessFile.setPalette(self.style().standardPalette())
            else:
                self.editMetadataFile.setText(filename)
                self.editMetadataFile.setPalette(self.style().standardPalette())

    def getValues(self):
        """Returns files to process and options"""

        metadata_file = self.editMetadataFile.text() if os.path.isfile(self.editMetadataFile.text()) else None
        return (self.editProcessFile.text(),
                self.gbMetadata.isChecked(),  metadata_file,
                self._metadata_options, self.cosine_widget.getValues(),
                self.tsne_widget.getValues(), self.network_widget.getValues())
