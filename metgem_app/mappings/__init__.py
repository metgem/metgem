import numpy as np
from scipy.interpolate import interp1d

MODE_LINEAR = 0
MODE_LOG = 1


class SizeMappingFunc(dict):

    def __init__(self, xs, ys, ymin, ymax, mode=MODE_LINEAR):
        if mode == MODE_LOG:
            xsarr = np.array(xs)
            with np.errstate(divide='ignore'):
                xsarr = np.log10(xs)
            xsarr[np.isneginf(xsarr)] = 0
            f = interp1d(xsarr, ys, bounds_error=False, fill_value=(ymin, ymax), copy=False)

            def f2(x):
                return f(np.log10(x)) if x > 0 else ymin

            self._func = f2
        else:
            self._func = interp1d(xs, ys, bounds_error=False, fill_value=(ymin, ymax), copy=False)

        # Store values as items in a subclassed dict instead of attributes of the class to allow serialization (json)
        self.__setitem__('xs', xs)
        self.__setitem__('ys', ys)
        self.__setitem__('ymin', ymin)
        self.__setitem__('ymax', ymax)
        self.__setitem__('mode', mode)

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)