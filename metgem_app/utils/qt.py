try:
    from PyQt5.QtCore import QObject, pyqtSignal
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor
except (ImportError, RuntimeError):
    from typing import Callable

    class QObject(object):
        pass

    class pyqtSignal(object):
        slots = []

        def __init__(self, *args):
            super().__init__()

        def connect(self, callable: Callable):
            self.slots.append(callable)

        def emit(self, *args, **kwargs):
            if isinstance(args, (list, tuple)) and args and isinstance(args[0], Exception):
                raise args[0]

            for callable in self.slots:
                callable(*args, **kwargs)

    class Qt(object):
        Horizontal = 1

    class QColor(object):
        def __call__(self, *args, **kwargs):
            return self
