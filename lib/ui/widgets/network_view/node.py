from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsEllipseItem, QStyle)
from PyQt5.QtCore import (Qt, QRectF)

from ....config import RADIUS, NODE_BORDER_WIDTH, FONT_SIZE


class Node(QGraphicsEllipseItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, index, label=None):
        super().__init__(-RADIUS, -RADIUS, 2 * RADIUS, 2 * RADIUS)

        self._edge_list = []
        self._pie = []

        self.id = index
        if label is None:
            label = str(index+1)
        self._label = label

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.setColor(Qt.lightGray)
        self.setPen(QPen(Qt.black, NODE_BORDER_WIDTH))

    def index(self):
        return self.id

    def color(self):
        return self._color if self._color != Qt.lightGray else QColor()

    def setColor(self, color):
        self._color = color

    def label(self):
        return self._label

    def setLabel(self, label):
        self._label = label
        if self.isVisible():
            self.update()

    def setPie(self, values):
        sum_ = sum(values)
        values = [v / sum_ for v in values] if sum_ > 0 else []
        self._pie = values

        if self.isVisible():
            self.update()

    def addEdge(self, edge):
        self._edge_list.append(edge)
        edge.adjust()

    def edges(self):
        return self._edge_list

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            for edge in self._edge_list:
                edge.adjust()
        elif change == QGraphicsItem.ItemSelectedChange:
            self.setZValue(not self.isSelected())  # Bring item to front
            self.setCacheMode(self.cacheMode())  # Force redraw
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        # If selected, change brush to yellow
        if option.state & QStyle.State_Selected:
            painter.setBrush(Qt.yellow)
        else:
            painter.setBrush(self._color)

        # Draw ellipse
        if self.spanAngle() != 0 and abs(self.spanAngle()) % (360 * 16) == 0:
            painter.drawEllipse(self.rect())
        else:
            painter.drawPie(self.rect(), self.startAngle(), self.spanAngle())

        # Get level of detail
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Draw pies if any
        if lod > 0.1 and len(self._pie) > 0:
            rect = QRectF(-0.85 * RADIUS, -0.85 * RADIUS, 1.7 * RADIUS, 1.7 * RADIUS)
            start = 0.
            colors = self.scene().pieColors()
            painter.setPen(QPen(Qt.NoPen))
            for i, v in enumerate(self._pie):
                painter.setBrush(colors[i])
                painter.drawPie(rect, start * 5760, v * 5760)
                start += v

        # Draw text
        if lod > 0.4:
            font = painter.font()
            font.setPixelSize(FONT_SIZE)
            painter.setFont(font)
            painter.setPen(QPen(Qt.black, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, self._label)
