import os
import sys
import csv

from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox, QCompleter, QFileSystemModel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QDir, QSignalMapper
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'open_file_dialog.ui')

OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
from .widgets import TSNEOptionsWidget, NetworkOptionsWidget, CosineOptionsWidget


class OpenFileDialog(OpenFileDialogBase, OpenFileDialogUI):
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
        self.editMetadataFile.textChanged.connect(self.check_metadata_file_type)
        self.btMore.clicked.connect(self.toggle_advanced_options)

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
            dialog.setMimeTypeFilters(['text/plain', 'text/csv'])

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

        return (self.editProcessFile.text(),
                self.gbMetadata.isChecked(),  self.editMetadataFile.text(),
                self.editCsvSeparator.text(), self.cosine_widget.getValues(), 
                self.tsne_widget.getValues(), self.network_widget.getValues())

    def check_metadata_file_type(self, text):
        """Check that selected metadata file is a valid csv file and try to get delimiter"""
        try:
            with open(text, 'r') as f:
                line = f.readline()
            delimiter = csv.Sniffer().sniff(line).delimiter
        except (OSError, FileNotFoundError):
            enabled = False
        else:
            enabled = True
        finally:
            self.editCsvSeparator.setText(delimiter)
            self.editCsvSeparator.setEnabled(enabled)
            self.labelCsvSeparator.setEnabled(enabled)
