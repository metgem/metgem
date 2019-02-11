from ..base import BaseWorker
from ...database import DataBaseBuilder

import os


class ConvertDatabasesWorker(BaseWorker):

    def __init__(self, ids: list, output_path: str, input_path: str=None, names: list=None):
        super().__init__()
        self.ids = ids
        self.input_path = input_path if input_path is not None else output_path
        self.output_path = output_path
        self.names = names if names is not None else ids
        self.iterative_update = False
        self.max = len(self.ids)
        self.desc = 'Converting databases...'

    def run(self):
        converted_ids = []

        with DataBaseBuilder(os.path.join(self.input_path, 'spectra')) as db:
            for i, (id_, name) in enumerate(zip(self.ids, self.names)):
                ext = os.path.splitext(id_)[1]
                if not ext:
                    id_ = f'{id_}.mgf'
                path = os.path.join(self.input_path, id_)
                if os.path.exists(path):
                    db.add_bank(path, name=name)
                self.updated.emit(i)
                converted_ids.append(id_)

        return converted_ids
