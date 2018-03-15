#!/usr/bin/env python

from PyQt5.QtCore import (QLineF, QPointF, QRectF, Qt, pyqtSignal,
                          QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt)
from PyQt5.QtGui import (QPainter, QPainterPath, QPen, QSurfaceFormat, QCursor)
from PyQt5.QtWidgets import (QGraphicsItem,
                             QGraphicsEllipseItem, QGraphicsPathItem,
                             QGraphicsScene, QGraphicsView,
                             QRubberBand, QStyle, QOpenGLWidget,
                             QFormLayout, QSizePolicy, QMenu, QTableView, QAction)

from ...config import RADIUS, NODE_BORDER_WIDTH, FONT_SIZE


class Edge(QGraphicsPathItem):

    Type = QGraphicsItem.UserType + 2

    def __init__(self, index, source_node, dest_node, weight=1, width=1):
        super().__init__()
        
        self.__is_self_loop = False

        self.index = index
        self.source_point = QPointF()
        self.dest_point = QPointF()
        self.weight = weight
        
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self._source = source_node
        self._dest = dest_node
        self._source.addEdge(self)
        self._dest.addEdge(self)
        
        self.setColor(Qt.darkGray)
        self.setWidth(width)
        self.adjust()
        
        self.setFlag(QGraphicsItem.ItemIsSelectable)

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

        if length > 2*RADIUS+NODE_BORDER_WIDTH:
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
            path.moveTo(self.source_point.x()-RADIUS-NODE_BORDER_WIDTH*2,
                        self.source_point.y())
            path.cubicTo(QPointF(self.source_point.x()-4*RADIUS,
                                 self.source_point.y()),
                         QPointF(self.source_point.x(),
                                 self.source_point.y()-4*RADIUS),
                         QPointF(self.dest_point.x(),
                                 self.dest_point.y()-RADIUS-NODE_BORDER_WIDTH*2))
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
            brect = QRectF(brect.x()+2*RADIUS-NODE_BORDER_WIDTH*2-w,
                           brect.y()+2*RADIUS-NODE_BORDER_WIDTH*2-w,
                           2*(RADIUS+NODE_BORDER_WIDTH+1+w),
                           2*(RADIUS+NODE_BORDER_WIDTH+1+w))
        return brect

        
