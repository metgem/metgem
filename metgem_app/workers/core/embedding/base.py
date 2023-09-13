import sys

import numpy as np

from metgem_app.workers.base import BaseWorker, UserRequestedStopError
from metgem_app.config import RADIUS


class BoundingBox:
    def __init__(self, layout):
        self.left, self.top = layout.min(axis=0)
        self.right, self.bottom = layout.max(axis=0)
        self.height = self.bottom - self.top
        self.width = self.right - self.left

    def __repr__(self):
        return f"{self.__class__.__name__}-> left:{self.left}, right:{self.right}, " \
               f"top:{self.top}, bottom: {self.bottom}, " \
               f"height:{self.height}, width: {self.width}"


class EmbeddingWorker(BaseWorker):

    def __init__(self, scores, options):
        super().__init__()
        self._scores = scores
        self.options = options
        self.use_distance_matrix = True
        self._io_wrapper = None
        self.init()

    # noinspection PyAttributeOutsideInit
    def init(self):
        raise NotImplementedError

    def run(self):
        if self._io_wrapper is not None:
            sys.stdout = self._io_wrapper

        # Compute layout
        mask = (self._scores >= self.options.min_score).sum(axis=0) > self.options.min_scores_above_threshold
        isolated_nodes = []

        if np.any(mask):
            layout = np.empty((self._scores.shape[0], 2))

            try:
                matrix = self._scores[mask][:, mask]
                matrix = 1 - matrix if self.use_distance_matrix else matrix
                layout[mask] = self._estimator.fit_transform(matrix)
                del matrix
            except UserRequestedStopError:
                if self._io_wrapper is not None:
                    sys.stdout = sys.__stdout__
                self.canceled.emit()
                return
            else:
                # Adjust scale
                bb = BoundingBox(layout[mask])
                layout *= (2 * RADIUS ** 2 / bb.width)

                # Calculate positions for excluded nodes
                isolated_nodes = np.where(~mask)[0]
                bb = BoundingBox(layout[mask])
                dx, dy = 0, 10 * RADIUS
                for index in isolated_nodes:
                    layout[index] = (bb.left - bb.width / 2 + dx, bb.bottom + dy)
                    dx += 5 * RADIUS
                    if dx >= bb.width * 2:
                        dx = 0
                        dy += 5 * RADIUS
        else:
            try:
                matrix = self._scores
                matrix = 1 - matrix if self.use_distance_matrix else matrix
                layout = self._estimator.fit_transform(matrix)
                del matrix
            except UserRequestedStopError:
                if self._io_wrapper is not None:
                    sys.stdout = sys.__stdout__
                self.canceled.emit()
                return

        if self._io_wrapper is not None:
            sys.stdout = sys.__stdout__

        return layout, isolated_nodes
