import sys
import io

from sklearn.manifold import TSNE

from .base import BaseWorker
from ..utils import AttrDict
from ..errors import UserRequestedStopError


class TSNEVisualizationOptions(AttrDict):
    """Class containing TSNE visualization options.
    """
    
    def __init__(self):
        super().__init__(perplexity=6,
                         learning_rate=200,
                         early_exaggeration=12,
                         barnes_hut=True,
                         angle=0.5,
                         random=False)

    
class ProgressStringIO(io.StringIO):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def write(self, s):
        """Method used to follow progress of processing."""

        if self.parent._should_stop:
            raise UserRequestedStopError()
        elif 'Iteration' in s:
            s = s.split(' Iteration ')[1]
            if ': error =' in s:
                s = s.split(': error =')[0]
            try:
                self.parent.updated.emit(int(s))
            except ValueError:
                pass

    
class TSNEWorker(BaseWorker):
    
    def __init__(self, scores, options):
        super().__init__()
        self._scores = scores
        self.options = options

        method = 'barnes_hut' if options.barnes_hut else 'exact'
        random_state = 0 if options.random else None
        self._tsne = TSNE(learning_rate=options.learning_rate,
                          early_exaggeration=options.early_exaggeration,
                          perplexity=options.perplexity, verbose=2,
                          random_state=random_state, metric='precomputed',
                          method=method, angle=options.angle)

        self.max = self._tsne.n_iter
        self.iterative_update = False
        self.desc = 'TSNE: Iteration {value:d} of {max:d}'

    def run(self):
        sys.stdout = ProgressStringIO(self)
        try:
            self._result = self._tsne.fit_transform(self._scores)
        except UserRequestedStopError:
            sys.stdout = sys.__stdout__
            self.canceled.emit()
            return False
            
        sys.stdout = sys.__stdout__
        self.finished.emit()
