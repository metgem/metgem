from typing import Dict, List
import os

from metgem_app.workers.base import BaseWorker
from metgem_app.database import SpectraLibrary, Spectrum
from metgem_app.models.metadata import DbResultsRole
from metgem_app.workers.gui.errors import NoDataError

from PySide6.QtCore import Qt


def yield_results(results: list, num_hits: int):
    """Yield `num_hits` first results. If `results` is smaller than `num_hits`continue yielding None
    until `num_hits` values has been yielded."""
    i = 0
    for i, r in enumerate(results[:num_hits]):
        yield r
    for _ in range(i + 1, num_hits):
        yield None


def clean_string(s: str):
    return ''.join(s.encode('ascii', 'ignore').decode().strip().splitlines())


class ExportDbResultsWorker(BaseWorker):
    KEYS_NEEDING_DB = {'Name', 'SMILES', 'Inchi', 'm/z parent'}

    def __init__(self, filename: str, separator: str, num_hits: int,
                 attributes: Dict[str, List[str]], base_path: str, model,
                 selected_rows: List[int]):
        super().__init__()
        self.filename = filename
        self.sep = separator
        self.num_hits = num_hits
        self.attrs = attributes
        self.base_path = base_path
        self.model = model
        self.selected_rows = selected_rows

        self.max = self.model.rowCount()
        self.iterative_update = True
        self.desc = 'Exporting Database results...'

    def run(self):
        nrows = self.model.rowCount()

        if nrows <= 0:
            self.error.emit(NoDataError())
            return

        rows = self.selected_rows if self.selected_rows else range(nrows)

        lib = None
        try:
            if self.KEYS_NEEDING_DB - set(self.attrs['standards']) or \
               self.KEYS_NEEDING_DB - set(self.attrs['standards']):
                lib = SpectraLibrary(os.path.join(self.base_path, 'spectra'))

            with open(self.filename, 'w', encoding='utf-8') as f:
                headers = ["id", "m/z"]
                headers += [f'Standard{i+1}_{attr.lower()}' for i in range(self.num_hits)
                            for attr in self.attrs.get('standards', [])]
                headers += [f'Analog{i+1}_{attr.lower()}' for i in range(self.num_hits)
                            for attr in self.attrs.get('analogs', [])]
                f.write(self.sep.join(headers) + '\n')

                # Export data
                for i in rows:
                    mz = self.model.index(i, 0).data()
                    data = [self.model.headerData(i, Qt.Vertical), str(mz)]
                    results_dict = {'standards': [], 'analogs': []}
                    results = self.model.index(i, 1).data(DbResultsRole)
                    if results is not None:
                        for type_, res in results.items():
                            if type_ not in ('standards', 'analogs'):
                                continue

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
                                        results_dict[type_].append(clean_string(r.bank) if r is not None
                                                                   and r.bank is not None else '')
                                    elif k == 'm/z parent':
                                        results_dict[type_].append(str(round(spec.pepmass, 4)) if spec is not None
                                                                   and spec.pepmass is not None else '')
                                    elif k == 'Name':
                                        results_dict[type_].append(clean_string(spec.name) if spec is not None
                                                                   and spec.name is not None else '')
                                    elif k == 'SMILES':
                                        results_dict[type_].append(clean_string(spec.smiles) if spec is not None
                                                                   and spec.smiles is not None else '')
                                    elif k == 'Inchi':
                                        results_dict[type_].append(clean_string(spec.inchi) if spec is not None
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
