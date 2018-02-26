from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QSizePolicy

try:
    from .axes import SpectrumAxes
    from ....workers import Spectrum
except:
    from axes import SpectrumAxes
    class Spectrum:
        MZ = 0
        INTENSITY = 1

import numpy as np


class BaseCanvas(FigureCanvas):
    dataRequested = pyqtSignal()
    dataLoaded = pyqtSignal()
    
    X_SPACING = 10
    X_MARGIN = 50
    Y_SPACING = 1
    
    def __init__(self, parent=None, title=None):
        # Create figure and axes
        fig = Figure()
        self.axes = fig.add_subplot(111, projection='spectrum_axes')

        # Initialize canvas
        super().__init__(fig)
        self.setParent(parent)

        # Set Default Y range
        self.axes.set_ylim(0, 100 + self.Y_SPACING)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Expanding)
        self.setMinimumWidth(300)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Font parameters used for axis labels
        self.fontdict = {'size': 8}

        # Adjust subplots size
        fig.subplots_adjust(left=0.2, bottom=0.2)
        
        # Spectrum title
        self._title = title
    
    def hasData(self):
        """Is data loaded, should be reimplemented in subclass"""
        return False
        
    def prepareAxes(self, data=None):
        """Prepare default axes"""

        if data is None:
            return

        if self._title:
            self.axes.set_title(self._title, self.fontdict, loc='right')
            
        self.axes.set_xlabel("$m/z$", self.fontdict)
        self.axes.set_ylabel("Normalized Intensity (%)", self.fontdict)
            
        if self.hasData():
            self.axes.set_xlim((data[:, Spectrum.MZ].min()-self.X_MARGIN,
                                data[:, Spectrum.MZ].max()+self.X_MARGIN))
        else:
            self.axes.set_xlim(0, 1000)
                                
    def plotSpectrum(self, data, yinverted=False, **kwargs):
        if data is None:
            return

        if yinverted:
            return self.axes.vlines(data[:, Spectrum.MZ], 0, np.negative(data[:, Spectrum.INTENSITY]),
                                    linewidth=0.5, **kwargs)
        else:
            return self.axes.vlines(data[:, Spectrum.MZ], 0, data[:, Spectrum.INTENSITY],
                                    linewidth=0.5, **kwargs)
    
    def autoAdjustYLim(self):
        pass
