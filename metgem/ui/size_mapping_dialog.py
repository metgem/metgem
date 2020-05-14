import os
import weakref
from typing import Any, Optional, Union

import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QAbstractTableModel, pyqtSignal, QVariant, QObject, QSize, \
    QModelIndex
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QShowEvent, QBrush, QColor
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsPathItem, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem,
                             QWidget, QStyle, QListWidgetItem, QMessageBox)
from scipy.interpolate import interp1d

UI_FILE = os.path.join(os.path.dirname(__file__), 'size_mapping_dialog.ui')

SizeMappingDialogUI, SizeMappingDialogBase = uic.loadUiType(UI_FILE,
                                                            from_imports='metgem.ui',
                                                            import_from='metgem.ui')

ColumnRole = Qt.UserRole + 1

MODE_LINEAR = 0
MODE_LOG = 1


class IterInstances:
    """"Metaclass to keep track of instances of a class"""

    def __new__(cls, name, bases, dct):
        dct['_instances'] = set()
        return super().__new__(cls, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        cls._instances.add(weakref.ref(instance))
        return instance

    def __iter__(cls):
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead


class IterPyQtWrapperInstances(IterInstances, type(QObject)):
    """"Metaclass to keep track of instances of a QObject class"""

    pass


class Link(QGraphicsPathItem):
    def __init__(self, handle1, handle2, width):
        super().__init__()

        self._width = width
        self.setPen(QPen(Qt.black, width))

        self._handle1 = handle1
        handle1.setRightLink(self)
        self._handle2 = handle2
        handle2.setLeftLink(self)
        self.adjust()

    def width(self):
        return self._width

    def handle1(self) -> 'Handle':
        return self._handle1

    def setHandle1(self, handle: 'Handle'):
        self._handle1 = handle
        handle.setRightLink(self)
        self.adjust()

    def handle2(self) -> 'Handle':
        return self._handle2

    def setHandle2(self, handle: 'Handle'):
        self._handle2 = handle
        handle.setLeftLink(self)
        self.adjust()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene():
            event.accept()
            self.scene().addHandle(event.pos(), link=self)
        else:
            super().mouseDoubleClickEvent(event)

    def adjust(self):
        if not self._handle1 or not self._handle2:
            return

        line = QLineF(self.mapFromItem(self._handle1, 0, 0),
                      self.mapFromItem(self._handle2, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > self.width() * 0.9:
            offset = QPointF((line.dx() * self.width() / 2) / length,
                             (line.dy() * self.width() / 2) / length)
            p1 = line.p1() + offset
            p2 = line.p2() - offset
        else:
            p1 = p2 = line.p1()

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        self.setPath(path)


class Handle(QGraphicsEllipseItem, metaclass=IterPyQtWrapperInstances):

    def __init__(self, size, llink: Link=None, rlink: Link=None,
                 brush: Union[QBrush, QColor, Qt.GlobalColor]=Qt.white,
                 movable=True):
        super().__init__(QRectF(-size / 2, -size / 2, size, size))

        self._movable = movable

        self.setPen(QPen(Qt.black, size / 10))
        if brush:
            self.setBrush(brush)
        self.setZValue(1)

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemSendsGeometryChanges)

        self._llink = llink
        self._rlink = rlink

    def size(self):
        return self.rect().width()

    def leftLink(self) -> Link:
        return self._llink

    def setLeftLink(self, link: Link):
        self._llink = link

    def rightLink(self) -> Link:
        return self._rlink

    def setRightLink(self, link: Link):
        self._rlink = link

    def setSelected(self, selected: bool):
        if selected:  # Allow only one handle to be selected at a time
            for obj in Handle:
                if obj != self:
                    obj.setSelected(False)
        super().setSelected(selected)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            rect = self.scene().drawAreaRect()
            if self._rlink and value.x() > self._rlink.handle2().x():
                value.setX(self._rlink.handle2().x())
            elif self._llink and value.x() < self._llink.handle1().x():
                value.setX(self._llink.handle1().x())

            if not rect.contains(value):
                value.setX(min(rect.right(), max(value.x(), rect.left())))
                value.setY(min(rect.bottom(), max(value.y(), rect.top())))

            return value
        elif change == QGraphicsItem.ItemPositionHasChanged:
            for link in (self._llink, self._rlink):
                if link:
                    link.adjust()
            if self.isSelected() and self.scene():
                self.scene().handleMoved.emit(self)

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene():
            event.accept()
            self.scene().removeHandle(self)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...):
        painter.setBrush(self.brush())

        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(self.pen().color(), self.pen().width()*3))
        else:
            painter.setPen(self.pen())

        painter.drawEllipse(self.rect())


