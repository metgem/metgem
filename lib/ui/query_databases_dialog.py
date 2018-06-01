import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QListWidgetItem

UI_FILE = os.path.join(os.path.dirname(__file__), 'query_databases_dialog.ui')

from .widgets import QueryDatabasesOptionsWidget, AutoToolTipItemDelegate
from ..workers.databases import QueryDatabasesOptions
from ..database import SpectraLibrary, Bank
from ..config import SQL_PATH, DEBUG

QueryDatabasesDialogUI, QueryDatabasesDialogBase = uic.loadUiType(UI_FILE, from_imports='lib.ui', import_from='lib.ui')


class QueryDatabasesDialog(QueryDatabasesDialogBase, QueryDatabasesDialogUI):
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
    IDS_ROLE = Qt.UserRole + 1

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._metadata_options = QueryDatabasesOptions()

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        # Add options widget
        self.db_widget = QueryDatabasesOptionsWidget()
        self.layout().insertWidget(self.layout().count()-1, self.db_widget)
        if options:
            self.db_widget.setValues(options)

        # Populate list
        selection = QSettings().value('Databases/Selection', [])
        self.lstDatabases.setFocus()
        self.lstDatabases.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lstDatabases.setItemDelegate(AutoToolTipItemDelegate())
        with SpectraLibrary(SQL_PATH, echo=DEBUG) as lib:
            for bank in lib.query(Bank):
                item = QListWidgetItem(bank.name)
                item.setData(QueryDatabasesDialog.IDS_ROLE, bank.id)
                self.lstDatabases.addItem(item)
                print(bank.name, selection)
                if bank.name in selection:
                    item.setSelected(True)

        # Connect events
        self.btSelectAll.clicked.connect(lambda: self.select('all'))
        self.btSelectNone.clicked.connect(lambda: self.select('none'))
        self.btSelectInvert.clicked.connect(lambda: self.select('invert'))
        self.btSaveSelection.clicked.connect(self.on_save_selection)

    def showEvent(self, event):
        self.adjustSize()
        super().showEvent(event)

    def select(self, type_):
        for i in range(self.lstDatabases.count()):
            item = self.lstDatabases.item(i)
            if type_ == 'all':
                item.setSelected(True)
            elif type_ == 'none':
                item.setSelected(False)
            elif type_ == 'invert':
                item.setSelected(not item.isSelected())

    def on_save_selection(self):
        QSettings().setValue('Databases/Selection', [item.text() for item in self.lstDatabases.selectedItems()])

    def getValues(self):
        options = self.db_widget.getValues()
        options.databases = [item.data(QueryDatabasesDialog.IDS_ROLE) for item in self.lstDatabases.selectedItems()]
        return options
