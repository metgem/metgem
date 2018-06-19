from PyQt5.QtGui import QPen, QColor, QFont, QBrush
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsEllipseItem, QStyle, QApplication)
from PyQt5.QtCore import (Qt, QRectF)

from .style import NetworkStyle


class Node(QGraphicsEllipseItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, index, radius, label=None):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)

        self._edge_list = []
        self._pie = []

        self._font = QApplication.font()
        self._text_color = QColor()
        self._radius = radius

        self.id = index
        if label is None:
            label = str(index+1)
        self._label = label

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.setBrush(Qt.lightGray)
        self.setPen(QPen(Qt.black, 1))

    def index(self) -> int:
        return self.id

    def radius(self) -> int:
        return self._radius

    def setRadius(self, radius: int):
        self._radius = radius
        self.setRect(QRectF(-radius, -radius, 2 * radius, 2 * radius))

    def font(self) -> QFont:
        return self._font

    def setFont(self, font: QFont):
        self._font = font

    def textColor(self) -> QColor:
        return self._text_color

    def setTextColor(self, color: QColor):
        self._text_color = color

    # noinspection PyMethodOverriding
    def setBrush(self, brush: QBrush, autoTextColor: bool = True):
        super().setBrush(brush)

        if autoTextColor:
            # Calculate the perceptive luminance (aka luma) - human eye favors green color...
            # See https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
            color = QBrush(brush).color()
            luma = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue() / 255
            self._text_color = QColor(Qt.black) if luma > 0.5 else QColor(Qt.white)

    def label(self):
        return self._label

    def setLabel(self, label):
        self._label = label
        self.update()

    def setPie(self, values):
        if values is not None:
            sum_ = sum(values)
            values = [v / sum_ for v in values] if sum_ > 0 else []
            self._pie = values
        else:
            self._pie = []
        self.update()

    def addEdge(self, edge):
        self._edge_list.append(edge)

    def edges(self):
        return self._edge_list

    def updateStyle(self, style: NetworkStyle, old: NetworkStyle = None):
        self.setRadius(style.nodeRadius())
        if old is None or self.brush().color() == old.nodeBrush().color():
            self.setBrush(style.nodeBrush(), autoTextColor=False)
        self.setTextColor(style.nodeTextColor())
        self.setPen(style.nodePen())
        self.setFont(style.nodeFont())
        self.update()

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

    def boundingRect(self):
        brect = super().boundingRect()
        pwidth = self.pen().width()
        size = 2 * (self.radius() + pwidth)
        return QRectF(brect.x() - pwidth, brect.y() - pwidth, size, size)

    # noinspection PyMethodOverriding
    def paint(self, painter, option, widget):
        scene = self.scene()
        if scene is None:
            return

        # If selected, change brush to yellow
        if option.state & QStyle.State_Selected:
            brush = scene.networkStyle().nodeBrush(state='selected')
            painter.setBrush(brush if brush is not None else self.brush())
            text_color = scene.networkStyle().nodeTextColor(state='selected')
            text_color = text_color if text_color is not None else self.textColor()
            painter.setPen(scene.networkStyle().nodePen(state='selected'))
        else:
            painter.setBrush(self.brush())
            painter.setPen(self.pen())
            text_color = self.textColor()

        # Draw ellipse
        if self.spanAngle() != 0 and abs(self.spanAngle()) % (360 * 16) == 0:
            painter.drawEllipse(self.rect())
        else:
            painter.drawPie(self.rect(), self.startAngle(), self.spanAngle())

        # Get level of detail
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Draw pies if any
        if lod > 0.1 and len(self._pie) > 0:
            radius = self.radius()
            rect = QRectF(-.85 * radius, -0.85 * radius, 1.7 * radius, 1.7 * radius)
            start = 0.
            colors = self.scene().pieColors()
            painter.setPen(QPen(Qt.NoPen))
            for i, v in enumerate(self._pie):
                painter.setBrush(colors[i])
                painter.drawPie(rect, start * 5760, v * 5760)
                start += v

        # Draw text
        if lod > 0.4:
            painter.setFont(self.font())
            painter.setPen(QPen(text_color, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, self._label)
