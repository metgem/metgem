import itertools
import os
import numpy as np

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMainWindow
from PyQt5 import uic
from PyQtAds import QtAds

from libmetgem import MZ, square_root_and_normalize_data
from libmetgem.cosine import compare_spectra, SpectraMatchState


class FragmentsListWidget(QWidget):
    IndexRole = Qt.UserRole + 1

    def __init__(self, parent):
        super().__init__(parent)

        self._spectra_widget = None

        uic.loadUi(os.path.join(os.path.dirname(__file__), 'fragments_list.ui'), self)
        self.twFragments.itemSelectionChanged.connect(self.update_peaks_selection)
        self.twNeutralLosses.itemSelectionChanged.connect(self.update_peaks_selection)

    @property
    def spectra_widget(self):
        return self._spectra_widget

    @spectra_widget.setter
    def spectra_widget(self, widget):
        self._spectra_widget = widget

    def update_peaks_selection(self):
        if self._spectra_widget is not None and self._spectra_widget.has_data():
            items = list(itertools.chain(self.twFragments.selectedItems(), self.twNeutralLosses.selectedItems()))
            rows1 = {item.data(FragmentsListWidget.IndexRole) for item in items if item.column() == 0}
            rows2 = {item.data(FragmentsListWidget.IndexRole) for item in items if item.column() == 1}
            for plot, data, rows in ((self._spectra_widget.spectrum1_plot, self._spectra_widget.spectrum1, rows1),
                                     (self._spectra_widget.spectrum2_plot, self._spectra_widget.spectrum2, rows2)):
                plot.set_linewidth([2. if x in rows else 0.5 for x in range(data.shape[0])])
            self._spectra_widget.draw()

    def clear_fragments_list(self):
        for table in (self.twFragments, self.twNeutralLosses):
            table.clear()
            table.setRowCount(0)
            table.horizontalHeader().hide()

    def populate_fragments_list(self):
        self.clear_fragments_list()
        mz1 = self._spectra_widget.spectrum1_parent
        data1 = self._spectra_widget.spectrum1
        mz2 = self._spectra_widget.spectrum2_parent
        data2 = self._spectra_widget.spectrum2
        dock_widget = QtAds.internal.findParent(QtAds.CDockWidget, self)
        main_window = dock_widget.dockManager().parent() if dock_widget else None

        if main_window is not None and mz1 is not None and data1 is not None and mz2 is not None and data2 is not None:
            data1 = square_root_and_normalize_data(data1)
            data2 = square_root_and_normalize_data(data2)
            matches = compare_spectra(mz1, data1, mz2, data2, main_window.network.options.cosine.mz_tolerance)
            if matches.size == 0:
                return

            float_precision = QSettings().value('Metadata/float_precision', 4, type=int)
            for table, t in ((self.twFragments, SpectraMatchState.fragment),
                             (self.twNeutralLosses, SpectraMatchState.neutral_loss)):
                filter_ = np.where(matches['type'] == t)[0]
                table.setRowCount(filter_.shape[0])
                table.setHorizontalHeaderLabels(["Top Spectrum", "Bottom Spectrum", "Partial Score"])
                if filter_.size > 0:
                    table.horizontalHeader().show()
                if table == self.twNeutralLosses:
                    data1 = mz1 - data1
                    data2 = mz2 - data2

                for column in range(table.model().columnCount()):
                    table.resizeColumnToContents(column)

                for row, (ix1, ix2, score, _) in enumerate(matches[filter_]):
                    for mz, data, ix, column in ((mz1, data1, ix1, 0), (mz2, data2, ix2, 1)):
                        item = QTableWidgetItem(f'{data[ix, MZ]:.{float_precision}f}')
                        item.setData(FragmentsListWidget.IndexRole, ix)
                        table.setItem(row, column, item)

                    item = QTableWidgetItem(f'{score:.{float_precision}f}')
                    item.setData(FragmentsListWidget.IndexRole, ix)
                    table.setItem(row, 2, item)
