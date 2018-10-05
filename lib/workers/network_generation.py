from .base import BaseWorker
from ..libmetgem_wrapper import generate_network
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
                         pairs_min_cosine=0.65,
                         max_connected_nodes=1000)


class GenerateNetworkWorker(BaseWorker):
    def __init__(self, scores, mzs, options):
        super().__init__()
        self._scores = scores
        self._mzs = mzs
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

        interactions = generate_network(self._scores, self._mzs,
                                        self.options.pairs_min_cosine,
                                        self.options.top_k,
                                        callback=callback)
        if not self.isStopped():
            return interactions
        else:
            self.canceled.emit()
