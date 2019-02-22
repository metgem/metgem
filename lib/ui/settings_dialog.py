from ..config import STYLES_PATH

import os
import random
import glob

from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings, QPointF
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QListWidgetItem

from PyQtNetworkView import style_from_css, NetworkScene


UI_FILE = os.path.join(os.path.dirname(__file__), 'settings_dialog.ui')

SettingsDialogUI, SettingsDialogBase = uic.loadUiType(UI_FILE,
                                                      from_imports='lib.ui',
                                                      import_from='lib.ui')

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
        nodes = scene.addNodes(range(len(POSITIONS)),
                               labels=[f"{random.randint(100000, 900000)/1000:.4f}" for x in POSITIONS],
                               positions=[QPointF(x, 96-y) for x, y in POSITIONS])
        sources, dests = zip(*LINKS)
        edges = self.gvStylePreview.scene().addEdges(range(len(LINKS)), [nodes[x] for x in sources],
                                                     [nodes[x] for x in dests], WIDTHS)

        self.gvStylePreview.minimap.setVisible(False)
        scene.setScale(4)
        nodes[4].setSelected(True)
        edges[3].setSelected(True)
        edges[4].setSelected(True)
        edges[5].setSelected(True)

        styles = [None] + glob.glob(os.path.join(STYLES_PATH, '*.css'))
        if STYLES_PATH != os.path.realpath('styles'):
            styles += glob.glob(os.path.join(os.path.realpath('styles'), '*.css'))

        current_style = QSettings().value('NetworkView/style', None)
        current_item = None
        for css in styles:
            style = style_from_css(css)
            item = QListWidgetItem(style.styleName())
            item.setData(StyleRole, style)
            item.setData(CssRole, css)
            if css == current_style:
                current_item = item
            self.lstStyles.addItem(item)

        self.lstStyles.currentItemChanged.connect(
            lambda item: self.gvStylePreview.scene().setNetworkStyle(item.data(StyleRole)))

        if current_item is not None:
            self.lstStyles.setCurrentItem(current_item)
        else:
            self.lstStyles.setCurrentRow(0)

        # Edges tab
        value = settings.value('Metadata/neutral_tolerance')
        if value is not None:
            self.spinNeutralTolerance.setValue(value)

    def showEvent(self, event: QShowEvent):
        self.tabWidget.setCurrentIndex(0)
        self.gvStylePreview.zoomToFit()
        super().showEvent(event)

    def done(self, r):
        if r == QDialog.Accepted:
            settings = QSettings()
            settings.setValue('Metadata/neutral_tolerance', self.spinNeutralTolerance.value())
            settings.setValue('NetworkView/style', self.lstStyles.currentItem().data(CssRole))
        super().done(r)

    def getValues(self):
        return self.gvStylePreview.scene().networkStyle()

