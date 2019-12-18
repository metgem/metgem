import io

from sklearn.manifold import Isomap

from .base import EmbeddingWorker
from ...utils import AttrDict
from ...errors import UserRequestedStopError


class IsomapVisualizationOptions(AttrDict):
    """Class containing Isomap visualization options.
    """

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         n_neighbors=5,
                         max_iter=300)


class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self._last_value = 0
        self._shift = 0

    def write(self, s):
        if self.parent.isStopped():
            raise UserRequestedStopError()
        # elif 'it: ' in s:
        #     s = s.split('it: ')[1]
        #     if ', stress ' in s:
        #         s = s.split(', stress ')[0]
        #     try:
        #         value = int(s)
        #         if value < self._last_value:
        #             self._shift += self._last_value
        #         self._last_value = value
        #         self.parent.updated.emit(int((self._shift + value) / self._n_init))
            # except ValueError:
            #     pass


class IsomapWorker(EmbeddingWorker):

    # noinspection PyAttributeOutsideInit
    def init(self):
        self._estimator = Isomap(max_iter=self.options.max_iter,
                                 n_neighbors=self.options.n_neighbors,
                                 metric='precomputed')

        self.max = self.options.max_iter
        self.iterative_update = False
        self.desc = 'MDS: Iteration {value:d} of {max:d}'
        self._io_wrapper = ProgressStringIO(self)
