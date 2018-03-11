import os

try:
    from rdkit.Chem import MolFromSmiles, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.inchi import INCHI_AVAILABLE
    if INCHI_AVAILABLE:
        from rdkit.Chem.inchi import MolFromInchi
except:
    RDKIT_AVAILABLE = False
    INCHI_AVAILABLE = False
else:
    RDKIT_AVAILABLE = True

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QItemSelectionModel, QByteArray
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'view_databases_dialog.ui')

from ..database import SpectraLibrary
from ..models import Bank, Spectrum, Base
from .widgets import AutoToolTipItemDelegate

ViewDatabasesDialogUI, ViewDatabasesDialogBase = uic.loadUiType(UI_FILE,
                                                                from_imports='lib.ui',
                                                                import_from='lib.ui')


class BanksModel(QAbstractListModel):
    BankIdRole = Qt.UserRole + 1

    def __init__(self, session):
        super().__init__()

        self.session = session
        self._data = []

        self.refresh()

    def refresh(self):
        self.beginResetModel()

        self._data = sorted([(b.name, b.id) for b in self.session.query(Bank.name, Bank.id)])

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
    ObjectRole = Qt.UserRole + 1

    def __init__(self, session, bank):
        self._columns = [col for col in Spectrum.__table__.columns
                         if col.name not in ('peaks', 'bank_id', 'id')]

        super().__init__(100, len(self._columns))

        self.session = session
        self._data = []
        for i, col in enumerate(self._columns):
            text = col.comment if col.comment is not None else col.name.split('_id')[0]
            self.setHorizontalHeaderItem(i, QStandardItem(text))

        self._bank_id = bank
        self._offset = 0
        self._max_results = 0

        self.refresh()

    def refresh(self):
        self.beginResetModel()

        query = self.session.query(Spectrum).filter(Spectrum.bank_id == self._bank_id)
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

        if role == SpectraModel.ObjectRole:
            try:
                return self._data[row]
            except IndexError:
                return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            try:
                attr = self._columns[column].name
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

    def set_bank(self, bank_id):
        self._bank_id = bank_id
        self._offset = 0
        self.refresh()

    def offset(self):
        return self._offset

    def set_offset(self, offset):
        self._offset = offset
        self.refresh()

    def max_results(self):
        return self._max_results


class ViewDatabasesDialog(ViewDatabasesDialogUI, ViewDatabasesDialogBase):

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.library = SpectraLibrary(os.path.join(base_path, 'spectra'))

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        model = BanksModel(self.library.session)
        self.cbBanks.setModel(model)
        self.cbBanks.setItemDelegate(AutoToolTipItemDelegate())

        model = SpectraModel(self.library.session,
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
        self.btGoTo.clicked.connect(self.on_goto_line)
        self.editGoTo.returnPressed.connect(self.on_goto_line)
        self.tvSpectra.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, item):
        obj = item.indexes()[0].data(role=SpectraModel.ObjectRole)
        if obj is None:
            return

        # Show spectrum
        self.widgetSpectrum.canvas.set_spectrum1(obj.peaks)

        # Try to render structure from InChI or SMILES
        if RDKIT_AVAILABLE:
            mol = None
            if INCHI_AVAILABLE and obj.inchi:  # Use InChI first
                mol = MolFromInchi(obj.inchi)
            if mol is None and obj.smiles:     # If InChI not available, use SMILES as a fallback
                mol = MolFromSmiles(obj.smiles)
            if mol is not None:
                if not mol.GetNumConformers():
                    rdDepictor.Compute2DCoords(mol)
                drawer = rdMolDraw2D.MolDraw2DSVG(self.widgetStructure.size().width(),
                                                  self.widgetStructure.size().height())
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                svg = drawer.GetDrawingText().replace('svg:', '')
                self.widgetStructure.load(QByteArray(svg.encode()))
            else:
                self.widgetStructure.load(QByteArray(b''))

    def on_bank_changed(self):
        bank = self.cbBanks.currentData(role=BanksModel.BankIdRole)
        self.tvSpectra.model().set_bank(bank)
        self.update_label()

    def on_goto_first(self):
        self.set_offset(0)

    def on_goto_previous(self):
        offset = self.tvSpectra.model().offset()
        delta = self.tvSpectra.model().rowCount()
        if offset - delta >= 0:
            self.set_offset(offset-delta)

    def on_goto_next(self):
        offset = self.tvSpectra.model().offset()
        max_ = self.tvSpectra.model().max_results()
        delta = self.tvSpectra.model().rowCount()
        if offset + delta <= max_:
            self.set_offset(offset+delta)

    def on_goto_last(self):
        max_ = self.tvSpectra.model().max_results()
        delta = self.tvSpectra.model().rowCount()
        self.set_offset(max_-max_%delta)

    def on_goto_line(self):
        try:
            num = int(self.editGoTo.text()) - 1
        except ValueError:
            return False
        else:
            max_ = self.tvSpectra.model().max_results()
            if 0 <= num < max_:
                delta = self.tvSpectra.model().rowCount()
                self.set_offset(num - num % delta)
                index = self.tvSpectra.model().index(num % delta, 0)
                self.tvSpectra.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                self.tvSpectra.scrollTo(index)

    def closeEvent(self, event):
        self.library.close()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def update_label(self):
        offset = self.tvSpectra.model().offset() + 1
        max_ = self.tvSpectra.model().max_results() + 1
        delta = self.tvSpectra.model().rowCount() - 1
        self.lblOffset.setText(f"{offset}-{min(offset+delta, max_)} of {max_}")

    def set_offset(self, offset):
        self.tvSpectra.model().set_offset(offset)
        self.update_label()
