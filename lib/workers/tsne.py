import sys
import io

import numpy as np

from sklearn.manifold import TSNE

from .base import BaseWorker
from ..utils import AttrDict, BoundingBox
from ..errors import UserRequestedStopError
from ..config import RADIUS


class TSNEVisualizationOptions(AttrDict):
    """Class containing TSNE visualization options.
    """
    
    def __init__(self):
        super().__init__(perplexity=6,
                         learning_rate=200,
                         min_score=0.65,
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
        self._scores = scores.copy()
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
        self.desc = 't-SNE: Iteration {value:d} of {max:d}'

    def run(self):
        sys.stdout = ProgressStringIO(self)

        # Compute layout
        self._scores[self._scores < self.options.min_score] = 0

        mask = self._scores.sum(axis=0) > 1
        layout = np.zeros((self._scores.shape[0], 2))
        if np.any(mask):
            try:
                layout[mask] = self._tsne.fit_transform(1 - self._scores[mask][:, mask])
            except UserRequestedStopError:
                sys.stdout = sys.__stdout__
                self.canceled.emit()
                return False
            else:
                # Adjust scale
                layout *= RADIUS

                # Calculate positions for excluded nodes
                bb = BoundingBox(layout)
                dx, dy = 0, 5 * RADIUS
                for index in np.where(~mask)[0]:
                    layout[index] = (bb.left + dx, bb.bottom + dy)
                    dx += 5 * RADIUS
                    if dx >= bb.width:
                        dx = 0
                        dy += 5 * RADIUS

        self._result = layout
            
        sys.stdout = sys.__stdout__
        self.finished.emit()
