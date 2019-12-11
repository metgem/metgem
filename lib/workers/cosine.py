from .base import BaseWorker
from ..utils import AttrDict

from libmetgem.cosine import compute_distance_matrix


class CosineComputationOptions(AttrDict):
    """Class containing spectra cosine scores options.

    Attributes:
        mz_tolerance (float): in Da.
        min_intensity (int): relative minimum intensity in percentage.
        parent_filter_tolerance (int): in Da.
        min_matched_peaks (int): Minimum number of common peaks between two spectra.
        min_matched_peaks_search (int): Window rank filter's parameters: for each peak in the spectrum, 
            it is kept only if it is in top `min_matched_peaks_search` in the +/-`matched_peaks_window` window.
        matched_peaks_window (int): in Da.

    """

    def __init__(self, **kwargs):
        super().__init__(mz_tolerance=0.02,
                         min_intensity=0,
                         parent_filter_tolerance=17,
                         min_matched_peaks=4,
                         min_matched_peaks_search=6,
                         matched_peaks_window=50,
                         is_ms1_data=False,
                         use_filtering=True,
                         use_min_intensity_filter=False,
                         use_parent_filter=True,
                         use_window_rank_filter=True,
                         **kwargs)


class ComputeScoresWorker(BaseWorker):
    """Generate a network from a MGF file.
    """

    def __init__(self, mzs, spectra, options):
        super().__init__()
        self._mzs = mzs
        self._spectra = spectra
        self.options = options
        self._num_spectra = len(self._spectra)
        self.max = self._num_spectra * (self._num_spectra - 1) // 2
        self.iterative_update = True
        self.desc = 'Computing scores...'

    def run(self):
        def callback(value):
            self.updated.emit(value)
            return not self.isStopped()

        if self.isStopped():
            self.canceled.emit()
            return False

        try:
            scores_matrix = compute_distance_matrix(self._mzs, self._spectra,
                                                    self.options.mz_tolerance, self.options.min_matched_peaks,
                                                    callback=callback)
        except MemoryError as e:
            self.error.emit(e)
            return

        if not self.isStopped():
            return scores_matrix
        else:
            self.canceled.emit()
