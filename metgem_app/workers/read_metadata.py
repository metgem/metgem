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
                         index_col=None,
                         comment=None)

    
class ReadMetadataWorker(BaseWorker):
    
    def __init__(self, filename, options, track_progress=True):
        super().__init__()
        self.filename = filename
        self.options = options
        self.options.skiprows = self.options.skiprows if self.options.skiprows != 0 else None
        self.options.nrows = self.options.nrows if self.options.nrows != 0 else None

        self.track_progress = track_progress
        self.max = 0
        self.iterative_update = True
        self.desc = 'Reading Metadata...'

    def run(self):  # TODO: Allow updates (read metadata file in a loop)
        try:
            # Make sure that the column used as index will be imported
            if self.options.index_col is not None and self.options.usecols is not None:
                if self.options.index_col not in self.options.usecols:
                    self.options.usecols.append(self.options.index_col)

                # The index column is used after filtering columns so we need to find the index of this column
                # inside the list of used columns
                self.options.usecols = sorted(self.options.usecols)
                self.options.index_col = self.options.usecols.index(self.options.index_col)

            data = None
            type_ = None
            ext = os.path.splitext(self.filename)[1]
            if ext in (".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"):
                type_ = "spreadsheet"
                kwargs = dict(**self.options,
                              engine="odf" if ext == ".ods" else None,
                              )
                kwargs['header'] = kwargs['header'] if type(kwargs['header']) is not str else 0
                with open(self.filename, 'rb') as f:
                    data = pd.read_excel(f, **kwargs)  # Workaround for Pandas's bug #15086
            elif ext in (".csv", ".txt", ".tsv"):
                type_ = "text"
                prefix = None if self.options.header is None or self.options.header == 'infer' else 'Column '
                kwargs = dict(**self.options, prefix=prefix, engine='c', float_precision='high')
                with open(self.filename, encoding='utf-8', errors='ignore') as f:
                    data = pd.read_csv(f, **kwargs)   # Workaround for Pandas's bug #15086

            if data is not None:
                if type_ == "spreadsheet":
                    # Drop rows and columns full of na values
                    data = data.dropna(how='all')

                    # Make sure that columns full of integer are loaded as integer and not float
                    col_should_be_int = data.select_dtypes(include=['float']).applymap(float.is_integer).all()
                    float_to_int_cols = col_should_be_int[col_should_be_int].index
                    data.loc[:, float_to_int_cols] = data.loc[:, float_to_int_cols].astype(int)
                else:
                    # Drop columns full of na values, csb reader already removed empty rows
                    data = data.dropna(how='all', axis=1)

                # Make sure that index is 0-based
                if self.options.index_col is not None:
                    data.index -= 1
                else:
                    data = data.reset_index(drop=True)

            if data is not None and data.size > 0:
                return data
        except(FileNotFoundError, IOError, pd.errors.ParserError,
               pd.errors.EmptyDataError, ValueError, ImportError) as e:
            self.error.emit(e)
            return

