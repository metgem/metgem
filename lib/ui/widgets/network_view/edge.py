from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsPathItem, QStyle)
from PyQt5.QtCore import (Qt, QPointF, QLineF, QRectF)

from ....config import RADIUS, NODE_BORDER_WIDTH


class Edge(QGraphicsPathItem):
    Type = QGraphicsItem.UserType + 2

    def __init__(self, index, source_node, dest_node, weight=1, width=1):
        super().__init__()

        self.__is_self_loop = False

        self.id = index
        self.source_point = QPointF()
        self.dest_point = QPointF()
        self.weight = weight

        self.setAcceptedMouseButtons(Qt.LeftButton)
        self._source = source_node
        self._dest = dest_node
        self._source.addEdge(self)
        if self._source != self._dest:
            self._dest.addEdge(self)

        self.setColor(Qt.darkGray)
        self.setWidth(width)
        self.adjust()

        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def index(self):
        return self.id

    def setColor(self, color):
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)

    def setWidth(self, width):
        pen = self.pen()
        if self._source != self._dest and width is not None:
            pen.setWidth(width)
        else:
            pen.setWidth(1)
        self.setPen(pen)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.setZValue(not self.isSelected())  # Bring item to front
            self.setCacheMode(self.cacheMode())  # Force redraw
        return super().itemChange(change, value)

    def sourceNode(self):
        return self._source

    def setSourceNode(self, node):
        self._source = node
        self.adjust()

    def destNode(self):
        return self._dest

    def setDestNode(self, node):
        self._dest = node
        self.adjust()

    def adjust(self):
        if not self._source or not self._dest:
            return

        line = QLineF(self.mapFromItem(self._source, 0, 0),
                      self.mapFromItem(self._dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > 2 * RADIUS + NODE_BORDER_WIDTH:
            edge_offset = QPointF((line.dx() * (RADIUS + NODE_BORDER_WIDTH + 1)) / length,
                                  (line.dy() * (RADIUS + NODE_BORDER_WIDTH + 1)) / length)
            self.source_point = line.p1() + edge_offset
            self.dest_point = line.p2() - edge_offset
        else:
            self.source_point = line.p1()
            self.dest_point = line.p1()

        path = QPainterPath()
        if self.sourceNode() == self.destNode():  # Draw self-loops
            self.__is_self_loop = True
            path.moveTo(self.source_point.x() - RADIUS - NODE_BORDER_WIDTH * 2,
                        self.source_point.y())
            path.cubicTo(QPointF(self.source_point.x() - 4 * RADIUS,
                                 self.source_point.y()),
                         QPointF(self.source_point.x(),
                                 self.source_point.y() - 4 * RADIUS),
                         QPointF(self.dest_point.x(),
                                 self.dest_point.y() - RADIUS - NODE_BORDER_WIDTH * 2))
        else:
            self.__is_self_loop = False
            path.moveTo(self.source_point)
            path.lineTo(self.dest_point)
        self.setPath(path)

    def paint(self, painter, option, widget):
        pen = self.pen()

        # If selected, change color to red
        if option.state & QStyle.State_Selected:
            pen.setColor(Qt.red)

        painter.setPen(pen)
        painter.drawPath(self.path())

    def boundingRect(self):
        brect = super().boundingRect()
        if self.__is_self_loop:
            w = self.pen().width()
            brect = QRectF(brect.x() + 2 * RADIUS - NODE_BORDER_WIDTH * 2 - w,
                           brect.y() + 2 * RADIUS - NODE_BORDER_WIDTH * 2 - w,
                           2 * (RADIUS + NODE_BORDER_WIDTH + 1 + w),
                           2 * (RADIUS + NODE_BORDER_WIDTH + 1 + w))
        return brect