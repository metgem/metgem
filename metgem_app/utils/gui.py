from qtpy.QtCore import QObject, Signal, QTimer
from qtpy import QtWidgets
from qtpy import QtCore
import shiboken2


def wrap_instance(obj, base=None):
    """Cast instance to the most suitable class
    Based on https://github.com/mottosso/Qt.py
    Arguments:
        obj (QObject): object to wrap.
        base (QObject, optional): Base class to wrap with. Defaults to QObject,
            which should handle anything.
    """

    assert isinstance(obj, QObject), "Argument 'obj' must be of type <QObject>"
    assert (base is None) or issubclass(base, QObject), (
        "Argument 'base' must be of type <QObject>")

    ptr = int(shiboken2.getCppPointer(obj)[0])

    if base is None:
        q_object = shiboken2.wrapInstance(ptr, QObject)
        meta_object = q_object.metaObject()

        while True:
            class_name = meta_object.className()

            try:
                base = getattr(QtWidgets, class_name)
            except AttributeError:
                try:
                    base = getattr(QtCore, class_name)
                except AttributeError:
                    meta_object = meta_object.superClass()
                    continue

            break

    return shiboken2.wrapInstance(ptr, base)


class SignalBlocker:
    """Context Manager to temporarily block signals from given Qt's widgets"""

    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for widget in self.widgets:
            widget.blockSignals(True)

    def __exit__(self, *args):
        for widget in self.widgets:
            widget.blockSignals(False)


class SignalGrouper(QObject):
    """Accumulate signals and emit a signal with all the senders after a timeout"""

    groupped = Signal(set)

    def __init__(self, timeout=100):
        super().__init__()
        self.senders = set()
        self.timer = None
        self.timeout = timeout

    # noinspection PyUnusedLocal
    def accumulate(self, *args):
        if not self.senders:
            def emit_signal():
                self.groupped.emit(self.senders)
                self.timer = None
                self.senders = set()

            self.timer = QTimer()
            self.timer.singleShot(self.timeout, emit_signal)

        self.senders.add(self.sender())
        

def enumerateMenu(menu: 'QMenu'):
    for action in menu.actions():
        if action.menu() is not None:
            yield from enumerateMenu(action.menu())
        elif not action.isSeparator():
            yield action
