import itertools


class AttrDict(dict):
    """A frozen dictionary where item can be accessed as attributes."""
    
    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError
    
    def __setattr__(self, item, value):
        return self.__setitem__(item, value)
    
    def __setitem__(self, item, value):
        if item not in self:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))
        super().__setitem__(item, value)

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        super().update(state)

    def __reduce__(self):
        return self.__class__, (), self.__getstate__()
        
    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]

    def update(self, data, **kwargs):
        data = {k: v for k, v in data.items() if k in self}
        super().update(data)

    def copy(self):
        return AttrDict(self)


class Network:
    __slots__ = 'spectra', 'scores', 'infos'


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


class BoundingBox:
    def __init__(self, layout):
        self.left, self.top = layout.min(axis=0)
        self.right, self.bottom = layout.max(axis=0)
        self.height = self.bottom - self.top
        self.width = self.right - self.left

    def __repr__(self):
        return f"{self.__class__.__name__}-> left:{self.left}, right:{self.right}, " \
               f"top:{self.top}, bottom: {self.bottom}, " \
               f"height:{self.height}, width: {self.width}"


class SignalBlocker:
    """Context Manager to temporarily block signals from given Qt's widgets"""

    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for widget in self.widgets:
            widget.blockSignals(True)

    def __exit__(self, *args):
        for widget in self.widgets:
            widget.blockSignals(False)
