import io

from metgem_app.workers.core.embedding.base import EmbeddingWorker, UserRequestedStopError
from metgem_app.workers.options import TSNEVisualizationOptions

    
class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def write(self, s):
        """Method used to follow progress of processing."""

        if self.parent.isStopped():
            raise UserRequestedStopError()
        elif 'Iteration' in s:
            s = s.split(' Iteration ')[1]
            if ': error =' in s:
                s = s.split(': error =')[0]
            try:
                self.parent.updated.emit(int(s))
            except ValueError:
                pass

    
class TSNEWorker(EmbeddingWorker):

    def __init__(self, scores, options: TSNEVisualizationOptions):
        super().__init__(scores, options)

    # noinspection PyAttributeOutsideInit
    def init(self):
        method = 'barnes_hut' if self.options.barnes_hut else 'exact'
        random_state = None if self.options.random else 0
        # Number of iterations should be at least 250
        n_iter = self.options.n_iter if self.options.n_iter >= 250 else 250
        self._estimator = TSNE(learning_rate=self.options.learning_rate,
                               early_exaggeration=self.options.early_exaggeration,
                               perplexity=self.options.perplexity, verbose=2, n_iter=n_iter,
                               random_state=random_state, metric='precomputed',
                               method=method, angle=self.options.angle,
                               init="random")

        self.max = self._estimator.n_iter
        self._io_wrapper = ProgressStringIO(self)
        self.iterative_update = False
        self.desc = 't-SNE: Iteration {value:d} of {max:d}'

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global TSNE
        # noinspection PyUnresolvedReferences
        from sklearn.manifold import TSNE
