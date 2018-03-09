import os

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QSize
from PyQt5 import uic

from sqlalchemy.orm import subqueryload

UI_FILE = os.path.join(os.path.dirname(__file__), 'view_databases_dialog.ui')

from ..database import SpectraLibrary
from ..models import Bank, Spectrum, Base

ViewDatabasesDialogUI, ViewDatabasesDialogBase = uic.loadUiType(UI_FILE,
                                                                from_imports='lib.ui',
                                                                import_from='lib.ui')


class BanksModel(QAbstractListModel):
    BankIdRole = Qt.UserRole + 1

    def __init__(self, database):
        super().__init__()

        self.database = database
        self._data = []

        self.refresh()

    def refresh(self):
        self.beginResetModel()

        with SpectraLibrary(self.database) as library:
            self._data = sorted([(b.name, b.id) for b in library.session.query(Bank.name, Bank.id)])

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        if row > self.rowCount():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._data[row][0]
        elif role == BanksModel.BankIdRole:
            return self._data[row][1]


class SpectraModel(QStandardItemModel):

    def __init__(self, database, bank):
        self._columns = [key.split('_id')[0] for key in Spectrum.__table__.columns._data.keys()
                         if key != 'peaks' and key != 'bank_id']

        super().__init__(100, len(self._columns))

        self.database = database
        self._data = []
        for i, key in enumerate(self._columns):
            self.setHorizontalHeaderItem(i, QStandardItem(key))

        self._bank_id = bank
        self._offset = 0
        self._max_results = 0

        self.refresh()

    def refresh(self):
        self.beginResetModel()

        with SpectraLibrary(self.database) as library:
            query = library.session.query(Spectrum)\
                    .filter(Spectrum.bank_id == self._bank_id)
            self._max_results = query.count()
            self._data = [spec for spec in query.limit(100).offset(self._offset)]

        self.endResetModel()

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        if row > self.rowCount() or column > self.columnCount():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            try:
                attr = self._columns[column]
                value = getattr(self._data[row], attr, None)
                if isinstance(value, Base):
                    value = getattr(value, 'name', None)
                return value
            except IndexError:
                return None
        else:
            return super().data(index, role)

    def bank(self):
        return self._bank_id

    def setBank(self, bank_id):
        self._bank_id = bank_id
        self._offset = 0
        self.refresh()

    def offset(self):
        return self._offset

    def setOffset(self, offset):
        self._offset = offset
        self.refresh()

    def maxResults(self):
        return self._max_results


class ViewDatabasesDialog(ViewDatabasesDialogUI, ViewDatabasesDialogBase):

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.database = os.path.join(base_path, 'spectra')

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        model = BanksModel(self.database)
        self.cbBanks.setModel(model)

        model = SpectraModel(self.database,
                             self.cbBanks.currentData(role=BanksModel.BankIdRole))
        self.tvSpectra.setModel(model)
        self.update_label()

        # Connect events
        self.btRefresh.clicked.connect(self.cbBanks.model().refresh)
        self.cbBanks.currentIndexChanged.connect(self.on_bank_changed)
        self.btFirst.clicked.connect(self.on_goto_first)
        self.btPrevious.clicked.connect(self.on_goto_previous)
        self.btNext.clicked.connect(self.on_goto_next)
        self.btLast.clicked.connect(self.on_goto_last)

    def on_bank_changed(self):
        bank = self.cbBanks.currentData(role=BanksModel.BankIdRole)
        self.tvSpectra.model().setBank(bank)
        self.update_label()

    def on_goto_first(self):
        self.tvSpectra.model().setOffset(0)
        self.update_label()

    def on_goto_previous(self):
        offset = self.tvSpectra.model().offset()
        delta = self.tvSpectra.model().rowCount()
        if offset - delta >= 0:
            self.tvSpectra.model().setOffset(offset-delta)
        self.update_label()

    def on_goto_next(self):
        offset = self.tvSpectra.model().offset()
        max_ = self.tvSpectra.model().maxResults()
        delta = self.tvSpectra.model().rowCount()
        if offset + delta <= max_:
            self.tvSpectra.model().setOffset(offset+delta)
        self.update_label()

    def on_goto_last(self):
        max_ = self.tvSpectra.model().maxResults()
        delta = self.tvSpectra.model().rowCount()
        self.tvSpectra.model().setOffset(max_-max_%delta)
        self.update_label()

    def update_label(self):
        offset = self.tvSpectra.model().offset() + 1
        max_ = self.tvSpectra.model().maxResults() + 1
        delta = self.tvSpectra.model().rowCount() - 1
        self.lblOffset.setText(f"{offset}-{min(offset+delta, max_)} of {max_}")
