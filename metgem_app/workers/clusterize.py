import numpy as np

from .base import BaseWorker
from ..utils import AttrDict


class ClusterizeOptions(AttrDict):

    def __init__(self):
        super().__init__(column_name='clusters',
                         min_cluster_size=5,
                         min_samples=None,
                         cluster_selection_epsilon=0.,
                         cluster_selection_method='eom')


class ClusterizeWorker(BaseWorker):

    def __init__(self, view, options):
        super().__init__()
        self._view = view
        self.options = options
        self.max = 0
        self.iterative_update = True
        self.desc = 'Clusterizing data (HDBSCAN)...'

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        global HDBSCAN
        from hdbscan import HDBSCAN

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        options = self.options
        clusterer = HDBSCAN(min_cluster_size=options.min_cluster_size,
                            min_samples=options.min_samples,
                            cluster_selection_epsilon=options.cluster_selection_epsilon,
                            cluster_selection_method=options.cluster_selection_method)
        layout_data = self._view.get_layout_data()
        isolated_nodes = layout_data['isolated_nodes']
        layout = layout_data['layout']
        mask = np.ones_like(layout, dtype=bool)
        mask[isolated_nodes] = False
        x = layout[mask].reshape(-1, 2)
        clusterer.fit(x.astype(np.float64))

        i = 0
        result = []
        for n in self._view.gvNetwork.scene().nodes():
            if n.index() in isolated_nodes:
                result.append("Noise")
            else:
                result.append(f"Cluster {clusterer.labels_[i] + 1}" if clusterer.labels_[i] > 0 else "Noise")
                i += 1

        if not self.isStopped():
            return result
        else:
            self.canceled.emit()
