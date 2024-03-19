from enum import Enum

# noinspection PyUnresolvedReferences
from PySide6.QtCore import QSettings

from matplotlib.ticker import FuncFormatter, AutoMinorLocator

import numpy as np

from metgem.ui.widgets.spectrum.base import BaseCanvas
from libmetgem import MZ, INTENSITY


class SpectrumPosition(Enum):
    first = 0
    second = 1


class SpectrumCanvas(BaseCanvas):
    first_spectrum_label = None
    second_spectrum_label = None

    def __init__(self, parent=None, spectrum1_data=None, spectrum2_data=None, title=None):
        self._spectrum1_data = None
        self._spectrum2_data = None
        self._spectrum1_parent = None
        self._spectrum2_parent = None
        self._spectrum1_idx = None
        self._spectrum2_idx = None
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

    def showEvent(self, event):
        try:
            super().showEvent(event)
        except RuntimeError:
            # workaround for "RuntimeError: Internal C++ object (PySide6.QtGui.QWindow) already deleted."
            pass

    def has_data(self):
        return self._spectrum1_data is not None

    def prepare_axes(self, data=None):
        super().prepare_axes(data)

        # Y Tick labels should be always positive
        self.axes.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{abs(x):.0f}'))

        # Place X minor ticks
        self.axes.xaxis.set_minor_locator(AutoMinorLocator())

    def format_label(self, spectrum_pos: SpectrumPosition = SpectrumPosition.first):
        label = self._spectrum1_label if spectrum_pos == SpectrumPosition.first else self._spectrum2_label
        parent = self._spectrum1_parent if spectrum_pos == SpectrumPosition.first else self._spectrum2_parent

        if label is not None:
            if parent is not None:
                float_precision = QSettings().value('Metadata/float_precision', 4, type=int)
                return f"{label} ($m/z$ {parent:.{float_precision}f})"
            else:
                return f"{label}"
        else:
            return self.first_spectrum_label if spectrum_pos == SpectrumPosition.first else self.second_spectrum_label

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

            label = self.format_label(SpectrumPosition.first)
            self._spectrum1_plot = self.plot_spectrum(self._spectrum1_data, colors='r', label=label)
            if self._spectrum2_data is not None:
                label = self.format_label(SpectrumPosition.second)
                self._spectrum2_plot = self.plot_spectrum(self._spectrum2_data, yinverted=True,
                                                          colors='b', label=label)
                self.axes.set_xmax(max(self._spectrum1_data.max(), self._spectrum2_data.max()) + 50)
            else:
                self._spectrum2_plot = None
                self.axes.set_xmax(self._spectrum1_data.max() + 50)

            self.axes.axhline(0, color='k', linewidth=0.5)
            handles = [handle for handle in (self._spectrum1_plot, self._spectrum2_plot)
                       if handle is not None and handle.get_label() is not None
                       and not handle.get_label().startswith('_')]
            if len(handles) > 0:
                self.axes.legend(handles=handles,
                                 bbox_to_anchor=(0, -0.4),
                                 loc='upper left',
                                 ncol=2,
                                 borderaxespad=0,
                                 frameon=False,
                                 fontsize='small')
            self.dataLoaded.emit()
        else:
            if self.toolbar is not None:
                self.toolbar.setVisible(False)
            self._spectrum1_plot = None
            self._spectrum2_plot = None
            self.dataCleared.emit()

        self.draw()

    def draw(self):
        super().draw()
        self.figure.subplots_adjust(bottom=0.4)

    @property
    def spectrum1(self):
        return self._spectrum1_data

    @spectrum1.setter
    def spectrum1(self, data):
        self._set_data('spectrum1', data)

    @property
    def spectrum1_parent(self):
        return self._spectrum1_parent

    @spectrum1_parent.setter
    def spectrum1_parent(self, mz):
        try:
            self._spectrum1_parent = float(mz)
            if self._spectrum1_plot is not None:
                self._spectrum1_plot.set_label(self.format_label(SpectrumPosition.first))
        except TypeError:
            pass

    @property
    def spectrum1_index(self):
        return self._spectrum1_idx

    @spectrum1_index.setter
    def spectrum1_index(self, idx):
        self._spectrum1_idx = idx

    @property
    def spectrum1_label(self):
        return self._spectrum1_label

    @spectrum1_label.setter
    def spectrum1_label(self, label):
        self._spectrum1_label = label
        if self._spectrum1_plot is not None:
            self._spectrum1_plot.set_label(self.format_label(SpectrumPosition.first))

    @property
    def spectrum2(self):
        return self._spectrum2_data

    @spectrum2.setter
    def spectrum2(self, data):
        self._set_data('spectrum2', data)

    @property
    def spectrum2_parent(self):
        return self._spectrum2_parent

    @spectrum2_parent.setter
    def spectrum2_parent(self, mz):
        self._spectrum2_parent = mz
        if self._spectrum2_plot is not None:
            self._spectrum2_plot.set_label(self.format_label(SpectrumPosition.second))

    @property
    def spectrum2_index(self):
        return self._spectrum2_idx

    @spectrum2_index.setter
    def spectrum2_index(self, idx):
        self._spectrum2_idx = idx

    @property
    def spectrum2_label(self):
        return self._spectrum1_label

    @spectrum2_label.setter
    def spectrum2_label(self, label):
        self._spectrum1_label = label
        if self._spectrum2_plot is not None:
            self._spectrum2_plot.set_label(self.format_label(SpectrumPosition.second))


    @property
    def spectrum1_plot(self):
        return self._spectrum1_plot

    @property
    def spectrum2_plot(self):
        return self._spectrum2_plot

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

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

    def get_supported_filetypes(self):
        types = super().get_supported_filetypes()
        types['mgf'] = 'Mascot Generic Format'
        types['msp'] = 'NIST Text Format of Individual Spectra'
        return types

    def get_supported_filetypes_grouped(self):
        types = super().get_supported_filetypes_grouped()
        types['Mascot Generic Format'] = ['mgf']
        types['NIST Text Format of Individual Spectra'] = ['msp']
        return types

    def get_default_filetype(self):
        return 'mgf'

    # noinspection PyPropertyAccess
    def get_default_filename(self):
        if self.spectrum1 is not None and self.spectrum2 is not None:
            if self.spectrum1_index is not None and self.spectrum2_index is not None:
                return f"spectra{self.spectrum1_index}_{self.spectrum2_index}.mgf"
            else:
                return "spectra.mgf"

        if self.spectrum1 is not None or self.spectrum2 is not None:
            idx = self.spectrum1_index if self.spectrum1_index is not None else self.spectrum2_index
            if idx is not None:
                return f"spectrum{idx}.mgf"

        return "spectrum.mgf"

    # noinspection PyUnusedLocal
    def print_mgf(self, fname, **kwargs):
        # noinspection PyShadowingNames
        def save_mgf(f, pepmass, data):
            if data is not None:
                f.write("BEGIN IONS\n")
                if pepmass is not None:
                    f.write(f"PEPMASS={pepmass}\n")
                for row in np.sort(data, axis=0):
                    f.write(f"{row[MZ]}\t{row[INTENSITY]}\n")
                f.write("END IONS\n")
                f.write("\n")

        if self.spectrum1 is not None or self.spectrum2 is not None:
            with open(fname, 'w', encoding="utf-8") as f:
                save_mgf(f, self.spectrum1_parent, self.spectrum1)
                save_mgf(f, self.spectrum2_parent, self.spectrum2)

    # noinspection PyUnusedLocal
    def print_msp(self, fname, **kwargs):
        # noinspection PyShadowingNames
        def save_msp(f, pepmass, data):
            if data is not None:
                if pepmass is not None:
                    f.write(f"PRECURSORMZ: {pepmass}\n")
                num_peaks = len(data)
                if num_peaks > 0:
                    f.write(f"Num Peaks: {num_peaks}\n")
                for row in np.sort(data, axis=0):
                    f.write(f"{row[MZ]}\t{row[INTENSITY]}\n")
                f.write("\n")

        if self.spectrum1 is not None or self.spectrum2 is not None:
            with open(fname, 'w', encoding="utf-8") as f:
                save_msp(f, self.spectrum1_parent, self.spectrum1)
                save_msp(f, self.spectrum2_parent, self.spectrum2)

