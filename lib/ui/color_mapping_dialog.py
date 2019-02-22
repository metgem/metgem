from ..ui.widgets.metadata import ColorMarkRole

import os
import random
from typing import List, Union

from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings, QSize, QAbstractTableModel, QModelIndex, QObject, QEvent
from PyQt5.QtGui import QColor, QStandardItemModel, QIcon, QDropEvent, QKeyEvent, QBrush, QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QColorDialog, QListWidgetItem, QFileDialog, QMessageBox

import matplotlib.cm as mplcm
import numpy as np

UI_FILE = os.path.join(os.path.dirname(__file__), 'color_mapping_dialog.ui')

ColorMappingDialogUI, ColorMappingDialogBase = uic.loadUiType(UI_FILE,
                                                              from_imports='lib.ui',
                                                              import_from='lib.ui')

ColumnRole = Qt.UserRole + 1

MOVE_COLUMNS_SELECT = 0
MOVE_COLUMNS_UNSELECT = 1

# COLORMAPS = ['auto', 'viridis', 'cividis', 'plasma', 'inferno', 'magma',
#              'Pastel1', 'Pastel2', 'Paired', 'Accent',
#              'Dark2', 'Set1', 'Set2', 'Set3',
#              'tab10', 'tab20', 'tab20b', 'tab20c',
#              'jet', 'rainbow', 'terrain', 'CMRmap', 'gnuplot', 'gnuplot2', 'hsv', 'gist_rainbow',
#              'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'copper',
#              'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds']


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


class ColumnListWidgetItem(ColorMixin, WidgetItem):
    def __init__(self, *args, column: int=None, **kwargs):
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


class ColorMappingDialog(ColorMappingDialogUI, ColorMappingDialogBase):

    def __init__(self, model: QAbstractTableModel, selected_indexes: List[QModelIndex], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._model = model

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        for i in range(model.columnCount()):
            index = model.index(0, i)
            text = model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            color = model.headerData(i, Qt.Horizontal, ColorMarkRole)
            item = ColumnListWidgetItem(text, column=index.column())
            if color is not None:
                item.setBackground(color)

            if index not in selected_indexes:
                self.lstColumns.addItem(item)
            else:
                self.lstUsedColumns.addItem(item)

        self.lstColumns.viewport().installEventFilter(self)
        self.lstUsedColumns.viewport().installEventFilter(self)
        self.lstUsedColumns.installEventFilter(self)

        colors = QSettings().value('NetworkView/pie_colors',
                                   [c.name() for c in generate_colors(8)],
                                   type=str)
        self.set_colors(colors)

        current_cmap = QSettings().value('ColorMap', 'auto')
        cmaps = ['auto'] + sorted([k for k in mplcm.cmap_d.keys() if not k.endswith('_r')], key=lambda s: s.casefold())
        for i, cmap in enumerate(cmaps):
            pixmap = cmap2pixmap(cmap)
            self.cbColorMap.addItem(QIcon(pixmap), cmap)
            if cmap == current_cmap:
                self.cbColorMap.setCurrentIndex(i)

        self.lstUsedColumns.itemDoubleClicked.connect(self.get_color)
        self.lstColors.itemDoubleClicked.connect(self.get_color)
        self.btEditColor.clicked.connect(lambda: self.get_color(self.lstColors.currentItem()))
        self.btAddColor.clicked.connect(self.add_color)
        self.btRemoveColors.clicked.connect(self.remove_selected_colors)
        self.btGenerateColors.clicked.connect(lambda: self.generate_new_colors(self.cbColorMap.currentText()))
        self.btAutoAssignColors.clicked.connect(self.auto_assign_colors)
        self.btUseSelectedColumns.clicked.connect(lambda: self.move_selected_columns(MOVE_COLUMNS_SELECT))
        self.btRemoveSelectedColumns.clicked.connect(lambda: self.move_selected_columns(MOVE_COLUMNS_UNSELECT))
        self.cbColorMap.currentIndexChanged[str].connect(self.generate_new_colors)
        self.btRemoveSelectedColumnsColors.clicked.connect(self.remove_selected_columns_colors)
        self.btLoadColorList.clicked.connect(self.load_color_list)
        self.btSaveColorList.clicked.connect(self.save_color_list)

    def done(self, r):
        if r == QDialog.Accepted:
            colors = [self.lstColors.item(row).data(Qt.BackgroundRole).color().name() for row in range(self.lstColors.count())]
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

    def get_color(self, item: ColorListWidgetItem=None):
        current_color = item.data(Qt.BackgroundRole).color() \
            if item is not None and item.data(Qt.BackgroundRole) is not None else QColor()
        color = QColorDialog.getColor(initial=current_color, parent=self, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            item.setBackground(color)

    def add_color(self):
        color = QColorDialog.getColor(parent=self, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            item = ColorListWidgetItem()
            item.setBackground(color)
            self.lstColors.addItem(item)

    def remove_selected_colors(self):
        for item in self.lstColors.selectedItems():
            self.lstColors.takeItem(item)

    def set_colors(self, colors: List[Union[str, QColor]]):
        self.lstColors.clear()
        for color in colors:
            if isinstance(color, str):
                color = QColor(color)

            if color.isValid():
                item = ColorListWidgetItem()
                item.setBackground(color)
                self.lstColors.addItem(item)

    def generate_new_colors(self, cmap: str='auto'):
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

    def remove_selected_columns_colors(self):
        for item in self.lstUsedColumns.selectedItems():
            item.setBackground(None)

    def load_color_list(self):
        filter_ = ["Color list (*.txt)"]
        filename, filter_ = QFileDialog.getOpenFileName(self, "Load color list",
                                                        filter=";;".join(filter_))
        if filename:
            colors = []
            try:
                with open(filename, 'r') as f:
                    for line in f.readlines():
                        color = QColor(line.strip('\n'))
                        if color.isValid():
                            colors.append(color)
                self.set_colors(colors)
            except FileNotFoundError:
                QMessageBox.warning(self, None, "Selected file does not exists.")
            except IOError:
                QMessageBox.warning(self, None, "Load failed (I/O Error).")

    def save_color_list(self):
        filter_ = ["Color list (*.txt)"]
        filename, filter_ = QFileDialog.getSaveFileName(self, "Save color list",
                                                        filter=";;".join(filter_))
        if filename:
            try:
                with open(filename, 'w') as f:
                    for row in range(self.lstColors.count()):
                        color = self.lstColors.item(row).data(Qt.BackgroundRole).color()
                        if color is not None and color.isValid():
                            f.write(color.name() + '\n')
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
                            item = self.lstUsedColumns.item(self.lstUsedColumns.row(first_item) + i)
                            if item:
                                item.setBackground(color)
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
                        if bg is not None and bg.color().isValid():
                            new_item.setBackground(bg.color())
                        self.lstUsedColumns.addItem(new_item)
                    self.lstUsedColumns.sortItems()
                    event.accept()

        return super().eventFilter(obj, event)

