#!/usr/bin/env python
from PyQt5 import QtWidgets, uic

class tsneOptionWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi('lib/ui/widgets/tsne_option_widget.ui', self)


class networkOptionWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi('lib/ui/widgets/network_option_widget.ui', self)
        