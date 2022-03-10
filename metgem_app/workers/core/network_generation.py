import numpy as np
import pandas as pd
from libmetgem.network import generate_network

from ..base import BaseWorker
from ..options import NetworkVisualizationOptions
from ...config import RADIUS


class GenerateNetworkWorker(BaseWorker):

    def __init__(self, scores, mzs, graph, options: NetworkVisualizationOptions,
                 keep_vertices=False):
        super().__init__()
        self._scores = scores
        self._mzs = mzs
        self._graph = graph
        self.options = options
        self._keep_vertices = keep_vertices
        self.max = len(mzs)
        self.iterative_update = True
        self.desc = 'Generating Network...'

    def run(self):
        def callback(value):
            if value < 0:
                self.max += -value
            else:
                self.updated.emit(min(value, self.max))
            return not self.isStopped()

        # Create edges table (filter score below a threshold and apply TopK algorithm
        interactions = generate_network(self._scores, self._mzs,
                                        self.options.pairs_min_cosine,
                                        self.options.top_k,
                                        callback=callback)

        # Recreate graph deleting all previously created edges and eventually nodes
        graph = self._graph
        graph.delete_edges(self._graph.es)
        if not self._keep_vertices:
            graph.delete_vertices(graph.vs)
            nodes_idx = np.arange(self._scores.shape[0])
            graph.add_vertices(nodes_idx.tolist())

        # Add edges from edges table
        graph.add_edges(zip(interactions['Source'], interactions['Target']))
        graph.es['__weight'] = interactions['Cosine'].tolist()

        # Set width for all edges based on their weight
        widths = np.array(interactions['Cosine'])
        if widths.size > 0:
            # noinspection PyUnboundLocalVariable
            min_ = max(0, widths.min() - 0.1)
            if min_ != widths.max():
                widths = (RADIUS - 1) * (widths - min_) / (widths.max() - min_) + 1
            else:
                widths = RADIUS
        else:
            widths = RADIUS
        graph.es['__width'] = widths

        if not self.isStopped():
            return pd.DataFrame(interactions), graph
        else:
            self.canceled.emit()
