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


class WorkerSet(set):
    """A set that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

    def parent(self):
        return self._parent

    def _pre_add(self):
        if not self:  # dict is empty, so we are going to create the first entry. Show the progress bar
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().addPermanentWidget(self.parent().widgetProgress)
            self.parent().widgetProgress.setVisible(True)

    def _post_add(self, worker):
        thread = QThread(self.parent())
        worker.moveToThread(thread)
        self.parent().btCancelProcess.pressed.connect(lambda: worker.stop())
        # remove_worker = lambda: self.remove(worker)
        worker.finished.connect(lambda: self.remove(worker))
        worker.canceled.connect(lambda: self.remove(worker))
        worker.error.connect(lambda: self.remove(worker))
        thread.started.connect(worker.run)
        thread.start()

    def _pre_remove(self, worker):
        pass

    def _post_remove(self):
        if not self:  # dict is now empty, hide the progress bar
            self.parent().widgetProgress.setVisible(False)
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().removeWidget(self.parent().widgetProgress)

    def add(self, worker):
        self._pre_add()
        super().add(worker)
        self._post_add(worker)

    def update(self, workers):
        self._pre_add()
        super().update(workers)
        for worker in workers:
            self._post_add(worker)

    def remove(self, worker):
        if worker in self:
            self._pre_remove(worker)
            super().remove(worker)
            self._post_remove()
