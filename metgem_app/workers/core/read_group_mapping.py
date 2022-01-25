from ..base import BaseWorker

    
class ReadGroupMappingWorker(BaseWorker):

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

        self.max = 0
        self.iterative_update = True
        self.desc = 'Reading Group mapping...'

    def run(self):
        try:
            with open(self.filename) as f:
                mapping = {}
                for line in f:
                    line = line.strip('\n')
                    if '=' in line:
                        key, value = line.split('=')
                        if key.startswith('GROUP_'):
                            key = key[6:]
                            cols = [v.strip() for v in value.split(';') if v.strip() != '']
                            if len(cols):
                                mapping[key] = cols
                self.updated.emit(1)
            return mapping
        except(FileNotFoundError, IOError, ValueError) as e:
            self.error.emit(e)
            return

