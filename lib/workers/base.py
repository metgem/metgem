from PyQt5.QtCore import QObject, pyqtSignal


class BaseWorker(QObject):

    finished = pyqtSignal()
    canceled = pyqtSignal()
    updated = pyqtSignal(int)
    error = pyqtSignal(Exception)
    maximumChanged = pyqtSignal(int)

    def __init__(self, track_progress=True):
        super().__init__()

        self._should_stop = False
        self._result = None
        self.track_progress = track_progress
        self._max = 100

        # If True, `updated` event sends progress since last update, otherwise since beginning of the process:
        self.iterative_update = True

        self.desc = ''

    def run(self):
        pass

    def stop(self):
        self._should_stop = True

    def result(self):
        return self._result

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, value):
        self._max = value
        self.maximumChanged.emit(value)
