from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPen, QBrush

try:
    from .NetworkView import NetworkStyle, DefaultStyle, DarkStyle

except ImportError:
    class NetworkStyle:
        _name = ""
        _node_brush = QBrush()
        _text_color = QColor()
        _node_radius = 0
        _node_pen = QPen()
        _font = QFont()
        _edge_pen = QPen()
        _background_brush = QBrush()

        def name(self):
            return self._name

        def nodeBrush(self) -> QBrush:
            return self._node_brush

        def textColor(self) -> QColor:
            return self._text_color

        def nodeRadius(self) -> int:
            return self._node_radius

        def nodePen(self) -> QPen:
            return self._node_pen

        def font(self) -> QFont:
            return self._font

        def edgePen(self) -> QPen:
            return self._edge_pen

        def backgroundBrush(self) -> QBrush:
            return self._background_brush


    class DefaultStyle(NetworkStyle):
        _name = "default"
        _node_brush = QBrush(Qt.lightGray)
        _text_color = QColor(Qt.black)
        _node_radius = 30
        _node_pen = QPen(Qt.black, 1, Qt.DotLine)
        _font = QFont("Arial", 10)
        _edge_pen = QPen(Qt.darkGray)
        _background_brush = QBrush(Qt.white)


    class DarkStyle(NetworkStyle):
        _name = "dark"
        _node_brush = QBrush(Qt.darkGray)
        _text_color = QColor(Qt.white)
        _node_radius = 30
        _node_pen = QPen(Qt.white, 2)
        _font = QFont("Times New Roman", 12)
        _edge_pen = QPen(Qt.lightGray)
        _background_brush = QBrush(QColor(Qt.darkGray).darker())
