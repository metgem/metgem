from .base import EmbeddingWorker
from ...utils import AttrDict


class IsomapVisualizationOptions(AttrDict):
    """Class containing Isomap visualization options.
    """

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         n_neighbors=5,
                         max_iter=300)


class IsomapWorker(EmbeddingWorker):

    # noinspection PyAttributeOutsideInit
    def init(self):
        self._estimator = Isomap(max_iter=self.options.max_iter,
                                 n_neighbors=self.options.n_neighbors,
                                 metric='precomputed')
        self.max = 0
        self.iterative_update = False
        self.desc = 'MDS: Iteration {value:d} of {max:d}'

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global Isomap
        # noinspection PyUnresolvedReferences
        from sklearn.manifold import Isomap
