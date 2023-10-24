from typing import Union

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QPixmap, QPainter, QPen, QIcon, QColor
from PySide6.QtWidgets import QListWidgetItem, QDialog
from metgem.ui.pen_parameters_dialog_ui import Ui_Dialog


class PenParametersDialog(QDialog, Ui_Dialog):
    PenStyleRole = Qt.UserRole
    ColorRole = Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        points = [(0, 0), (-6.6572836, 4.361927), (-9.2177166, 7.340494), (-2.2137959, 2.5753221),
                  (-4.66601534, 6.1499951), (-4.81185534, 9.5429151), (-0.070593, 1.642318), (1.35985124, 3.843193),
                  (2.70403794, 4.203864), (3.9058194, 1.048006), (7.699405, -2.258071), (11.636839, -2.220768),
                  (4.653883, 0.04409), (8.669976, 4.329893), (13.502289, 2.931417), (7.08685, -2.050941),
                  (17.480776, -9.315182), (14.745917, -16.1672141), (-0.308121, -0.771981), (-2.309601, -0.355324),
                  (-2.309601, -0.355324)]
        points = [QPointF(*p) * 10 for p in points]
        path = QPainterPath()
        ref_p = QPointF(14.1681, 0.2321) * 10
        path.moveTo(ref_p)
        for i in range(0, len(points) - 2, 3):
            ep = points[i + 2] + ref_p
            c1 = points[i] + ref_p
            c2 = points[i + 1] + ref_p
            path.cubicTo(c1, c2, ep)
            ref_p = ep

        rect = path.boundingRect().adjusted(-5, -5, 5, 5)

        pen_styles = {k: getattr(Qt, k) for k in dir(Qt) if isinstance(getattr(Qt, k), Qt.PenStyle)}
        for name, style in sorted(pen_styles.items(), key=lambda x: x[1]):
            if "PenStyle" in name or "Custom" in name or "NoPen" in name:
                continue
            item = QListWidgetItem(name)
            item.setData(PenParametersDialog.PenStyleRole, style)
            pixmap = QPixmap(int(rect.width()), int(rect.height()))
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            painter.setPen(QPen(Qt.darkGreen, 10, style))
            painter.drawPath(path)
            painter.end()
            item.setIcon(QIcon(pixmap))
            self.lstPenStyles.addItem(item)

        colors = {k: getattr(Qt, k) for k in dir(Qt) if isinstance(getattr(Qt, k), Qt.GlobalColor)}
        for name, color in sorted(colors.items(), key=lambda x: x[1]):
            if "color" in name or name == "transparent":
                continue
            item = QListWidgetItem(name)
            item.setData(PenParametersDialog.ColorRole, color)
            pixmap = QPixmap(100, 25)
            painter = QPainter()
            painter.begin(pixmap)
            painter.setBrush(color)
            painter.drawRect(pixmap.rect())
            painter.end()
            item.setIcon(QIcon(pixmap))
            self.lstPenColors.addItem(item)

    def getValues(self) -> Union[QPen, None]:
        try:
            item = self.lstPenStyles.selectedItems()[0]
        except IndexError:
            return
        else:
            style = item.data(PenParametersDialog.PenStyleRole)

        try:
            item = self.lstPenColors.selectedItems()[0]
        except IndexError:
            return
        else:
            color = item.data(PenParametersDialog.ColorRole)

        return QPen(Qt.GlobalColor(color),
                    float(self.spinPenSize.value()),
                    Qt.PenStyle(style))

    def setValues(self, pen: QPen):
        for i in range(self.lstPenStyles.count()):
            item = self.lstPenStyles.item(i)
            if item.data(PenParametersDialog.PenStyleRole) == pen.style():
                item.setSelected(True)
                break

        for i in range(self.lstPenColors.count()):
            item = self.lstPenColors.item(i)
            if QColor(item.data(PenParametersDialog.ColorRole)).name() == pen.color().name():
                item.setSelected(True)
                break

        self.spinPenSize.setValue(pen.width())
