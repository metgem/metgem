import numpy as np
from libmetgem.network import generate_network

from .base import BaseWorker
from ..config import RADIUS
from ..utils import AttrDict


class NetworkVisualizationOptions(AttrDict):
    """Class containing Network visualization options.

    Attributes:
        top_k (int): Maximum numbers of edges for each nodes in the network. Default value = 10
        pairs_min_cosine (float): Minimum cosine score for network generation. Default value = 0.65
        max_connected_nodes (int): Maximum size of a Network cluster. Default value = 1000

    """
    
    def __init__(self):
        super().__init__(top_k=10,
                         pairs_min_cosine=0.7,
                         max_connected_nodes=1000)


class GenerateNetworkWorker(BaseWorker):

    def __init__(self, scores, mzs, graph, options, keep_vertices=False):
        super().__init__()
        self._scores = scores
        self._mzs = mzs
        self._graph = graph
        self._keep_vertices = keep_vertices
        self.options = options
        self.max = len(mzs)
        self.iterative_update = False
        self.desc = 'Generating Network...'

    def run(self):
        def callback(value):
            if value < 0:
                 self.max += -value
            else:
                self.updated.emit(value)
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
            min_ = max(0, widths.min() - 0.1)
            if min_ != widths.max():
                widths = (RADIUS - 1) * (widths - min_) / (widths.max() - min_) + 1
            else:
                widths = RADIUS
        else:
            widths = RADIUS
        graph.es['__width'] = widths

        # Max Connected Components option: split large clusters by removing edges with smaller weights until
        # cluster size is lower than the desired value
        graph.es['__index'] = graph.es.indices
        max_connected_nodes = self.options.max_connected_nodes
        if max_connected_nodes > 0:  # 0 means no limit
            clusters = [c for c in graph.clusters() if len(c) > max_connected_nodes]
            self.max += len(clusters)

            edges_indices_to_remove = set()  # store indices in the full graph that we will need to remove
            for ids in clusters:
                if self.isStopped():
                    self.canceled.emit()
                    return
                self.updated.emit(1)

                vcount = len(ids)
                # Clusters
                if vcount <= max_connected_nodes:
                    break

                subgraph = graph.subgraph(ids)
                while vcount > max_connected_nodes:
                    e = min(subgraph.es, key=lambda x: x['__weight'])
                    edges_indices_to_remove.add(e['__index'])
                    subgraph.delete_edges(e.index)
                    c = subgraph.clusters()
                    if len(c) > 1:
                        vcount = max(len(l) for l in c)
            graph.delete_edges(edges_indices_to_remove)
        del graph.es['__index']

        if not self.isStopped():
            return interactions, graph
        else:
            self.canceled.emit()
