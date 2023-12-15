from libmetgem.cosine import compute_similarity_matrix

from metgem.workers.base import BaseWorker
from metgem.workers.options import CosineComputationOptions


class ComputeScoresWorker(BaseWorker):
    """Generate a network from a MGF file.
    """

    def __init__(self, mzs, spectra, options: CosineComputationOptions):
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
            scores_matrix = compute_similarity_matrix(self._mzs, self._spectra,
                                                      self.options.mz_tolerance, self.options.min_matched_peaks,
                                                      dense_output=self.options.dense_output,
                                                      callback=callback)
        except MemoryError as e:
            self.error.emit(e)
            return

        if not self.isStopped():
            return scores_matrix
        else:
            self.canceled.emit()
