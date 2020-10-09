from collections import deque

from PyQt5.QtCore import QThread

from .generic import GenericWorker


def isiterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


class WorkerQueue(deque):
    """A list that manages itself visibility of it's parent's progressbar"""

    def __init__(self, parent, widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent
        self._isrunning = False

        self.widgetProgress = widget

    def parent(self):
        return self._parent

    def is_running(self):
        return self._isrunning

    def show_progressbar(self, worker):
        if worker.track_progress and not self.widgetProgress.isVisible():
            self.widgetProgress.show()

    def hide_progressbar(self):
        if not self:  # deque is now empty, hide the progress bar
            if self.widgetProgress is not None:
                self.widgetProgress.hide()

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

        def cleanup():
            if worker.thread() != self.parent().thread():
                worker.thread().quit()

            # self.disconnect_events(worker)
            self._isrunning = False
            self.hide_progressbar()

        def update_progress(i):
            if worker.iterative_update:
                self.widgetProgress.setValue(self.widgetProgress.value() + i)
            else:
                self.widgetProgress.setValue(i)

            self.widgetProgress.setFormat(worker.desc.format(value=i, max=worker.max))

        # TODO: This doesn't work if connected directly to worker.stop, not sure why
        worker._reject = lambda: worker.stop()
        self.widgetProgress.rejected.connect(worker._reject)
        worker.started.connect(lambda: self.show_progressbar(worker))
        worker.finished.connect(cleanup)
        worker.canceled.connect(self.clear)
        worker.canceled.connect(cleanup)
        worker.error.connect(self.clear)
        worker.error.connect(cleanup)
        worker.updated.connect(update_progress)
        worker.maximumChanged.connect(self.update_maximum)

        if use_thread:
            # noinspection PyUnboundLocalVariable
            thread.started.connect(worker.start)
            thread.start()
        else:
            worker.start()

    def disconnect_events(self, worker):
        try:
            # noinspection PyProtectedMember
            self.widgetProgress.rejected.disconnect(worker._reject)
        except TypeError:
            pass

    def start(self):
        if self._isrunning:
            if not self:
                self._isrunning = False
            return

        self.run()

    def run(self, last_worker=None):
        self._isrunning = bool(self)

        try:
            item = self.popleft()
        except IndexError:
            self._isrunning = False
            return

        if callable(item):
            worker = item(last_worker)
        else:
            worker = item

        if isiterable(worker):
            for w in reversed(worker):
                self.appendleft(w)
            return self.run(last_worker)
        else:
            if worker is None:
                return self.run(last_worker)

            worker.finished.connect(lambda: self.run(worker))
            self.connect_events(worker)

    def remove(self, worker):
        if worker.thread() != self.parent().thread():
            worker.thread().quit()

        # self.disconnect_events(worker)
        if worker in self:
            super().remove(worker)
        self.hide_progressbar()
