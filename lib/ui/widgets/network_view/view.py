from PyQt5.QtCore import QRectF, pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QSurfaceFormat
from PyQt5.QtWidgets import QGraphicsView, QRubberBand, QOpenGLWidget, QFormLayout, QSizePolicy, QMenu

from .scene import Node, NetworkScene


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
        
        scene = NetworkScene(self)
        self.setScene(scene)        
        
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHint(QPainter.Antialiasing)
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_M:
            self.minimap.setVisible(not self.minimap.isVisible())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        pos = self.mapToScene(event.pos()).toPoint()
        node = self.scene().nodeAt(pos, self.transform())
        if node is not None:
            action = menu.addAction('Show spectrum')
            action.triggered.connect(lambda: self.showSpectrumTriggered.emit(node))
            action = menu.addAction('Set as compare spectrum')
            action.triggered.connect(lambda: self.compareSpectrumTriggered.emit(node))

        if len(menu.actions()) > 0:
            menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        pos = self.mapToScene(event.pos()).toPoint()
        node = self.scene().nodeAt(pos, self.transform())
        if node is not None:
            self.showSpectrumTriggered.emit(node)
            
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
            


