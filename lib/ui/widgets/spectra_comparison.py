import itertools
import os
import numpy as np

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QTableWidgetItem

from libmetgem import MZ, square_root_and_normalize_data
from libmetgem.cosine import compare_spectra, SpectraMatchState


class SpectraComparisonWidget(QWidget):
    IndexRole = Qt.UserRole + 1

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'spectrum.ui'), self)
        self.spectraWidget.dataLoaded.connect(self.populate_fragments_list)
        self.spectraWidget.dataCleared.connect(self.clear_fragments_list)
        self.twFragments.itemSelectionChanged.connect(self.update_peaks_selection)
        self.twNeutralLosses.itemSelectionChanged.connect(self.update_peaks_selection)

    def parent(self):
        return self._parent

    def update_peaks_selection(self):
        if self.spectraWidget.has_data():
            items = list(itertools.chain(self.twFragments.selectedItems(), self.twNeutralLosses.selectedItems()))
            rows1 = {item.data(SpectraComparisonWidget.IndexRole) for item in items if item.column() == 0}
            rows2 = {item.data(SpectraComparisonWidget.IndexRole) for item in items if item.column() == 1}
            for plot, data, rows in ((self.spectraWidget.spectrum1_plot, self.spectraWidget.spectrum1, rows1),
                                     (self.spectraWidget.spectrum2_plot, self.spectraWidget.spectrum2, rows2)):
                plot.set_linewidth([2. if x in rows else 0.5 for x in range(data.shape[0])])
            self.spectraWidget.draw()

    def clear_fragments_list(self):
        for table in (self.twFragments, self.twNeutralLosses):
            table.clear()
            table.setRowCount(0)
            table.horizontalHeader().hide()

    def populate_fragments_list(self):
        self.clear_fragments_list()
        mz1 = self.spectraWidget.spectrum1_parent
        data1 = self.spectraWidget.spectrum1
        mz2 = self.spectraWidget.spectrum2_parent
        data2 = self.spectraWidget.spectrum2

        if mz1 is not None and data1 is not None and mz2 is not None and data2 is not None:
            data1 = square_root_and_normalize_data(data1)
            data2 = square_root_and_normalize_data(data2)
            matches = compare_spectra(mz1, data1, mz2, data2, self.parent().network.options.cosine.mz_tolerance)
            if matches.size == 0:
                return

            for table, t in ((self.twFragments, SpectraMatchState.fragment),
                             (self.twNeutralLosses, SpectraMatchState.neutral_loss)):
                filter_ = np.where(matches['type'] == t)[0]
                table.setRowCount(filter_.shape[0])
                table.setHorizontalHeaderLabels(["Spectrum 1 (top)", "Spectrum 2 (bottom)", "Partial Score"])
                if filter_.size > 0:
                    table.horizontalHeader().show()
                if table == self.twNeutralLosses:
                    data1 = mz1 - data1
                    data2 = mz2 - data2

                for row, (ix1, ix2, score, _) in enumerate(matches[filter_]):
                    for mz, data, ix, column in ((mz1, data1, ix1, 0), (mz2, data2, ix2, 1)):
                        item = QTableWidgetItem(str(data[ix, MZ]))
                        item.setData(SpectraComparisonWidget.IndexRole, ix)
                        table.setItem(row, column, item)

                    item = QTableWidgetItem(f'{score:.4f}')
                    item.setData(SpectraComparisonWidget.IndexRole, ix)
                    table.setItem(row, 2, item)

    def __getattr__(self, item):
        return getattr(self.spectraWidget, item)