class Node(QGraphicsEllipseItem):

    Type = QGraphicsItem.UserType + 1

    def __init__(self, index, label=''):
        super().__init__(-RADIUS, -RADIUS, 2*RADIUS, 2*RADIUS)

        self._edge_list = []
        self._pie = []
        
        self.index = index
        self.label = label
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        
        self.setColor(Qt.lightGray)
        self.setPen(QPen(Qt.black, NODE_BORDER_WIDTH))
    
    def setLabel(self, label):
        self.label = label
        self.update()

    def setColor(self, color):
        self._color = color
        
    def setPie(self, values):
        self._pie = values
        self.setCacheMode(self.cacheMode())  # Force redraw
        
    def addEdge(self, edge):
        self._edge_list.append(edge)
        edge.adjust()

    def edges(self):
        return self._edge_list

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self._edge_list:
                edge.adjust()
        elif change == QGraphicsItem.ItemSelectedChange:
            self.setZValue(not self.isSelected()) # Bring item to front
            self.setCacheMode(self.cacheMode()) # Force redraw
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
        if self.spanAngle() != 0  and abs(self.spanAngle()) % (360 * 16) == 0:
            painter.drawEllipse(self.rect())
        else:
            painter.drawPie(self.rect(), self.startAngle(), self.spanAngle())
        
        # Get level of detail
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Draw pies if any
        if lod > 0.1 and len(self._pie) > 0:
            rect = QRectF(-0.85*RADIUS, -0.85*RADIUS, 1.7*RADIUS, 1.7*RADIUS)
            start = 0.
            for i, v in enumerate(self._pie):
                painter.setPen(QPen(Qt.NoPen))
                painter.setBrush(get_color(i))
                painter.drawPie(rect, start*5760, v*5760)
                start += v
                
        # Draw text
        if lod > 0.4:
            # font = painter.font()
            # fm = painter.fontMetrics()
            # factor = self.rect().width() / fm.width(self.label)
            # font.setPointSize(font.pointSizeF()*factor)
            font = painter.font()
            font.setPixelSize(FONT_SIZE)
            painter.setFont(font)
            painter.setPen(QPen(Qt.black, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, self.label)

            
class MiniMapGraphicsView(QGraphicsView):

    def __init__(self, parent):
        super().__init__(parent)
        
        self._drag_start_pos = None
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(200, 200)
        self.viewport().setFixedSize(self.contentsRect().size())
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setFocusProxy(parent)
        
        self.band = QRubberBand(QRubberBand.Rectangle, self)
        self.band.hide()
        
    def centerOn(self, pos):
        if self.band.isVisible():
            self.parent().centerOn(self.mapToScene(pos))
            rect = self.band.geometry()
            rect.moveCenter(pos)
            self.band.setGeometry(rect)
        
    def mousePressEvent(self, event):
        if self.band.isVisible() and event.button() == Qt.LeftButton:
            rect = self.band.geometry()
            if event.pos() in rect:
                self._drag_start_pos = event.pos()
            else:
                self.centerOn(event.pos())
    
    def mouseMoveEvent(self, event):
        if self.band.isVisible() and event.buttons() == Qt.MouseButtons(Qt.LeftButton) and self._drag_start_pos is not None:
            self.centerOn(event.pos())
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.band.isVisible():
            self.viewport().unsetCursor()
            self._drag_start_pos = None
    
    def adjustRubberband(self):
        if not self.parent().items():
            self.band.hide()
        else:
            rect = self.parent().mapToScene(self.parent().rect()).boundingRect()
            if not rect.contains(self.scene().sceneRect()):
                rect = self.mapFromScene(rect).boundingRect()
                self.band.setGeometry(rect)
                self.band.show()
            else:
                self.band.hide()
        
    def zoomToFit(self):
        self.fitInView(self.scene().sceneRect().adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)


class NetworkView(QGraphicsView):

    showSpectrumTriggered = pyqtSignal(Node)
    compareSpectrumTriggered = pyqtSignal(Node)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._minimum_zoom = 0
        
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        self.setViewport(QOpenGLWidget())
        self.viewport().setFormat(fmt)

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setFormAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.minimap = MiniMapGraphicsView(self)
        layout.addWidget(self.minimap)
        self.setLayout(layout)
        
        scene = QGraphicsScene(self)
        self.setScene(scene)        
        
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMinimumSize(640, 480)
        self.setStyleSheet(
            """NetworkView:focus {
                border: 3px solid palette(highlight);
            }""")
        
    def setScene(self, scene):
        super().setScene(scene)
        self.minimap.setScene(scene)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        pos = self.mapToScene(event.pos()).toPoint()
        item = self.scene().itemAt(pos, self.transform())
        if item is not None and isinstance(item, Node):
            action = menu.addAction('Show spectrum')
            action.triggered.connect(lambda: self.showSpectrumTriggered.emit(item))
            action = menu.addAction('Set as compare spectrum')
            action.triggered.connect(lambda: self.compareSpectrumTriggered.emit(item))

        if len(menu.actions()) > 0:
            menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        pos = self.mapToScene(event.pos()).toPoint()
        item = self.scene().itemAt(pos, self.transform())
        if item is not None and isinstance(item, Node):
            self.showSpectrumTriggered.emit(item)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.itemAt(event.pos()):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        elif event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setRubberBandSelectionMode(Qt.ContainsItemShape)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().unsetCursor()
        elif event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
            
    def mouseMoveEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.minimap.adjustRubberband()
            
        super().mouseMoveEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.minimap.adjustRubberband()
        
    def translate(self, x, y):
        super().translate(x, y)
        self.minimap.adjustRubberband()
        
    def scale(self, factor_x, factor_y):
        super().scale(factor_x, factor_y)
        self.minimap.adjustRubberband()
                
    def zoomToFit(self):
        self.fitInView(self.scene().sceneRect().adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)
        self._minimum_zoom = self.transform().m11()  # Set zoom out limit to horizontal scaling factor
        self.minimap.adjustRubberband()
        
    def wheelEvent(self, event):
        self.scaleView(2**(event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()

        if factor < self._minimum_zoom or factor > 2:
            return

        self.scale(scaleFactor, scaleFactor)


class GraphTableModel(QAbstractTableModel):
    NodesModelType = 0
    EdgesModelType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attributes = None

    def rowCount(self, parent=QModelIndex()):
        if self._type == GraphTableModel.EdgesModelType:
            return self.parent().graph.ecount()
        else:
            return self.parent().graph.vcount()
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.attributes)
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        column = index.column()
        row = index.row()
        if column > self.columnCount() or row > self.rowCount():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            if self._type == GraphTableModel.EdgesModelType:
                return self.parent().graph.es[self.attributes[column]][row]
            else:
                return self.parent().graph.vs[self.attributes[column]][row]
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.attributes[section]
        else:
            return super().headerData(section, orientation, role)

    def beginResetModel(self):
        self._attributes = None
        super().beginResetModel()

    @property
    def attributes(self):
        if self._attributes is None:
            if self._type == GraphTableModel.EdgesModelType:
                self._attributes = [x for x in self.parent().graph.es.attributes() if not x.startswith('__')]
            else:
                self._attributes = [x for x in self.parent().graph.vs.attributes() if not x.startswith('__')]
        return self._attributes
            
            
class NodesModel(GraphTableModel):
    _type = GraphTableModel.NodesModelType
    
    
class EdgesModel(GraphTableModel):
    _type = GraphTableModel.EdgesModelType
        
        
class ProxyModel(QSortFilterProxyModel):

        def __init__(self, parent=None):
            super().__init__(parent)
            
            # self._filter = None
            self._selection = None
            
        def filterAcceptsRow(self, source_row, source_parent):
            if self._selection is not None:
                index = self.sourceModel().index(source_row, 0)
                # idx = self.sourceModel().data(index, IndexRole)
                if index.row() in self._selection:
                    return True
                return False
            
            return super().filterAcceptsRow(source_row, source_parent)
            
        def setSelection(self, idx):
            """Display only selected items from the scene"""

            if len(idx) == 0:
                self._selection = None
            else:
                self._selection = idx
            self.invalidateFilter()

class NodeTableView(QTableView):
    """ TableView to display Nodes information """
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
            
    def displayColumnInfo(self, column_index):
        model = self.model()
        print (column_index)

    """def contextMenuEvent(self, event):
        menu = QMenu(self)
        selectAction = QAction("Show in graphs", self)
        menu.addAction(selectAction)
        menu.popup(QCursor.pos())
        print(self.columnAt(QCursor.pos().x()))"""
