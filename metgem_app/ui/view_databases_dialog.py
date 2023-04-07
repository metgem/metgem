import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QDialog

from ..models.databases import BanksModel, SpectraModel
from ..database import SpectraLibrary, Spectrum
from .widgets.delegates.autotooltip import AutoToolTipItemDelegate
from .widgets.delegates.quality import LibraryQualityDelegate
from .view_databases_dialog_ui import Ui_Dialog


class ViewDatabasesDialog(QDialog, Ui_Dialog):

    def __init__(self, *args, base_path=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.library = SpectraLibrary(os.path.join(base_path, 'spectra'))

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        model = BanksModel(self.library)
        self.cbBanks.setModel(model)
        self.cbBanks.setItemDelegate(AutoToolTipItemDelegate())

        model = SpectraModel(self.library,
                             self.cbBanks.currentData(role=BanksModel.BankIdRole))
        for i in range(model.columnCount()):
            if model.headerData(i, Qt.Horizontal) == Spectrum.libraryquality.comment:
                self.tvSpectra.setItemDelegateForColumn(i, LibraryQualityDelegate())
                break
        self.tvSpectra.setModel(model)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.id), True)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.bank_id), True)
        self.tvSpectra.setColumnHidden(model.column_index(Spectrum.peaks), True)

        self.widgetSpectrumDetails.setModel(model)
        self.widgetSpectrumDetails.widgetFragmentsList.hide()

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
        self.widgetSpectrumDetails.setCurrentIndex(index.row())

    def on_bank_changed(self):
        bank = self.cbBanks.currentData(role=BanksModel.BankIdRole)
        self.tvSpectra.model().set_bank(bank)
        self.select_row(0)
        self.update_label()

    def on_goto_first(self):
        self.select_row(0)

    def on_goto_previous(self):
        first, last = self.visible_rows()
        self.select_row(first-(last-first+1), QAbstractItemView.ScrollHint.PositionAtTop)

    def on_goto_next(self):
        first, last = self.visible_rows()
        self.select_row(last+1, QAbstractItemView.ScrollHint.PositionAtTop)

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
        self.update_label()
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def update_label(self):
        model = self.tvSpectra.model()
        if model is None:
            return

        first, last = self.visible_rows()
        max_ = model.rowCount()
        self.lblOffset.setText(f"{first+1}-{last} of {max_}")

    def visible_rows(self):
        model = self.tvSpectra.model()
        if model is not None:
            return 0, 0

        first = self.tvSpectra.rowAt(0)
        last = self.tvSpectra.rowAt(self.tvSpectra.height())
        last = self.tvSpectra.rowAt(self.tvSpectra.height() - self.tvSpectra.rowHeight(last)/2)
        max_ = model.rowCount()
        last = last if last > 0 else max_
        return first, last

    def select_row(self, row, scroll_hint: QAbstractItemView.ScrollHint = QAbstractItemView.ScrollHint.EnsureVisible):
        model = self.tvSpectra.model()
        if model is None:
            return

        if 0 <= row < model.rowCount():
            index = model.index(row, 0)
            self.tvSpectra.selectRow(row)
            self.tvSpectra.scrollTo(index, scroll_hint)

