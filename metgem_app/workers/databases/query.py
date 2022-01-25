import operator

from libmetgem.database import query

from ..base import BaseWorker
from ..options import QueryDatabasesOptions
from ...config import SQL_PATH, get_debug_flag
from ...database import SpectraLibrary, Bank
from ..struct import StandardsResult


class QueryDatabasesWorker(BaseWorker):

    def __init__(self, indices, mzs, spectra,
                 options: QueryDatabasesOptions):
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

        use_filtering = self.options.use_filtering
        use_min_intensity_filter = self.options.use_min_intensity_filter if use_filtering else False
        use_parent_filter = self.options.use_parent_filter if use_filtering else False
        use_window_rank_filter = self.options.use_window_rank_filter if use_filtering else False
        min_intensity = self.options.min_intensity if use_min_intensity_filter else 0
        parent_filter_tolerance = self.options.parent_filter_tolerance if use_parent_filter else 0
        matched_peaks_window = self.options.matched_peaks_window if use_window_rank_filter else 0
        min_matched_peaks_search = self.options.min_matched_peaks_search if use_window_rank_filter else 0

        # Query database
        analog_mz_tolerance = self.options.analog_mz_tolerance if self.options.analog_search else 0
        qr = query(SQL_PATH, self._indices, self._mzs, self._spectra, self.options.databases,
                   self.options.mz_tolerance, self.options.min_matched_peaks, min_intensity,
                   parent_filter_tolerance, matched_peaks_window,
                   min_matched_peaks_search, self.options.min_cosine, analog_mz_tolerance,
                   bool(self.options.positive_polarity), callback=callback)

        if qr is None:  # User canceled the process
            self.canceled.emit()
            return

        # Get list of data banks
        with SpectraLibrary(SQL_PATH, echo=get_debug_flag()) as lib:
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
