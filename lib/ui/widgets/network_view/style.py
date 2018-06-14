from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPen, QBrush

try:
    from .NetworkView import NetworkStyle, DefaultStyle, DarkStyle

except ImportError:
    class NetworkStyle:
        name = ""
        node_brush = QBrush()
        node_text_color = QColor()
        node_radius = 0
        node_pen = QPen()
        node_font = QFont()
        edge_pen = QPen()
        background_brush = QBrush()

        def __init__(self, name=None, node_brush=None, node_text_color=None,
                     node_pen=None, node_font=None, edge_pen=None, background_brush=None):
            if name is not None:
                self.name = name
            if node_brush is not None:
                self.node_brush = node_brush
            if node_text_color is not None:
                self.node_text_color = node_text_color
            if node_pen is not None:
                self.node_pen = node_pen
            if node_font is not None:
                self.node_font = node_font
            if edge_pen is not None:
                self.edge_pen = edge_pen
            if background_brush is not None:
                self.background_brush = background_brush

        def styleName(self):
            return self.name

        def nodeBrush(self) -> QBrush:
            return self.node_brush

        def nodeTextColor(self) -> QColor:
            return self.node_text_color

        def nodeRadius(self) -> int:
            return self.node_radius

        def nodePen(self) -> QPen:
            return self.node_pen

        def nodeFont(self) -> QFont:
            return self.node_font

        def edgePen(self) -> QPen:
            return self.edge_pen

        def backgroundBrush(self) -> QBrush:
            return self.background_brush


    class DefaultStyle(NetworkStyle):
        name = "default"
        node_brush = QBrush(Qt.lightGray)
        node_text_color = QColor(Qt.black)
        node_radius = 30
        node_pen = QPen(Qt.black, 1, Qt.DotLine)
        node_font = QFont("Arial", 10)
        edge_pen = QPen(Qt.darkGray)
        background_brush = QBrush(Qt.white)


    class DarkStyle(NetworkStyle):
        name = "dark"
        node_brush = QBrush(Qt.darkGray)
        node_text_color = QColor(Qt.white)
        node_radius = 30
        node_pen = QPen(Qt.white, 2)
        node_font = QFont("Times New Roman", 12)
        edge_pen = QPen(Qt.lightGray)
        background_brush = QBrush(QColor(Qt.darkGray).darker())
