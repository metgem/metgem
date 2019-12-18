from .base import BaseWorker
from ..utils import AttrDict

import numpy as np

try:
    import hdbscan
except ImportError:
    HAS_HDBSCAN = False
else:
    HAS_HDBSCAN = True


class ClusterizeOptions(AttrDict):

    def __init__(self):
        super().__init__(column_name='clusters',
                         min_cluster_size=5,
                         min_samples=None,
                         cluster_selection_epsilon=0.,
                         cluster_selection_method='eom')


class ClusterizeWorker(BaseWorker):

    def __init__(self, scores, options):
        super().__init__()
        self._scores = scores
        self.options = options
        self.max = 0
        self.iterative_update = True
        self.desc = 'Clusterizing data (HDBSCAN)...'

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        options = self.options
        clusterer = hdbscan.HDBSCAN(metric='precomputed',
                                    min_cluster_size=options.min_cluster_size,
                                    min_samples=options.min_samples,
                                    cluster_selection_epsilon=options.cluster_selection_epsilon,
                                    cluster_selection_method=options.cluster_selection_method)
        clusterer.fit(1 - self._scores.astype(np.float64))
        result = [f"Cluster {group + 1}" if group != -1 else "Noise"
                  for group in clusterer.labels_]

        if not self.isStopped():
            return result
        else:
            self.canceled.emit()
