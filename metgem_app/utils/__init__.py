import itertools
import os
import subprocess
import sys

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .emf_export import HAS_EMF_EXPORT

if HAS_EMF_EXPORT:
    from .emf_export import EMFPaintDevice, EMFPaintEngine


class AttrDict(dict):
    """A dictionary where item can be accessed as attributes."""
    
    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError as e:
            raise AttributeError(e)
    
    def __setattr__(self, item, value):
        return self.__setitem__(item, value)

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


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


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


class SignalGrouper(QObject):
    """Accumulate signals and emit a signal with all the senders after a timeout"""

    groupped = pyqtSignal(set)

    def __init__(self, timeout=100):
        super().__init__()
        self.senders = set()
        self.timer = None
        self.timeout = timeout

    # noinspection PyUnusedLocal
    def accumulate(self, *args):
        if not self.senders:
            def emit_signal():
                self.groupped.emit(self.senders)
                self.timer = None
                self.senders = set()

            self.timer = QTimer()
            self.timer.singleShot(self.timeout, emit_signal)

        self.senders.add(self.sender())


def open_folder(path: str):
    """Open a folder in file manager"""

    if sys.platform.startswith('win'):
        os.startfile(path)
    elif sys.platform.startswith('darwin'):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def enumerateMenu(menu: 'QMenu'):
    for action in menu.actions():
        if action.menu() is not None:
            yield from enumerateMenu(action.menu())
        elif not action.isSeparator():
            yield action


def hasinstance(collection: list, type_: type):
    """Check if a collection has a member"""

    for item in collection:
        if isinstance(item, type_):
            return True
    return False
