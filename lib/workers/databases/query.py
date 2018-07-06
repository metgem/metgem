from ..base import BaseWorker
from ..cosine import cosine_score, CosineComputationOptions
from ..read_mgf import filter_data
from ...database import SpectraLibrary, Spectrum
from ...config import SQL_PATH, DEBUG

from collections import namedtuple
from sqlalchemy.exc import OperationalError
from sqlalchemy import or_

STANDARDS = 0
ANALOGS = 1
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

    def __init__(self, indexes, mzs, spectra, options):
        super().__init__()
        self._indexes = indexes
        self._mzs = mzs
        self._spectra = spectra
        self.options = options
        self.max = len(mzs) * 100
        self.iterative_update = False
        self.type_ = "analogs" if options.analog_search else "standards"
        self.desc = f'Querying library for {self.type_}...'

    def run(self):
        results = {}
        count = 0

        try:
            with SpectraLibrary(SQL_PATH, echo=DEBUG) as lib:
                for idx, mz_parent, spec_data in zip(self._indexes, self._mzs, self._spectra):
                    if self.isStopped():
                        self.canceled.emit()
                        return False

                    results[idx] = {self.type_: []}
                    tol = self.options.analog_mz_tolerance if self.options.analog_search else self.options.mz_tolerance

                    # Create query
                    query = lib.query(Spectrum)

                    # Filter query by selecting databases, if needed
                    if self.options.databases:
                        query = query.filter(Spectrum.bank_id.in_(self.options.databases))

                    # Filter query by selecting polarity
                    query = query.filter(or_(Spectrum.positive == self.options.positive_polarity,
                                             Spectrum.positive.is_(None)))

                    # Filter query by selecting pepmass window
                    query = query.filter(Spectrum.pepmass >= mz_parent - tol, Spectrum.pepmass <= mz_parent + tol)

                    # If we are looking for analogs, do not include standards
                    if self.options.analog_search:
                        tol = self.options.mz_tolerance
                        query = query.filter(or_(Spectrum.pepmass < mz_parent - tol,
                                                 Spectrum.pepmass > mz_parent + tol))

                    num_results = query.count()
                    if num_results > 0:
                        step = 100. / num_results
                        for i, obj in enumerate(query):
                            if self.isStopped():
                                self.canceled.emit()
                                return False

                            data = filter_data(obj.peaks.copy(), obj.pepmass, self.options.min_intensity,
                                               self.options.parent_filter_tolerance,
                                               self.options.matched_peaks_window,
                                               self.options.min_matched_peaks_search)
                            if data.size > 0:
                                score = cosine_score(mz_parent, spec_data, obj.pepmass, data,
                                                     self.options.mz_tolerance, self.options.min_matched_peaks)
                                if score > self.options.min_cosine:
                                    result = StandardsResult(score=score, id=obj.spectrumid,
                                                             bank=obj.bank.name,
                                                             text=f"[{score:.2f}] {obj.bank.name}: {obj.name}")
                                    results[idx][self.type_].append(result)
                            self.updated.emit(count+step*i)

                    # Sort results by decreasing scores
                    results[idx][self.type_] = sorted(results[idx][self.type_], reverse=True)

                    count += 100
            return results

        except OperationalError as e:
            self.error.emit(e)
            return
