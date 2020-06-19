import json

import yaml

from .base import BaseWorker
from ..models.metadata import DbResultsRole


class NoDataError(Exception):
    pass


class CustomDumper(yaml.Dumper):
    # https://stackoverflow.com/questions/16782112/can-pyyaml-dump-dict-items-in-non-alphabetical-order
    def represent_dict_preserve_order(self, data):
        return self.represent_dict(data.items())

    def represent_float(self, data):
        text = '{0:.4f}'.format(data)
        return self.represent_scalar(u'tag:yaml.org,2002:float', text)


CustomDumper.add_representer(dict, CustomDumper.represent_dict_preserve_order)
CustomDumper.add_representer(float, CustomDumper.represent_float)


class ExportDbResultsWorker(BaseWorker):

    def __init__(self, filename, model, fmt='yaml'):
        super().__init__()
        self.filename = filename
        self.model = model
        self.fmt = 'json' if fmt == 'json' else 'yaml'

        self.max = self.model.rowCount()
        self.iterative_update = True
        self.desc = 'Exporting Database results...'

    def run(self):
        nrows = self.model.rowCount()

        if nrows <= 0:
            self.error.emit(NoDataError())
            return

        try:
            with open(self.filename, 'w') as f:
                # Export data
                for i in range(nrows):
                    data = {}

                    index = self.model.index(i, 0)
                    data['mz'] = round(self.model.data(index), 4)

                    index = self.model.index(i, 1)
                    results = self.model.data(index, DbResultsRole)
                    if results is not None:
                        for type_, res in results.items():
                            data[type_] = []

                            for r in res:
                                try:
                                    desc = r.text.split(r.bank + ': ')[1] if r.text is not None else ''
                                except IndexError:
                                    pass

                                data[type_].append({'score': round(r.score, 4),
                                                    'bank': r.bank,
                                                    'description': desc})

                        if self.fmt == 'json':
                            json.dump({i+1: data}, f, indent=4)
                        else:
                            yaml.dump({i+1: data}, f, default_flow_style=False, Dumper=CustomDumper)
                    self.updated.emit(1)
            return True
        except(FileNotFoundError, IOError, ValueError) as e:
            self.error.emit(e)
            return