class Scene(QGraphicsScene):
    handleMoved = pyqtSignal(Handle)
    handleSelectionChanged = pyqtSignal(QVariant)  # Handle or None

    DATA_VALUE = 0
    DATA_SIZE = 1

    def __init__(self, *args, handle_size: int=10, **kwargs):
        super().__init__(*args, **kwargs)

        self._xlabel = self.addText('Nodes Size')
        self._xlabel.setRotation(270)
        self._ylabel = self.addText('Values')
        self._area = self.addRect(self.sceneRect())
        self._tooltip = self.addText('')

        self._handle1 = Handle(handle_size, brush=Qt.red)
        self.addItem(self._handle1)
        self._handle2 = Handle(handle_size, brush=Qt.blue)
        self.addItem(self._handle2)
        link = Link(self._handle1, self._handle2, handle_size / 5)
        self.addItem(link)

        self.selectionChanged.connect(self.on_selection_changed)

    def linkAt(self, x: int):
        for item in self.items():
            if isinstance(item, Link):
                if item.handle1().pos().x() <= x <= item.handle2().pos().x():
                    return item
        return

    def selectedHandle(self):
        for item in self.selectedItems():
            if isinstance(item, Handle):
                return item
        return

    def addHandle(self, pos: QPointF=None, link: Link=None):
        if link is None and pos is not None:
            link = self.linkAt(pos.x())

        if link is not None:
            handle = Handle(link.handle1().size())
            rlink = Link(handle, link.handle2(), link.width())
            link.setHandle2(handle)
            self.addItem(handle)
            self.addItem(rlink)
            handle.setPos(pos)
            handle.setSelected(True)

    def removeHandle(self, handle: Handle):
        if handle and handle != self._handle1 and handle != self._handle2:
            if handle.leftLink() and handle.rightLink():
                handle.leftLink().setHandle2(handle.rightLink().handle2())
                self.removeItem(handle.rightLink())
            self.removeItem(handle)

    def on_selection_changed(self):
        self.handleSelectionChanged.emit(self.selectedHandle())

    def xlabel(self):
        return self._xlabel

    def ylabel(self):
        return self._ylabel

    def drawAreaRect(self):
        return self._area.rect()

    def setUpperText(self, text: str):
        self._tooltip.setPlainText(text)
        self._tooltip.setPos(self._area.rect().left(), self._area.rect().top() - self._tooltip.boundingRect().height())

    def adjust(self):
        sr = self.sceneRect()
        xr = self._xlabel.boundingRect()
        yr = self._ylabel.boundingRect()
        dr = sr.adjusted(xr.height(), yr.height(), -xr.height(), -yr.height())

        self._xlabel.setPos(0, sr.height() / 2 + xr.width() / 2)
        self._ylabel.setPos(sr.width() / 2 - yr.width() / 2, sr.height() - yr.height())
        self._area.setRect(dr)
        self._handle1.setPos(dr.bottomLeft())
        self._handle1.setFlag(QGraphicsItem.ItemIsMovable, False)
        self._handle2.setPos(dr.topRight())
        self._handle2.setFlag(QGraphicsItem.ItemIsMovable, False)

    def customHandles(self):
        for item in self.items():
            if isinstance(item, Handle) and item != self._handle1 and item != self._handle2:
                yield item

    def removeAllHandles(self):
        for item in self.items():
            if isinstance(item, Handle) and item != self._handle1 and item != self._handle2:
                self.removeHandle(item)


