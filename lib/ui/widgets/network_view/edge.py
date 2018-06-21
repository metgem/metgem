from PyQt5.QtGui import QPainterPath, QPen
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsPathItem, QStyle)
from PyQt5.QtCore import (Qt, QPointF, QLineF, QRectF)

from .style import NetworkStyle


class Edge(QGraphicsPathItem):
    Type = QGraphicsItem.UserType + 2

    def __init__(self, index, source_node, dest_node, weight=1, width=1):
        super().__init__()

        self.__is_self_loop = False

        self.id = index
        self.source_point = QPointF()
        self.dest_point = QPointF()
        self.weight = weight

        self._source = source_node
        self._dest = dest_node
        self._source.addEdge(self)
        if self._source != self._dest:
            self._dest.addEdge(self)

        self.setPen(QPen(Qt.darkGray))
        self.setWidth(width)

        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def index(self):
        return self.id

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

    def setPen(self, pen: QPen):
        pen.setWidth(self.pen().width())
        super().setPen(pen)

    def width(self):
        return self.pen().width()

    def setWidth(self, width):
        pen = self.pen()
        if self._source != self._dest and width is not None:
            pen.setWidth(width)
        else:
            pen.setWidth(1)
        super().setPen(pen)

    def adjust(self):
        if not self._source or not self._dest:
            return

        line = QLineF(self.mapFromItem(self._source, 0, 0),
                      self.mapFromItem(self._dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        min_len = self._source.radius() + self._dest.radius() + self._source.pen().width() + self._dest.pen().width()
        if length > min_len:
            offset = QPointF((line.dx() * (self._source.radius() + self._source.pen().width() + 1)) / length,
                             (line.dy() * (self._source.radius() + self._source.pen().width() + 1)) / length)
            self.source_point = line.p1() + offset
            offset = QPointF((line.dx() * (self._dest.radius() + self._dest.pen().width() + 1)) / length,
                             (line.dy() * (self._dest.radius() + self._dest.pen().width() + 1)) / length)
            self.dest_point = line.p2() - offset
        else:
            self.source_point = self.dest_point = line.p1()

        path = QPainterPath()
        if self.sourceNode() == self.destNode():  # Draw self-loops
            self.__is_self_loop = True
            radius = self._source.radius()
            path.moveTo(self.source_point.x() - radius - 2 * self._source.pen().width(),
                        self.source_point.y())
            path.cubicTo(QPointF(self.source_point.x() - 4 * radius,
                                 self.source_point.y()),
                         QPointF(self.source_point.x(),
                                 self.source_point.y() - 4 * radius),
                         QPointF(self.dest_point.x(),
                                 self.dest_point.y() - radius - 2 * self._source.pen().width()))
        else:
            self.__is_self_loop = False
            path.moveTo(self.source_point)
            path.lineTo(self.dest_point)
        self.setPath(path)

    def updateStyle(self, style: NetworkStyle, old: NetworkStyle = None):
        self.setPen(style.edgePen())
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.setZValue(not self.isSelected())  # Bring item to front
            self.setCacheMode(self.cacheMode())  # Force redraw
        return super().itemChange(change, value)

    def boundingRect(self):
        brect = super().boundingRect()
        if self.__is_self_loop:
            w = self.pen().width()
            radius = self._source.radius()
            width = self._source.pen().width()
            delta = 2 * radius - 2 * width - w
            size = 2 * (radius + width + 1 + w)
            brect = QRectF(brect.x() + delta, brect.y() + delta, size, size)
        return brect

    # noinspection PyMethodOverriding
    def paint(self, painter, option, widget):
        scene = self.scene()
        if scene is None:
            return

        # If selected, change color to red
        if option.state & QStyle.State_Selected:
            pen = scene.networkStyle().edgePen(state='selected')
            pen.setWidth(self.pen().width())
        else:
            pen = self.pen()

        painter.setPen(pen)
        painter.drawPath(self.path())
