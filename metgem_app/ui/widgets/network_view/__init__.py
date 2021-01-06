import struct
from typing import Union

from PyQt5.QtCore import Qt, QLineF, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QFont, QMouseEvent, QIcon
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsLineItem, QGraphicsSceneMouseEvent, QLineEdit,
                             QGraphicsEllipseItem, QDialog, QFormLayout, QSpinBox, QDialogButtonBox,
                             QUndoStack, QUndoView, QMenu, QWidgetAction, QGraphicsScene)
from PyQtNetworkView import NetworkView as BaseNetworkView
from PyQtNetworkView.graphicsitem import GraphicsItemLayer

from .commands import AddCommand, DeleteCommand, EditTextCommand, EditArrowCommand, MoveCommand, ResizeCommand
from .annotations import ArrowItem, RectItem, TextItem, EllipseItem

MODE_LINE = 0
MODE_RECT = 1
MODE_TEXT = 2
MODE_ELLIPSE = 3
MODE_ARROW = 4


class TextItemInputDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Add/Edit Text Item")

        layout = QFormLayout()
        self.leText = QLineEdit()
        layout.addRow("Text", self.leText)
        self.spinFontSize = QSpinBox()
        self.spinFontSize.setMinimum(8)
        self.spinFontSize.setMaximum(5096)
        self.spinFontSize.setValue(18)
        layout.addRow("Font Size", self.spinFontSize)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def getValues(self):
        return self.leText.text(), self.spinFontSize.value()

    def setValues(self, text, font_size):
        self.leText.setText(text)
        self.spinFontSize.setValue(font_size)


