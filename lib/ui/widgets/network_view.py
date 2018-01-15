#!/usr/bin/env python

from PyQt5.QtCore import (QLineF, QPointF, QRectF, Qt,
        QAbstractTableModel, QModelIndex, QSortFilterProxyModel)
from PyQt5.QtGui import (QPainter, QPainterPath, QPen, QSurfaceFormat, QImage)
from PyQt5.QtWidgets import (QApplication, QGraphicsItem,
        QGraphicsEllipseItem, QGraphicsPathItem, QFrame,
        QGraphicsTextItem, QGraphicsScene, QGraphicsView,
        QRubberBand, QStyle, QOpenGLWidget, QStyleOptionGraphicsItem,
        QFormLayout, QSizePolicy)

# IndexRole = Qt.UserRole + 1

RADIUS = 30
NODE_BORDER_WIDTH = 5
FONT_SIZE = 14

class Edge(QGraphicsPathItem):

    Type = QGraphicsItem.UserType + 2

    def __init__(self, index, sourceNode, destNode, weight=1, width=1):
        super().__init__()
        
        self.__is_self_loop = False

        self.index = index
        self.sourcePoint = QPointF()
        self.destPoint = QPointF()
        self.weight = weight
        
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.source = sourceNode
        self.dest = destNode
        self.source.addEdge(self)
        self.dest.addEdge(self)
        
        self.setColor(Qt.darkGray)
        self.setWidth(width)
        self.adjust()
        
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # self.setOpacity(0.3)

    def setColor(self, color):
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)
        
        
    def setWidth(self, width):
        pen = self.pen()
        if self.sourceNode() != self.destNode():
            pen.setWidth(width)
        else:
            pen.setWidth(1)
        self.setPen(pen)
        
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # if value:
                # self.setPen(QPen(Qt.red, self.pen().width(), Qt.SolidLine))
            # else:
                # self.setPen(QPen(self._color, self.pen().width(), Qt.SolidLine))
            self.setZValue(not self.isSelected()) # Bring item to front
            self.setCacheMode(self.cacheMode()) # Force redraw
        return super().itemChange(change, value)
        
        
    def sourceNode(self):
        return self.source
        

    def setSourceNode(self, node):
        self.source = node
        self.adjust()
        

    def destNode(self):
        return self.dest
        

    def setDestNode(self, node):
        self.dest = node
        self.adjust()
        

    def adjust(self):
        if not self.source or not self.dest:
            return

        line = QLineF(self.mapFromItem(self.source, 0, 0),
                      self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > 2*RADIUS+NODE_BORDER_WIDTH:
            edgeOffset = QPointF((line.dx() * (RADIUS + NODE_BORDER_WIDTH + 1)) / length,
                                 (line.dy() * (RADIUS + NODE_BORDER_WIDTH + 1)) / length)
            self.sourcePoint = line.p1() + edgeOffset
            self.destPoint = line.p2() - edgeOffset
        else:
            self.sourcePoint = line.p1()
            self.destPoint = line.p1()
        
        path = QPainterPath()
        if self.sourceNode() == self.destNode(): # Draw self-loops
            self.__is_self_loop = True
            path.moveTo(self.sourcePoint.x()-RADIUS-NODE_BORDER_WIDTH*2,
                        self.sourcePoint.y())
            path.cubicTo(QPointF(self.sourcePoint.x()-4*RADIUS,
                                 self.sourcePoint.y()),
                         QPointF(self.sourcePoint.x(),
                                 self.sourcePoint.y()-4*RADIUS),
                         QPointF(self.destPoint.x(),
                                 self.destPoint.y()-RADIUS-NODE_BORDER_WIDTH*2))
        else:
            self.__is_self_loop = False
            path.moveTo(self.sourcePoint)
            path.lineTo(self.destPoint)
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

        self.edgeList = []
        self._pie = []
        
        self.index = index
        self.label = label
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        
        self.setColor(Qt.lightGray)
        self.setPen(QPen(Qt.black, NODE_BORDER_WIDTH))
        
        # self.setOpacity(0.3)
    
    
    def setColor(self, color):
        self._color = color
        
        
    def setPie(self, values):
        self._pie = values
        self.setCacheMode(self.cacheMode()) # Force redraw

        
    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()
        

    def edges(self):
        return self.edgeList
        

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
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
        
        self.dragStartPos = None
        
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
                self.dragStartPos = event.pos()
            else:
                self.centerOn(event.pos())
    
    
    def mouseMoveEvent(self, event):
        if self.band.isVisible() and event.buttons() == Qt.MouseButtons(Qt.LeftButton) and self.dragStartPos is not None:
            self.centerOn(event.pos())
    
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.band.isVisible():
            self.viewport().unsetCursor()
            self.dragStartPos = None
    
    
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

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._minimum_zoom = 0
        
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        # fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        # fmt.setProfile(QSurfaceFormat.CoreProfile)
        # fmt.setDepthBufferSize(24)
        # QSurfaceFormat.setDefaultFormat(fmt)
        self.setViewport(QOpenGLWidget())
        self.viewport().setFormat(fmt)
        
        # print(self.viewport().format().samples(), self.viewport().format().depthBufferSize())
        # self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setFormAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.minimap = MiniMapGraphicsView(self)
        layout.addWidget(self.minimap)
        self.setLayout(layout)
        
        scene = QGraphicsScene(self)
        # scene.setItemIndexMethod(QGraphicsScene.NoIndex)
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
        # self.setWindowTitle("Test Network")

        
    def setScene(self, scene):
        super().setScene(scene)
        self.minimap.setScene(scene)

        
    # def activateOpenGL(self):
        # vport = QOpenGLWidget()
        # fmt = QSurfaceFormat()
        # fmt.setSamples(4)
        # QSurfaceFormat.setDefaultFormat(fmt)
        # vport.setFormat(fmt)
        # self.setViewport(vport)

            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.itemAt(event.pos()):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # self.setLowLOD()
        elif event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setRubberBandSelectionMode(Qt.ContainsItemShape)
            
        super().mousePressEvent(event)
        
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().unsetCursor()
            # self.setHighLOD()
        elif event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
            
            
    def mouseMoveEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.minimap.adjustRubberband()
            
        super().mouseMoveEvent(event)
        
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.minimap.adjustRubberband()
        
    
    # def setLowLOD(self):
        # pass
        # if self.edges_group is not None:
            # self.edges_group.hide()
        
        
    # def setHighLOD(self):
        # pass
        # if self.edges_group is not None:
            # self.edges_group.show()
        
        
    def translate(self, x, y):
        super().translate(x, y)
        self.minimap.adjustRubberband()
        
        
    def scale(self, factor_x, factor_y):
        super().scale(factor_x, factor_y)
        self.minimap.adjustRubberband()

                
    def zoomToFit(self):
        self.fitInView(self.scene().sceneRect().adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)
        self._minimum_zoom = self.transform().m11() # Set zoom out limit to horizontal scaling factor
        self.minimap.adjustRubberband()
        
        
    def wheelEvent(self, event):
        self.scaleView(2**(event.angleDelta().y() / 240.0))
        

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()

        if factor < self._minimum_zoom or factor > 2:
            return

        self.scale(scaleFactor, scaleFactor)
        

NodesModelType = 0
EdgesModelType = 1
class GraphTableModel(QAbstractTableModel):

    def __init__(self, graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        
    # def clear(self):
        # self.beginResetModel()

        # self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        if self._type == EdgesModelType:
            return self.graph.ecount()
        else:
            return self.graph.vcount()
        
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.attributes)
        
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        column = index.column()
        row = index.row()
        if column > self.columnCount() or row > self.rowCount():
            return None
        
        # if role == IndexRole:
            # return row
        # el
        if role in (Qt.DisplayRole, Qt.EditRole):
            if self._type == EdgesModelType:
                return str(self.graph.es[self.attributes[column]][row])
            else:
                return str(self.graph.vs[self.attributes[column]][row])
            
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.attributes[section]
        # elif role == Qt.DisplayRole and orientation == Qt.Vertical:
            # return None
        else:
            return super().headerData(section, orientation, role)
         
         
    @property   
    def attributes(self):
        if self._type == EdgesModelType:
            return [x for x in self.graph.es.attributes() if not x.startswith('__')]
        else:
            return [x for x in self.graph.vs.attributes() if not x.startswith('__')]
            
            
class NodesModel(GraphTableModel):
    _type = NodesModelType
    
    
class EdgesModel(GraphTableModel):
    _type = EdgesModelType
        
        
class ProxyModel(QSortFilterProxyModel):

        def __init__(self, parent=None):
            super().__init__(parent)
            
            # self._filter = None
            self._selection = None
           
            
        def filterAcceptsRow(self, sourceRow, sourceParent):
            if self._selection is not None:
                index = self.sourceModel().index(sourceRow, 0)
                # idx = self.sourceModel().data(index, IndexRole)
                if index.row() in self._selection:
                    return True
                return False
            
            return super().filterAcceptsRow(sourceRow, sourceParent)
            
            
        def setSelection(self, idx):
            '''Display only selected items from the scene'''
            if len(idx) == 0:
                self._selection = None
            else:
                self._selection = idx
            self.invalidateFilter()
        
        
if __name__ == '__main__':
    import sys
    import random
    import json
    import pandas as pd
    import numpy as np
    import igraph as ig
    from tqdm import tqdm
    
    
    from PyQt5.QtWidgets import (QVBoxLayout, QLineEdit, QWidget, QTableView,
        QTabWidget, QSplitter, QFileDialog, QGraphicsRectItem)
        
    class MainWindow(QWidget):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            self._show_help = False
            self.interactions = None
            self.label = None
            self.nodes_group = None
            self.edges_group = None
            
            self.graph = ig.Graph()
            
            layout = QVBoxLayout()
            self.setLayout(layout)
            
            edit = QLineEdit()
            layout.addWidget(edit)
            
            splitter = QSplitter(Qt.Vertical)
            layout.addWidget(splitter)
            
            self.view = NetworkView()
            self.view._drawForeground = self.view.drawForeground
            self.view.drawForeground = self.drawForeground
            splitter.addWidget(self.view)

            tab = QTabWidget()
            splitter.addWidget(tab)
            self._tables = []
            for Model, name in ((NodesModel, "Nodes"), 
                                (EdgesModel, "Edges")):
                table = QTableView()
                table.setSortingEnabled(True)
                model = Model(self.graph)
                proxy = ProxyModel()
                proxy.setSourceModel(model)
                table.setModel(proxy)
                tab.addTab(table, name)
                self._tables.append(table)

            # Connect Events
            edit.returnPressed.connect(self.filter_by_label)
            self.view.scene().selectionChanged.connect(self.on_selection_changed)
            
        
        
        def exportToCytoscape(self):
            try:
                from py2cytoscape.data.cyrest_client import CyRestClient
                
                # Create exportable copy of the graph object
                g = self.graph.copy()
                for attr in g.vs.attributes():
                    if attr.startswith('__'):
                        del g.vs[attr]
                    else:
                        g.vs[attr] = [str(x) for x in g.vs[attr]]
                for attr in g.es.attributes():
                    if attr.startswith('__'):
                        del g.es[attr]
                    else:
                        g.es[attr] = [str(x) for x in g.es[attr]]
                
                cy = CyRestClient()
                # cy.session.delete()
                g_cy = cy.network.create_from_igraph(g)
                
                # cy.layout.apply(name='force-directed', network=g_cy)
                
                layout = np.empty((g.vcount(), 2))
                for item in self.view.scene().items():
                    if item.Type == Node.Type:
                        layout[item.index] = (item.x(), item.y())
                positions = [(suid, x, y) for suid, (x, y) in zip(g_cy.get_nodes()[::-1], layout)]
                cy.layout.apply_from_presets(network=g_cy, positions=positions)
                
                with open('styles.json', 'r') as f:
                    style_js = json.load(f)
                style = cy.style.create('cyREST style', style_js)
                cy.style.apply(style, g_cy)
            except ConnectionRefusedError:
                print('Please launch Cytoscape before trying to export.')
            except ImportError:
                print('py2tocytoscape is required for this action (https://pypi.python.org/pypi/py2cytoscape).')
            except FileNotFoundError:
                print('styles.json not found...')
                
            # for c in g_cy.get_view(g_cy.get_views()[0])['elements']['nodes']:
                # pos = c['position']
                # id_ = int(c['data']['id_original'])
                # nodes[id_].setPos(QPointF(pos['x'], pos['y']))
        
        
        def exportAsImage(self):
            filename, filter = QFileDialog.getSaveFileName(self, "Save image", filter="SVG Files (*.svg);;BMP Files (*.bmp);;JPEG (*.JPEG);;PNG (*.png)")
            if filename:
                if filter == 'SVG Files (*.svg)':
                    try:
                        from PyQt5.QtSvg import QSvgGenerator
                    except ImportError:
                        print('QtSvg was not found on your system. It is needed for SVG export.')
                    else:
                        svg_gen = QSvgGenerator()

                        svg_gen.setFileName(filename)
                        svg_gen.setSize(self.size())
                        svg_gen.setViewBox(self.scene().sceneRect())
                        svg_gen.setTitle("SVG Generator Example Drawing")
                        svg_gen.setDescription("An SVG drawing created by the SVG Generator.")

                        painter = QPainter(svg_gen)
                        self.view.scene().render(painter)
                        painter.end()
                else:
                    image = QImage(self.view.scene().sceneRect().size().toSize(), QImage.Format_ARGB32)
                    image.fill(Qt.transparent)

                    painter = QPainter(image)
                    self.view.scene().render(painter);
                    image.save(filename)
            
            
        def drawForeground(self, painter, rect):
            self.view._drawForeground(painter, rect)
            
            if self._show_help:
                painter.resetTransform()
                help_text = '''
                Help
                
                C:   Export network to Cytoscape (it should be opened)
                F:   Switch to fullscreen/normal mode
                H:   Show this help text
                M:   Show/hide minimap
                P:   Show/hide pie (randomly choosen)
                S:   Save image as...
                Z:   Zoom to fit window
                +:   Zoom int
                -:   Zoom out
                Esc: Quit
                F5:  Recalculate layout
                '''
                painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignTop, help_text)

                
        def keyPressEvent(self, event):
            key = event.key()

            if key == Qt.Key_Plus:
                self.view.scaleView(1.2)
            elif key == Qt.Key_Minus:
                self.view.scaleView(1 / 1.2)
            elif key == Qt.Key_Escape:
                    self.close()
            elif key == Qt.Key_F5:
                if self.interactions is not None:
                    if self.infos is not None:
                        self.draw(self.interactions, self.infos)
                    else:
                        self.draw(self.interactions)
            elif key == Qt.Key_C:
                self.exportToCytoscape()
            elif key == Qt.Key_M:
                self.view.minimap.setVisible(not self.view.minimap.isVisible())
            elif key == Qt.Key_Z:
                self.view.zoomToFit()
            elif key == Qt.Key_F:
                if not self.isFullScreen():
                    self.setWindowFlags(Qt.Window)
                    self.showFullScreen()
                    # self.activateOpenGL()
                else:
                    self.setWindowFlags(Qt.Widget)
                    self.showNormal()
                    # self.actfivateOpenGL()
            elif key == Qt.Key_P:
                if not hasattr(self, '_pie_used'):
                    self._pie_used = False
                    
                if self._pie_used == False:
                    self._pie_used = True
                    for node in self.nodes_group.childItems():
                        pie = [random.random()/x for x in range(1, random.randint(1, 4))]
                        if len(pie) > 0:
                            pie.append(1-sum(pie))
                        node.setPie(pie)
                        node.update()
                else:
                    self._pie_used = False
                    for node in self.nodes_group.childItems():
                        node.setPie([])
                        node.update()
            elif key == Qt.Key_H:
                self._show_help = not self._show_help
                self.view.viewport().update()
            elif key == Qt.Key_S:
                self.exportAsImage()
            else:
                super().keyPressEvent(event)
                
                
        def drawNetwork(self, interactions, infos=None, labels=None):
            self.interactions = interactions
            self.infos = infos
            self.labels = labels
        
            self.view.scene().clear()
        
            nodes_idx = np.unique(np.vstack((interactions['Source'], interactions['Target'])))
            
            widths = np.array(interactions['Cosine'])
            min = max(0, widths.min() - 0.1)
            if min != widths.max():
                widths = (RADIUS-1)*(widths-min)/(widths.max()-min)+1
            else:
                widths = RADIUS
            
            print('Creating graph...')
            g = self.graph
            g.delete_vertices(g.vs) # Delete all previously created nodes
            g.add_vertices(nodes_idx.tolist()) #[int(x) for x in nodes_idx])
            # print(interactions['Source'])
            # print(interactions['Source']-1)
            g.add_edges(zip(interactions['Source']-1, interactions['Target']-1))
            # g.add_edges([(int(x['Source']-1), int(x['Target']-1)) for x in interactions])
            g.es['__weight'] = interactions['Cosine']
            g.es['__width'] = widths
            
            if interactions is not None:
                for col in interactions.dtype.names:
                    g.es[col] = interactions[col]
                    
            if infos is not None:
                for col in infos.dtype.names:
                    g.vs[col] = infos[col]

            if labels is not None:
                g.vs['__label'] = labels.astype('str')
            else:
                g.vs['__label'] = nodes_idx.astype('str')
            
            print('Adding nodes...')
            group = QGraphicsRectItem() #Create a pseudo-group, QGraphicsItemGroup is not used because it does not let children handle events
            group.setZValue(1) # Draw nodes on top of edges
            for i, n in enumerate(tqdm(g.vs)):
                node = Node(i, n['__label'])
                node.setParentItem(group)
            g.vs['__gobj'] = group.childItems()
            self.view.scene().addItem(group)
            self.nodes_group = group
               
            print('Adding edges...')
            group = QGraphicsRectItem()
            group.setZValue(0)
            for i, e in enumerate(tqdm(g.es)):
                edge = Edge(i, g.vs['__gobj'][e.source], g.vs['__gobj'][e.target], e['__weight'], e['__width'])
                edge.setParentItem(group)
            g.es['__gobj'] = group.childItems()
            self.view.scene().addItem(group)
            self.edges_group = group
             
            print('Computing layout...') 
            clusters = sorted(g.clusters(), key=len, reverse=True)
            dx, dy = 0, 0
            max_height = 0
            max_width = 0
            for i, ids in enumerate(tqdm(clusters)):
                graph = g.subgraph(ids)
                vcount = graph.vcount()
                
                if vcount == 1:
                    l = ig.Layout([(0, 0)])
                    border = 2*RADIUS
                elif vcount == 2:
                    l = ig.Layout([(0, -2*RADIUS), (0, 2*RADIUS)])
                    border = 2*RADIUS
                else:
                    l = graph.layout_graphopt(node_mass=3)
                    l.scale(3)
                    border = 5*RADIUS
                
                bb = l.bounding_box(border=border)
                l.translate(dx-bb.left, dy-bb.top)
            
                color = get_color(i)
                for coord, node in zip(l, graph.vs):
                    node['__gobj'].setPos(QPointF(*coord))
                    node['__gobj'].setColor(color)
                    
                if max_width == 0:
                    max_width = bb.width*2
            
                dx += bb.width
                max_height = max(max_height, bb.height)
                if dx >= max_width:
                    dx = 0
                    dy += max_height
                    max_height = 0
                    
            self.view.zoomToFit()
            self.view.minimap.zoomToFit()
            
            
        def on_selection_changed(self):
            items = self.view.scene().selectedItems()
            nodes_idx, edges_idx = [], []
            for item in items:
                if item.Type == Node.Type:
                    nodes_idx.append(item.index)
                elif item.Type == Edge.Type:
                    edges_idx.append(item.index)
            self._tables[0].model().setSelection(nodes_idx)
            self._tables[1].model().setSelection(edges_idx)
            

        def filter_by_label(self):
            import time
            t0 = time.time()
            num_nodes = 0
            num_edges = 0
            search = edit.text()
            for item in self.view.scene().items():
                if item.Type == Node.Type:
                    if search in item.label:
                        num_nodes += 1
                        item.setSelected(True)
                    else:
                        item.setSelected(False)
                elif item.Type == Edge.Type:
                    pass
            print('Selected {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))
            
            t0 = time.time()
            self._tables[0].model().setFilterRegExp(edit.text())
            # self._tables[0].model().setFilterKeyColumn(0)
            print('Filtered {} node(s) and {} edge(s) in {:.1f}ms'.format(num_nodes, num_edges, (time.time()-t0)*1000))
            
            
        def draw(self, interactions, infos, labels=None):
            for table in self._tables:
                table.model().sourceModel().beginResetModel()
                
            self.drawNetwork(interactions, infos, labels)
            
            for table in self._tables:
                table.model().sourceModel().endResetModel()
                
    
    COLORS = [Qt.GlobalColor(x) for x in range(4, 19) if x != Qt.yellow]
    def get_color(index):
        return COLORS[index % len(COLORS)]
    
    app = QApplication(sys.argv)
    
    win = MainWindow()

    interactions = pd.DataFrame({'Source': [1, 3, 4, 5],
                                'Target': [2, 3, 4, 5],
                                'Delta MZ': [28.031406, 0., 0., 0.],
                                'Cosine': [0.891845, 1., 1., 1.]}).to_records()


    infos = pd.DataFrame({'Source': [1, 2, 3, 4, 5],
                          'parent mass': [621.307, 593.276, 609.270, 545.272, 447.274]}).to_records()
    
    win.draw(interactions, infos)
    # win.draw(interactions, infos, labels=infos['parent mass'])
    
    win.show()

    sys.exit(app.exec_())
