from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGraphicsItem

from ....config import get_python_rendering_flag

from PyQtNetworkView.graphicsitem import GraphicsItemLayer
if get_python_rendering_flag():
    from PyQtNetworkView._pure import NetworkScene
else:
    from PyQtNetworkView import NetworkScene


class AnnotationsNetworkScene(NetworkScene):
    annotationAdded = pyqtSignal(QGraphicsItem)
    arrowEdited = pyqtSignal(QGraphicsItem)
    editAnnotationItemRequested = pyqtSignal(QGraphicsItem)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clearAnnotations()

    # noinspection PyAttributeOutsideInit
    def clearAnnotations(self):
        if hasattr(self, 'annotationsLayer'):
            self.removeItem(self.annotationsLayer)

        self.annotationsLayer = GraphicsItemLayer()
        self.addItem(self.annotationsLayer)
        self.annotationsLayer.setZValue(1000)

    def requestEditAnnotationItem(self, item: QGraphicsItem):
        self.editAnnotationItemRequested.emit(item)

    def getDefaultFontSizeFromRect(self):
        return max(self.height(), self.width()) / 25 / self.scale()

    def getDefaultPenSizeFromRect(self):
        return self.getDefaultFontSizeFromRect() / 16
