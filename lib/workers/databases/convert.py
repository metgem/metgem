from sqlalchemy.exc import OperationalError

from ..base import BaseWorker
from ...database import DataBaseBuilder

import os


class ConvertDatabasesWorker(BaseWorker):

    def __init__(self, ids: list, output_path: str, input_path: str=None):
        super().__init__()
        self.ids = ids
        self.input_path = input_path if input_path is not None else output_path
        self.output_path = output_path
        self.iterative_update = False
        self.max = len(self.ids)
        self.desc = 'Converting databases...'

    def run(self):
        converted = {}
        for k in self.ids.keys():
            converted[k] = set()

        with DataBaseBuilder(os.path.join(self.input_path, 'spectra')) as db:
            for origin in self.ids:
                for i, (name, ids) in enumerate(self.ids[origin].items()):
                    filenames = []
                    for id_ in ids:
                        path = os.path.join(self.input_path, id_)
                        if os.path.exists(path):
                            filenames.append(path)

                    try:
                        db.add_bank(filenames, bank_name=origin + ' - ' + name)
                    except OperationalError as e:
                        self.error.emit(e)
                        return False

                    self.updated.emit(i)
                    converted[origin].add(name)

        return converted
