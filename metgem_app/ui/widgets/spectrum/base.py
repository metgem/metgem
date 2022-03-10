from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from qtpy.QtCore import Signal, Qt
from qtpy.QtWidgets import QSizePolicy

from libmetgem import MZ, INTENSITY

import numpy as np

try:
    # noinspection PyUnresolvedReferences
    import mplcursors
except ImportError:
    HAS_MPLCURSORS = False
else:
    HAS_MPLCURSORS = True


class BaseCanvas(FigureCanvas):
    dataRequested = Signal()
    dataLoaded = Signal()
    dataCleared = Signal()

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

    def has_data(self):
        """Is data loaded, should be reimplemented in subclass"""
        return False

    def prepare_axes(self, data=None):
        """Prepare default axes"""

        if data is None:
            return

        if self._title is not None:
            self.axes.set_title(self._title, self.fontdict, loc='right')

        self.axes.set_xlabel("$m/z$", self.fontdict)
        self.axes.set_ylabel("Normalized Intensity (%)", self.fontdict)

        if self.has_data():
            self.axes.set_xlim((data[:, MZ].min() - self.X_MARGIN,
                                data[:, MZ].max() + self.X_MARGIN))
        else:
            self.axes.set_xlim(0, 1000)

    def plot_spectrum(self, data, yinverted=False, **kwargs):
        if data is None:
            return

        if yinverted:
            vlines = self.axes.vlines(data[:, MZ], 0, np.negative(data[:, INTENSITY]),
                                      linewidth=0.5, **kwargs)
        else:
            vlines = self.axes.vlines(data[:, MZ], 0, data[:, INTENSITY],
                                      linewidth=0.5, **kwargs)

        if HAS_MPLCURSORS:
            cursor = mplcursors.cursor(vlines)

            @cursor.connect('add')
            def on_add(sel):
                sel.annotation.set_text(sel.annotation.get_text().replace('<i>m/z</i>\n', '$m/z$ '))
                sel.annotation.get_bbox_patch().set(fc="tab:gray")
                sel.annotation.arrow_patch.set(arrowstyle="-|>", alpha=.5)

        return vlines

    def auto_adjust_ylim(self):
        pass
