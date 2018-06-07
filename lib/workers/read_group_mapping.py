from .base import BaseWorker

    
class ReadGroupMappingWorker(BaseWorker):
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

        self.iterative_update = True
        self.max = 0
        self.desc = 'Reading Group mapping...'

    def run(self):
        try:
            with open(self.filename) as f:
                mapping = {}
                for line in f:
                    key, value = line.strip('\n').split('=')
                    if key.startswith('GROUP_'):
                        key = key[6:]
                        cols = [v.strip() for v in value.split(';')]
                        if len(cols):
                            mapping[key] = cols
                self.updated.emit(1)
            return mapping
        except(FileNotFoundError, IOError) as e:
            self.error.emit(e)
            return

