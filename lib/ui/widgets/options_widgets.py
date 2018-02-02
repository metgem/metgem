#!/usr/bin/env python
from PyQt5 import QtWidgets, uic


class TSNE_option_widget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi('lib/ui/widgets/TSNE_option_widget.ui', self)

class Network_option_widget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi('lib/ui/widgets/Network_option_widget.ui', self)
        