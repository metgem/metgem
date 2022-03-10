# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\phate_options_widget.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\phate_options_widget.ui' applies.
#
# Created: Sat Mar  5 14:43:05 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_gbOptions(object):
    def setupUi(self, gbOptions):
        gbOptions.setObjectName("gbOptions")
        gbOptions.resize(284, 156)
        self.gridLayout_3 = QtWidgets.QGridLayout(gbOptions)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.chkRandomState = QtWidgets.QCheckBox(gbOptions)
        self.chkRandomState.setObjectName("chkRandomState")
        self.gridLayout_3.addWidget(self.chkRandomState, 6, 0, 1, 4)
        self.spinKnn = QtWidgets.QSpinBox(gbOptions)
        self.spinKnn.setEnabled(True)
        self.spinKnn.setMaximum(100)
        self.spinKnn.setProperty("value", 5)
        self.spinKnn.setObjectName("spinKnn")
        self.gridLayout_3.addWidget(self.spinKnn, 3, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(gbOptions)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 4, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_7 = QtWidgets.QLabel(gbOptions)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_2.addWidget(self.label_7)
        self.spinMinScoresAboveThreshold = QtWidgets.QSpinBox(gbOptions)
        self.spinMinScoresAboveThreshold.setMinimum(1)
        self.spinMinScoresAboveThreshold.setMaximum(100)
        self.spinMinScoresAboveThreshold.setObjectName("spinMinScoresAboveThreshold")
        self.horizontalLayout_2.addWidget(self.spinMinScoresAboveThreshold)
        self.label_8 = QtWidgets.QLabel(gbOptions)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_2.addWidget(self.label_8)
        self.spinMinScore = QtWidgets.QDoubleSpinBox(gbOptions)
        self.spinMinScore.setMaximum(1.0)
        self.spinMinScore.setSingleStep(0.05)
        self.spinMinScore.setProperty("value", 0.7)
        self.spinMinScore.setObjectName("spinMinScore")
        self.horizontalLayout_2.addWidget(self.spinMinScore)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.gridLayout_3.addLayout(self.horizontalLayout_2, 0, 0, 1, 3)
        self.spinDecay = QtWidgets.QSpinBox(gbOptions)
        self.spinDecay.setEnabled(True)
        self.spinDecay.setMinimum(1)
        self.spinDecay.setMaximum(100)
        self.spinDecay.setSingleStep(1)
        self.spinDecay.setProperty("value", 15)
        self.spinDecay.setObjectName("spinDecay")
        self.gridLayout_3.addWidget(self.spinDecay, 4, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(gbOptions)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 3, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(gbOptions)
        self.label_5.setObjectName("label_5")
        self.gridLayout_3.addWidget(self.label_5, 5, 0, 1, 1)
        self.spinGamma = QtWidgets.QDoubleSpinBox(gbOptions)
        self.spinGamma.setEnabled(True)
        self.spinGamma.setDecimals(1)
        self.spinGamma.setMaximum(1.0)
        self.spinGamma.setSingleStep(0.1)
        self.spinGamma.setProperty("value", 1.0)
        self.spinGamma.setObjectName("spinGamma")
        self.gridLayout_3.addWidget(self.spinGamma, 5, 1, 1, 1)

        self.retranslateUi(gbOptions)
        QtCore.QMetaObject.connectSlotsByName(gbOptions)
        gbOptions.setTabOrder(self.spinMinScore, self.chkRandomState)

    def retranslateUi(self, gbOptions):
        gbOptions.setTitle(QtWidgets.QApplication.translate("gbOptions", "PHATE Visualization", None, -1))
        self.chkRandomState.setText(QtWidgets.QApplication.translate("gbOptions", "Random Initial State", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("gbOptions", "Alpha decay", None, -1))
        self.label_7.setText(QtWidgets.QApplication.translate("gbOptions", "At least", None, -1))
        self.label_8.setText(QtWidgets.QApplication.translate("gbOptions", "cosine score(s) above", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("gbOptions", "Number of nearest neighbors", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("gbOptions", "Informational distance constant", None, -1))

