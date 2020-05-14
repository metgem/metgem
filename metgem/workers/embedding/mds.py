import io

from sklearn.manifold import MDS

from .base import EmbeddingWorker
from ...errors import UserRequestedStopError
from ...utils import AttrDict


class MDSVisualizationOptions(AttrDict):
    """Class containing MDS visualization options.
    """

    def __init__(self):
        super().__init__(min_score=0.70,
                         min_scores_above_threshold=1,
                         max_iter=300,
                         random=False)


class ProgressStringIO(io.StringIO):

    def __init__(self, parent, n_init, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self._n_init = n_init
        self._last_value = 0
        self._shift = 0

    def write(self, s):
        if self.parent.isStopped():
            raise UserRequestedStopError()
        elif 'it: ' in s:
            s = s.split('it: ')[1]
            if ', stress ' in s:
                s = s.split(', stress ')[0]
            try:
                value = int(s)
                if value < self._last_value:
                    self._shift += self._last_value
                self._last_value = value
                self.parent.updated.emit(int((self._shift + value) / self._n_init))

            except ValueError:
                pass


class MDSWorker(EmbeddingWorker):

    # noinspection PyAttributeOutsideInit
    def init(self):
        random_state = None if self.options.random else 0
        n_init = 8
        self._estimator = MDS(max_iter=self.options.max_iter, verbose=2, n_init=n_init,
                              random_state=random_state, dissimilarity='precomputed')

        self.max = self.options.max_iter
        self.iterative_update = False
        self.desc = 'MDS: Iteration {value:d} of {max:d}'
        self._io_wrapper = ProgressStringIO(self, n_init)
