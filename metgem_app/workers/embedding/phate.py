import io

from .base import EmbeddingWorker
from ...utils import AttrDict
from ...errors import UserRequestedStopError


class PHATEVisualizationOptions(AttrDict):
    """Class containing PHATE visualization options.
    """

    def __init__(self):
        super().__init__(knn=5,
                         decay=15,
                         gamma=1,
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         random=False)


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

    @staticmethod
    def import_modules():
        global PHATE
        # noinspection PyUnresolvedReferences
        from phate import PHATE
