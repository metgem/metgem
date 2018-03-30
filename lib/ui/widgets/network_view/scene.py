import itertools

from PyQt5.QtWidgets import QGraphicsScene

try:
    from .NetworkView import Node, Edge, NetworkScene as BaseNetworkScene

    class NetworkScene(BaseNetworkScene):
        def setLayout(self, layout):
            super().setLayout(layout.ravel())

except ImportError:
    print('Warning: Using Python fallback NetworkView')
    from .node import Node
    from .edge import Edge

    from .graphicsitem import GraphicsItemLayer


    class NetworkScene(QGraphicsScene):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.clear()

        def clear(self):
            super().clear()

            self.nodesLayer = GraphicsItemLayer()
            self.addItem(self.nodesLayer)
            self.nodesLayer.setZValue(1)

            self.edgesLayer = GraphicsItemLayer()
            self.addItem(self.edgesLayer)
            self.edgesLayer.setZValue(0)

        def addNodes(self, indexes, labels, positions=[]):
            nodes = []
            for index, label, pos in itertools.zip_longest(indexes, labels, positions):
                node = Node(index, label)
                if pos:
                    node.setPos(pos)
                node.setParentItem(self.nodesLayer)
                nodes.append(node)
            return nodes

        def addEdges(self, indexes, sourceNodes, destNodes, weights, widths):
            edges = []
            for index, source, dest, weight, width in zip(indexes, sourceNodes, destNodes, weights, widths):
                edge = Edge(index, source, dest, weight, width)
                edge.setParentItem(self.edgesLayer)
                edges.append(edge)
            return edges

        def nodes(self):
            return self.nodesLayer.childItems()

        def selectedNodes(self):
            return [item for item in self.selectedItems() if self.nodesLayer.isAncestorOf(item)]

        def setNodesSelection(self, items):
            self.clearSelection()
            nodes = self.nodes()
            if len(items) > 0:
                if isinstance(items[0], Node):
                    for node in items:
                        node.setSelected(True)
                else:
                    for index in items:
                        nodes[index].setSelected(True)

        def edges(self):
            return self.edgesLayer.childItems()

        def selectedEdges(self):
            return [item for item in self.selectedItems() if self.edgesLayer.isAncestorOf(item)]

        def setEdgesSelection(self, items):
            self.clearSelection()
            edges = self.edges()
            if len(items) > 0:
                if isinstance(items[0], Node):
                    for edge in items:
                        edge.setSelected(True)
                else:
                    for index in items:
                        edges[index].setSelected(True)

        def setLayout(self, positions):
            for node, pos in zip(self.nodes(), positions):
                node.setPos(*pos)
