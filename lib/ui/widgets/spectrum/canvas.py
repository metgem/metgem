from matplotlib.ticker import FuncFormatter, AutoMinorLocator

import numpy as np

if __name__ == '__main__':
    from base import BaseCanvas
    class Spectrum:
        MZ = 0
        INTENSITY = 1
else:
    from .base import BaseCanvas
    from ....workers import Spectrum


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
        self.set_spectrum1(spectrum1_data)
        self.set_spectrum2(spectrum2_data)

        self.prepare_axes()

    def has_data(self):
        return self._spectrum1_data is not None

    def prepare_axes(self, data=None):
        super().prepare_axes(data)

        # Y Tick labels should be always positive
        self.axes.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{abs(x):.0f}'))

        # Place X minor ticks
        self.axes.xaxis.set_minor_locator(AutoMinorLocator())

    def _set_data(self, type_, data, label=None):
        self.axes.clear()

        if type_ == 'spectrum1':
            self._spectrum1_data = data
            self._spectrum1_label = label
        else:
            self._spectrum2_data = data
            self._spectrum2_label = label

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
            else:
                self._spectrum2_plot = None

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

    def spectrum1(self):
        return self._spectrum1_data, self._spectrum1_label

    def set_spectrum1(self, data, label=None):
        self._set_data('spectrum1', data, label)

    def spectrum2(self):
        return self._spectrum2_data, self._spectrum2_label

    def set_spectrum2(self, data, label=None):
        self._set_data('spectrum2', data, label)

    def auto_adjust_ylim(self):
        if self.has_data():
            xlim = self.axes.get_xlim()
            intensities = self._spectrum1_data[:, Spectrum.INTENSITY][
                np.logical_and(self._spectrum1_data[:, Spectrum.MZ] >= xlim[0],
                               self._spectrum1_data[:, Spectrum.MZ] <= xlim[1])]
            max_ = intensities.max() if intensities.size > 0 else 0

            if self._spectrum2_data is not None:
                intensities = self._spectrum2_data[:, Spectrum.INTENSITY][
                    np.logical_and(self._spectrum2_data[:, Spectrum.MZ] >= xlim[0],
                                   self._spectrum2_data[:, Spectrum.MZ] <= xlim[1])]
                min_ = intensities.max() if intensities.size > 0 else 0
            else:
                min_ = 0

            self.axes.set_ylim(-min_ - self.Y_SPACING, max_ + self.Y_SPACING)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton

    test_data = np.array([(413.2566833496094, 10), (452.5115661621094, 73),
                          (453.51629638671875, 15), (466.2967224121094, 3),
                          (466.51702880859375, 4), (468.5006103515625, 3),
                          (478.3836364746094, 3), (488.2716369628906, 19),
                          (502.2874450683594, 3), (510.25146484375, 12),
                          (522.5934448242188, 16), (523.4685668945312, 12),
                          (536.016845703125, 3), (537.0192260742188, 9),
                          (544.9962158203125, 4), (549.4879150390625, 11),
                          (551.0189819335938, 6), (563.5028686523438, 48),
                          (564.5081176757812, 10), (575.5017700195312, 3),
                          (577.5186767578125, 11), (589.5211181640625, 7),
                          (591.5034790039062, 8), (592.5388793945312, 3),
                          (603.5335693359375, 7), (658.4512329101562, 3),
                          (664.4981079101562, 3), (672.46337890625, 7),
                          (686.4786376953125, 36), (691.2647094726562, 8),
                          (694.4434814453125, 4), (698.4788818359375, 6),
                          (700.493896484375, 5), (704.5325927734375, 10),
                          (708.45751953125, 27), (712.4949951171875, 28),
                          (714.5094604492188, 8), (720.4577026367188, 4),
                          (722.4723510742188, 4), (726.5132446289062, 100),
                          (727.520751953125, 28), (734.4771118164062, 24),
                          (736.4967041015625, 5), (738.51025390625, 10),
                          (740.5271606445312, 27), (742.487060546875, 5),
                          (743.4899291992188, 5), (748.4940795898438, 89),
                          (749.5020141601562, 17), (752.5279541015625, 22),
                          (754.5435791015625, 21), (758.5093383789062, 5),
                          (760.4962158203125, 6), (762.5086059570312, 24),
                          (764.4684448242188, 6), (765.4764404296875, 6),
                          (766.5445556640625, 20), (771.5205688476562, 3),
                          (774.5076293945312, 17), (776.5237426757812, 15),
                          (778.4954223632812, 3), (779.4884033203125, 12),
                          (782.5361328125, 3), (785.5362548828125, 4),
                          (788.525146484375, 16), (793.5059814453125, 5),
                          (796.55224609375, 8), (797.53564453125, 3),
                          (802.5390014648438, 3), (804.5169677734375, 3),
                          (805.498779296875, 3), (807.5198974609375, 4),
                          (818.5345458984375, 11), (859.5935668945312, 3),
                          (907.3575439453125, 5), (911.4693603515625, 3),
                          (924.4972534179688, 3), (1086.5140380859375, 6),
                          (1235.772705078125, 3), (1253.8197021484375, 6),
                          (1275.807373046875, 9), (1433.981689453125, 4),
                          (1452.0233154296875, 3), (1460.004150390625, 5),
                          (1474.0247802734375, 13), (1478.0467529296875, 4),
                          (1486.023193359375, 3), (1488.0406494140625, 4),
                          (1492.06396484375, 10), (1500.0445556640625, 8),
                          (1502.05615234375, 4), (1506.0709228515625, 4),
                          (1514.06396484375, 19), (1519.08642578125, 3),
                          (1526.067626953125, 3), (1528.0831298828125, 7),
                          (1532.0906982421875, 3), (1539.0859375, 3),
                          (1541.09326171875, 5), (1554.1014404296875, 4)])

    def compare_spectra():
        if canvas.spectrum2()[0] is None:
            canvas.set_spectrum2(test_data)
            button.setText('Show single spectrum')
        else:
            canvas.set_spectrum2(None)
            button.setText('Compare spectra')


    app = QApplication(sys.argv)
    win = QMainWindow()
    widget = QWidget()
    layout = QVBoxLayout(widget)

    win.setCentralWidget(widget)
    widget.setLayout(layout)

    canvas = SpectrumCanvas(title='Long long name Test spectrum')
    canvas.set_spectrum1(test_data)
    layout.addWidget(canvas)

    button = QPushButton('Compare spectra')
    button.pressed.connect(compare_spectra)
    layout.addWidget(button)

    win.show()
    sys.exit(app.exec_())
