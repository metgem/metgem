import numpy as np
import igraph as ig
import fa2

from .base import BaseWorker
from ..config import RADIUS


class NetworkWorker(BaseWorker):
    
    def __init__(self, graph):
        super().__init__()
        self.graph = graph

    def run(self):
        total_vcount = self.graph.vcount()
        layout = np.zeros((total_vcount, 2))

        forceatlas2 = fa2.ForceAtlas2(adjustSizes=2*RADIUS, scalingRatio=RADIUS, verbose=False)

        clusters = sorted(self.graph.clusters(), key=len, reverse=True)
        dx, dy = 0, 0
        max_height = 0
        max_width = 0
        processed_vcount = 0
        for i, ids in enumerate(clusters):
            if self._should_stop:
                self.canceled.emit()
                return False
                
            graph = self.graph.subgraph(ids)
            vcount = graph.vcount()
            
            if vcount == 1:
                l = ig.Layout([(0, 0)])
                border = 2*RADIUS
            elif vcount == 2:
                l = ig.Layout([(0, -2*RADIUS), (0, 2*RADIUS)])
                border = 2*RADIUS
            else:
                l = forceatlas2.forceatlas2_igraph_layout(graph, pos=None, iterations=1000, weight_attr='__weight')
                border = 5*RADIUS
            
            bb = l.bounding_box(border=border)
            l.translate(dx-bb.left, dy-bb.top)
        
            for coord, node in zip(l, graph.vs):
                layout[node['__network_gobj'].index] = coord
                
            if max_width == 0:
                max_width = bb.width*2
        
            dx += bb.width
            max_height = max(max_height, bb.height)
            if dx >= max_width:
                dx = 0
                dy += max_height
                max_height = 0

            processed_vcount += vcount
            self.updated.emit(processed_vcount / total_vcount * 100)

        self._result = layout
        self.finished.emit()
