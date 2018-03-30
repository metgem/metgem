import pandas as pd


from .base import BaseWorker

    
class ReadMetadataWorker(BaseWorker):
    
    def __init__(self, filename, csv_separator = None):
        super().__init__()
        self.filename = filename
        self.csv_separator = csv_separator


    def run(self):
        if metadata_file.endswith(".csv"):
            data = pd.read_csv(metadata_file, sep=self.csv_separator)
        else:
            data = pd.read_excel(metadata_file)

        self._result = data
        self.finished.emit()
