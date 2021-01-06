import math
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt5.QtGui import (QPainterPath, QPainterPathStroker, QPainter,
                         QBrush, QColor, QPolygonF, QPen)
from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsSimpleTextItem,
                             QGraphicsItem, QGraphicsEllipseItem, QStyleOptionGraphicsItem, QWidget)


class ArrowItem(QGraphicsLineItem):

    def __init__(self, *args, has_head=True, has_tail=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 10, Qt.SolidLine))
        self._has_head = has_head
        self._has_tail = has_tail

    def hasTail(self):
        return self._has_tail

    def setTail(self, visible: bool):
        if self._has_tail != visible:
            self._has_tail = visible
            self.update()

    def hasHead(self):
        return self._has_head

    def setHead(self, visible: bool):
        if self._has_head != visible:
            self._has_head = visible
            self.update()

    def getAngle(self):
        dx, dy = self.line().dx(), self.line().dy()
        return math.pi - math.atan(dx / dy) if dy != 0 else math.copysign(math.pi / 2, dx)

    def shape(self):
        path = QPainterPath()
        stroker = QPainterPathStroker()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker.setWidth(self.pen().width() * 5.)
        return stroker.createStroke(path)

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen = self.pen()
            pen.setColor(color)
            painter.setPen(pen)
            brush = QBrush()
            brush.setColor(color)
            brush.setStyle(Qt.SolidPattern)
            painter.setBrush(brush)
        else:
            painter.setPen(self.pen())
            brush = QBrush()
            brush.setColor(self.pen().color())
            brush.setStyle(Qt.SolidPattern)
            painter.setBrush(brush)
        painter.drawLine(self.line())

        angle = self.getAngle()
        if self.line().dy() >= 0.:
            angle = 1.0 * math.pi + angle
        size = self.pen().width() * 5.

        if self._has_tail:
            p0 = self.line().p1()
            p1 = p0 + QPointF(math.sin(angle + math.pi + math.pi * .1) * size,
                              -math.cos(angle + math.pi + math.pi * .1) * size)
            p2 = p0 + QPointF(math.sin(angle + math.pi - math.pi * .1) * size,
                              -math.cos(angle + math.pi - math.pi * .1) * size)
            painter.drawPolygon(QPolygonF() << p0 << p1 << p2)

        if self._has_head:
            p0 = self.line().p2()
            p1 = p0 + QPointF(math.sin(angle + math.pi * .1) * size,
                              -math.cos(angle + math.pi * .1) * size)
            p2 = p0 + QPointF(math.sin(angle - math.pi * .1) * size,
                              -math.cos(angle - math.pi * .1) * size)
            painter.drawPolygon(QPolygonF() << p0 << p1 << p2)

    def __str__(self):
        return 'Arrow' if self.hasHead() or self.hasTail() else 'Line'


class RectItem(QGraphicsRectItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 100, Qt.SolidLine))
        self.setBrush(QBrush(Qt.black, Qt.SolidPattern))

    def shape(self) -> QPainterPath:
        rect = self.rect()
        path = QPainterPath()
        stroker = QPainterPathStroker()
        path.addRect(rect)
        stroker.setWidth(self.pen().width())
        shape = stroker.createStroke(path)
        return shape

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen = self.pen()
            pen.setColor(color)
            painter.setPen(pen)
        else:
            painter.setPen(self.pen())
        painter.drawRect(self.rect())

    def __str__(self):
        return 'Rectangle'


class EllipseItem(QGraphicsEllipseItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 10, Qt.SolidLine))
        self.setBrush(QBrush(Qt.black, Qt.SolidPattern))

    def shape(self) -> QPainterPath:
        rect = self.rect()
        path = QPainterPath()
        stroker = QPainterPathStroker()
        path.addEllipse(rect)
        stroker.setWidth(self.pen().width())
        shape = stroker.createStroke(path)
        if self.isSelected():
            handles_path = QPainterPath()
            handles_path.addRect(QRectF(rect.topLeft(), QSizeF(2., 2.)))
            handles_path.addRect(QRectF(rect.topRight() - QPointF(2., 0.), QSizeF(5., 5.)))
            handles_path.addRect(QRectF(rect.bottomLeft() - QPointF(0., 2.), QSizeF(2., 2.)))
            handles_path.addRect(QRectF(rect.bottomRight() - QPointF(2., 2.), QSizeF(2., 2.)))
            shape += handles_path
        return shape

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        pen = self.pen()
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            painter.setBrush(color)
            painter.drawRect(QRectF(rect.topLeft(), QSizeF(2., 2.)))
            painter.drawRect(QRectF(rect.topRight() - QPointF(2., 0.), QSizeF(2., 2.)))
            painter.drawRect(QRectF(rect.bottomLeft() - QPointF(0., 2.), QSizeF(2., 2.)))
            painter.drawRect(QRectF(rect.bottomRight() - QPointF(2., 2.), QSizeF(2., 2.)))
        else:
            painter.setPen(pen)
            painter.drawEllipse(rect)

    def __str__(self):
        return 'Ellipse'


class TextItem(QGraphicsSimpleTextItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 10, Qt.SolidLine))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        pen = self.pen()
        if self.isSelected():
            pen.setColor(QColor(255, 0, 0))
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setFont(self.font())
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.text())

    def __str__(self):
        return 'Text'
