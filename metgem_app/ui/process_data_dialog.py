import os

from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QPalette, QColor
from qtpy.QtWidgets import QFileDialog, QDialog, QMenu, QListWidgetItem, QMessageBox

from ..utils.network import generate_id
from ..utils.gui import enumerateMenu
from ..workers.core import WorkerQueue, ImportModulesWorker
from ..workers.options import ReadMetadataOptions

from .widgets import CosineOptionsWidget, AVAILABLE_NETWORK_WIDGETS
from .widgets.network import short_id
from .progress_dialog import ProgressDialog
from .import_metadata_dialog import ImportMetadataDialog
from .process_data_dialog_ui import Ui_ProcessFileDialog


class ProcessDataDialog(QDialog, Ui_ProcessFileDialog):
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
    IdRole = Qt.UserRole + 2

    def __init__(self, create_network_menu, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._metadata_options = ReadMetadataOptions()
        self._options = options
        self._dialog = None
        self._workers = WorkerQueue(self, ProgressDialog(self))
        self._create_network_menu = create_network_menu

        self.setupUi(self)
        self.btBrowseProcessFile.setFocus()
        self.gbMetadata.setChecked(False)
        self.gbMSAnnotations.setChecked(False)

        # Create palette used when validating input files
        self._error_palette = QPalette()
        self._error_palette.setColor(QPalette.Base, QColor(Qt.red).lighter(150))

        # Set completer for input files
        # TODO: Completer makes the dialog freeze for seconds on show, disable it until fixed
        # for edit in (self.editProcessFile, self.editMetadataFile):
        #     completer = QCompleter(edit)
        #     if sys.platform.startswith('win'):
        #         completer.setCaseSensitivity(Qt.CaseInsensitive)
        #     model = QFileSystemModel(completer)
        #     model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        #     if edit == self.editProcessFile:
        #         model.setNameFilterDisables(False)
        #         model.setNameFilters(['*.mgf', '*.msp'])
        #     model.setRootPath(QDir.currentPath())
        #     completer.setModel(model)
        #     edit.setCompleter(completer)

        # Add cosine options widget
        self.cosine_widget = CosineOptionsWidget()
        self.layout().addWidget(self.cosine_widget, self.layout().count()-2, 0)

        if options:
            self.cosine_widget.setValues(options.cosine)

        # Build menu to add views
        self._menu = menu = QMenu()
        self.btAddView.setMenu(menu)
        set_default = True
        extras_menu = None
        for view_class in AVAILABLE_NETWORK_WIDGETS.values():
            if view_class.extra:
                if extras_menu is None:
                    extras_menu = menu.addMenu("Extras")
                action = extras_menu.addAction('Add {} view'.format(view_class.title))
            else:
                action = menu.addAction('Add {} view'.format(view_class.title))
            if not view_class.worker_class.enabled():
                action.setEnabled(False)
            action.setIcon(self.btAddView.icon())
            action.setData(view_class)
            action.triggered.connect(self.on_add_view_triggered)
            if set_default:
                self.btAddView.setDefaultAction(action)
                set_default = False

        # Connect events
        self.btBrowseProcessFile.clicked.connect(lambda: self.browse('process'))
        self.btBrowseMetadataFile.clicked.connect(lambda: self.browse('metadata'))
        self.btBrowseMSAnnotationsFile.clicked.connect(lambda: self.browse('annotations'))
        self.btMetadataOptions.clicked.connect(lambda: self.on_show_options_dialog())
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
            self._dialog = widget_class.dialog_class(self, options=None)

            # noinspection PyShadowingNames
            def add_view(result):
                if result == QDialog.Accepted:
                    options = self._dialog.getValues()
                    id_ = generate_id(widget_class.name)
                    self._options[id_] = options
                    item = QListWidgetItem(f"{widget_class.title} ({short_id(id_)})")
                    item.setToolTip(id_)
                    item.setSizeHint(QSize(0, 50))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(ProcessDataDialog.NameRole, widget_class.name)
                    item.setData(ProcessDataDialog.IdRole, id_)
                    self.lstViews.addItem(item)

            def error_import_modules(e):
                if isinstance(e, ImportError):
                    # One or more dependencies could not be loaded, disable action associated with the view
                    for menu in (self.btAddView.menu(), self._create_network_menu):
                        actions = list(enumerateMenu(menu))
                        for action in actions:
                            if action.data() == widget_class:
                                action.setEnabled(False)  # Disable action

                                # Set a new default action
                                index = actions.index(action)
                                default = actions[(index + 1) % len(actions)]
                                menu.setDefaultAction(default)
                                break

                    QMessageBox.warning(self, None,
                        f"{widget_class.title} view can't be added because a requested module can't be loaded.")

            self._dialog.finished.connect(add_view)
            worker = ImportModulesWorker(widget_class.worker_class, widget_class.title)
            worker.error.connect(error_import_modules)
            worker.finished.connect(self._dialog.open)
            self._workers.append(worker)
            self._workers.start()

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
                id_ = item.data(ProcessDataDialog.IdRole)
                options = self._options.get(id_, {})
                dialog = widget_class.dialog_class(self, options=options)

                def set_options(result):
                    if result == QDialog.Accepted:
                        options = dialog.getValues()
                        self._options[id_] = options

                dialog.finished.connect(set_options)
                dialog.open()

    def on_clear_view(self):
        if QMessageBox.question(self, None, "Clear the list?") == QMessageBox.Yes:
            self.lstViews.clear()

    def on_show_options_dialog(self, filename=None):
        if filename is None:
            filename = self.editMetadataFile.text()

        filename = filename if os.path.exists(filename) else None
        dialog = ImportMetadataDialog(self, filename=filename)

        def set_options(result):
            if result == QDialog.Accepted:
                filename, options = dialog.getValues()
                self.editMetadataFile.setText(filename)
                self.editMetadataFile.setPalette(self.style().standardPalette())
                self._metadata_options = options

        dialog.finished.connect(set_options)
        dialog.open()

    def done(self, r):
        if r == QDialog.Accepted:
            process_file = self.editProcessFile.text()
            metadata_file = self.editMetadataFile.text()
            annotations_file = self.editMSAnnotationsFile.text()

            process_ok = len(process_file) > 0 and os.path.exists(process_file)\
                and os.path.splitext(process_file)[1].lower() in ('.mgf', '.msp')
            metadata_ok = not self.gbMetadata.isChecked()\
                or (os.path.exists(metadata_file) and os.path.isfile(metadata_file))
            annotations_ok = not self.gbMSAnnotations.isChecked() \
                or (os.path.exists(annotations_file) and os.path.isfile(annotations_file))

            if not process_ok:
                self.editProcessFile.setPalette(self._error_palette)

            if not metadata_ok:
                self.editMetadataFile.setPalette(self._error_palette)

            if not annotations_ok:
                self.editMSAnnotationsFile.setPalette(self._error_palette)

            if not process_ok or not metadata_ok or not annotations_ok:
                return

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
            dialog.setNameFilters(["Metadata File (*.csv *.tsv *.txt *.xls *.xlsx *.xlsm *.xlsb *.ods)",
                                   "Microsoft Excel spreadsheets (*.xls *.xlsx, *.xlsm *.xlsb)",
                                   "OpenDocument spreadsheets (*.ods)",
                                   "All files (*)"])
        elif type_ == 'annotations':
            dialog.setNameFilters(["MS Annotations File (*_edges_msannotation.csv)",
                                   "All files (*)"])

        def on_dialog_finished(result):
            if result == QDialog.Accepted:
                filename = dialog.selectedFiles()[0]
                if type_ == 'metadata':
                    self.on_show_options_dialog(filename)
                elif type_ == 'annotations':
                    self.editMSAnnotationsFile.setText(filename)
                    self.editMSAnnotationsFile.setPalette(self.style().standardPalette())
                else:
                    self.editProcessFile.setText(filename)
                    self.editProcessFile.setPalette(self.style().standardPalette())

        dialog.finished.connect(on_dialog_finished)
        dialog.open()

    def getValues(self):
        """Returns files to process and options"""

        metadata_file = self.editMetadataFile.text() if os.path.isfile(self.editMetadataFile.text()) else None
        ms_annotations_file = self.editMSAnnotationsFile.text()\
            if os.path.isfile(self.editMSAnnotationsFile.text()) else None
        self._options.cosine = self.cosine_widget.getValues()
        views = [self.lstViews.item(row).data(ProcessDataDialog.IdRole) for row in range(self.lstViews.count())]
        return (self.editProcessFile.text(),
                self.gbMetadata.isChecked(), metadata_file, self._metadata_options,
                self.gbMSAnnotations.isChecked(), ms_annotations_file,
                self._options, views)
