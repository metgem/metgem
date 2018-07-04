import operator
import numpy as np

from .base import BaseWorker
from ..utils import AttrDict
from ..errors import UserRequestedStopError

try:
    from libmetgem.cosine import cosine_score, compute_distance_matrix
except ImportError:
    def cosine_score(spectrum1_mz, spectrum1_data, spectrum2_mz, spectrum2_data, mz_tolerance, min_matched_peaks):
        """Compute cosine score from two spectra.

        Returns:
            float: Cosine similarity between spectrum1 and spectrum2."""

        dm = spectrum1_mz - spectrum2_mz

        diff_matrix = spectrum2_data[:, 0] - spectrum1_data[:, 0][:, None]
        if dm != 0.:
            idxMatched1, idxMatched2 = np.where( \
                np.logical_or(np.abs(diff_matrix) <= mz_tolerance,
                              np.abs(diff_matrix + dm) <= mz_tolerance))
        else:
            idxMatched1, idxMatched2 = np.where(np.abs(diff_matrix) <= mz_tolerance)
        del diff_matrix

        if idxMatched1.size + idxMatched2.size == 0:
            return 0.

        peakUsed1 = [False] * spectrum1_data.size
        peakUsed2 = [False] * spectrum2_data.size

        peakMatches = []
        for i in range(idxMatched1.size):
            peakMatches.append((idxMatched1[i], idxMatched2[i],
                                spectrum1_data[idxMatched1[i], 1] * spectrum2_data[
                                    idxMatched2[i], 1]))

        peakMatches = sorted(peakMatches, key=operator.itemgetter(2), reverse=True)

        score = 0.
        numMatchedPeaks = 0
        for i in range(len(peakMatches)):
            if not peakUsed1[peakMatches[i][0]] and not peakUsed2[peakMatches[i][1]]:
                score += peakMatches[i][2]
                peakUsed1[peakMatches[i][0]] = True
                peakUsed2[peakMatches[i][1]] = True
                numMatchedPeaks += 1

        if numMatchedPeaks < min_matched_peaks:
            return 0.

        return score

    def compute_distance_matrix(mzs, spectra, mz_tolerance, min_matched_peaks, callback=None):
        size = len(mzs)
        has_callback = callback is not None
        matrix = np.empty((len(spectra), len(spectra)), dtype=np.float32)
        for i in range(len(spectra)):
            for j in range(i):
                matrix[i, j] = matrix[j, i] = cosine_score(mzs[i], spectra[i], mzs[j], spectra[j],
                                                           mz_tolerance, min_matched_peaks)
                if has_callback:
                    callback(size-1)
        np.fill_diagonal(matrix, 1)
        if has_callback:
            callback(size)
        matrix[matrix > 1] = 1
        return matrix

MZ = 0
INTENSITY = 1


def human_readable_data(data):
    data = data.copy()
    data[:, INTENSITY] = data[:, INTENSITY] ** 2
    data[:, INTENSITY] = data[:, INTENSITY] / data[:, INTENSITY].max() * 100
    return data


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
            if self.isStopped():
                raise UserRequestedStopError()

        try:
            scores_matrix = compute_distance_matrix(self._mzs, self._spectra,
                                                    self.options.mz_tolerance, self.options.min_matched_peaks,
                                                    callback=callback)
        except UserRequestedStopError:
            self.canceled.emit()
            return

        return scores_matrix