class ColumnListWidgetItem(QListWidgetItem):
    def __init__(self, *args, column: int=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizeHint(QSize(self.sizeHint().width(), 32))
        self.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.setData(ColumnRole, column)

    def __lt__(self, other):
        scol = self.data(ColumnRole)
        ocol = other.data(ColumnRole)
        if scol is not None and ocol is not None:
            return scol < ocol
        return super().__lt__(other)


class SizeMappingDialog(SizeMappingDialogUI, SizeMappingDialogBase):

    def __init__(self, model: QAbstractTableModel, column_id: int, func: 'SizeMappingFunc' = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._model = model
        self._first_show = True
        self._column_id = column_id
        self._func = func

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(self.geometry().size())

        self.spinMaxValue.valueChanged.connect(lambda x: self.on_range_changed('max-value', x))
        self.spinMinValue.valueChanged.connect(lambda x: self.on_range_changed('min-value', x))
        self.spinMaxSize.valueChanged.connect(lambda x: self.on_range_changed('max-size', x))
        self.spinMinSize.valueChanged.connect(lambda x: self.on_range_changed('min-size', x))
        self.btAddHandle.clicked.connect(self.on_add_handle)
        self.btRemoveHandle.clicked.connect(self.on_remove_handle)

        self.gvMapping.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.gvMapping.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gvMapping.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scene = Scene(QRectF(0, 0, self.gvMapping.minimumWidth(), self.gvMapping.minimumHeight()),
                      handle_size=self.gvMapping.minimumWidth() / 30)
        self.gvMapping.setScene(scene)

        self.cbMode.addItems(["Linear", "Log"])
        self.cbMode.activated[int].connect(self.on_mode_changed)
        self._current_mode = MODE_LINEAR
        self.cbMode.setCurrentIndex(MODE_LINEAR)

        self.lstColumns.selectionModel().currentChanged.connect(self.on_column_changed)

        for col in range(model.columnCount()):
            text = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            item = ColumnListWidgetItem(text, column=col)
            self.lstColumns.addItem(item)

    def showEvent(self, event: QShowEvent):
        scene = self.gvMapping.scene()
        self.gvMapping.fitInView(scene.sceneRect(), Qt.IgnoreAspectRatio)
        scene.adjust()

        if self._first_show:
            self.setValues(self._column_id, self._func)
            self._first_show = False

        super().showEvent(event)

        scene.handleMoved.connect(self.on_handle_moved)
        scene.handleSelectionChanged.connect(self.on_selection_changed)

    def mapHandlePosToValue(self, pos: QPointF, mode=None):
        dr = self.gvMapping.scene().drawAreaRect()
        xmin = self.spinMinValue.value()
        xmax = self.spinMaxValue.value()
        ymin = self.spinMinSize.value()
        ymax = self.spinMaxSize.value()

        if mode is None:
            mode = self.cbMode.currentIndex()

        if mode == MODE_LOG:
            xmin = np.log10(xmin) if xmin > 0 else 0
            xmax = np.log10(xmax) if xmax > 0 else 0

        x = (pos.x() - dr.left()) / dr.width() * (xmax - xmin) + xmin
        y = (dr.height() - (pos.y() - dr.top())) / dr.height() * (ymax - ymin) + ymin

        if mode == MODE_LOG:
            x = np.power(10, x)

        return QPointF(x, y)

    def mapValueToHandlePos(self, pos: QPointF, mode=None):
        dr = self.gvMapping.scene().drawAreaRect()
        xmin = self.spinMinValue.value()
        xmax = self.spinMaxValue.value()
        ymin = self.spinMinSize.value()
        ymax = self.spinMaxSize.value()

        if mode is None:
            mode = self.cbMode.currentIndex()

        x = pos.x()
        if mode == MODE_LOG:
            x = np.log10(x) if x > 0 else 0
            xmin = np.log10(xmin) if xmin > 0 else 0
            xmax = np.log10(xmax) if xmax > 0 else 0

        x = (x - xmin) / (xmax - xmin) * dr.width() + dr.left()
        y = dr.height() - ((pos.y() - ymin) / (ymax - ymin) * dr.height() - dr.top())

        return QPointF(x, y)

    def all_controls(self):
        return (self.gvMapping, self.spinMinValue, self.spinMaxValue, self.spinMinSize, self.spinMaxSize,
                self.spinHandleValue, self.spinHandleSize, self.btAddHandle, self.cbMode)

    def on_column_changed(self, current: QModelIndex, previous: QModelIndex):
        column_id = current.data(ColumnRole)
        xmin = xmax = self._model.data(self._model.index(0, column_id))
        try:
            for i in range(1, self._model.rowCount()):
                value = self._model.data(self._model.index(i, column_id))
                if value < xmin:
                    xmin = value
                elif value > xmax:
                    xmax = value
            for spin in (self.spinMinValue, self.spinMaxValue):
                spin.setMinimum(xmin)
                spin.setMaximum(xmax)
            self.spinMinValue.setValue(xmin)
            self.spinMaxValue.setValue(xmax)
            self.spinMinSize.setValue(20)
            self.spinMaxSize.setValue(100)
        except TypeError:
            QMessageBox.warning(self, None, "This column does not contains numerical data.")
            for w in self.all_controls():
                w.setEnabled(False)
        else:
            self.gvMapping.scene().removeAllHandles()
            for w in self.all_controls():
                w.setEnabled(True)

    def on_remove_handle(self):
        if self.gvMapping.scene():
            self.gvMapping.scene().removeHandle(self.gvMapping.scene().selectedHandle())

    def on_add_handle(self):
        if self.gvMapping.scene():
            pos = self.mapValueToHandlePos(QPointF(self.spinHandleValue.value(), self.spinHandleSize.value()))
            self.gvMapping.scene().addHandle(pos)

    def on_mode_changed(self, index: int):
        for handle in self.gvMapping.scene().customHandles():
            self.gvMapping.scene().removeItem(handle)
            handle.setPos(self.mapValueToHandlePos(self.mapHandlePosToValue(handle.pos(), mode=self._current_mode),
                                                   mode=index))
            self.gvMapping.scene().addItem(handle)
        self._current_mode = index

    def on_range_changed(self, type_: str, value: Union[float, int]):
        if type_ == 'max-value':
            self.spinMinValue.setMaximum(value)
            self.spinHandleValue.setMaximum(value)
        elif type_ == 'min-value':
            self.spinMaxValue.setMinimum(value)
            self.spinHandleValue.setMinimum(value)
        elif type_ == 'max-size':
            self.spinMinSize.setMaximum(value)
            self.spinHandleSize.setMaximum(value)
        elif type_ == 'min-size':
            self.spinMaxSize.setMinimum(value)
            self.spinHandleSize.setMinimum(value)

        if self.gvMapping.scene():
            self.on_handle_moved(self.gvMapping.scene().selectedHandle())

    def on_handle_moved(self, handle: Handle):
        if handle is not None:
            pos = self.mapHandlePosToValue(handle.pos())
            text = f"({pos.x():.1f},{pos.y():.1f})"
            self.gvMapping.scene().setUpperText(text)
            self.spinHandleValue.setValue(pos.x())
            self.spinHandleSize.setValue(pos.y())

    def on_selection_changed(self, handle: Handle):
        if handle is not None:
            self.on_handle_moved(handle)
        else:
            self.gvMapping.scene().setUpperText('')

        if handle is not None:
            self.btRemoveHandle.setEnabled(True)

            pos = self.mapHandlePosToValue(handle.pos())

            self.spinHandleValue.setMinimum(self.spinMinValue.value())
            self.spinHandleValue.setMaximum(self.spinMaxValue.value())
            self.spinHandleValue.setValue(pos.x())
            self.spinHandleSize.setMinimum(self.spinMinSize.value())
            self.spinHandleSize.setMaximum(self.spinMaxSize.value())
            self.spinHandleSize.setValue(pos.y())
        else:
            self.btRemoveHandle.setEnabled(False)

    def setValues(self, column_id: int, func: 'SizeMappingFunc' = None):
        model = self.lstColumns.model()
        for row in range(model.rowCount()):
            index = model.index(row)
            if index.data(ColumnRole) == column_id:
                self.lstColumns.setCurrentIndex(index)

        if func is not None:
            self.cbMode.setCurrentIndex(func.get('mode', MODE_LINEAR))
            self.spinMinSize.setValue(func.get('ymin', 0))
            self.spinMaxSize.setValue(func.get('ymax', 10))

            scene = self.gvMapping.scene()
            xs = func.get('xs', [0, 0])
            ys = func.get('ys', [0, 0])
            for x, y in zip(xs[:-2], ys[:-2]):
                pos = self.mapValueToHandlePos(QPointF(x, y))
                scene.addHandle(pos)
            scene.clearSelection()

    def getValues(self):
        ymin = self.spinMinSize.value()
        ymax = self.spinMaxSize.value()
        scene = self.gvMapping.scene()

        id_ = self.lstColumns.currentIndex().row()

        xs = []
        ys = []
        for item in scene.items():
            if isinstance(item, Handle):
                pos = self.mapHandlePosToValue(item.pos())
                xs.append(pos.x())
                ys.append(pos.y())

        return id_, SizeMappingFunc(xs, ys, ymin, ymax, mode=self.cbMode.currentIndex())


class SizeMappingFunc(dict):

    def __init__(self, xs, ys, ymin, ymax, mode=MODE_LINEAR):
        if mode == MODE_LOG:
            xsarr = np.array(xs)
            with np.errstate(divide='ignore'):
                xsarr = np.log10(xs)
            xsarr[np.isneginf(xsarr)] = 0
            f = interp1d(xsarr, ys, bounds_error=False, fill_value=(ymin, ymax), copy=False)

            def f2(x):
                return f(np.log10(x)) if x > 0 else ymin

            self._func = f2
        else:
            self._func = interp1d(xs, ys, bounds_error=False, fill_value=(ymin, ymax), copy=False)

        # Store values as items in a subclassed dict instead of attributes of the class to allow serialization (json)
        self.__setitem__('xs', xs)
        self.__setitem__('ys', ys)
        self.__setitem__('ymin', ymin)
        self.__setitem__('ymax', ymax)
        self.__setitem__('mode', mode)

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
