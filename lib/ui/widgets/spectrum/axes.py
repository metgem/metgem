from matplotlib.axes import Axes
from matplotlib.projections import register_projection


class SpectrumAxes(Axes):
    name = 'spectrum_axes'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fmt_xdata = lambda x: '{:.4f}'.format(x)
        self.fmt_ydata = lambda y: '{:.0f}%'.format(y)
    
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
        
    def drag_pan(self, button, key, x, y):
        super().drag_pan(button, 'x', x, y)  # pretend key=='x' to prevent Y axis range to change


register_projection(SpectrumAxes)
