import os
import pandas as pd

from .base import BaseWorker
from ..utils import AttrDict


class ReadMetadataOptions(AttrDict):

    def __init__(self):
        super().__init__(sep=None,
                         skiprows=None,
                         nrows=None,
                         dtype=None,
                         header='infer',
                         usecols=None,
                         comment=None)

    
class ReadMetadataWorker(BaseWorker):
    
    def __init__(self, filename, options, track_progress=True):
        super().__init__()
        self.filename = filename
        self.options = options
        self.options.skiprows = self.options.skiprows if self.options.skiprows is not 0 else None
        self.options.nrows = self.options.nrows if self.options.nrows is not 0 else None

        self.track_progress = track_progress
        self.iterative_update = True
        self.max = 0
        self.desc = 'Reading Metadata...'

    def run(self):  # TODO: Allow updates (read metadata file in a loop)
        try:
            ext = os.path.splitext(self.filename)[1]
            kwargs = dict(**self.options, prefix='Column ', engine='c', float_precision='round_trip')
            data = None
            if ext in (".xls", ".xlsx"):
                kwargs['header'] = kwargs['header'] if type(kwargs['header']) is not str else 0
                data = pd.read_excel(self.filename, **kwargs)
            elif ext in (".csv", ".txt", ".tsv"):
                data = pd.read_csv(self.filename, **kwargs)
            if data is not None and data.size > 0:
                return data
        except(FileNotFoundError, IOError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as e:
            self.error.emit(e)
            return

