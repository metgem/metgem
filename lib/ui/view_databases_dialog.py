import os

from PyQt5.QtWidgets import QAbstractItemView, QDataWidgetMapper, QLabel

try:
    from rdkit.Chem import MolFromSmiles, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.inchi import INCHI_AVAILABLE
    if INCHI_AVAILABLE:
        from rdkit.Chem.inchi import MolFromInchi
except ImportError:
    RDKIT_AVAILABLE = False
    INCHI_AVAILABLE = False
else:
    RDKIT_AVAILABLE = True

try:
    import pybel
    from lxml import etree
except ImportError:
    OPENBABEL_AVAILABLE = False
    INCHI_AVAILABLE = False
else:
    OPENBABEL_AVAILABLE = True
    INCHI_AVAILABLE = 'inchi' in pybel.informats.keys()

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex,
                          QByteArray, QAbstractTableModel)
from PyQt5 import uic

UI_FILE = os.path.join(os.path.dirname(__file__), 'view_databases_dialog.ui')

from ..database import SpectraLibrary
from ..models import Bank, Spectrum, Base
from .widgets import AutoToolTipItemDelegate, LibraryQualityDelegate, SpectrumWidget, SpectrumCanvas

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


class SpectraModel(QAbstractTableModel):
    ObjectRole = Qt.UserRole + 1

    BATCH_SIZE = 200

    def __init__(self, session, bank):
        columns = [col for col in Spectrum.__table__.columns]
        self._columns = {index: col for index, col in enumerate(columns)}
        self._rcolumns = {col.key: index for index, col in enumerate(columns)}

        super().__init__()

        self.session = session
        self._data = []
        self._bank_id = bank
        self._offset = 0
        self._max_results = 0

        self.query_db()

    def query_db(self):
        query = self.session.query(Spectrum).filter(Spectrum.bank_id == self._bank_id)
        self._max_results = query.count()
        self._data.extend([spec for spec in query.limit(self.BATCH_SIZE).offset(self._offset)])
        self._offset += self.BATCH_SIZE

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._max_results

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if (orientation == Qt.Horizontal and section > self.columnCount())\
                or (orientation == Qt.Horizontal and section > self.rowCount()):
            return None

        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            col = self._columns[section]
            return col.comment if col.comment is not None else col.name.split('_id')[0]
        else:
            return super().headerData(section, orientation, role)

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        if row > self.rowCount() or column > self.columnCount():
            return None

        if row >= self._offset:
            self.query_db()

        try:
            obj = self._data[row]
        except IndexError:
            return None

        if role == SpectraModel.ObjectRole:
            return obj
        elif role in (Qt.DisplayRole, Qt.EditRole):
            attr = self._columns[column].name.split('_id')[0]
            attr = 'polarity' if attr == 'positive' else attr
            value = getattr(obj, attr, None)
            if isinstance(value, Base):
                value = getattr(value, 'name', None)
            return value

    def bank(self):
        return self._bank_id

    def set_bank(self, bank_id):
        self.beginResetModel()
        self._bank_id = bank_id
        self._data = []
        self._offset = 0
        self.query_db()
        self.endResetModel()

    def column_index(self, column):
        return self._rcolumns[column.key]


