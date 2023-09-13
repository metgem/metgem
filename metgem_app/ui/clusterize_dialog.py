from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from metgem_app.workers.options import ClusterizeOptions
from metgem_app.ui.clusterize_dialog_ui import Ui_Dialog


class ClusterizeDialog(QDialog, Ui_Dialog):

    def __init__(self, *args, views, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        for desc, name in (('Excess of Mass', 'eom'), ('Leaf', 'leaf')):
            self.cbMethod.addItem(desc, name)

        for key, name in views.items():
            self.cbView.addItem(name, key)

        self.chkMinSamples.stateChanged.connect(self.spinMinSamples.setEnabled)

    def getValues(self):
        options = ClusterizeOptions()
        options.column_name = self.btColumnName.text()
        options.min_cluster_size = self.spinMinClusterSize.value()
        options.min_samples = self.spinMinSamples.value() if self.chkMinSamples.isChecked() else None
        options.cluster_selection_epsilon = self.spinEpsilon.value()
        options.cluster_selection_method = self.cbMethod.currentData()

        return self.cbView.currentData(), options
