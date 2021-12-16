import os
import random
from itertools import zip_longest
from typing import List, Union, Optional, Tuple

import matplotlib.cm as mplcm
import numpy as np
import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings, QSize, QAbstractTableModel, QModelIndex, QObject, QEvent, QRect, QRectF
from PyQt5.QtGui import QColor, QStandardItemModel, QIcon, QDropEvent, QKeyEvent, QBrush, QImage, QPixmap, QPainter, \
    QTransform, QPen, QPolygonF, QGradient, QPalette
from PyQt5.QtWidgets import (QDialog, QColorDialog, QListWidgetItem, QFileDialog, QMessageBox, QInputDialog,
                             QAbstractItemView, QDialogButtonBox, QFormLayout, QDoubleSpinBox, QAbstractSpinBox, QLabel,
                             QStyledItemDelegate, QStyleOptionViewItem, QWidget, QHBoxLayout, QButtonGroup,
                             QToolButton)

from PyQtNetworkView.node import NODE_POLYGON_MAP, NodePolygon
from ..models.metadata import ColorMarkRole, ColumnDataRole
from ..utils import pairwise

UI_FILE = os.path.join(os.path.dirname(__file__), 'color_mapping_dialog.ui')

ColorMappingDialogUI, ColorMappingDialogBase = uic.loadUiType(UI_FILE,
                                                              from_imports='metgem_app.ui',
                                                              import_from='metgem_app.ui')

ColumnRole = Qt.UserRole + 1
ValueRole = Qt.UserRole + 2

MOVE_COLUMNS_SELECT = 0
MOVE_COLUMNS_UNSELECT = 1

NODE_BRUSH_STYLES = {
    Qt.NoBrush,
    Qt.Dense1Pattern,
    Qt.Dense2Pattern,
    Qt.Dense3Pattern,
    Qt.Dense4Pattern,
    Qt.Dense5Pattern,
    Qt.Dense6Pattern,
    Qt.Dense7Pattern,
    Qt.HorPattern,
    Qt.VerPattern,
    Qt.CrossPattern,
    Qt.BDiagPattern,
    Qt.FDiagPattern,
    Qt.DiagCrossPattern,
}


# https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
# noinspection PyCallByClass,PyTypeChecker
def generate_colors(n, seed=None):
    """Generate list of `n` colors"""

    colors = []
    if seed is None:
        h = random.random()
    else:
        h = seed

    golden_ratio = 0.618033988749895  # 1/phi
    for i in range(n):
        colors.append(QColor.fromHsv(h * 360, 150, 254, 255))
        h += golden_ratio
        h %= 1
    return colors


def get_colors(n, cmap='auto'):
    if cmap == 'auto':
        return generate_colors(n)
    else:
        try:
            cm = mplcm.get_cmap(cmap)
        except ValueError:
            return []
        if (isinstance(cm, (mplcm.colors.ListedColormap, mplcm.colors.LinearSegmentedColormap)) and cm.N < 256) \
                or n == 1:
            return [QColor(*cm(i, bytes=True)) for i in range(cm.N)]
        else:
            step = 256 // (n - 1)
            return [QColor(*cm(i * step, bytes=True)) for i in range(n)]


# https://gist.github.com/ChrisBeaumont/4025831
# noinspection PyArgumentList
def cmap2pixmap(cmap, steps=50):
    """Convert a maplotlib colormap into a QPixmap
    :param cmap: The colormap to use
    :type cmap: Matplotlib colormap instance (e.g. matplotlib.cm.gray)
    :param steps: The number of color steps in the output. Default=50
    :type steps: int
    :rtype: QPixmap
    """
    if cmap == 'auto':
        colors = generate_colors(steps)
    else:
        try:
            norm = mplcm.colors.Normalize(vmin=0., vmax=1.)
            sm = mplcm.ScalarMappable(norm=norm, cmap=cmap)
            inds = np.linspace(0, 1, steps)
            colors = [QColor(*c) for c in sm.to_rgba(inds, bytes=True)]
        except ValueError:
            return

    im = QImage(steps, 1, QImage.Format_Indexed8)
    im.setColorTable([c.rgba() for c in colors])
    for i in range(steps):
        im.setPixel(i, 0, i)
    im = im.scaled(72, 18)
    return QPixmap.fromImage(im)


