import os
import sys

from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox, QCompleter, QFileSystemModel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QDir
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'open_file_dialog.ui')

if __name__ == '__main__':
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE)
    from widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget


    class CosineComputationOptions:
        pass
else:
    OpenFileDialogUI, OpenFileDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')
    from .widgets.options_widgets import TSNEOptionWidget, NetworkOptionWidget
    from ..workers import CosineComputationOptions


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

    def __init__(self, *args, folder=None, options=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        # Set completer for input files
        for edit in (self.editProcessFile, self.editMetadataFile):
            completer = QCompleter(edit)
            if sys.platform == 'win32':
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

        # Add advanced option button
        self.btMore = self.buttonBox.addButton("&More", QDialogButtonBox.ActionRole)

        # Add options widgets
        self.tsne_widget = TSNEOptionWidget()
        self.network_widget = NetworkOptionWidget()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.network_widget)
        layout.addWidget(self.tsne_widget)

        if options:
            self.tsne_widget.setValues(options.tsne)
            self.network_widget.setValues(options.network)

        self.wgAdvancedOptions.setLayout(layout)

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))
        self.btMore.clicked.connect(self.toggle_advanced_options)

    def done(self, r):
        if r == QDialog.Accepted:
            process_file = self.editProcessFile.text()
            metadata_file = self.editMetadataFile.text()
            if len(process_file) > 0 and os.path.exists(process_file) and os.path.splitext(process_file)[1] == '.mgf':
                if len(metadata_file) == 0 or os.path.exists(metadata_file):
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

    def toggle_advanced_options(self):
        """Toggle the Network and t-SNE parameters widgets"""

        if self.wgAdvancedOptions.isVisible():
            self.wgAdvancedOptions.hide()
            self.btMore.setText("&More")
        else:
            self.wgAdvancedOptions.show()
            self.btMore.setText("&Less")

        self.adjustSize()

    def browse(self, type='process'):
        """Open a dialog to file either .mgf or metadata.txt file"""

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)

        if type == 'process':
            dialog.setNameFilters(["MGF Files (*.mgf)", "All files (*.*)"])
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()[0]
            if type == 'process':
                self.editProcessFile.setText(filename)
                self.editProcessFile.setPalette(self.style().standardPalette())
            else:
                self.editMetadataFile.setText(filename)
                self.editMetadataFile.setPalette(self.style().standardPalette())

    def getValues(self):
        """Returns files to process and options"""

        options = CosineComputationOptions()
        options.mz_tolerance = self.spinMZTolerance.value()
        options.min_intensity = self.spinMinIntensity.value()
        options.parent_filter_tolerance = self.spinParentFilterTolerance.value()
        options.min_matched_peaks = self.spinMinMatchedPeaks.value()

        return (self.editProcessFile.text(), self.editMetadataFile.text(),
                options, self.tsne_widget.getValues(),
                self.network_widget.getValues())


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = OpenFileDialog(folder=os.path.realpath(os.path.dirname(__file__)))

    if dialog.exec_() == QDialog.Accepted:
        print('You chose these files:', dialog.getValues())
