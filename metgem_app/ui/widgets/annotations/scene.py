from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGraphicsItem

from ....config import get_python_rendering_flag

from PySide6MolecularNetwork.graphicsitem import GraphicsItemLayer
if get_python_rendering_flag():
    from PySide6MolecularNetwork._pure import NetworkScene
else:
    from PySide6MolecularNetwork import NetworkScene


class AnnotationsNetworkScene(NetworkScene):
    annotationAdded = Signal(QGraphicsItem)
    arrowEdited = Signal(QGraphicsItem)
    editAnnotationItemRequested = Signal(QGraphicsItem)
    
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
