import math
from typing import Optional

from qtpy.QtCore import Qt, QRectF, QPointF, QSizeF
from qtpy.QtGui import (QPainterPath, QPainterPathStroker, QPainter,
                         QBrush, QColor, QPolygonF, QPen)
from qtpy.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsSimpleTextItem,
                             QGraphicsItem, QGraphicsEllipseItem, QStyleOptionGraphicsItem, QWidget)


class ArrowItem(QGraphicsLineItem):

    def __init__(self, *args, has_head=True, has_tail=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 10, Qt.SolidLine))
        self._has_head = has_head
        self._has_tail = has_tail
        self._arrow_head = QPolygonF()
        self._arrow_tail = QPolygonF()

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
        path.addPolygon(self._arrow_head)
        path.addPolygon(self._arrow_tail)
        stroker.setWidth(self.pen().width())
        return stroker.createStroke(path)

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        pen = self.pen()
        brush = QBrush()
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen.setColor(color)
        else:
            color = pen.color()

        painter.setPen(pen)
        brush.setColor(color)
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawLine(self.line())

        angle = self.getAngle()
        if self.line().dy() >= 0.:
            angle += math.pi
        size = self.pen().width() * 2.5

        if self._has_tail or self._has_head:
            painter.setPen(QPen(color, self.pen().width(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        if self._has_tail:
            a = angle + math.pi + math.pi * .1
            b = angle + math.pi - math.pi * .1
            p0 = self.line().p1() + QPointF(math.sin(angle) * self.pen().width(),
                                            -math.cos(angle) * self.pen().width())
            p1 = p0 + QPointF(math.sin(a) * size, -math.cos(a) * size)
            p2 = p0 + QPointF(math.sin(b) * size, -math.cos(b) * size)
            self._arrow_tail.clear()
            self._arrow_tail.append(p0)
            self._arrow_tail.append(p1)
            self._arrow_tail.append(p2)
            painter.drawPolygon(self._arrow_tail)

        if self._has_head:
            a = angle + math.pi * .1
            b = angle - math.pi * .1
            p0 = self.line().p2() - QPointF(math.sin(angle) * self.pen().width(),
                                            -math.cos(angle) * self.pen().width())
            p1 = p0 + QPointF(math.sin(a) * size, -math.cos(a) * size)
            p2 = p0 + QPointF(math.sin(b) * size, -math.cos(b) * size)
            self._arrow_head.clear()
            self._arrow_head.append(p0)
            self._arrow_head.append(p1)
            self._arrow_head.append(p2)
            painter.drawPolygon(self._arrow_head)

    def __str__(self):
        return 'Arrow' if self.hasHead() or self.hasTail() else 'Line'


class RectItem(QGraphicsRectItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 100, Qt.SolidLine))
        self.setBrush(Qt.transparent)

    def shape(self) -> QPainterPath:
        rect = self.rect()
        path = QPainterPath()
        stroker = QPainterPathStroker()
        path.addRect(rect)
        stroker.setWidth(self.pen().width())
        shape = stroker.createStroke(path)
        return shape

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen = self.pen()
            pen.setColor(color)
            painter.setPen(pen)
        else:
            painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())

    def __str__(self):
        return 'Rectangle'


class EllipseItem(QGraphicsEllipseItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setPen(QPen(Qt.black, 10, Qt.SolidLine))
        self.setBrush(Qt.transparent)

    def shape(self) -> QPainterPath:
        rect = self.rect()
        path = QPainterPath()
        stroker = QPainterPathStroker()
        path.addEllipse(rect)
        stroker.setWidth(self.pen().width())
        if self.isSelected():
            path.addRect(QRectF(rect.topLeft(), QSizeF(5., 5.)))
            path.addRect(QRectF(rect.topRight() - QPointF(5., 0.), QSizeF(5., 5.)))
            path.addRect(QRectF(rect.bottomLeft() - QPointF(0., 5.), QSizeF(5., 5.)))
            path.addRect(QRectF(rect.bottomRight() - QPointF(5., 5.), QSizeF(5., 5.)))
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        pen = self.pen()
        if self.isSelected():
            color = QColor(255, 0, 0)
            pen.setColor(color)
            painter.setPen(pen)
            painter.setBrush(self.brush())
            painter.drawEllipse(rect)
            painter.setBrush(color)
            painter.drawRect(QRectF(rect.topLeft(), QSizeF(5., 5.)))
            painter.drawRect(QRectF(rect.topRight() - QPointF(5., 0.), QSizeF(5., 5.)))
            painter.drawRect(QRectF(rect.bottomLeft() - QPointF(0., 5.), QSizeF(5., 5.)))
            painter.drawRect(QRectF(rect.bottomRight() - QPointF(5., 5.), QSizeF(5., 5.)))
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

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        pen = self.pen()
        if self.isSelected():
            pen.setColor(QColor(255, 0, 0))
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setFont(self.font())
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.text())

    def __str__(self):
        return f'Text <{self.text()}>'
