# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\network_options_widget.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\network_options_widget.ui' applies.
#
# Created: Sat Mar  5 14:43:04 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_gbNetworkOptions(object):
    def setupUi(self, gbNetworkOptions):
        gbNetworkOptions.setObjectName("gbNetworkOptions")
        gbNetworkOptions.resize(250, 111)
        self.gridLayout_3 = QtWidgets.QGridLayout(gbNetworkOptions)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.spinNetworkMaxNeighbor = QtWidgets.QSpinBox(gbNetworkOptions)
        self.spinNetworkMaxNeighbor.setEnabled(True)
        self.spinNetworkMaxNeighbor.setMinimum(1)
        self.spinNetworkMaxNeighbor.setMaximum(20)
        self.spinNetworkMaxNeighbor.setProperty("value", 10)
        self.spinNetworkMaxNeighbor.setObjectName("spinNetworkMaxNeighbor")
        self.gridLayout_3.addWidget(self.spinNetworkMaxNeighbor, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(gbNetworkOptions)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(gbNetworkOptions)
        self.label_7.setObjectName("label_7")
        self.gridLayout_3.addWidget(self.label_7, 1, 0, 1, 1)
        self.spinNetworkMinScore = QtWidgets.QDoubleSpinBox(gbNetworkOptions)
        self.spinNetworkMinScore.setEnabled(True)
        self.spinNetworkMinScore.setDecimals(2)
        self.spinNetworkMinScore.setMaximum(1.0)
        self.spinNetworkMinScore.setSingleStep(0.05)
        self.spinNetworkMinScore.setProperty("value", 0.7)
        self.spinNetworkMinScore.setObjectName("spinNetworkMinScore")
        self.gridLayout_3.addWidget(self.spinNetworkMinScore, 1, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem, 3, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem1, 0, 2, 3, 1)
        self.label_4 = QtWidgets.QLabel(gbNetworkOptions)
        self.label_4.setEnabled(True)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 2, 0, 1, 1)
        self.spinNetworkMaxConnectedComponentSize = QtWidgets.QSpinBox(gbNetworkOptions)
        self.spinNetworkMaxConnectedComponentSize.setEnabled(True)
        self.spinNetworkMaxConnectedComponentSize.setMinimum(0)
        self.spinNetworkMaxConnectedComponentSize.setMaximum(10000)
        self.spinNetworkMaxConnectedComponentSize.setProperty("value", 1000)
        self.spinNetworkMaxConnectedComponentSize.setObjectName("spinNetworkMaxConnectedComponentSize")
        self.gridLayout_3.addWidget(self.spinNetworkMaxConnectedComponentSize, 2, 1, 1, 1)

        self.retranslateUi(gbNetworkOptions)
        QtCore.QMetaObject.connectSlotsByName(gbNetworkOptions)
        gbNetworkOptions.setTabOrder(self.spinNetworkMaxNeighbor, self.spinNetworkMinScore)
        gbNetworkOptions.setTabOrder(self.spinNetworkMinScore, self.spinNetworkMaxConnectedComponentSize)

    def retranslateUi(self, gbNetworkOptions):
        gbNetworkOptions.setTitle(QtWidgets.QApplication.translate("gbNetworkOptions", "Network Visualization", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("gbNetworkOptions", "Maximum Neighbor Number (topK)", None, -1))
        self.label_7.setText(QtWidgets.QApplication.translate("gbNetworkOptions", "Minimal Cosine Score Value", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("gbNetworkOptions", "Max. Connected Component Size ", None, -1))

