from metgem.ui.widgets import QueryDatabasesOptionsWidget, AutoToolTipItemDelegate
from metgem.workers.options import QueryDatabasesOptions
from metgem.database import SpectraLibrary, Bank
from metgem.config import SQL_PATH, get_debug_flag
from metgem.ui.query_databases_dialog_ui import Ui_Dialog

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QListWidgetItem, QDialog


class QueryDatabasesDialog(QDialog, Ui_Dialog):

    IdsRole = Qt.UserRole + 1

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
        with SpectraLibrary(SQL_PATH, echo=get_debug_flag()) as lib:
            for bank in lib.query(Bank):
                item = QListWidgetItem(bank.name)
                item.setData(QueryDatabasesDialog.IdsRole, bank.id)
                self.lstDatabases.addItem(item)
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
        options.databases = [item.data(QueryDatabasesDialog.IdsRole) for item in self.lstDatabases.selectedItems()]
        return options
