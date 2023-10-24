from metgem.workers.base import BaseWorker
from metgem.workers.options import NetworkVisualizationOptions


class MaxConnectedComponentsWorker(BaseWorker):

    def __init__(self, graph, options: NetworkVisualizationOptions,
                 keep_vertices=False):
        super().__init__()
        self._graph = graph
        self._keep_vertices = keep_vertices
        self.options = options
        self.max = 0
        self.iterative_update = True
        self.desc = 'Applying Maximum Connected Components Settings...'

    def run(self):
        graph = self._graph

        # Max Connected Components option: split large clusters by removing edges with smaller weights until
        # cluster size is lower than the desired value
        graph.es['__index'] = graph.es.indices
        max_connected_nodes = self.options.max_connected_nodes
        if max_connected_nodes > 0:  # 0 means no limit
            clusters = [c for c in graph.clusters() if len(c) > max_connected_nodes]
            self.max = len(clusters)

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
            return graph
        else:
            self.canceled.emit()
