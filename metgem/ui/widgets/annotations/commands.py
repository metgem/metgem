from typing import Union

from PySide6.QtCore import QLineF, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QUndoCommand
from metgem.ui.widgets.annotations.annotations import ArrowItem, TextItem


class AddCommand(QUndoCommand):

    def __init__(self, item: QGraphicsItem, scene: QGraphicsScene, parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.scene = scene
        scene.update()
        self.setText(f"Add {str(item)}")

    def undo(self):
        self.scene.removeItem(self.item)
        self.scene.update()

    def redo(self):
        self.item.setParentItem(self.scene.annotationsLayer)
        self.scene.clearSelection()
        self.scene.update()


class DeleteCommand(QUndoCommand):

    def __init__(self, item: QGraphicsItem, scene: QGraphicsScene, parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.scene = scene
        scene.update()
        self.setText(f"Remove {str(item)}")

    def undo(self):
        self.scene.addItem(self.item)
        self.scene.clearSelection()
        self.scene.update()

    def redo(self):
        self.scene.removeItem(self.item)
        self.scene.update()


class MoveCommand(QUndoCommand):

    def __init__(self, item: QGraphicsItem, old_pos: QPointF, scene: QGraphicsScene, parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = item.pos()
        self.scene = scene
        scene.update()
        self.setText(f"Move {str(item)}")

    def undo(self):
        self.item.setPos(self.old_pos)

    def redo(self):
        self.item.setPos(self.new_pos)

    def mergeWith(self, command: QUndoCommand) -> bool:
        return self.item == command.item


class ResizeCommand(QUndoCommand):

    def __init__(self, item: QGraphicsItem, old_pos: QPointF, old_line_or_rect: Union[QLineF, QRectF],
                 scene: QGraphicsScene, parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.old_pos = old_pos
        self.old_line_or_rect = old_line_or_rect
        self.new_pos = item.pos()
        self.new_line_or_rect = item.rect() if isinstance(old_line_or_rect, QRectF) else item.line()
        self.scene = scene
        scene.update()
        self.setText(f"Resize {str(item)}")

    def undo(self):
        self.item.setPos(self.old_pos)
        if isinstance(self.old_line_or_rect, QRectF):
            self.item.setRect(self.old_line_or_rect)
        else:
            self.item.setLine(self.old_line_or_rect)

    def redo(self):
        self.item.setPos(self.new_pos)
        if isinstance(self.new_line_or_rect, QRectF):
            self.item.setRect(self.new_line_or_rect)
        else:
            self.item.setLine(self.new_line_or_rect)

    def mergeWith(self, command: QUndoCommand) -> bool:
        return self.item == command.item


class EditArrowCommand(QUndoCommand):

    def __init__(self, item: ArrowItem, old_tail: bool, old_head: bool, scene: QGraphicsScene,
                 parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.old_tail = old_tail
        self.new_tail = item.hasTail()
        self.old_head = old_head
        self.new_head = item.hasHead()
        self.scene = scene
        scene.update()
        self.setText(f"Edit {str(item)}")

    def undo(self):
        self.item.setTail(self.old_tail)
        self.item.setHead(self.old_head)

    def redo(self):
        self.item.setTail(self.new_tail)
        self.item.setHead(self.new_head)


class EditTextCommand(QUndoCommand):

    def __init__(self, item: TextItem, old_text: str, old_font_size: int,
                 scene: QGraphicsScene, parent: QUndoCommand = None):
        super().__init__(parent)
        self.item = item
        self.old_text = old_text
        self.new_text = item.text()
        self.old_font_size = old_font_size
        self.new_font_size = item.font().pointSize()
        self.scene = scene
        scene.update()
        self.setText(f"Edit {str(item)}")

    def undo(self):
        self.item.setText(self.old_text)
        font = self.item.font()
        font.setPointSize(self.old_font_size)
        self.item.setFont(font)

    def redo(self):
        self.item.setText(self.new_text)
        font = self.item.font()
        font.setPointSize(self.new_font_size)
        self.item.setFont(font)

    def mergeWith(self, command: QUndoCommand) -> bool:
        return self.item == command.item