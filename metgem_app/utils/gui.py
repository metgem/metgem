from qtpy.QtCore import QObject, Signal, QTimer


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
