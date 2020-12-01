from PyQt5.QtCore import Qt

from .base import BaseWorker


class NoDataError(Exception):
    pass


class ExportMetadataWorker(BaseWorker):

    def __init__(self, filename, model, sep=None, selected_rows=None):
        super().__init__()
        self.filename = filename
        self.model = model
        self.sep = sep if sep is not None else ','
        self.selected_rows = selected_rows

        self.max = self.model.rowCount()
        self.iterative_update = True
        self.desc = 'Exporting Metadata...'

    def run(self):
        ncolumns = self.model.columnCount()
        nrows = self.model.rowCount()

        if ncolumns <= 0 or nrows <= 0:
            self.error.emit(NoDataError())
            return

        rows = self.selected_rows if self.selected_rows else range(nrows)

        try:
            with open(self.filename, 'w') as f:
                # Export headers
                data = ""
                data += f"id{self.sep}"
                for j in range(ncolumns):
                    data += f"{self.model.headerData(j, Qt.Horizontal)}{self.sep}"
                f.write(f"{data[:-1]}\n")

                # Export data
                for i in rows:
                    data = f"{self.model.headerData(i, Qt.Vertical)}{self.sep}"
                    for j in range(ncolumns):
                        index = self.model.index(i, j)
                        d = str(self.model.data(index))
                        if self.sep in d:
                            d = '"' + d.replace('"', "'") + '"'
                        data += f"{d}{self.sep}"
                    f.write(f"{data[:-1]}\n")
                    self.updated.emit(1)
            return True
        except(FileNotFoundError, IOError, ValueError) as e:
            self.error.emit(e)
            return