class NetworkView(BaseNetworkView):
    annotationAdded = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._undo_stack = QUndoStack(self)
        self._undo_view = QUndoView(self._undo_stack)
        self._undo_view.setCleanIcon(QIcon(":/icons/images/document-save.svg"))
        self._undo_menu = QMenu(self)
        action = QWidgetAction(self._undo_menu)
        action.setDefaultWidget(self._undo_view)
        self._undo_menu.addAction(action)

        self._orig_point = None
        self._item_to_draw = None
        self._item_old_pos = None
        self._item_old_line_or_rect = None
        self._mode = None
        self._dialog = None
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def setScene(self, scene: QGraphicsScene):
        super().setScene(scene)
        self.clearAnnotations()

    def setDrawMode(self, mode):
        self._mode = mode
        if mode is None:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self._orig_point = None
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    def mode(self):
        return self._mode

    def undoView(self):
        return self._undo_view

    def undoStack(self):
        return self._undo_stack

    def undoMenu(self):
        return self._undo_menu

    def deleteSelectedAnnotations(self):
        scene = self.scene()
        for item in scene.annotationsLayer.childItems():
            if item.isSelected():
                self._undo_stack.push(DeleteCommand(item, scene))

    def clearAnnotations(self):
        scene = self.scene()

        if hasattr(scene, 'annotationsLayer'):
            scene.removeItem(scene.annotationsLayer)

        scene.annotationsLayer = GraphicsItemLayer()
        scene.addItem(scene.annotationsLayer)
        scene.annotationsLayer.setZValue(-1)
        self._undo_stack.clear()

    def loadAnnotations(self, buffer: bytes) -> None:
        if not buffer:
            return

        scene = self.scene()
        if not scene:
            return

        def read(len):
            nonlocal buffer, pos
            data = buffer[pos:pos+len]
            pos += len
            return data

        pos = 0
        data = read(1)

        while data:
            if data in (b'L', b'A'):
                x1, y1, x2, y2 = struct.unpack("ffff", read(16))
                line = QLineF(0., 0., x2, y2)
                if data == b'L':
                    self.addLineItem(line, QPointF(x1, y1))
                elif data == b'A':
                    data, = struct.unpack("B", read(1))
                    has_head = (data >> 0) & 1
                    has_tail = (data >> 1) & 1
                    self.addArrowItem(line, QPointF(x1, y1), has_head, has_tail)
            elif data in (b'R', b'C'):
                x, y, w, h = struct.unpack("ffff", read(16))
                rect = QRectF(0., 0., w, h)
                if data == b'R':
                    self.addRectItem(rect, QPointF(x, y))
                elif data == b'C':
                    self.addEllipseItem(rect, QPointF(x, y))
            elif data == b'T':
                x, y, len = struct.unpack("ffH", read(10))
                text = read(len).decode()
                font_size, = struct.unpack("H", read(2))
                font = QFont()
                font.setPointSize(font_size)
                self.addTextItem(text, font, QPointF(x, y))

            data = read(1)

        self._undo_stack.setClean()

    def saveAnnotations(self) -> bytes:
        scene = self.scene()
        if not scene:
            return b''

        buffer = b''
        for item in scene.items():
            if isinstance(item, ArrowItem):
                char = b'A' if item.hasHead() or item.hasTail() else b'L'
                line = item.line()
                pos = item.pos()
                buffer += char
                buffer += struct.pack("ffff", pos.x(), pos.y(),
                                      line.x2(), line.y2())
                if char == b'A':
                    buffer += struct.pack("B", item.hasHead() + item.hasTail() * 2)
            elif isinstance(item, (RectItem, EllipseItem)):
                char = b'R' if isinstance(item, RectItem) else b'C'
                rect = item.rect()
                pos = item.pos()
                buffer += char
                buffer += struct.pack("ffff", pos.x(), pos.y(),
                                      rect.width(), rect.height())
            elif isinstance(item, TextItem):
                pos = item.pos()
                text = item.text()
                font = item.font()
                buffer += b'T'
                buffer += struct.pack("ff", pos.x(), pos.y())
                buffer += struct.pack("H", len(text))
                buffer += str.encode(text)
                buffer += struct.pack("H", font.pointSize())

        return buffer

    def addLineItem(self, line: QLineF, pos: QPointF) -> Union[ArrowItem, None]:
        return self.addArrowItem(line, pos, False, False)

    def addArrowItem(self, line: QLineF, pos: QPointF, has_head=True, has_tail=False) -> Union[ArrowItem, None]:
        scene = self.scene()
        if not scene:
            return

        item = ArrowItem(line, has_head=has_head, has_tail=has_tail)
        self._undo_stack.push(AddCommand(item, scene))
        item.setPos(pos)
        self.annotationAdded.emit()
        return item

    def addRectItem(self, rect: QRectF, pos: QPointF) -> Union[RectItem, None]:
        scene = self.scene()
        if not scene:
            return

        item = RectItem(rect)
        self._undo_stack.push(AddCommand(item, scene))
        item.setPos(pos)
        self.annotationAdded.emit()
        return item

    def addEllipseItem(self, rect: QRectF, pos: QPointF) -> Union[QGraphicsEllipseItem, None]:
        scene = self.scene()
        if not scene:
            return

        item = EllipseItem(rect)
        self._undo_stack.push(AddCommand(item, scene))
        item.setPos(pos)
        self.annotationAdded.emit()
        return item

    def addTextItem(self, text: str, font: QFont, pos: QPointF) -> Union[TextItem, None]:
        scene = self.scene()
        if not scene:
            return

        item = TextItem(text)
        item.setFont(font)
        self._undo_stack.push(AddCommand(item, scene))
        item.setPos(pos)
        self.annotationAdded.emit()
        return item

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        scene = self.scene()
        if scene and self._mode is None:
            item = self.itemAt(event.pos())

            # Edit text item
            if isinstance(item, TextItem):
                def edit_text_item(result):
                    if result == QDialog.Accepted:
                        old_text = item.text()
                        old_font = item.font()
                        text, font_size = self._dialog.getValues()
                        font = QFont()
                        font.setPointSize(font_size)
                        item.setText(text)
                        item.setFont(font)
                        self._undo_stack.push(EditTextCommand(item, old_text, old_font.pointSize(), self.scene()))

                self._dialog = TextItemInputDialog(self)
                self._dialog.setValues(item.text(), item.font().pointSize())
                self._dialog.finished.connect(edit_text_item)
                self._dialog.open()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        scene = self.scene()
        if scene:
            # Add a text item at mouse position
            if self._mode == MODE_TEXT:
                def add_text_item(result):
                    if result == QDialog.Accepted:
                        text, font_size = self._dialog.getValues()
                        font = QFont()
                        font.setPointSize(font_size)
                        self.addTextItem(text, font, self.mapToScene(event.pos()))

                self._dialog = TextItemInputDialog(self)
                self._dialog.finished.connect(add_text_item)
                self._dialog.open()

            # Define starting point of item (line, rect, ellipse, etc)
            elif self._mode is not None:
                self._orig_point = self.mapToScene(event.pos())

            # Edit item (line, rect, ellipse, etc)
            elif self._mode is None:
                self._item_to_draw = item = self.itemAt(event.pos())
                if item:
                    self._item_old_pos = item.pos()
                    event_pos = self.mapToScene(event.pos()) - item.pos()

                    # Edit Arrows head and tails
                    if isinstance(item, ArrowItem) and event.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier:
                        tol = item.pen().width() * 5.
                        if (event_pos - item.line().p1()).manhattanLength() < tol:
                            has_tail = item.hasTail()
                            item.setTail(not has_tail)
                            self._undo_stack.push(EditArrowCommand(item, has_tail, item.hasHead(), self.scene()))
                        elif (event_pos - item.line().p2()).manhattanLength() < tol:
                            has_head = item.hasHead()
                            item.setHead(not has_head)
                            self._undo_stack.push(EditArrowCommand(item, item.hasTail(), has_head, self.scene()))

                    # Resize Line and Arrow
                    if isinstance(item, ArrowItem):
                        self._item_old_line_or_rect = item.line()
                        if (event_pos - item.line().p1()).manhattanLength() < 10.:
                            self._orig_point = item.line().p2() + item.pos()
                        elif (event_pos - item.line().p2()).manhattanLength() < 10.:
                            self._orig_point = item.line().p1() + item.pos()

                    # Resize Rect and Ellipse
                    elif isinstance(item, (EllipseItem, RectItem)):
                        self._item_old_line_or_rect = item.rect()
                        if (event_pos - item.rect().topLeft()).manhattanLength() < 10.:
                            self._orig_point = item.rect().bottomRight() + item.pos()
                        elif (event_pos - item.rect().bottomRight()).manhattanLength() < 10.:
                            self._orig_point = item.rect().topLeft() + item.pos()
                        elif (event_pos - item.rect().topRight()).manhattanLength() < 10.:
                            self._orig_point = item.rect().bottomLeft() + item.pos()
                        elif (event_pos - item.rect().bottomLeft()).manhattanLength() < 10.:
                            self._orig_point = item.rect().topRight() + item.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        scene = self.scene()
        if scene and self._orig_point is not None:
            # Edit line or arrow
            if self._mode in (MODE_LINE, MODE_ARROW) \
                    or (self._mode is None and isinstance(self._item_to_draw, QGraphicsLineItem)):
                pos = self.mapToScene(event.pos())
                x = pos.x() - self._orig_point.x()
                y = pos.y() - self._orig_point.y()
                if self._item_to_draw and self._orig_point == self._item_to_draw.line().p2() + self._item_to_draw.pos():
                    # Moving line around head
                    line = QLineF(0, 0, -x, -y)
                    point = pos
                else:
                    line = QLineF(0, 0, x, y)
                    point = None

                if self._item_to_draw is None:
                    if self._mode == MODE_LINE:
                        self._item_to_draw = self.addLineItem(line, self._orig_point)
                    elif self._mode == MODE_ARROW:
                        self._item_to_draw = self.addArrowItem(line, self._orig_point)
                else:
                    self._item_to_draw.setLine(line)
                    if point is not None:
                        self._item_to_draw.setPos(point)
                return

            # Edit rect or circle
            elif self._mode in (MODE_RECT, MODE_ELLIPSE) \
                    or (self._mode is None and isinstance(self._item_to_draw, (RectItem, EllipseItem))):
                pos = self.mapToScene(event.pos())
                width = pos.x() - self._orig_point.x()
                height = pos.y() - self._orig_point.y()
                dx = 0 if width >= 0 else width
                dy = 0 if height >= 0 else height
                rect = QRectF(0, 0, abs(width), abs(height))
                point = self._orig_point + QPointF(dx, dy)
                if self._item_to_draw is None:
                    if self._mode == MODE_RECT:
                        self._item_to_draw = self.addRectItem(rect, point)
                    elif self._mode == MODE_ELLIPSE:
                        self._item_to_draw = self.addEllipseItem(rect, point)
                else:
                    self._item_to_draw.setRect(rect)
                    self._item_to_draw.setPos(point)
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._mode is None and self._item_to_draw is not None and event.button() == Qt.LeftButton:
            if isinstance(self._item_old_line_or_rect, QRectF):
                line_or_rect = self._item_to_draw.rect()
            elif isinstance(self._item_old_line_or_rect, QLineF):
                line_or_rect = self._item_to_draw.line()
            else:
                line_or_rect = None

            if line_or_rect is None or self._item_old_line_or_rect == line_or_rect:
                if self._item_old_pos != self._item_to_draw.pos():
                    self._undo_stack.push(MoveCommand(self._item_to_draw, self._item_old_pos, self.scene()))
            else:
                self._undo_stack.push(ResizeCommand(self._item_to_draw, self._item_old_pos,
                                                    self._item_old_line_or_rect, self.scene()))
        self._item_old_pos = None
        self._item_old_line_or_rect = None
        self._item_to_draw = None
        self._orig_point = None
        super().mouseReleaseEvent(event)
