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
                         min_score=0.70,
                         min_scores_above_threshold=1,
                         early_exaggeration=12,
                         barnes_hut=True,
                         angle=0.5,
                         n_iter=1000,
                         random=False)

    
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

    
class TSNEWorker(BaseWorker):
    
    def __init__(self, scores, options):
        super().__init__()
        self._scores = scores
        self.options = options

        method = 'barnes_hut' if options.barnes_hut else 'exact'
        random_state = None if options.random else 0
        n_iter = options.n_iter if options.n_iter >= 250 else 250  # Number of iterations should be at least 250
        self._tsne = TSNE(learning_rate=options.learning_rate,
                          early_exaggeration=options.early_exaggeration,
                          perplexity=options.perplexity, verbose=2, n_iter=n_iter,
                          random_state=random_state, metric='precomputed',
                          method=method, angle=options.angle)

        self.max = self._tsne.n_iter
        self.iterative_update = False
        self.desc = 't-SNE: Iteration {value:d} of {max:d}'

    def run(self):
        sys.stdout = ProgressStringIO(self)

        # Compute layout
        mask = (self._scores >= self.options.min_score).sum(axis=0) > self.options.min_scores_above_threshold
        layout = np.zeros((self._scores.shape[0], 2))
        line = None
        if np.any(mask):
            try:
                layout[mask] = self._tsne.fit_transform(1 - self._scores[mask][:, mask])
            except UserRequestedStopError:
                sys.stdout = sys.__stdout__
                self.canceled.emit()
                return
            else:
                # Adjust scale
                bb = BoundingBox(layout[mask])
                layout *= (2*RADIUS**2 / bb.width)

                # Calculate positions for excluded nodes
                bb = BoundingBox(layout[mask])
                dx, dy = 0, 5 * RADIUS
                line = (bb.left-bb.width/2-5*RADIUS, bb.bottom+5*RADIUS/2, bb.left+bb.width*3/2, bb.bottom+5*RADIUS/2)
                for index in np.where(~mask)[0]:
                    layout[index] = (bb.left - bb.width/2 + dx, bb.bottom + dy)
                    dx += 5 * RADIUS
                    if dx >= bb.width*2:
                        dx = 0
                        dy += 5 * RADIUS

        sys.stdout = sys.__stdout__
        return layout, line
