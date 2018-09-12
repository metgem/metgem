from PyQt5.QtCore import QThread

from .generic import GenericWorker


class WorkerSet(set):
    """A set that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

        self.widgetProgress = widget

    def parent(self):
        return self._parent

    def show_progressbar(self, worker):
        if worker.track_progress and not self.widgetProgress.isVisible():
            self.widgetProgress.setModal(True)
            self.widgetProgress.show()

    def hide_progressbar(self):
        if not self:  # dict is now empty, hide the progress bar
            if self.widgetProgress is not None:
                self.widgetProgress.close()
                self.widgetProgress.setModal(False)

    def update_progress(self, i, worker):
        if worker.iterative_update:
            self.widgetProgress.setValue(self.widgetProgress.value() + i)
        else:
            self.widgetProgress.setValue(i)

        self.widgetProgress.setFormat(worker.desc.format(value=i, max=worker.max))

    def update_maximum(self, maximum):
        self.widgetProgress.setMaximum(maximum)

    def connect_events(self, worker):
        use_thread = not isinstance(worker, GenericWorker)

        if use_thread:
            thread = QThread(self.parent())
            worker.moveToThread(thread)
            thread.setPriority(QThread.IdlePriority)

        self.widgetProgress.setValue(0)
        self.widgetProgress.setMinimum(0)
        self.widgetProgress.setMaximum(worker.max)
        if worker.max == 0:
            self.widgetProgress.setFormat(worker.desc)
        else:
            worker.started.connect(lambda: self.widgetProgress.setFormat(worker.desc.format(value=0, max=worker.max)))

        self.widgetProgress.rejected.connect(lambda: worker.stop())
        worker.started.connect(lambda: self.show_progressbar(worker))
        worker.finished.connect(lambda: self.remove(worker))
        worker.canceled.connect(lambda: self.remove(worker))
        worker.error.connect(lambda: self.remove(worker))
        worker.updated.connect(lambda i: self.update_progress(i, worker))
        worker.maximumChanged.connect(self.update_maximum)

        if use_thread:
            thread.started.connect(worker.start)
            thread.start()
        else:
            worker.start()

    def add(self, worker):
        super().add(worker)

        self.connect_events(worker)

    def update(self, workers):
        super().update(workers)

        for worker in workers:
            self.connect_events(worker)

    def remove(self, worker):
        if worker.thread() != self.parent().thread():
            worker.thread().quit()
        if worker in self:
            super().remove(worker)
            self.hide_progressbar()

