import csv
import os
import sys

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDir, QSize
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QFileDialog, QDialog, QCompleter, QFileSystemModel, QMenu, \
    QListWidgetItem, QMessageBox

from .widgets import CosineOptionsWidget, AVAILABLE_NETWORK_WIDGETS
from ..ui.import_metadata_dialog import ImportMetadataDialog
from ..workers.read_metadata import ReadMetadataOptions

UI_FILE = os.path.join(os.path.dirname(__file__), 'process_data_dialog.ui')

ProcessDataDialogUI, ProcessDataDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')


class ProcessDataDialog(ProcessDataDialogBase, ProcessDataDialogUI):
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
    NameRole = Qt.UserRole + 1

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._metadata_options = ReadMetadataOptions()
        self._options = options

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
                model.setNameFilters(['*.mgf', '*.msp'])
            model.setRootPath(QDir.currentPath())
            completer.setModel(model)
            edit.setCompleter(completer)
            edit.setText(QDir.currentPath())

        # Add cosine options widget
        self.cosine_widget = CosineOptionsWidget()
        self.layout().addWidget(self.cosine_widget, self.layout().count()-2, 0)

        if options:
            self.cosine_widget.setValues(options.cosine)

        # Build menu to add views
        menu = QMenu()
        self.btAddView.setMenu(menu)
        set_default = True
        for view_class in AVAILABLE_NETWORK_WIDGETS.values():
            action = menu.addAction('Add {} view'.format(view_class.title))
            action.setIcon(self.btAddView.icon())
            action.setData(view_class)
            action.triggered.connect(self.on_add_view_triggered)
            if set_default:
                self.btAddView.setDefaultAction(action)
                set_default = False

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))
        self.editMetadataFile.textChanged.connect(self.on_metadata_file_changed)
        self.btOptions.clicked.connect(self.on_show_options_dialog)
        self.cbCsvDelimiter.delimiterChanged.connect(self.on_delimiter_changed)
        self.btRemoveViews.clicked.connect(self.on_remove_views)
        self.btEditView.clicked.connect(self.on_edit_view)
        self.btClear.clicked.connect(self.on_clear_view)
        self.lstViews.itemDoubleClicked.connect(self.on_edit_view)
        self.btSelectAll.clicked.connect(lambda: self.select('all'))
        self.btSelectNone.clicked.connect(lambda: self.select('none'))
        self.btSelectInvert.clicked.connect(lambda: self.select('invert'))

    def select(self, type_):
        for row in range(self.lstViews.count()):
            item = self.lstViews.item(row)
            if type_ == 'all':
                item.setSelected(True)
            elif type_ == 'none':
                item.setSelected(False)
            elif type_ == 'invert':
                item.setSelected(not item.isSelected())

    def on_add_view_triggered(self):
        action = self.sender()
        widget_class = action.data()
        if widget_class is not None:
            for row in range(self.lstViews.count()):
                item = self.lstViews.item(row)
                if item.data(ProcessDataDialog.NameRole) == widget_class.name:
                    QMessageBox.warning(self, None, "A network of this type already exists.")
                    return

            options = self._options.get(widget_class.name, {})
            dialog = widget_class.dialog_class(self, options=options)

            def add_view(result):
                if result == QDialog.Accepted:
                    options = dialog.getValues()
                    self._options[widget_class.name] = options
                    item = QListWidgetItem(widget_class.title)
                    item.setSizeHint(QSize(0, 50))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(ProcessDataDialog.NameRole, widget_class.name)
                    self.lstViews.addItem(item)

            dialog.finished.connect(add_view)
            dialog.open()

    def on_remove_views(self):
        for item in self.lstViews.selectedItems():
            self.lstViews.takeItem(self.lstViews.row(item))

    def on_edit_view(self, item: QListWidgetItem = None):
        if item is None or isinstance(item, bool):
            items = self.lstViews.selectedItems()
            try:
                item = items[0]
            except IndexError:
                return

        name = item.data(ProcessDataDialog.NameRole)
        try:
            widget_class = AVAILABLE_NETWORK_WIDGETS[name]
        except KeyError:
            return
        else:
            if widget_class is not None:
                options = self._options.get(name, {})
                dialog = widget_class.dialog_class(self, options=options)

                def set_options(result):
                    if result == QDialog.Accepted:
                        options = dialog.getValues()
                        self._options[widget_class.name] = options

                dialog.finished.connect(set_options)
                dialog.open()

    def on_clear_view(self):
        if QMessageBox.question(self, None, "Clear the list?") == QMessageBox.Yes:
            self.lstViews.clear()

    def on_delimiter_changed(self, delimiter):
        self._metadata_options.sep = delimiter

    def on_show_options_dialog(self):
        delimiter = self.cbCsvDelimiter.delimiter()
        dialog = ImportMetadataDialog(self, filename=self.editMetadataFile.text(), delimiter=delimiter)

        def set_options(result):
            if result == QDialog.Accepted:
                filename, options = dialog.getValues()
                self.editMetadataFile.setText(filename)
                self.cbCsvDelimiter.setDelimiter(options.sep)
                self._metadata_options = options

        dialog.finished.connect(set_options)
        dialog.open()

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
            if len(process_file) > 0 and os.path.exists(process_file) and os.path.splitext(process_file)[1].lower() in ('.mgf', '.msp'):
                if not self.gbMetadata.isChecked() or (os.path.exists(metadata_file) and os.path.isfile(metadata_file)):
                    super().done(r)
                else:
                    self.editMetadataFile.setPalette(self._error_palette)
            else:
                self.editProcessFile.setPalette(self._error_palette)
        else:
            super().done(r)

    def browse(self, type_='process'):
        """Open a dialog to choose either .mgf or metadata.txt file"""

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)

        if type_ == 'process':
            dialog.setNameFilters(["All supported formats (*.mgf *.msp)",
                                   "Mascot Generic Format (*.mgf)",
                                   "NIST Text Format of Individual Spectra (*.msp)",
                                   "All files (*)"])
        elif type_ == 'metadata':
            dialog.setNameFilters(["Metadata File (*.csv *.tsv *.txt)", "All files (*)"])

        def set_filename(result):
            if result == QDialog.Accepted:
                filename = dialog.selectedFiles()[0]
                if type_ == 'process':
                    self.editProcessFile.setText(filename)
                    self.editProcessFile.setPalette(self.style().standardPalette())
                else:
                    self.editMetadataFile.setText(filename)
                    self.editMetadataFile.setPalette(self.style().standardPalette())

        dialog.finished.connect(set_filename)
        dialog.open()

    def getValues(self):
        """Returns files to process and options"""

        metadata_file = self.editMetadataFile.text() if os.path.isfile(self.editMetadataFile.text()) else None
        self._options.cosine = self.cosine_widget.getValues()
        views = [self.lstViews.item(row).data(ProcessDataDialog.NameRole) for row in range(self.lstViews.count())]
        return (self.editProcessFile.text(), self.gbMetadata.isChecked(),  metadata_file,
                self._metadata_options, self._options, views)
