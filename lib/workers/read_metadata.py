import pandas as pd

from .base import BaseWorker

    
class ReadMetadataWorker(BaseWorker):
    
    def __init__(self, filename, csv_separator=None):
        super().__init__()
        self.filename = filename
        self.csv_separator = csv_separator
        self.iterative_update = True
        self.max = 0
        self.desc = 'Reading Metadata...'

    def run(self):
        try:
            if self.filename.endswith(".xls") or self.filename.endswith(".xlsx"):
                data = pd.read_excel(self.filename)
            else:
                if self.csv_separator == r"\s+":
                    data = pd.read_csv(self.filename, delim_whitespace=True)
                else:
                    data = pd.read_csv(self.filename, sep=self.csv_separator)
            self._result = data.to_records()
            self.finished.emit()
        except(FileNotFoundError, IOError) as e:
            self.error.emit(e)
            self._result = None
        else:
            self.finished.emit()

