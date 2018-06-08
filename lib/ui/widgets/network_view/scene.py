from PyQt5.QtGui import QColor

try:
    from .NetworkView import Node, Edge, NetworkScene as BaseNetworkScene

    class NetworkScene(BaseNetworkScene):
        def setLayout(self, layout, scale=0):
            super().setLayout(layout.ravel(), scale)

except ImportError:
    print('Warning: Using Python fallback NetworkView')

    import itertools

    from PyQt5.QtCore import Qt, pyqtSignal, QRectF
    from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem

    from .node import Node
    from .edge import Edge

    from .graphicsitem import GraphicsItemLayer


    class NetworkScene(QGraphicsScene):
        scaleChanged = pyqtSignal(float)
        layoutChanged = pyqtSignal()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._colors = []

            self._scale = 1

            self.clear()

        def clear(self):
            super().clear()

            self.nodesLayer = GraphicsItemLayer()
            self.addItem(self.nodesLayer)
            self.nodesLayer.setZValue(1)

            self.edgesLayer = GraphicsItemLayer()
            self.addItem(self.edgesLayer)
            self.edgesLayer.setZValue(0)

        def addNodes(self, indexes, labels=[], positions=[], colors=[]):
            nodes = []
            for index, label, pos, color in itertools.zip_longest(indexes, labels, positions, colors):
                node = Node(index, label)
                if pos:
                    node.setPos(pos)
                if isinstance(color, QColor) and color.isValid():
                    node.setColor(color)
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
            try:
                return self.nodesLayer.childItems()
            except RuntimeError:
                return []

        def selectedNodes(self):
            try:
                return [item for item in self.selectedItems() if self.nodesLayer.isAncestorOf(item)]
            except RuntimeError:
                return []

        def setNodesSelection(self, items):
            self.clearSelection()
            if len(items) > 0:
                if isinstance(items[0], Node):
                    for node in items:
                        node.setSelected(True)
                else:
                    nodes = self.nodes()
                    for index in items:
                        nodes[index].setSelected(True)

        def selectedNodesBoundingRect(self):
            boundingRect = QRectF()
            for node in self.selectedNodes():
                boundingRect |= node.sceneBoundingRect()
            return boundingRect

        def edges(self):
            try:
                return self.edgesLayer.childItems()
            except RuntimeError:
                return []

        def selectedEdges(self):
            try:
                return [item for item in self.selectedItems() if self.edgesLayer.isAncestorOf(item)]
            except RuntimeError:
                return []

        def setEdgesSelection(self, items):
            self.clearSelection()
            edges = self.edges()
            if len(items) > 0:
                if isinstance(items[0], Edge):
                    for edge in items:
                        edge.setSelected(True)
                else:
                    for index in items:
                        edges[index].setSelected(True)

        def setLayout(self, positions, scale=None):
            scale = scale if scale is not None else self._scale
            for node in self.nodes():
                pos = positions[node.index()]
                node.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, False)
                node.setPos(*pos * scale)
                node.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

            for edge in self.edges():
                edge.adjust()

            self.layoutChanged.emit()

        def scale(self):
            return self._scale

        def setScale(self, scale=1):
            for node in self.nodes():
                node.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, False)
                node.setPos(node.pos() * scale / self._scale)
                node.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

            for edge in self.edges():
                edge.adjust()

            self._scale = scale
            self.scaleChanged.emit(scale)

        def setLabelsFromModel(self, model, column_id, role=Qt.DisplayRole):
            for node in self.nodes():
                label = model.index(node.index(), column_id).data(role)
                node.setLabel(str(label))

        def resetLabels(self):
            for node in self.nodes():
                label = str(node.index() + 1)
                node.setLabel(label)

        def pieColors(self):
            return self._colors

        def setPieColors(self, colors):
            self._colors = colors

        def setPieChartsFromModel(self, model, column_ids, role=Qt.DisplayRole):
            if len(column_ids) != len(self._colors):
                return

            for node in self.nodes():
                values = [model.index(node.index(), cid).data(role) for cid in column_ids]
                node.setPie(values)

        def resetPieCharts(self):
            for node in self.nodes():
                node.setPie(None)

        def hideItems(self, items):
            for item in items:
                item.hide()

        def showItems(self, items):
            for item in items:
                item.show()

        def hideSelectedItems(self):
            items = self.selectedItems()
            self.clearSelection()
            for item in items:
                item.hide()

        def showAllItems(self):
            for item in self.items():
                item.show()

        def nodesColors(self):
            return [node.color() for node in sorted(self.nodes(), key=lambda node: node.index())]

        def setNodesColors(self, colors):
            for node in self.nodes():
                color = colors[node.index()]
                if color.isValid():
                    node.setColor(color)

        def setSelectedNodesColor(self, color: QColor):
            for node in self.selectedNodes():
                if color.isValid():
                    node.setColor(color)

        def nodeAt(self, *args, **kwargs):
            item = self.itemAt(*args, **kwargs)
            if isinstance(item, Node):
                return item

        def edgeAt(self, *args, **kwargs):
            item = self.itemAt(*args, **kwargs)
            if isinstance(item, Edge):
                return item
