from matplotlib.axes import Axes
from matplotlib.projections import register_projection


class SpectrumAxes(Axes):
    name = 'spectrum_axes'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fmt_xdata = lambda x: '{:.4f}'.format(x)
        self.fmt_ydata = lambda y: '{:.0f}%'.format(y)

        self.__xmax = None
    
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
        return '<i>m/z</i> {}, intensity={}'.format(xs, ys.replace('-', ''))

    def get_xmax(self):
        return self.__xmax

    def set_xmax(self, max):
        self.set_xlim(0, max)
        self.__xmax = max

    def drag_pan(self, button, key, x, y):
        xlim = self.get_xlim()
        super().drag_pan(button, 'x', x, y)  # pretend key=='x' to prevent Y axis range to change
        xlim_new = self.get_xlim()
        if self.__xmax is not None and xlim_new[0] < 0 or xlim_new[1] > self.__xmax:
            # If xlim is outside allowed range, roll-back
            self.set_xlim(xlim)


register_projection(SpectrumAxes)
