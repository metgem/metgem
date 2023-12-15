import io

from metgem.workers.core.embedding.base import EmbeddingWorker, UserRequestedStopError
from metgem.workers.options import UMAPVisualizationOptions


class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self._read_value = False

    def write(self, s):
        """Method used to follow progress of processing."""

        if self.parent.isStopped():
            raise UserRequestedStopError()
        elif s == "\tcompleted ":
            self._read_value = True
        elif self._read_value and s != " ":
            self._read_value = False
            try:
                self.parent.updated.emit(int(s))
            except ValueError:
                pass


class UMAPWorker(EmbeddingWorker):

    def __init__(self, scores, options: UMAPVisualizationOptions):
        super().__init__(scores, options)

    # noinspection PyAttributeOutsideInit
    def init(self):
        random_state = None if self.options.random else 0
        self._estimator = UMAP(n_neighbors=self.options.n_neighbors,
                               min_dist=self.options.min_dist,
                               n_epochs=self.options.n_epochs, verbose=True,
                               random_state=random_state, metric='precomputed')

        # Set number of epochs (see UMAP.transform)
        if self.options.n_epochs is None:
            # For smaller datasets we can use more epochs
            if self._scores.shape[0] <= 10000:
                n_epochs = 100
            else:
                n_epochs = 30
        else:
            n_epochs = self.n_epochs // 3.0

        self.max = n_epochs
        self.iterative_update = False
        self.desc = 'UMAP: Iteration {value:d} of {max:d}'
        self._io_wrapper = ProgressStringIO(self)

    def get_n_neighbors(self, n: int):
        return self.options.n_neighbors

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global UMAP
        # noinspection PyUnresolvedReferences
        from umap import UMAP
