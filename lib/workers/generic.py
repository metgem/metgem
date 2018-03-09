from .base import BaseWorker


class GenericWorker(BaseWorker):

    def __init__(self, callback, *args, **kwargs):
        super().__init__(track_progress=False)
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def run(self):
        print(self.callback)
        self.callback(*self.args, **self.kwargs)
        self.finished.emit()
