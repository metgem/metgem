from PyQt5.QtCore import QThread


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

    def update_progress(self, i, worker):
        if worker.iterative_update:
            self.parent().progressBar.setValue(self.parent().progressBar.value() + i)
        else:
            self.parent().progressBar.setValue(i)

        self.parent().progressBar.setFormat(worker.desc.format(value=i, max=worker.max))

    def connect_events(self, worker):
        thread = QThread(self.parent())
        worker.moveToThread(thread)

        self.parent().progressBar.setMinimum(0)
        self.parent().progressBar.setMaximum(worker.max)

        self.parent().btCancelProcess.pressed.connect(lambda: worker.stop())
        worker.finished.connect(lambda: self.remove(worker))
        worker.canceled.connect(lambda: self.remove(worker))
        worker.error.connect(lambda: self.remove(worker))
        worker.updated.connect(lambda i: self.update_progress(i, worker))
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
