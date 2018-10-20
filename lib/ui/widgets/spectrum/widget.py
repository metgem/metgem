from PyQt5.QtCore import Qt, pyqtProperty
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QVBoxLayout

from .toolbar import SpectrumNavigationToolbar
from .canvas import SpectrumCanvas


class SpectrumWidget(QWidget):

    def __init__(self, *args, extended_mode=False, orientation=Qt.Horizontal, **kwargs):
        super().__init__(*args, **kwargs)

        self.canvas = SpectrumCanvas(self)
        self.toolbar = SpectrumNavigationToolbar(self.canvas, self, extended_mode=extended_mode)
        self.toolbar.setOrientation(orientation)
        self.toolbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout() if orientation == Qt.Vertical else QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.setAlignment(self.toolbar, Qt.AlignHCenter)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.toolbar.setVisible(False)

    @pyqtProperty(str)
    def spectrum1_parent(self):
        return self.canvas.spectrum1_parent

    @spectrum1_parent.setter
    def spectrum1_parent(self, mz):
        self.canvas.spectrum1_parent = mz

    def set_spectrum1(self, data, idx=None, parent=None):
        if data is not None:
            self.canvas.spectrum1_index = idx
            self.canvas.spectrum1_parent = parent
            self.canvas.spectrum1 = data
        else:
            self.canvas.spectrum1_index = None
            self.canvas.spectrum1_parent = None
            self.canvas.spectrum1 = None

    def set_spectrum2(self, data, idx=None, parent=None):
        if data is not None:
            self.canvas.spectrum2_index = idx
            self.canvas.spectrum2_parent = parent
            self.canvas.spectrum2 = data
        else:
            self.canvas.spectrum2_index = None
            self.canvas.spectrum2_parent = None
            self.canvas.spectrum2 = None

    def set_title(self, title):
        self.canvas.title = title

    def __getattr__(self, item):
        return getattr(self.canvas, item)


class ExtendedSpectrumWidget(SpectrumWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, extended_mode=True, orientation=Qt.Vertical, **kwargs)
