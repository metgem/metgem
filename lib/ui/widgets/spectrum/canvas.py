from PyQt5.QtCore import pyqtProperty

from matplotlib.ticker import FuncFormatter, AutoMinorLocator

import numpy as np

from .base import BaseCanvas, MZ, INTENSITY


class SpectrumCanvas(BaseCanvas):

    def __init__(self, parent=None, spectrum1_data=None, spectrum2_data=None, title=None):
        self._spectrum1_data = None
        self._spectrum2_data = None
        self._spectrum1_label = None
        self._spectrum2_label = None
        self._spectrum1_plot = None
        self._spectrum2_plot = None

        super().__init__(parent, title=title)

        if self.toolbar is not None:
            self.toolbar.setVisible(False)

        # Load data
        self.spectrum1 = spectrum1_data
        self.spectrum2 = spectrum2_data

        self.prepare_axes()

    def has_data(self):
        return self._spectrum1_data is not None

    def prepare_axes(self, data=None):
        super().prepare_axes(data)

        # Y Tick labels should be always positive
        self.axes.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{abs(x):.0f}'))

        # Place X minor ticks
        self.axes.xaxis.set_minor_locator(AutoMinorLocator())

    def _set_data(self, type_, data):
        self.axes.clear()

        if type_ == 'spectrum1':
            self._spectrum1_data = data
        else:
            self._spectrum2_data = data

        if self._spectrum2_data is not None:
            self.axes.set_ylim(-100 - self.Y_SPACING, 100 + self.Y_SPACING)
        else:
            self.axes.set_ylim(0, 100 + self.Y_SPACING)

        self.prepare_axes(self._spectrum1_data)
        if self.has_data():
            if self.toolbar is not None:
                self.toolbar.setVisible(True)

            self._spectrum1_plot = self.plot_spectrum(self._spectrum1_data, colors='r', label=self._spectrum1_label)
            if self._spectrum2_data is not None:
                self._spectrum2_plot = self.plot_spectrum(self._spectrum2_data, yinverted=True, colors='b',
                                                          label=self._spectrum2_label)
                self.axes.set_xmax(max(self._spectrum1_data.max(), self._spectrum2_data.max()) + 50)
            else:
                self._spectrum2_plot = None
                self.axes.set_xmax(self._spectrum1_data.max() + 50)

            self.axes.axhline(0, color='k', linewidth=0.5)
            handles = [handle for handle, label in ((self._spectrum1_plot, self._spectrum1_label),
                                                    (self._spectrum2_plot, self._spectrum2_label))
                       if handle is not None and label is not None]
            if len(handles) > 0:
                self.axes.legend(handles=handles)
            self.dataLoaded.emit()
        else:
            if self.toolbar is not None:
                self.toolbar.setVisible(False)
            self._spectrum1_plot = None
            self._spectrum2_plot = None

        self.draw()

    @pyqtProperty(np.ndarray)
    def spectrum1(self):
        return self._spectrum1_data

    @spectrum1.setter
    def spectrum1(self, data):
        self._set_data('spectrum1', data)

    @pyqtProperty(str)
    def spectrum1_label(self):
        return self._spectrum1_label

    @spectrum1_label.setter
    def spectrum1_label(self, label):
        self._spectrum1_label = label
        if self._spectrum1_plot is not None:
            self._spectrum1_plot.set_label(label)

    @pyqtProperty(np.ndarray)
    def spectrum2(self):
        return self._spectrum2_data

    @spectrum2.setter
    def spectrum2(self, data):
        self._set_data('spectrum2', data)

    @pyqtProperty(str)
    def spectrum2_label(self):
        return self._spectrum2_label

    @spectrum2_label.setter
    def spectrum2_label(self, label):
        self._spectrum2_label = label
        if self._spectrum2_plot is not None:
            self._spectrum2_plot.set_label(label)

    def auto_adjust_ylim(self):
        if self.has_data():
            xlim = self.axes.get_xlim()
            intensities = self._spectrum1_data[:, INTENSITY][
                np.logical_and(self._spectrum1_data[:, MZ] >= xlim[0],
                               self._spectrum1_data[:, MZ] <= xlim[1])]
            max_ = intensities.max() if intensities.size > 0 else 0

            if self._spectrum2_data is not None:
                intensities = self._spectrum2_data[:, INTENSITY][
                    np.logical_and(self._spectrum2_data[:, MZ] >= xlim[0],
                                   self._spectrum2_data[:, MZ] <= xlim[1])]
                min_ = intensities.max() if intensities.size > 0 else 0
            else:
                min_ = 0

            self.axes.set_ylim(-min_ - self.Y_SPACING, max_ + self.Y_SPACING)
