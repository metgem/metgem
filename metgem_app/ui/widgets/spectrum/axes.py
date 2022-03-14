from qtpy.QtCore import QSettings
from matplotlib.axes import Axes
from matplotlib.projections import register_projection

import numpy as np


class SpectrumAxes(Axes):
    name = 'spectrum_axes'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        float_precision = QSettings().value('Metadata/float_precision', 4, type=int)
        self.fmt_xdata = lambda x: f'{x:.{float_precision}f}'
        self.fmt_ydata = lambda y: f'{y:.0f}%'

        self._xmax = None
    
    def format_coord(self, x, y):
        """Return a format string formatting the *x*, *y* coord"""
        if x is None:
            xs = '???'
        else:
            xs = self.format_xdata(x)
        if y is None:
            ys = '???'
        else:
            ys = self.format_ydata(y)
        return f"<i>m/z</i> {xs}, intensity={ys.replace('-', '')}"

    def get_xmax(self):
        return self._xmax

    # noinspection PyShadowingBuiltins
    def set_xmax(self, max):
        super().set_xlim(0, max)
        self._xmax = max

    def set_xlim(self, left=None, right=None, emit=True, auto=False, **kw):
        if hasattr(self, '_xmax') and self._xmax is not None:
            if isinstance(left, (tuple, list, np.ndarray)):
                left, right = left
            if left < 0 or right > self._xmax or right - left < 10:
                return
        super().set_xlim(left, right, emit, auto, **kw)


register_projection(SpectrumAxes)
