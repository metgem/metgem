import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from metgem.ui.widgets.spectrum.spectra_comparison_ui import Ui_Spectra


class SpectraComparisonWidget(QWidget, Ui_Spectra):
    IndexRole = Qt.UserRole + 1

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.widgetFragmentsList.spectra_widget = self.widgetSpectra
        self.widgetSpectra.dataLoaded.connect(self.widgetFragmentsList.populate_fragments_list)
        self.widgetSpectra.dataCleared.connect(self.widgetFragmentsList.clear_fragments_list)

    def __getattr__(self, item):
        return getattr(self.widgetSpectra, item)
