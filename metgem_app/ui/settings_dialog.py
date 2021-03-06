import glob
import os
import random

from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings, QPointF, QCoreApplication
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQtNetworkView import style_from_css, NetworkScene

from .. import utils
from ..config import STYLES_PATH, APP_PATH

UI_FILE = os.path.join(os.path.dirname(__file__), 'settings_dialog.ui')

SettingsDialogUI, SettingsDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='metgem_app.ui',
                                                      import_from='metgem_app.ui')

POSITIONS = [(14, 47), (34, 37), (15, 21), (40, 14), (58, 33),
             (60, 59), (46, 77), (70, 80), (84, 63), (76, 42)]
LINKS = [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5), (4, 5), (5, 6), (5, 7), (5, 8), (5, 9)]
WIDTHS = (11.024, 9.868, 13.504, 6.664, 9.944, 10.036, 7.984, 11.028, 6.464, 8.504)

StyleRole = Qt.UserRole + 1
CssRole = Qt.UserRole + 2


class SettingsDialog(SettingsDialogUI, SettingsDialogBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        settings = QSettings()

        # Theme tab
        scene = NetworkScene()
        self.gvStylePreview.setScene(scene)
        nodes = scene.createNodes(range(len(POSITIONS)),
                                  labels=[f"{random.randint(100000, 900000)/1000:.4f}" for _ in POSITIONS],
                                  positions=[QPointF(x, 96-y) for x, y in POSITIONS])
        sources, dests = zip(*LINKS)
        edges = scene.createEdges(range(len(LINKS)), [nodes[x] for x in sources],
                                                     [nodes[x] for x in dests], WIDTHS)

        self.gvStylePreview.minimap.setVisible(False)
        scene.setScale(4)
        nodes[4].setSelected(True)
        edges[3].setSelected(True)
        edges[4].setSelected(True)
        edges[5].setSelected(True)

        styles = [None] + glob.glob(os.path.join(STYLES_PATH, '*.css'))
        app_style_path = os.path.realpath(os.path.join(APP_PATH, QCoreApplication.applicationName().lower(), 'styles'))
        if STYLES_PATH != app_style_path:
            styles += glob.glob(os.path.join(app_style_path, '*.css'))

        current_style = settings.value('NetworkView/style', None)
        current_item = None
        for css in styles:
            style = style_from_css(css)
            item = QListWidgetItem(style.styleName())
            item.setData(StyleRole, style)
            item.setData(CssRole, css)
            if css == current_style:
                current_item = item
            self.lstStyles.addItem(item)

        self.lstStyles.currentItemChanged.connect(self.on_change_theme)

        if current_item is not None:
            self.lstStyles.setCurrentItem(current_item)
        else:
            self.lstStyles.setCurrentRow(0)

        font_size = settings.value('NetworkView/style_font_size', 0, type=int)
        if font_size > 0:
            self.chkOverrideFontSize.setChecked(True)
            self.spinFontSize.setEnabled(True)
            self.spinFontSize.setValue(font_size)
        else:
            self.chkOverrideFontSize.setChecked(False)
            self.spinFontSize.setEnabled(False)

        self.chkOverrideFontSize.stateChanged.connect(self.spinFontSize.setEnabled)
        self.spinFontSize.valueChanged.connect(self.on_change_font_size)

        # Metadata tab
        value = settings.value('Metadata/neutral_tolerance', 50, type=int)
        if value is not None:
            self.spinNeutralTolerance.setValue(value)

        value = settings.value('Metadata/float_precision', 4, type=int)
        if value is not None:
            self.spinFloatPrecision.setValue(value)

    def showEvent(self, event: QShowEvent):
        self.tabWidget.setCurrentIndex(0)
        self.gvStylePreview.zoomToFit()
        super().showEvent(event)

    def on_change_theme(self, item):
        self.gvStylePreview.scene().setNetworkStyle(item.data(StyleRole))
        with utils.SignalBlocker(self.spinFontSize):
            style = item.data(StyleRole)
            if style is not None:
                font = style.nodeFont()
                self.spinFontSize.setValue(font.pointSize())

    def on_change_font_size(self, font_size):
        style = self.gvStylePreview.scene().networkStyle()
        if self.chkOverrideFontSize.isChecked():
            font = style.nodeFont()
            font.setPointSize(font_size)
            style.setNodeFont(font)
        self.gvStylePreview.scene().setNetworkStyle(style)

    def done(self, r):
        if r == QDialog.Accepted:
            settings = QSettings()
            settings.setValue('Metadata/neutral_tolerance', self.spinNeutralTolerance.value())
            settings.setValue('Metadata/float_precision', self.spinFloatPrecision.value())
            settings.setValue('NetworkView/style', self.lstStyles.currentItem().data(CssRole))
            settings.setValue('NetworkView/style_font_size',
                              self.spinFontSize.value() if self.chkOverrideFontSize.isChecked() else None)
        super().done(r)

    def getValues(self):
        style = self.gvStylePreview.scene().networkStyle()
        if self.chkOverrideFontSize.isChecked():
            font = style.nodeFont()
            font.setPointSize(self.spinFontSize.value())
            style.setNodeFont(font)
        return style