class SpectrumDataWidgetMapper(QDataWidgetMapper):

    def addMapping(self, widget, section, property_name=None):
        model = self.model()
        if model is not None and not isinstance(section, int):
            section = model.column_index(section)

        if isinstance(widget, QLabel):
            property_name = b'text'
        elif isinstance(widget, (SpectrumWidget, SpectrumCanvas)):
            if isinstance(widget, SpectrumWidget):
                widget = widget.canvas
            property_name = b'spectrum1'

        if property_name is None:
            super().addMapping(widget, section)
        else:
            super().addMapping(widget, section, property_name)


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
        for i in range(model.columnCount()):
            if model.headerData(i, Qt.Horizontal) == Spectrum.libraryquality.comment:
                self.tvSpectra.setItemDelegateForColumn(i, LibraryQualityDelegate())
                break
        self.tvSpectra.setModel(model)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.id), True)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.bank_id), True)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.peaks), True)

        self._mapper = SpectrumDataWidgetMapper()
        self._mapper.setModel(model)
        self._mapper.addMapping(self.lblName, Spectrum.name)
        self._mapper.addMapping(self.lblInChI, Spectrum.inchi)
        self._mapper.addMapping(self.lblSmiles, Spectrum.smiles)
        self._mapper.addMapping(self.lblPubMed, Spectrum.pubmed)
        self._mapper.addMapping(self.lblPepmass, Spectrum.pepmass)
        self._mapper.addMapping(self.lblPolarity, Spectrum.positive)
        self._mapper.addMapping(self.lblCharge, Spectrum.charge)
        self._mapper.addMapping(self.lblMSLevel, Spectrum.mslevel)
        self._mapper.addMapping(self.lblQuality, Spectrum.libraryquality)
        self._mapper.addMapping(self.lblLibraryId, Spectrum.spectrumid)
        self._mapper.addMapping(self.lblSourceInstrument, Spectrum.source_instrument_id)
        self._mapper.addMapping(self.lblPi, Spectrum.pi_id)
        self._mapper.addMapping(self.lblOrganism, Spectrum.organism_id)
        self._mapper.addMapping(self.lblDataCollector, Spectrum.datacollector_id)
        self._mapper.addMapping(self.lblSubmitUser, Spectrum.submituser_id)
        self._mapper.addMapping(self.widgetSpectrum, Spectrum.peaks)

        # Connect events
        self.btRefresh.clicked.connect(self.on_refresh)
        self.cbBanks.currentIndexChanged.connect(self.on_bank_changed)
        self.btFirst.clicked.connect(self.on_goto_first)
        self.btPrevious.clicked.connect(self.on_goto_previous)
        self.btNext.clicked.connect(self.on_goto_next)
        self.btLast.clicked.connect(self.on_goto_last)
        self.btGoTo.clicked.connect(self.on_goto_line)
        self.editGoTo.returnPressed.connect(self.on_goto_line)
        self.tvSpectra.selectionModel().currentChanged.connect(self.on_selection_changed)
        self.tvSpectra.verticalScrollBar().valueChanged.connect(self.update_label)

    def on_refresh(self):
        self.cbBanks.model().refresh()
        self.cbBanks.setCurrentIndex(0)

    def on_selection_changed(self, index):
        obj = index.data(role=SpectraModel.ObjectRole)
        if obj is None:
            return

        # Update description labels
        self._mapper.setCurrentIndex(index.row())

        # Try to render structure from InChI or SMILES
        if RDKIT_AVAILABLE:
            mol = None
            if INCHI_AVAILABLE and obj.inchi:  # Use InChI first
                mol = MolFromInchi(obj.inchi)
            elif obj.smiles:                   # If InChI not available, use SMILES as a fallback
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
        elif OPENBABEL_AVAILABLE:  # If RDkit not available, try to use OpenBabel
            mol = None
            try:
                if INCHI_AVAILABLE and obj.inchi:
                    mol = pybel.readstring('inchi', obj.inchi)
                elif obj.smiles:
                    mol = pybel.readstring('smiles', obj.smiles)
            except OSError:
                self.widgetStructure.load(QByteArray(b''))
            else:
                if mol is not None:
                    # Convert to svg, code loosely based on _repr_svg_ from pybel's Molecule
                    namespace = "http://www.w3.org/2000/svg"
                    tree = etree.fromstring(mol.write("svg"))
                    svg = tree.find(f"{{{namespace}}}g/{{{namespace}}}svg")
                    self.widgetStructure.load(QByteArray(etree.tostring(svg)))
                else:
                    self.widgetStructure.load(QByteArray(b''))

    def on_bank_changed(self):
        bank = self.cbBanks.currentData(role=BanksModel.BankIdRole)
        self.tvSpectra.model().set_bank(bank)
        self.select_row(0)

    def on_goto_first(self):
        self.select_row(0)

    def on_goto_previous(self):
        first, last = self.visible_rows()
        self.select_row(first-(last-first+1), QAbstractItemView.PositionAtTop)

    def on_goto_next(self):
        first, last = self.visible_rows()
        self.select_row(last+1, QAbstractItemView.PositionAtTop)

    def on_goto_last(self):
        self.select_row(self.tvSpectra.model().rowCount()-1)

    def on_goto_line(self):
        try:
            row = int(self.editGoTo.text()) - 1
        except ValueError:
            return False
        else:
            self.select_row(row)

    def closeEvent(self, event):
        self.library.close()
        super().closeEvent(event)

    def showEvent(self, event):
        self.select_row(0)
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def update_label(self):
        first, last = self.visible_rows()
        max_ = self.tvSpectra.model().rowCount()
        self.lblOffset.setText(f"{first+1}-{last} of {max_}")

    def visible_rows(self):
        first = self.tvSpectra.rowAt(0)
        last = self.tvSpectra.rowAt(self.tvSpectra.height())
        last = self.tvSpectra.rowAt(self.tvSpectra.height() - self.tvSpectra.rowHeight(last)/2)
        max_ = self.tvSpectra.model().rowCount()
        last = last if last > 0 else max_
        return first, last

    def select_row(self, row, scroll_hint: QAbstractItemView.ScrollHint = QAbstractItemView.EnsureVisible):
        if 0 <= row < self.tvSpectra.model().rowCount():
            index = self.tvSpectra.model().index(row, 0)
            self.tvSpectra.selectRow(row)
            self.tvSpectra.scrollTo(index, scroll_hint)

