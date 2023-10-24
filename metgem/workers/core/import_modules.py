from metgem.workers.base import BaseWorker


class ImportModulesWorker(BaseWorker):
    def __init__(self, worker_class, title):
        super().__init__()
        self._worker_class = worker_class

        self.max = 0
        self.desc = f'Loading modules for {title}...'

    def run(self):
        try:
            self._worker_class.import_modules()
        except ImportError as e:
            self._worker_class.disable()
            self.error.emit(e)
            return
        else:
            return True
