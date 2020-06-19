import os

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class SpectraComparisonWidget(QWidget):
    IndexRole = Qt.UserRole + 1

    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'spectra_comparison.ui'), self)
        self.widgetFragmentsList.spectra_widget = self.widgetSpectra
        self.widgetSpectra.dataLoaded.connect(self.widgetFragmentsList.populate_fragments_list)
        self.widgetSpectra.dataCleared.connect(self.widgetFragmentsList.clear_fragments_list)

    def __getattr__(self, item):
        return getattr(self.widgetSpectra, item)
