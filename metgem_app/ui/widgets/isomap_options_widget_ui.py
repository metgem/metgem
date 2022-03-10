# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\git\metgem\metgem_app\ui\widgets\isomap_options_widget.ui',
# licensing of 'E:\git\metgem\metgem_app\ui\widgets\isomap_options_widget.ui' applies.
#
# Created: Sat Mar  5 14:43:02 2022
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_gbOptions(object):
    def setupUi(self, gbOptions):
        gbOptions.setObjectName("gbOptions")
        gbOptions.resize(331, 107)
        self.gridLayout_3 = QtWidgets.QGridLayout(gbOptions)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.spinNumIterations = QtWidgets.QSpinBox(gbOptions)
        self.spinNumIterations.setMinimum(1)
        self.spinNumIterations.setMaximum(10000)
        self.spinNumIterations.setSingleStep(50)
        self.spinNumIterations.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spinNumIterations.setProperty("value", 300)
        self.spinNumIterations.setObjectName("spinNumIterations")
        self.gridLayout_3.addWidget(self.spinNumIterations, 3, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(gbOptions)
        self.label_6.setObjectName("label_6")
        self.gridLayout_3.addWidget(self.label_6, 3, 0, 1, 1)
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
        self.label = QtWidgets.QLabel(gbOptions)
        self.label.setObjectName("label")
        self.gridLayout_3.addWidget(self.label, 4, 0, 1, 1)
        self.spinNumNeighbors = QtWidgets.QSpinBox(gbOptions)
        self.spinNumNeighbors.setMinimum(1)
        self.spinNumNeighbors.setMaximum(1000)
        self.spinNumNeighbors.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spinNumNeighbors.setProperty("value", 5)
        self.spinNumNeighbors.setObjectName("spinNumNeighbors")
        self.gridLayout_3.addWidget(self.spinNumNeighbors, 4, 1, 1, 1)

        self.retranslateUi(gbOptions)
        QtCore.QMetaObject.connectSlotsByName(gbOptions)

    def retranslateUi(self, gbOptions):
        gbOptions.setTitle(QtWidgets.QApplication.translate("gbOptions", "Isomap Visualization", None, -1))
        self.label_6.setText(QtWidgets.QApplication.translate("gbOptions", "Number of iterations", None, -1))
        self.label_7.setText(QtWidgets.QApplication.translate("gbOptions", "At least", None, -1))
        self.label_8.setText(QtWidgets.QApplication.translate("gbOptions", "cosine score(s) above", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("gbOptions", "Number of neighbors", None, -1))

