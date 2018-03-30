import itertools

from PyQt5.QtCore import QThread


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


class WorkerSet(set):
    """A set that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

    def parent(self):
        return self._parent

    def show_progressbar(self):
        if not self:  # dict is empty, so we are going to create the first entry. Show the progress bar
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().addPermanentWidget(self.parent().widgetProgress)
            self.parent().widgetProgress.setVisible(True)

    def hide_progressbar(self):
        if not self:  # dict is now empty, hide the progress bar
            self.parent().widgetProgress.setVisible(False)
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().removeWidget(self.parent().widgetProgress)

    def connect_events(self, worker):
        thread = QThread(self.parent())
        worker.moveToThread(thread)

        self.parent().btCancelProcess.pressed.connect(lambda: worker.stop())
        worker.finished.connect(lambda: self.remove(worker))
        worker.canceled.connect(lambda: self.remove(worker))
        worker.error.connect(lambda: self.remove(worker))
        thread.started.connect(worker.run)

        thread.start()

    def add(self, worker):
        if worker.track_progress:
            self.show_progressbar()

        super().add(worker)

        self.connect_events(worker)

    def update(self, workers):
        show_progress = False
        for worker in workers:
            if worker.track_progress:
                show_progress = True
                break
        if show_progress:
            self.show_progressbar()

        super().update(workers)

        for worker in workers:
            self.connect_events(worker)

    def remove(self, worker):
        if worker in self:
            super().remove(worker)

            self.hide_progressbar()
