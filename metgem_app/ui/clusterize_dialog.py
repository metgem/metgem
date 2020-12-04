import os

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from ..workers import ClusterizeOptions


class ClusterizeDialog(QDialog):

    def __init__(self, *args, views, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'clusterize_dialog.ui'), self)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        for desc, name in (('Excess of Mass', 'eom'), ('Leaf', 'leaf')):
            self.cbMethod.addItem(desc, name)

        for key, title in views.items():
            self.cbView.addItem(title, key)

        self.chkMinSamples.stateChanged.connect(self.spinMinSamples.setEnabled)

    def getValues(self):
        options = ClusterizeOptions()
        options.column_name = self.btColumnName.text()
        options.min_cluster_size = self.spinMinClusterSize.value()
        options.min_samples = self.spinMinSamples.value() if self.chkMinSamples.isChecked() else None
        options.cluster_selection_epsilon = self.spinEpsilon.value()
        options.cluster_selection_method = self.cbMethod.currentData()

        return self.cbView.currentData(), options
