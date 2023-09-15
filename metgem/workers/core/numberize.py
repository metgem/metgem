import pandas as pd

from metgem.workers.base import BaseWorker
from metgem.workers.options import NumberizeOptions


class NumberizeWorker(BaseWorker):

    def __init__(self, widget: 'NetworkFrame', options: NumberizeOptions):
        super().__init__()
        self._widget = widget
        self.options = options
        self.max = 0
        self.iterative_update = True
        self.desc = 'Numberizing clusters...'

    # noinspection PyGlobalUndefined, PyUnresolvedReferences
    @staticmethod
    def import_modules():
        pass

    def run(self):
        if self.isStopped():
            self.canceled.emit()
            return False

        subgraphs = sorted(self._widget.graph.clusters().subgraphs(), key=lambda g: g.vcount(), reverse=True)
        nodes_clusters = {v['name']: i+1 for i, g in enumerate(subgraphs) for v in g.vs}
        result = pd.DataFrame.from_dict(nodes_clusters, orient='index')

        if not self.isStopped():
            return result
        else:
            self.canceled.emit()
