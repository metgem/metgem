from typing import Dict, List
import os

from .base import BaseWorker
from ..database import SpectraLibrary, Spectrum
from ..models.metadata import DbResultsRole


class NoDataError(Exception):
    pass


def yield_results(results: list, num_hits: int):
    """Yield `num_hits` first results. If `results` is smaller than `num_hits`continue yielding None
    until `num_hits` values has beend yielded."""
    for i, r in enumerate(results[:num_hits]):
        yield r
    for _ in range(i + 1, num_hits):
        yield None


class ExportDbResultsWorker(BaseWorker):
    KEYS_NEEDING_DB = {'Name', 'SMILES', 'Inchi', 'm/z parent'}

    def __init__(self, filename: str, separator: str, num_hits: int,
                 attributes: Dict[str, List[str]], base_path: str, model):
        super().__init__()
        self.filename = filename
        self.sep = separator
        self.num_hits = num_hits
        self.attrs = attributes
        self.model = model
        self.base_path = base_path

        self.max = self.model.rowCount()
        self.iterative_update = True
        self.desc = 'Exporting Database results...'

    def run(self):
        nrows = self.model.rowCount()

        if nrows <= 0:
            self.error.emit(NoDataError())
            return

        try:
            if self.KEYS_NEEDING_DB  - set(self.attrs['standards']) or \
               self.KEYS_NEEDING_DB - set(self.attrs['standards']):
                lib = SpectraLibrary(os.path.join(self.base_path, 'spectra'))
            else:
                lib = None

            with open(self.filename, 'w', encoding='utf-8') as f:
                headers = ["id", "m/z"]
                headers += [f'Standard{i+1}_{attr.lower()}' for i in range(self.num_hits)
                            for attr in self.attrs.get('standards', [])]
                headers += [f'Analog{i+1}_{attr.lower()}' for i in range(self.num_hits)
                            for attr in self.attrs.get('analogs', [])]
                f.write(self.sep.join(headers) + '\n')

                # Export data
                for i in range(nrows):
                    mz = round(self.model.index(i, 0).data(), 4)
                    data = [str(i+1), str(mz)]
                    results_dict = {'standards': [], 'analogs': []}
                    results = self.model.index(i, 1).data(DbResultsRole)
                    if results is not None:
                        for type_, res in results.items():
                            res = results.get(type_, None)
                            for r in yield_results(res, self.num_hits):
                                if lib is not None and r is not None:
                                    query = lib.query(Spectrum).filter(Spectrum.id == r.id)
                                    spec = query.first()
                                else:
                                    spec = None

                                for k in self.attrs[type_]:
                                    if k == 'Score':
                                        results_dict[type_].append(str(round(r.score, 4)) if r is not None else '')
                                    elif k == 'Database':
                                        results_dict[type_].append(r.bank if r is not None
                                                                   and r.bank is not None else '')
                                    elif k == 'm/z parent':
                                        results_dict[type_].append(str(round(spec.pepmass, 4)) if spec is not None
                                                                   and spec.pepmass is not None else '')
                                    elif k == 'Name':
                                        results_dict[type_].append(spec.name if spec is not None
                                                                   and spec.name is not None else '')
                                    elif k == 'SMILES':
                                        results_dict[type_].append(spec.smiles if spec is not None
                                                                   and spec.smiles is not None else '')
                                    elif k == 'Inchi':
                                        results_dict[type_].append(spec.inchi if spec is not None
                                                                   and spec.inchi is not None else '')

                        for type_ in ('standards', 'analogs'):
                            data += results_dict[type_] if results_dict[type_] else\
                                ['' for _ in range(self.num_hits) for _ in self.attrs[type_]]
                    f.write(self.sep.join(data) + '\n')

                    self.updated.emit(1)
            return True
        except(FileNotFoundError, IOError, ValueError) as e:
            self.error.emit(e)
            return
        finally:
            if lib is not None:
                lib.close()
