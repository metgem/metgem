import io

from metgem.workers.core.embedding.base import EmbeddingWorker, UserRequestedStopError
from metgem.workers.options import PHATEVisualizationOptions


class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def write(self, s):
        """Method used to follow progress of processing."""

        if self.parent.isStopped():
            raise UserRequestedStopError()
        elif 'Calculat' in s:
            self.parent.updated.emit(1)


class PHATEWorker(EmbeddingWorker):

    def __init__(self, scores, options: PHATEVisualizationOptions):
        super().__init__(scores, options)

    # noinspection PyAttributeOutsideInit
    def init(self):
        self.use_distance_matrix = False
        random_state = None if self.options.random else 0
        self._estimator = PHATE(knn=self.options.knn,
                                decay=self.options.decay,
                                gamma=self.options.gamma, verbose=2,
                                random_state=random_state, knn_dist='precomputed_affinity')

        self.max = 9
        self.iterative_update = True
        self.desc = 'PHATE: Step {value:d} of {max:d}'
        self._io_wrapper = ProgressStringIO(self)

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global PHATE
        # noinspection PyUnresolvedReferences
        from phate import PHATE
