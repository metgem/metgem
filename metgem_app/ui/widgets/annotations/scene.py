from qtpy.QtCore import Signal
from qtpy.QtWidgets import QGraphicsItem

from ....config import get_python_rendering_flag

from PySide2MolecularNetwork.graphicsitem import GraphicsItemLayer
if get_python_rendering_flag():
    from PySide2MolecularNetwork._pure import NetworkScene
else:
    from PySide2MolecularNetwork import NetworkScene


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
