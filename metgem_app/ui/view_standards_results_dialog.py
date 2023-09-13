import numpy as np
from PySide6.QtCore import Qt, QModelIndex, QItemSelection, QItemSelectionModel
from PySide6.QtGui import QStandardItemModel, QIcon, QStandardItem
from PySide6.QtWidgets import QAbstractItemView, QDialog

from metgem_app.ui.widgets.delegates.quality import LibraryQualityDelegate
from metgem_app.database import Spectrum
from metgem_app.models.standards_results import SpectraModel
from metgem_app.ui.view_standards_results_dialog_ui import Ui_Dialog


class ViewStandardsResultsDialog(QDialog, Ui_Dialog):

    def __init__(self, *args, mz_parent=None, spectrum: np.ndarray = None, base_path=None,
                 selection: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._selected_index = QModelIndex()

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        if spectrum is not None:
            self.widgetSpectrumDetails.widgetSpectrum.set_spectrum2(spectrum, parent=mz_parent)

        self.current = selection['current'] if 'current' in selection else 0

        model = SpectraModel(base_path, selection)

        for i in range(model.columnCount()):
            if model.headerData(i, Qt.Horizontal) == Spectrum.libraryquality.comment:
                self.tvSpectra.setItemDelegateForColumn(i, LibraryQualityDelegate())
                break

        forbidden_cols = (model.column_index(Spectrum.id),
                          model.column_index(Spectrum.bank_id),
                          model.column_index(Spectrum.peaks))
        tree_model = QStandardItemModel()
        tree_model.setColumnCount(model.columnCount()-len(forbidden_cols))
        tree_model.setHorizontalHeaderLabels([model.headerData(section) for section in range(model.columnCount())
                                              if section not in forbidden_cols])

        standards_item = QStandardItem(QIcon(":/icons/images/library-query.svg"), 'Standards')
        standards_item.setSelectable(False)
        standards_item.setData("standards", role=SpectraModel.TypeRole)
        tree_model.appendRow(standards_item)
        analogs_item = QStandardItem(QIcon(":/icons/images/library-query-analogs.svg"), 'Analogs')
        analogs_item.setSelectable(False)
        analogs_item.setData("analogs", role=SpectraModel.TypeRole)
        tree_model.appendRow(analogs_item)

        standards_rows = 0
        for row in range(model.rowCount()):
            values = []
            index = None
            for column in range(model.columnCount()):
                if column in forbidden_cols:
                    continue
                index = model.index(row, column)
                item = QStandardItem(str(model.data(index)))
                item.setEditable(False)
                values.append(item)
            if index is not None:
                if model.data(index, role=SpectraModel.TypeRole) == 'analogs':
                    analogs_item.appendRow(values)
                else:
                    standards_item.appendRow(values)
                    standards_rows += 1
        standards_item.setData(0, SpectraModel.RowRole)
        analogs_item.setData(standards_rows, SpectraModel.RowRole)

        self.tvSpectra.setModel(tree_model)
        self.tvSpectra.expandAll()
        self.widgetSpectrumDetails.setModel(model)
        self.widgetSpectrumDetails.widgetSpectrum.canvas.first_spectrum_label = "Database"
        self.widgetSpectrumDetails.widgetSpectrum.canvas.second_spectrum_label = "Experimental"

        # Connect events
        self.tvSpectra.selectionModel().currentChanged.connect(self.on_selection_changed)

    def getValues(self):
        if self._selected_index.isValid():
            parent = self._selected_index.parent()
            if parent.isValid():
                if parent.data(role=SpectraModel.TypeRole) == "standards":
                    return self._selected_index.row()

    def on_selection_changed(self, index):
        if not index.isValid():
            return

        parent = index.parent()
        if parent.isValid():
            # Update description labels
            self.widgetSpectrumDetails.setCurrentIndex(index.row() + parent.data(SpectraModel.RowRole))
            self._selected_index = index

    def closeEvent(self, event):
        super().closeEvent(event)

    def showEvent(self, event):
        self.activateWindow()
        self.select_row(self.current)
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def select_row(self, row, scroll_hint: QAbstractItemView.ScrollHint = QAbstractItemView.ScrollHint.EnsureVisible):
        if 0 <= row < self.widgetSpectrumDetails.model().rowCount():
            index = self.widgetSpectrumDetails.model().index(row, 0)
            if index.data(role=SpectraModel.TypeRole) == 'standards':
                parent = self.tvSpectra.model().index(0, 0)
            else:
                parent = self.tvSpectra.model().index(1, 0)
            index_first = self.tvSpectra.model().index(row, 0, parent=parent)
            index_last = self.tvSpectra.model().index(row, self.tvSpectra.model().columnCount()-1, parent=parent)
            self.tvSpectra.selectionModel().select(QItemSelection(index_first, index_last),
                                                   QItemSelectionModel.Select)
            self.on_selection_changed(index_first)
            self.tvSpectra.scrollTo(index_first, scroll_hint)