def nodePolygonToPixmap(polygon: NodePolygon, size: QSize = QSize(48, 48), zoom: int = 1.2) -> QPixmap:
    w, h = size.width(), size.height()
    image = QImage(w*zoom, h*zoom, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setPen(QPen(QPalette().color(QPalette.Text), 5))
    painter.setTransform(QTransform().translate(w/2*zoom, h/2*zoom).scale(w/100., h/100.))
    if polygon == NodePolygon.Circle:
        painter.drawEllipse(QRectF(-50*zoom, -50*zoom, 100., 100.))
    else:
        polygon = NODE_POLYGON_MAP.get(polygon)
        painter.drawPolygon(polygon)
    painter.end()
    return QPixmap(image)


def nodeBrushStyleToPixmap(style: Qt.BrushStyle, size: QSize = QSize(48, 48), zoom: int = 1.2) -> QPixmap:
    w, h = size.width(), size.height()
    image = QImage(w*zoom, h*zoom, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setBrush(QBrush(style))
    painter.drawRect(QRectF(zoom, zoom, w, h))
    painter.end()
    return QPixmap(image)


class ColorDialog(QColorDialog):

    @staticmethod
    def getColorPolygonAndBrushStyle(
            initial_color: Union[QColor, Qt.GlobalColor, QGradient] = QColor(),
            initial_polygon: NodePolygon = NodePolygon.Circle,
            initial_brushstyle: Qt.BrushStyle = Qt.NoBrush,
            parent: Optional[QWidget] = None, title: str = '',
            options: Union[QColorDialog.ColorDialogOptions,
                           QColorDialog.ColorDialogOption] = QColorDialog.ColorDialogOptions()) \
            -> (QColor, NodePolygon):

        dlg = QColorDialog(parent)

        # Add buttons to select polygon
        polygons_group = QButtonGroup(parent)
        polygons_layout = QHBoxLayout(parent)
        for p in NodePolygon:
            if p == NodePolygon.Custom:
                continue

            button = QToolButton(parent)
            button.setCheckable(True)
            button.setText(p.name)
            button.setIcon(QIcon(nodePolygonToPixmap(p, button.iconSize())))

            if p == initial_polygon:
                button.setChecked(True)
            polygons_group.addButton(button)
            polygons_group.setId(button, p.value)
            polygons_layout.addWidget(button)
        dlg.layout().insertLayout(dlg.layout().count()-1, polygons_layout)

        # Add buttons to select brush style
        brushstyle_group = QButtonGroup(parent)
        brushstyle_layout = QHBoxLayout(parent)
        for p in NODE_BRUSH_STYLES:
            button = QToolButton(parent)
            button.setCheckable(True)
            button.setIcon(QIcon(nodeBrushStyleToPixmap(p, button.iconSize())))

            if p == initial_brushstyle:
                button.setChecked(True)
            brushstyle_group.addButton(button)
            brushstyle_group.setId(button, p)
            brushstyle_layout.addWidget(button)
        dlg.layout().insertLayout(dlg.layout().count()-1, brushstyle_layout)

        if title:
            dlg.setWindowTitle(title)
        dlg.setOptions(options)
        dlg.setCurrentColor(initial_color)
        dlg.exec_()
        return (dlg.selectedColor(),
                NodePolygon(polygons_group.checkedId()),
                brushstyle_group.checkedId(),
                )


class RangeInputDialog(QDialog):
    def __init__(self, parent=None, low=None, high=None):
        super().__init__(parent)

        self.sbLowValue = QDoubleSpinBox(self)
        self.sbLowValue.setMinimum(0)
        self.sbLowValue.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        if low is not None:
            self.sbLowValue.setValue(low)

        self.sbHighValue = QDoubleSpinBox(self)
        self.sbHighValue.setMinimum(0)
        self.sbLowValue.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        if high is not None:
            self.sbHighValue.setValue(high)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("Low value", self.sbLowValue)
        layout.addRow("High value", self.sbHighValue)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def getRange(self):
        return self.sbLowValue.value(), self.sbHighValue.value()


class WidgetItem(QListWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizeHint(QSize(self.sizeHint().width(), 32))
        self.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)


class ColorMixin:
    __metaclass__ = WidgetItem

    def setBackground(self, background: Union[QBrush, QColor]):
        if background is not None:
            if not isinstance(background, QBrush):
                background = QBrush(background)
            color = background.color()
            luma = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
            text_color = QColor(Qt.black) if luma > 0.5 else QColor(Qt.white)

            super().setBackground(color)
            self.setForeground(text_color)
        else:
            self.setData(Qt.BackgroundRole, None)
            self.setData(Qt.ForegroundRole, None)


class GroupListWidgetItem(ColorMixin, WidgetItem):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.setData(ValueRole, data)


class BoolListWidgetItem(ColorMixin, WidgetItem):
    def __init__(self, data, *args, **kwargs):
        super().__init__(str(data), *args, **kwargs)
        self.setData(ValueRole, data)


class RangeListWidgetItem(ColorMixin, WidgetItem):
    def __init__(self, low, high, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setData(ValueRole, (low, high))

    def setData(self, role, value):
        super().setData(role, value)
        if role == ValueRole:
            self.setText('[{0:.2f} - {1:.2f}]'.format(*value))

    def __lt__(self, other):
        sval = self.data(ValueRole)
        oval = other.data(ValueRole)
        if sval is not None and oval is not None:
            return sval < oval
        return super().__lt__(other)


class ColumnListWidgetItem(ColorMixin, WidgetItem):
    def __init__(self, *args, column: int = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setData(ColumnRole, column)

    def __lt__(self, other):
        scol = self.data(ColumnRole)
        ocol = other.data(ColumnRole)
        if scol is not None and ocol is not None:
            return scol < ocol
        return super().__lt__(other)


class ColorListWidgetItem(ColorMixin, WidgetItem):
    def setBackground(self, background: QBrush):
        if not isinstance(background, QBrush):
            background = QBrush(background)

        color = background.color()
        self.setData(Qt.DisplayRole,
                     f"RGB{color.red(), color.green(), color.blue()} [{color.name()}]")
        super().setBackground(background)


class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)
        polygon_id = index.data(BaseColorMappingDialog.PolygonRole)
        brushstyle = index.data(BaseColorMappingDialog.BrushStyleRole)
        h = option.rect.height()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRect(option.rect)
        painter.setPen(QPen(Qt.lightGray, h/5.))
        if brushstyle is not None:
            painter.setBrush(QBrush(Qt.lightGray, brushstyle))
        zoom = .9
        painter.setTransform(QTransform()
                             .translate(option.rect.x()+h/2+10, option.rect.y()+h/2)
                             .rotate(-5.)
                             .scale(h/100.*zoom, h/100.*zoom))
        if polygon_id is None or polygon_id == NodePolygon.Circle:
            painter.drawEllipse(QRect(-50, -50, 100, 100))
        else:
            polygon = NODE_POLYGON_MAP.get(polygon_id, QPolygonF())
            painter.drawPolygon(polygon)
        painter.restore()


class BaseColorMappingDialog(ColorMappingDialogUI, ColorMappingDialogBase):

    PolygonRole = Qt.UserRole
    BrushStyleRole = Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        current_cmap = QSettings().value('ColorMap', 'auto')
        cmaps = ['auto'] + sorted([k for k in mplcm.cmap_d.keys() if not k.endswith('_r')], key=lambda s: s.casefold())
        for i, cmap in enumerate(cmaps):
            pixmap = cmap2pixmap(cmap)
            self.cbColorMap.addItem(QIcon(pixmap), cmap)
            if cmap == current_cmap:
                self.cbColorMap.setCurrentIndex(i)

        self.lstUsedColumns.setItemDelegate(ItemDelegate())
        self.lstColors.setItemDelegate(ItemDelegate())

        self.lstColumns.viewport().installEventFilter(self)
        self.lstUsedColumns.viewport().installEventFilter(self)
        self.lstUsedColumns.installEventFilter(self)

        self.lstUsedColumns.itemDoubleClicked.connect(self.get_color)
        self.lstColors.itemDoubleClicked.connect(self.get_color)
        self.btEditColor.clicked.connect(lambda: self.get_color(self.lstColors.currentItem()))
        self.btAddColor.clicked.connect(self.add_color)
        self.btRemoveColors.clicked.connect(self.remove_selected_colors)
        self.btGenerateColors.clicked.connect(lambda: self.generate_new_colors(self.cbColorMap.currentText()))
        self.btAutoAssignColors.clicked.connect(self.auto_assign_colors)
        self.cbColorMap.currentIndexChanged[str].connect(self.generate_new_colors)
        self.btRemoveSelectedColumnsColors.clicked.connect(self.remove_selected_columns_colors)
        self.btLoadColorList.clicked.connect(self.load_color_list)
        self.btSaveColorList.clicked.connect(self.save_color_list)

    def get_color(self, item: ColorListWidgetItem = None):
        current_color = item.data(Qt.BackgroundRole).color() \
            if item is not None and item.data(Qt.BackgroundRole) is not None else QColor()
        current_polygon = item.data(BaseColorMappingDialog.PolygonRole) \
            if item is not None and item.data(BaseColorMappingDialog.PolygonRole) is not None else NodePolygon.Circle
        current_brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole) \
            if item is not None and item.data(BaseColorMappingDialog.BrushStyleRole) is not None else Qt.NoBrush

        color, polygon_id, brushstyle = ColorDialog.getColorPolygonAndBrushStyle(
            initial_color=current_color,
            initial_polygon=current_polygon,
            initial_brushstyle=current_brushstyle,
            parent=self,
            options=QColorDialog.ShowAlphaChannel)

        if color.isValid():
            item.setBackground(color)
        item.setData(BaseColorMappingDialog.PolygonRole, polygon_id)
        item.setData(BaseColorMappingDialog.BrushStyleRole, brushstyle)

    def add_color(self):
        color, polygon_id, brushstyle = ColorDialog.getColorPolygonAndBrushStyle(
            parent=self,
            options=QColorDialog.ShowAlphaChannel)

        if color.isValid():
            item = ColorListWidgetItem()
            item.setBackground(color)
            item.setData(BaseColorMappingDialog.PolygonRole, polygon_id)
            item.setData(BaseColorMappingDialog.BrushStyleRole, brushstyle)
            self.lstColors.addItem(item)

    def remove_selected_colors(self):
        for item in self.lstColors.selectedItems():
            self.lstColors.takeItem(self.lstColors.row(item))

    def set_colors(self, colors: List[Union[str, QColor]],
                   polygons: List[Union[int, str, NodePolygon]] = [],
                   brush_styles: List[Union[str, Qt.BrushStyle]] = []):
        self.lstColors.clear()
        for color, poly, brush_style in zip_longest(colors, polygons, brush_styles):
            if isinstance(color, str):
                color = QColor(color)

            if isinstance(poly, str):
                try:
                    poly = NodePolygon[poly]
                except KeyError:
                    poly = NodePolygon.Circle
            if isinstance(poly, int):
                poly = NodePolygon(poly)

            if isinstance(brush_style, str):
                brush_style = Qt.BrushStyle(int(brush_style))

            if color.isValid():
                item = ColorListWidgetItem()
                item.setBackground(color)
                if poly is not None:
                    item.setData(BaseColorMappingDialog.PolygonRole, poly)
                if brush_style is not None:
                    item.setData(BaseColorMappingDialog.BrushStyleRole, brush_style)
                self.lstColors.addItem(item)

    def generate_new_colors(self, cmap: str = 'auto'):
        self.set_colors(get_colors(self.lstUsedColumns.count(), cmap=cmap))

    def auto_assign_colors(self):
        column_items = self.lstUsedColumns.selectedItems()
        if not column_items:
            column_items = [self.lstUsedColumns.item(row) for row in range(self.lstUsedColumns.count())]
        color_items = self.lstColors.selectedItems()
        if not color_items:
            color_items = [self.lstColors.item(row) for row in range(self.lstColors.count())]

        for i, column_item in enumerate(column_items):
            try:
                color_item = color_items[i]
            except IndexError:
                color_item = color_items[-1]

            if color_item:
                column_item.setBackground(color_item.data(Qt.BackgroundRole).color())
                column_item.setData(BaseColorMappingDialog.PolygonRole,
                                    color_item.data(BaseColorMappingDialog.PolygonRole))
                column_item.setData(BaseColorMappingDialog.BrushStyleRole,
                                    color_item.data(BaseColorMappingDialog.BrushStyleRole))

    def remove_selected_columns_colors(self):
        for item in self.lstUsedColumns.selectedItems():
            item.setBackground(None)

    def import_color_item(self, row: List[str]) -> Tuple:
        color = QColor(row[1][0])
        if color.isValid():
            return color,

    def load_color_list(self):
        filter_ = ["Color list (*.txt)"]
        filename, filter_ = QFileDialog.getOpenFileName(self, "Load color list",
                                                        filter=";;".join(filter_))
        if filename:
            data = []
            try:
                df = pd.read_csv(filename, header=None)

                for row in df.iterrows():
                    d = self.import_color_item(row)
                    if d is not None:
                        data.append(d)

                self.set_colors(*zip(*data))
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Load failed (I/O Error).")

    def export_color_item(self, item: QListWidgetItem) -> List[str]:
        color = item.data(Qt.BackgroundRole).color()
        if color is not None and color.isValid():
            return color.name(),

    def save_color_list(self):
        filter_ = ["Color list (*.txt)"]
        filename, filter_ = QFileDialog.getSaveFileName(self, "Save color list",
                                                        filter=";;".join(filter_))
        if filename:
            try:
                with open(filename, 'w') as f:
                    for row in range(self.lstColors.count()):
                        f.write(",".join([str(_) for _ in self.export_color_item(self.lstColors.item(row))]) + '\n')
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Save failed (I/O Error).")

    def eventFilter(self, obj: QObject, event: Union[QDropEvent, QKeyEvent, QEvent]):
        if event.type() == QEvent.KeyPress and obj == self.lstUsedColumns:
            if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
                self.remove_selected_columns_colors()
                event.accept()
        elif event.type() == QEvent.DragEnter and obj == event.source().viewport():
            event.setDropAction(Qt.IgnoreAction)  # Do not allow internal drag'n'drop
        elif event.type() == QEvent.Drop and obj == self.lstUsedColumns.viewport():
            if event.source() == self.lstColors:
                data = event.mimeData()
                if data.hasFormat('application/x-qabstractitemmodeldatalist'):
                    first_item = self.lstUsedColumns.itemAt(event.pos())

                    if first_item is not None:
                        model = QStandardItemModel()
                        model.dropMimeData(data, Qt.CopyAction, 0, 0, QModelIndex())
                        for i in range(model.rowCount()):
                            color = model.item(i, 0).data(Qt.BackgroundRole).color()
                            polygon_id = model.item(i, 0).data(BaseColorMappingDialog.PolygonRole)
                            brushstyle = model.item(i, 0).data(BaseColorMappingDialog.BrushStyleRole)
                            item = self.lstUsedColumns.item(self.lstUsedColumns.row(first_item) + i)
                            if item:
                                item.setBackground(color)
                                item.setData(BaseColorMappingDialog.PolygonRole, polygon_id)
                                item.setData(BaseColorMappingDialog.BrushStyleRole, brushstyle)
                    event.accept()
            elif event.source() == self.lstColumns:
                data = event.mimeData()
                if data.hasFormat('application/x-qabstractitemmodeldatalist'):
                    event.setDropAction(Qt.MoveAction)
                    model = QStandardItemModel()
                    model.dropMimeData(data, Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(model.rowCount()):
                        item = model.item(i, 0)
                        new_item = ColumnListWidgetItem(item.data(Qt.DisplayRole),
                                                        column=item.data(ColumnRole))
                        bg = item.data(Qt.BackgroundRole)
                        polygon_id = item.data(BaseColorMappingDialog.PolygonRole)
                        brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole)
                        if bg is not None and bg.color().isValid():
                            new_item.setBackground(bg.color())
                        new_item.setData(BaseColorMappingDialog.PolygonRole, polygon_id)
                        new_item.setData(BaseColorMappingDialog.BrushStyleRole, brushstyle)
                        self.lstUsedColumns.addItem(new_item)
                    self.lstUsedColumns.sortItems()
                    event.accept()

        return super().eventFilter(obj, event)


class PieColorMappingDialog(BaseColorMappingDialog):

    def __init__(self, *args, model: QAbstractTableModel = None, selected_columns: List[int] = None, **kwargs):
        super().__init__(*args, **kwargs)

        for i in range(self.layoutBins.count()):
            w = self.layoutBins.itemAt(i).widget()
            if w is not None and not isinstance(w, QLabel):
                w.hide()

        if model is not None:
            for col in range(model.columnCount()):
                text = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                color = model.headerData(col, Qt.Horizontal, ColorMarkRole)
                item = ColumnListWidgetItem(text, column=col)
                if color is not None:
                    item.setBackground(color)

                if selected_columns is not None and col in selected_columns:
                    self.lstUsedColumns.addItem(item)
                else:
                    self.lstColumns.addItem(item)

        colors = QSettings().value('NetworkView/pie_colors',
                                   [c.name() for c in generate_colors(8)],
                                   type=str)
        self.set_colors(colors)

        self.btUseSelectedColumns.clicked.connect(lambda: self.move_selected_columns(MOVE_COLUMNS_SELECT))
        self.btRemoveSelectedColumns.clicked.connect(lambda: self.move_selected_columns(MOVE_COLUMNS_UNSELECT))

    def move_selected_columns(self, direction=MOVE_COLUMNS_SELECT):
        if direction == MOVE_COLUMNS_SELECT:
            source = self.lstColumns
            dest = self.lstUsedColumns
        else:
            source = self.lstUsedColumns
            dest = self.lstColumns

        for item in source.selectedItems():
            source.takeItem(source.row(item))
            new_item = ColumnListWidgetItem(item.data(Qt.DisplayRole), column=item.data(ColumnRole))
            bg = item.data(Qt.BackgroundRole)
            if bg is not None and bg.color().isValid():
                new_item.setBackground(bg.color())
            dest.addItem(new_item)
            new_item.setSelected(True)

    def done(self, r):
        if r == QDialog.Accepted:
            colors = [self.lstColors.item(row).data(Qt.BackgroundRole).color().name()
                      for row in range(self.lstColors.count())]
            QSettings().setValue('NetworkView/pie_colors', colors)
        super().done(r)

    def getValues(self):
        columns = []
        colors = []
        for row in range(self.lstUsedColumns.count()):
            item = self.lstUsedColumns.item(row)
            column = item.data(ColumnRole)
            bg = item.data(Qt.BackgroundRole)
            columns.append(column)
            if bg is not None and bg.color().isValid():
                colors.append(bg.color())
            else:
                colors.append(QColor(Qt.transparent))
        return columns, colors


class ColorMappingDialog(BaseColorMappingDialog):

    def __init__(self, *args, model: QAbstractTableModel = None, column_id: int = None, mapping: dict = None, **kwargs):
        self._model = model
        self._column_id = column_id

        super().__init__(*args, **kwargs)

        data = self._model.headerData(self._column_id, Qt.Horizontal, role=ColumnDataRole)
        if data is not None and not isinstance(data, pd.Series):
            data = pd.Series(data)
        self._data = data

        if model is not None and column_id is not None:
            for i in range(model.columnCount()):
                index = model.index(0, i)
                text = model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                color = model.headerData(i, Qt.Horizontal, ColorMarkRole)
                item = ColumnListWidgetItem(text, column=index.column())
                if color is not None:
                    item.setBackground(color)

                if index.column() != column_id:
                    self.lstColumns.addItem(item)

        self.lstUsedColumns.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.lstColumns.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_bins(mapping)

        colors = QSettings().value('NetworkView/node_colors',
                                   [c.name() for c in generate_colors(8)],
                                   type=str)
        self.set_colors(colors)

        self.btUseSelectedColumns.clicked.connect(self.on_use_selected_column)
        self.btRemoveSelectedColumns.clicked.connect(self.on_unuse_selected_column)

    def populate_bins(self, mapping=None):
        try:
            self.btGenerateBins.clicked.disconnect()
            self.btMergeBins.clicked.disconnect()
            self.btSplitBins.clicked.disconnect()
            self.btEditBin.clicked.disconnect()
            self.btAddBin.clicked.disconnect()
            self.btRemoveBins.clicked.disconnect()
        except TypeError:
            pass

        data = self._data

        if data is not None:
            if data.dtype == np.bool:
                self.lblUsedColumns.setText('Groups')
                for val in (True, False):
                    item = BoolListWidgetItem(val)
                    self.lstUsedColumns.addItem(item)
                    if mapping is not None:
                        color = mapping.get(val, None)
                        if color is None:
                            color = mapping.get(str(val).lower(), None)  # True -> 'true', False -> 'false'
                        if color is not None:
                            item.setBackground(QColor(color))
            elif data.dtype == np.object:
                self.lblUsedColumns.setText('Groups')
                if mapping is not None:
                    for group, color in mapping:
                        item = GroupListWidgetItem(str(group))
                        item.setBackground(QColor(color))
                        self.lstUsedColumns.addItem(item)
                else:
                    groups = data.dropna().unique()
                    for group in groups:
                        item = GroupListWidgetItem(str(group))
                        self.lstUsedColumns.addItem(item)
            else:
                self.lblUsedColumns.setText('Bins')
                if mapping is not None:
                    values, colors = mapping
                    try:
                        for low, high, color in zip(values[:-1], values[1:], colors):
                            item = RangeListWidgetItem(low, high)
                            item.setBackground(QColor(color))
                            self.lstUsedColumns.addItem(item)
                    except ValueError:
                        self.generate_new_bins(8)
                else:
                    self.generate_new_bins(8)

                self.btGenerateBins.clicked.connect(self.on_generate_new_bins)
                self.btMergeBins.clicked.connect(self.on_merge_bins)
                self.btSplitBins.clicked.connect(self.on_split_bins)
                self.btEditBin.clicked.connect(self.on_edit_bin)
                self.btAddBin.clicked.connect(self.on_add_bin)
                self.btRemoveBins.clicked.connect(self.on_remove_bins)

    def on_unuse_selected_column(self):
        self.lstUsedColumns.clear()

        if self._column_id is not None:
            index = self._model.index(0, self._column_id)
            text = self._model.headerData(self._column_id, Qt.Horizontal, Qt.DisplayRole)
            color = self._model.headerData(self._column_id, Qt.Horizontal, ColorMarkRole)
            item = ColumnListWidgetItem(text, column=index.column())
            if color is not None:
                item.setBackground(color)

            self.lstColumns.addItem(item)

    def on_use_selected_column(self):
        self.on_unuse_selected_column()

        selected_items = self.lstColumns.selectedItems()
        if len(selected_items) != 1:
            return

        self.lstUsedColumns.clear()
        item = selected_items[0]
        self.lstColumns.takeItem(self.lstColumns.row(item))
        self._column_id = item.data(ColumnRole)

        self.populate_bins()

    def on_remove_bins(self):
        for item in self.lstUsedColumns.selectedItems():
            self.lstUsedColumns.takeItem(self.lstUsedColumns.row(item))

    def on_add_bin(self):
        dlg = RangeInputDialog(self)
        if dlg.exec():
            item = RangeListWidgetItem(*dlg.getRange())
            self.lstUsedColumns.addItem(item)

    def on_edit_bin(self):
        for item in self.lstUsedColumns.selectedItems():
            low, high = item.data(ValueRole)
            dlg = RangeInputDialog(self, low=low, high=high)
            if dlg.exec():
                item.setData(ValueRole, dlg.getRange())
            break

    def on_split_bins(self):
        for item in self.lstUsedColumns.selectedItems():
            low, high = item.data(ValueRole)
            self.lstUsedColumns.takeItem(self.lstUsedColumns.row(item))
            diff = (low + high) / 2
            item = RangeListWidgetItem(low, low + diff)
            self.lstUsedColumns.addItem(item)
            item = RangeListWidgetItem(low + diff, high)
            self.lstUsedColumns.addItem(item)

    def on_merge_bins(self):
        bins = []
        for item in self.lstUsedColumns.selectedItems():
            bins.extend(item.data(ValueRole))
            self.lstUsedColumns.takeItem(self.lstUsedColumns.row(item))

        if bins:
            item = RangeListWidgetItem(min(bins), max(bins))
            self.lstUsedColumns.addItem(item)

    def on_generate_new_bins(self):
        bins, ok = QInputDialog.getInt(self, None, "Enter a number of bins:", value=8, min=1)

        if ok:
            self.generate_new_bins(bins)

    def generate_new_bins(self, bins=8):
        self.lstUsedColumns.clear()
        for low, high in pairwise(np.histogram_bin_edges(self._data, bins=bins)):
            item = RangeListWidgetItem(low, high)
            self.lstUsedColumns.addItem(item)

    def import_color_item(self, row: List[str]) -> Tuple:
        color = QColor(row[1][0])
        try:
            polygon_id = NodePolygon[row[1][1]] if len(row[1]) > 1 else NodePolygon.Circle
        except KeyError:
            polygon_id = NodePolygon.Circle
        brushstyle = Qt.BrushStyle(row[1][2]) if len(row[1]) > 2 else Qt.NoBrush

        if color.isValid():
            return color, polygon_id, brushstyle

    def export_color_item(self, item: QListWidgetItem) -> List[str]:
        color = item.data(Qt.BackgroundRole).color()
        polygon_id = item.data(BaseColorMappingDialog.PolygonRole)
        polygon_id = polygon_id if polygon_id is not None else NodePolygon.Circle
        brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole)
        brushstyle = brushstyle if brushstyle is not None else Qt.NoBrush

        if color is not None and color.isValid():
            return color.name(), polygon_id.name, brushstyle

    def done(self, r):
        if r == QDialog.Accepted:
            colors = [self.lstColors.item(row).data(Qt.BackgroundRole).color().name()
                      for row in range(self.lstColors.count())]
            QSettings().setValue('NetworkView/node_colors', colors)
        super().done(r)

    def getValues(self):
        item = self.lstUsedColumns.item(0)
        if isinstance(item, BoolListWidgetItem):
            mapping = {}
            for row in range(self.lstUsedColumns.count()):
                item = self.lstUsedColumns.item(row)
                group = item.data(ValueRole)
                bg = item.data(Qt.BackgroundRole)
                polygon_id = item.data(BaseColorMappingDialog.PolygonRole)
                polygon_id = polygon_id if polygon_id is not None else NodePolygon.Circle
                brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole)
                brushstyle = brushstyle if brushstyle is not None else Qt.NoBrush

                if bg is not None and bg.color().isValid():
                    mapping[group] = (bg.color(), polygon_id.value, brushstyle)
                else:
                    mapping[group] = (QColor(Qt.transparent), polygon_id.value, brushstyle)
            return self._column_id, mapping
        elif isinstance(item, GroupListWidgetItem):
            mapping = {}
            for row in range(self.lstUsedColumns.count()):
                item = self.lstUsedColumns.item(row)
                group = str(item.data(ValueRole))
                bg = item.data(Qt.BackgroundRole)
                polygon_id = item.data(BaseColorMappingDialog.PolygonRole)
                polygon_id = polygon_id if polygon_id is not None else NodePolygon.Circle
                brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole)
                brushstyle = brushstyle if brushstyle is not None else Qt.NoBrush

                if bg is not None and bg.color().isValid():
                    mapping[group] = (bg.color(), polygon_id.value, brushstyle)
                else:
                    mapping[group] = (QColor(Qt.transparent), polygon_id.value, brushstyle)
            return self._column_id, mapping
        else:
            bins = []
            colors = []
            polygons = []
            styles = []
            for row in range(self.lstUsedColumns.count()):
                item = self.lstUsedColumns.item(row)
                low, high = item.data(ValueRole)
                bg = item.data(Qt.BackgroundRole)
                polygon_id = item.data(BaseColorMappingDialog.PolygonRole)
                polygon_id = polygon_id if polygon_id is not None else NodePolygon.Circle
                brushstyle = item.data(BaseColorMappingDialog.BrushStyleRole)
                brushstyle = brushstyle if brushstyle is not None else Qt.NoBrush

                bins.append(low)
                polygons.append(polygon_id.value)
                styles.append(brushstyle)
                if bg is not None and bg.color().isValid():
                    colors.append(bg.color())
                else:
                    colors.append(QColor(Qt.transparent))

            try:
                # noinspection PyUnboundLocalVariable
                bins.append(high)
            except UnboundLocalError:
                pass

            return self._column_id, (bins, colors, polygons, styles)
