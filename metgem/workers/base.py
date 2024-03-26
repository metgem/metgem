from metgem.utils.qt import QObject, Signal


class UserRequestedStopError(Exception):
    """Raised if user request to stop a worker's process"""


class BaseWorker(QObject):
    started = Signal()
    finished = Signal()
    canceled = Signal()
    updated = Signal(object)
    error = Signal(Exception)
    maximumChanged = Signal(object)
    handle_sparse = False  # Whether the worker can handle sparse distance/similarity matrix

    _enabled = True

    def __init__(self, track_progress=True):
        super().__init__()

        self.import_modules()

        self._should_stop = False
        self._result = None
        self.track_progress = track_progress
        self._max = 100

        # If True, `updated` event sends progress since last update, otherwise since beginning of the process:
        self.iterative_update = True

        self.desc = ''

    @classmethod
    def enable(cls):
        cls._enabled = True

    @classmethod
    def disable(cls):
        cls._enabled = False

    @classmethod
    def enabled(cls):
        return cls._enabled

    @staticmethod
    def import_modules():
        """Import module needed for this worker to run"""
        pass

    @classmethod
    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            yield subclass
            yield from subclass.get_subclasses()

    def start(self):
        self.started.emit()
        result = self.run()
        if result is not None:
            self._result = result
            self.finished.emit()

    def isStopped(self):
        return self._should_stop

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
