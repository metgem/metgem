from ..base import BaseWorker
from ..libmetgem_wrapper import query
from ..cosine import CosineComputationOptions
from ...database import SpectraLibrary, Bank
from ...config import SQL_PATH, DEBUG

import operator
from collections import namedtuple

StandardsResult = namedtuple('StandardsResult', ['score', 'bank', 'id', 'text'])


class QueryDatabasesOptions(CosineComputationOptions):
    """Class containing spectra cosine scores options.

    Attributes:
        See `CosineComputationOptions`.
        min_cosine (float): Minimum cosine score for database query.
        analog_search (bool): Look for analogs (different m/z parent) instead or standards (same m/z parent).
        analog_mz_tolerance (float): m/z tolerance used for analog search, in Da.
        positive_polarity (bool): True for positive polarity, False for negative polarity.
        databases (list of int): Indexes of databases to query in. If empty, search in all available databases.
    """

    def __init__(self):
        super().__init__(min_cosine=0.65,
                         analog_search=False,
                         analog_mz_tolerance=100.,
                         positive_polarity=True,
                         databases=[])


class QueryDatabasesWorker(BaseWorker):

    def __init__(self, indices, mzs, spectra, options):
        super().__init__()
        self._indices = list(indices)
        self._mzs = mzs
        self._spectra = spectra
        self.options = options
        self.max = 0
        self.iterative_update = False
        self._type = "analogs" if options.analog_search else "standards"
        self.desc = f'Querying library for {self._type}...'

    def run(self):
        def callback(value):
            if value > 0 and self.max == 0:
                 self.max = 100
            self.updated.emit(value)
            return not self.isStopped()

        results = {}

        # Query database
        analog_mz_tolerance = self.options.analog_mz_tolerance if self.options.analog_search else 0
        qr = query(SQL_PATH, self._indices, self._mzs, self._spectra, self.options.databases,
                   self.options.mz_tolerance, self.options.min_matched_peaks, self.options.min_intensity,
                   self.options.parent_filter_tolerance, self.options.matched_peaks_window,
                   self.options.min_matched_peaks_search, self.options.min_cosine, analog_mz_tolerance,
                   bool(self.options.positive_polarity), callback=callback)

        if qr is None:  # User canceled the process
            return results

        # Get list of data banks
        with SpectraLibrary(SQL_PATH, echo=DEBUG) as lib:
            bank_names = dict(lib.query(Bank.id, Bank.name).all())

        # Re-organize results
        for idx, v in qr.items():
            results[idx] = {self._type: []}
            for r in sorted(v, key=operator.itemgetter('score'), reverse=True):
                score = r['score']
                id_ = r['id']
                bank = bank_names[r['bank_id']]
                try:
                    name = r['name'].decode()
                except AttributeError:
                    name = r['name']
                std_result = StandardsResult(score=score, id=id_, bank=bank, text=f"[{score:.2f}] {bank}: {name}")
                results[idx][self._type].append(std_result)

        return results
