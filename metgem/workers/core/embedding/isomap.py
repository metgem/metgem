from metgem.workers.core.embedding.base import EmbeddingWorker
from metgem.workers.options import IsomapVisualizationOptions


class IsomapWorker(EmbeddingWorker):

    def __init__(self, scores, options: IsomapVisualizationOptions):
        super().__init__(scores, options)

    # noinspection PyAttributeOutsideInit
    def init(self):
        self._estimator = Isomap(max_iter=self.options.max_iter,
                                 n_neighbors=self.options.n_neighbors,
                                 metric='precomputed')
        self.max = 0
        self.iterative_update = False
        self.desc = 'MDS: Iteration {value:d} of {max:d}'

    def get_n_neighbors(self, n: int):
        return self.options.n_neighbors

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global Isomap
        # noinspection PyUnresolvedReferences
        from sklearn.manifold import Isomap
