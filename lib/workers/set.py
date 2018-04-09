from PyQt5.QtCore import QThread

from ..ui.progress_dialog import ProgressDialog


class WorkerSet(set):
    """A set that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

        self.widgetProgress = None

    def parent(self):
        return self._parent

    def show_progressbar(self):
        if not self:  # dict is empty, so we are going to create the first entry. Show the progress bar
            self.widgetProgress = ProgressDialog(self._parent)
            self.widgetProgress.show()

    def hide_progressbar(self):
        if not self:  # dict is now empty, hide the progress bar
            if self.widgetProgress is not None:
                self.widgetProgress.hide()
                self.widgetProgress.deleteLater()
                self.widgetProgress = None

    def update_progress(self, i, worker):
        if self.widgetProgress is not None:
            if worker.iterative_update:
                self.widgetProgress.setValue(self.widgetProgress.value() + i)
            else:
                self.widgetProgress.setValue(i)

            self.widgetProgress.setFormat(worker.desc.format(value=i, max=worker.max))

    def update_maximum(self, maximum):
        if self.widgetProgress is not None:
            self.widgetProgress.setMaximum(maximum)

    def connect_events(self, worker):
        thread = QThread(self.parent())
        worker.moveToThread(thread)

        if self.widgetProgress is not None:
            self.widgetProgress.setValue(0)
            self.widgetProgress.setMinimum(0)
            self.widgetProgress.setMaximum(worker.max)

            self.widgetProgress.rejected.connect(lambda: worker.stop())

        worker.finished.connect(lambda: self.remove(worker))
        worker.canceled.connect(lambda: self.remove(worker))
        worker.error.connect(lambda: self.remove(worker))
        worker.updated.connect(lambda i: self.update_progress(i, worker))
        worker.maximumChanged.connect(self.update_maximum)
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
