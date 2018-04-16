from PyQt5.QtCore import QThread

from .generic import GenericWorker
from ..ui.progress_dialog import ProgressDialog


class WorkerSet(set):
    """A set that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

        self.widgetProgress = ProgressDialog(self._parent)

    def parent(self):
        return self._parent

    def show_progressbar(self):
        if not self:  # dict is empty, so we are going to create the first entry. Show the progress bar
            self.widgetProgress.show()
            self.widgetProgress.setModal(True)

    def hide_progressbar(self):
        if not self:  # dict is now empty, hide the progress bar
            if self.widgetProgress is not None:
                self.widgetProgress.setModal(False)
                self.widgetProgress.close()

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

        self.widgetProgress.setValue(0)
        self.widgetProgress.setMinimum(0)
        self.widgetProgress.setMaximum(worker.max)
        if worker.max == 0:
            self.widgetProgress.setFormat(worker.desc)
        else:
            worker.started.connect(lambda: self.widgetProgress.setFormat(worker.desc.format(value=0, max=worker.max)))

        self.widgetProgress.rejected.connect(lambda: worker.stop())
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
        if worker.thread() != self.parent().thread():
            worker.thread().quit()
        if worker in self:
            super().remove(worker)

            self.hide_progressbar()

