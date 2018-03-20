from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from .toolbar import SpectrumNavigationToolbar
from .canvas import SpectrumCanvas


class SpectrumWidget(QWidget):

    def __init__(self, *args, extended_mode=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.canvas = SpectrumCanvas(self)
        self.toolbar = SpectrumNavigationToolbar(self.canvas, self, extended_mode=extended_mode)

        self.toolbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.setAlignment(self.toolbar, Qt.AlignHCenter)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.toolbar.setVisible(False)

    def set_spectrum1(self, data, label=None):
        if label is not None:
            self.canvas.spectrum1_label = str(label)
        self.canvas.spectrum1 = data

    def set_spectrum2(self, data, label=None):
        if label is not None:
            self.canvas.spectrum2_label = str(label)
        self.canvas.spectrum2 = data

    def __getattr__(self, item):
        return getattr(self.canvas, item)


class ExtendedSpectrumWidget(SpectrumWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, extended_mode=True, **kwargs)
