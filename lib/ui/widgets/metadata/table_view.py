from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import Qt


class NodeTableView(QTableView):
    """ TableView to display Nodes information """
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)