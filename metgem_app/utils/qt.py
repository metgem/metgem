try:
    from PyQt5.QtCore import QObject, pyqtSignal
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor
except (ImportError, RuntimeError):
    class QObject(object):
        pass

    class pyqtSignal(object):
        def __init__(self, *args):
            super().__init__()

        def emit(self, *args, **kwargs):
            pass

    class Qt(object):
        Horizontal = 1

    class QColor(object):
        def __call__(self, *args, **kwargs):
            return self
